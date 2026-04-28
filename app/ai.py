import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")


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
    - If it's already a URL, clean it up and return it
    
    Examples:
    "bbc news" -> https://www.bbc.com/news
    "hacker news" -> https://news.ycombinator.com
    "amazon kenya" -> https://www.amazon.com
    "reddit python" -> https://www.reddit.com/r/python
    
    Website: "{site_name}"
    URL:
    """
    response = model.generate_content(prompt)
    url = response.text.strip()

    # make sure it starts with http
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
    Extract the most important structured data from the page as a clean list.
    For example: headlines, prices, names, dates, links — whatever is most relevant.
    Format each item on its own line like: Item: Value
    """

    response = model.generate_content(prompt)
    raw = response.text.strip()

    # parse the response into sections
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