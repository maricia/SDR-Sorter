import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

# -----------------------------
# App configuration
# -----------------------------
APP_TITLE = "SDR Zip Sorter"
INSTRUCTIONS_PDF = "instructions.pdf"
INSTRUCTIONS_DOC = "instructions.docx"  # must be in same folder as this GUI (or update name)


ODS_SCRIPT = "ODSSDRSorterV4.py"
TESTHOUND_SCRIPT = "TestHoundSDRSorterV4.py"

# Styling colors (tweak if you want)
BG = "#0f172a"         # slate-900
FG = "#e2e8f0"         # slate-200
ACCENT = "#22c55e"     # green-500
ACCENT2 = "#38bdf8"    # sky-400
CARD = "#111827"       # gray-900


def open_path(path: Path):
    """Open a file or folder with default app (Windows/macOS/Linux)."""
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=False)
        else:
            subprocess.run(["xdg-open", str(path)], check=False)
    except Exception as e:
        messagebox.showerror("Open failed", f"Couldn't open:\n{path}\n\nError:\n{e}")


class SDRSorterGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.configure(bg=BG)
        self.geometry("820x420")
        self.minsize(780, 400)

        # Resolve app folder so it runs from anywhere
        self.app_dir = Path(__file__).resolve().parent
        self.ods_script = self.app_dir / ODS_SCRIPT
        self.testhound_script = self.app_dir / TESTHOUND_SCRIPT
        self.instructions_path = self.app_dir / INSTRUCTIONS_DOC

        # State
        self.mode = tk.StringVar(value="ODS")  # "ODS" or "TestHound"
        self.zip_path = tk.StringVar(value="")
        self.out_dir = tk.StringVar(value="")
        self.status = tk.StringVar(value="Select a ZIP and an output folder.")

        # UI
        self._build_styles()
        self._build_layout()

        # Quick validation warnings if scripts missing
        self._startup_checks()

    def _build_styles(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure("TFrame", background=BG)
        style.configure("Card.TFrame", background=CARD)
        style.configure("TLabel", background=BG, foreground=FG, font=("Segoe UI", 10))
        style.configure("Title.TLabel", background=BG, foreground=FG, font=("Segoe UI", 16, "bold"))
        style.configure("Sub.TLabel", background=BG, foreground="#94a3b8", font=("Segoe UI", 10))
        style.configure("Card.TLabel", background=CARD, foreground=FG, font=("Segoe UI", 10))
        style.configure("Status.TLabel", background=BG, foreground="#a7f3d0", font=("Segoe UI", 10))

        style.configure("TButton", font=("Segoe UI", 10), padding=8)
        style.map("TButton",
                  foreground=[("active", FG)],
                  background=[("active", "#1f2937")])

    def _build_layout(self):
        # Header
        header = ttk.Frame(self)
        header.pack(fill="x", padx=18, pady=(14, 8))

        ttk.Label(header, text="SDR Zip Sorter", style="Title.TLabel").pack(anchor="w")
        ttk.Label(header, text="Choose ODS or TestHound, select the SecureVaultBundle ZIP, and pick an output folder.", style="Sub.TLabel").pack(anchor="w", pady=(4, 0))

        # Main card
        card = ttk.Frame(self, style="Card.TFrame")
        card.pack(fill="both", expand=True, padx=18, pady=10)

        # Mode selection row
        mode_row = ttk.Frame(card, style="Card.TFrame")
        mode_row.pack(fill="x", padx=14, pady=(14, 8))

        ttk.Label(mode_row, text="Mode:", style="Card.TLabel").pack(side="left")

        rb1 = ttk.Radiobutton(mode_row, text="ODS", value="ODS", variable=self.mode)
        rb2 = ttk.Radiobutton(mode_row, text="TestHound", value="TestHound", variable=self.mode)
        rb1.pack(side="left", padx=(12, 6))
        rb2.pack(side="left", padx=6)

        # ZIP picker row
        zip_row = ttk.Frame(card, style="Card.TFrame")
        zip_row.pack(fill="x", padx=14, pady=8)

        ttk.Label(zip_row, text="ZIP File:", style="Card.TLabel", width=12).pack(side="left")
        zip_entry = ttk.Entry(zip_row, textvariable=self.zip_path)
        zip_entry.pack(side="left", fill="x", expand=True, padx=8)
        ttk.Button(zip_row, text="Browse…", command=self.pick_zip).pack(side="left")

        # Output picker row
        out_row = ttk.Frame(card, style="Card.TFrame")
        out_row.pack(fill="x", padx=14, pady=8)

        ttk.Label(out_row, text="Output:", style="Card.TLabel", width=12).pack(side="left")
        out_entry = ttk.Entry(out_row, textvariable=self.out_dir)
        out_entry.pack(side="left", fill="x", expand=True, padx=8)
        ttk.Button(out_row, text="Browse…", command=self.pick_output).pack(side="left")

        # Buttons row
        btn_row = ttk.Frame(card, style="Card.TFrame")
        btn_row.pack(fill="x", padx=14, pady=(14, 10))

        ttk.Button(btn_row, text="Run Sorter", command=self.run_sorter).pack(side="left")
        ttk.Button(btn_row, text="Open Output Folder", command=self.open_output).pack(side="left", padx=10)
        ttk.Button(btn_row, text="Open Instructions", command=self.open_instructions).pack(side="left")

        ttk.Button(btn_row, text="Exit", command=self.destroy).pack(side="right")

        # Status + output log window
        status_row = ttk.Frame(self)
        status_row.pack(fill="x", padx=18, pady=(6, 2))
        ttk.Label(status_row, textvariable=self.status, style="Status.TLabel").pack(anchor="w")

        log_frame = ttk.Frame(self)
        log_frame.pack(fill="both", expand=False, padx=18, pady=(2, 14))

        self.log = tk.Text(log_frame, height=7, bg="#0b1220", fg="#e5e7eb", insertbackground="#e5e7eb",
                           relief="flat", wrap="word", font=("Consolas", 9))
        self.log.pack(fill="both", expand=True)
        self._log_line("Ready. Select your ZIP and output folder.")

    def _startup_checks(self):
        missing = []
        if not self.ods_script.exists():
            missing.append(str(self.ods_script.name))
        if not self.testhound_script.exists():
            missing.append(str(self.testhound_script.name))

        if missing:
            self.status.set(f"Missing files in app folder: {', '.join(missing)}")
            self._log_line("WARNING: One or more sorter scripts are missing next to the GUI.")
        else:
            self._log_line("Found sorter scripts next to the GUI. Good to go.")

        if not self.instructions_path.exists():
            self._log_line(f"Note: Instructions doc not found: {self.instructions_path.name} (button will prompt you).")

    def _log_line(self, msg: str):
        self.log.insert("end", msg + "\n")
        self.log.see("end")

    def pick_zip(self):
        path = filedialog.askopenfilename(
            title="Select SecureVaultBundle ZIP",
            filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")]
        )
        if path:
            self.zip_path.set(path)
            self.status.set("ZIP selected. Now select an output folder.")
            self._log_line(f"ZIP: {path}")

    def pick_output(self):
        path = filedialog.askdirectory(title="Select Output Folder")
        if path:
            self.out_dir.set(path)
            self.status.set("Output folder selected. Ready to run.")
            self._log_line(f"Output: {path}")

    def open_output(self):
        out = self.out_dir.get().strip()
        if not out:
            messagebox.showinfo("No output folder", "Select an output folder first.")
            return
        open_path(Path(out))

    def open_instructions(self):
    # Prefer PDF, fall back to DOCX
       pdfs = sorted(self.app_dir.glob("*.pdf"))
       docxs = sorted(self.app_dir.glob("*.docx"))

       if pdfs:
           open_path(pdfs[0])
           return
       if docxs:
           open_path(docxs[0])
           return

       messagebox.showinfo(
          "Instructions not found",
          "No PDF or DOCX instructions were found in the application folder.")



    def run_sorter(self):
        zipf = self.zip_path.get().strip()
        outd = self.out_dir.get().strip()

        if not zipf or not Path(zipf).exists():
            messagebox.showerror("Missing ZIP", "Please select a valid ZIP file.")
            return
        if not outd or not Path(outd).exists():
            messagebox.showerror("Missing Output", "Please select a valid output folder.")
            return

        mode = self.mode.get()
        script = self.ods_script if mode == "ODS" else self.testhound_script

        if not script.exists():
            messagebox.showerror("Missing script", f"Can't find {script.name} next to the GUI.\n\nExpected at:\n{script}")
            return

        self.status.set(f"Running {mode} sorter…")
        self._log_line("")
        self._log_line(f"=== Running {script.name} ===")

        # Use the current Python interpreter running the GUI
        cmd = [sys.executable, str(script), zipf, outd]

        try:
            # Run and capture output
            proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(self.app_dir))
            if proc.stdout:
                self._log_line(proc.stdout.strip())
            if proc.stderr:
                self._log_line("---- STDERR ----")
                self._log_line(proc.stderr.strip())

            if proc.returncode == 0:
                self.status.set(f"Done. {mode} sort complete.")
                self._log_line("=== Complete ===")
            else:
                self.status.set(f"{mode} sorter ended with errors. See log.")
                messagebox.showerror("Sorter error", "The sorter reported an error. See the log window for details.")
        except Exception as e:
            self.status.set("Failed to run sorter.")
            messagebox.showerror("Run failed", str(e))


if __name__ == "__main__":
    app = SDRSorterGUI()
    app.mainloop()
