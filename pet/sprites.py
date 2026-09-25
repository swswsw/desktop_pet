"""Procedural pixel art sprite generator for desktop sheep pet."""

from PIL import Image, ImageDraw
from PyQt6.QtGui import QImage, QPixmap
import math

# Color palettes for wool
WOOL_PALETTES = {
    "white": {
        "base": (255, 255, 255, 255),
        "shade": (218, 222, 235, 255),
        "outline": (160, 165, 185, 255),
    },
    "pink": {
        "base": (255, 205, 225, 255),
        "shade": (235, 155, 190, 255),
        "outline": (195, 115, 150, 255),
    },
    "black": {
        "base": (55, 52, 62, 255),
        "shade": (36, 34, 42, 255),
        "outline": (20, 18, 25, 255),
    },
    "golden": {
        "base": (255, 230, 130, 255),
        "shade": (230, 190, 75, 255),
        "outline": (180, 140, 40, 255),
    },
    "mint": {
        "base": (185, 245, 215, 255),
        "shade": (140, 215, 180, 255),
        "outline": (95, 175, 140, 255),
    },
    "lavender": {
        "base": (225, 210, 255, 255),
        "shade": (185, 165, 230, 255),
        "outline": (145, 125, 190, 255),
    },
    "sky_blue": {
        "base": (195, 230, 255, 255),
        "shade": (150, 195, 240, 255),
        "outline": (105, 150, 205, 255),
    },
    "rainbow": {
        "base": (255, 235, 245, 255),
        "shade": (210, 225, 255, 255),
        "outline": (170, 180, 240, 255),
    },
}

SKIN_COLOR = (255, 224, 205, 255)
SKIN_SHADE = (235, 195, 175, 255)
BLUSH_COLOR = (255, 170, 185, 255)
EYE_COLOR = (35, 30, 45, 255)
NOSE_COLOR = (225, 125, 145, 255)
HOOF_COLOR = (45, 40, 52, 255)
HOOF_SHADE = (30, 25, 38, 255)


def draw_pixel_circle(draw, cx, cy, r, fill, outline=None):
    """Draw a pixelated circle/ellipse."""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill, outline=outline)


