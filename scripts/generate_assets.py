"""
scripts/generate_assets.py - High-Resolution Asset Generator for Centinela Sísmico.
Creates:
1. pwa/og-image.png (1200x630 px) - Social preview card for WhatsApp, Facebook, LinkedIn, Twitter
2. pwa/icon-192.png (192x192 px) - Standard PWA home screen icon
3. pwa/icon-512.png (512x512 px) - High-DPI PWA splash icon
4. pwa/apple-touch-icon.png (180x180 px) - iOS Safari home screen icon
"""

import os
import sys
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PWA_DIR = os.path.join(REPO_ROOT, "pwa")

FONT_REGULAR = "C:/Windows/Fonts/segoeui.ttf"
FONT_BOLD = "C:/Windows/Fonts/segoeuib.ttf"
FONT_SEMIBOLD = "C:/Windows/Fonts/seguisb.ttf" if os.path.exists("C:/Windows/Fonts/seguisb.ttf") else FONT_BOLD

def draw_shield(draw, cx, cy, w, h, fill_color, border_color, border_width=4):
    """Draw a classic heraldic protective shield shape."""
    top_y = cy - h // 2
    bot_y = cy + h // 2
    left_x = cx - w // 2
    right_x = cx + w // 2
    mid_y = top_y + int(h * 0.55)

    # Shield polygon points
    points = [
        (left_x, top_y),
        (right_x, top_y),
        (right_x, mid_y),
        (cx, bot_y),
        (left_x, mid_y),
    ]
    draw.polygon(points, fill=fill_color)
    if border_width > 0:
        # Draw border lines
        draw.line([(left_x, top_y), (right_x, top_y), (right_x, mid_y), (cx, bot_y), (left_x, mid_y), (left_x, top_y)], 
                  fill=border_color, width=border_width)

def draw_seismic_wave(draw, start_x, end_x, y_center, amplitude, color, width=3):
    """Draw an authentic seismic waveform (flat line -> P-wave tremor -> major S-wave displacement -> coda)."""
    points = []
    total_len = end_x - start_x
    for i in range(total_len + 1):
        x = start_x + i
        t = i / float(total_len)
        
        # Envelope: calm baseline -> small P tremor at 0.25 -> big S wave at 0.55 -> damped tail
        if t < 0.2:
            dy = 0.0
        elif t < 0.4:
            # P-wave micro-tremor
            env = math.sin((t - 0.2) / 0.2 * math.pi)
            dy = env * amplitude * 0.22 * math.sin(t * 70)
        elif t < 0.75:
            # S-wave major shear pulse
            env = math.sin((t - 0.4) / 0.35 * math.pi)
            dy = env * amplitude * math.sin(t * 38)
        else:
            # Coda decay
            decay = math.exp(-(t - 0.75) * 8)
            dy = decay * amplitude * 0.25 * math.sin(t * 45)
            
        points.append((x, int(y_center + dy)))
    
    for k in range(len(points) - 1):
        draw.line([points[k], points[k+1]], fill=color, width=width)

