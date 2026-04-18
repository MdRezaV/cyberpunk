# 🌃 CyberPunk

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

> Apply retro-futuristic visual effects to digital images via command-line

A CLI application for applying cyberpunk-inspired visual transformations to digital images. Features batch processing, modular effect composition, adaptive color quantization, and CRT-style post-processing effects.

## Example

| <img width="626" height="626" alt="input" src="https://github.com/user-attachments/assets/59a5654a-6c62-4428-9c80-bc4216c92cab" /> | <img width="626" height="626" alt="output" src="https://github.com/user-attachments/assets/0581f582-3a9a-4255-b36b-cdc2722cc722" /> |
|:---:|:---:|
| **Input** | **Output** |


## Features

### Core Effects
- **Pixelation** – Block-based pixel art stylization with configurable block size
- **Color Quantization** – Reduce palette to 2-256 colors with median-cut or octree algorithms
- **Dithering** – Floyd-Steinberg, ordered, or none for smooth color transitions
- **Custom Palettes** – Define your own hexadecimal color schemes
- **Saturation Control** – Adjust color intensity (0.0–5.0x)
- **Posterization** – Reduce bit depth per channel for retro poster effects

### Visual Effects
| Effect | Description | Parameters |
|--------|-------------|------------|
| `--chromatic` | RGB channel split for aberration | Pixel offset |
| `--glitch` | Random block shifts for glitch art | Intensity 0.0–1.0 |
| `--noise` | Gaussian grain overlay | Intensity 0.0–1.0 |
| `--neon-edge` | Edge detection with colored glow | Hex color (default: `ff00ff`) |
| `--scanlines` | CRT-style horizontal scanlines | Intensity 0.0–1.0 |
| `--vignette` | Radial edge darkening | Strength 0.0–1.0 |
| `--vhs-tracking` | Analog tape tracking distortion | Intensity 0.0–1.0 |
| `--halftone` | Comic-style dot pattern | Dot size (default: 4) |
| `--bloom` | Emissive glow on bright areas | Threshold, radius, intensity |
| `--pixel-sort` | Sort pixels by luminance | Direction, threshold, mask |
| `--gradient-map` | Remap luminance to color gradient | Comma-separated hex colors |

### Workflow
- **Batch Processing** – Process entire directories of images
- **Presets** – One-click apply predefined visual styles
- **Preview Mode** – Fast low-res previews (max 512px)
- **EXIF Preservation** – Keep metadata in output files
- **Verbose Logging** – Detailed step-by-step processing info
- **Multiple Formats** – Output to PNG, JPEG, or WebP

---

## Installation

### Requirements
- Python 3.8+
- `numpy`
- `pillow` (PIL)
- `tqdm`

### Quick Install
```bash
pip install numpy pillow tqdm
```

### Clone & Run
```bash
git clone https://github.com/MdRezaV/cyberpunk.git
cd cyberpunk
python cyberpunk.py --help
```

> The script will attempt to auto-install missing dependencies via `pip` if not found.

---

## Usage

### Basic Syntax
```bash
# Single image processing
python cyberpunk.py INPUT_FILE [OPTIONS]

# Batch directory processing
python cyberpunk.py --batch DIRECTORY [OPTIONS]
```

### Quick Start Examples

```bash
# Apply cyberpunk preset with verbose logging
python cyberpunk.py input.png --preset cyberpunk --verbose

# Process all images in a folder using nord preset
python cyberpunk.py --batch ./photos --preset nord --output ./output --verbose

# Custom color quantization with 16 colors and Floyd-Steinberg dithering
python cyberpunk.py input.jpg --colors 16 --palette ff00ff,00ff00,0000ff --quant-method median

# Gradient mapping with bloom glow
python cyberpunk.py input.png --gradient-map "000000,ff00ff,00ffff" --bloom 200 10 0.6

# Stack multiple effects: VHS distortion + pixel sorting
python cyberpunk.py input.png --vhs-tracking 0.5 --pixel-sort vertical 128 bright
```

---

## Available Presets

| Preset | Description | Key Effects |
|--------|-------------|-------------|
| `nord` | Cool Nordic color palette | 15-color custom palette |
| `dracula` | Dark theme with vibrant accents | 10-color dark palette |
| `cyberpunk` | Classic neon cyberpunk aesthetic | Pixelation, saturation boost, vignette, scanlines, neon edge |
| `clean_sharp` | Minimal enhancement | High color count, low noise, subtle vignette |
| `landscape_vivid` | Enhanced natural scenes | Increased saturation, vivid colors |
| `retro_wave` | 80s synthwave aesthetic | Gradient map, bloom, scanlines, vignette |
| `matrix_code` | Green digital rain style | Gradient map, vertical pixel sort, subtle noise |
| `glitch_core` | Maximum glitch intensity | Chromatic aberration, glitch, VHS tracking, halftone |

