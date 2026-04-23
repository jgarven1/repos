"""
Plaud Menu Bar App
------------------
Sits in the macOS menu bar. Click the 🎙 icon to export new transcripts,
open your transcripts folder, or quit.

Run once from terminal to start it:
    python3 plaud_menu_bar.py

Or double-click Plaud.app (created by running: bash create_app.sh)
"""

import pathlib
import subprocess
import sys
import threading

import rumps

SCRIPT_DIR = pathlib.Path(__file__).parent
TRANSCRIPTS_DIR = SCRIPT_DIR / "transcripts"
EXPORT_SCRIPT = SCRIPT_DIR / "plaud_transcripts.py"
PYTHON = sys.executable


class PlaudApp(rumps.App):
    def __init__(self):
        super().__init__("🎙", quit_button="Quit")
        self._running = False
        self.menu = [
            "Export New Transcripts",
            "Open Transcripts Folder",
            None,
        ]

    # ------------------------------------------------------------------
    # Running state — updates the menu bar icon and menu item title
    # ------------------------------------------------------------------

    def _set_running(self, value):
        self._running = value
        self.title = "🎙⏳" if value else "🎙"
        self.menu["Export New Transcripts"].title = (
            "Exporting… (please wait)" if value else "Export New Transcripts"
        )

    # ------------------------------------------------------------------
    # Menu actions
    # ------------------------------------------------------------------

    @rumps.clicked("Export New Transcripts")
    def export(self, _):
        if self._running:
            rumps.notification(
                "Plaud", "Already running", "Please wait for the current export to finish."
            )
            return
        self._set_running(True)
        threading.Thread(target=self._run_export, daemon=True).start()

    @rumps.clicked("Open Transcripts Folder")
    def open_folder(self, _):
        TRANSCRIPTS_DIR.mkdir(exist_ok=True)
        subprocess.run(["open", str(TRANSCRIPTS_DIR)])

    # ------------------------------------------------------------------
    # Background export
    # ------------------------------------------------------------------

    def _run_export(self):
        try:
            result = subprocess.run(
                [PYTHON, str(EXPORT_SCRIPT)],
                capture_output=True,
                text=True,
                cwd=str(SCRIPT_DIR),
            )
            if result.returncode == 0:
                summary = next(
                    (line.split("] ")[-1] for line in result.stderr.splitlines() if "Done." in line),
                    "Finished.",
                )
                rumps.notification("Plaud ✓", "Export complete", summary)
            else:
                lines = result.stderr.strip().splitlines()
                last = lines[-1].split("] ")[-1] if lines else "Unknown error"
                rumps.notification("Plaud ✗", "Export failed", last)
        except Exception as exc:
            rumps.notification("Plaud ✗", "Error", str(exc))
        finally:
            self._set_running(False)


if __name__ == "__main__":
    PlaudApp().run()
