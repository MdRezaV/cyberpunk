#!/usr/bin/env python3
# pip install numpy pillow tqdm
"""
cyberpunk - Command-line image processing tool for stylized retro-futuristic visual effects.
This module provides a hardened CLI application for applying cyberpunk-inspired visual
transformations to digital images. The architectural scope encompasses batch and single-image
processing pipelines with modular effect composition and adaptive color quantization using
Pillow's built-in algorithms. Core capabilities include configurable dithering strategies,
chromatic aberration simulation, glitch art generation, and CRT-style post-processing effects.
The design intent prioritizes functional equivalence across execution paths while maintaining
extensibility for future effect modules. Operational context targets creative professionals,
digital artists, and automation workflows requiring deterministic, reproducible image
stylization with comprehensive logging and error recovery mechanisms.
"""
import sys

HELP_MESSAGE = """Cyberpunk Image Processor CLI - Apply retro-futuristic visual effects to digital images.

Usage: cyberpunk [OPTIONS] INPUT_FILE
       cyberpunk --batch DIRECTORY [OPTIONS]

Positional Arguments:
  input                 Path to the input image file (required unless using --batch)

Input/Output Options:
  -o, --output PATH     Specify output file path (default: cyberpunk_<name>.png)
  -b, --batch DIRECTORY Process all supported images in the specified directory
  --format EXT          Force output file format (.png, .jpg, .webp)
  --quality INT         JPEG/WebP output quality 1-100 (default: 95)
  --preserve-exif       Copy EXIF metadata from the original image

Core Processing Options:
  -p, --pixel-size INT  Pixel block dimension for pixelation effect
  -c, --colors INT      Target color palette size (2-256)
  -d, --dither TYPE     Dithering algorithm: none, floydsteinberg, ordered
  --palette HEX_LIST    Custom comma-separated hexadecimal color palette
  -s, --saturation FL   Color saturation multiplier (0.0-5.0)
  --posterize INT       Bit depth per channel for posterization (1-8)
  --quant-method TYPE   Color quantization algorithm: auto, median, octree

Visual Effects Options:
  --chromatic INT       RGB channel split offset in pixels
  --glitch FL           Block shift intensity (0.0-1.0)
  --noise FL            Gaussian noise grain intensity (0.0-1.0)
  --neon-edge [HEX]     Enable neon edge glow with optional hex color
  --scanlines FL        CRT scanline darkening intensity (0.0-1.0)
  --vignette FL         Radial edge darkening strength (0.0-1.0)
  --vhs-tracking FL     VHS tape tracking distortion intensity (0.0-1.0)
  --halftone [SIZE]     Enable halftone pattern with optional dot size
  --bloom [THR RAD INT] Enable bloom glow with threshold, radius, intensity
  --pixel-sort [DIR TH MASK] Enable pixel sorting with direction, threshold, mask
  --gradient-map HEX    Remap luminance to gradient via comma-separated hex colors

Workflow Options:
  --preset TYPE         Apply predefined visual preset: nord, dracula, cyberpunk, clean_sharp, landscape_vivid, retro_wave, matrix_code, glitch_core
  --preview             Generate fast low-resolution preview (max dimension 512px)
  -v, --verbose         Enable detailed step-by-step processing logs

Examples:
  cyberpunk input.png --preset cyberpunk --verbose
      Apply cyberpunk preset to single image with detailed step-by-step logging

  cyberpunk --batch ./photos --preset nord --output ./output --verbose
      Process all images in directory using nord preset with verbose output

  cyberpunk input.jpg --colors 16 --palette ff00ff,00ff00,0000ff --quant-method median
      Quantize image to 16 custom colors using median-cut algorithm

  cyberpunk input.png --gradient-map "000000,ff00ff,00ffff" --bloom 200 10 0.6
      Apply gradient color mapping with emissive bloom glow on bright areas

  cyberpunk input.png --vhs-tracking 0.5 --pixel-sort vertical 128 bright
      Stack multiple cyberpunk effects: VHS distortion, pixel sorting
"""

if "--help" in sys.argv or "-h" in sys.argv:
    print(HELP_MESSAGE)
    sys.exit(0)

import os
import argparse
import random
import time
import subprocess
from pathlib import Path

def resolve_external_dependencies():
    try:
        import numpy as np
        from PIL import Image, ImageFilter, ImageEnhance, ImageChops, ImageDraw, ImageOps
        from tqdm import tqdm
        return np, Image, ImageFilter, ImageEnhance, ImageChops, ImageDraw, ImageOps, tqdm
    except ModuleNotFoundError as missing_package_error:
        missing_package_name = missing_package_error.name
        print(f"[ERROR] Missing required dependency: {missing_package_name}", file=sys.stderr)
        print(f"[INFO] Attempting automatic installation via pip...", file=sys.stderr)
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", missing_package_name],
                check=True,
                capture_output=True
            )
            print(f"[SUCCESS] Installed {missing_package_name}. Re-evaluating imports.", file=sys.stderr)
            return resolve_external_dependencies()
        except subprocess.CalledProcessError as installation_failure:
            print(f"[ERROR] Automatic installation failed for {missing_package_name}.", file=sys.stderr)
            print(f"[ERROR] Cause: {installation_failure}", file=sys.stderr)
            print(f"[ERROR] Resolution: Manually execute 'pip install numpy pillow tqdm' in your terminal.", file=sys.stderr)
            sys.exit(1)

np, Image, ImageFilter, ImageEnhance, ImageChops, ImageDraw, ImageOps, tqdm = resolve_external_dependencies()

