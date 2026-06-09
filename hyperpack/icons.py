"""
Icon processing: extract from APK, rename via appfilter.xml, optional resize
"""

import os
import re
import shutil
import struct
import zipfile
import zlib
from pathlib import Path
from . import console


def find_icon_folder(res_path):
    """
    Find the drawable folder with the most PNG icons.
    Returns Path or None.
    """
    res = Path(res_path)
    best_folder = None
    best_count = 0

    for folder in res.iterdir():
        if not folder.is_dir() or "drawable" not in folder.name:
            continue
        count = sum(1 for f in folder.iterdir() if f.suffix.lower() == ".png")
        if count > best_count:
            best_count = count
            best_folder = folder

    return best_folder, best_count


def find_appfilter(extracted_path):
    """
    Find appfilter.xml - prefer assets/ version over res/xml/.
    Returns Path or None.
    """
    extracted = Path(extracted_path)

    # Prefer assets/appfilter.xml
    assets_filter = extracted / "assets" / "appfilter.xml"
    if assets_filter.exists():
        return assets_filter

    # Fallback to res/xml/appfilter.xml
    res_filter = extracted / "res" / "xml" / "appfilter.xml"
    if res_filter.exists():
        return res_filter

    return None


def extract_apk(apk_path, extract_dir):
    """Extract APK (it's a ZIP) to extract_dir."""
    extract_dir = Path(extract_dir)
    extract_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(apk_path, "r") as z:
        z.extractall(extract_dir)
    return extract_dir


def _parse_appfilter_regex(xml_content):
    """
    Method 1: Regex-based parser.
    Handles standard ComponentInfo{package/activity} format.
    Returns list of (package_name, drawable_name) tuples.
    """
    pattern = r'component="ComponentInfo\{([^/]+)/[^}]+\}"\s+drawable="([^"]+)"'
    return re.findall(pattern, xml_content)


def _parse_appfilter_xml(appfilter_path):
    """
    Method 2: XML-parser based (contributed by community).
    More robust with non-standard appfilter.xml schemes.
    Handles multiple components per drawable and various formats.
    Returns list of (package_name, drawable_name) tuples.
    Credits: Reddit user suggestion via r/HyperOS
    """
    import xml.etree.ElementTree as ET

    try:
        tree = ET.parse(appfilter_path)
        root = tree.getroot()
    except ET.ParseError:
        return []

    drawable_map = {}

    for item in root.findall("item"):
        component = item.get("component")
        drawable = item.get("drawable")
        if not component or not drawable:
            continue

        # Clean component name
        component_name = component.replace("ComponentInfo{", "").replace("}", "").strip()
        if component_name.startswith(":"):
            continue

        parts = component_name.split("/")
        if drawable in drawable_map:
            drawable_map[drawable].append(parts)
        else:
            drawable_map[drawable] = [parts]

    # Flatten to (package_name, drawable_name) tuples
    result = []
    for drawable, components in drawable_map.items():
        for component_parts in components:
            if component_parts:
                result.append((component_parts[0], drawable))

    return result


def rename_icons(copy_icon_dir, appfilter_path, output_dir):
    """
    Read appfilter.xml, map drawable names to package names,
    copy renamed icons to output_dir.

    Uses regex parser first; falls back to XML parser if 0 matches found.
    Returns (success_count, missing_count)
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    copy_icon_dir = Path(copy_icon_dir)

    with open(appfilter_path, "r", encoding="utf-8") as f:
        xml_content = f.read()

    # Try regex first (fast, handles standard format)
    matches = _parse_appfilter_regex(xml_content)

    # Fallback to XML parser if regex found nothing
    if not matches:
        console.warn("Standard appfilter format not detected, trying XML parser…")
        matches = _parse_appfilter_xml(appfilter_path)

    if not matches:
        raise RuntimeError(
            "Could not parse appfilter.xml — no icon mappings found.\n"
            "This icon pack may use an unsupported appfilter format."
        )

    success = 0
    missing = 0

    for package_name, drawable_name in matches:
        src = copy_icon_dir / f"{drawable_name}.png"
        dst = output_dir / f"{package_name}.png"
        if src.exists():
            shutil.copy2(src, dst)
            success += 1
        else:
            missing += 1

    return success, missing


def get_icon_size(icon_path):
    """Return (width, height) of a PNG, or None on failure."""
    try:
        # Read PNG dimensions without Pillow (from header)
        with open(icon_path, "rb") as f:
            f.read(16)  # PNG signature + IHDR length + type
            width = int.from_bytes(f.read(4), "big")
            height = int.from_bytes(f.read(4), "big")
        return width, height
    except Exception:
        return None


def _add_srgb_sbit(png_path):
    """Patch PNG with sRGB and sBIT chunks (required by HyperOS)."""
    with open(png_path, "rb") as f:
        data = f.read()

    srgb_data = b"\x00"
    srgb_crc = zlib.crc32(b"sRGB" + srgb_data) & 0xFFFFFFFF
    srgb_chunk = struct.pack(">I", 1) + b"sRGB" + srgb_data + struct.pack(">I", srgb_crc)

    sbit_data = bytes([8, 8, 8, 8])
    sbit_crc = zlib.crc32(b"sBIT" + sbit_data) & 0xFFFFFFFF
    sbit_chunk = struct.pack(">I", 4) + b"sBIT" + sbit_data + struct.pack(">I", sbit_crc)

    new_data = data[:33] + srgb_chunk + sbit_chunk + data[33:]
    with open(png_path, "wb") as f:
        f.write(new_data)


def resize_icons(input_dir, output_dir, target_size):
    """
    Resize all PNGs in input_dir to target_size x target_size.
    Requires Pillow. Returns (success, failed) counts.
    """
    try:
        from PIL import Image
    except ImportError:
        raise RuntimeError("Pillow is not installed. Run: pip install Pillow")

    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    success = 0
    failed = 0

    icons = list(input_dir.glob("*.png"))
    total = len(icons)

    for i, icon_path in enumerate(icons):
        out_path = output_dir / icon_path.name
        try:
            with Image.open(icon_path) as img:
                img = img.convert("RGBA")
                # Trim transparent padding
                bbox = img.getbbox()
                if bbox:
                    img = img.crop(bbox)
                resized = img.resize((target_size, target_size), Image.Resampling.LANCZOS)
                resized.save(out_path, format="PNG")
            _add_srgb_sbit(out_path)
            success += 1
        except Exception as e:
            failed += 1

        if (i + 1) % 100 == 0 or (i + 1) == total:
            console.progress(f"Resizing icons… {i+1}/{total}")

    return success, failed
