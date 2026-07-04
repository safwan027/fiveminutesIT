"""
email_renderer.py — Render context.json + brief.json into an email-friendly HTML newsletter
"""

import json
from datetime import datetime
from pathlib import Path

def _impact_color(impact: str) -> str:
    return {"pos": "#1a5c32", "neg": "#8b2020", "neu": "#4a4840"}.get(impact, "#4a4840")

def _impact_bg(impact: str) -> str:
    return {"pos": "#e6f4ec", "neg": "#fdecea", "neu": "#f1efe8"}.get(impact, "#f1efe8")

def _badge(text: str) -> str:
    return f'<span style="display:inline-block; font-size:11px; font-weight:500; border-radius:4px; padding:2px 8px; background:#eaf2fd; color:#1a3f7a; margin-right:4px;">{text}</span>'

def _geo_badge(geo: str) -> str:
    if "Foreign" in geo:
        return f'<span style="display:inline-block; font-size:11px; font-weight:500; border-radius:4px; padding:2px 8px; background:#f0eefe; color:#3d2f8e; margin-right:4px;">🌐 {geo}</span>'
    return f'<span style="display:inline-block; font-size:11px; font-weight:500; border-radius:4px; padding:2px 8px; background:#fef6e4; color:#7a4f0d; margin-right:4px;">🇮🇳 {geo}</span>'

