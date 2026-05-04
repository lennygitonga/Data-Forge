import httpx
from bs4 import BeautifulSoup
import time

MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds between retries

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def clean_html(html: str) -> str:
    """Strip scripts, styles, nav, footer and return clean text."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    # remove excessive blank lines
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return "\n".join(lines)[:8000]


def fetch_page(url: str) -> dict:
    """
    Fetch a webpage with retry logic.
    Falls back to Playwright if static fetch fails.
    """
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"Static fetch attempt {attempt}/{MAX_RETRIES}: {url}")
            response = httpx.get(
                url,
                headers=HEADERS,
                timeout=15,
                follow_redirects=True
            )
            response.raise_for_status()

            text = clean_html(response.text)

            if len(text) < 100:
                raise Exception("Page content too short — likely blocked or JS-rendered")

            return {
                "success": True,
                "url": str(response.url),
                "text": text,
                "used_playwright": False
            }

        except Exception as e:
            last_error = str(e)
            print(f"Attempt {attempt} failed: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)

    # all static attempts failed — try Playwright
    print(f"Static fetch failed after {MAX_RETRIES} attempts — trying Playwright...")
    return fetch_with_playwright(url)


def fetch_with_playwright(url: str) -> dict:
    """
    Fallback for JavaScript heavy sites using Playwright with stealth mode.
    """
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"Playwright attempt {attempt}/{MAX_RETRIES}: {url}")
            from playwright.sync_api import sync_playwright
            from playwright_stealth import stealth_sync

            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-blink-features=AutomationControlled",
                        "--disable-infobars",
                        "--window-size=1920,1080",
                    ]
                )
                context = browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    locale="en-US",
                    timezone_id="America/New_York",
                )
                page = context.new_page()

                # apply stealth mode
                stealth_sync(page)

                page.goto(url, timeout=30000, wait_until="networkidle")

                # wait a bit like a human would
                page.wait_for_timeout(2000)

                content = page.content()
                browser.close()

            text = clean_html(content)

            if len(text) < 100:
                raise Exception("Playwright returned empty content — site may require login")

            return {
                "success": True,
                "url": url,
                "text": text,
                "used_playwright": True
            }

        except Exception as e:
            last_error = str(e)
            print(f"Playwright attempt {attempt} failed: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)

    return {
        "success": False,
        "url": url,
        "text": "",
        "error": f"All fetch attempts failed. Last error: {last_error}",
        "used_playwright": True
    }