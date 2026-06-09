# HyperPack

> Install **any** Android icon pack on Xiaomi HyperOS — automatically.

HyperPack automates the entire process of converting a Play Store icon pack into a HyperOS-compatible theme and deploying it directly to your device via ADB. What used to take an hour of manual steps now takes about 60 seconds.

---

## Features

- 🎨 Supports any icon pack from the Play Store (free or paid)
- 📦 Automatically extracts, renames, and maps icons via `appfilter.xml`
- 🔄 Pulls `transform_config.xml` from your existing HyperOS themes
- 📐 Optional icon resizing with correct PNG metadata (via Pillow)
- 🚀 Pushes the finished theme directly to your device via ADB
- 💻 Works on **Windows**, **Linux**, and **macOS**
- 🧹 Cleans up all temporary files when done

---

## Requirements

| Requirement | Notes |
|---|---|
| Python 3.8+ | [python.org](https://www.python.org/downloads/) |
| ADB (Android Platform Tools) | [Download](https://developer.android.com/tools/releases/platform-tools) |
| Pillow (optional) | Icon resizing — `pip install Pillow` |
| Xiaomi device with HyperOS | USB Debugging enabled |

---

## Installation

```bash
git clone https://github.com/yourusername/hyperpack.git
cd hyperpack
pip install -r requirements.txt   # optional but recommended
```

---

## Usage

1. Connect your Xiaomi device via USB
2. Enable USB Debugging (Settings → Developer Options → USB Debugging)
3. Accept the "Allow USB Debugging" prompt on your phone
4. Install the icon pack you want from the Play Store
5. Download **any** free icon theme from the Xiaomi Theme Store (needed as a container)
6. Run HyperPack:

```bash
python hyperpack.py
```

HyperPack will walk you through the rest interactively.

---

## How it works

```
Play Store icon pack (.apk)
        │
        ▼
  Extract icons + appfilter.xml
        │
        ▼
  Rename icons to HyperOS package name format
  (com.app.name.png instead of app_name.png)
        │
        ▼
  (Optional) Resize to match HyperOS requirements
        │
        ▼
  Patch dummy theme .mrc with your icons
        │
        ▼
  Push patched theme to device via ADB
        │
        ▼
  Apply from Theme Store → Icons → Downloaded ✓
```

---

## Step-by-step on your phone

After HyperPack finishes:

1. Open **Xiaomi Theme Store**
2. Go to **Icons** → **Downloaded**
3. Tap **Apply** on the dummy theme
4. Done — your icon pack is active! 🎉

---

## FAQ

**Why do some apps still show their default icon?**  
The icon pack may not include every app. HyperOS falls back to the original icon for unsupported apps. More popular icon packs (like Nothingness, Lawnicons, etc.) cover thousands of apps.

**Do I need root?**  
No. HyperPack uses only ADB and standard file operations.

**Will this survive a theme update?**  
If you re-download or update the dummy theme from the Theme Store, the icons will reset. Just re-run HyperPack — it only takes about a minute.

**Which icon packs work best?**  
Any pack that includes an `appfilter.xml` works. Recommended:
- [Nothingness](https://play.google.com/store/apps/details?id=dev.narikdesign.nothingness)
- [Lawnicons](https://github.com/LawnchairLauncher/lawnicons)
- Whicons, Candycons, Delta, etc.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `ADB not found` | Add platform-tools to your PATH |
| `Package not found` | Make sure icon pack is installed on the phone |
| `No MRC files found` | Download any free theme from the Theme Store first |
| `Access denied` on MRC folder | Use ADB — MT Manager may not have permission |
| Icons look stretched | Re-run and choose a different target resize |

---

## Contributing

Pull requests are welcome! If you've found a workaround for a specific device or HyperOS version, please open an issue or PR.

---

## Credits

Based on the community guide by [u/6oldsmith](https://www.reddit.com/r/HyperOS/comments/1ruof69/) on r/HyperOS.

---

## License

MIT

## Contributors

- [dev-mca](https://github.com/dev-mca) — Project creator
- Community contributor (r/HyperOS) — XML-based appfilter parser for non-standard icon pack formats
