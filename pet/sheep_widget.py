"""Main interactive Sheep Pet desktop widget with physics, AI, and animations."""

import random
import math
from typing import List, Optional
from PyQt6.QtWidgets import QWidget, QMenu, QApplication
from PyQt6.QtCore import Qt, QTimer, QPoint, QRect, QRectF
from PyQt6.QtGui import (
    QPainter, QColor, QFont, QPen, QBrush, QAction, QCursor
)

from pet.sprites import SpriteManager
from pet.audio import SoundManager
from pet.storage import load_settings, save_settings
from pet.food_item import FoodItem
from pet.dialogs import PetStatusDialog, StyleDialog, HelpDialog


THOUGHTS_GENERAL = [
    "Baaaa~!",
    "Fluffy as a cloud ☁",
    "Chewing on sweet grass ☘",
    "Such a nice desktop day!",
    "Life is woolly good!",
    "Baa baa baa~",
    "Looking out for wolves... none found!",
]
THOUGHTS_HUNGRY = [
    "My tummy is rumbling...",
    "Got any apples or clover?",
    "Craving a little snack!",
]
THOUGHTS_SLEEPY = [
    "So sleepy... *yawn*",
    "Is it bedtime yet?",
    "Counting my fellow sheep... 1, 2, zzz",
]
THOUGHTS_HAPPY = [
    "I love you! ♥",
    "Best human ever!",
    "Yay yay yay!",
    "Feeling so warm and loved!",
]