def render_email(brief: dict, store: dict, today: str) -> str:
    score = brief["sentiment_score"]
    sentiment_7d_avg = brief["sentiment_7d_avg"]
    pct = int((score + 1) / 2 * 100)
    
    # --- Headers ---
    hl_items = ""
    for i, h in enumerate(brief.get("headlines", []), 1):
        bg = _impact_bg(h.get("impact", "neu"))
        color = _impact_color(h.get("impact", "neu"))
        impact_label = h.get("impact_label", "Neutral")
        
        hl_items += f"""
        <div style="background:#ffffff; border:1px solid #e0e0e0; border-radius:8px; margin-bottom:12px; overflow:hidden;">
            <div style="padding:14px 16px;">
                <div style="display:flex; align-items:flex-start; margin-bottom:8px;">
                    <span style="font-size:12px; color:#9e9c96; font-family:monospace; margin-right:12px; padding-top:2px;">{i:02d}</span>
                    <div style="flex:1;">
                        <div style="font-size:15px; font-weight:bold; color:#1a1916; margin-bottom:6px; line-height:1.4;">
                            {h.get('text', 'Headline')}
                        </div>
                        <div style="margin-bottom:8px;">
                            {_geo_badge(h.get('geo', 'India'))}
                            <span style="display:inline-block; font-size:11px; font-weight:500; border-radius:4px; padding:2px 8px; background:{bg}; color:{color}; margin-right:4px;">{impact_label}</span>
                            {_badge(h.get('badge', ''))}
                        </div>
                    </div>
                </div>
                <div style="padding-left:30px; font-size:14px; color:#4a4840; line-height:1.6;">
                    {h.get('detail', '')}
                </div>
            </div>
        </div>
        """

    # --- Market Outlook (Para A) inside details/summary ---
    para_a = store.get("para_a", {})
    sections_html = ""
    for s in para_a.get("sections", []):
        sections_html += f"""
        <div style="margin-bottom:16px;">
            <h4 style="font-size:14px; font-weight:bold; color:#1a1916; margin-bottom:6px;">{s.get('title', '')}</h4>
            <p style="font-size:14px; color:#4a4840; line-height:1.6; margin:0;">{s.get('content', '')}</p>
        </div>
        """

    # --- Market Dynamics (Changelog) inside details/summary ---
    entries = list(reversed(store.get("changelog", [])))[:5] # Show last 5 to not bloat email
    entries_html = ""
    if not entries:
        entries_html = "<p style='font-size:14px; color:#9e9c96;'>No changes recorded yet.</p>"
    else:
        for entry in entries:
            entries_html += f"""
            <div style="border-bottom:1px solid #e0e0e0; padding:12px 0;">
                <div style="font-size:12px; color:#9e9c96; font-family:monospace; margin-bottom:4px;">{entry.get('date', '')}</div>
                <div style="font-size:14px; font-weight:bold; color:#1a1916; margin-bottom:6px;">{entry.get('title', 'Change detected')}</div>
                <div style="font-size:13px; color:#4a4840;">{entry.get('reason', 'No specific reason provided.')}</div>
            </div>
            """

    # Expandable sections CSS fallback
    # We use details/summary, which is supported by Apple Mail and modern clients.
    # We also provide a fallback styling so they look like headers.

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>fiveminutesIT</title>
<style>
    body {{
        margin: 0; padding: 0; background-color: #f7f5f0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }}
    .email-container {{
        max-width: 800px; margin: 0 auto; background-color: #ffffff;
    }}
    .header {{
        background-color: #ffffff; padding: 20px 24px; border-bottom: 1px solid #e0e0e0; text-align: center;
    }}
    .content {{
        padding: 32px 24px;
    }}
    .summary-box {{
        padding: 16px; border-radius: 8px; margin-bottom: 12px;
    }}
    .details-box {{
        background: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; margin-bottom: 16px; overflow: hidden;
    }}
    summary {{
        cursor: pointer; padding: 14px 16px; font-weight: bold; background-color: #faf9f6; outline: none; font-size: 15px; color: #b20710; list-style: none; display: flex; justify-content: space-between; align-items: center;
    }}
    summary::-webkit-details-marker {{
        display: none;
    }}
    summary::after {{
        content: '+'; font-size: 18px; font-weight: normal; color: #b20710;
    }}
    details[open] summary::after {{
        content: '-';
    }}
    .details-content {{
        padding: 16px; border-top: 1px solid #e0e0e0;
    }}
    .footer {{
        padding: 24px; text-align: center; font-size: 12px; color: #9e9c96; border-top: 1px solid #e0e0e0; background-color: #f7f5f0;
    }}
</style>
</head>
<body>
    <div style="background-color: #f7f5f0; padding-top: 20px; padding-bottom: 40px;">
        <div class="email-container">
            <!-- Header -->
            <div class="header">
                <h1 style="margin: 0; font-size: 28px; color: #000000; letter-spacing: -0.02em;">fiveminutesIT</h1>
                <p style="margin: 8px 0 0; font-size: 14px; color: #6b6860;">Latest Issue — {datetime.strptime(today, "%Y-%m-%d").strftime("%d %b %Y")}</p>
            </div>
            
            <!-- Main Content -->
            <div class="content">
                <!-- Metrics -->
                <div style="display:flex; justify-content:space-between; margin-bottom: 24px; border:1px solid #e0e0e0; border-radius:8px; padding:16px;">
                    <div style="text-align:center; width:50%; border-right:1px solid #e0e0e0;">

                        <div style="font-size:12px; color:#6b6860; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:4px;">Market Mood</div>
                        <div style="font-size:24px; font-weight:bold; color:{_impact_color('pos' if score > 0.1 else 'neg' if score < -0.1 else 'neu')};">
                            {brief.get('sentiment_label', 'Neutral').title()}
                        </div>            
                    </div>
                    <div style="text-align:center; width:50%;">
                        <div style="font-size:12px; color:#6b6860; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:4px;">Sentiment Score</div>
                        <div style="font-size:24px; font-weight:bold; color:#4a4840;">
                            {brief.get('sentiment_label', 'Neutral').title()}
                        </div>
                    </div>
                    <div style="text-align:center; width:50%;">
                        <div style="font-size:12px; color:#6b6860; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:4px;">7-Day Average Score</div>
                        <div style="font-size:24px; font-weight:bold; color:#4a4840;">
                            {store["sentiment_7d_avg"]:+.2f}
                        </div>  
                    </div>
                </div>

                <!-- Headlines -->
                <h2 style="font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em; color: #9e9c96; border-bottom: 1px solid #e0e0e0; padding-bottom: 8px; margin-bottom: 16px; margin-top: 32px;">Today's Headlines</h2>
                {hl_items}

                <!-- Summaries -->
                <h2 style="font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em; color: #9e9c96; border-bottom: 1px solid #e0e0e0; padding-bottom: 8px; margin-bottom: 16px;">How today affects your job search</h2>
                
                <div class="summary-box" style="background:#e6f4ec; border-left:4px solid #7bc49a;">
                    <h3 style="margin:0 0 6px; font-size:13px; color:#1a5c32; text-transform:uppercase;">Headlines lifting sentiment</h3>
                    <p style="margin:0; font-size:14px; color:#1f4a2a; line-height:1.5;">{brief.get('summary_positive', '')}</p>
                </div>
                
                <div class="summary-box" style="background:#fdecea; border-left:4px solid #f4a4a4;">
                    <h3 style="margin:0 0 6px; font-size:13px; color:#8b2020; text-transform:uppercase;">Headlines dragging sentiment</h3>
                    <p style="margin:0; font-size:14px; color:#6a1818; line-height:1.5;">{brief.get('summary_negative', '')}</p>
                </div>
                
                <div class="summary-box" style="background:#f1efe8; border-left:4px solid #c8c6be; margin-bottom:24px;">
                    <h3 style="margin:0 0 6px; font-size:13px; color:#4a4840; text-transform:uppercase;">Structurally Important</h3>
                    <p style="margin:0; font-size:14px; color:#4a4840; line-height:1.5;">{brief.get('summary_neutral', '')}</p>
                </div>

                

                <!-- Expandable Sections -->
                <div style="margin-top: 32px;">
                    <details class="details-box">
                        <summary>Market Outlook</summary>
                        <div class="details-content">
                            {sections_html}
                        </div>
                    </details>
                    
                    <details class="details-box">
                        <summary>Market Dynamics</summary>
                        <div class="details-content">
                            {entries_html}
                        </div>
                    </details>
                </div>
                
            </div>
            
            <!-- Footer -->
            <div class="footer">
                <p style="margin: 0;">Information is curated and analysed with AI and can make mistakes</p>
                
            </div>
        </div>
    </div>
</body>
</html>"""
    return html
