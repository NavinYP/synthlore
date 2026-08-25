import os
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
from typing import Dict, Any

class VisualProfile:
    def __init__(self, font_path: str, font_size: int, bg_color: tuple, text_color: tuple, has_grid: bool = False, is_stamped: bool = False):
        self.font_path = font_path
        self.font_size = font_size
        self.bg_color = bg_color
        self.text_color = text_color
        self.has_grid = has_grid
        self.is_stamped = is_stamped

class VisualRenderer:
    def __init__(self):
        # Resolve fonts (macOS defaults + fallback)
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        custom_courier = os.path.join(base_dir, "assets", "fonts", "CourierPrime-Regular.ttf")
        
        courier = custom_courier if os.path.exists(custom_courier) else "/System/Library/Fonts/Courier.ttc"
        serif = "/System/Library/Fonts/Times.ttc"
        script = "/System/Library/Fonts/MarkerFelt.ttc"
        
        self.profiles = {
            "Guild Ledger": VisualProfile(courier, 18, (240, 235, 220), (30, 30, 30), has_grid=True),
            "Dispatcher Log": VisualProfile(courier, 16, (220, 230, 240), (20, 20, 40), has_grid=True),
            "Official Contract": VisualProfile(serif, 20, (250, 248, 240), (10, 10, 10), is_stamped=True),
            "Smuggler's Diary": VisualProfile(script, 22, (200, 190, 170), (60, 40, 20)),
            "Maintenance Report": VisualProfile(courier, 16, (230, 230, 220), (40, 40, 40)),
            "Letter of Grievance": VisualProfile(script, 24, (245, 240, 230), (50, 10, 10)),
            "Procurement Order": VisualProfile(serif, 18, (255, 255, 255), (0, 0, 0), has_grid=True, is_stamped=True)
        }
        # Fallback profile
        self.default_profile = VisualProfile(courier, 18, (255, 255, 255), (0, 0, 0))

    def _draw_grid(self, draw: ImageDraw.ImageDraw, width: int, height: int, color: tuple):
        """Draws a ledger-style grid."""
        for y in range(0, height, 40):
            draw.line([(0, y), (width, y)], fill=color, width=1)
        for x in range(0, width, 100):
            draw.line([(x, 0), (x, height)], fill=color, width=1)
            
    def _draw_stamp(self, img: Image.Image, draw: ImageDraw.ImageDraw, width: int, height: int):
        """Draws a fake 'APPROVED' guild seal."""
        import random
        # Random placement near bottom right
        x = width - random.randint(150, 250)
        y = height - random.randint(150, 250)
        
        # Draw a red circle
        draw.ellipse([(x, y), (x+100, y+100)], outline=(200, 50, 50), width=4)
        draw.ellipse([(x+5, y+5), (x+95, y+95)], outline=(200, 50, 50), width=2)
        
        # Add text (requires a font, use default if needed)
        try:
            stamp_font = ImageFont.truetype("/System/Library/Fonts/Courier.ttc", 16)
        except:
            stamp_font = ImageFont.load_default()
            
        draw.text((x+15, y+40), "SEALED", fill=(200, 50, 50), font=stamp_font)

    def render_document(self, text: str, doc_type: str, output_path: str):
        profile = self.profiles.get(doc_type, self.default_profile)
        
        width, height = 800, 1200
        img = Image.new('RGB', (width, height), color=profile.bg_color)
        draw = ImageDraw.Draw(img)
        
        if profile.has_grid:
            grid_color = tuple(max(0, c - 20) for c in profile.bg_color)
            self._draw_grid(draw, width, height, grid_color)
            
        try:
            font = ImageFont.truetype(profile.font_path, profile.font_size)
        except Exception as e:
            print(f"Warning: Could not load font {profile.font_path}, using default. Error: {e}")
            font = ImageFont.load_default()
            
        # Very basic word wrap
        margin = 50
        offset = 50
        
        # Break text into paragraphs, then wrap
        paragraphs = text.split("\n")
        for para in paragraphs:
            if not para.strip():
                offset += profile.font_size
                continue
                
            # Heuristic wrap length based on font size
            wrap_width = int((width - 2 * margin) / (profile.font_size * 0.6))
            wrapped_lines = textwrap.wrap(para, width=wrap_width)
            
            for line in wrapped_lines:
                if offset > height - 100:
                    break # Stop if we run out of page (for simplicity in v1)
                draw.text((margin, offset), line, font=font, fill=profile.text_color)
                offset += int(profile.font_size * 1.5)
            offset += profile.font_size # Paragraph spacing
            
        if profile.is_stamped:
            self._draw_stamp(img, draw, width, height)
            
        # Add slight blur to simulate ink bleed
        img = img.filter(ImageFilter.GaussianBlur(radius=0.3))
        
        # Save
        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        img.save(output_path)
        return output_path
