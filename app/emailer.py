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
            body {{ font-family: Arial, sans-serif; background: #FAF7F2; margin: 0; padding: 0; }}
            .container {{ max-width: 600px; margin: 30px auto; background: #FFFFFF; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.08); border: 1px solid #E8D9B5; }}
            .header {{ background: #6B0F1A; color: white; padding: 35px 30px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 22px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; color: #C9A84C; }}
            .header p {{ margin: 8px 0 0; color: #e8c9c9; font-size: 13px; letter-spacing: 1px; }}
            .body {{ padding: 35px 30px; }}
            .section {{ margin-bottom: 28px; }}
            .section h2 {{ color: #6B0F1A; font-size: 13px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; border-bottom: 2px solid #C9A84C; padding-bottom: 8px; margin-bottom: 14px; }}
            .summary {{ background: #FAF7F2; border-left: 4px solid #6B0F1A; padding: 16px 18px; border-radius: 0 6px 6px 0; line-height: 1.7; color: #1A1A1A; font-size: 14px; }}
            ul {{ padding-left: 18px; color: #333; line-height: 2; font-size: 14px; margin: 0; }}
            ul li {{ border-bottom: 1px solid #FAF7F2; padding: 2px 0; }}
            table {{ width: 100%; border-collapse: collapse; font-size: 13px; color: #444; }}
            td {{ padding: 10px 8px; border-bottom: 1px solid #E8D9B5; }}
            tr:last-child td {{ border-bottom: none; }}
            .footer {{ background: #6B0F1A; text-align: center; padding: 18px; font-size: 11px; color: #C9A84C; letter-spacing: 1px; text-transform: uppercase; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Data-Forge</h1>
                <p>Intelligence Report — {site}</p>
            </div>
            <div class="body">
                <div class="section">
                    <h2>Summary</h2>
                    <div class="summary">{summary.get("summary", "No summary available.")}</div>
                </div>
                <div class="section">
                    <h2>Key Points</h2>
                    <ul>{key_points_html}</ul>
                </div>
                <div class="section">
                    <h2>Extracted Data</h2>
                    <table>{data_html}</table>
                </div>
            </div>
            <div class="footer">
                Powered by Data-Forge — Automated Web Intelligence
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