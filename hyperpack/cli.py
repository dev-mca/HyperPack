"""
HyperPack interactive CLI
"""

import os
import sys
import shutil
import tempfile
import zipfile
from pathlib import Path

from . import console
from . import adb
from . import icons
from . import theme


TOTAL_STEPS = 7


def check_requirements():
    """Check Python deps and ADB."""
    console.section("Checking requirements")

    # ADB
    if adb.check_adb():
        console.success("ADB found")
    else:
        console.error("ADB not found. Please install Android Platform Tools.")
        console.info("Download: https://developer.android.com/tools/releases/platform-tools")
        sys.exit(1)

    # Pillow (optional)
    try:
        import PIL
        console.success(f"Pillow found (icon resizing available)")
        return True
    except ImportError:
        console.warn("Pillow not installed – icon resizing will be skipped.")
        console.info("Install with: pip install Pillow")
        return False


def check_device():
    """Ensure exactly one device is connected."""
    console.section("Checking device connection")
    devices = adb.get_devices()

    if not devices:
        console.error("No device found. Make sure:")
        console.info("1. USB Debugging is enabled (Settings → Developer options)")
        console.info("2. Phone is connected via USB")
        console.info("3. You tapped 'Allow' on the phone")
        sys.exit(1)

    if len(devices) > 1:
        console.warn(f"{len(devices)} devices connected. Using first: {devices[0]}")
    else:
        console.success(f"Device connected: {devices[0]}")

    return devices[0]


def get_package_name():
    """Ask user for icon pack package name."""
    console.section("Icon Pack")
    console.info("Find the package name in: Settings → Apps → [Icon Pack App] → App info")
    console.info("Or use the 'Package Name Viewer' app from Play Store")
    print()

    package = console.ask("Enter icon pack package name", "dev.narikdesign.nothingness")
    if not package:
        console.error("Package name is required.")
        sys.exit(1)

    return package.strip()


def pull_apk(package_name, work_dir):
    """Pull the base.apk from device."""
    console.section("Pulling APK from device")

    apk_paths = adb.get_apk_paths(package_name)
    if not apk_paths:
        console.error(f"Package '{package_name}' not found on device.")
        console.info("Make sure the icon pack app is installed.")
        sys.exit(1)

    # Always use base.apk
    base_apk_remote = next((p for p in apk_paths if p.endswith("base.apk")), apk_paths[0])
    console.info(f"Found: {base_apk_remote}")

    local_apk = work_dir / "base.apk"
    console.progress("Pulling APK…")
    ok = adb.pull_file(base_apk_remote, local_apk)

    if not ok or not local_apk.exists():
        console.error("Failed to pull APK.")
        sys.exit(1)

    size_mb = local_apk.stat().st_size / 1_000_000
    console.done(f"APK pulled ({size_mb:.1f} MB)")
    return local_apk


