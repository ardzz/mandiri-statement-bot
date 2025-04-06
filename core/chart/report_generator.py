import os
from PIL import Image, ImageDraw, ImageFont

from .visuals import (
    plot_balance_over_time,
    plot_incoming_vs_outgoing,
    plot_total_incoming_outgoing
)

def generate_all_charts(transactions: list[dict], user_id: int) -> None:
    """Generates individual charts and saves them to disk."""
    folder = f"cache/chart_cache"
    os.makedirs(folder, exist_ok=True)

    plot_balance_over_time(transactions, f"{folder}/{user_id}_balance.png")
    plot_incoming_vs_outgoing(transactions, f"{folder}/{user_id}_bar.png")
    plot_total_incoming_outgoing(transactions, f"{folder}/{user_id}_pie.png")

def combine_charts(user_id: int, period: str = "") -> str:
    """Combines individual charts into a single report image with an optional period label."""
    folder = f"cache/chart_cache"
    files = [
        f"{folder}/{user_id}_balance.png",
        f"{folder}/{user_id}_bar.png",
        f"{folder}/{user_id}_pie.png"
    ]

    images = [Image.open(f) for f in files if os.path.exists(f)]
    if not images:
        raise FileNotFoundError("No chart images found to combine.")

    width = min(img.width for img in images)
    resized = [img.resize((width, int(img.height * (width / img.width)))) for img in images]

    # Font setup for the period text
    try:
        font = ImageFont.truetype("arial.ttf", 28)
    except:
        font = ImageFont.load_default()

    title_height = 40 if period else 0
    total_height = sum(img.height for img in resized) + title_height
    combined_img = Image.new('RGB', (width, total_height), (255, 255, 255))

    draw = ImageDraw.Draw(combined_img)
    if period:
        draw.text((10, 10), f"Period: {period}", fill="black", font=font)

    y = title_height
    for img in resized:
        combined_img.paste(img, (0, y))
        y += img.height

    output_path = f"{folder}/{user_id}_report.png"
    combined_img.save(output_path)
    return output_path
