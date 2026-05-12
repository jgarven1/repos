"""
Plaud Transcripts — GUI App
Double-click Plaud.app to open this window.
"""

import pathlib
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

SCRIPT_DIR  = pathlib.Path(__file__).parent
MAIN_SCRIPT = SCRIPT_DIR / "plaud_transcripts.py"
PYTHON      = sys.executable


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_accounts():
    """Return list of configured account names (default account shown as 'default')."""
    accounts = []
    if (SCRIPT_DIR / ".plaud_session.json").exists():
        accounts.append("default")
    for f in sorted(SCRIPT_DIR.glob(".plaud_session_*.json")):
        accounts.append(f.stem[len(".plaud_session_"):])
    return accounts


def session_file(account):
    if account == "default":
        return SCRIPT_DIR / ".plaud_session.json"
    return SCRIPT_DIR / f".plaud_session_{account}.json"


def transcripts_dir(account):
    if account == "default":
        return SCRIPT_DIR / "transcripts"
    return SCRIPT_DIR / f"transcripts_{account}"


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class PlaudApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Plaud Transcripts")
        self.resizable(False, False)
        self._build_ui()
        self._refresh_accounts()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        pad = dict(padx=20, pady=8)

        # ── Header ────────────────────────────────────────────────────
        header = tk.Frame(self, bg="#1a1a1a")
        header.grid(row=0, column=0, sticky="ew")
        tk.Label(
            header, text="🎙  Plaud Transcripts",
            font=("Helvetica", 18, "bold"),
            fg="white", bg="#1a1a1a", pady=16, padx=20,
        ).pack(anchor="w")

        # ── Body ──────────────────────────────────────────────────────
        body = ttk.Frame(self, padding=20)
        body.grid(row=1, column=0, sticky="nsew")

        # Accounts
        ttk.Label(body, text="Accounts", font=("Helvetica", 13, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))

        self.account_box = tk.Listbox(body, height=4, width=38, selectmode="single",
                                       font=("Helvetica", 12))
        self.account_box.grid(row=1, column=0, columnspan=2, sticky="ew")

        acc_btns = ttk.Frame(body)
        acc_btns.grid(row=2, column=0, columnspan=2, sticky="w", pady=(6, 0))
        ttk.Button(acc_btns, text="Add Account",    command=self._add_account).pack(side="left", padx=(0, 6))
        ttk.Button(acc_btns, text="Remove Account", command=self._remove_account).pack(side="left")

        ttk.Separator(body, orient="horizontal").grid(
            row=3, column=0, columnspan=2, sticky="ew", pady=16)

        # Export
        ttk.Label(body, text="Export", font=("Helvetica", 13, "bold")).grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(0, 4))

        ttk.Label(body, text="Account:").grid(row=5, column=0, sticky="w")
        self.export_var = tk.StringVar()
        self.export_combo = ttk.Combobox(body, textvariable=self.export_var,
                                          state="readonly", width=28)
        self.export_combo.grid(row=5, column=1, sticky="ew", padx=(8, 0))

        self.export_btn = ttk.Button(body, text="Export New Transcripts",
                                      command=self._export)
        self.export_btn.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(10, 4))

        ttk.Button(body, text="Open Transcripts Folder",
                   command=self._open_folder).grid(
            row=7, column=0, columnspan=2, sticky="ew")

        ttk.Separator(body, orient="horizontal").grid(
            row=8, column=0, columnspan=2, sticky="ew", pady=16)

        # Log
        ttk.Label(body, text="Activity Log", font=("Helvetica", 13, "bold")).grid(
            row=9, column=0, columnspan=2, sticky="w", pady=(0, 4))

        self.log = tk.Text(body, height=12, width=52, state="disabled",
                           font=("Courier", 10), bg="#f5f5f5", relief="flat")
        scroll = ttk.Scrollbar(body, command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.grid(row=10, column=0, sticky="nsew")
        scroll.grid(row=10, column=1, sticky="ns")

        ttk.Button(body, text="Clear Log", command=self._clear_log).grid(
            row=11, column=0, columnspan=2, sticky="e", pady=(6, 0))

    # ------------------------------------------------------------------
    # Account management
    # ------------------------------------------------------------------

    def _refresh_accounts(self):
        accounts = get_accounts()
        self.account_box.delete(0, tk.END)
        for a in accounts:
            self.account_box.insert(tk.END, f"  {a}")
        self.export_combo["values"] = accounts
        if accounts and not self.export_var.get():
            self.export_var.set(accounts[0])

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

        # Launch setup in background — Chrome opens, user logs in, then
        # clicks OK here which sends Enter to the waiting process.
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

        # Send Enter so the script saves the session and exits
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
        sel = self.account_box.curselection()
        if not sel:
            messagebox.showinfo("Remove Account", "Select an account first.", parent=self)
            return
        name = self.account_box.get(sel[0]).strip()
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
            # Strip the timestamp prefix from log lines
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
