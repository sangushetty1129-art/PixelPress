# PixelPress

### A Modern Image Compression & Optimization Tool

PixelPress is a Python-based desktop application designed to make image compression simple, efficient, and accessible. It provides an intuitive graphical interface for compressing, resizing, and optimizing images while maintaining control over image quality and output settings.

## Features

- **Modern GUI:** Clean and intuitive interface built with CustomTkinter.
- **Batch Compression:** Compress multiple images in a single operation.
- **Drag and Drop:** Easily import images using drag-and-drop functionality.
- **Image Preview:** Preview images before and after compression.
- **Image Resizing:** Resize images while maintaining aspect ratio.
- **Quality Control:** Adjust compression quality according to your requirements.
- **Multiple Formats:** Support for JPEG, PNG, WebP, BMP, and TIFF.
- **Compression Statistics:** View image size and compression results.
- **Output Management:** Choose where compressed images are saved.
- **Compression History:** Keep track of previous compression operations.
- **Theme Support:** Customize the application's appearance.

## Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core application logic |
| CustomTkinter | Modern graphical user interface |
| Pillow | Image processing and compression |
| TkinterDnD2 | Drag-and-drop functionality |

## Getting Started

Follow these steps to run PixelPress locally.

### Prerequisites

- Python 3.10 or later
- Git
- Windows, or another platform compatible with the application's dependencies

### Installation

**1. Clone the repository**

```bash
git clone https://github.com/sangushetty1129-art/PixelPress.git
```

**2. Navigate to the project directory**

```bash
cd PixelPress
```

**3. Create a virtual environment**

```bash
python -m venv .venv
```

**4. Activate the virtual environment**

For Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

**5. Install dependencies**

```bash
python -m pip install -r requirements.txt
```

**6. Run PixelPress**

```bash
python img_comp.py
```

## Project Structure

```text
PixelPress/
│
├── img_comp.py
├── requirements.txt
├── README.md
├── .gitignore
└── .venv/
```

## Usage

1. Launch PixelPress.
2. Add images using the file selection option or drag-and-drop.
3. Configure compression quality and image settings.
4. Select the desired output format and destination.
5. Start compression.
6. Review the compressed images and compression statistics.

## Developer

**Sangamesh**

GitHub: [@sangushetty1129-art](https://github.com/sangushetty1129-art)

## Acknowledgements

PixelPress uses open-source Python libraries, including Pillow, CustomTkinter, and TkinterDnD2.

Their respective authors and maintainers deserve credit for the libraries that make this application possible.

---

If you find PixelPress useful, consider giving the repository a star.

