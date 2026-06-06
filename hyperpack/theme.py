"""
Theme packing: build Final ZIP, patch MRC files
"""

import shutil
import zipfile
from pathlib import Path
from . import console


DEFAULT_TRANSFORM_CONFIG = """<?xml version="1.0" encoding="UTF-8"?>
<IconTransform>
  <Config name="ConfigIconMask" value="M96.4286 62.2772C96.4286 72.1118 96.4286 77.029 94.7547 82.3225C92.6512 88.1016 88.0988 92.654 82.3196 94.7576C77.6553 96.2326 73.278 96.4076 65.575 96.4284H50H34.425C26.722 96.4076 22.3446 96.2326 17.6803 94.7576C11.9012 92.654 7.34879 88.1016 5.24522 82.3225C3.57141 77.029 3.57141 72.1118 3.57141 62.2772V49.9999V37.7225C3.57141 27.888 3.57141 22.9707 5.24522 17.6772C7.34879 11.8981 11.9012 7.34569 17.6803 5.24212C22.3446 3.76712 26.722 3.59212 34.425 3.57129H50H65.575C73.278 3.59212 77.6553 3.76712 82.3196 5.24212C88.0988 7.34569 92.6512 11.8981 94.7547 17.6772C96.4286 22.9707 96.4286 27.888 96.4286 37.7225V49.9999V62.2772Z"/>
</IconTransform>"""


def find_transform_config(mrc_extract_dir):
    """
    Find the best transform_config.xml in an extracted MRC.
    Prefers the one with a ConfigIconMask (SVG path = better quality).
    Returns Path or None.
    """
    mrc_dir = Path(mrc_extract_dir)
    candidates = list(mrc_dir.rglob("transform_config*.xml"))
    
    if not candidates:
        return None

    for candidate in candidates:
        content = candidate.read_text(encoding="utf-8", errors="ignore")
        if "ConfigIconMask" in content:
            return candidate

    return candidates[0]


def extract_mrc(mrc_path, extract_dir):
    """Extract MRC file (it's a ZIP)."""
    extract_dir = Path(extract_dir)
    extract_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(mrc_path, "r") as z:
        z.extractall(extract_dir)
    return extract_dir


def build_final_zip(icons_dir, transform_config_path, output_zip_path):
    """
    Build the final theme ZIP:
      res/drawable-xxhdpi/*.png
      transform_config.xml
    """
    icons_dir = Path(icons_dir)
    output_zip_path = Path(output_zip_path)
    output_zip_path.parent.mkdir(parents=True, exist_ok=True)

    icon_files = list(icons_dir.glob("*.png"))

    with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Add transform_config.xml
        zf.write(transform_config_path, "transform_config.xml")

        # Add icons
        for icon in icon_files:
            zf.write(icon, f"res/drawable-xxhdpi/{icon.name}")

    return len(icon_files)


def patch_mrc(mrc_path, icons_dir, transform_config_path, output_mrc_path):
    """
    Replace the icons and transform_config in an existing MRC with our own.
    Keeps any other files in the MRC intact.
    """
    mrc_path = Path(mrc_path)
    icons_dir = Path(icons_dir)
    output_mrc_path = Path(output_mrc_path)

    icon_files = list(icons_dir.glob("*.png"))

    with zipfile.ZipFile(mrc_path, "r") as src_zip:
        existing_names = src_zip.namelist()

        with zipfile.ZipFile(output_mrc_path, "w", zipfile.ZIP_DEFLATED) as dst_zip:
            # Copy non-icon, non-transform files from original
            skip_prefixes = ("res/drawable", "transform_config")
            for name in existing_names:
                if not any(name.startswith(p) for p in skip_prefixes):
                    dst_zip.writestr(name, src_zip.read(name))

            # Write new transform_config
            dst_zip.write(transform_config_path, "transform_config.xml")

            # Write new icons
            for icon in icon_files:
                dst_zip.write(icon, f"res/drawable-xxhdpi/{icon.name}")

    return len(icon_files)


def write_default_transform_config(output_path):
    """Write the built-in rounded-square transform_config.xml."""
    Path(output_path).write_text(DEFAULT_TRANSFORM_CONFIG, encoding="utf-8")
