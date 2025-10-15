from __future__ import annotations
from typing import List, Dict

from langchain_core.tools import tool
from tavily import TavilyClient

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from textwrap import wrap
import os, requests, json
from tavily import TavilyClient

from config import OPENAI_API_KEY, TAVILY_API_KEY, PUSHOVER_API, PUSHOVER_TOKEN, PUSHOVER_USER


# --- Tavily search: up-to-date web results (snippets + links) ---
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)


@tool
def web_search(query: str) -> List[Dict]:
    """Search the web for up-to-date information (uses Tavily)."""
    print(f"using web_search tool for {query}")

    response = tavily_client.search(
        query=query,
        search_depth="basic",   # or "advanced"
        include_images=False,
        max_results=5
    )
    print(f'tavily result: {response}')
    return response['results']

# --- Simple PDF generator using ReportLab ---
@tool
def generate_pdf_report(title: str, body: str, output_path: str = "reports/report.pdf") -> str:
    """Generate a simple PDF report with a title and multi-line body. Returns file path."""
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    x = 50
    y = height - 60

    c.setFont("Helvetica-Bold", 16)
    c.drawString(x, y, title)
    y -= 30

    c.setFont("Helvetica", 11)
    max_chars = 95
    for paragraph in body.split("\n"):
        for line in wrap(paragraph, max_chars):
            if y < 60:
                c.showPage()
                c.setFont("Helvetica", 11)
                y = height - 60
            c.drawString(x, y, line)
            y -= 14
        y -= 8  # paragraph spacing

    c.save()
    return os.path.abspath(output_path)

@tool
def pushover_notify(
    title: str,
    message: str,
    url: str | None = None,
    url_title: str | None = None,
    priority: int = 0,
    sound: str  | None = None,
) -> dict:
    """
    Send a push notificaiton to Pushover subscribers.
    Returns a JSON dict with 'status' and 'request' if successful.
    """
    token = PUSHOVER_TOKEN
    user = PUSHOVER_USER
    api = PUSHOVER_API

    if any(v is None for v in [token, user, api]):
        return { "status": 0, "error": "Missing PUSHOVER_API_TOKEN or PUSHOVER_USER_KEY"}
    
    data = {
        "token": token,
        "user": user,
        "title": title,
        "message": message,
        "priority": priority    # -2, -1, 0, 1, 2
    }
    
    if url:         data['url'] = url
    if url_title:   data['url_title'] = url_title
    if sound:       data['sound'] = sound

    print(data)

    try:
        req = requests.post(api, data=data, timeout=10)
        req.raise_for_status()
        return req.json()
    except requests.RequestException as e:
        return {"status": 0, "error": str(e)}
    

