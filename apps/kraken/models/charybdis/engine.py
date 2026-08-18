"""Charybdis — image/video generation engine.

Creates real images using Pillow. Generates art, icons, wallpapers,
diagrams, and visual content. Saves files to disk.
"""

from __future__ import annotations

import math
import os
import random
import time
from collections.abc import Callable

from PIL import Image, ImageDraw, ImageFont

from apps.kraken.core.engine import BaseEngine, EngineResponse
from apps.kraken.core.tools import file_write


def _classify_intent(msg: str) -> str:
    lower = msg.lower().strip()
    first_word = lower.split()[0] if lower.split() else ""
    if first_word in ("hello", "hi", "hey"):
        if len(lower.split()) <= 4:
            return "greeting"
    if any(w in lower for w in ["help", "what can you do", "capabilities"]):
        return "help"
    if any(w in lower for w in ["generate", "create", "make", "draw", "paint",
                                  "image", "picture", "photo", "art"]):
        if any(w in lower for w in ["icon", "logo", "symbol", "badge"]):
            return "icon"
        if any(w in lower for w in ["wallpaper", "background", "desktop", "bg"]):
            return "wallpaper"
        if any(w in lower for w in ["diagram", "chart", "graph", "flow"]):
            return "diagram"
        if any(w in lower for w in ["banner", "header", "cover", "hero"]):
            return "banner"
        if any(w in lower for w in ["pixel", "sprite", "game", "retro"]):
            return "pixel_art"
        if any(w in lower for w in ["mandala", "pattern", "geometric", "abstract"]):
            return "pattern"
        if any(w in lower for w in ["card", "business card", "postcard"]):
            return "card"
        if any(w in lower for w in ["logo"]):
            return "logo"
        if any(w in lower for w in ["gradient", "ombre", "fade"]):
            return "gradient"
        if any(w in lower for w in ["texture", "noise", "perlin"]):
            return "texture"
        if any(w in lower for w in ["tile", "seamless", "repeat"]):
            return "tile"
        if any(w in lower for w in ["chart", "bar chart", "pie chart", "line chart"]):
            return "chart"
        if any(w in lower for w in ["timeline", "infographic"]):
            return "timeline"
        return "image"
    if any(w in lower for w in ["icon", "symbol", "badge"]):
        return "icon"
    if any(w in lower for w in ["wallpaper", "background", "desktop"]):
        return "wallpaper"
    if any(w in lower for w in ["banner", "header", "cover"]):
        return "banner"
    if "?" in lower:
        return "question"
    return "general"


def _get_font(size: int = 20):
    """Get a font, with fallback to default."""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    ]
    for p in font_paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def _generate_plasma(width: int, height: int, seed: int, colors: list[str]) -> Image.Image:
    """Generate a plasma fractal image."""
    random.seed(seed)
    img = Image.new("RGB", (width, height))
    pixels = img.load()

    # Parse hex colors to RGB
    rgb_colors = []
    for c in colors:
        c = c.lstrip("#")
        rgb_colors.append(tuple(int(c[i:i+2], 16) for i in (0, 2, 4)))

    # Generate plasma using sine waves
    for y in range(height):
        for x in range(width):
            v1 = math.sin(x * 0.02 + seed)
            v2 = math.sin(y * 0.02 + seed * 0.7)
            v3 = math.sin((x + y) * 0.015 + seed * 1.3)
            v4 = math.sin(math.sqrt(x*x + y*y) * 0.03 + seed * 0.5)
            v = (v1 + v2 + v3 + v4) / 4.0
            v = (v + 1) / 2.0  # normalize to 0-1

            # Interpolate between colors
            idx = v * (len(rgb_colors) - 1)
            i = int(idx)
            t = idx - i
            if i >= len(rgb_colors) - 1:
                r, g, b = rgb_colors[-1]
            else:
                r1, g1, b1 = rgb_colors[i]
                r2, g2, b2 = rgb_colors[i+1]
                r = int(r1 + (r2 - r1) * t)
                g = int(g1 + (g2 - g1) * t)
                b = int(b1 + (b2 - b1) * t)
            pixels[x, y] = (r, g, b)
    return img


