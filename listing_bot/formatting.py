from html import escape

from .models import Announcement


def format_announcement(item: Announcement) -> str:
    lines = [
        f"🆕 <b>{escape(item.exchange)}</b>",
        f'<a href="{escape(item.url, quote=True)}">{escape(item.title)}</a>',
    ]
    if item.tickers:
        lines.append(f"Токены: <code>{escape(', '.join(item.tickers))}</code>")
    if item.listing_time:
        lines.append(f"Время листинга: {escape(item.listing_time)}")
    if item.published_at:
        lines.append(f"Опубликовано: {item.published_at:%Y-%m-%d %H:%M} UTC")
    return "\n".join(lines)
