#!/usr/bin/env python3
"""
Music Transposition GUI Application

A simple GUI application for uploading PDF sheet music, converting to MusicXML,
and transposing to different keys.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import threading
import os

from cli import run_audiveris, unzip_mxl, parse_musicxml, convert_musicxml_to_pdf
from transpose import transpose_musicxml, KEY_SIGNATURES


class MusicTransposerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Music Transposition Tool")
        self.root.geometry("600x700")
        self.root.resizable(False, False)

        # State variables
        self.pdf_path = None
        self.mxl_path = None
        self.xml_path = None
        self.music_data = None
        self.transposed_xml_path = None  # Track the last transposed file

        # Setup UI
        self.setup_ui()

    def setup_ui(self):
        """Create the user interface."""
        # Header
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        title_label = tk.Label(
            header_frame,
            text="🎵 Music Transposition Tool",
            font=("Arial", 18, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(pady=15)

        # Main content area
        content_frame = tk.Frame(self.root, padx=30, pady=20)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Step 1: Upload PDF
        upload_label = tk.Label(
            content_frame,
            text="Step 1: Upload Sheet Music PDF",
            font=("Arial", 12, "bold")
        )
        upload_label.pack(anchor=tk.W, pady=(0, 10))

        upload_btn_frame = tk.Frame(content_frame)
        upload_btn_frame.pack(fill=tk.X, pady=(0, 5))

        self.upload_btn = tk.Button(
            upload_btn_frame,
            text="📁 Choose PDF File",
            command=self.upload_pdf,
            bg="#3498db",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=10,
            cursor="hand2"
        )
        self.upload_btn.pack(side=tk.LEFT)

        self.file_label = tk.Label(
            upload_btn_frame,
            text="No file selected",
            font=("Arial", 9),
            fg="#7f8c8d"
        )
        self.file_label.pack(side=tk.LEFT, padx=10)

        # Processing status
        self.status_label = tk.Label(
            content_frame,
            text="",
            font=("Arial", 9),
            fg="#27ae60"
        )
        self.status_label.pack(anchor=tk.W, pady=(5, 15))

        # Separator
        separator1 = ttk.Separator(content_frame, orient='horizontal')
        separator1.pack(fill=tk.X, pady=15)

        # Step 2: Current Key Display
        key_info_label = tk.Label(
            content_frame,
            text="Step 2: Current Key Information",
            font=("Arial", 12, "bold")
        )
        key_info_label.pack(anchor=tk.W, pady=(0, 10))

        key_info_frame = tk.Frame(content_frame, bg="#ecf0f1", relief=tk.RIDGE, borderwidth=2)
        key_info_frame.pack(fill=tk.X, pady=(0, 15))

        self.current_key_label = tk.Label(
            key_info_frame,
            text="Current Key: Not loaded",
            font=("Arial", 11),
            bg="#ecf0f1",
            pady=10
        )
        self.current_key_label.pack()

        self.time_sig_label = tk.Label(
            key_info_frame,
            text="Time Signature: N/A",
            font=("Arial", 9),
            bg="#ecf0f1",
            fg="#7f8c8d"
        )
        self.time_sig_label.pack(pady=(0, 5))

        self.part_label = tk.Label(
            key_info_frame,
            text="Part: N/A",
            font=("Arial", 9),
            bg="#ecf0f1",
            fg="#7f8c8d"
        )
        self.part_label.pack(pady=(0, 10))

        # Separator
        separator2 = ttk.Separator(content_frame, orient='horizontal')
        separator2.pack(fill=tk.X, pady=15)

        # Step 3: Transpose Selection
        transpose_label = tk.Label(
            content_frame,
            text="Step 3: Select Target Key",
            font=("Arial", 12, "bold")
        )
        transpose_label.pack(anchor=tk.W, pady=(0, 10))

        transpose_frame = tk.Frame(content_frame)
        transpose_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            transpose_frame,
            text="Transpose to:",
            font=("Arial", 10)
        ).pack(side=tk.LEFT, padx=(0, 10))

        # Create dropdown with all keys
        self.key_var = tk.StringVar()
        self.key_options = self.create_key_options()
        self.key_dropdown = ttk.Combobox(
            transpose_frame,
            textvariable=self.key_var,
            values=self.key_options,
            state="readonly",
            width=25,
            font=("Arial", 10)
        )
        self.key_dropdown.pack(side=tk.LEFT)
        self.key_dropdown.set("Select a key...")

        # Buttons frame
        buttons_frame = tk.Frame(content_frame)
        buttons_frame.pack(pady=20)

        # Transpose button
        self.transpose_btn = tk.Button(
            buttons_frame,
            text="🎼 Transpose Music",
            command=self.transpose_music,
            bg="#27ae60",
            fg="white",
            font=("Arial", 11, "bold"),
            padx=30,
            pady=12,
            cursor="hand2",
            state=tk.DISABLED
        )
        self.transpose_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Convert to PDF button
        self.pdf_btn = tk.Button(
            buttons_frame,
            text="📄 Convert to PDF",
            command=self.convert_to_pdf,
            bg="#e67e22",
            fg="white",
            font=("Arial", 11, "bold"),
            padx=30,
            pady=12,
            cursor="hand2",
            state=tk.DISABLED
        )
        self.pdf_btn.pack(side=tk.LEFT)

        # Progress/Result label
        self.result_label = tk.Label(
            content_frame,
            text="",
            font=("Arial", 9),
            fg="#27ae60",
            wraplength=500
        )
        self.result_label.pack()

    def create_key_options(self):
        """Create formatted list of key options for dropdown."""
        options = []
        self.key_mapping = {}  # Map display string to fifths value

        for fifths in range(-7, 8):
            key_info = KEY_SIGNATURES[fifths]
            key_name = key_info[0]
            accidental = key_info[1]
            count = key_info[2]

            if accidental == 'sharp':
                display = f"{key_name} major ({count} sharps)"
            elif accidental == 'flat':
                display = f"{key_name} major ({count} flats)"
            else:
                display = f"{key_name} major"

            options.append(display)
            self.key_mapping[display] = fifths

        return options

    def upload_pdf(self):
        """Handle PDF file upload."""
        file_path = filedialog.askopenfilename(
            title="Select Sheet Music PDF",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )

        if file_path:
            self.pdf_path = file_path
            filename = Path(file_path).name
            self.file_label.config(text=filename, fg="#2c3e50")
            self.status_label.config(text="⏳ Processing PDF...", fg="#f39c12")
            self.upload_btn.config(state=tk.DISABLED)

            # Process in background thread
            thread = threading.Thread(target=self.process_pdf)
            thread.daemon = True
            thread.start()

    def process_pdf(self):
        """Process PDF through Audiveris, unzip, and parse."""
        try:
            # Step 1: Run Audiveris
            self.update_status("⏳ Converting PDF to MusicXML with Audiveris...")
            run_audiveris(self.pdf_path)

            # Find the generated MXL file
            pdf_path = Path(self.pdf_path)
            self.mxl_path = str(pdf_path.with_suffix('.mxl'))

            if not Path(self.mxl_path).exists():
                raise FileNotFoundError("Audiveris did not generate MXL file")

            # Step 2: Unzip MXL
            self.update_status("⏳ Extracting MusicXML archive...")
            unzipped_dir = unzip_mxl(self.mxl_path)

            # Find the XML file inside
            xml_files = list(Path(unzipped_dir).rglob("*.xml"))
            if not xml_files:
                raise FileNotFoundError("No XML file found in MXL archive")

            self.xml_path = str(xml_files[0])

            # Step 3: Parse MusicXML
            self.update_status("⏳ Parsing MusicXML data...")
            self.music_data = parse_musicxml(self.xml_path)

            # Update UI with results
            self.root.after(0, self.display_music_info)

        except Exception as e:
            self.root.after(0, lambda: self.show_error(str(e)))

    def update_status(self, message):
        """Update status label (thread-safe)."""
        self.root.after(0, lambda: self.status_label.config(text=message))

    def display_music_info(self):
        """Display parsed music information in UI."""
        if self.music_data.key_signature is not None:
            key_info = KEY_SIGNATURES[self.music_data.key_signature]
            key_name = key_info[0]
            accidental = key_info[1]
            count = key_info[2]

            if accidental == 'sharp':
                key_display = f"{key_name} major ({count} sharps)"
            elif accidental == 'flat':
                key_display = f"{key_name} major ({count} flats)"
            else:
                key_display = f"{key_name} major"

            self.current_key_label.config(
                text=f"Current Key: {key_display}",
                fg="#2c3e50"
            )
        else:
            self.current_key_label.config(text="Current Key: Unknown")

        # Time signature
        if self.music_data.time_signature:
            time_sig = f"{self.music_data.time_signature[0]}/{self.music_data.time_signature[1]}"
            self.time_sig_label.config(text=f"Time Signature: {time_sig}")

        # Part name
        if self.music_data.part_name:
            self.part_label.config(text=f"Part: {self.music_data.part_name}")

        # Enable transpose button
        self.transpose_btn.config(state=tk.NORMAL)
        self.upload_btn.config(state=tk.NORMAL)
        self.status_label.config(text="✅ Ready to transpose!", fg="#27ae60")

    def transpose_music(self):
        """Handle transposition."""
        if not self.music_data:
            messagebox.showerror("Error", "No music data loaded")
            return

        # Get selected key
        selected = self.key_var.get()
        if selected == "Select a key...":
            messagebox.showwarning("Warning", "Please select a target key")
            return

        # Find the fifths value for selected key
        target_fifths = self.key_mapping.get(selected)

        if target_fifths is None:
            messagebox.showerror("Error", "Invalid key selection")
            return

        # Check if same key
        if target_fifths == self.music_data.key_signature:
            messagebox.showinfo("Info", "Music is already in the selected key!")
            return

        # Disable button during processing
        self.transpose_btn.config(state=tk.DISABLED)
        self.result_label.config(text="⏳ Transposing...", fg="#f39c12")

        # Transpose in background
        def do_transpose():
            try:
                output_path = transpose_musicxml(self.music_data, target_fifths)
                self.root.after(0, lambda: self.show_transpose_success(output_path))
            except Exception as e:
                self.root.after(0, lambda: self.show_error(f"Transposition failed: {e}"))

        thread = threading.Thread(target=do_transpose)
        thread.daemon = True
        thread.start()

    def show_transpose_success(self, output_path):
        """Display success message after transposition."""
        self.transpose_btn.config(state=tk.NORMAL)
        self.pdf_btn.config(state=tk.NORMAL)  # Enable PDF conversion
        self.transposed_xml_path = output_path  # Store for PDF conversion

        filename = Path(output_path).name
        self.result_label.config(
            text=f"✅ Success! Transposed file saved as:\n{filename}",
            fg="#27ae60"
        )
        messagebox.showinfo(
            "Success",
            f"Music transposed successfully!\n\nOutput file:\n{output_path}"
        )

    def convert_to_pdf(self):
        """Convert the transposed MusicXML to PDF."""
        if not self.transposed_xml_path:
            messagebox.showerror("Error", "No transposed music file available")
            return

        # Disable button during processing
        self.pdf_btn.config(state=tk.DISABLED)
        self.result_label.config(text="⏳ Converting to PDF...", fg="#f39c12")

        # Convert in background
        def do_convert():
            try:
                pdf_path = convert_musicxml_to_pdf(self.transposed_xml_path)
                self.root.after(0, lambda: self.show_pdf_success(pdf_path))
            except Exception as e:
                self.root.after(0, lambda: self.show_error(f"PDF conversion failed: {e}"))

        thread = threading.Thread(target=do_convert)
        thread.daemon = True
        thread.start()

    def show_pdf_success(self, pdf_path):
        """Display success message after PDF conversion."""
        self.pdf_btn.config(state=tk.NORMAL)
        filename = Path(pdf_path).name
        self.result_label.config(
            text=f"✅ PDF created successfully:\n{filename}",
            fg="#27ae60"
        )

        # Ask if user wants to open the PDF
        response = messagebox.askyesno(
            "Success",
            f"PDF created successfully!\n\n{pdf_path}\n\nWould you like to open it?"
        )

        if response:
            # Open PDF with default application
            import subprocess
            subprocess.run(["open", pdf_path])  # macOS command

    def show_error(self, error_message):
        """Display error message."""
        self.upload_btn.config(state=tk.NORMAL)
        self.transpose_btn.config(state=tk.DISABLED)
        self.status_label.config(text="❌ Error occurred", fg="#e74c3c")
        self.result_label.config(text="", fg="#e74c3c")
        messagebox.showerror("Error", error_message)


def main():
    """Launch the GUI application."""
    root = tk.Tk()
    app = MusicTransposerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
