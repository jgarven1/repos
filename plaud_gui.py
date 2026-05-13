"""
Plaud Transcripts — GUI App
Double-click Plaud.app to open this window.
"""

import json
import pathlib
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

import security

SCRIPT_DIR  = pathlib.Path(__file__).parent
MAIN_SCRIPT = SCRIPT_DIR / "plaud_transcripts.py"
PYTHON      = sys.executable


# ---------------------------------------------------------------------------
# Helpers (delegate to security module)
# ---------------------------------------------------------------------------

def get_accounts():
    return security.get_accounts()

def session_file(account):
    return security.session_path(account)

def transcripts_dir(account):
    return security.transcripts_path(account)


def extract_session_info(account):
    """Decrypt the session and return displayable (non-sensitive) info."""
    sf = session_file(account)
    if not sf.exists():
        return {}
    try:
        data = security.decrypt_session(sf)
        info = {
            "Session file": sf.name,
            "Location":     str(sf.parent),
            "Encrypted":    "Yes ✓",
            "Permissions":  "Owner only (600) ✓",
            "Cookies saved": str(len(data.get("cookies", []))),
        }
        for origin in data.get("origins", []):
            for item in origin.get("localStorage", []):
                val = item.get("value", "")
                if "@" in val and len(val) < 120:
                    try:
                        parsed = json.loads(val)
                        email = parsed.get("email") or parsed.get("userEmail")
                        if email:
                            info["Email"] = email
                            break
                    except Exception:
                        pass
        return info
    except Exception:
        return {"Session file": sf.name, "Status": "Could not decrypt"}


# ---------------------------------------------------------------------------
# Account detail / edit dialog
# ---------------------------------------------------------------------------

