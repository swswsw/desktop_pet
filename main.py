import os
import sys

# Ensure X11/xcb backend is used on Linux desktops so absolute positioning
# and interactive click-and-drag window movement work reliably.
# (Pure Wayland xdg-shell intentionally ignores application move() requests and centers all windows)
if "QT_QPA_PLATFORM" not in os.environ:
    os.environ["QT_QPA_PLATFORM"] = "xcb"

import argparse
import signal
from typing import List
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon

from pet.sprites import SpriteManager
from pet.audio import SoundManager
from pet.sheep_widget import SheepWidget


class PetApp:
    """Manages the sheep pet application lifecycle and multi-pet herd."""

    def __init__(self, args):
        self.args = args
        self.scale = args.scale
        self.sprite_mgr = SpriteManager(scale=self.scale)
        self.sound_mgr = SoundManager()
        if args.no_sound:
            self.sound_mgr.set_muted(True)

        self.pets: List[SheepWidget] = []
        self._init_tray()

    def _init_tray(self):
        """Create a system tray icon if system supports it."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.tray = None
            return

        tray_pix = self.sprite_mgr.get_sheep_frame("idle", 0, "white", "none")
        self.tray = QSystemTrayIcon(QIcon(tray_pix), QApplication.instance())
        self.tray.setToolTip("Desktop Sheep Pet")

        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #26252d;
                color: #f0f0f4;
                border: 1px solid #484656;
                padding: 4px;
            }
            QMenu::item:selected {
                background-color: #4f46e5;
                color: white;
            }
        """)

        act_spawn = menu.addAction("🐑 Spawn Sheep Friend")
        act_spawn.triggered.connect(self.spawn_pet)

        act_pet_all = menu.addAction("♥ Pet All Sheep")
        act_pet_all.triggered.connect(self.pet_all)

        act_feed_all = menu.addAction("🍎 Feed All Sheep")
        act_feed_all.triggered.connect(lambda: self.feed_all("apple"))

        menu.addSeparator()

        act_mute = menu.addAction("🔊 Toggle Sound")
        act_mute.triggered.connect(self.toggle_sound)

        menu.addSeparator()

        act_quit = menu.addAction("❌ Exit All Pets")
        act_quit.triggered.connect(self.quit_app)

        self.tray.setContextMenu(menu)
        self.tray.show()

    def spawn_pet(self, wool_color=None, accessory=None, name=None) -> SheepWidget:
        """Spawn a new sheep pet onto the desktop."""
        pet_id = len(self.pets) + 1
        pet = SheepWidget(
            sprite_mgr=self.sprite_mgr,
            sound_mgr=self.sound_mgr,
            pet_id=pet_id,
        )

        if wool_color:
            pet.wool_color = wool_color
        if accessory:
            pet.accessory = accessory
        if name:
            pet.pet_name = name
        elif pet_id > 1:
            pet.pet_name = f"Buddy {pet_id}"

        pet.destroyed.connect(lambda: self._on_pet_destroyed(pet))
        pet.show()
        self.pets.append(pet)
        return pet

    def _on_pet_destroyed(self, pet):
        if pet in self.pets:
            self.pets.remove(pet)
        if not self.pets:
            QApplication.instance().quit()

    def pet_all(self):
        for p in list(self.pets):
            p.pet_action()

    def feed_all(self, food_type="apple"):
        for p in list(self.pets):
            p.spawn_food(food_type)

    def toggle_sound(self):
        new_muted = self.sound_mgr.toggle_muted()
        for p in self.pets:
            p.sound_muted = new_muted
            p.save_state()

    def quit_app(self):
        for p in list(self.pets):
            p.save_state()
            p.close()
        QApplication.instance().quit()


def main():
    parser = argparse.ArgumentParser(description="Desktop Animated Sheep Pet")
    parser.add_argument("--color", type=str, default=None, help="Wool color (white, pink, black, golden, mint, lavender, sky_blue, rainbow)")
    parser.add_argument("--accessory", type=str, default=None, help="Accessory (none, sunglasses, flower_crown, party_hat, bell_collar, top_hat)")
    parser.add_argument("--name", type=str, default=None, help="Sheep pet name")
    parser.add_argument("--count", type=int, default=1, help="Number of sheep to spawn (default: 1)")
    parser.add_argument("--scale", type=int, default=3, help="Pixel art scale factor (default: 3)")
    parser.add_argument("--no-sound", action="store_true", help="Start with audio muted")

    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setApplicationName("Desktop Sheep Pet")
    app.setQuitOnLastWindowClosed(True)

    # Clean signal handling (Ctrl+C)
    signal.signal(signal.SIGINT, lambda *args: app.quit())
    sig_timer = QTimer()
    sig_timer.start(500)
    sig_timer.timeout.connect(lambda: None)  # allows python interpreter to process SIGINT

    pet_app = PetApp(args)

    for i in range(max(1, args.count)):
        color = args.color
        if not color and i > 0:
            # Variety for buddies
            palette_names = ["pink", "golden", "mint", "lavender", "sky_blue", "black"]
            color = palette_names[(i - 1) % len(palette_names)]
        pet_app.spawn_pet(wool_color=color, accessory=args.accessory, name=args.name)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
