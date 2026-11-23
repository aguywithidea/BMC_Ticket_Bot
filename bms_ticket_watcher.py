"""Watch a BookMyShow movie page and alert when show booking controls appear."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import webbrowser
from urllib.request import Request, urlopen

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


BOOKING_WORDS = re.compile(r"\b(book\s*(tickets|now)|select\s*seats|available\s*shows?)\b", re.I)
SHOWTIME = re.compile(r"\b(?:[01]?\d|2[0-3]):[0-5]\d\s*(?:am|pm)?\b", re.I)
NOT_AVAILABLE = re.compile(r"\b(not\s*available|coming\s*soon|notify\s*me|no\s*shows?)\b", re.I)


def has_booking_signal(page) -> tuple[bool, str]:
    """Require a booking phrase and a visible time/show control to reduce false alerts."""
    body = page.locator("body").inner_text(timeout=8000)
    if NOT_AVAILABLE.search(body) and not BOOKING_WORDS.search(body):
        return False, ""
    candidates = page.get_by_role("button").all_inner_texts()
    candidates += page.get_by_role("link").all_inner_texts()
    controls = " ".join(candidates)
    if BOOKING_WORDS.search(controls) and SHOWTIME.search(body):
        excerpt = " ".join(body.split())
        return True, excerpt[:500]
    return False, ""


def notify(title: str, url: str, detail: str) -> None:
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    if messagebox.askyesno(title, f"Showtimes or booking controls may be live.\n\n{detail[:350]}\n\nOpen BookMyShow now?"):
        webbrowser.open(url)
    root.destroy()


def send_telegram(url: str, detail: str) -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    text = f"🎟️ Avengers: Doomsday tickets may be open in Chennai!\n\n{url}\n\n{detail[:500]}"
    request = Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=json.dumps({"chat_id": chat_id, "text": text, "disable_web_page_preview": True}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=20) as response:
        result = json.loads(response.read())
    if not result.get("ok"):
        raise RuntimeError(f"Telegram rejected the message: {result}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Alert when a BookMyShow movie page shows bookable showtimes.")
    parser.add_argument("url", help="Full BookMyShow movie page URL for your city")
    parser.add_argument("--interval", type=int, default=300, help="Check interval in seconds (default: 300; minimum: 120)")
    parser.add_argument("--once", action="store_true", help="Check once and exit")
    parser.add_argument("--state-file", help="Optional file used to avoid repeating alerts while availability remains live")
    args = parser.parse_args()
    if not args.url.startswith(("https://in.bookmyshow.com/", "https://www.bookmyshow.com/")):
        parser.error("Use a BookMyShow movie page URL beginning with https://in.bookmyshow.com/")
    if args.interval < 120:
        parser.error("Use an interval of at least 120 seconds")

    print(f"Watching {args.url}\nChecking every {args.interval} seconds. Press Ctrl+C to stop.", flush=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(locale="en-IN")
        alerted = False
        if args.state_file and os.path.exists(args.state_file):
            try:
                with open(args.state_file, encoding="utf-8") as state:
                    alerted = json.load(state).get("alerted", False)
            except (OSError, ValueError):
                alerted = False
        try:
            while True:
                try:
                    page.goto(args.url, wait_until="domcontentloaded", timeout=45000)
                    page.wait_for_timeout(5000)
                    live, detail = has_booking_signal(page)
                    print(time.strftime("%Y-%m-%d %H:%M:%S"), "booking signal" if live else "no showtimes detected", flush=True)
                    if live and not alerted:
                        alerted = True
                        if os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"):
                            send_telegram(args.url, detail)
                        else:
                            notify("BookMyShow tickets may be open", args.url, detail)
                    elif not live:
                        alerted = False
                    if args.state_file:
                        os.makedirs(os.path.dirname(args.state_file) or ".", exist_ok=True)
                        with open(args.state_file, "w", encoding="utf-8") as state:
                            json.dump({"alerted": alerted}, state)
                except (PlaywrightTimeoutError, Exception) as exc:
                    print(f"Page check failed: {exc}", file=sys.stderr, flush=True)
                if args.once:
                    break
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("Stopped.")
        finally:
            browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
