"""Render the synthetic photo-review label documents used by the browser demo."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
WIDTH, HEIGHT = 1600, 1000
FONT_PATHS = (
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial.ttf",
)


def font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_PATHS:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def render_label(filename: str, lot: str) -> None:
    image = Image.new("RGB", (WIDTH, HEIGHT), "#f8fbf9")
    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle(
        (70, 70, WIDTH - 70, HEIGHT - 70), radius=28, fill="#ffffff", outline="#274438", width=5
    )
    draw.rectangle((70, 70, WIDTH - 70, 245), fill="#e8f3eb")
    draw.line((70, 245, WIDTH - 70, 245), fill="#274438", width=3)

    draw.text((125, 115), "RECEIVING LABEL", fill="#19372a", font=font(58))
    draw.text((125, 185), "M20 DISTRIBUTION COMPONENT", fill="#4d6658", font=font(25))

    field_font = font(56)
    label_font = font(24)
    field_rows = (
        ("ITEM", "M20-DIST-COMPONENT-NOS"),
        ("LOT", lot),
        ("QTY", "5"),
    )
    y = 365
    for label, value in field_rows:
        draw.text((145, y), f"{label}:", fill="#587064", font=label_font)
        draw.text((360, y - 13), value, fill="#142e22", font=field_font)
        draw.line((145, y + 78, WIDTH - 145, y + 78), fill="#d4e1d8", width=2)
        y += 150

    watermark = Image.new("RGBA", image.size, (0, 0, 0, 0))
    watermark_draw = ImageDraw.Draw(watermark)
    watermark_font = font(86)
    watermark_draw.text(
        (245, 725), "SYNTHETIC POC LABEL", fill=(39, 93, 65, 58), font=watermark_font
    )
    watermark = watermark.rotate(8, resample=Image.Resampling.BICUBIC, expand=False)
    image = Image.alpha_composite(image.convert("RGBA"), watermark).convert("RGB")
    image.save(ROOT / filename, format="PNG", optimize=True)


def main() -> None:
    render_label("input-01.png", "LOT-B5")
    render_label("input-02.png", "LOT-X9")


if __name__ == "__main__":
    main()
