import os
import time
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MAX_RETRIES = 3
RETRY_DELAY = 2


def call_groq(prompt: str, max_tokens: int = 1000) -> str:
    """
    Call Groq API with retry logic.
    """
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            last_error = str(e)
            print(f"Groq attempt {attempt} failed: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)

    raise Exception(f"Groq API failed after {MAX_RETRIES} attempts: {last_error}")


def resolve_site(site_name: str) -> str:
    """
    Takes a plain name like 'bbc news' and returns a full URL.
    """
    prompt = f"""
    A user wants to scrape this website: "{site_name}"

    Your job is to return the full URL of that website.
    Rules:
    - Return ONLY the URL, nothing else
    - Always include https://
    - Return the most popular/official version of the site
    - If it is already a URL, clean it up and return it

    Examples:
    "bbc news" -> https://www.bbc.com/news
    "hacker news" -> https://news.ycombinator.com
    "amazon kenya" -> https://www.amazon.com
    "reddit python" -> https://www.reddit.com/r/python

    Website: "{site_name}"
    URL:
    """

    url = call_groq(prompt, max_tokens=50)

    # clean up the response
    url = url.strip().split("\n")[0].strip()
    if not url.startswith("http"):
        url = "https://" + url

    return url


def summarise_content(site: str, text: str, query: str = None) -> dict:
    """
    Takes scraped text and returns a structured summary.
    """
    query_line = f"The user specifically wants to know: {query}" if query else ""

    prompt = f"""
    You scraped the website: {site}
    {query_line}

    Here is the raw scraped content:
    {text}

    Your job is to produce a clear, useful summary for the user.

    Return your response in this exact format:

    SUMMARY:
    Write 3-5 sentences summarising the most important information found on this page.

    KEY POINTS:
    - Point 1
    - Point 2
    - Point 3
    - Point 4
    - Point 5

    DATA:
    Extract ALL structured data items from the page — do not limit to 5 or 10.
    Extract every single item you can find — every headline, every price, every product,
    every discount, every listing. The more the better.
    Format each item on its own line like: Item: Value
    There is no maximum — extract everything.
    """

    raw = call_groq(prompt, max_tokens=4000)

    result = {
        "summary": "",
        "key_points": [],
        "data": []
    }

    current_section = None
    for line in raw.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("SUMMARY:"):
            current_section = "summary"
        elif line.startswith("KEY POINTS:"):
            current_section = "key_points"
        elif line.startswith("DATA:"):
            current_section = "data"
        elif current_section == "summary":
            result["summary"] += line + " "
        elif current_section == "key_points" and line.startswith("-"):
            result["key_points"].append(line[1:].strip())
        elif current_section == "data" and line:
            result["data"].append(line)

    return result