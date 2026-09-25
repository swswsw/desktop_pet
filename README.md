# buildwithgemini-desktop_pet

# 🐑 Desktop Animated Sheep Pet

An interactive, animated desktop sheep pet for Linux. Designed with procedural pixel art animations, realistic physics, sound effects, needs/Tamagotchi stats, and rich user interactions.

The pet starts near the **bottom-right** of your screen and can be freely **moved anywhere by click and drag**!

![Animations Showcase](animations_showcase.png)
![Customizations Showcase](customizations_showcase.png)

---

## 🚀 How to Run

### Method 1: Desktop Shortcut (Easiest)
Double-click the **Desktop Sheep Pet** (`SheepPet.desktop`) shortcut located on your Desktop.

---

### Method 2: Terminal Launcher Script
Open a terminal and run:
```bash
cd /config/Desktop/test2
./launch_pet.sh
```

To run it in the background so you can close the terminal:
```bash
cd /config/Desktop/test2
./launch_pet.sh > /dev/null 2>&1 &
```

---

### Method 3: Python Command Line
You can run it directly with Python and customize options:

```bash
cd /config/Desktop/test2
python3 main.py
```

#### CLI Options & Customizations:
| Flag | Description | Examples |
|---|---|---|
| `--color` | Wool color palette | `white`, `pink`, `black`, `golden`, `mint`, `lavender`, `sky_blue`, `rainbow` |
| `--accessory` | Hat or accessory | `none`, `flower_crown`, `sunglasses`, `party_hat`, `bell_collar`, `top_hat` |
| `--name` | Custom name for your sheep | `--name "Bella"` |
| `--count` | Number of sheep to spawn (Herd Mode) | `--count 3` |
| `--scale` | Pixel art scaling factor (default: 3) | `--scale 4` (larger), `--scale 2` (smaller) |
| `--no-sound` | Start with sound effects muted | `--no-sound` |

**Examples:**
```bash
# Spawn a pink sheep wearing a flower crown named Bella:
python3 main.py --color pink --accessory flower_crown --name "Bella"

# Spawn a flock of 3 sheep friends:
python3 main.py --count 3

# Run silently with extra large pixels:
python3 main.py --scale 4 --no-sound
```

---

### How to Stop / Close the Pet:
- **Via Mouse**: Right-click the sheep and select **"❌ Quit Pet"**.
- **Via Terminal**:
  ```bash
  pkill -f "python3.*main.py"
  ```

---

## 🎮 Controls & Interactions

| Action | Control | What Happens |
|---|---|---|
| **Move the Pet** | **Click & Drag** (Hold Left Click) | Pick up the sheep and move it anywhere on your screen. Release to place it. |
| **Pet the Sheep** | **Quick Left-Click (Tap)** | Blushes, jumps for joy, spawns floating hearts (`♥`), and purrs. |
| **Acrobatic Trick** | **Double-Click** | Performs an acrobatic 360° somersault flip! |
| **Open Menu** | **Right-Click** | Opens context menu to feed treats, shear wool, change colors, put on hats, or view stats. |
| **Feed Snacks** | Right-Click ➔ **☘ Feed Treat...** | Drop apples (🍎), clovers (☘), cookies (🍪), or carrots (🥕) for the sheep to run over and eat. |
| **Drop to Floor** | Right-Click ➔ **⬇ Drop to Bottom Floor** | If perched high up, drops the sheep back down with gravity physics and a bounce. |
| **Status Card** | Right-Click ➔ **📊 Pet Status Card** | Displays Tamagotchi gauges (Happiness, Fullness, Energy, Wool Puffiness). |

---

## ✨ Features

- **Starting Position**: Starts near the bottom-right corner of the desktop, on top of the taskbar facing inward.
- **Physics & Drag-and-Drop**: Moves smoothly with cursor; drops securely onto the desktop or snaps flush to the taskbar floor.
- **Procedural Pixel-Art Animations**:
  - **Idle**: Blinking eyes, gentle breathing wool fluff, tail wiggles.
  - **Walking / Trotting**: Smooth trot cycle wandering across your screen.
  - **Grazing**: Nibbles on clover and grass with sweet flower pops.
  - **Happy Petting**: Bounces playfully with blushing cheeks and hearts (`♥`).
  - **Drag / Dangle**: Pedals little legs in mid-air with wide surprised eyes `(O.O)`.
  - **Falling & Landing**: Wind resistance fall with squash-and-stretch landing dust puffs.
  - **Acrobatic Flip**: Full 360° rotation trick.
  - **Sleeping**: Curls into a snug cloud ball with floating `Zzz` bubbles.
  - **Sheared & Sweaters**: Shear its wool to reveal a cozy red striped sweater! Wool grows back over time.
- **Audio Synthesizer**: Built-in 8-bit procedural sound effects (baa, munch, pop, boing, chime).
- **Settings Persistence**: Custom name, wool color, accessory, and stats are saved to `~/.config/desktop_sheep_pet/settings.json`.

---

## 📂 Project Architecture

```
/config/Desktop/test2/
├── pet/
│   ├── __init__.py
│   ├── sprites.py       # Procedural pixel-art sprite engine & caching
│   ├── audio.py         # 8-bit sound synthesis (WAV) & QtMultimedia player
│   ├── food_item.py     # Interactive falling snack widgets
│   ├── sheep_widget.py  # Main pet window, drag-and-drop, physics & AI
│   ├── dialogs.py       # Status card HUD, Style dialog, and Help guide
│   └── storage.py       # State & settings persistence (JSON)
├── main.py              # Application lifecycle, herd manager & CLI options
├── launch_pet.sh        # Bash runner script
├── test_pet.py          # Automated verification test suite
├── SheepPet.desktop     # Desktop launcher shortcut
└── README.md            # Documentation
```