try:
    from PIL import ImageResampling, ImageDither
    NEAREST_RESAMPLE_MODE = ImageResampling.NEAREST
    DITHERING_ALGORITHMS = {
        "none": ImageDither.NONE,
        "floydsteinberg": ImageDither.FLOYDSTEINBERG,
        "ordered": ImageDither.ORDERED
    }
except ImportError:
    NEAREST_RESAMPLE_MODE = Image.NEAREST
    DITHERING_ALGORITHMS = {
        "none": Image.NONE,
        "floydsteinberg": Image.FLOYDSTEINBERG,
        "ordered": Image.ORDERED
    }

VISUAL_STYLE_PRESETS = {
    "nord": {
        "palette": "3b4252,434c5e,4c566a,d8dee9,e5e9f0,eceff4,8fbcbb,88c0d0,81a1c1,5e81ac,bf616a,d08770,ebcb8b,a3be8c,b48ead"
    },
    "dracula": {
        "palette": "282a36,44475a,6272a4,f8f8f2,bd93f9,ff79c6,8be9fd,50fa7b,fffb86,ff5555",
    },
    "cyberpunk": {
        "pixel_size": 12, "colors": 16, "saturation": 1.6, "dither": "floydsteinberg",
        "vignette": 0.7, "scanlines": 0.4, "neon_edge": "ff00ff"
    },
    "clean_sharp": {
        "pixel_size": 1, "colors": 64, "saturation": 1.1, "noise": 0.01,
        "vignette": 0.1, "dither": "none"
    },
    "landscape_vivid": {
        "pixel_size": 1, "colors": 96, "saturation": 1.4, "noise": 0.01,
        "vignette": 0.2, "dither": "none"
    },
    "retro_wave": {
        "gradient_map": "1a1a2e,16213e,0f3460,e94560,ff6b9d",
        "bloom": [220, 12, 0.7], "scanlines": 0.3, "vignette": 0.5, "saturation": 1.4
    },
    "matrix_code": {
        "gradient_map": "000000,003300,00ff00,ccffcc",
        "pixel_sort": ["vertical", 200, "bright"], "noise": 0.03
    },
    "glitch_core": {
        "glitch": 0.4, "chromatic": 3, "vhs_tracking": 0.6,
        "pixel_sort": ["horizontal", 100, "all"], "halftone": 6, "saturation": 1.8
    }
}

LOG_PREFIXES = {"info": "[*]", "debug": "[🔍]", "warn": "[!]", "error": "[✗]", "success": "[+]"}

def log_processing_event(message, severity="info", verbose_mode=False, **output_kwargs):
    prefix = LOG_PREFIXES.get(severity, "[*]")
    if severity == "debug" and not verbose_mode:
        return
    print(f"{prefix} {message}", **output_kwargs)

def convert_hex_to_rgb(hex_string):
    cleaned_hex = hex_string.lstrip('#')
    return tuple(int(cleaned_hex[i:i+2], 16) for i in (0, 2, 4))

def convert_rgb_to_hex(rgb_tuple):
    return '#{:02x}{:02x}{:02x}'.format(*[int(value) for value in rgb_tuple])

def adjust_image_saturation(source_image, saturation_factor, verbose_mode=False):
    clamped_factor = max(0.0, min(5.0, float(saturation_factor)))
    if clamped_factor == 1.0:
        log_processing_event("Saturation adjustment skipped: factor equals 1.0 (no change)", "debug", verbose_mode)
        return source_image
    log_processing_event(f"Applying saturation adjustment with factor={clamped_factor}", "debug", verbose_mode)
    start_time = time.time()
    result_image = ImageEnhance.Color(source_image).enhance(clamped_factor)
    log_processing_event(f"Saturation adjustment completed in {time.time() - start_time:.3f}s", "debug", verbose_mode)
    return result_image

def apply_color_posterization(source_image, bit_depth, verbose_mode=False):
    clamped_depth = int(bit_depth)
    if not (1 <= clamped_depth <= 8):
        safe_depth = max(1, min(8, clamped_depth))
        log_processing_event(f"Posterization bit depth {clamped_depth} out of valid range [1,8]; clamped to {safe_depth}", "warn")
        clamped_depth = safe_depth
    log_processing_event(f"Applying posterization with {clamped_depth} levels per channel", "debug", verbose_mode)
    return ImageOps.posterize(source_image, clamped_depth)