def create_sheep_frame(
    state: str = "idle",
    frame_idx: int = 0,
    wool_color: str = "white",
    accessory: str = "none",
    canvas_size: int = 36,
    scale: int = 3,
) -> Image.Image:
    """Generate a single PIL Image frame for the sheep."""
    img = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    palette = WOOL_PALETTES.get(wool_color, WOOL_PALETTES["white"])
    wb = palette["base"]
    ws = palette["shade"]
    wo = palette["outline"]

    # In black sheep mode, skin should be softer charcoal/beige for visibility
    if wool_color == "black":
        skin = (230, 205, 190, 255)
        skin_s = (195, 170, 155, 255)
    else:
        skin = SKIN_COLOR
        skin_s = SKIN_SHADE

    # Coordinate offsets and animation transforms
    body_x, body_y = 13, 17
    head_x, head_y = 23, 13
    eye_style = "open"  # "open", "blink", "happy", "sleep", "surprised"
    chewing = False
    flail_legs = False
    is_sleeping = False
    is_sheared = (state == "sheared")

    leg_offsets = [0, 0, 0, 0]  # [front_r, front_l, back_r, back_l] y/x offset

    # State specific parameters
    if state == "idle":
        # 4 frames: gentle breathing, blinking, tail wag
        cycle = frame_idx % 4
        if cycle == 1:
            body_y -= 1
            head_y -= 1
        elif cycle == 2:
            eye_style = "blink"
        elif cycle == 3:
            pass

    elif state == "walk":
        # 6 frames trot cycle
        cycle = frame_idx % 6
        bob = [0, -1, 0, -1, 0, -1][cycle]
        body_y += bob
        head_y += bob
        leg_offsets = [
            [-2, 1, 2, -1],
            [-1, 2, 1, -2],
            [1, -2, -1, 2],
            [2, -1, -2, 1],
            [1, 1, -1, -1],
            [0, 0, 0, 0],
        ][cycle]

    elif state == "graze":
        # Head down eating grass
        cycle = frame_idx % 6
        head_x, head_y = 24, 18
        if cycle in (1, 2, 3, 4):
            chewing = True
            eye_style = "happy"
        if cycle in (2, 3):
            head_y += 1

    elif state == "sleep":
        is_sleeping = True
        body_y += 2
        head_x, head_y = 20, 17
        eye_style = "sleep"
        if frame_idx % 4 == 1:
            body_y -= 1

    elif state == "drag":
        # Picked up in the air
        flail_legs = True
        eye_style = "surprised"
        cycle = frame_idx % 4
        leg_offsets = [
            [-2, 3, -1, 2],
            [2, -2, 3, -1],
            [-3, 2, -2, 3],
            [1, -3, 2, -2],
        ][cycle]

    elif state == "fall":
        eye_style = "surprised"
        leg_offsets = [2, 2, 2, 2]
        head_y -= 1

    elif state == "land":
        cycle = frame_idx % 2
        if cycle == 0:
            # Squashed
            body_y += 2
            head_y += 2
        else:
            # Rebound
            body_y -= 1
            head_y -= 1

    elif state == "happy":
        cycle = frame_idx % 4
        jump = [0, -3, -5, -2][cycle]
        body_y += jump
        head_y += jump
        eye_style = "happy"

    elif state == "roll":
        # Curled up ball for rolling trick
        is_sleeping = True
        body_y += 1
        head_x, head_y = 21, 16
        eye_style = "happy"

    # 1. DRAW TAIL
    tail_x = body_x - 9
    tail_y = body_y - 2
    if state == "walk" and (frame_idx % 2 == 1):
        tail_x -= 1
    elif state == "happy":
        tail_x += (frame_idx % 2) * 2 - 1
    draw.ellipse([tail_x, tail_y, tail_x + 5, tail_y + 5], fill=wb, outline=ws)

    # 2. DRAW LEGS
    if not is_sleeping:
        legs = [
            (body_x - 5, body_y + 6, leg_offsets[2]),  # back left
            (body_x - 2, body_y + 6, leg_offsets[3]),  # back right
            (body_x + 3, body_y + 6, leg_offsets[0]),  # front left
            (body_x + 6, body_y + 6, leg_offsets[1]),  # front right
        ]
        for lx, ly, loff in legs:
            l_dy = loff if isinstance(loff, int) else loff
            if flail_legs:
                draw.rectangle([lx, ly + l_dy, lx + 2, ly + l_dy + 5], fill=skin)
                draw.rectangle([lx, ly + l_dy + 4, lx + 2, ly + l_dy + 6], fill=HOOF_COLOR)
            else:
                draw.rectangle([lx, ly + l_dy, lx + 2, ly + l_dy + 4], fill=skin)
                draw.rectangle([lx, ly + l_dy + 3, lx + 2, ly + l_dy + 4], fill=HOOF_COLOR)

    # 3. DRAW BODY (WOOL or SWEATER IF SHEARED)
    if is_sheared:
        # Skinny body wearing striped sweater
        draw.rounded_rectangle([body_x - 7, body_y - 4, body_x + 7, body_y + 5], radius=4, fill=(230, 60, 60, 255))
        # Stripes
        draw.line([body_x - 5, body_y - 1, body_x + 5, body_y - 1], fill=(255, 255, 255, 255), width=1)
        draw.line([body_x - 5, body_y + 2, body_x + 5, body_y + 2], fill=(255, 255, 255, 255), width=1)
    else:
        # Fluffy cloud wool body made of overlapping circles
        puffs = [
            (body_x - 6, body_y - 4, 5),
            (body_x, body_y - 6, 6),
            (body_x + 6, body_y - 3, 5),
            (body_x - 6, body_y + 2, 5),
            (body_x + 6, body_y + 2, 5),
            (body_x, body_y + 3, 6),
            (body_x, body_y - 1, 7),  # Central mass
        ]
        # Draw shade / outline base
        for px, py, pr in puffs:
            draw.ellipse([px - pr - 1, py - pr, px + pr + 1, py + pr + 1], fill=ws)
        # Draw main wool
        for px, py, pr in puffs:
            draw.ellipse([px - pr, py - pr, px + pr, py + pr], fill=wb)

    # 4. DRAW HEAD
    hx, hy = head_x, head_y
    # Head skin base
    draw.rounded_rectangle([hx - 4, hy - 4, hx + 5, hy + 5], radius=3, fill=skin)
    draw.ellipse([hx - 2, hy + 1, hx + 5, hy + 6], fill=skin_s)

    # Head wool cap
    if not is_sheared:
        draw.ellipse([hx - 4, hy - 7, hx + 4, hy - 2], fill=wb, outline=ws)
        draw.ellipse([hx - 1, hy - 8, hx + 3, hy - 3], fill=wb)

    # Ear (droopy & cute)
    ear_y = hy - 2
    if state == "drag" or state == "fall":
        # Flapping up
        draw.ellipse([hx - 6, ear_y - 3, hx - 2, ear_y + 1], fill=skin)
        draw.ellipse([hx - 5, ear_y - 2, hx - 3, ear_y], fill=BLUSH_COLOR)
    else:
        # Soft droop
        draw.ellipse([hx - 6, ear_y, hx - 2, ear_y + 4], fill=skin)
        draw.ellipse([hx - 5, ear_y + 1, hx - 3, ear_y + 3], fill=BLUSH_COLOR)

    # Eyes
    if eye_style == "open":
        draw.rectangle([hx + 1, hy - 1, hx + 2, hy + 1], fill=EYE_COLOR)
        # Eye shine
        draw.point((hx + 1, hy - 1), fill=(255, 255, 255, 255))
    elif eye_style == "blink":
        draw.line([hx, hy, hx + 3, hy], fill=EYE_COLOR, width=1)
    elif eye_style == "happy":
        # Curved happy eye ^
        draw.line([hx, hy + 1, hx + 1, hy - 1], fill=EYE_COLOR, width=1)
        draw.line([hx + 1, hy - 1, hx + 2, hy + 1], fill=EYE_COLOR, width=1)
        # Blush
        draw.rectangle([hx - 1, hy + 2, hx + 1, hy + 3], fill=BLUSH_COLOR)
    elif eye_style == "sleep":
        draw.line([hx, hy, hx + 2, hy], fill=EYE_COLOR, width=1)
    elif eye_style == "surprised":
        # Wide eye (o)
        draw.rectangle([hx, hy - 2, hx + 3, hy + 1], fill=(255, 255, 255, 255))
        draw.rectangle([hx + 1, hy - 1, hx + 2, hy], fill=EYE_COLOR)

    # Nose / Mouth
    draw.point((hx + 4, hy + 2), fill=NOSE_COLOR)

    # Chewing grass if grazing
    if chewing:
        grass_frame = frame_idx % 2
        gx = hx + 4
        gy = hy + 3
        draw.line([gx, gy, gx + 4, gy + 1 + grass_frame], fill=(70, 185, 60, 255), width=1)
        draw.line([gx + 2, gy + 1, gx + 5, gy - 1], fill=(90, 215, 75, 255), width=1)
        # Tiny yellow flower
        draw.point((gx + 5, gy - 1), fill=(255, 220, 60, 255))

    # 5. ACCESSORIES
    if accessory == "sunglasses":
        # Cool 8-bit shades
        draw.rectangle([hx - 1, hy - 2, hx + 4, hy + 1], fill=(20, 20, 25, 255))
        draw.line([hx - 4, hy - 2, hx - 1, hy - 2], fill=(20, 20, 25, 255), width=1)
        # White highlight shine
        draw.point((hx + 1, hy - 1), fill=(255, 255, 255, 255))
        draw.point((hx + 3, hy), fill=(255, 255, 255, 255))

    elif accessory == "flower_crown":
        # Ring of colorful blossoms
        flowers = [
            (hx - 3, hy - 5, (255, 105, 135, 255)),  # Pink rose
            (hx, hy - 6, (255, 225, 60, 255)),       # Yellow buttercup
            (hx + 3, hy - 5, (90, 180, 255, 255)),   # Blue daisy
        ]
        for fx, fy, col in flowers:
            draw.ellipse([fx - 1, fy - 1, fx + 1, fy + 1], fill=col)
            draw.point((fx, fy), fill=(255, 255, 255, 255))
        draw.point((hx - 1, hy - 4), fill=(60, 175, 75, 255))
        draw.point((hx + 2, hy - 4), fill=(60, 175, 75, 255))

    elif accessory == "party_hat":
        # Festive party cone
        ph_x, ph_y = hx, hy - 7
        draw.polygon([(ph_x, ph_y - 6), (ph_x - 3, ph_y), (ph_x + 3, ph_y)], fill=(255, 90, 95, 255))
        draw.line([ph_x - 2, ph_y - 2, ph_x + 2, ph_y - 2], fill=(255, 230, 80, 255), width=1)
        draw.line([ph_x - 1, ph_y - 4, ph_x + 1, ph_y - 4], fill=(70, 190, 255, 255), width=1)
        # Pom-pom on top
        draw.ellipse([ph_x - 1, ph_y - 8, ph_x + 1, ph_y - 6], fill=(255, 240, 100, 255))

    elif accessory == "bell_collar":
        # Red ribbon collar
        draw.line([hx - 3, hy + 4, hx + 2, hy + 4], fill=(220, 45, 55, 255), width=1)
        # Golden bell
        draw.ellipse([hx - 1, hy + 5, hx + 1, hy + 7], fill=(255, 215, 40, 255), outline=(190, 150, 20, 255))

    elif accessory == "top_hat":
        # Dapper black top hat
        th_x, th_y = hx, hy - 7
        draw.rectangle([th_x - 4, th_y - 1, th_x + 4, th_y], fill=(35, 35, 40, 255))
        draw.rectangle([th_x - 3, th_y - 7, th_x + 3, th_y - 1], fill=(45, 45, 55, 255))
        # Red hat ribbon
        draw.line([th_x - 3, th_y - 2, th_x + 3, th_y - 2], fill=(220, 50, 60, 255), width=1)

    # 6. SLEEP ZZZ PARTICLES (rendered in sprite for sleep)
    if is_sleeping:
        z_cycle = frame_idx % 4
        z_coords = [
            (hx + 5, hy - 6, 4, (120, 160, 240, 180)),
            (hx + 7, hy - 9, 6, (140, 180, 255, 220)),
            (hx + 9, hy - 12, 7, (170, 200, 255, 255)),
            (hx + 10, hy - 14, 8, (190, 220, 255, 160)),
        ]
        zx, zy, zsize, zcol = z_coords[z_cycle]
        draw.line([zx, zy, zx + zsize // 2, zy], fill=zcol, width=1)
        draw.line([zx + zsize // 2, zy, zx, zy + zsize // 2], fill=zcol, width=1)
        draw.line([zx, zy + zsize // 2, zx + zsize // 2, zy + zsize // 2], fill=zcol, width=1)

    # 7. ROTATION FOR TRICKS (ROLL)
    if state == "roll":
        angle = (frame_idx % 8) * -45
        img = img.rotate(angle, resample=Image.Resampling.NEAREST, center=(canvas_size // 2, canvas_size // 2))

    # 8. SCALE UP TO CRISP PIXEL ART
    target_size = canvas_size * scale
    scaled_img = img.resize((target_size, target_size), resample=Image.Resampling.NEAREST)
    return scaled_img


def create_food_sprite(food_type: str = "apple", scale: int = 3) -> Image.Image:
    """Generate crisp pixel art for food items."""
    canvas = 16
    img = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if food_type == "apple":
        # Shiny red apple
        draw.ellipse([3, 5, 12, 14], fill=(235, 45, 55, 255))
        draw.ellipse([4, 6, 6, 8], fill=(255, 125, 130, 255))  # highlight
        # Stem & Leaf
        draw.line([7, 3, 8, 5], fill=(115, 75, 45, 255), width=1)
        draw.ellipse([9, 2, 12, 4], fill=(75, 195, 65, 255))

    elif food_type == "clover":
        # 4-leaf lucky clover
        green = (55, 190, 75, 255)
        dark = (40, 145, 55, 255)
        draw.ellipse([4, 4, 8, 8], fill=green)
        draw.ellipse([8, 4, 12, 8], fill=green)
        draw.ellipse([4, 8, 8, 12], fill=green)
        draw.ellipse([8, 8, 12, 12], fill=green)
        draw.ellipse([7, 7, 9, 9], fill=dark)
        # Stem
        draw.line([8, 10, 8, 15], fill=dark, width=1)

    elif food_type == "cookie":
        # Chocolate chip cookie
        draw.ellipse([3, 3, 13, 13], fill=(225, 175, 100, 255), outline=(185, 135, 70, 255))
        chips = [(5, 6), (9, 5), (6, 10), (10, 9), (7, 7)]
        for cx, cy in chips:
            draw.rectangle([cx, cy, cx + 1, cy + 1], fill=(70, 45, 30, 255))

    elif food_type == "carrot":
        # Crunchy orange carrot
        draw.polygon([(4, 4), (12, 4), (8, 14)], fill=(255, 120, 25, 255))
        draw.line([5, 6, 11, 6], fill=(230, 95, 15, 255), width=1)
        draw.line([6, 9, 10, 9], fill=(230, 95, 15, 255), width=1)
        # Green top
        draw.line([8, 1, 8, 4], fill=(70, 190, 60, 255), width=1)
        draw.line([6, 2, 8, 4], fill=(95, 215, 80, 255), width=1)
        draw.line([10, 2, 8, 4], fill=(95, 215, 80, 255), width=1)

    return img.resize((canvas * scale, canvas * scale), resample=Image.Resampling.NEAREST)


def create_particle_sprite(p_type: str = "heart", scale: int = 3) -> Image.Image:
    """Generate floating particle icons."""
    canvas = 12
    img = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if p_type == "heart":
        col = (255, 75, 125, 255)
        draw.rectangle([2, 3, 4, 5], fill=col)
        draw.rectangle([6, 3, 8, 5], fill=col)
        draw.polygon([(1, 4), (9, 4), (5, 9)], fill=col)
        draw.point((3, 4), fill=(255, 180, 210, 255))  # highlight

    elif p_type == "star":
        col = (255, 220, 45, 255)
        draw.polygon([(5, 1), (7, 4), (10, 5), (7, 7), (6, 10), (4, 7), (1, 5), (4, 4)], fill=col)
        draw.point((5, 5), fill=(255, 255, 255, 255))

    elif p_type == "dust":
        col = (210, 215, 225, 200)
        draw.ellipse([2, 4, 9, 8], fill=col)
        draw.ellipse([4, 2, 7, 6], fill=col)

    return img.resize((canvas * scale, canvas * scale), resample=Image.Resampling.NEAREST)


class SpriteManager:
    """Caches and provides QPixmap animations for sheep, items, and particles."""

    def __init__(self, scale: int = 3):
        self.scale = scale
        self._pixmap_cache = {}

    def pil_to_qpixmap(self, pil_img: Image.Image) -> QPixmap:
        """Convert a PIL Image directly into a PyQt6 QPixmap."""
        data = pil_img.tobytes("raw", "RGBA")
        qimg = QImage(data, pil_img.width, pil_img.height, QImage.Format.Format_RGBA8888)
        return QPixmap.fromImage(qimg)

    def get_sheep_frame(
        self,
        state: str,
        frame_idx: int,
        wool_color: str,
        accessory: str,
        facing_left: bool = False,
    ) -> QPixmap:
        """Retrieve cached sheep QPixmap frame."""
        key = (state, frame_idx, wool_color, accessory, facing_left)
        if key in self._pixmap_cache:
            return self._pixmap_cache[key]

        pil_frame = create_sheep_frame(
            state=state,
            frame_idx=frame_idx,
            wool_color=wool_color,
            accessory=accessory,
            scale=self.scale,
        )

        if facing_left:
            pil_frame = pil_frame.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

        pixmap = self.pil_to_qpixmap(pil_frame)
        self._pixmap_cache[key] = pixmap
        return pixmap

    def get_food_pixmap(self, food_type: str) -> QPixmap:
        """Retrieve food item QPixmap."""
        key = ("food", food_type)
        if key in self._pixmap_cache:
            return self._pixmap_cache[key]

        pil_img = create_food_sprite(food_type, scale=self.scale)
        pixmap = self.pil_to_qpixmap(pil_img)
        self._pixmap_cache[key] = pixmap
        return pixmap

    def get_particle_pixmap(self, p_type: str) -> QPixmap:
        """Retrieve particle QPixmap."""
        key = ("particle", p_type)
        if key in self._pixmap_cache:
            return self._pixmap_cache[key]

        pil_img = create_particle_sprite(p_type, scale=self.scale)
        pixmap = self.pil_to_qpixmap(pil_img)
        self._pixmap_cache[key] = pixmap
        return pixmap

    def clear_cache(self):
        """Clear cache if customization changes frequently."""
        self._pixmap_cache.clear()
