"""Generate PICU BoardIQ PWA icons in multiple sizes.
Brand palette: navy #0A2540, mid-blue #1B6CB6, teal #14B8A6.
Renders a simple flat brain mark + EKG pulse line at each required size.
"""
from PIL import Image, ImageDraw, ImageFont
import os

# Required icon sizes (Android maskable, iOS apple-touch, favicons)
SIZES = [
    ("icon-192.png", 192, False),
    ("icon-512.png", 512, False),
    ("icon-192-maskable.png", 192, True),
    ("icon-512-maskable.png", 512, True),
    ("apple-touch-icon.png", 180, False),
    ("favicon-32.png", 32, False),
    ("favicon-16.png", 16, False),
]

NAVY = (10, 37, 64)
BLUE = (27, 108, 182)
TEAL = (20, 184, 166)
WHITE = (255, 255, 255)

def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def make_icon(size, maskable):
    """Render one icon at the given pixel size.
    maskable adds 10% safe-zone padding so Android can mask it to any shape.
    """
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Background gradient navy -> blue
    radius = int(size * (0.22 if not maskable else 0.30))
    # For maskable, extend background fully and shrink content
    pad = int(size * 0.12) if maskable else 0
    inner = size - 2 * pad
    # Manually paint a vertical gradient onto a temp image
    grad = Image.new("RGBA", (size, size), NAVY + (255,))
    gd = ImageDraw.Draw(grad)
    for y in range(size):
        t = y / size
        c = lerp(NAVY, BLUE, t)
        gd.line([(0, y), (size, y)], fill=c + (255,))

    # Mask for rounded square
    mask = Image.new("L", (size, size), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)
    img.paste(grad, (0, 0), mask)

    # Now draw the brain-pulse motif inside the content area
    cx, cy = size / 2, size / 2
    # Scale content: smaller if maskable to fit safe zone
    scale = inner / size if maskable else 1.0
    # Convenient unit: u = size / 64 scaled
    u = (size / 64) * scale

    # Brain outline -- abstract rounded blob (one curve, white)
    bw = u * 1.6  # stroke width for brain
    # Use ellipse + ellipse for a brain-ish shape (two bumps)
    brain_top = cy - u * 9
    brain_bot = cy + u * 6
    brain_left = cx - u * 13
    brain_right = cx + u * 13
    # Two overlapping rounded ellipses for hemispheres
    left_ell = [int(brain_left), int(brain_top + u * 2), int(cx + u * 1.5), int(brain_bot - u * 1)]
    right_ell = [int(cx - u * 1.5), int(brain_top + u * 2), int(brain_right), int(brain_bot - u * 1)]
    d.ellipse(left_ell, outline=WHITE + (255,), width=int(bw))
    d.ellipse(right_ell, outline=WHITE + (255,), width=int(bw))

    # EKG pulse line across the middle in teal
    line_y = cy + u * 1.5
    pulse = []
    # Start left, flat, spike up + down, flat, end right
    px = cx - u * 13
    pulse.append((px, line_y))
    px += u * 4; pulse.append((px, line_y))
    px += u * 1.5; pulse.append((px, line_y - u * 1))
    px += u * 1.0; pulse.append((px, line_y + u * 4))
    px += u * 1.0; pulse.append((px, line_y - u * 5))
    px += u * 1.0; pulse.append((px, line_y + u * 1))
    px += u * 1.5; pulse.append((px, line_y))
    px = cx + u * 13; pulse.append((px, line_y))
    d.line(pulse, fill=TEAL + (255,), width=int(u * 2.3), joint="curve")

    # Small dot at start of pulse
    r = max(2, int(u * 1.4))
    sx, sy = cx - u * 13, line_y
    d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=TEAL + (255,))

    # Letters "IQ" small under the brain in white
    try:
        font_size = max(8, int(u * 7))
        # Try a system font; fall back to default
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()
        text = "IQ"
        # Pillow >= 10: use textbbox
        try:
            bbox = d.textbbox((0, 0), text, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        except Exception:
            tw, th = font.getsize(text)
        tx = cx - tw / 2
        ty = brain_bot + u * 0.5
        d.text((tx, ty), text, fill=WHITE + (255,), font=font)
    except Exception:
        pass

    return img

OUT_DIR = os.path.dirname(__file__)
for name, sz, mask in SIZES:
    img = make_icon(sz, mask)
    path = os.path.join(OUT_DIR, name)
    img.save(path, "PNG", optimize=True)
    print(f"Saved {name} ({sz}px, maskable={mask}) -> {os.path.getsize(path)} bytes")

# Favicon.ico (multi-size)
ico_path = os.path.join(OUT_DIR, "favicon.ico")
ico_sizes = [(16, 16), (32, 32), (48, 48)]
imgs = [make_icon(s[0], False).resize(s) for s in ico_sizes]
imgs[0].save(ico_path, format="ICO", sizes=ico_sizes, append_images=imgs[1:])
print(f"Saved favicon.ico -> {os.path.getsize(ico_path)} bytes")

print("\nAll icons generated successfully.")