def apply_pixelation_effect(source_image, block_dimension, verbose_mode=False):
    safe_block_size = max(1, int(block_dimension))
    width_pixels, height_pixels = source_image.size
    scaled_width = max(1, width_pixels // safe_block_size)
    scaled_height = max(1, height_pixels // safe_block_size)
    log_processing_event(
        f"Pixelation: block_size={safe_block_size}, resizing {width_pixels}x{height_pixels} "
        f"→ {scaled_width}x{scaled_height} → {width_pixels}x{height_pixels}",
        "debug", verbose_mode
    )
    downscaled_image = source_image.resize((scaled_width, scaled_height), NEAREST_RESAMPLE_MODE)
    return downscaled_image.resize((width_pixels, height_pixels), NEAREST_RESAMPLE_MODE)

def quantize_with_octree_algorithm(source_image, target_colors, dither_method, verbose_mode=False):
    log_processing_event(f"Quantization: using octree method, target={target_colors} colors", "debug", verbose_mode)
    try:
        return source_image.quantize(colors=target_colors, dither=dither_method, method=Image.OCTREE)
    except (AttributeError, NotImplementedError):
        log_processing_event("Quantization: octree method unavailable; falling back to median-cut", "debug", verbose_mode)
        return source_image.quantize(colors=target_colors, dither=dither_method)

def quantize_image_colors(source_image, target_colors, dither_method, custom_palette_hex=None, algorithm='auto', verbose_mode=False):
    clamped_colors = max(2, min(256, int(target_colors)))
    dither_value = DITHERING_ALGORITHMS.get(dither_method, DITHERING_ALGORITHMS["floydsteinberg"])
    
    if custom_palette_hex:
        hex_values = [color.strip() for color in custom_palette_hex.split(',') if color.strip()]
        if len(hex_values) > 256:
            hex_values = hex_values[:256]
            log_processing_event("Custom palette truncated to 256 colors (PNG palette limit)", "debug", verbose_mode)
        palette_rgb_values = [convert_hex_to_rgb(color_hex) for color_hex in hex_values]
        log_processing_event(
            f"Using custom palette with {len(palette_rgb_values)} colors: "
            f"{', '.join(hex_values[:5])}{'...' if len(palette_rgb_values) > 5 else ''}",
            "debug", verbose_mode
        )
        palette_image = Image.new("P", (1, 1))
        palette_data = []
        for rgb_value in palette_rgb_values:
            palette_data.extend(rgb_value)
        palette_data.extend([0] * (768 - len(palette_data)))
        palette_image.putpalette(palette_data)
        log_processing_event(f"Applying custom palette quantization with dither={dither_method}", "debug", verbose_mode)
        return source_image.quantize(palette=palette_image, dither=dither_value)
    
    selected_algorithm = algorithm
    if algorithm == 'auto':
        selected_algorithm = 'octree'
        log_processing_event("Quantization: auto-selected octree method (Pillow built-in)", "debug", verbose_mode)
        
    if selected_algorithm == 'octree':
        return quantize_with_octree_algorithm(source_image, clamped_colors, dither_value, verbose_mode)
    
    log_processing_event(f"Quantization: using PIL median-cut, target={clamped_colors} colors, dither={dither_method}", "debug", verbose_mode)
    median_method = Image.MEDIANCUT if hasattr(Image, 'MEDIANCUT') else None
    return source_image.quantize(colors=clamped_colors, dither=dither_value, method=median_method)

def apply_chromatic_aberration(source_image, pixel_offset, verbose_mode=False):
    if pixel_offset == 0:
        log_processing_event("Chromatic aberration skipped: offset equals 0 (no effect)", "debug", verbose_mode)
        return source_image
    log_processing_event(f"Applying chromatic aberration with RGB split offset={pixel_offset}px", "debug", verbose_mode)
    pixel_array = np.array(source_image)
    red_channel, green_channel, blue_channel = pixel_array[:, :, 0], pixel_array[:, :, 1], pixel_array[:, :, 2]
    shifted_array = np.stack([
        np.roll(red_channel, int(pixel_offset), axis=1),
        green_channel,
        np.roll(blue_channel, -int(pixel_offset), axis=1)
    ], axis=-1).astype(np.uint8)
    return Image.fromarray(shifted_array, "RGB")

def apply_glitch_distortion(source_image, intensity, verbose_mode=False):
    clamped_intensity = max(0.0, min(1.0, float(intensity)))
    if clamped_intensity == 0:
        log_processing_event("Glitch effect skipped: intensity equals 0 (no effect)", "debug", verbose_mode)
        return source_image
    log_processing_event(f"Applying glitch effect with block shifts, intensity={clamped_intensity}", "debug", verbose_mode)
    pixel_array = np.array(source_image)
    image_height, image_width, _ = pixel_array.shape
    shift_iterations = int(image_height * clamped_intensity * 2)
    for _ in range(shift_iterations):
        start_row = random.randint(0, image_height - 2)
        end_row = random.randint(1, image_height)
        horizontal_shift = random.randint(-int(image_width * 0.1), int(image_width * 0.1))
        pixel_array[start_row:end_row] = np.roll(pixel_array[start_row:end_row], horizontal_shift, axis=1)
    return Image.fromarray(pixel_array)

def apply_gaussian_noise(source_image, intensity, color_noise=False, verbose_mode=False):
    clamped_intensity = max(0.0, min(1.0, float(intensity)))
    if clamped_intensity == 0:
        log_processing_event("Noise effect skipped: intensity equals 0 (no effect)", "debug", verbose_mode)
        return source_image
    noise_type = "color" if color_noise else "monochrome"
    log_processing_event(f"Applying {noise_type} Gaussian noise grain, intensity={clamped_intensity}", "debug", verbose_mode)
    pixel_array = np.array(source_image, dtype=np.float32)
    noise_array = np.random.normal(0, clamped_intensity * 255, pixel_array.shape)
    if not color_noise:
        noise_array = noise_array.mean(axis=2, keepdims=True)
    return Image.fromarray(np.clip(pixel_array + noise_array, 0, 255).astype(np.uint8))

def apply_neon_edge_glow(source_image, glow_color_hex="ff00ff", edge_threshold=100, blur_radius=4, verbose_mode=False):
    if not glow_color_hex:
        log_processing_event("Neon edge glow skipped: no color specified", "debug", verbose_mode)
        return source_image
    log_processing_event(
        f"Applying neon edge glow with color=#{glow_color_hex}, "
        f"threshold={edge_threshold}, blur_radius={blur_radius}",
        "debug", verbose_mode
    )
    edge_mask = source_image.convert("L").filter(ImageFilter.FIND_EDGES).point(
        lambda pixel_value: 255 if pixel_value > edge_threshold else 0
    )
    glow_layer = Image.new("RGB", source_image.size, convert_hex_to_rgb(glow_color_hex))
    glow_layer = Image.composite(
        glow_layer,
        Image.new("RGB", source_image.size, (0, 0, 0)),
        edge_mask
    ).filter(ImageFilter.GaussianBlur(blur_radius))
    return ImageChops.screen(source_image, glow_layer)

def apply_crt_scanlines(source_image, intensity, verbose_mode=False):
    clamped_intensity = max(0.0, min(1.0, float(intensity)))
    if clamped_intensity == 0:
        log_processing_event("Scanline effect skipped: intensity equals 0 (no effect)", "debug", verbose_mode)
        return source_image
    log_processing_event(f"Applying CRT scanline effect, intensity={clamped_intensity}", "debug", verbose_mode)
    width_pixels, height_pixels = source_image.size
    scanline_mask = Image.new("L", (width_pixels, height_pixels))
    mask_drawer = ImageDraw.Draw(scanline_mask)
    for row_index in range(0, height_pixels, 2):
        mask_drawer.line([(0, row_index), (width_pixels, row_index)], fill=int(255 * (1 - clamped_intensity)))
    return Image.composite(source_image, Image.new("RGB", source_image.size, (0, 0, 0)), scanline_mask)

def apply_radial_vignette(source_image, strength, verbose_mode=False):
    clamped_strength = max(0.0, min(1.0, float(strength)))
    if clamped_strength == 0:
        log_processing_event("Vignette effect skipped: strength equals 0 (no effect)", "debug", verbose_mode)
        return source_image
    log_processing_event(f"Applying vignette edge darkening, strength={clamped_strength}", "debug", verbose_mode)
    width_pixels, height_pixels = source_image.size
    center_x, center_y = width_pixels / 2, height_pixels / 2
    row_coordinates, col_coordinates = np.ogrid[:height_pixels, :width_pixels]
    radial_distance = np.sqrt((col_coordinates - center_x) ** 2 + (row_coordinates - center_y) ** 2)
    max_distance = np.sqrt(center_x ** 2 + center_y ** 2)
    vignette_mask = np.clip(
        255 - (radial_distance / max_distance) * 255 * clamped_strength,
        0, 255
    ).astype(np.uint8)
    return Image.composite(source_image, Image.new("RGB", source_image.size, (0, 0, 0)), Image.fromarray(vignette_mask, "L"))

def apply_vhs_tracking_distortion(source_image, intensity, wave_frequency=0.02, verbose_mode=False):
    clamped_intensity = max(0.0, min(1.0, float(intensity)))
    if clamped_intensity == 0:
        log_processing_event("VHS tracking effect skipped: intensity equals 0", "debug", verbose_mode)
        return source_image
    log_processing_event(
        f"Applying VHS tracking distortion: intensity={clamped_intensity}, "
        f"frequency={wave_frequency}", "debug", verbose_mode
    )
    pixel_array = np.array(source_image, dtype=np.float32)
    image_height, image_width = pixel_array.shape[:2]
    result_array = np.zeros_like(pixel_array)
    
    for y_coordinate in range(image_height):
        horizontal_offset = (
            np.sin(y_coordinate * wave_frequency) * 0.5 +
            np.sin(y_coordinate * wave_frequency * 2.3) * 0.3 +
            np.sin(y_coordinate * wave_frequency * 0.7) * 0.2
        ) * (image_width * 0.05) * clamped_intensity
        horizontal_offset += random.uniform(-1, 1) * clamped_intensity * 3
        result_array[y_coordinate] = np.roll(pixel_array[y_coordinate], int(horizontal_offset), axis=0)
        
        if clamped_intensity > 0.5:
            bleed_amount = int((clamped_intensity - 0.5) * 4)
            if bleed_amount > 0:
                red_channel = np.roll(result_array[:, :, 0], bleed_amount, axis=1)
                result_array[:, :, 0] = np.clip(
                    result_array[:, :, 0] * 0.9 + red_channel * 0.1, 0, 255
                )
    return Image.fromarray(np.clip(result_array, 0, 255).astype(np.uint8), "RGB")

def apply_halftone_pattern(source_image, dot_size=4, angle=45, grayscale=False, verbose_mode=False):
    dot_size = max(1, int(dot_size))
    angle = float(angle) % 360
    log_processing_event(
        f"Applying halftone effect: dot_size={dot_size}, angle={angle}°, "
        f"grayscale={grayscale}", "debug", verbose_mode
    )
    base_image = source_image.convert("L") if grayscale else source_image.convert("RGB")
    mode = "L" if grayscale else "RGB"
    width_pixels, height_pixels = base_image.size
    result_image = Image.new(mode, (width_pixels, height_pixels), 255 if grayscale else (255, 255, 255))
    drawing_context = ImageDraw.Draw(result_image)
    cos_angle, sin_angle = np.cos(np.radians(angle)), np.sin(np.radians(angle))
    
    for y_coordinate in range(0, height_pixels, dot_size):
        for x_coordinate in range(0, width_pixels, dot_size):
            sample_x = min(x_coordinate + dot_size // 2, width_pixels - 1)
            sample_y = min(y_coordinate + dot_size // 2, height_pixels - 1)
            if grayscale:
                luminance_value = base_image.getpixel((sample_x, sample_y))
                radius = (1 - luminance_value / 255) * (dot_size * 0.45)
                if radius > 0.5:
                    drawing_context.ellipse([
                        x_coordinate + (dot_size - radius) // 2,
                        y_coordinate + (dot_size - radius) // 2,
                        x_coordinate + (dot_size + radius) // 2,
                        y_coordinate + (dot_size + radius) // 2
                    ], fill=0)
            else:
                red_val, green_val, blue_val = base_image.getpixel((sample_x, sample_y))
                avg_brightness = (red_val + green_val + blue_val) / 765
                radius = (1 - avg_brightness) * (dot_size * 0.45)
                if radius > 0.5:
                    offset = int(radius * 0.3)
                    for channel_color, dx, dy in [
                        ((red_val, 0, 0), -offset, -offset),
                        ((0, green_val, 0), offset, 0),
                        ((0, 0, blue_val), 0, offset)
                    ]:
                        if sum(channel_color) > 0:
                            drawing_context.ellipse([
                                x_coordinate + (dot_size - radius) // 2 + dx,
                                y_coordinate + (dot_size - radius) // 2 + dy,
                                x_coordinate + (dot_size + radius) // 2 + dx,
                                y_coordinate + (dot_size + radius) // 2 + dy
                            ], fill=channel_color)
    return result_image

def apply_bloom_glow(source_image, threshold=200, radius=8, intensity=0.5, verbose_mode=False):
    threshold = max(0, min(255, int(threshold)))
    radius = max(1, int(radius))
    intensity = max(0.0, min(1.0, float(intensity)))
    if intensity == 0:
        log_processing_event("Bloom effect skipped: intensity equals 0", "debug", verbose_mode)
        return source_image
    log_processing_event(
        f"Applying bloom glow: threshold={threshold}, radius={radius}, "
        f"intensity={intensity}", "debug", verbose_mode
    )
    luminance_mask = source_image.convert("L")
    bright_region_mask = luminance_mask.point(
        lambda p: 255 if p > threshold else 0, mode="1"
    ).convert("L")
    bright_regions = Image.composite(
        source_image,
        Image.new("RGB", source_image.size, (0, 0, 0)),
        bright_region_mask
    )
    glow_layer = bright_regions.filter(ImageFilter.GaussianBlur(radius))
    glow_layer = ImageEnhance.Brightness(glow_layer).enhance(1.5)
    result_image = ImageChops.screen(source_image, glow_layer)
    if intensity < 1.0:
        result_image = Image.blend(source_image, result_image, intensity)
    return result_image

def apply_pixel_sorting(source_image, direction="vertical", threshold=128, mask_mode="bright", verbose_mode=False):
    valid_directions = {"horizontal", "vertical"}
    valid_masks = {"bright", "dark", "all"}
    if direction not in valid_directions:
        log_processing_event(f"Pixel sort: invalid direction '{direction}'; using 'vertical'", "warn")
        direction = "vertical"
    if mask_mode not in valid_masks:
        log_processing_event(f"Pixel sort: invalid mask_mode '{mask_mode}'; using 'bright'", "warn")
        mask_mode = "bright"
    threshold = max(0, min(255, int(threshold)))
    log_processing_event(
        f"Applying pixel sort: direction={direction}, threshold={threshold}, "
        f"mask={mask_mode}", "debug", verbose_mode
    )
    pixel_array = np.array(source_image.convert("RGB"))
    luminance_grid = np.mean(pixel_array, axis=2)
    result_array = pixel_array.copy()
    
    if direction == "vertical":
        for x_coordinate in range(pixel_array.shape[1]):
            column_data = pixel_array[:, x_coordinate]
            column_luminance = luminance_grid[:, x_coordinate]
            if mask_mode == "bright":
                sort_mask = column_luminance >= threshold
            elif mask_mode == "dark":
                sort_mask = column_luminance < threshold
            else:
                sort_mask = np.ones_like(column_luminance, dtype=bool)
            if np.any(sort_mask):
                sorted_indices = np.argsort(column_luminance[sort_mask])
                column_data[sort_mask] = column_data[sort_mask][sorted_indices]
            result_array[:, x_coordinate] = column_data
    else:
        for y_coordinate in range(pixel_array.shape[0]):
            row_data = pixel_array[y_coordinate]
            row_luminance = luminance_grid[y_coordinate]
            if mask_mode == "bright":
                sort_mask = row_luminance >= threshold
            elif mask_mode == "dark":
                sort_mask = row_luminance < threshold
            else:
                sort_mask = np.ones_like(row_luminance, dtype=bool)
            if np.any(sort_mask):
                sorted_indices = np.argsort(row_luminance[sort_mask])
                row_data[sort_mask] = row_data[sort_mask][sorted_indices]
            result_array[y_coordinate] = row_data
    return Image.fromarray(result_array, "RGB")

def apply_luminance_gradient_map(source_image, color_stops_hex, verbose_mode=False):
    if not color_stops_hex:
        log_processing_event("Gradient map skipped: no colors specified", "debug", verbose_mode)
        return source_image
    hex_values = [c.strip().lstrip('#') for c in color_stops_hex.split(',') if c.strip()]
    if len(hex_values) < 2:
        log_processing_event("Gradient map requires at least 2 color stops", "error")
        return source_image
    rgb_stops = [convert_hex_to_rgb(h) for h in hex_values]
    log_processing_event(
        f"Applying gradient map with {len(rgb_stops)} color stops: "
        f"{', '.join(hex_values[:4])}{'...' if len(hex_values) > 4 else ''}",
        "debug", verbose_mode
    )
    luminance_array = np.array(source_image.convert("L"), dtype=np.float32) / 255.0
    lookup_table = np.zeros((256, 3), dtype=np.uint8)
    num_stops = len(rgb_stops)
    for i in range(256):
        normalized_position = i / 255.0
        stop_index = min(int(normalized_position * (num_stops - 1)), num_stops - 2)
        local_t = (normalized_position - stop_index / (num_stops - 1)) * (num_stops - 1)
        start_color, end_color = np.array(rgb_stops[stop_index]), np.array(rgb_stops[stop_index + 1])
        lookup_table[i] = np.clip(start_color + (end_color - start_color) * local_t, 0, 255).astype(np.uint8)
    result_array = lookup_table[luminance_array.astype(int)]
    return Image.fromarray(result_array, "RGB")

def execute_processing_pipeline(source_image, cli_args):
    verbose_mode = getattr(cli_args, 'verbose', False)
    width_pixels, height_pixels = source_image.size
    image_mode = source_image.mode
    log_processing_event(f"Input image: {width_pixels}x{height_pixels} {image_mode}", "debug", verbose_mode)
    pipeline_start = time.time()
    execution_log = []
    processed_image = source_image.convert("RGB")
    
    if cli_args.saturation != 1.0:
        processed_image = adjust_image_saturation(processed_image, cli_args.saturation, verbose_mode)
        execution_log.append(f"saturation={cli_args.saturation}")
    if cli_args.posterize:
        processed_image = apply_color_posterization(processed_image, cli_args.posterize, verbose_mode)
        execution_log.append(f"posterize={cli_args.posterize}")
    if cli_args.pixel_size and cli_args.pixel_size > 1:
        processed_image = apply_pixelation_effect(processed_image, cli_args.pixel_size, verbose_mode)
        execution_log.append(f"pixel_size={cli_args.pixel_size}")
        
    quantization_start = time.time()
    processed_image = quantize_image_colors(
        processed_image, cli_args.colors, cli_args.dither,
        cli_args.palette, algorithm=cli_args.quant_method, verbose_mode=verbose_mode
    )
    quantization_duration = time.time() - quantization_start
    execution_log.append(
        f"quantize(colors={cli_args.colors}, method={cli_args.quant_method}, "
        f"dither={cli_args.dither}, duration={quantization_duration:.2f}s)"
    )
    processed_image = processed_image.convert("RGB")
    
    if cli_args.chromatic and cli_args.chromatic != 0:
        processed_image = apply_chromatic_aberration(processed_image, cli_args.chromatic, verbose_mode)
        execution_log.append(f"chromatic_aberration={cli_args.chromatic}")
    if cli_args.glitch and cli_args.glitch > 0:
        processed_image = apply_glitch_distortion(processed_image, cli_args.glitch, verbose_mode)
        execution_log.append(f"glitch_intensity={cli_args.glitch}")
    if cli_args.noise and cli_args.noise > 0:
        processed_image = apply_gaussian_noise(processed_image, cli_args.noise, verbose_mode)
        execution_log.append(f"noise_intensity={cli_args.noise}")
    if cli_args.neon_edge:
        processed_image = apply_neon_edge_glow(processed_image, cli_args.neon_edge, verbose_mode=verbose_mode)
        execution_log.append(f"neon_edge_color=#{cli_args.neon_edge}")
    if cli_args.scanlines and cli_args.scanlines > 0:
        processed_image = apply_crt_scanlines(processed_image, cli_args.scanlines, verbose_mode)
        execution_log.append(f"scanline_intensity={cli_args.scanlines}")
    if cli_args.vignette and cli_args.vignette > 0:
        processed_image = apply_radial_vignette(processed_image, cli_args.vignette, verbose_mode)
        execution_log.append(f"vignette_strength={cli_args.vignette}")
    if cli_args.vhs_tracking and cli_args.vhs_tracking > 0:
        processed_image = apply_vhs_tracking_distortion(processed_image, cli_args.vhs_tracking, verbose_mode)
        execution_log.append(f"vhs_tracking={cli_args.vhs_tracking}")
    if cli_args.halftone:
        dot_size = int(cli_args.halftone[0]) if isinstance(cli_args.halftone, list) else 4
        processed_image = apply_halftone_pattern(processed_image, dot_size=dot_size, verbose_mode=verbose_mode)
        execution_log.append(f"halftone_dot_size={dot_size}")
    if cli_args.bloom is not None:
        params = cli_args.bloom if isinstance(cli_args.bloom, list) else []
        threshold = int(params[0]) if len(params) > 0 else 200
        radius = int(params[1]) if len(params) > 1 else 8
        intensity = float(params[2]) if len(params) > 2 else 0.5
        processed_image = apply_bloom_glow(processed_image, threshold, radius, intensity, verbose_mode=verbose_mode)
        execution_log.append(f"bloom(thresh={threshold},r={radius},int={intensity})")
    if cli_args.pixel_sort is not None:
        params = cli_args.pixel_sort if isinstance(cli_args.pixel_sort, list) else []
        direction = params[0] if len(params) > 0 else "vertical"
        threshold = int(params[1]) if len(params) > 1 else 128
        mask = params[2] if len(params) > 2 else "bright"
        processed_image = apply_pixel_sorting(processed_image, direction, threshold, mask, verbose_mode=verbose_mode)
        execution_log.append(f"pixel_sort(dir={direction},thresh={threshold},mask={mask})")
    if cli_args.gradient_map:
        processed_image = apply_luminance_gradient_map(processed_image, cli_args.gradient_map, verbose_mode)
        execution_log.append(f"gradient_map={cli_args.gradient_map}")
        
    total_duration = time.time() - pipeline_start
    log_processing_event(
        f"Processing pipeline: completed {len(execution_log)} steps in {total_duration:.2f}s",
        "info", verbose_mode
    )
    if verbose_mode:
        for step_description in execution_log:
            log_processing_event(f"  → {step_description}", "debug")
    return processed_image

def save_output_image(processed_image, output_path, cli_args, original_image=None, verbose_mode=False):
    save_parameters = {}
    file_extension = output_path.suffix.lower()
    if file_extension in (".jpg", ".jpeg"):
        save_parameters.update({"quality": cli_args.quality, "optimize": True})
        log_processing_event(f"Saving as JPEG with quality={cli_args.quality}", "debug", verbose_mode)
    elif file_extension == ".png":
        save_parameters.update({"optimize": True, "compress_level": 6})
        log_processing_event("Saving as PNG with compression level 6", "debug", verbose_mode)
    elif file_extension == ".webp":
        save_parameters.update({
            "quality": cli_args.quality,
            "lossless": cli_args.quality == 100
        })
        log_processing_event(
            f"Saving as WebP with quality={cli_args.quality}, lossless={cli_args.quality == 100}",
            "debug", verbose_mode
        )
    if cli_args.preserve_exif and original_image and "exif" in getattr(original_image, "info", {}):
        save_parameters["exif"] = original_image.info["exif"]
        log_processing_event("Preserving EXIF metadata in output", "debug", verbose_mode)
    save_start = time.time()
    processed_image.save(str(output_path), **save_parameters)
    save_duration = time.time() - save_start
    file_size_kb = output_path.stat().st_size / 1024
    log_processing_event(
        f"Saved to {output_path} ({file_size_kb:.1f} KB) in {save_duration:.2f}s",
        "debug", verbose_mode
    )

def process_batch_directory(input_file_paths, output_directory, cli_args):
    verbose_mode = getattr(cli_args, 'verbose', False)
    output_directory.mkdir(parents=True, exist_ok=True)
    log_processing_event(f"Batch processing: {len(input_file_paths)} images → {output_directory}", "info")
    for input_path in tqdm(input_file_paths, desc="Processing"):
        try:
            original_image = Image.open(input_path)
            processed_image = execute_processing_pipeline(original_image, cli_args)
            output_filename = f"cyberpunk_{input_path.stem}{cli_args.format or input_path.suffix}"
            save_output_image(processed_image, output_directory / output_filename, cli_args, original_image, verbose_mode)
        except Exception as processing_error:
            log_processing_event(f"Failed to process {input_path.name}: {processing_error}", "error", file=sys.stderr)

def _configure_argument_parser():
    parser = argparse.ArgumentParser(
        description="Cyberpunk Image Processor CLI - Apply retro-futuristic visual effects to digital images.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=HELP_MESSAGE.split("Examples:")[1].strip() if "Examples:" in HELP_MESSAGE else ""
    )
    input_output_group = parser.add_argument_group("Input/Output")
    input_output_group.add_argument("input", nargs="?", help="Input image file path (required unless using --batch)")
    input_output_group.add_argument("-o", "--output", help="Output file path (default: cyberpunk_<name>.png)")
    input_output_group.add_argument("-b", "--batch", type=Path, help="Process all supported images in specified directory")
    input_output_group.add_argument("--format", choices=[".png", ".jpg", ".webp"], help="Force output file format")
    input_output_group.add_argument("--quality", type=int, default=95, help="JPEG/WebP output quality (1-100, default: 95)")
    input_output_group.add_argument("--preserve-exif", action="store_true", help="Copy EXIF metadata from original image")
    
    core_processing_group = parser.add_argument_group("Core Processing")
    core_processing_group.add_argument("-p", "--pixel-size", type=int, default=None, help="Pixel block dimension for pixelation effect")
    core_processing_group.add_argument("-c", "--colors", type=int, default=None, help="Target color palette size (2-256)")
    core_processing_group.add_argument("-d", "--dither", choices=["none", "floydsteinberg", "ordered"], default=None, help="Dithering algorithm for color quantization")
    core_processing_group.add_argument("--palette", default=None, help="Custom comma-separated hexadecimal color palette")
    core_processing_group.add_argument("-s", "--saturation", type=float, default=None, help="Color saturation multiplier (0.0-5.0)")
    core_processing_group.add_argument("--posterize", type=int, default=None, help="Bit depth per channel for posterization (1-8)")
    core_processing_group.add_argument("--quant-method", choices=["auto", "median", "octree"], default="auto", help="Color quantization algorithm: auto (default), median (PIL median-cut), or octree")
    
    effects_group = parser.add_argument_group("Visual Effects")
    effects_group.add_argument("--chromatic", type=int, default=None, help="RGB channel split offset in pixels for chromatic aberration")
    effects_group.add_argument("--glitch", type=float, default=None, help="Block shift intensity for glitch effect (0.0-1.0)")
    effects_group.add_argument("--noise", type=float, default=None, help="Gaussian noise grain intensity (0.0-1.0)")
    effects_group.add_argument("--neon-edge", nargs="?", const="ff00ff", default=None, help="Enable neon edge glow with optional hex color (default: ff00ff)")
    effects_group.add_argument("--scanlines", type=float, default=None, help="CRT scanline darkening intensity (0.0-1.0)")
    effects_group.add_argument("--vignette", type=float, default=None, help="Radial edge darkening strength (0.0-1.0)")
    effects_group.add_argument("--vhs-tracking", type=float, default=None, help="VHS tape tracking distortion intensity (0.0-1.0)")
    effects_group.add_argument("--halftone", nargs="?", const="4", default=None, help="Enable halftone pattern; optional dot_size param (default: 4)")
    effects_group.add_argument("--bloom", nargs="*", default=None, help="Enable bloom glow: [threshold] [radius] [intensity] (defaults: 200, 8, 0.5)")
    effects_group.add_argument("--pixel-sort", nargs="*", default=None, help="Enable pixel sorting: [direction] [threshold] [mask] (defaults: vertical, 128, bright)")
    effects_group.add_argument("--gradient-map", default=None, help="Remap luminance to gradient: comma-separated hex colors (e.g., '000000,ff00ff,00ffff')")
    
    workflow_group = parser.add_argument_group("Workflow Options")
    workflow_group.add_argument("--preset", choices=["nord", "dracula", "cyberpunk", "clean_sharp", "landscape_vivid", "retro_wave", "matrix_code", "glitch_core"], help="Apply predefined visual preset configuration")
    workflow_group.add_argument("--preview", action="store_true", help="Generate fast low-resolution preview (max dimension 512px)")
    workflow_group.add_argument("--verbose", "-v", action="store_true", help="Enable detailed step-by-step processing logs")
    return parser

def main():
    cli_parser = _configure_argument_parser()
    cli_args = cli_parser.parse_args()
    verbose_mode = cli_args.verbose
    
    if not cli_args.input and not cli_args.batch:
        print("[error] Provide an input file path or use --batch for directory processing", file=sys.stderr)
        sys.exit(1)
    if cli_args.input and not Path(cli_args.input).exists():
        log_processing_event(f"Input file not found: {cli_args.input}", "error")
        sys.exit(1)
    if cli_args.batch and not cli_args.batch.is_dir():
        log_processing_event(f"Batch directory not found: {cli_args.batch}", "error")
        sys.exit(1)
        
    if cli_args.preset:
        log_processing_event(f"Applying visual preset: '{cli_args.preset}'", "info", verbose_mode)
        for parameter_name, parameter_value in VISUAL_STYLE_PRESETS[cli_args.preset].items():
            if getattr(cli_args, parameter_name) is None:
                setattr(cli_args, parameter_name, parameter_value)
                log_processing_event(f"  → {parameter_name}={parameter_value}", "debug", verbose_mode)
                
    fallback_defaults = {
        "pixel_size": 10, "colors": 25, "dither": "floydsteinberg",
        "saturation": 1.0, "chromatic": 0, "glitch": 0.0, "noise": 0.05,
        "scanlines": 0.0, "vignette": 0.0, "vhs_tracking": 0.0,
        "bloom": None, "pixel_sort": None, "gradient_map": None
    }
    for parameter_name, default_value in fallback_defaults.items():
        if getattr(cli_args, parameter_name) is None:
            setattr(cli_args, parameter_name, default_value)
            
    if verbose_mode:
        log_processing_event("Final processing configuration:", "info")
        for parameter_name, parameter_value in vars(cli_args).items():
            if parameter_value is not None and parameter_name not in ('input', 'output', 'batch'):
                log_processing_event(f"  {parameter_name}: {parameter_value}", "debug")
                
    if cli_args.batch:
        supported_extensions = ("*.jpg", "*.jpeg", "*.png", "*.bmp", "*.tiff", "*.webp")
        input_file_paths = [
            file_path
            for extension_pattern in supported_extensions
            for file_path in cli_args.batch.glob(extension_pattern)
        ]
        if not input_file_paths:
            log_processing_event("No supported image files found in batch directory", "error", file=sys.stderr)
            sys.exit(1)
        output_directory = Path(cli_args.output) if cli_args.output else cli_args.batch / "cyberpunk_output"
        process_batch_directory(input_file_paths, output_directory, cli_args)
        log_processing_event(f"Batch processing complete: output saved to {output_directory}", "success")
        return
        
    output_path = Path(cli_args.output) if cli_args.output else Path(f"cyberpunk_{Path(cli_args.input).stem}{cli_args.format or '.png'}")
    log_processing_event(f"Loading input image: {cli_args.input}", "debug", verbose_mode)
    original_image = Image.open(cli_args.input)
    original_dimensions = original_image.size
    
    if cli_args.preview:
        original_width, original_height = original_image.size
        if max(original_width, original_height) > 512:
            scale_ratio = 512 / max(original_width, original_height)
            preview_dimensions = (int(original_width * scale_ratio), int(original_height * scale_ratio))
            log_processing_event(f"Preview mode: resizing {original_width}x{original_height} → {preview_dimensions[0]}x{preview_dimensions[1]}", "info", verbose_mode)
            original_image = original_image.resize(preview_dimensions, NEAREST_RESAMPLE_MODE)
            
    log_processing_event(f"Processing image with '{cli_args.preset or 'custom'}' configuration (quantization: {cli_args.quant_method})", "info")
    processing_start = time.time()
    result_image = execute_processing_pipeline(original_image, cli_args)
    processing_duration = time.time() - processing_start
    save_output_image(result_image, output_path, cli_args, original_image, verbose_mode)
    log_processing_event(
        f"Processing complete: {original_dimensions[0]}x{original_dimensions[1]} → {output_path.name} in {processing_duration:.2f}s",
        "success"
    )
    if verbose_mode and result_image.mode == "P":
        palette_color_count = len(result_image.getpalette()) // 3 if result_image.getpalette() else 0
        log_processing_event(f"  Final color palette: {palette_color_count} colors", "debug")

if __name__ == "__main__":
    main()