import httpx
from bs4 import BeautifulSoup

def fetch_page(url: str) -> dict:
    """
    Try to fetch a webpage using httpx.
    If it fails, fall back to Playwright for JavaScript heavy sites.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = httpx.get(url, headers=headers, timeout=15, follow_redirects=True)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # remove scripts and styles - we don't need them
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()

        # get the clean text
        text = soup.get_text(separator="\n", strip=True)

        # trim to first 8000 characters so Gemini doesn't overflow
        text = text[:8000]

        return {
            "success": True,
            "url": str(response.url),
            "text": text,
            "used_playwright": False
        }

    except Exception as e:
        # static fetch failed — try Playwright
        print(f"Static fetch failed: {e} — trying Playwright...")
        return fetch_with_playwright(url)


def fetch_with_playwright(url: str) -> dict:
    """
    Fallback for JavaScript heavy sites using Playwright.
    """
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=30000)
            page.wait_for_load_state("networkidle")

            content = page.content()
            browser.close()

        soup = BeautifulSoup(content, "html.parser")

        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        text = text[:8000]

        return {
            "success": True,
            "url": url,
            "text": text,
            "used_playwright": True
        }

    except Exception as e:
        return {
            "success": False,
            "url": url,
            "text": "",
            "error": str(e),
            "used_playwright": True
        }