def extract_and_process(apk_path, work_dir, has_pillow):
    """Extract APK, find icons, rename, optionally resize."""
    console.section("Extracting and processing icons")

    # Extract
    extract_dir = work_dir / "extracted"
    console.progress("Extracting APK…")
    icons.extract_apk(apk_path, extract_dir)
    console.done("APK extracted")

    # Find icon folder
    res_dir = extract_dir / "res"
    icon_folder, icon_count = icons.find_icon_folder(res_dir)
    if not icon_folder:
        console.error("Could not find icon folder inside APK.")
        sys.exit(1)
    console.success(f"Found {icon_count} icons in {icon_folder.name}")

    # Find appfilter.xml
    appfilter = icons.find_appfilter(extract_dir)
    if not appfilter:
        console.error("appfilter.xml not found in APK.")
        sys.exit(1)
    console.success(f"Found appfilter.xml")

    # Copy icons to staging
    copy_dir = work_dir / "copy_icon"
    copy_dir.mkdir(exist_ok=True)
    console.progress("Copying icons…")
    copied = 0
    for f in icon_folder.glob("*.png"):
        shutil.copy2(f, copy_dir / f.name)
        copied += 1
    if copied == 0:
        console.error("No PNG icons found in the icon folder.")
        console.info("This icon pack may use a different format (e.g. WebP or XML drawables).")
        sys.exit(1)
    console.done(f"Icons staged ({copied} files)")

    # Rename icons using appfilter
    rename_dir = work_dir / "icon_rename"
    console.progress("Renaming icons to HyperOS package names…")
    try:
        success, missing = icons.rename_icons(copy_dir, appfilter, rename_dir)
    except RuntimeError as e:
        console.error(str(e))
        console.info("Try a different icon pack that uses a standard appfilter.xml format.")
        sys.exit(1)

    if success == 0:
        console.error("No icons were renamed -- appfilter.xml mappings did not match any icon files.")
        console.info("The icon pack may use a non-standard naming scheme.")
        sys.exit(1)

    console.done(f"Renamed {success} icons  ({missing} skipped – no match in appfilter)")

    final_icons_dir = rename_dir

    # Optional resize
    if has_pillow:
        # Detect current size
        sample = next(rename_dir.glob("*.png"), None)
        if sample:
            size = icons.get_icon_size(sample)
            if size:
                current_w = size[0]
                console.info(f"Current icon size: {current_w}×{current_w}px")
                do_resize = console.ask_yes_no(
                    f"Resize icons? (recommended if size differs from HyperOS standard 192px)",
                    default=current_w != 192
                )
                if do_resize:
                    target = console.ask("Target size in pixels", str(current_w))
                    try:
                        target_px = int(target)
                    except ValueError:
                        target_px = current_w

                    resize_dir = work_dir / "icon_resize"
                    console.progress(f"Resizing to {target_px}px…")
                    ok, fail = icons.resize_icons(rename_dir, resize_dir, target_px)
                    console.done(f"Resized {ok} icons ({fail} failed)")
                    final_icons_dir = resize_dir

    return final_icons_dir


def get_transform_config(work_dir):
    """Get transform_config.xml from device MRC or use built-in default."""
    console.section("Getting transform_config.xml")

    mrc_files = adb.list_mrc_files()

    if not mrc_files:
        console.warn("No MRC files found on device.")
        console.warn("Download any free icon theme from the Xiaomi Theme Store first,")
        console.warn("then re-run HyperPack. Using built-in default for now.")
        out = work_dir / "transform_config.xml"
        theme.write_default_transform_config(out)
        return out

    newest = mrc_files[0]
    console.info(f"Found {len(mrc_files)} theme(s) on device")
    console.info(f"Using newest: {newest['name']}  ({newest['size']//1000} KB, {newest['date']})")

    # Pull and extract MRC
    mrc_local = work_dir / "dummy.mrc"
    console.progress("Pulling theme from device…")
    ok = adb.pull_mrc(newest["name"], mrc_local)
    if not ok:
        console.warn("Could not pull MRC. Using built-in default.")
        out = work_dir / "transform_config.xml"
        theme.write_default_transform_config(out)
        return out, None

    mrc_extract = work_dir / "mrc_extract"
    theme.extract_mrc(mrc_local, mrc_extract)
    console.done("Theme pulled")

    # Find transform_config
    transform = theme.find_transform_config(mrc_extract)
    if not transform:
        console.warn("transform_config.xml not found in theme. Using built-in default.")
        out = work_dir / "transform_config.xml"
        theme.write_default_transform_config(out)
        return out, newest["name"]

    console.success(f"Found transform_config.xml")
    return transform, newest["name"]