def _generate_wave(width: int, height: int, seed: int, colors: list[str]) -> Image.Image:
    """Generate wave pattern."""
    random.seed(seed)
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)

    rgb_colors = []
    for c in colors:
        c = c.lstrip("#")
        rgb_colors.append(tuple(int(c[i:i+2], 16) for i in (0, 2, 4)))

    num_waves = random.randint(5, 12)
    for i in range(num_waves):
        color = rgb_colors[i % len(rgb_colors)]
        amplitude = random.randint(20, 80)
        frequency = random.uniform(0.005, 0.03)
        phase = random.uniform(0, 2 * math.pi)
        y_offset = int(height * (i + 1) / (num_waves + 1))

        points = []
        for x in range(0, width + 1, 2):
            y = y_offset + int(amplitude * math.sin(frequency * x + phase))
            points.append((x, y))
        # Close the polygon
        points.append((width, height))
        points.append((0, height))

        if len(points) >= 3:
            draw.polygon(points, fill=color)
    return img


def _generate_circles(width: int, height: int, seed: int, colors: list[str]) -> Image.Image:
    """Generate abstract circle composition."""
    random.seed(seed)
    img = Image.new("RGB", (width, height), (15, 15, 25))
    draw = ImageDraw.Draw(img)

    rgb_colors = []
    for c in colors:
        c = c.lstrip("#")
        rgb_colors.append(tuple(int(c[i:i+2], 16) for i in (0, 2, 4)))

    num_circles = random.randint(8, 25)
    for _ in range(num_circles):
        x = random.randint(0, width)
        y = random.randint(0, height)
        r = random.randint(20, min(width, height) // 3)
        color = random.choice(rgb_colors)
        alpha_color = color + (random.randint(60, 180),)
        # Draw filled circle
        draw.ellipse([x-r, y-r, x+r, y+r], fill=color)
    return img


def _generate_mandala(width: int, height: int, seed: int, colors: list[str]) -> Image.Image:
    """Generate mandala pattern."""
    random.seed(seed)
    img = Image.new("RGB", (width, height), (10, 10, 30))
    draw = ImageDraw.Draw(img)

    rgb_colors = []
    for c in colors:
        c = c.lstrip("#")
        rgb_colors.append(tuple(int(c[i:i+2], 16) for i in (0, 2, 4)))

    cx, cy = width // 2, height // 2
    max_r = min(width, height) // 2 - 10
    layers = random.randint(6, 15)

    for layer in range(layers):
        r = int(max_r * (layer + 1) / layers)
        segments = random.randint(6, 24)
        color = rgb_colors[layer % len(rgb_colors)]

        for seg in range(segments):
            angle1 = (2 * math.pi * seg) / segments
            angle2 = (2 * math.pi * (seg + 0.5)) / segments

            x1 = cx + int(r * math.cos(angle1))
            y1 = cy + int(r * math.sin(angle1))
            x2 = cx + int(r * math.cos(angle2))
            y2 = cy + int(r * math.sin(angle2))

            draw.line([(cx, cy), (x1, y1)], fill=color, width=2)
            draw.ellipse([x1-4, y1-4, x1+4, y1+4], fill=color)

    return img


def _generate_landscape(width: int, height: int, seed: int) -> Image.Image:
    """Generate a procedural landscape."""
    random.seed(seed)
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)

    # Sky gradient
    for y in range(height // 2):
        r = int(20 + 60 * (y / (height/2)))
        g = int(10 + 40 * (y / (height/2)))
        b = int(80 + 100 * (y / (height/2)))
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Mountains
    for layer in range(3):
        points = [(0, height)]
        base_y = height // 2 + layer * 40
        amplitude = 80 - layer * 20
        for x in range(0, width + 10, 10):
            y = base_y + int(amplitude * math.sin(x * 0.01 + layer * 2))
            points.append((x, y))
        points.append((width, height))
        shade = 30 + layer * 20
        draw.polygon(points, fill=(shade, shade + 10, shade + 5))

    # Ground
    ground_y = int(height * 0.7)
    draw.rectangle([0, ground_y, width, height], fill=(20, 40, 20))

    return img


def _add_text_overlay(img: Image.Image, text: str, position: str = "center") -> Image.Image:
    """Add text overlay to image."""
    draw = ImageDraw.Draw(img)
    font = _get_font(max(16, min(img.width, img.height) // 15))

    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

    if position == "center":
        x = (img.width - tw) // 2
        y = (img.height - th) // 2
    elif position == "bottom":
        x = (img.width - tw) // 2
        y = img.height - th - 30
    else:
        x = 20
        y = 20

    # Shadow
    draw.text((x+2, y+2), text, fill=(0, 0, 0), font=font)
    draw.text((x, y), text, fill=(255, 255, 255), font=font)
    return img


def _save_image(img: Image.Image, filepath: str) -> str:
    """Save image and return info."""
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    img.save(filepath, "PNG")
    return filepath


class CharybdisEngine(BaseEngine):
    model_id = "charybdis"

    def __init__(self, cfg):
        self.cfg = cfg

    def respond(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: Callable[[str], None] | None = None,
        workspace: str | None = None,
    ) -> EngineResponse:
        t0 = self._tick()

        user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                user_msg = (m.get("content") or "").strip()
                break

        ws = workspace or os.getcwd()
        intent = _classify_intent(user_msg)

        if intent == "image":
            text = self._task_image(user_msg, ws)
        elif intent == "icon":
            text = self._task_icon(user_msg, ws)
        elif intent == "wallpaper":
            text = self._task_wallpaper(user_msg, ws)
        elif intent == "banner":
            text = self._task_banner(user_msg, ws)
        elif intent == "diagram":
            text = self._task_diagram(user_msg, ws)
        elif intent == "pixel_art":
            text = self._task_pixel_art(user_msg, ws)
        elif intent == "pattern":
            text = self._task_pattern(user_msg, ws)
        elif intent == "card":
            text = self._task_card(user_msg, ws)
        elif intent == "logo":
            text = self._task_logo(user_msg, ws)
        elif intent == "gradient":
            text = self._task_gradient(user_msg, ws)
        elif intent == "texture":
            text = self._task_texture(user_msg, ws)
        elif intent == "tile":
            text = self._task_tile(user_msg, ws)
        elif intent == "chart":
            text = self._task_chart(user_msg, ws)
        elif intent == "timeline":
            text = self._task_timeline(user_msg, ws)
        elif intent == "help":
            text = self._help_text()
        elif intent == "greeting":
            text = "Hey! What should I create?"
        else:
            text = self._task_general(user_msg, ws)

        if stream:
            for ch in text:
                stream(ch)
            stream("\x00")
        return EngineResponse(text=text, elapsed=self._done(t0), model_id=self.model_id)

    # ── Image Generation ─────────────────────────────────────────

    def _task_image(self, msg: str, ws: str) -> str:
        width, height = 800, 600
        seed = int(time.time() * 1000) % 100000
        lower = msg.lower()

        # Try to extract dimensions
        dim_match = None
        for pattern in [r"(\d+)\s*x\s*(\d+)", r"(\d+)\s*by\s*(\d+)"]:
            import re
            dim_match = re.search(pattern, lower)
            if dim_match:
                width = min(int(dim_match.group(1)), 2048)
                height = min(int(dim_match.group(2)), 2048)
                break

        # Choose color palette
        palettes = {
            "ocean": ["#0077B6", "#00B4D8", "#90E0EF", "#CAF0F8", "#023E8A"],
            "sunset": ["#FF6B6B", "#FFA07A", "#FFD700", "#FF4500", "#8B0000"],
            "forest": ["#2D6A4F", "#40916C", "#52B788", "#74C69D", "#1B4332"],
            "cyber": ["#FF00FF", "#00FFFF", "#FF1493", "#00FF00", "#FFD700"],
            "dark": ["#1a1a2e", "#16213e", "#0f3460", "#e94560", "#533483"],
            "neon": ["#FF00FF", "#00FF00", "#FF0080", "#0080FF", "#FFFF00"],
        }
        palette = palettes.get("cyber", palettes["ocean"])
        for name, colors in palettes.items():
            if name in lower:
                palette = colors
                break

        # Generate based on style keywords
        if any(w in lower for w in ["wave", "ocean", "water", "sea"]):
            img = _generate_wave(width, height, seed, palette)
        elif any(w in lower for w in ["circle", "orb", "bubble"]):
            img = _generate_circles(width, height, seed, palette)
        elif any(w in lower for w in ["mandala", "sacred", "spiritual"]):
            img = _generate_mandala(width, height, seed, palette)
        elif any(w in lower for w in ["landscape", "mountain", "nature", "scene"]):
            img = _generate_landscape(width, height, seed)
        else:
            img = _generate_plasma(width, height, seed, palette)

        # Add text if requested
        text_match = re.search(r'text[:"]*\s*["\']?(.+?)["\']?\s*$', lower)
        if text_match:
            overlay_text = text_match.group(1).strip().strip("\"'")
            img = _add_text_overlay(img, overlay_text)

        filename = f"image_{seed}.png"
        filepath = os.path.join(ws, filename)
        _save_image(img, filepath)

        return (
            f"**Created:** `{filename}`\n"
            f"**Size:** {width}x{height}\n"
            f"**Style:** Plasma fractal\n\n"
            f"![Generated Image]({filename})\n\n"
            f"File saved to: {filepath}"
        )

    def _task_icon(self, msg: str, ws: str) -> str:
        size = 256
        seed = int(time.time() * 1000) % 100000
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Generate icon shape
        colors = ["#00F2C2", "#0077B6", "#FF6B6B", "#FFD700", "#FF00FF"]
        color = random.choice(colors)
        rgb = tuple(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))

        shape = random.choice(["circle", "hexagon", "diamond", "star"])
        cx, cy = size // 2, size // 2
        r = size // 2 - 20

        if shape == "circle":
            draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=rgb)
        elif shape == "hexagon":
            points = []
            for i in range(6):
                angle = math.pi / 3 * i - math.pi / 6
                points.append((cx + int(r * math.cos(angle)), cy + int(r * math.sin(angle))))
            draw.polygon(points, fill=rgb)
        elif shape == "diamond":
            points = [(cx, cy-r), (cx+r, cy), (cx, cy+r), (cx-r, cy)]
            draw.polygon(points, fill=rgb)
        elif shape == "star":
            points = []
            for i in range(10):
                angle = math.pi / 5 * i - math.pi / 2
                radius = r if i % 2 == 0 else r * 0.5
                points.append((cx + int(radius * math.cos(angle)), cy + int(radius * math.sin(angle))))
            draw.polygon(points, fill=rgb)

        # Add letter if specified
        letter_match = re.search(r'letter[:"]*\s*["\']?([a-zA-Z])', msg.lower())
        if letter_match:
            letter = letter_match.group(1).upper()
            font = _get_font(size // 2)
            bbox = draw.textbbox((0, 0), letter, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            draw.text((cx - tw//2, cy - th//2 - 5), letter, fill=(255, 255, 255), font=font)

        filename = f"icon_{seed}.png"
        filepath = os.path.join(ws, filename)
        _save_image(img, filepath)

        return (
            f"**Created:** `{filename}`\n"
            f"**Size:** {size}x{size} ({shape})\n\n"
            f"File saved to: {filepath}"
        )

    def _task_wallpaper(self, msg: str, ws: str) -> str:
        width, height = 1920, 1080
        seed = int(time.time() * 1000) % 100000
        lower = msg.lower()

        palettes = {
            "ocean": ["#0077B6", "#00B4D8", "#90E0EF", "#CAF0F8", "#023E8A"],
            "sunset": ["#FF6B6B", "#FFA07A", "#FFD700", "#FF4500", "#8B0000"],
            "forest": ["#2D6A4F", "#40916C", "#52B788", "#74C69D", "#1B4332"],
            "cyber": ["#FF00FF", "#00FFFF", "#FF1493", "#00FF00", "#FFD700"],
        }
        palette = palettes["ocean"]
        for name, colors in palettes.items():
            if name in lower:
                palette = colors
                break

        if any(w in lower for w in ["wave", "ocean", "water"]):
            img = _generate_wave(width, height, seed, palette)
        elif any(w in lower for w in ["landscape", "mountain", "nature"]):
            img = _generate_landscape(width, height, seed)
        else:
            img = _generate_plasma(width, height, seed, palette)

        filename = f"wallpaper_{seed}.png"
        filepath = os.path.join(ws, filename)
        _save_image(img, filepath)

        return (
            f"**Created:** `{filename}`\n"
            f"**Size:** {width}x{height}\n"
            f"**Style:** Wallpaper\n\n"
            f"File saved to: {filepath}"
        )

    def _task_banner(self, msg: str, ws: str) -> str:
        width, height = 1200, 400
        seed = int(time.time() * 1000) % 100000

        palette = ["#0077B6", "#00B4D8", "#90E0EF", "#023E8A"]
        img = _generate_wave(width, height, seed, palette)

        # Add text
        text_match = re.search(r'(?:text|title|say)[:"]*\s*["\']?(.+?)["\']?\s*$', msg.lower())
        if text_match:
            text = text_match.group(1).strip().strip("\"'")
            img = _add_text_overlay(img, text, "center")

        filename = f"banner_{seed}.png"
        filepath = os.path.join(ws, filename)
        _save_image(img, filepath)

        return (
            f"**Created:** `{filename}`\n"
            f"**Size:** {width}x{height}\n\n"
            f"File saved to: {filepath}"
        )

    def _task_diagram(self, msg: str, ws: str) -> str:
        width, height = 800, 600
        seed = int(time.time() * 1000) % 100000
        img = Image.new("RGB", (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(img)

        # Draw a simple flowchart
        boxes = ["Start", "Process A", "Decision", "Process B", "End"]
        colors = ["#4CAF50", "#2196F3", "#FF9800", "#2196F3", "#F44336"]

        box_w, box_h = 150, 50
        start_x = width // 2 - box_w // 2
        y = 40

        for i, (box, color) in enumerate(zip(boxes, colors)):
            x = start_x
            draw.rounded_rectangle([x, y, x + box_w, y + box_h], radius=10, fill=color)
            # Center text
            font = _get_font(14)
            bbox = draw.textbbox((0, 0), box, font=font)
            tw = bbox[2] - bbox[0]
            draw.text((x + (box_w - tw) // 2, y + 15), box, fill=(255, 255, 255), font=font)

            # Arrow
            if i < len(boxes) - 1:
                arrow_y = y + box_h
                draw.line([(width // 2, arrow_y), (width // 2, arrow_y + 20)], fill=(100, 100, 100), width=2)
                draw.polygon([(width // 2 - 5, arrow_y + 15), (width // 2 + 5, arrow_y + 15), (width // 2, arrow_y + 25)], fill=(100, 100, 100))

            y += box_h + 30

        filename = f"diagram_{seed}.png"
        filepath = os.path.join(ws, filename)
        _save_image(img, filepath)

        return (
            f"**Created:** `{filename}`\n"
            f"**Size:** {width}x{height}\n"
            f"**Type:** Flowchart\n\n"
            f"File saved to: {filepath}"
        )

    def _task_pixel_art(self, msg: str, ws: str) -> str:
        pixel_size = 8
        grid_w, grid_h = 32, 32
        width = grid_w * pixel_size
        height = grid_h * pixel_size
        seed = int(time.time() * 1000) % 100000
        random.seed(seed)

        img = Image.new("RGB", (width, height), (20, 20, 30))
        draw = ImageDraw.Draw(img)

        colors = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", "#00FFFF",
                   "#FF8800", "#8800FF", "#00FF88", "#FF0088"]

        # Generate pixel creature
        for y in range(grid_h):
            for x in range(grid_w):
                if random.random() < 0.3:
                    color = random.choice(colors)
                    rgb = tuple(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
                    draw.rectangle([x * pixel_size, y * pixel_size,
                                    (x+1) * pixel_size - 1, (y+1) * pixel_size - 1], fill=rgb)

        filename = f"pixel_{seed}.png"
        filepath = os.path.join(ws, filename)
        _save_image(img, filepath)

        return (
            f"**Created:** `{filename}`\n"
            f"**Size:** {width}x{height} ({grid_w}x{grid_h} pixels)\n\n"
            f"File saved to: {filepath}"
        )

    def _task_pattern(self, msg: str, ws: str) -> str:
        width, height = 800, 800
        seed = int(time.time() * 1000) % 100000

        palette = ["#FF00FF", "#00FFFF", "#FF1493", "#00FF00"]
        img = _generate_mandala(width, height, seed, palette)

        filename = f"pattern_{seed}.png"
        filepath = os.path.join(ws, filename)
        _save_image(img, filepath)

        return (
            f"**Created:** `{filename}`\n"
            f"**Size:** {width}x{height}\n"
            f"**Style:** Mandala\n\n"
            f"File saved to: {filepath}"
        )

    def _task_card(self, msg: str, ws: str) -> str:
        width, height = 800, 450
        seed = int(time.time() * 1000) % 100000

        img = Image.new("RGB", (width, height), (240, 240, 245))
        draw = ImageDraw.Draw(img)

        # Accent stripe
        draw.rectangle([0, 0, width, 8], fill=(0, 120, 200))

        # Content area
        font_large = _get_font(28)
        font_small = _get_font(16)

        draw.text((40, 40), "Card Title", fill=(30, 30, 30), font=font_large)
        draw.text((40, 80), "Subtitle or description text goes here", fill=(100, 100, 100), font=font_small)

        # Separator
        draw.line([(40, 120), (width - 40, 120)], fill=(200, 200, 200), width=2)

        # Body
        draw.text((40, 140), "Main content area.\nAdd your details here.", fill=(60, 60, 60), font=font_small)

        filename = f"card_{seed}.png"
        filepath = os.path.join(ws, filename)
        _save_image(img, filepath)

        return (
            f"**Created:** `{filename}`\n"
            f"**Size:** {width}x{height}\n\n"
            f"File saved to: {filepath}"
        )

    def _task_logo(self, msg: str, ws: str) -> str:
        size = 512
        seed = int(time.time() * 1000) % 100000
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Background circle
        color = "#0077B6"
        rgb = tuple(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
        draw.ellipse([20, 20, size-20, size-20], fill=rgb)

        # Letter
        letter_match = re.search(r'(?:letter|text|name)[:"]*\s*["\']?([a-zA-Z])', msg.lower())
        letter = letter_match.group(1).upper() if letter_match else "L"
        font = _get_font(size // 3)
        bbox = draw.textbbox((0, 0), letter, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((size - tw) // 2, (size - th) // 2 - 10), letter, fill=(255, 255, 255), font=font)

        filename = f"logo_{seed}.png"
        filepath = os.path.join(ws, filename)
        _save_image(img, filepath)

        return (
            f"**Created:** `{filename}`\n"
            f"**Size:** {size}x{size}\n"
            f"**Style:** Circle logo\n\n"
            f"File saved to: {filepath}"
        )

    def _task_gradient(self, msg: str, ws: str) -> str:
        width, height = 800, 600
        seed = int(time.time() * 1000) % 100000
        random.seed(seed)
        lower = msg.lower()

        # Choose direction
        if any(w in lower for w in ["horizontal", "left", "right"]):
            direction = "horizontal"
        elif any(w in lower for w in ["vertical", "top", "bottom"]):
            direction = "vertical"
        elif any(w in lower for w in ["diagonal"]):
            direction = "diagonal"
        else:
            direction = random.choice(["horizontal", "vertical", "diagonal"])

        # Choose colors
        palettes = {
            "sunset": [(255, 100, 50), (255, 200, 50), (255, 50, 100)],
            "ocean": [(0, 50, 150), (0, 150, 200), (100, 200, 255)],
            "forest": [(20, 80, 30), (40, 140, 60), (80, 180, 100)],
            "neon": [(255, 0, 255), (0, 255, 255), (255, 255, 0)],
            "fire": [(200, 20, 0), (255, 100, 0), (255, 200, 0)],
        }
        palette_name = "sunset"
        for name in palettes:
            if name in lower:
                palette_name = name
                break
        colors = palettes[palette_name]

        img = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(img)

        for y in range(height):
            for x in range(width):
                if direction == "horizontal":
                    t = x / width
                elif direction == "vertical":
                    t = y / height
                else:
                    t = (x + y) / (width + height)

                # Interpolate through colors
                idx = t * (len(colors) - 1)
                i = min(int(idx), len(colors) - 2)
                frac = idx - i
                r = int(colors[i][0] + (colors[i+1][0] - colors[i][0]) * frac)
                g = int(colors[i][1] + (colors[i+1][1] - colors[i][1]) * frac)
                b = int(colors[i][2] + (colors[i+1][2] - colors[i][2]) * frac)
                img.putpixel((x, y), (r, g, b))

        filename = f"gradient_{seed}.png"
        filepath = os.path.join(ws, filename)
        _save_image(img, filepath)
        return (
            f"**Created:** `{filename}`\n"
            f"**Size:** {width}x{height}\n"
            f"**Style:** {direction} gradient ({palette_name})\n\n"
            f"File saved to: {filepath}"
        )

    def _task_texture(self, msg: str, ws: str) -> str:
        width, height = 512, 512
        seed = int(time.time() * 1000) % 100000
        random.seed(seed)
        lower = msg.lower()

        img = Image.new("RGB", (width, height))
        pixels = img.load()

        # Generate Perlin-like noise
        octaves = 4
        for y in range(height):
            for x in range(width):
                val = 0
                amp = 1
                freq = 0.01
                for _ in range(octaves):
                    val += amp * math.sin(x * freq + seed * 0.1) * math.cos(y * freq + seed * 0.2)
                    amp *= 0.5
                    freq *= 2
                val = (val + 1) / 2  # normalize to 0-1
                val = max(0, min(1, val))

                if "stone" in lower or "rock" in lower:
                    r = g = b = int(val * 120 + 40)
                elif "wood" in lower:
                    r = int(val * 80 + 100)
                    g = int(val * 40 + 60)
                    b = int(val * 20 + 30)
                elif "metal" in lower:
                    r = g = b = int(val * 80 + 160)
                else:
                    r = int(val * 100 + 50)
                    g = int(val * 80 + 40)
                    b = int(val * 60 + 30)
                pixels[x, y] = (r, g, b)

        filename = f"texture_{seed}.png"
        filepath = os.path.join(ws, filename)
        _save_image(img, filepath)
        return (
            f"**Created:** `{filename}`\n"
            f"**Size:** {width}x{height}\n"
            f"**Style:** Noise texture\n\n"
            f"File saved to: {filepath}"
        )

    def _task_tile(self, msg: str, ws: str) -> str:
        tile_size = 128
        grid = 4
        width = tile_size * grid
        height = tile_size * grid
        seed = int(time.time() * 1000) % 100000
        random.seed(seed)

        # Generate a single tile
        tile = Image.new("RGB", (tile_size, tile_size), (20, 20, 30))
        draw = ImageDraw.Draw(tile)

        colors = ["#FF00FF", "#00FFFF", "#FF1493", "#00FF00"]
        num_shapes = random.randint(3, 8)
        for _ in range(num_shapes):
            color = random.choice(colors)
            rgb = tuple(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
            shape = random.choice(["circle", "rect", "triangle"])
            x = random.randint(0, tile_size)
            y = random.randint(0, tile_size)
            size = random.randint(10, 40)
            if shape == "circle":
                draw.ellipse([x-size, y-size, x+size, y+size], fill=rgb)
            elif shape == "rect":
                draw.rectangle([x, y, x+size, y+size], fill=rgb)
            else:
                points = [(x, y-size), (x+size, y+size), (x-size, y+size)]
                draw.polygon(points, fill=rgb)

        # Tile it
        img = Image.new("RGB", (width, height))
        for gy in range(grid):
            for gx in range(grid):
                img.paste(tile, (gx * tile_size, gy * tile_size))

        filename = f"tile_{seed}.png"
        filepath = os.path.join(ws, filename)
        _save_image(img, filepath)
        return (
            f"**Created:** `{filename}`\n"
            f"**Size:** {width}x{height} ({grid}x{grid} tiles)\n"
            f"**Style:** Seamless pattern\n\n"
            f"File saved to: {filepath}"
        )

    def _task_chart(self, msg: str, ws: str) -> str:
        width, height = 800, 600
        seed = int(time.time() * 1000) % 100000
        random.seed(seed)
        lower = msg.lower()

        img = Image.new("RGB", (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(img)

        # Generate random data
        num_bars = random.randint(5, 10)
        data = [(f"Item {i+1}", random.randint(10, 100)) for i in range(num_bars)]
        max_val = max(v for _, v in data)

        colors = ["#0077B6", "#00B4D8", "#90E0EF", "#023E8A", "#00F2C2",
                   "#FF6B6B", "#FFD700", "#FF8800", "#00FF00", "#FF00FF"]

        # Chart area
        chart_left = 80
        chart_right = width - 40
        chart_top = 60
        chart_bottom = height - 80
        chart_w = chart_right - chart_left
        chart_h = chart_bottom - chart_top

        # Title
        font = _get_font(24)
        title = "Bar Chart"
        bbox = draw.textbbox((0, 0), title, font=font)
        tw = bbox[2] - bbox[0]
        draw.text(((width - tw) // 2, 20), title, fill=(30, 30, 30), font=font)

        # Bars
        bar_w = chart_w // (num_bars * 2)
        for i, (label, value) in enumerate(data):
            x = chart_left + (i * 2 + 0.5) * bar_w
            bar_h = int((value / max_val) * chart_h)
            y = chart_bottom - bar_h
            color = colors[i % len(colors)]
            rgb = tuple(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
            draw.rectangle([x, y, x + bar_w, chart_bottom], fill=rgb)

            # Label
            font_small = _get_font(12)
            bbox = draw.textbbox((0, 0), label, font=font_small)
            lw = bbox[2] - bbox[0]
            draw.text((x + (bar_w - lw) // 2, chart_bottom + 5), label, fill=(80, 80, 80), font=font_small)

            # Value
            val_text = str(value)
            bbox = draw.textbbox((0, 0), val_text, font=font_small)
            vw = bbox[2] - bbox[0]
            draw.text((x + (bar_w - vw) // 2, y - 15), val_text, fill=(30, 30, 30), font=font_small)

        # Axes
        draw.line([(chart_left, chart_top), (chart_left, chart_bottom)], fill=(100, 100, 100), width=2)
        draw.line([(chart_left, chart_bottom), (chart_right, chart_bottom)], fill=(100, 100, 100), width=2)

        filename = f"chart_{seed}.png"
        filepath = os.path.join(ws, filename)
        _save_image(img, filepath)
        return (
            f"**Created:** `{filename}`\n"
            f"**Size:** {width}x{height}\n"
            f"**Type:** Bar chart ({num_bars} items)\n\n"
            f"File saved to: {filepath}"
        )

    def _task_timeline(self, msg: str, ws: str) -> str:
        width, height = 800, 500
        seed = int(time.time() * 1000) % 100000
        random.seed(seed)

        img = Image.new("RGB", (width, height), (245, 245, 250))
        draw = ImageDraw.Draw(img)

        # Title
        font = _get_font(24)
        draw.text((40, 20), "Timeline", fill=(30, 30, 30), font=font)

        # Timeline line
        line_y = height // 2
        draw.line([(60, line_y), (width - 60, line_y)], fill=(0, 120, 200), width=3)

        # Events
        events = [
            ("Start", "Project kickoff"),
            ("Phase 1", "Research & planning"),
            ("Phase 2", "Development"),
            ("Phase 3", "Testing"),
            ("Launch", "Release v1.0"),
        ]
        num_events = len(events)
        spacing = (width - 120) // (num_events - 1)

        colors = ["#0077B6", "#00B4D8", "#00F2C2", "#FF6B6B", "#FFD700"]
        for i, (title, desc) in enumerate(events):
            x = 60 + i * spacing
            color = colors[i % len(colors)]
            rgb = tuple(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))

            # Dot
            draw.ellipse([x-8, line_y-8, x+8, line_y+8], fill=rgb)

            # Connect line
            if i % 2 == 0:
                draw.line([(x, line_y-8), (x, line_y-50)], fill=rgb, width=2)
                font_small = _get_font(14)
                draw.text((x-30, line_y-70), title, fill=(30, 30, 30), font=font_small)
                draw.text((x-40, line_y-50), desc, fill=(100, 100, 100), font=_get_font(11))
            else:
                draw.line([(x, line_y+8), (x, line_y+50)], fill=rgb, width=2)
                font_small = _get_font(14)
                draw.text((x-30, line_y+55), title, fill=(30, 30, 30), font=font_small)
                draw.text((x-40, line_y+75), desc, fill=(100, 100, 100), font=_get_font(11))

        filename = f"timeline_{seed}.png"
        filepath = os.path.join(ws, filename)
        _save_image(img, filepath)
        return (
            f"**Created:** `{filename}`\n"
            f"**Size:** {width}x{height}\n"
            f"**Type:** Timeline ({num_events} events)\n\n"
            f"File saved to: {filepath}"
        )

    def _task_general(self, msg: str, ws: str) -> str:
        # Default: generate a plasma image
        width, height = 800, 600
        seed = int(time.time() * 1000) % 100000
        palette = ["#FF00FF", "#00FFFF", "#FF1493", "#00FF00", "#FFD700"]
        img = _generate_plasma(width, height, seed, palette)

        filename = f"image_{seed}.png"
        filepath = os.path.join(ws, filename)
        _save_image(img, filepath)

        return (
            f"**Created:** `{filename}`\n"
            f"**Size:** {width}x{height}\n\n"
            f"File saved to: {filepath}\n\n"
            f"Tip: Be more specific for different styles:\n"
            f"- \"Generate an ocean wallpaper\"\n"
            f"- \"Create a neon icon with letter A\"\n"
            f"- \"Make a landscape image\""
        )

    def _help_text(self) -> str:
        return (
            "**Charybdis — Image Generator**\n\n"
            "I create real images, not just describe them.\n\n"
            "**What I can make:**\n"
            "- `generate image` — Plasma fractal art\n"
            "- `generate icon` — Geometric icons with optional letter\n"
            "- `generate wallpaper` — Desktop backgrounds\n"
            "- `generate banner` — Header images with text\n"
            "- `generate diagram` — Flowcharts and diagrams\n"
            "- `generate pixel art` — Retro pixel art\n"
            "- `generate pattern` — Mandala and geometric patterns\n"
            "- `generate card` — Card layouts\n"
            "- `generate logo` — Circle logos with initials\n\n"
            "**Styles:** ocean, sunset, forest, cyber, neon\n\n"
            "**Examples:**\n"
            "- \"Generate an ocean wallpaper\"\n"
            "- \"Create a neon icon with letter K\"\n"
            "- \"Make a sunset banner that says Hello\"\n"
            "- \"Generate a cyber image 1024x768\"\n\n"
            "All images are saved as PNG files."
        )
