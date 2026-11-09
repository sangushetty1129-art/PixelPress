import os
import io
import json
import threading
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk
from PIL import Image, ImageTk, ImageOps
APP_NAME = "PixelPress"
DEVELOPER = "Sangamesh"
GITHUB_URL = "https://github.com/sangushetty1129-art"

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
HISTORY_FILE = os.path.join(os.path.expanduser("~"), ".pixelpress_history.json")


class PixelPressApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("1180x800")
        self.root.minsize(960, 680)

        self.files = []
        self.current_preview_path = None
        self.original_preview_photo = None
        self.compressed_preview_photo = None
        self.preview_output = None
        self.busy = False

        self.quality = tk.IntVar(value=75)
        self.resize_enabled = tk.BooleanVar(value=False)
        self.resize_width = tk.StringVar(value="1920")
        self.resize_height = tk.StringVar(value="1080")
        self.keep_aspect = tk.BooleanVar(value=True)
        self.output_format = tk.StringVar(value="Keep original")
        self.preset = tk.StringVar(value="Balanced")
        self.target_size_kb = tk.StringVar(value="500")
        self.target_enabled = tk.BooleanVar(value=False)
        self.preserve_metadata = tk.BooleanVar(value=True)
        self.output_dir = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Downloads", "PixelPress"))
        self.overwrite = tk.BooleanVar(value=False)
        self.theme = tk.StringVar(value="Dark")

        self.setup_theme()
        self.build_ui()
        self.refresh_file_list()
        self.load_history()

    def setup_theme(self):
        ctk.set_appearance_mode(self.theme.get())
        ctk.set_default_color_theme("blue")

    def build_ui(self):
        # Header
        header = ctk.CTkFrame(self.root, corner_radius=0)
        header.pack(fill="x")

        ctk.CTkLabel(
            header,
            text="PixelPress",
            font=ctk.CTkFont(size=27, weight="bold")
        ).pack(side="left", padx=22, pady=12)

        ctk.CTkLabel(
            header,
            text="Image compression • conversion • resizing",
            text_color=("gray40", "gray70")
        ).pack(side="left", padx=8)

        self.theme_button = ctk.CTkButton(
            header,
            text="Toggle Light / Dark",
            width=145,
            command=self.toggle_theme
        )
        self.theme_button.pack(side="right", padx=18, pady=10)

        # Main container
        main = ctk.CTkFrame(self.root)
        main.pack(fill="both", expand=True, padx=10, pady=10)

        # Left panel
        left = ctk.CTkFrame(main, width=320)
        left.pack(side="left", fill="y", padx=(0, 8), pady=5)
        left.pack_propagate(False)

        ctk.CTkLabel(
            left,
            text="Images",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w", padx=12, pady=(12, 5))

        ctk.CTkLabel(
            left,
            text="Add images or folders. Drag and drop is supported when installed.",
            wraplength=280,
            justify="left",
            text_color=("gray40", "gray70")
        ).pack(anchor="w", padx=12, pady=(0, 8))

        button_row = ctk.CTkFrame(left, fg_color="transparent")
        button_row.pack(fill="x", padx=8, pady=4)

        ctk.CTkButton(
            button_row,
            text="Add Images",
            command=self.add_images
        ).pack(side="left", fill="x", expand=True, padx=3)

        ctk.CTkButton(
            button_row,
            text="Add Folder",
            command=self.add_folder,
            fg_color="gray"
        ).pack(side="left", fill="x", expand=True, padx=3)

        self.file_list = tk.Listbox(
            left,
            selectmode=tk.EXTENDED,
            activestyle="dotbox"
        )
        self.file_list.pack(fill="both", expand=True, padx=10, pady=8)
        self.file_list.bind("<<ListboxSelect>>", self.on_file_select)

        if DND_AVAILABLE:
            try:
                self.file_list.drop_target_register(DND_FILES)
                self.file_list.dnd_bind("<<Drop>>", self.on_drop)
            except Exception:
                pass

        ctk.CTkButton(
            left,
            text="Remove Selected",
            command=self.remove_selected,
            fg_color="gray"
        ).pack(fill="x", padx=10, pady=4)

        ctk.CTkButton(
            left,
            text="Clear List",
            command=self.clear_files,
            fg_color="#9b3d3d",
            hover_color="#7d3030"
        ).pack(fill="x", padx=10, pady=(4, 10))

        # Right panel
        right = ctk.CTkFrame(main)
        right.pack(side="left", fill="both", expand=True, pady=5)

        # Scrollable content: preview, settings and output folder
        content = ctk.CTkScrollableFrame(right)
        content.pack(fill="both", expand=True, padx=6, pady=(6, 4))

        # Preview
        preview_frame = ctk.CTkFrame(content)
        preview_frame.pack(fill="x", padx=4, pady=4)

        ctk.CTkLabel(
            preview_frame,
            text="Preview",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w", padx=12, pady=8)

        previews = ctk.CTkFrame(preview_frame, fg_color="transparent")
        previews.pack(fill="x", padx=6, pady=4)

        original_box = ctk.CTkFrame(previews)
        original_box.pack(side="left", fill="both", expand=True, padx=4)

        compressed_box = ctk.CTkFrame(previews)
        compressed_box.pack(side="left", fill="both", expand=True, padx=4)

        ctk.CTkLabel(original_box, text="Original").pack(pady=4)

        ctk.CTkLabel(
            compressed_box,
            text="Compressed / output preview"
        ).pack(pady=4)

        self.original_preview = ctk.CTkLabel(
            original_box,
            text="Select an image",
            height=160
        )
        self.original_preview.pack(fill="both", expand=True, padx=5, pady=5)

        self.compressed_preview = ctk.CTkLabel(
            compressed_box,
            text="Compress to generate preview",
            height=160
        )
        self.compressed_preview.pack(fill="both", expand=True, padx=5, pady=5)

        self.stats_label = ctk.CTkLabel(
            preview_frame,
            text="Add images to begin.",
            justify="left"
        )
        self.stats_label.pack(anchor="w", padx=12, pady=8)

        # Settings
        settings = ctk.CTkFrame(content)
        settings.pack(fill="x", padx=4, pady=5)

        settings_left = ctk.CTkFrame(settings, fg_color="transparent")
        settings_left.pack(side="left", fill="both", expand=True, padx=8, pady=8)

        settings_right = ctk.CTkFrame(settings, fg_color="transparent")
        settings_right.pack(side="left", fill="both", expand=True, padx=8, pady=8)

        # Compression settings
        ctk.CTkLabel(
            settings_left,
            text="Compression",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w")

        ctk.CTkLabel(settings_left, text="Preset").pack(anchor="w", pady=(5, 0))

        self.preset_menu = ctk.CTkOptionMenu(
            settings_left,
            values=["Smallest", "Balanced", "High quality", "Custom"],
            variable=self.preset,
            command=self.apply_preset
        )
        self.preset_menu.pack(fill="x", pady=3)

        ctk.CTkLabel(
            settings_left,
            text="JPEG / WebP quality"
        ).pack(anchor="w", pady=(4, 0))

        self.quality_slider = ctk.CTkSlider(
            settings_left,
            from_=10,
            to=100,
            number_of_steps=90,
            variable=self.quality
        )
        self.quality_slider.bind(
            "<ButtonRelease-1>",
            self.set_custom_preset
        )
        self.quality_slider.pack(fill="x", pady=4)

        self.quality_text = ctk.CTkLabel(
            settings_left,
            text=str(self.quality.get())
        )
        self.quality_text.pack(anchor="e")

        self.quality.trace_add(
            "write",
            lambda *_: self.quality_text.configure(
                text=str(self.quality.get())
            )
        )

        ctk.CTkCheckBox(
            settings_left,
            text="Target file size (JPEG/WebP)",
            variable=self.target_enabled
        ).pack(anchor="w", pady=(5, 0))

        target_row = ctk.CTkFrame(
            settings_left,
            fg_color="transparent"
        )
        target_row.pack(fill="x", pady=3)

        ctk.CTkEntry(
            target_row,
            textvariable=self.target_size_kb,
            width=100
        ).pack(side="left")

        ctk.CTkLabel(
            target_row,
            text="KB (approx.)"
        ).pack(side="left", padx=8)

        # Output and resizing
        ctk.CTkLabel(
            settings_right,
            text="Output & Resize",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w")

        ctk.CTkLabel(
            settings_right,
            text="Output format"
        ).pack(anchor="w", pady=(5, 0))

        ctk.CTkOptionMenu(
            settings_right,
            variable=self.output_format,
            values=["Keep original", "JPEG", "PNG", "WebP", "BMP"]
        ).pack(fill="x", pady=3)

        ctk.CTkCheckBox(
            settings_right,
            text="Resize images",
            variable=self.resize_enabled,
            command=self.toggle_resize
        ).pack(anchor="w", pady=(5, 0))

        size_row = ctk.CTkFrame(
            settings_right,
            fg_color="transparent"
        )
        size_row.pack(fill="x", pady=3)

        ctk.CTkEntry(
            size_row,
            textvariable=self.resize_width,
            width=75,
            placeholder_text="Width"
        ).pack(side="left")

        ctk.CTkLabel(size_row, text="×").pack(side="left", padx=4)

        ctk.CTkEntry(
            size_row,
            textvariable=self.resize_height,
            width=75,
            placeholder_text="Height"
        ).pack(side="left")

        ctk.CTkCheckBox(
            settings_right,
            text="Keep aspect ratio",
            variable=self.keep_aspect
        ).pack(anchor="w", pady=2)

        ctk.CTkCheckBox(
            settings_right,
            text="Preserve metadata when possible",
            variable=self.preserve_metadata
        ).pack(anchor="w", pady=2)

        # Output folder
        output_frame = ctk.CTkFrame(content)
        output_frame.pack(fill="x", padx=4, pady=5)

        ctk.CTkLabel(
            output_frame,
            text="Output folder"
        ).pack(side="left", padx=8)

        ctk.CTkEntry(
            output_frame,
            textvariable=self.output_dir
        ).pack(side="left", fill="x", expand=True, padx=5, pady=8)

        ctk.CTkButton(
            output_frame,
            text="Browse",
            width=80,
            command=self.choose_output_dir
        ).pack(side="right", padx=8)

        # Fixed bottom panel: always visible
        bottom = ctk.CTkFrame(right)
        bottom.pack(fill="x", padx=6, pady=(4, 6))

        self.progress = ctk.CTkProgressBar(bottom)
        self.progress.pack(fill="x", padx=10, pady=(8, 3))
        self.progress.set(0)

        self.status = ctk.CTkLabel(
            bottom,
            text="Ready",
            anchor="w"
        )
        self.status.pack(fill="x", padx=10, pady=3)

        action_row = ctk.CTkFrame(
            bottom,
            fg_color="transparent"
        )
        action_row.pack(fill="x", padx=6, pady=6)

        self.compress_button = ctk.CTkButton(
            action_row,
            text="Compress All",
            command=self.start_compression,
            height=36
        )
        self.compress_button.pack(
            side="left",
            fill="x",
            expand=True,
            padx=3
        )

        ctk.CTkButton(
            action_row,
            text="Open Output Folder",
            command=self.open_output_folder,
            fg_color="gray",
            height=36
        ).pack(
            side="left",
            fill="x",
            expand=True,
            padx=3
        )

        ctk.CTkButton(
            action_row,
            text="View History",
            command=self.show_history,
            fg_color="gray",
            height=36
        ).pack(
            side="left",
            fill="x",
            expand=True,
            padx=3
        )

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def toggle_theme(self):
        self.theme.set("Light" if self.theme.get() == "Dark" else "Dark")
        ctk.set_appearance_mode(self.theme.get())

    def add_images(self):
        paths = filedialog.askopenfilenames(title="Select images", filetypes=[("Image files", "*.jpg *.jpeg *.png *.webp *.bmp *.tif *.tiff")])
        self.add_paths(paths)

    def add_folder(self):
        folder = filedialog.askdirectory(title="Select folder containing images")
        if not folder:
            return
        paths = []
        for root, _, filenames in os.walk(folder):
            for name in filenames:
                if os.path.splitext(name)[1].lower() in SUPPORTED_EXTENSIONS:
                    paths.append(os.path.join(root, name))
        self.add_paths(paths)

    def on_drop(self, event):
        try:
            paths = self.root.tk.splitlist(event.data)
            self.add_paths(paths)
        except Exception as exc:
            self.set_status(f"Could not read dropped files: {exc}")

    def add_paths(self, paths):
        added = 0
        for path in paths:
            path = os.path.abspath(path)
            if os.path.isfile(path) and os.path.splitext(path)[1].lower() in SUPPORTED_EXTENSIONS and path not in self.files:
                self.files.append(path)
                added += 1
        self.refresh_file_list()
        if self.files and added:
            self.file_list.selection_clear(0, tk.END)
            self.file_list.selection_set(0)
            self.on_file_select()
        self.set_status(f"Added {added} image(s). Total: {len(self.files)}")

    def refresh_file_list(self):
        self.file_list.delete(0, tk.END)
        for path in self.files:
            self.file_list.insert(tk.END, os.path.basename(path))

    def on_file_select(self, _event=None):
        selection = self.file_list.curselection()
        if not selection:
            return
        path = self.files[selection[0]]
        self.current_preview_path = path
        try:
            image = Image.open(path)
            self.display_preview(image, self.original_preview)
            self.compressed_preview.configure(image=None, text="Compress to generate preview")
            self.compressed_preview.image = None
            size_mb = os.path.getsize(path) / (1024 * 1024)
            self.stats_label.configure(text=f"Selected: {os.path.basename(path)}  |  {image.width} × {image.height}  |  {size_mb:.3f} MB")
        except Exception as exc:
            self.set_status(f"Preview error: {exc}")

    def display_preview(self, image, widget):
        image = ImageOps.exif_transpose(image.copy())
        image.thumbnail((430, 300), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(image)
        widget.configure(image=photo, text="")
        widget.image = photo
        return photo

    def remove_selected(self):
        indices = list(self.file_list.curselection())
        for index in reversed(indices):
            del self.files[index]
        self.refresh_file_list()
        self.set_status("Removed selected files.")

    def clear_files(self):
        self.files.clear()
        self.refresh_file_list()
        self.original_preview.configure(image=None, text="Select an image")
        self.original_preview.image = None
        self.compressed_preview.configure(image=None, text="Preview appears after compressing")
        self.compressed_preview.image = None
        self.stats_label.configure(text="Add images to begin.")
        self.set_status("Image list cleared.")

    def apply_preset(self, value):
        mapping = {"Smallest": 35, "Balanced": 75, "High quality": 92}
        if value in mapping:
            self.quality.set(mapping[value])

    def set_custom_preset(self, _value=None):
        if self.preset.get() != "Custom":
            self.preset.set("Custom")

    def toggle_resize(self):
        self.set_status("Resize enabled." if self.resize_enabled.get() else "Resize disabled.")

    def choose_output_dir(self):
        folder = filedialog.askdirectory(title="Choose output folder")
        if folder:
            self.output_dir.set(folder)

    def open_output_folder(self):
        folder = self.output_dir.get()
        os.makedirs(folder, exist_ok=True)
        try:
            os.startfile(folder)
        except Exception:
            messagebox.showinfo("Output folder", folder)

    def get_output_extension(self, source):
        selected = self.output_format.get()
        if selected == "Keep original":
            return os.path.splitext(source)[1].lower()
        return {"JPEG": ".jpg", "PNG": ".png", "WebP": ".webp", "BMP": ".bmp"}[selected]

    def prepare_image(self, source):
        image = Image.open(source)
        image = ImageOps.exif_transpose(image)
        if self.resize_enabled.get():
            try:
                width = int(self.resize_width.get())
                height = int(self.resize_height.get())
                if width <= 0 or height <= 0:
                    raise ValueError("Width and height must be positive.")
            except ValueError as exc:
                raise ValueError("Enter valid positive width and height.") from exc
            if self.keep_aspect.get():
                image.thumbnail((width, height), Image.Resampling.LANCZOS)
            else:
                image = image.resize((width, height), Image.Resampling.LANCZOS)
        return image

    def encode_image(self, image, fmt, quality, source_path):
        fmt = fmt.upper()
        output = io.BytesIO()
        save_kwargs = {}

        if fmt in ("JPEG", "JPG"):
            if image.mode not in ("RGB", "L"):
                image = image.convert("RGB")
            save_kwargs = {"quality": quality, "optimize": True}
            if self.preserve_metadata.get():
                try:
                    exif = Image.open(source_path).getexif()
                    if exif:
                        save_kwargs["exif"] = exif.tobytes()
                except Exception:
                    pass
            image.save(output, format="JPEG", **save_kwargs)
        elif fmt == "WEBP":
            if image.mode not in ("RGB", "RGBA"):
                image = image.convert("RGBA" if "A" in image.getbands() else "RGB")
            image.save(output, format="WEBP", quality=quality, method=6)
        elif fmt == "PNG":
            image.save(output, format="PNG", optimize=True)
        elif fmt == "BMP":
            if image.mode not in ("RGB", "RGBA"):
                image = image.convert("RGB")
            image.save(output, format="BMP")
        elif fmt in ("TIFF", "TIF"):
            image.save(output, format="TIFF")
        else:
            image.save(output, format=fmt)
        return output.getvalue()

    def compress_one(self, source):
        image = self.prepare_image(source)
        ext = self.get_output_extension(source)
        fmt = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".webp": "WEBP", ".bmp": "BMP", ".tif": "TIFF", ".tiff": "TIFF"}.get(ext, "JPEG")
        quality = int(self.quality.get())
        data = self.encode_image(image, fmt, quality, source)

        if self.target_enabled.get() and fmt in ("JPEG", "WEBP"):
            try:
                target_bytes = int(self.target_size_kb.get()) * 1024
                if target_bytes <= 0:
                    raise ValueError
                # Try lower quality values to approach target size. This is approximate.
                for q in range(quality - 5, 9, -5):
                    candidate = self.encode_image(image, fmt, q, source)
                    data = candidate
                    quality = q
                    if len(candidate) <= target_bytes:
                        break
            except ValueError:
                raise ValueError("Target size must be a positive number of KB.")

        output_dir = self.output_dir.get().strip()
        if not output_dir:
            raise ValueError("Please choose an output folder.")
        os.makedirs(output_dir, exist_ok=True)

        base = os.path.splitext(os.path.basename(source))[0]
        out_path = os.path.join(output_dir, f"{base}_compressed{ext}")
        if os.path.abspath(out_path) == os.path.abspath(source):
            out_path = os.path.join(output_dir, f"{base}_compressed_2{ext}")
        if os.path.exists(out_path):
            counter = 2
            while os.path.exists(os.path.join(output_dir, f"{base}_compressed_{counter}{ext}")):
                counter += 1
            out_path = os.path.join(output_dir, f"{base}_compressed_{counter}{ext}")

        with open(out_path, "wb") as f:
            f.write(data)
        return out_path, len(data), quality

    def start_compression(self):
        if self.busy:
            return
        if not self.files:
            messagebox.showwarning("No images", "Add at least one image first.")
            return
        self.busy = True
        self.compress_button.configure(state="disabled")
        self.progress.set(0)
        thread = threading.Thread(target=self.compression_worker, daemon=True)
        thread.start()

    def compression_worker(self):
        results = []
        errors = []
        total = len(self.files)
        for index, path in enumerate(list(self.files), start=1):
            try:
                out_path, size, used_quality = self.compress_one(path)
                results.append((path, out_path, size, used_quality))
                self.add_history(path, out_path, size)
                if path == self.current_preview_path:
                    self.root.after(0, self.update_compressed_preview, out_path)
            except Exception as exc:
                errors.append(f"{os.path.basename(path)}: {exc}")
            self.root.after(0, self.progress.set, index / total)
            self.root.after(0, self.set_status, f"Processing {index}/{total}: {os.path.basename(path)}")

        self.root.after(0, self.compression_finished, results, errors)

    def update_compressed_preview(self, path):
        try:
            image = Image.open(path)
            self.display_preview(image, self.compressed_preview)
            original_size = os.path.getsize(self.current_preview_path)
            new_size = os.path.getsize(path)
            savings = (original_size - new_size) / original_size * 100 if original_size else 0
            self.stats_label.configure(
                text=f"Original: {original_size / 1024 / 1024:.3f} MB  |  Output: {new_size / 1024 / 1024:.3f} MB  |  Savings: {savings:.1f}%"
            )
        except Exception as exc:
            self.set_status(f"Preview update failed: {exc}")

    def compression_finished(self, results, errors):
        self.busy = False
        self.compress_button.configure(state="normal")
        self.progress.set(1 if results else 0)
        summary = f"Finished: {len(results)} image(s) compressed."
        if errors:
            summary += f" {len(errors)} failed."
        self.set_status(summary)
        if errors:
            messagebox.showwarning("Completed with errors", summary + "\n\n" + "\n".join(errors[:10]))
        else:
            messagebox.showinfo("Compression complete", summary + f"\n\nOutput folder:\n{self.output_dir.get()}")

    def set_status(self, text):
        self.status.configure(text=text)

    def add_history(self, source, output, size):
        try:
            history = []
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    history = json.load(f)
            history.insert(0, {
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "source": source,
                "output": output,
                "output_bytes": size
            })
            history = history[:100]
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2)
        except Exception:
            pass

    def load_history(self):
        # History is read when the history window is opened.
        pass

    def show_history(self):
        window = ctk.CTkToplevel(self.root)
        window.title("Compression History")
        window.geometry("800x450")
        ctk.CTkLabel(window, text="Recent compression history", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
        box = tk.Listbox(window, height=18)
        box.pack(fill="both", expand=True, padx=12, pady=8)
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
            for item in history:
                box.insert(tk.END, f"{item.get('date')} | {os.path.basename(item.get('source', ''))} → {os.path.basename(item.get('output', ''))} | {item.get('output_bytes', 0) / 1024:.1f} KB")
        except Exception:
            box.insert(tk.END, "No history available yet.")

    def on_close(self):
        self.root.destroy()


def main():
    if DND_AVAILABLE:
        class CTkDND(ctk.CTk, TkinterDnD.DnDWrapper):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.TkdndVersion = TkinterDnD._require(self)

        root = CTkDND()
    else:
        root = ctk.CTk()
    app = PixelPressApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
