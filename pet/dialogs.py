"""Charming HUD dialogs and cards for the desktop sheep pet."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QComboBox, QLineEdit, QCheckBox, QSlider, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette


class PetStatusDialog(QDialog):
    """Tamagotchi-style Pet Status HUD card."""

    pet_action_requested = pyqtSignal(str, object)  # action_name, param

    def __init__(self, sheep_widget, parent=None):
        super().__init__(parent)
        self.sheep = sheep_widget
        self.setWindowTitle(f"{self.sheep.pet_name}'s Status")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedSize(340, 480)
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2a33;
                color: #f0f0f4;
                font-family: sans-serif;
                border-radius: 12px;
            }
            QLabel {
                color: #f0f0f4;
            }
            QProgressBar {
                border: 1px solid #4a4956;
                border-radius: 6px;
                text-align: center;
                background-color: #1e1d24;
                color: white;
                font-weight: bold;
                height: 16px;
            }
            QProgressBar::chunk {
                border-radius: 5px;
            }
            QPushButton {
                background-color: #4f46e5;
                color: white;
                border: none;
                padding: 7px 12px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #6366f1;
            }
            QPushButton:pressed {
                background-color: #4338ca;
            }
            QFrame#card {
                background-color: #212028;
                border-radius: 8px;
                padding: 10px;
            }
        """)

        self._init_ui()
        self.update_stats()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # Header / Avatar Area
        header_card = QFrame()
        header_card.setObjectName("card")
        header_layout = QHBoxLayout(header_card)

        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(72, 72)
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.avatar_label)

        info_layout = QVBoxLayout()
        self.name_label = QLabel(self.sheep.pet_name)
        self.name_label.setFont(QFont("sans-serif", 14, QFont.Weight.Bold))
        self.state_label = QLabel("Mood: Happy")
        self.state_label.setStyleSheet("color: #a5b4fc; font-size: 11px;")
        info_layout.addWidget(self.name_label)
        info_layout.addWidget(self.state_label)
        header_layout.addLayout(info_layout)
        header_layout.addStretch()

        layout.addWidget(header_card)

        # Stats Card
        stats_card = QFrame()
        stats_card.setObjectName("card")
        stats_layout = QVBoxLayout(stats_card)
        stats_layout.setSpacing(8)

        # Happiness
        self.happy_bar = self._create_bar(stats_layout, "♥ Happiness", "#ec4899")
        # Hunger
        self.hunger_bar = self._create_bar(stats_layout, "☘ Fullness", "#10b981")
        # Energy
        self.energy_bar = self._create_bar(stats_layout, "⚡ Energy", "#f59e0b")
        # Wool Puffiness
        self.wool_bar = self._create_bar(stats_layout, "☁ Wool Fluffiness", "#8b5cf6")

        layout.addWidget(stats_card)

        # Quick Actions
        actions_label = QLabel("Quick Interactions")
        actions_label.setFont(QFont("sans-serif", 10, QFont.Weight.Bold))
        layout.addWidget(actions_label)

        row1 = QHBoxLayout()
        btn_pet = QPushButton("♥ Pet Sheep")
        btn_pet.clicked.connect(lambda: self.sheep.pet_action())
        btn_feed = QPushButton("☘ Feed Clover")
        btn_feed.clicked.connect(lambda: self.sheep.spawn_food("clover"))
        row1.addWidget(btn_pet)
        row1.addWidget(btn_feed)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        btn_apple = QPushButton("🍎 Feed Apple")
        btn_apple.clicked.connect(lambda: self.sheep.spawn_food("apple"))
        btn_trick = QPushButton("✨ Do Trick")
        btn_trick.clicked.connect(lambda: self.sheep.do_trick())
        row2.addWidget(btn_apple)
        row2.addWidget(btn_trick)
        layout.addLayout(row2)

        row3 = QHBoxLayout()
        self.btn_shear = QPushButton("✂ Shear Wool")
        self.btn_shear.clicked.connect(lambda: self.sheep.shear_sheep())
        btn_style = QPushButton("🎨 Customize")
        btn_style.clicked.connect(self._open_style_dialog)
        row3.addWidget(self.btn_shear)
        row3.addWidget(btn_style)
        layout.addLayout(row3)

    def _create_bar(self, layout, label_text, color):
        lbl = QLabel(label_text)
        lbl.setStyleSheet("font-size: 11px; font-weight: bold;")
        layout.addWidget(lbl)
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setStyleSheet(f"QProgressBar::chunk {{ background-color: {color}; }}")
        layout.addWidget(bar)
        return bar

    def update_stats(self):
        """Update gauges with current pet values."""
        self.happy_bar.setValue(int(self.sheep.stats["happiness"]))
        self.hunger_bar.setValue(int(self.sheep.stats["hunger"]))
        self.energy_bar.setValue(int(self.sheep.stats["energy"]))
        self.wool_bar.setValue(int(self.sheep.stats["wool_puff"]))

        # Avatar
        pix = self.sheep.sprite_mgr.get_sheep_frame("idle", 0, self.sheep.wool_color, self.sheep.accessory)
        scaled_pix = pix.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)
        self.avatar_label.setPixmap(scaled_pix)

        # Status text
        st = self.sheep.state
        status_map = {
            "idle": "Relaxing and looking around",
            "walk": "Roaming the desktop pastures",
            "graze": "Nibbling sweet clover",
            "sleep": "Sleeping cozily (Zzz...)",
            "happy": "So joyful and full of love!",
            "drag": "Being held up in mid-air!",
            "fall": "Wheee! Falling down!",
            "roll": "Performing a backflip trick!",
            "sheared": "Rocking a comfy cozy sweater!",
        }
        mood = status_map.get(st, "Chilling")
        self.state_label.setText(f"Activity: {mood}")

        if self.sheep.stats["sheared"]:
            self.btn_shear.setText("✂ Wool Growing...")
            self.btn_shear.setEnabled(False)
        else:
            self.btn_shear.setText("✂ Shear Wool")
            self.btn_shear.setEnabled(self.sheep.stats["wool_puff"] >= 70)

    def _open_style_dialog(self):
        dlg = StyleDialog(self.sheep, self)
        dlg.exec()
        self.update_stats()