### Using Presets
```bash
python cyberpunk.py input.png --preset retro_wave
```

> Preset values can be overridden by specifying individual options after `--preset`.

---

## Command-Line Options Reference

### Input/Output
| Option | Description | Default |
|--------|-------------|---------|
| `input` | Path to input image file *(required unless --batch)* | – |
| `-o, --output PATH` | Specify output file path | `cyberpunk_<name>.png` |
| `-b, --batch DIRECTORY` | Process all supported images in directory | – |
| `--format EXT` | Force output format: `.png`, `.jpg`, `.webp` | Auto-detect |
| `--quality INT` | JPEG/WebP quality (1-100) | `95` |
| `--preserve-exif` | Copy EXIF metadata from original | `false` |

### Core Processing
| Option | Description | Range/Values |
|--------|-------------|--------------|
| `-p, --pixel-size INT` | Pixel block dimension for pixelation | `1+` |
| `-c, --colors INT` | Target color palette size | `2–256` |
| `-d, --dither TYPE` | Dithering algorithm | `none`, `floydsteinberg`, `ordered` |
| `--palette HEX_LIST` | Custom comma-separated hex palette | e.g., `ff00ff,00ff00` |
| `-s, --saturation FL` | Color saturation multiplier | `0.0–5.0` |
| `--posterize INT` | Bit depth per channel | `1–8` |
| `--quant-method TYPE` | Quantization algorithm | `auto`, `median`, `octree` |

### Visual Effects
| Option | Description | Parameters |
|--------|-------------|------------|
| `--chromatic INT` | RGB channel split offset | Pixel value |
| `--glitch FL` | Block shift intensity | `0.0–1.0` |
| `--noise FL` | Gaussian noise intensity | `0.0–1.0` |
| `--neon-edge [HEX]` | Enable neon edge glow | Optional hex color |
| `--scanlines FL` | CRT scanline darkening | `0.0–1.0` |
| `--vignette FL` | Radial edge darkening | `0.0–1.0` |
| `--vhs-tracking FL` | VHS tracking distortion | `0.0–1.0` |
| `--halftone [SIZE]` | Enable halftone pattern | Optional dot size |
| `--bloom [THR RAD INT]` | Enable bloom glow | Threshold, radius, intensity |
| `--pixel-sort [DIR TH MASK]` | Enable pixel sorting | Direction, threshold, mask |
| `--gradient-map HEX` | Luminance to gradient remap | Comma-separated hex |

### Workflow
| Option | Description |
|--------|-------------|
| `--preset TYPE` | Apply predefined visual preset |
| `--preview` | Generate fast low-res preview (max 512px) |
| `-v, --verbose` | Enable detailed processing logs |

---

## Known Bugs

- **PNG transparent backgrounds**: Images with alpha channels (transparency) are not handled optimally. Transparent pixels may be converted to solid black or white during processing. For best results, convert PNGs with transparency to a solid background format (e.g., JPEG) before processing, or use the `--format jpg` option to force opaque output.

---

## Development

### Running Locally
```bash
# Clone repository
git clone https://github.com/MdRezaV/cyberpunk.git
cd cyberpunk

# Install dependencies
pip install numpy pillow tqdm

# Run with example
python cyberpunk.py example.png --preset cyberpunk --verbose
```

### Adding New Effects
1. Create a new function following the pattern: `apply_<effect_name>(image, params, verbose_mode)`
2. Add corresponding CLI argument in `_configure_argument_parser()`
3. Integrate into `execute_processing_pipeline()`
4. Document in HELP_MESSAGE and README for new options

### Testing
```bash
# Test single image
python cyberpunk.py test.png --verbose

# Test batch processing
python cyberpunk.py --batch ./test_images --preset dracula --output ./results
```

---

## Contributing

Contributions are welcome! 

---

### Guidelines
- Follow PEP 8 style guidelines
- Add docstrings to new functions
- Include verbose logging support
- Update HELP_MESSAGE and README for new options
- Test with multiple image formats

---

## License

Distributed under the **Apache License 2.0**. See [LICENSE](LICENSE) for more information.

---

## Acknowledgments

- Built with [Pillow](https://python-pillow.org/) for image processing
- Color algorithms powered by [NumPy](https://numpy.org/)
- Progress tracking via [tqdm](https://github.com/tqdm/tqdm)
- Inspired by retro computing, CRT displays, and cyberpunk aesthetics

---

> Report issues or request features on [GitHub Issues](https://github.com/MdRezaV/cyberpunk/issues)
