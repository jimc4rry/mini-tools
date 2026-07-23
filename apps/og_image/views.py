"""
Dynamic og:image generator: a branded gradient card with the page title,
so links shared to Slack/X/iMessage/etc. get a real preview instead of a
blank box. Pure function of the `title` query param - nothing stored,
nothing rate-limited (crawlers are expected to fetch this often, and a
render takes a few milliseconds).
"""
import io

from django.http import HttpResponse
from django.views.decorators.http import require_GET
from PIL import Image, ImageDraw, ImageFont, ImageOps

WIDTH, HEIGHT = 1200, 630
MARGIN = 90
MAX_TITLE_LENGTH = 200
MAX_LINES = 4

ACCENT = (109, 94, 252)       # #6d5efc
ACCENT_2 = (34, 211, 238)     # #22d3ee
OVERLAY = (9, 11, 18, 90)     # matches --bg, for text contrast
WHITE = (255, 255, 255, 255)
BRAND = (255, 255, 255, 200)


def _gradient_background():
    # A 135deg linear gradient (top-left -> bottom-right) between the two
    # brand accent colors, matching CSS `--accent-gradient` in base.html.
    # Upscale well past the crop's diagonal before rotating, so the rotated
    # corners (padded black by PIL) fall outside the final crop area.
    base_size = max(WIDTH, HEIGHT) * 2
    mask = Image.linear_gradient("L").resize((base_size, base_size))
    mask = mask.rotate(135, expand=True, resample=Image.BICUBIC)
    left = (mask.width - WIDTH) // 2
    top = (mask.height - HEIGHT) // 2
    mask = mask.crop((left, top, left + WIDTH, top + HEIGHT))
    return ImageOps.colorize(mask, black=ACCENT, white=ACCENT_2).convert("RGBA")


def _wrap_title(draw, text, font, max_width):
    words = text.split()
    lines, current = [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=font) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines[:MAX_LINES]


@require_GET
def generate(request):
    title = (request.GET.get("title") or "Minitools Hub").strip()[:MAX_TITLE_LENGTH]

    img = _gradient_background()
    overlay = Image.new("RGBA", img.size, OVERLAY)
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    title_font = ImageFont.load_default(size=64)
    lines = _wrap_title(draw, title, title_font, WIDTH - 2 * MARGIN)
    line_height = 78
    y = (HEIGHT - line_height * len(lines)) // 2 - 20
    for line in lines:
        line_width = draw.textlength(line, font=title_font)
        draw.text(((WIDTH - line_width) / 2, y), line, font=title_font, fill=WHITE)
        y += line_height

    brand_font = ImageFont.load_default(size=30)
    draw.text((MARGIN, HEIGHT - 74), "Minitools Hub", font=brand_font, fill=BRAND)

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    response = HttpResponse(buf.getvalue(), content_type="image/png")
    response["Cache-Control"] = "public, max-age=86400"
    return response