class SheepWidget(QWidget):
    """The interactive animated sheep pet window."""

    def __init__(self, sprite_mgr: Optional[SpriteManager] = None, sound_mgr: Optional[SoundManager] = None, pet_id: int = 1):
        super().__init__()
        self.pet_id = pet_id
        self.sprite_mgr = sprite_mgr or SpriteManager(scale=3)
        self.sound_mgr = sound_mgr or SoundManager()

        # Load persisted settings
        self.settings = load_settings()
        self.pet_name = self.settings.get("pet_name", "Fluffy")
        self.wool_color = self.settings.get("wool_color", "white")
        self.accessory = self.settings.get("accessory", "none")
        self.behavior_mode = self.settings.get("behavior_mode", "wander")
        self.sound_muted = self.settings.get("sound_muted", False)
        self.sound_mgr.set_muted(self.sound_muted)

        # Pet Stats & Needs
        self.stats = {
            "happiness": float(self.settings.get("happiness", 85)),
            "hunger": float(self.settings.get("hunger", 75)),
            "energy": float(self.settings.get("energy", 90)),
            "wool_puff": float(self.settings.get("wool_puff", 60)),
            "sheared": bool(self.settings.get("sheared", False)),
        }

        # Window styling
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        # Snug size: 130 wide x 120 high
        self.setFixedSize(130, 120)

        # Position and physics
        self.screen_geo = QApplication.primaryScreen().availableGeometry()
        self.default_floor_y = self.screen_geo.bottom() - self.height() + 2
        self.floor_y = self.default_floor_y

        # Start near the bottom-right of the screen
        margin_right = 50 + (self.pet_id - 1) * 110
        start_x = max(self.screen_geo.left() + 20, self.screen_geo.right() - self.width() - margin_right)
        self.pos_x = float(start_x)
        self.pos_y = float(self.floor_y)
        self.vx = 0.0
        self.vy = 0.0
        self.gravity = 1.3
        self.bounce = -0.42
        self.is_falling = False

        # State & Animation
        self.state = "idle"  # idle, walk, graze, sleep, drag, fall, land, happy, roll, sheared
        self.frame_idx = 0
        self.facing_left = True  # Face inwards towards desktop center
        self.state_ticks = 0
        self.state_target_ticks = 60

        # Drag tracking and interactive cursor
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.is_dragging = False
        self._drag_pos = QPoint()
        self._drag_start_global = QPoint()

        # Thought bubble & Particles
        self.thought_text = ""
        self.thought_ticks = 0
        self.particles = []  # list of dicts

        # Active food items on screen
        self.active_food: List[FoodItem] = []
        self.target_food: Optional[FoodItem] = None

        # Child dialogs
        self.status_dialog: Optional[PetStatusDialog] = None

        self.move(int(self.pos_x), int(self.pos_y))

        # Main animation timer (30 FPS)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._game_loop)
        self.timer.start(33)

        # Random idle thought greeting
        self.say("Baaaa~! Hello!")

    def _get_screen_bounds(self) -> QRect:
        screen = self.screen() or QApplication.primaryScreen()
        return screen.availableGeometry()

    def _game_loop(self):
        """Main update step for physics, AI, needs, and particles."""
        self.state_ticks += 1
        screen_geo = self._get_screen_bounds()
        self.default_floor_y = screen_geo.bottom() - self.height() + 2
        self.floor_y = min(self.default_floor_y, self.floor_y)

        # 1. Update Needs & Stats
        self._update_stats()

        # 2. Physics & Falling
        if not self.is_dragging:
            self._update_physics(screen_geo)

        # 3. AI Behavior (if not dragging or falling)
        if not self.is_dragging and not self.is_falling:
            self._update_ai(screen_geo)

        # 4. Particles & Thoughts
        self._update_particles()
        if self.thought_ticks > 0:
            self.thought_ticks -= 1
            if self.thought_ticks == 0:
                self.thought_text = ""

        # 5. Animation frame step
        if self.state in ("walk", "graze", "roll"):
            if self.state_ticks % 3 == 0:
                self.frame_idx = (self.frame_idx + 1)
        elif self.state in ("idle", "sleep", "happy", "drag"):
            if self.state_ticks % 6 == 0:
                self.frame_idx = (self.frame_idx + 1)
        elif self.state == "land":
            if self.state_ticks % 4 == 0:
                self.frame_idx += 1
                if self.frame_idx >= 2:
                    self.set_state("idle", 40)

        # Redraw
        self.update()

    def _update_stats(self):
        """Simulate Tamagotchi hunger, energy, happiness decay, and wool growth."""
        if self.state_ticks % 100 == 0:
            # Hunger slowly drops
            if self.state != "graze":
                self.stats["hunger"] = max(0.0, self.stats["hunger"] - 0.2)

            # Energy changes
            if self.state == "sleep":
                self.stats["energy"] = min(100.0, self.stats["energy"] + 1.2)
                if self.stats["energy"] >= 99.0 and self.behavior_mode != "sleepy":
                    self.wake_up()
            else:
                self.stats["energy"] = max(0.0, self.stats["energy"] - 0.1)

            # Wool growth
            if self.stats["sheared"]:
                self.stats["wool_puff"] = min(100.0, self.stats["wool_puff"] + 0.8)
                if self.stats["wool_puff"] >= 75.0:
                    self.stats["sheared"] = False
                    self.say("My wool grew back! Fluffy again!")
            else:
                self.stats["wool_puff"] = min(100.0, self.stats["wool_puff"] + 0.1)

            # Happiness slight decay if very hungry or tired
            if self.stats["hunger"] < 25.0 or self.stats["energy"] < 20.0:
                self.stats["happiness"] = max(0.0, self.stats["happiness"] - 0.3)

            # Update dialog if visible
            if self.status_dialog and self.status_dialog.isVisible():
                self.status_dialog.update_stats()

    def _update_physics(self, screen_geo: QRect):
        """Apply gravity, collisions, and screen boundaries."""
        if self.pos_y < self.floor_y or abs(self.vy) > 0.5:
            self.is_falling = True
            if self.state not in ("fall", "land", "roll"):
                self.set_state("fall")

            self.vy += self.gravity
            self.pos_y += self.vy
            self.pos_x += self.vx
            self.vx *= 0.96  # air drag

            # Floor contact
            if self.pos_y >= self.floor_y:
                self.pos_y = self.floor_y
                if abs(self.vy) > 3.0:
                    self.vy = self.vy * self.bounce
                    self.sound_mgr.play("boing")
                    self.spawn_particle("dust", self.width() // 2, self.height() - 10)
                    self.set_state("land", 10)
                else:
                    self.vy = 0.0
                    self.vx = 0.0
                    self.is_falling = False
                    self.set_state("idle", 40)
        else:
            self.is_falling = False
            self.pos_y = self.floor_y

        # Screen left/right bounds
        min_x = screen_geo.left() - 10
        max_x = screen_geo.right() - self.width() + 10
        if self.pos_x < min_x:
            self.pos_x = min_x
            self.vx = abs(self.vx) * 0.5
            self.facing_left = False
        elif self.pos_x > max_x:
            self.pos_x = max_x
            self.vx = -abs(self.vx) * 0.5
            self.facing_left = True

        self.move(int(self.pos_x), int(self.pos_y))

    def _update_ai(self, screen_geo: QRect):
        """Manage autonomous wandering, grazing, seeking snacks, and sleeping."""
        # 1. Target Food Check
        if self.active_food:
            # Pick closest food
            closest = None
            min_dist = 999999
            for food in self.active_food:
                if food.isVisible():
                    fc = food.get_center()
                    dist = abs(fc.x() - (self.pos_x + self.width() // 2))
                    if dist < min_dist:
                        min_dist = dist
                        closest = food
            self.target_food = closest
        else:
            self.target_food = None

        # If food is spotted, walk towards it!
        if self.target_food:
            food_center_x = self.target_food.get_center().x()
            sheep_center_x = self.pos_x + self.width() // 2
            dx = food_center_x - sheep_center_x

            if abs(dx) > 15:
                self.state = "walk"
                speed = 2.4
                if dx < 0:
                    self.facing_left = True
                    self.pos_x -= speed
                else:
                    self.facing_left = False
                    self.pos_x += speed
                self.move(int(self.pos_x), int(self.pos_y))
            else:
                # Arrived at food! Consume it
                self.target_food.eat()
                if self.target_food in self.active_food:
                    self.active_food.remove(self.target_food)
                self.target_food = None
                self.sound_mgr.play("munch")
                self.stats["hunger"] = min(100.0, self.stats["hunger"] + 35.0)
                self.stats["happiness"] = min(100.0, self.stats["happiness"] + 20.0)
                self.say("Nom nom nom! So tasty! ♥")
                self.spawn_particle("heart", self.width() // 2, 20)
                self.set_state("graze", 60)
            return

        # 2. Curious Mode (Follow Mouse)
        if self.behavior_mode == "follow" and self.state not in ("sleep", "roll"):
            mouse_x = QCursor.pos().x()
            sheep_center_x = self.pos_x + self.width() // 2
            dx = mouse_x - sheep_center_x
            if abs(dx) > 40:
                self.state = "walk"
                speed = 2.0
                if dx < 0:
                    self.facing_left = True
                    self.pos_x -= speed
                else:
                    self.facing_left = False
                    self.pos_x += speed
                self.move(int(self.pos_x), int(self.pos_y))
            else:
                if self.state == "walk":
                    self.set_state("idle", 30)
            return

        # 3. Regular autonomous transitions
        if self.state_ticks >= self.state_target_ticks:
            if self.behavior_mode == "stay":
                self.set_state("idle", random.randint(50, 120))
                return

            if self.behavior_mode == "sleepy" or self.stats["energy"] < 15.0:
                if self.state != "sleep":
                    self.set_state("sleep", random.randint(120, 240))
                    self.say("Zzz... sleepy time...")
                    return

            # Pick next random state
            weights = [("idle", 35), ("walk", 40), ("graze", 20), ("sleep", 5)]
            choices, w = zip(*weights)
            next_state = random.choices(choices, weights=w)[0]

            if next_state == "idle":
                self.set_state("idle", random.randint(40, 100))
                if random.random() < 0.2:
                    self._say_random_thought()

            elif next_state == "walk":
                self.facing_left = random.choice([True, False])
                self.set_state("walk", random.randint(50, 120))

            elif next_state == "graze":
                self.set_state("graze", random.randint(60, 120))
                self.sound_mgr.play("munch")
                self.stats["hunger"] = min(100.0, self.stats["hunger"] + 15.0)

            elif next_state == "sleep":
                self.set_state("sleep", random.randint(100, 200))
                self.say("Zzz...")

        # If currently walking, move horizontally
        if self.state == "walk":
            speed = 1.4
            if self.facing_left:
                self.pos_x -= speed
            else:
                self.pos_x += speed
            self.move(int(self.pos_x), int(self.pos_y))

    def _say_random_thought(self):
        if not self.settings.get("show_thoughts", True):
            return
        if self.stats["hunger"] < 35.0:
            text = random.choice(THOUGHTS_HUNGRY)
        elif self.stats["energy"] < 25.0:
            text = random.choice(THOUGHTS_SLEEPY)
        elif self.stats["happiness"] > 85.0:
            text = random.choice(THOUGHTS_HAPPY)
        else:
            text = random.choice(THOUGHTS_GENERAL)
        self.say(text)

    def say(self, text: str, duration_ticks: int = 100):
        """Display a comic speech bubble above the sheep."""
        self.thought_text = text
        self.thought_ticks = duration_ticks

    def set_state(self, state: str, target_ticks: int = 60):
        """Change pet animation state."""
        self.state = state
        self.state_ticks = 0
        self.state_target_ticks = target_ticks
        self.frame_idx = 0

    def spawn_particle(self, p_type: str, x: int, y: int):
        """Spawn floating particle that drifts upward."""
        self.particles.append({
            "type": p_type,
            "x": float(x),
            "y": float(y),
            "vx": (random.random() - 0.5) * 1.5,
            "vy": -1.2 - random.random() * 1.0,
            "alpha": 1.0,
            "life": 30,
        })

    def _update_particles(self):
        survivors = []
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["life"] -= 1
            p["alpha"] = max(0.0, p["life"] / 30.0)
            if p["life"] > 0:
                survivors.append(p)
        self.particles = survivors

    # User Actions
    def pet_action(self):
        """Pet the sheep: hearts, happy bounce, purr chime sound."""
        self.sound_mgr.play("happy")
        self.stats["happiness"] = min(100.0, self.stats["happiness"] + 15.0)
        self.set_state("happy", 45)
        self.say(random.choice(["♥ Purr baaa! ♥", "Hehehe, that tickles!", "So happy! ♥"]))
        for _ in range(3):
            px = random.randint(self.width() // 2 - 20, self.width() // 2 + 20)
            py = random.randint(30, 50)
            self.spawn_particle("heart", px, py)

    def do_trick(self):
        """Perform a joyful backflip / somersault roll."""
        self.sound_mgr.play("boing")
        self.set_state("roll", 24)
        self.say("Ta-daa! 360° flip!")
        self.spawn_particle("star", self.width() // 2, 25)

    def shear_sheep(self):
        """Shear sheep wool, leaving it in a cute red sweater."""
        if self.stats["sheared"]:
            return
        self.sound_mgr.play("pop")
        self.stats["sheared"] = True
        self.stats["wool_puff"] = 15.0
        self.say("Baa! Look at my new sweater!")
        self.set_state("sheared", 60)
        for _ in range(4):
            self.spawn_particle("dust", self.width() // 2 + random.randint(-15, 15), 50)

    def wake_up(self):
        """Wake up the sheep from sleep."""
        self.set_state("idle", 40)
        self.sound_mgr.play("baa")
        self.say("I'm awake and energized!")

    def spawn_food(self, food_type: str = "apple"):
        """Drop a delicious treat near the sheep."""
        drop_x = int(self.pos_x + (random.choice([-80, 80])))
        drop_y = int(self.pos_y - 120)
        screen_geo = self._get_screen_bounds()
        drop_x = max(screen_geo.left() + 20, min(screen_geo.right() - 60, drop_x))
        drop_y = max(screen_geo.top() + 20, drop_y)

        food = FoodItem(
            food_type=food_type,
            x=drop_x,
            y=drop_y,
            floor_y=screen_geo.bottom() + 1,
            sprite_manager=self.sprite_mgr,
        )
        food.consumed.connect(lambda f: self.active_food.remove(f) if f in self.active_food else None)
        food.expired.connect(lambda f: self.active_food.remove(f) if f in self.active_food else None)
        food.show()
        self.active_food.append(food)
        self.say(f"Ooh! A yummy {food_type}!")

    def save_state(self):
        """Persist current settings and stats."""
        data = {
            "pet_name": self.pet_name,
            "wool_color": self.wool_color,
            "accessory": self.accessory,
            "behavior_mode": self.behavior_mode,
            "sound_muted": self.sound_muted,
            "happiness": self.stats["happiness"],
            "hunger": self.stats["hunger"],
            "energy": self.stats["energy"],
            "wool_puff": self.stats["wool_puff"],
            "sheared": self.stats["sheared"],
        }
        save_settings(data)

    # Mouse Events
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self._drag_start_global = event.globalPosition().toPoint()
            self._drag_offset = event.globalPosition().toPoint() - self.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            self.set_state("drag", 99999)
            self.sound_mgr.play("baa")
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            self._show_context_menu(event.globalPosition().toPoint())
            event.accept()

    def mouseMoveEvent(self, event):
        if self.is_dragging and (event.buttons() & Qt.MouseButton.LeftButton):
            curr_global = event.globalPosition().toPoint()
            new_pos = curr_global - self._drag_offset

            # Clamp within screen bounds
            screen_geo = self._get_screen_bounds()
            min_x = screen_geo.left() - 10
            max_x = screen_geo.right() - self.width() + 10
            min_y = screen_geo.top()
            max_y = screen_geo.bottom() - self.height() + 2

            self.pos_x = float(max(min_x, min(max_x, new_pos.x())))
            self.pos_y = float(max(min_y, min(max_y, new_pos.y())))
            self.move(int(self.pos_x), int(self.pos_y))
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_dragging:
            self.is_dragging = False
            self.setCursor(Qt.CursorShape.PointingHandCursor)

            curr_global = event.globalPosition().toPoint()
            dist_moved = (curr_global - self._drag_start_global).manhattanLength()

            # If user barely moved mouse (< 6 px), count as a pet tap!
            if dist_moved < 6:
                self.pet_action()
            else:
                self.vx = 0.0
                self.vy = 0.0
                self.is_falling = False

                screen_geo = self._get_screen_bounds()
                screen_floor = screen_geo.bottom() - self.height() + 2
                # If released near the bottom floor, snap flush to bottom
                if abs(self.pos_y - screen_floor) < 50 or self.pos_y > screen_floor:
                    self.pos_y = float(screen_floor)
                    self.floor_y = self.pos_y
                else:
                    # Released elsewhere on desktop: keep at this height
                    self.floor_y = self.pos_y

                self.move(int(self.pos_x), int(self.pos_y))
                self.set_state("idle", 40)
                self.say("Here is nice!")
            event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.do_trick()
            event.accept()

    def _drop_to_floor(self):
        """Send sheep back down to desktop floor."""
        self.floor_y = self.default_floor_y
        self.is_falling = True
        self.set_state("fall", 99999)
        self.sound_mgr.play("boing")

    # Context Menu
    def _show_context_menu(self, global_pos: QPoint):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #26252d;
                color: #f0f0f4;
                border: 1px solid #484656;
                border-radius: 8px;
                padding: 6px;
                font-family: sans-serif;
            }
            QMenu::item {
                padding: 6px 20px 6px 12px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #4f46e5;
                color: white;
            }
            QMenu::separator {
                height: 1px;
                background-color: #3b3a47;
                margin: 4px 6px;
            }
        """)

        act_pet = menu.addAction("♥ Pet Sheep")
        act_pet.triggered.connect(self.pet_action)

        feed_menu = menu.addMenu("☘ Feed Treat...")
        act_apple = feed_menu.addAction("🍎 Crisp Red Apple")
        act_apple.triggered.connect(lambda: self.spawn_food("apple"))
        act_clover = feed_menu.addAction("☘ Sweet Clover")
        act_clover.triggered.connect(lambda: self.spawn_food("clover"))
        act_cookie = feed_menu.addAction("🍪 Chocolate Cookie")
        act_cookie.triggered.connect(lambda: self.spawn_food("cookie"))
        act_carrot = feed_menu.addAction("🥕 Crunchy Carrot")
        act_carrot.triggered.connect(lambda: self.spawn_food("carrot"))

        act_trick = menu.addAction("✨ Do Flip Trick")
        act_trick.triggered.connect(self.do_trick)

        if not self.stats["sheared"]:
            act_shear = menu.addAction("✂ Shear Wool")
            act_shear.triggered.connect(self.shear_sheep)
        else:
            act_shear = menu.addAction("✂ (Wool Growing...)")
            act_shear.setEnabled(False)

        if self.state == "sleep":
            act_sleep = menu.addAction("☀️ Wake Up")
            act_sleep.triggered.connect(self.wake_up)
        else:
            act_sleep = menu.addAction("💤 Put to Bed")
            act_sleep.triggered.connect(lambda: self.set_state("sleep", 200))

        if self.floor_y < self.default_floor_y - 20:
            act_drop = menu.addAction("⬇ Drop to Bottom Floor")
            act_drop.triggered.connect(self._drop_to_floor)

        menu.addSeparator()

        color_menu = menu.addMenu("🎨 Wool Color")
        colors = [
            ("Classic White", "white"),
            ("Strawberry Pink", "pink"),
            ("Midnight Black", "black"),
            ("Golden Fleece", "golden"),
            ("Matcha Mint", "mint"),
            ("Lavender", "lavender"),
            ("Sky Blue", "sky_blue"),
            ("Rainbow Pastel", "rainbow"),
        ]
        for name, col_code in colors:
            c_act = color_menu.addAction(name)
            c_act.setCheckable(True)
            c_act.setChecked(self.wool_color == col_code)
            c_act.triggered.connect(lambda checked, c=col_code: self._set_color(c))

        acc_menu = menu.addMenu("🎀 Accessories")
        accs = [
            ("None", "none"),
            ("Flower Crown", "flower_crown"),
            ("Cool Sunglasses", "sunglasses"),
            ("Party Hat", "party_hat"),
            ("Bell Ribbon Collar", "bell_collar"),
            ("Dapper Top Hat", "top_hat"),
        ]
        for name, acc_code in accs:
            a_act = acc_menu.addAction(name)
            a_act.setCheckable(True)
            a_act.setChecked(self.accessory == acc_code)
            a_act.triggered.connect(lambda checked, a=acc_code: self._set_accessory(a))

        beh_menu = menu.addMenu("🐾 Personality")
        modes = [
            ("Wander & Graze", "wander"),
            ("Follow Mouse Cursor", "follow"),
            ("Sleepyhead", "sleepy"),
            ("Stay Put", "stay"),
        ]
        for name, m_code in modes:
            m_act = beh_menu.addAction(name)
            m_act.setCheckable(True)
            m_act.setChecked(self.behavior_mode == m_code)
            m_act.triggered.connect(lambda checked, m=m_code: self._set_mode(m))

        menu.addSeparator()

        act_status = menu.addAction("📊 Pet Status Card...")
        act_status.triggered.connect(self._open_status_dialog)

        act_sound = menu.addAction("🔊 Sound Effects")
        act_sound.setCheckable(True)
        act_sound.setChecked(not self.sound_muted)
        act_sound.triggered.connect(self._toggle_sound)

        act_help = menu.addAction("❓ Guide & Controls...")
        act_help.triggered.connect(self._open_help_dialog)

        menu.addSeparator()

        act_quit = menu.addAction("❌ Send to Pasture (Exit)")
        act_quit.triggered.connect(self._quit_pet)

        menu.exec(global_pos)

    def _set_color(self, color_name: str):
        self.wool_color = color_name
        self.save_state()
        self.update()

    def _set_accessory(self, acc_name: str):
        self.accessory = acc_name
        self.save_state()
        self.update()

    def _set_mode(self, mode: str):
        self.behavior_mode = mode
        self.save_state()

    def _toggle_sound(self):
        self.sound_muted = not self.sound_muted
        self.sound_mgr.set_muted(self.sound_muted)
        self.save_state()

    def _open_status_dialog(self):
        if not self.status_dialog:
            self.status_dialog = PetStatusDialog(self)
        self.status_dialog.update_stats()
        self.status_dialog.show()
        self.status_dialog.raise_()
        self.status_dialog.activateWindow()

    def _open_help_dialog(self):
        dlg = HelpDialog(self)
        dlg.exec()

    def _quit_pet(self):
        self.save_state()
        self.close()

    # Paint Event
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        # 1. Draw Sheep Sprite
        curr_state = "sheared" if self.stats["sheared"] else self.state
        pixmap = self.sprite_mgr.get_sheep_frame(
            state=curr_state,
            frame_idx=self.frame_idx,
            wool_color=self.wool_color,
            accessory=self.accessory,
            facing_left=self.facing_left,
        )

        # Place sheep at bottom-center of the widget
        sx = (self.width() - pixmap.width()) // 2
        sy = self.height() - pixmap.height() - 4
        if not pixmap.isNull():
            painter.drawPixmap(sx, sy, pixmap)

        # 2. Draw Floating Particles
        for p in self.particles:
            p_pix = self.sprite_mgr.get_particle_pixmap(p["type"])
            if not p_pix.isNull():
                painter.setOpacity(p["alpha"])
                painter.drawPixmap(int(p["x"]), int(p["y"]), p_pix)
        painter.setOpacity(1.0)

        # 3. Draw Thought / Speech Bubble
        if self.thought_text and self.thought_ticks > 0:
            self._draw_speech_bubble(painter, self.thought_text, sx + pixmap.width() // 2, sy)

    def _draw_speech_bubble(self, painter: QPainter, text: str, anchor_x: int, anchor_y: int):
        painter.setFont(QFont("sans-serif", 9, QFont.Weight.Bold))
        metrics = painter.fontMetrics()
        text_w = metrics.horizontalAdvance(text)
        text_h = metrics.height()

        padding_x = 10
        padding_y = 5
        bubble_w = text_w + padding_x * 2
        bubble_h = text_h + padding_y * 2

        bx = max(4, min(self.width() - bubble_w - 4, anchor_x - bubble_w // 2))
        by = max(4, anchor_y - bubble_h - 10)

        # Background bubble pill
        painter.setPen(QPen(QColor(60, 55, 75, 230), 1))
        painter.setBrush(QBrush(QColor(255, 255, 255, 240)))
        painter.drawRoundedRect(QRectF(bx, by, bubble_w, bubble_h), 6.0, 6.0)

        # Little pointer triangle down to sheep
        tail_poly = [
            QPoint(anchor_x - 3, int(by + bubble_h)),
            QPoint(anchor_x + 3, int(by + bubble_h)),
            QPoint(anchor_x, anchor_y - 2),
        ]
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(tail_poly)

        # Text
        painter.setPen(QPen(QColor(30, 25, 40), 1))
        painter.drawText(int(bx + padding_x), int(by + padding_y + metrics.ascent()), text)