class StyleDialog(QDialog):
    """Customization dialog for Wool Colors, Accessories, and Name."""

    def __init__(self, sheep_widget, parent=None):
        super().__init__(parent)
        self.sheep = sheep_widget
        self.setWindowTitle("Customize Your Sheep")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedSize(320, 420)
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2a33;
                color: #f0f0f4;
                border-radius: 10px;
            }
            QLabel { color: #f0f0f4; font-size: 12px; }
            QComboBox, QLineEdit {
                background-color: #1e1d24;
                color: white;
                border: 1px solid #4a4956;
                border-radius: 5px;
                padding: 6px;
            }
            QPushButton {
                background-color: #4f46e5;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #6366f1; }
        """)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        # Pet Name
        layout.addWidget(QLabel("Pet Name:"))
        self.name_edit = QLineEdit(self.sheep.pet_name)
        layout.addWidget(self.name_edit)

        # Wool Color
        layout.addWidget(QLabel("Wool Color:"))
        self.color_combo = QComboBox()
        colors = [
            ("Classic Fluffy White", "white"),
            ("Bubblegum Strawberry Pink", "pink"),
            ("Midnight Black", "black"),
            ("Golden Honey Fleece", "golden"),
            ("Fresh Mint Matcha", "mint"),
            ("Cozy Lavender", "lavender"),
            ("Sky Cloud Blue", "sky_blue"),
            ("Pastel Rainbow", "rainbow"),
        ]
        for label, val in colors:
            self.color_combo.addItem(label, val)

        idx = self.color_combo.findData(self.sheep.wool_color)
        if idx >= 0:
            self.color_combo.setCurrentIndex(idx)
        layout.addWidget(self.color_combo)

        # Accessory
        layout.addWidget(QLabel("Accessory:"))
        self.acc_combo = QComboBox()
        accs = [
            ("None", "none"),
            ("Flower Crown", "flower_crown"),
            ("Cool Sunglasses", "sunglasses"),
            ("Party Hat", "party_hat"),
            ("Bell Ribbon Collar", "bell_collar"),
            ("Dapper Top Hat", "top_hat"),
        ]
        for label, val in accs:
            self.acc_combo.addItem(label, val)

        idx = self.acc_combo.findData(self.sheep.accessory)
        if idx >= 0:
            self.acc_combo.setCurrentIndex(idx)
        layout.addWidget(self.acc_combo)

        # Behavior Mode
        layout.addWidget(QLabel("Behavior Personality:"))
        self.mode_combo = QComboBox()
        modes = [
            ("Free Wanderer (Roams & Grazes)", "wander"),
            ("Curious (Follows Mouse Cursor)", "follow"),
            ("Sleepyhead (Loves Napping)", "sleepy"),
            ("Calm (Stays in one spot)", "stay"),
        ]
        for label, val in modes:
            self.mode_combo.addItem(label, val)
        idx = self.mode_combo.findData(self.sheep.behavior_mode)
        if idx >= 0:
            self.mode_combo.setCurrentIndex(idx)
        layout.addWidget(self.mode_combo)

        # Save Button
        btn_save = QPushButton("Save & Apply")
        btn_save.clicked.connect(self._apply)
        layout.addWidget(btn_save)

    def _apply(self):
        self.sheep.pet_name = self.name_edit.text().strip() or "Fluffy"
        self.sheep.wool_color = self.color_combo.currentData()
        self.sheep.accessory = self.acc_combo.currentData()
        self.sheep.behavior_mode = self.mode_combo.currentData()
        self.sheep.save_state()
        self.sheep.update()
        self.accept()


class HelpDialog(QDialog):
    """User guide & controls tutorial."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sheep Pet Guide & Controls")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedSize(360, 400)
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2a33;
                color: #f0f0f4;
                border-radius: 10px;
            }
            QLabel { color: #f0f0f4; font-size: 12px; }
            QPushButton {
                background-color: #4f46e5;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("🐑 Desktop Sheep Pet Guide")
        title.setFont(QFont("sans-serif", 13, QFont.Weight.Bold))
        layout.addWidget(title)

        guide_text = QLabel("""
<b>Interactions:</b><br>
• <b>Left-Click:</b> Pet sheep (gives hearts, joy & happiness!).<br>
• <b>Click & Drag:</b> Pick up sheep anywhere on your screen. Drop mid-air to watch gravity and a soft bounce!<br>
• <b>Double-Click:</b> Performs an acrobatic somersault roll or trick.<br>
• <b>Right-Click:</b> Context menu for feeding snacks, styles, sheep stats, audio mute, and spawning buddies.<br><br>

<b>Needs & Stats:</b><br>
• <b>Happiness:</b> Increases when petted and fed.<br>
• <b>Fullness:</b> Drops gradually; sheep grazes or eats dropped apples, clover & cookies.<br>
• <b>Energy:</b> Drops over time; sheep takes cozy naps to recharge.<br>
• <b>Wool Fluffiness:</b> Grows over time and can be shorn for a cute sweater!
        """)
        guide_text.setWordWrap(True)
        layout.addWidget(guide_text)

        btn_close = QPushButton("Got it!")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)