def generate_og_image():
    W, H = 1200, 630
    img = Image.new("RGBA", (W, H), (11, 17, 33, 255))
    draw = ImageDraw.Draw(img)

    # 1. Subtle Radial Glow Background
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    # Cyan glow behind shield
    glow_draw.ellipse((850 - 240, 280 - 240, 850 + 240, 280 + 240), fill=(2, 132, 199, 50))
    # Emerald glow on left
    glow_draw.ellipse((160 - 200, 150 - 200, 160 + 200, 150 + 200), fill=(16, 185, 129, 30))
    glow = glow.filter(ImageFilter.GaussianBlur(70))
    img = Image.alpha_composite(img, glow)
    draw = ImageDraw.Draw(img)

    # 2. Ambient grid lines
    grid_color = (255, 255, 255, 10)
    for gx in range(0, W, 80):
        draw.line([(gx, 0), (gx, H)], fill=grid_color, width=1)
    for gy in range(0, H, 80):
        draw.line([(0, gy), (W, gy)], fill=grid_color, width=1)

    # 3. Seismic Wave across background
    draw_seismic_wave(draw, 0, W, 360, amplitude=65, color=(14, 165, 233, 75), width=2)
    draw_seismic_wave(draw, 0, W, 360, amplitude=55, color=(56, 189, 248, 140), width=3)

    # 4. Large Emblem / Shield on the Right Side
    shield_x, shield_y = 920, 290
    # Outer pulse circles
    draw.ellipse((shield_x - 170, shield_y - 170, shield_x + 170, shield_y + 170), outline=(2, 132, 199, 45), width=2)
    draw.ellipse((shield_x - 145, shield_y - 145, shield_x + 145, shield_y + 145), outline=(16, 185, 129, 75), width=2)
    draw.ellipse((shield_x - 120, shield_y - 120, shield_x + 120, shield_y + 120), outline=(56, 189, 248, 110), width=2)

    # Protective Shield
    draw_shield(draw, shield_x, shield_y, w=180, h=220, 
                fill_color=(15, 28, 56, 245), 
                border_color=(56, 189, 248, 255), 
                border_width=5)
    
    # Inner pulse inside shield
    draw_seismic_wave(draw, shield_x - 75, shield_x + 75, shield_y + 35, amplitude=32, color=(16, 185, 129, 255), width=4)

    # Geometric Lightning Bolt inside shield (no font glyph dependency)
    lx, ly = shield_x, shield_y - 25
    bolt_points = [
        (lx + 6, ly - 42),
        (lx - 16, ly + 2),
        (lx, ly + 2),
        (lx - 8, ly + 40),
        (lx + 18, ly - 2),
        (lx + 2, ly - 2)
    ]
    draw.polygon(bolt_points, fill=(253, 224, 71, 255))
    draw.line(bolt_points + [bolt_points[0]], fill=(254, 240, 138, 255), width=1)

    # 5. Left Side: Typography & Hierarchy
    left_margin = 80

    # Category Pill
    pill_w, pill_h = 420, 36
    draw.rounded_rectangle([left_margin, 70, left_margin + pill_w, 70 + pill_h], radius=18, 
                           fill=(2, 132, 199, 45), outline=(56, 189, 248, 160), width=1)
    font_cat = ImageFont.truetype(FONT_SEMIBOLD, 13)
    draw.text((left_margin + 20, 79), "GEOFÍSICA APLICADA & PSICOLOGÍA DE EMERGENCIAS", 
              font=font_cat, fill=(186, 230, 253, 255))

    # Main App Title
    font_title = ImageFont.truetype(FONT_BOLD, 64)
    draw.text((left_margin, 122), "Centinela Sísmico", font=font_title, fill=(255, 255, 255, 255))

    # Subtitle / Philosophy
    font_sub = ImageFont.truetype(FONT_SEMIBOLD, 23)
    draw.text((left_margin, 205), "Protección Familiar • Alerta Temprana • Cero Fatiga de Alarma", 
              font=font_sub, fill=(56, 189, 248, 255))

    # Core Value Proposition
    font_desc = ImageFont.truetype(FONT_REGULAR, 20)
    draw.text((left_margin, 252), 
              "El vigía inteligente que calcula la onda destructiva antes de que llegue a tu hogar.\nTecnología Calmada con datos del USGS, 100% gratuita y funcional sin internet.", 
              font=font_desc, fill=(203, 213, 225, 240), spacing=8)

    # 6. Feature Badges (Pills without broken emoji glyphs)
    pills = [
        ("Cero Sobresaltos (USGS MMI)", (16, 185, 129)),
        ("Ventaja Onda S por GPS", (2, 132, 199)),
        ("100% Funcional Sin Internet", (234, 179, 8)),
        ("Guía de Grietas ATC-20", (168, 85, 247)),
    ]
    pill_x = left_margin
    pill_y = 350
    for text, (r, g, b) in pills:
        font_pill = ImageFont.truetype(FONT_SEMIBOLD, 14)
        bbox = draw.textbbox((0, 0), text, font=font_pill)
        tw = bbox[2] - bbox[0] + 34
        draw.rounded_rectangle([pill_x, pill_y, pill_x + tw, pill_y + 36], radius=10, 
                               fill=(r, g, b, 40), outline=(r, g, b, 180), width=1)
        # Draw checkmark bullet
        draw.text((pill_x + 10, pill_y + 8), "•", font=font_pill, fill=(r, g, b, 255))
        draw.text((pill_x + 22, pill_y + 8), text, font=font_pill, fill=(255, 255, 255, 240))
        pill_x += tw + 14
        if pill_x > 700:
            pill_x = left_margin
            pill_y += 48

    # 7. Bottom Signature & Accreditation
    draw.line([(left_margin, 520), (W - left_margin, 520)], fill=(255, 255, 255, 30), width=1)
    
    font_foot_bold = ImageFont.truetype(FONT_BOLD, 16)
    font_foot_reg = ImageFont.truetype(FONT_REGULAR, 16)
    
    draw.text((left_margin, 545), "Fabio Ignacio Torres Benítez", font=font_foot_bold, fill=(255, 255, 255, 255))
    draw.text((left_margin + 235, 545), "• Psicólogo Clínico & Cognitivo | Ingeniero de Datos & IA", font=font_foot_reg, fill=(148, 163, 184, 240))
    
    url_text = "neurodeveloper11.github.io/centinela-sismico"
    bbox_url = draw.textbbox((0, 0), url_text, font=font_foot_bold)
    url_w = bbox_url[2] - bbox_url[0]
    draw.text((W - left_margin - url_w, 545), url_text, font=font_foot_bold, fill=(56, 189, 248, 255))

    # Save optimized PNG
    out_path = os.path.join(PWA_DIR, "og-image.png")
    img.convert("RGB").save(out_path, format="PNG", optimize=True)
    size_kb = os.path.getsize(out_path) / 1024.0
    print(f"✅ Generated {out_path} ({size_kb:.1f} KB)")


def generate_pwa_icon(size):
    img = Image.new("RGBA", (size, size), (11, 17, 33, 255))
    draw = ImageDraw.Draw(img)

    # Background subtle radial circle
    pad = int(size * 0.06)
    draw.rounded_rectangle([pad, pad, size - pad, size - pad], radius=int(size * 0.22), 
                           fill=(15, 23, 42, 255), outline=(2, 132, 199, 180), width=max(2, size // 64))

    # Protective shield
    cx, cy = size // 2, size // 2
    sw, sh = int(size * 0.58), int(size * 0.68)
    draw_shield(draw, cx, cy + int(size * 0.02), w=sw, h=sh, 
                fill_color=(2, 132, 199, 220), 
                border_color=(56, 189, 248, 255), 
                border_width=max(2, size // 48))

    # Seismic pulse line
    draw_seismic_wave(draw, cx - int(sw * 0.42), cx + int(sw * 0.42), cy + int(size * 0.05), 
                      amplitude=int(size * 0.12), color=(16, 185, 129, 255), width=max(3, size // 32))

    filename = f"icon-{size}.png" if size in (192, 512) else "apple-touch-icon.png"
    out_path = os.path.join(PWA_DIR, filename)
    img.save(out_path, format="PNG", optimize=True)
    print(f"✅ Generated {out_path} ({size}x{size})")


if __name__ == "__main__":
    generate_og_image()
    generate_pwa_icon(192)
    generate_pwa_icon(512)
    generate_pwa_icon(180)