def build_and_deploy(final_icons_dir, transform_config, mrc_name, work_dir):
    """Build the patched MRC and push to device."""
    console.section("Building and deploying theme")

    if mrc_name:
        # Patch existing MRC
        original_mrc = work_dir / "dummy.mrc"
        output_mrc = work_dir / "hyperpack_output.mrc"

        console.progress("Building patched theme…")
        count = theme.patch_mrc(original_mrc, final_icons_dir, transform_config, output_mrc)
        console.done(f"Theme built with {count} icons")

        # Push back
        size_mb = output_mrc.stat().st_size / 1_000_000
        console.progress(f"Pushing theme to device ({size_mb:.1f} MB)…")
        ok = adb.push_mrc(output_mrc, mrc_name)

        if ok:
            console.done("Theme pushed to device!")
        else:
            console.error("Failed to push theme to device.")
            console.info(f"Manual push: adb push {output_mrc} {adb.ICONS_PATH}/{mrc_name}")
    else:
        # No MRC on device – build standalone ZIP for manual install
        output_zip = work_dir / "HyperPack_Final.zip"
        console.progress("Building theme ZIP…")
        count = theme.build_final_zip(final_icons_dir, transform_config, output_zip)
        console.done(f"ZIP built with {count} icons")

        dest = Path.home() / "Downloads" / "HyperPack_Final.zip"
        shutil.copy2(output_zip, dest)
        console.success(f"Saved to: {dest}")
        console.info("Push manually: adb push ~/Downloads/HyperPack_Final.zip /sdcard/Download/")


def print_final_instructions(mrc_name):
    """Tell user what to do on the phone."""
    console.section("Almost done! Apply on your phone")
    print()
    if mrc_name:
        print(f"  {console.Color.WHITE}1.{console.Color.RESET}  Open the Xiaomi Theme Store")
        print(f"  {console.Color.WHITE}2.{console.Color.RESET}  Go to Icons → Downloaded")
        print(f"  {console.Color.WHITE}3.{console.Color.RESET}  Tap Apply on the dummy theme")
        print(f"  {console.Color.WHITE}4.{console.Color.RESET}  Enjoy your icon pack! 🎉")
    else:
        print(f"  {console.Color.WHITE}1.{console.Color.RESET}  Download a free icon theme from Theme Store (any theme)")
        print(f"  {console.Color.WHITE}2.{console.Color.RESET}  Push the ZIP with ADB and repeat step 3 in the guide")
    print()


def main():
    console.banner()

    # Step 1: Requirements
    console.step(1, TOTAL_STEPS, "Requirements")
    has_pillow = check_requirements()

    # Step 2: Device
    console.step(2, TOTAL_STEPS, "Device")
    check_device()

    # Step 3: Package name
    console.step(3, TOTAL_STEPS, "Icon Pack")
    package_name = get_package_name()

    # Working directory
    work_dir = Path(tempfile.mkdtemp(prefix="hyperpack_"))
    console.info(f"Working directory: {work_dir}")

    try:
        # Step 4: Pull APK
        console.step(4, TOTAL_STEPS, "Pull APK")
        apk_path = pull_apk(package_name, work_dir)

        # Step 5: Process icons
        console.step(5, TOTAL_STEPS, "Process Icons")
        final_icons_dir = extract_and_process(apk_path, work_dir, has_pillow)

        # Step 6: Transform config
        console.step(6, TOTAL_STEPS, "Transform Config")
        result = get_transform_config(work_dir)
        if isinstance(result, tuple):
            transform_config, mrc_name = result
        else:
            transform_config, mrc_name = result, None

        # Step 7: Build & deploy
        console.step(7, TOTAL_STEPS, "Deploy")
        build_and_deploy(final_icons_dir, transform_config, mrc_name, work_dir)

        print_final_instructions(mrc_name)

    except KeyboardInterrupt:
        print()
        console.warn("Cancelled by user.")
        sys.exit(0)
    finally:
        # Cleanup
        if console.ask_yes_no("Clean up temporary files?", default=True):
            shutil.rmtree(work_dir, ignore_errors=True)
            console.success("Cleaned up.")
        else:
            console.info(f"Temp files kept at: {work_dir}")
