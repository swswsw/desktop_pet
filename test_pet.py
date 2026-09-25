"""Comprehensive automated tests for Desktop Sheep Pet."""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QPoint

# Ensure pet package is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pet.sprites import SpriteManager, WOOL_PALETTES
from pet.audio import SoundManager
from pet.storage import load_settings, save_settings
from pet.food_item import FoodItem
from pet.sheep_widget import SheepWidget
from pet.dialogs import PetStatusDialog, StyleDialog, HelpDialog


def test_sprites(app):
    print("Testing sprites...")
    sm = SpriteManager(scale=3)
    states = ["idle", "walk", "graze", "sleep", "drag", "fall", "land", "happy", "roll", "sheared"]
    accessories = ["none", "sunglasses", "flower_crown", "party_hat", "bell_collar", "top_hat"]

    for state in states:
        for f in range(4):
            pm = sm.get_sheep_frame(state, f, "white", "none", facing_left=False)
            assert not pm.isNull(), f"Failed rendering {state} frame {f}"
            pm_left = sm.get_sheep_frame(state, f, "white", "none", facing_left=True)
            assert not pm_left.isNull(), f"Failed rendering {state} frame {f} left"

    for acc in accessories:
        pm = sm.get_sheep_frame("idle", 0, "pink", acc)
        assert not pm.isNull(), f"Failed rendering accessory {acc}"

    for col in WOOL_PALETTES:
        pm = sm.get_sheep_frame("walk", 1, col, "sunglasses")
        assert not pm.isNull(), f"Failed rendering color {col}"

    for food in ["apple", "clover", "cookie", "carrot"]:
        pm = sm.get_food_pixmap(food)
        assert not pm.isNull(), f"Failed rendering food {food}"

    for p in ["heart", "star", "dust"]:
        pm = sm.get_particle_pixmap(p)
        assert not pm.isNull(), f"Failed rendering particle {p}"

    print("✓ All sprites tested successfully.")


def test_audio(app):
    print("Testing audio synthesis & effects...")
    sm = SoundManager()
    for snd in ["baa", "munch", "pop", "boing", "happy"]:
        sm.play(snd)
    assert not sm.muted
    sm.toggle_muted()
    assert sm.muted
    sm.toggle_muted()
    assert not sm.muted
    print("✓ Audio tested successfully.")


def test_storage():
    print("Testing settings storage...")
    settings = load_settings()
    assert "pet_name" in settings
    assert "wool_color" in settings
    test_data = dict(settings)
    test_data["pet_name"] = "FluffyTest"
    save_settings(test_data)
    loaded = load_settings()
    assert loaded["pet_name"] == "FluffyTest"
    # Restore default name
    test_data["pet_name"] = "Fluffy"
    save_settings(test_data)
    print("✓ Storage tested successfully.")


def test_sheep_interactions(app):
    print("Testing sheep widget & interactions...")
    sprite_mgr = SpriteManager(scale=3)
    sound_mgr = SoundManager()
    sheep = SheepWidget(sprite_mgr=sprite_mgr, sound_mgr=sound_mgr, pet_id=1)
    sheep.show()

    # Verify initial properties
    assert sheep.pos_y == sheep.floor_y or sheep.pos_y > 0
    assert sheep.width() == 130
    assert sheep.height() == 120

    # Test actions
    initial_happy = sheep.stats["happiness"]
    sheep.pet_action()
    assert sheep.state == "happy"
    assert sheep.stats["happiness"] >= initial_happy

    # Test trick
    sheep.do_trick()
    assert sheep.state == "roll"

    # Test speech bubble
    sheep.say("Test thought")
    assert sheep.thought_text == "Test thought"

    # Test particles
    sheep.spawn_particle("heart", 50, 50)
    assert len(sheep.particles) > 0
    sheep._update_particles()

    # Test shearing
    sheep.shear_sheep()
    assert sheep.stats["sheared"] is True

    # Test food drop & consumption
    sheep.spawn_food("apple")
    assert len(sheep.active_food) == 1
    food = sheep.active_food[0]
    assert food.food_type == "apple"
    food.eat()
    assert food not in sheep.active_food

    # Verify starts near bottom right of screen
    screen_geo = sheep._get_screen_bounds()
    assert sheep.pos_x > screen_geo.right() - sheep.width() - 250
    assert abs(sheep.pos_y - (screen_geo.bottom() - sheep.height() + 2)) < 5

    # Test click and drag to move pet
    from PyQt6.QtGui import QMouseEvent
    from PyQt6.QtCore import QPointF
    start_pos_x = sheep.pos_x
    start_pos_y = sheep.pos_y

    press = QMouseEvent(QMouseEvent.Type.MouseButtonPress, QPointF(20, 20), QPointF(start_pos_x + 20, start_pos_y + 20), Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    sheep.mousePressEvent(press)
    assert sheep.is_dragging is True

    # Drag 120 pixels left, 80 pixels up
    drag_target_x = start_pos_x + 20 - 120
    drag_target_y = start_pos_y + 20 - 80
    move = QMouseEvent(QMouseEvent.Type.MouseMove, QPointF(20, 20), QPointF(drag_target_x, drag_target_y), Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    sheep.mouseMoveEvent(move)
    assert sheep.pos_x < start_pos_x

    # Release
    rel = QMouseEvent(QMouseEvent.Type.MouseButtonRelease, QPointF(20, 20), QPointF(drag_target_x, drag_target_y), Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier)
    sheep.mouseReleaseEvent(rel)
    assert sheep.is_dragging is False
    assert sheep.state == "idle"
    # Ensure pet stays where moved
    assert sheep.floor_y == sheep.pos_y

    # Test drop to floor
    sheep._drop_to_floor()
    assert sheep.floor_y == sheep.default_floor_y
    assert sheep.is_falling is True

    # Test Status Dialog
    status_dlg = PetStatusDialog(sheep)
    status_dlg.update_stats()
    assert status_dlg.name_label.text() == sheep.pet_name
    status_dlg.close()

    sheep.close()
    print("✓ Sheep widget & interactions tested successfully.")


def main():
    app = QApplication(sys.argv)
    test_sprites(app)
    test_audio(app)
    test_storage()
    test_sheep_interactions(app)
    print("\n🎉 ALL PET TESTS PASSED!")
    app.quit()


if __name__ == "__main__":
    main()
