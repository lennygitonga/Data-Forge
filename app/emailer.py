import resend
import os
import json
import csv
import io
from dotenv import load_dotenv

load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY")


def build_html_email(site: str, summary: dict) -> str:
    """
    Builds a beautiful HTML email from the AI summary.
    """
    key_points_html = "".join(
        f"<li>{point}</li>" for point in summary.get("key_points", [])
    )

    data_html = "".join(
        f"<tr><td style='padding:8px;border-bottom:1px solid #eee'>{item}</td></tr>"
        for item in summary.get("data", [])
    )

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; background: #f4f4f4; margin: 0; padding: 0; }}
            .container {{ max-width: 600px; margin: 30px auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .header {{ background: #1a1a2e; color: white; padding: 30px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 24px; }}
            .header p {{ margin: 5px 0 0; color: #aaa; font-size: 14px; }}
            .body {{ padding: 30px; }}
            .section {{ margin-bottom: 25px; }}
            .section h2 {{ color: #1a1a2e; font-size: 16px; border-bottom: 2px solid #f0f0f0; padding-bottom: 8px; }}
            .summary {{ background: #f8f9ff; border-left: 4px solid #1a1a2e; padding: 15px; border-radius: 0 8px 8px 0; line-height: 1.6; color: #333; }}
            ul {{ padding-left: 20px; color: #444; line-height: 1.8; }}
            table {{ width: 100%; border-collapse: collapse; font-size: 14px; color: #444; }}
            .footer {{ background: #f8f8f8; text-align: center; padding: 20px; font-size: 12px; color: #999; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>⚡ Data-Forge Report</h1>
                <p>Scraped from: {site}</p>
            </div>
            <div class="body">
                <div class="section">
                    <h2>📋 Summary</h2>
                    <div class="summary">{summary.get("summary", "No summary available.")}</div>
                </div>
                <div class="section">
                    <h2>🔑 Key Points</h2>
                    <ul>{key_points_html}</ul>
                </div>
                <div class="section">
                    <h2>📊 Extracted Data</h2>
                    <table>{data_html}</table>
                </div>
            </div>
            <div class="footer">
                Powered by Data-Forge • Automated Web Intelligence
            </div>
        </div>
    </body>
    </html>
    """


def build_csv_attachment(summary: dict) -> str:
    """
    Converts extracted data into a CSV string.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Data"])
    for item in summary.get("data", []):
        writer.writerow([item])
    return output.getvalue()


def send_report_email(to_email: str, site: str, summary: dict) -> bool:
    """
    Sends the scraped report to the user via Resend.
    """
    try:
        html = build_html_email(site, summary)
        csv_data = build_csv_attachment(summary)

        params = {
            "from": "Data-Forge <onboarding@resend.dev>",
            "to": [to_email],
            "subject": f"⚡ Data-Forge Report — {site}",
            "html": html,
            "attachments": [
                {
                    "filename": "scraped_data.csv",
                    "content": list(csv_data.encode("utf-8")),
                }
            ],
        }

        email = resend.Emails.send(params)
        print(f"✓ Email sent to {to_email} — ID: {email['id']}")
        return True

    except Exception as e:
        print(f"✗ Email failed: {e}")
        return False