class AccountDetailDialog(tk.Toplevel):
    def __init__(self, parent, account):
        super().__init__(parent)
        self.parent      = parent
        self.account     = account
        self.new_name    = None
        self.title(f"Account — {account}")
        self.resizable(False, False)
        self.grab_set()
        self._build_ui()
        self.transient(parent)
        self.wait_window()

    def _build_ui(self):
        pad = dict(padx=24, pady=6)

        # Header
        hdr = tk.Frame(self, bg="#1a1a1a")
        hdr.grid(row=0, column=0, columnspan=2, sticky="ew")
        tk.Label(hdr, text=f"🔐  Account Details",
                 font=("Helvetica", 14, "bold"),
                 fg="white", bg="#1a1a1a", pady=12, padx=20).pack(anchor="w")

        body = ttk.Frame(self, padding=20)
        body.grid(row=1, column=0, sticky="nsew")

        # Account name (editable)
        ttk.Label(body, text="Account Name", font=("Helvetica", 11, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 2))
        name_frame = ttk.Frame(body)
        name_frame.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        self.name_var = tk.StringVar(value=self.account)
        self.name_entry = ttk.Entry(name_frame, textvariable=self.name_var, width=28,
                                     font=("Helvetica", 12))
        self.name_entry.pack(side="left", padx=(0, 8))
        ttk.Button(name_frame, text="Save Name", command=self._save_name).pack(side="left")

        ttk.Separator(body, orient="horizontal").grid(
            row=2, column=0, sticky="ew", pady=10)

        # Session info
        ttk.Label(body, text="Login Information", font=("Helvetica", 11, "bold")).grid(
            row=3, column=0, sticky="w", pady=(0, 6))

        info = extract_session_info(self.account)
        for i, (key, val) in enumerate(info.items()):
            row_frame = ttk.Frame(body)
            row_frame.grid(row=4 + i, column=0, sticky="ew", pady=2)
            tk.Label(row_frame, text=f"{key}:", font=("Helvetica", 10, "bold"),
                     width=18, anchor="w").pack(side="left")
            tk.Label(row_frame, text=val, font=("Helvetica", 10),
                     fg="#333333", anchor="w").pack(side="left")

        ttk.Separator(body, orient="horizontal").grid(
            row=4 + len(info), column=0, sticky="ew", pady=10)

        # Security note
        tk.Label(body,
                 text="🔒  Your login is stored as a browser session file.\n"
                      "    No passwords are saved.",
                 font=("Helvetica", 10), fg="#555555", justify="left").grid(
            row=5 + len(info), column=0, sticky="w", pady=(0, 12))

        ttk.Button(body, text="Close", command=self.destroy).grid(
            row=6 + len(info), column=0, sticky="e")

    def _save_name(self):
        new = self.name_var.get().strip()
        if not new:
            messagebox.showwarning("Invalid name", "Account name cannot be empty.", parent=self)
            return
        if new == self.account:
            self.destroy()
            return
        if session_file(new).exists():
            messagebox.showwarning("Name taken",
                                   f"An account named '{new}' already exists.", parent=self)
            return

        # Rename session file (stays encrypted, just renamed)
        old_sf = security.session_path(self.account)
        new_sf = security.session_path(new)
        if old_sf.exists():
            old_sf.rename(new_sf)
            security.set_secure_permissions(new_sf)

        # Rename transcripts folder if it exists
        old_td = security.transcripts_path(self.account)
        new_td = security.transcripts_path(new)
        if old_td.exists() and not new_td.exists():
            old_td.rename(new_td)

        self.new_name = new
        messagebox.showinfo("Renamed", f"Account renamed to '{new}'.", parent=self)
        self.destroy()


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class PlaudApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw()   # hide until authenticated
        self.title("Plaud Transcripts")
        self.resizable(False, False)
        self._build_ui()

        # Migrate any old plain-text sessions from the repos folder
        migrated = security.migrate_old_files(SCRIPT_DIR)
        if migrated:
            self._log(f"Migrated {len(migrated)} session file(s) to secure storage.")

        self._refresh_accounts()

        # Authenticate before showing the window
        threading.Thread(target=self._authenticate, daemon=True).start()

    def _authenticate(self):
        success, error = security.authenticate("Open Plaud Transcripts")
        if success:
            self.after(0, self.deiconify)
        else:
            # LocalAuthentication may not be available on all setups —
            # fall back to a simple password stored in Keychain.
            self.after(0, lambda: self._fallback_auth(error))

    def _fallback_auth(self, reason):
        import keyring
        stored = keyring.get_password("com.plaud.transcripts", "app_password")
        if stored is None:
            # First launch — let the user set a password
            pw = simpledialog.askstring(
                "Set App Password",
                "Touch ID is not available.\n\nSet a password to protect this app:",
                show="*", parent=self,
            )
            if not pw:
                self.destroy()
                return
            keyring.set_password("com.plaud.transcripts", "app_password", pw)
            self.deiconify()
        else:
            pw = simpledialog.askstring(
                "Plaud Transcripts — Locked",
                "Enter your app password:",
                show="*", parent=self,
            )
            if pw == stored:
                self.deiconify()
            else:
                messagebox.showerror("Access Denied",
                                     "Incorrect password. Plaud Transcripts will close.")
                self.destroy()

    def _build_ui(self):
        # ── Header ────────────────────────────────────────────────────
        header = tk.Frame(self, bg="#1a1a1a")
        header.grid(row=0, column=0, sticky="ew")
        title_frame = tk.Frame(header, bg="#1a1a1a")
        title_frame.pack(anchor="w", padx=20, pady=14)
        tk.Label(title_frame, text="🎙  Plaud Transcripts",
                 font=("Helvetica", 18, "bold"),
                 fg="white", bg="#1a1a1a").pack(side="left")
        tk.Label(title_frame, text="  Secure Terminal",
                 font=("Helvetica", 13, "bold"),
                 fg="#00cc44", bg="#1a1a1a").pack(side="left", padx=(8, 0))

        # ── Tabs ──────────────────────────────────────────────────────
        notebook = ttk.Notebook(self)
        notebook.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)

        self._build_tab_transcripts(notebook)
        self._build_tab_claude(notebook)

    # ------------------------------------------------------------------
    # Tab 1 — Transcripts
    # ------------------------------------------------------------------

    def _build_tab_transcripts(self, notebook):
        body = ttk.Frame(notebook, padding=20)
        notebook.add(body, text="  Transcripts  ")

        ttk.Label(body, text="Accounts", font=("Helvetica", 13, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
        ttk.Label(body, text="Double-click an account to view or edit details.",
                  font=("Helvetica", 10), foreground="#666666").grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(0, 4))

        self.account_box = tk.Listbox(body, height=4, width=38, selectmode="single",
                                       font=("Helvetica", 12))
        self.account_box.grid(row=2, column=0, columnspan=2, sticky="ew")
        self.account_box.bind("<Double-Button-1>", self._view_account)

        acc_btns = ttk.Frame(body)
        acc_btns.grid(row=3, column=0, columnspan=2, sticky="w", pady=(6, 0))
        ttk.Button(acc_btns, text="Add Account",    command=self._add_account).pack(side="left", padx=(0, 6))
        ttk.Button(acc_btns, text="View / Edit",    command=self._view_account).pack(side="left", padx=(0, 6))
        ttk.Button(acc_btns, text="Remove Account", command=self._remove_account).pack(side="left")

        ttk.Separator(body, orient="horizontal").grid(
            row=4, column=0, columnspan=2, sticky="ew", pady=16)

        ttk.Label(body, text="Export", font=("Helvetica", 13, "bold")).grid(
            row=5, column=0, columnspan=2, sticky="w", pady=(0, 4))
        ttk.Label(body, text="Account:").grid(row=6, column=0, sticky="w")
        self.export_var = tk.StringVar()
        self.export_combo = ttk.Combobox(body, textvariable=self.export_var,
                                          state="readonly", width=28)
        self.export_combo.grid(row=6, column=1, sticky="ew", padx=(8, 0))
        self.export_btn = ttk.Button(body, text="Export New Transcripts",
                                      command=self._export)
        self.export_btn.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(10, 4))
        ttk.Button(body, text="Open Transcripts Folder",
                   command=self._open_folder).grid(
            row=8, column=0, columnspan=2, sticky="ew")

        ttk.Separator(body, orient="horizontal").grid(
            row=9, column=0, columnspan=2, sticky="ew", pady=16)

        ttk.Label(body, text="Activity Log", font=("Helvetica", 13, "bold")).grid(
            row=10, column=0, columnspan=2, sticky="w", pady=(0, 4))
        self.log = tk.Text(body, height=12, width=52, state="disabled",
                           font=("Courier", 10), bg="#f5f5f5", fg="#1a1a1a", relief="flat")
        scroll = ttk.Scrollbar(body, command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.grid(row=11, column=0, sticky="nsew")
        scroll.grid(row=11, column=1, sticky="ns")
        ttk.Button(body, text="Clear Log", command=self._clear_log).grid(
            row=12, column=0, columnspan=2, sticky="e", pady=(6, 0))

    # ------------------------------------------------------------------
    # Tab 2 — Claude AI
    # ------------------------------------------------------------------

    def _build_tab_claude(self, notebook):
        body = ttk.Frame(notebook, padding=20)
        notebook.add(body, text="  Claude AI  ")

        # API key section
        ttk.Label(body, text="Anthropic API Key",
                  font=("Helvetica", 13, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))

        self.api_key_status = tk.StringVar()
        self._refresh_api_key_status()
        ttk.Label(body, textvariable=self.api_key_status,
                  font=("Helvetica", 10)).grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(0, 6))

        key_btns = ttk.Frame(body)
        key_btns.grid(row=2, column=0, columnspan=2, sticky="w")
        ttk.Button(key_btns, text="Set API Key",    command=self._set_api_key).pack(side="left", padx=(0, 6))
        ttk.Button(key_btns, text="Remove API Key", command=self._remove_api_key).pack(side="left")

        ttk.Separator(body, orient="horizontal").grid(
            row=3, column=0, columnspan=2, sticky="ew", pady=16)

        # Process section
        ttk.Label(body, text="Process Transcripts",
                  font=("Helvetica", 13, "bold")).grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(0, 4))
        ttk.Label(body,
                  text="Send unprocessed transcripts to Claude to extract\n"
                       "summaries, action items, decisions and topics.",
                  font=("Helvetica", 10), foreground="#555555", justify="left").grid(
            row=5, column=0, columnspan=2, sticky="w", pady=(0, 8))

        proc_row = ttk.Frame(body)
        proc_row.grid(row=6, column=0, columnspan=2, sticky="ew")
        ttk.Label(proc_row, text="Account:").pack(side="left")
        self.proc_account_var = tk.StringVar()
        self.proc_combo = ttk.Combobox(proc_row, textvariable=self.proc_account_var,
                                        state="readonly", width=20)
        self.proc_combo.pack(side="left", padx=(8, 0))

        self.process_btn = ttk.Button(body, text="Process with Claude",
                                       command=self._process_with_claude)
        self.process_btn.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        ttk.Separator(body, orient="horizontal").grid(
            row=8, column=0, columnspan=2, sticky="ew", pady=16)

        # Ask section
        ttk.Label(body, text="Ask Your Meetings",
                  font=("Helvetica", 13, "bold")).grid(
            row=9, column=0, columnspan=2, sticky="w", pady=(0, 4))
        ttk.Label(body,
                  text='e.g. "What action items do I have from this week?"',
                  font=("Helvetica", 10, "italic"), foreground="#555555").grid(
            row=10, column=0, columnspan=2, sticky="w", pady=(0, 6))

        self.question_var = tk.StringVar()
        question_entry = ttk.Entry(body, textvariable=self.question_var,
                                    width=44, font=("Helvetica", 11))
        question_entry.grid(row=11, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        question_entry.bind("<Return>", lambda e: self._ask_claude())

        self.ask_btn = ttk.Button(body, text="Ask Claude", command=self._ask_claude)
        self.ask_btn.grid(row=12, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        # Answer display
        self.answer_box = tk.Text(body, height=12, width=52, state="disabled",
                                   font=("Helvetica", 10), bg="#f0f7ff",
                                   fg="#1a1a1a", relief="flat", wrap="word")
        ans_scroll = ttk.Scrollbar(body, command=self.answer_box.yview)
        self.answer_box.configure(yscrollcommand=ans_scroll.set)
        self.answer_box.grid(row=13, column=0, sticky="nsew")
        ans_scroll.grid(row=13, column=1, sticky="ns")

    # ------------------------------------------------------------------
    # Account management
    # ------------------------------------------------------------------

    def _refresh_accounts(self):
        accounts = get_accounts()
        self.account_box.delete(0, tk.END)
        for a in accounts:
            self.account_box.insert(tk.END, f"  {a}")
        self.export_combo["values"] = accounts
        self.proc_combo["values"]   = accounts
        if accounts:
            if not self.export_var.get():
                self.export_var.set(accounts[0])
            if not self.proc_account_var.get():
                self.proc_account_var.set(accounts[0])

    def _selected_account(self):
        sel = self.account_box.curselection()
        if not sel:
            return None
        return self.account_box.get(sel[0]).strip()

    def _view_account(self, event=None):
        name = self._selected_account()
        if not name:
            messagebox.showinfo("View Account", "Select an account first.", parent=self)
            return
        dlg = AccountDetailDialog(self, name)
        if dlg.new_name:
            self._log(f"Account renamed: '{name}' → '{dlg.new_name}'")
            current = self.export_var.get()
            self._refresh_accounts()
            if current == name:
                self.export_var.set(dlg.new_name)

    def _add_account(self):
        name = simpledialog.askstring(
            "Add Account",
            "Enter a name for this account:\n(e.g.  JG  ·  work  ·  personal)",
            parent=self,
        )
        if not name or not name.strip():
            return
        name = name.strip()

        if session_file(name).exists():
            messagebox.showinfo("Already exists",
                                f"An account named '{name}' is already set up.", parent=self)
            return

        args = [PYTHON, str(MAIN_SCRIPT), "--setup"]
        if name != "default":
            args += ["--account", name]

        self._log(f"Opening Chrome for '{name}' — log in to Plaud, then click OK below.")
        proc = subprocess.Popen(
            args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, cwd=str(SCRIPT_DIR),
        )

        messagebox.showinfo(
            "Log in to Plaud",
            f"A Chrome window has opened.\n\n"
            f"Log in to your '{name}' Plaud account.\n\n"
            f"When you can see your recordings, click OK.",
            parent=self,
        )

        proc.stdin.write(b"\n")
        proc.stdin.flush()
        proc.wait()

        if session_file(name).exists():
            self._log(f"✓ '{name}' account added successfully.")
        else:
            self._log(f"✗ Setup for '{name}' may have failed — session file not found.")

        self._refresh_accounts()
        self.export_var.set(name)

    def _remove_account(self):
        name = self._selected_account()
        if not name:
            messagebox.showinfo("Remove Account", "Select an account first.", parent=self)
            return
        if not messagebox.askyesno(
            "Remove Account",
            f"Remove the '{name}' account?\n\n"
            "This only removes the saved login — your transcripts are kept.",
            parent=self,
        ):
            return
        sf = session_file(name)
        if sf.exists():
            sf.unlink()
        self._log(f"Removed '{name}' account.")
        self._refresh_accounts()

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def _export(self):
        account = self.export_var.get()
        if not account:
            messagebox.showinfo("No account", "Add an account first.", parent=self)
            return
        if not session_file(account).exists():
            messagebox.showinfo("Not logged in",
                                f"No saved login for '{account}'.\nClick Add Account to set it up.",
                                parent=self)
            return

        self.export_btn.configure(state="disabled", text="Exporting…")
        self._log(f"── Exporting '{account}' account ──")
        threading.Thread(target=self._run_export, args=(account,), daemon=True).start()

    def _run_export(self, account):
        args = [PYTHON, str(MAIN_SCRIPT)]
        if account != "default":
            args += ["--account", account]

        proc = subprocess.Popen(
            args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, cwd=str(SCRIPT_DIR),
        )
        for line in proc.stdout:
            text = line.strip()
            if "] " in text:
                text = text.split("] ", 1)[-1]
            if text:
                self._log(text)
        proc.wait()
        self.after(0, lambda: self.export_btn.configure(
            state="normal", text="Export New Transcripts"))
        self._log("── Done ──")

    # ------------------------------------------------------------------
    # Folder
    # ------------------------------------------------------------------

    def _open_folder(self):
        account = self.export_var.get() or "default"
        folder = transcripts_dir(account)
        folder.mkdir(parents=True, exist_ok=True)
        subprocess.run(["open", str(folder)])

    # ------------------------------------------------------------------
    # Claude AI methods
    # ------------------------------------------------------------------

    def _refresh_api_key_status(self):
        if security.get_api_key():
            self.api_key_status.set("✓  API key saved securely in Keychain")
        else:
            self.api_key_status.set("✗  No API key set — add one below to enable Claude features")

    def _set_api_key(self):
        key = simpledialog.askstring(
            "Set Anthropic API Key",
            "Paste your Anthropic API key:\n(stored securely in macOS Keychain — never saved to disk)",
            show="*", parent=self,
        )
        if not key or not key.strip():
            return
        key = key.strip()
        if not key.startswith("sk-"):
            messagebox.showwarning("Invalid key",
                                   "Anthropic API keys start with 'sk-'. Please check and try again.",
                                   parent=self)
            return
        security.set_api_key(key)
        self._refresh_api_key_status()
        self._log("✓ Anthropic API key saved to Keychain.")

    def _remove_api_key(self):
        if not messagebox.askyesno("Remove API Key",
                                    "Remove the Anthropic API key from Keychain?",
                                    parent=self):
            return
        security.delete_api_key()
        self._refresh_api_key_status()
        self._log("Anthropic API key removed.")

    def _process_with_claude(self):
        if not security.get_api_key():
            messagebox.showinfo("No API Key",
                                "Add your Anthropic API key first.", parent=self)
            return
        account = self.proc_account_var.get() or "default"
        self.process_btn.configure(state="disabled", text="Processing…")
        self._log(f"── Processing '{account}' transcripts with Claude ──")
        threading.Thread(target=self._run_processing, args=(account,), daemon=True).start()

    def _run_processing(self, account):
        try:
            import claude_processor
            succeeded, failed = claude_processor.process_all_unprocessed(
                account=account,
                progress_cb=self._log,
            )
            self._log(f"── Done: {succeeded} processed, {failed} failed ──")
        except Exception as exc:
            self._log(f"✗ Processing error: {exc}")
        finally:
            self.after(0, lambda: self.process_btn.configure(
                state="normal", text="Process with Claude"))

    def _ask_claude(self):
        question = self.question_var.get().strip()
        if not question:
            return
        if not security.get_api_key():
            messagebox.showinfo("No API Key",
                                "Add your Anthropic API key first.", parent=self)
            return
        account = self.proc_account_var.get() or "default"
        self.ask_btn.configure(state="disabled", text="Asking…")
        self._set_answer("Thinking…")
        threading.Thread(target=self._run_ask,
                          args=(question, account), daemon=True).start()

    def _run_ask(self, question, account):
        try:
            import claude_processor
            answer = claude_processor.ask(question, account=account)
        except Exception as exc:
            answer = f"Error: {exc}"
        self.after(0, lambda: self._set_answer(answer))
        self.after(0, lambda: self.ask_btn.configure(state="normal", text="Ask Claude"))

    def _set_answer(self, text):
        self.answer_box.configure(state="normal")
        self.answer_box.delete("1.0", tk.END)
        self.answer_box.insert(tk.END, text)
        self.answer_box.configure(state="disabled")

    # ------------------------------------------------------------------
    # Log helpers
    # ------------------------------------------------------------------

    def _log(self, message):
        def _append():
            self.log.configure(state="normal")
            self.log.insert(tk.END, message + "\n")
            self.log.see(tk.END)
            self.log.configure(state="disabled")
        self.after(0, _append)

    def _clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", tk.END)
        self.log.configure(state="disabled")


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = PlaudApp()
    app.mainloop()
