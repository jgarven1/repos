"""
Premiere AI — GUI
Double-click or run: python3 premiere_gui.py

Pipeline:
  1. Browse to a folder of video files
  2. Transcribe with Whisper (cached, so re-runs are instant)
  3. Enter a natural language editing goal
  4. Claude generates an edit sequence
  5. Export EDL → import into Premiere Pro or DaVinci Resolve
"""

import pathlib
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

import premiere_processor as pp

_KEYCHAIN_SERVICE = "com.premiere-ai"
_KEYCHAIN_USER    = "anthropic_api_key"


# ---------------------------------------------------------------------------
# API key helpers (macOS Keychain via keyring)
# ---------------------------------------------------------------------------

def _get_api_key():
    try:
        import keyring
        return keyring.get_password(_KEYCHAIN_SERVICE, _KEYCHAIN_USER)
    except Exception:
        return None


def _set_api_key(key):
    try:
        import keyring
        keyring.set_password(_KEYCHAIN_SERVICE, _KEYCHAIN_USER, key)
    except Exception:
        pass


def _delete_api_key():
    try:
        import keyring
        keyring.delete_password(_KEYCHAIN_SERVICE, _KEYCHAIN_USER)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class PremiereApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Premiere AI")
        self.resizable(False, False)

        self._video_folder  = None
        self._video_files   = []
        self._transcripts   = []   # [{video_name, segments}]
        self._edit_clips    = []   # last generated edit sequence

        self._build_ui()

    def _build_ui(self):
        # ── Header ────────────────────────────────────────────────────
        header = tk.Frame(self, bg="#1a1a1a")
        header.grid(row=0, column=0, sticky="ew")

        hdr_inner = tk.Frame(header, bg="#1a1a1a")
        hdr_inner.pack(side="left", anchor="w", padx=20, pady=14)
        tk.Label(hdr_inner, text="🎬  Premiere AI",
                 font=("Helvetica", 18, "bold"),
                 fg="white", bg="#1a1a1a").pack(side="left")
        tk.Label(hdr_inner, text="  Edit Sequencer",
                 font=("Helvetica", 13),
                 fg="#00cc44", bg="#1a1a1a").pack(side="left", padx=(8, 0))

        tk.Button(header, text="⚙  API Key", command=self._manage_api_key,
                  bg="#333333", fg="white", relief="flat",
                  font=("Helvetica", 10), cursor="hand2",
                  padx=10, pady=6).pack(side="right", padx=16, pady=10)

        # ── Body ──────────────────────────────────────────────────────
        body = ttk.Frame(self, padding=20)
        body.grid(row=1, column=0, sticky="nsew")

        # ── Section 1: Video Files ────────────────────────────────────
        ttk.Label(body, text="Video Files",
                  font=("Helvetica", 13, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 6))

        folder_row = ttk.Frame(body)
        folder_row.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 6))
        self.folder_var = tk.StringVar(value="No folder selected")
        ttk.Label(folder_row, textvariable=self.folder_var,
                  font=("Helvetica", 10), foreground="#555555",
                  width=42).pack(side="left")
        ttk.Button(folder_row, text="Browse…",
                   command=self._browse_folder).pack(side="right")

        self.file_list = tk.Listbox(
            body, height=6, width=54,
            font=("Courier", 10), bg="#f5f5f5", fg="#1a1a1a",
            selectmode="extended", relief="flat",
        )
        self.file_list.grid(row=2, column=0, columnspan=3, sticky="ew")

        model_row = ttk.Frame(body)
        model_row.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(8, 0))
        ttk.Label(model_row, text="Whisper model:").pack(side="left")
        self.model_var = tk.StringVar(value="base")
        ttk.Combobox(
            model_row, textvariable=self.model_var,
            values=pp.WHISPER_MODELS, state="readonly", width=10,
        ).pack(side="left", padx=(6, 0))
        ttk.Label(model_row,
                  text="  larger = more accurate, slower",
                  foreground="#888888", font=("Helvetica", 9)).pack(side="left", padx=(4, 0))

        self.transcribe_btn = ttk.Button(
            body, text="Transcribe Videos", command=self._transcribe)
        self.transcribe_btn.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(10, 0))

        ttk.Separator(body, orient="horizontal").grid(
            row=5, column=0, columnspan=3, sticky="ew", pady=16)

        # ── Section 2: Edit Prompt ────────────────────────────────────
        ttk.Label(body, text="Edit Prompt",
                  font=("Helvetica", 13, "bold")).grid(
            row=6, column=0, columnspan=3, sticky="w", pady=(0, 4))
        ttk.Label(body,
                  text='e.g. "Create a 3-minute highlight reel of the product demo"',
                  font=("Helvetica", 10, "italic"), foreground="#555555").grid(
            row=7, column=0, columnspan=3, sticky="w", pady=(0, 6))

        self.prompt_text = tk.Text(
            body, height=4, width=54,
            font=("Helvetica", 11), relief="flat",
            bg="#f0f7ff", fg="#1a1a1a", wrap="word",
        )
        self.prompt_text.grid(row=8, column=0, columnspan=3, sticky="ew")

        self.generate_btn = ttk.Button(
            body, text="Generate Edit Sequence", command=self._generate)
        self.generate_btn.grid(row=9, column=0, columnspan=3, sticky="ew", pady=(10, 0))

        ttk.Separator(body, orient="horizontal").grid(
            row=10, column=0, columnspan=3, sticky="ew", pady=16)

        # ── Section 3: Output ─────────────────────────────────────────
        ttk.Label(body, text="Output",
                  font=("Helvetica", 13, "bold")).grid(
            row=11, column=0, columnspan=3, sticky="w", pady=(0, 4))

        self.log = tk.Text(
            body, height=12, width=54, state="disabled",
            font=("Courier", 10), bg="#f5f5f5", fg="#1a1a1a", relief="flat",
        )
        log_scroll = ttk.Scrollbar(body, command=self.log.yview)
        self.log.configure(yscrollcommand=log_scroll.set)
        self.log.grid(row=12, column=0, columnspan=2, sticky="nsew")
        log_scroll.grid(row=12, column=2, sticky="ns")

        export_row = ttk.Frame(body)
        export_row.grid(row=13, column=0, columnspan=3, sticky="ew", pady=(10, 0))

        self.export_edl_btn = ttk.Button(
            export_row, text="Export EDL",
            command=self._export_edl, state="disabled")
        self.export_edl_btn.pack(side="left", padx=(0, 8))

        self.export_summary_btn = ttk.Button(
            export_row, text="Export Summary",
            command=self._export_summary, state="disabled")
        self.export_summary_btn.pack(side="left")

        ttk.Button(export_row, text="Clear Log",
                   command=self._clear_log).pack(side="right")

    # ------------------------------------------------------------------
    # Folder / file scanning
    # ------------------------------------------------------------------

    def _browse_folder(self):
        folder = filedialog.askdirectory(title="Select folder containing video files")
        if not folder:
            return
        self._video_folder = pathlib.Path(folder)
        self.folder_var.set(str(self._video_folder))
        self._scan_folder()

    def _scan_folder(self):
        self._video_files = pp.find_video_files(self._video_folder)
        self.file_list.delete(0, tk.END)
        if not self._video_files:
            self.file_list.insert(tk.END, "  (no video files found)")
            return
        for f in self._video_files:
            tag = "✓ " if pp.is_transcribed(f) else "  "
            self.file_list.insert(tk.END, f"  {tag}{f.name}")
        self._log(f"Found {len(self._video_files)} video file(s) in '{self._video_folder.name}'")

    # ------------------------------------------------------------------
    # Transcription
    # ------------------------------------------------------------------

    def _transcribe(self):
        if not self._video_files:
            messagebox.showinfo("No videos",
                                "Browse to a folder with video files first.", parent=self)
            return
        self.transcribe_btn.configure(state="disabled", text="Transcribing…")
        threading.Thread(
            target=self._run_transcription,
            args=(self.model_var.get(),),
            daemon=True,
        ).start()

    def _run_transcription(self, model):
        self._transcripts = []
        for vp in self._video_files:
            try:
                segs = pp.transcribe_video(vp, model, progress_cb=self._log)
                self._transcripts.append({"video_name": vp.name, "segments": segs})
            except Exception as exc:
                self._log(f"✗ '{vp.name}': {exc}")
        self.after(0, lambda: self.transcribe_btn.configure(
            state="normal", text="Transcribe Videos"))
        self.after(0, self._scan_folder)
        self._log(f"── Transcription done: {len(self._transcripts)} file(s) ready ──")

    # ------------------------------------------------------------------
    # Edit sequence generation
    # ------------------------------------------------------------------

    def _generate(self):
        prompt = self.prompt_text.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showinfo("No prompt", "Enter an editing goal first.", parent=self)
            return
        if not self._transcripts:
            messagebox.showinfo("No transcripts",
                                "Transcribe the videos first.", parent=self)
            return
        api_key = _get_api_key()
        if not api_key:
            messagebox.showinfo("No API Key",
                                "Add your Anthropic API key via ⚙ API Key.", parent=self)
            return
        self.generate_btn.configure(state="disabled", text="Generating…")
        self._log("── Sending transcripts to Claude… ──")
        threading.Thread(
            target=self._run_generate,
            args=(prompt, api_key),
            daemon=True,
        ).start()

    def _run_generate(self, prompt, api_key):
        try:
            clips = pp.generate_edit_sequence(self._transcripts, prompt, api_key)
            self._edit_clips = clips
            self._log(f"✓ Edit sequence: {len(clips)} clip(s)")
            for i, c in enumerate(clips, 1):
                dur = float(c["out_seconds"]) - float(c["in_seconds"])
                self._log(
                    f"  {i}. {c['source_file']}  "
                    f"{pp.fmt_time(float(c['in_seconds']))} → "
                    f"{pp.fmt_time(float(c['out_seconds']))}  ({dur:.1f}s)"
                )
                if c.get("note"):
                    self._log(f"     {c['note']}")
            self.after(0, lambda: self.export_edl_btn.configure(state="normal"))
            self.after(0, lambda: self.export_summary_btn.configure(state="normal"))
        except Exception as exc:
            self._log(f"✗ Error: {exc}")
        finally:
            self.after(0, lambda: self.generate_btn.configure(
                state="normal", text="Generate Edit Sequence"))

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def _export_edl(self):
        if not self._edit_clips:
            return
        out = filedialog.asksaveasfilename(
            title="Save EDL",
            defaultextension=".edl",
            filetypes=[("EDL files", "*.edl"), ("All files", "*.*")],
            initialfile="claude_edit.edl",
        )
        if not out:
            return
        try:
            pp.export_edl(self._edit_clips, out)
            self._log(f"✓ EDL saved → {out}")
        except Exception as exc:
            self._log(f"✗ Export failed: {exc}")

    def _export_summary(self):
        if not self._edit_clips:
            return
        out = filedialog.asksaveasfilename(
            title="Save Summary",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile="claude_edit_summary.txt",
        )
        if not out:
            return
        try:
            pp.export_summary(self._edit_clips, out)
            self._log(f"✓ Summary saved → {out}")
        except Exception as exc:
            self._log(f"✗ Export failed: {exc}")

    # ------------------------------------------------------------------
    # API key management
    # ------------------------------------------------------------------

    def _manage_api_key(self):
        existing = _get_api_key()
        if existing:
            action = messagebox.askquestion(
                "API Key",
                "API key is set ✓\n\nClick Yes to replace it, No to remove it.",
                parent=self,
            )
            if action != "yes":
                _delete_api_key()
                self._log("API key removed.")
                return

        key = simpledialog.askstring(
            "Set Anthropic API Key",
            "Paste your Anthropic API key\n(stored securely in macOS Keychain):",
            show="*", parent=self,
        )
        if not key or not key.strip():
            return
        key = key.strip()
        if not key.startswith("sk-"):
            messagebox.showwarning("Invalid key",
                                   "Anthropic keys start with 'sk-'. Please check and try again.",
                                   parent=self)
            return
        _set_api_key(key)
        self._log("✓ API key saved to Keychain.")

    # ------------------------------------------------------------------
    # Log helpers
    # ------------------------------------------------------------------

    def _log(self, msg):
        def _append():
            self.log.configure(state="normal")
            self.log.insert(tk.END, msg + "\n")
            self.log.see(tk.END)
            self.log.configure(state="disabled")
        self.after(0, _append)

    def _clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", tk.END)
        self.log.configure(state="disabled")


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = PremiereApp()
    app.mainloop()
