"""Interactive falling food treat items for desktop sheep pet."""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPoint
from PyQt6.QtGui import QPainter
from pet.sprites import SpriteManager


class FoodItem(QWidget):
    """A floating/falling food item on the desktop that the sheep can eat."""

    consumed = pyqtSignal(object)  # emits self when consumed
    expired = pyqtSignal(object)

    def __init__(self, food_type: str = "apple", x: int = 100, y: int = 100, floor_y: int = 800, sprite_manager: SpriteManager = None):
        super().__init__()
        self.food_type = food_type
        self.floor_y = floor_y
        self.sprite_manager = sprite_manager or SpriteManager(scale=3)

        self.pos_x = float(x)
        self.pos_y = float(y)
        self.vy = 0.0
        self.gravity = 1.2
        self.bounce_factor = -0.4
        self.on_floor = False
        self.lifetime_ms = 45000  # disappears after 45s if uneaten

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(48, 48)
        self.move(int(self.pos_x), int(self.pos_y))

        # Physics timer
        self.phys_timer = QTimer(self)
        self.phys_timer.timeout.connect(self._physics_step)
        self.phys_timer.start(25)  # ~40 fps

        # Expiry timer
        self.expire_timer = QTimer(self)
        self.expire_timer.singleShot(self.lifetime_ms, self._on_expired)

    def _physics_step(self):
        if not self.on_floor:
            self.vy += self.gravity
            self.pos_y += self.vy
            target_floor = self.floor_y - self.height()
            if self.pos_y >= target_floor:
                self.pos_y = target_floor
                if abs(self.vy) > 2.5:
                    self.vy = self.vy * self.bounce_factor
                else:
                    self.vy = 0
                    self.on_floor = True
            self.move(int(self.pos_x), int(self.pos_y))

    def _on_expired(self):
        self.expired.emit(self)
        self.close()

    def get_center(self) -> QPoint:
        return QPoint(int(self.pos_x + self.width() / 2), int(self.pos_y + self.height() / 2))

    def eat(self):
        """Called when sheep consumes the treat."""
        self.consumed.emit(self)
        self.phys_timer.stop()
        self.close()

    def paintEvent(self, event):
        painter = QPainter(self)
        pix = self.sprite_manager.get_food_pixmap(self.food_type)
        if not pix.isNull():
            # Center the pixmap
            x = (self.width() - pix.width()) // 2
            y = (self.height() - pix.height()) // 2
            painter.drawPixmap(x, y, pix)
