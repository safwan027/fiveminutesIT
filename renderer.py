"""
renderer.py — Render context.json + brief.json into HTML pages
Produces: index.html (daily), para-a.html, changelog.html
"""

import json
from datetime import date
from pathlib import Path


# ── Shared HTML shell ──────────────────────────────────────────────────────────

def _shell(title: str, active_tab: str, body: str) -> str:
    tabs = [
        ("index.html", "daily", "Today's Brief"),
        ("para-a.html", "para-a", "Market Context"),
        ("changelog.html", "changelog", "Change Log"),
    ]
    nav = "\n".join(
        f'<a href="{href}" class="tab{" active" if key == active_tab else ""}">'
        f'{label}</a>'
        for href, key, label in tabs
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — India IT Brief</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@400;500&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {{
  --bg: #f7f5f0;
  --surface: #ffffff;
  --border: rgba(0,0,0,0.1);
  --text: #1a1916;
  --muted: #6b6860;
  --hint: #9e9c96;
  --green-bg: #e6f4ec; --green-text: #1a5c32; --green-border: #7bc49a;
  --red-bg: #fdecea; --red-text: #8b2020; --red-border: #f4a4a4;
  --amber-bg: #fef6e4; --amber-text: #7a4f0d; --amber-border: #f5cc7c;
  --blue-bg: #eaf2fd; --blue-text: #1a3f7a; --blue-border: #8fbee8;
  --purple-bg: #f0eefe; --purple-text: #3d2f8e; --purple-border: #b8adf0;
  --gray-bg: #f1efe8; --gray-text: #4a4840; --gray-border: #c8c6be;
  --font-display: 'DM Serif Display', Georgia, serif;
  --font-body: 'DM Sans', system-ui, sans-serif;
  --font-mono: 'DM Mono', monospace;
  --radius: 10px;
}}
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: var(--font-body);
  background: var(--bg);
  color: var(--text);
  font-size: 15px;
  line-height: 1.6;
  min-height: 100vh;
}}
.site-header {{
  background: var(--surface);
  border-bottom: 1px solid var(--border);
}}
.header-top {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid #e0e0e0;
}}
.header-left {{
  display: flex;
  gap: 16px;
  font-size: 14px;
  font-weight: 500;
}}
.e-paper {{ color: #b20710; font-weight: bold; text-decoration: none; }}
.site-logo {{
  font-family: var(--font-display);
  font-size: 40px;
  color: #000;
  text-decoration: none;
  letter-spacing: -0.01em;
}}
.header-right {{
  display: flex;
  gap: 16px;
  align-items: center;
  font-size: 13px;
  font-weight: 500;
}}
.subscribe-btn {{
  background: #b20710;
  color: #fff;
  padding: 6px 16px;
  text-decoration: none;
  border-radius: 2px;
}}
.header-bottom {{
  display: flex;
  justify-content: center;
  padding: 12px 24px;
}}
.nav {{
  display: flex;
  gap: 32px;
}}
.tab {{
  font-family: var(--font-display);
  font-size: 18px;
  color: #000;
  text-decoration: none;
}}
.tab.active {{ font-weight: bold; border-bottom: 2px solid #000; }}
.main {{
  max-width: 760px;
  margin: 0 auto;
  padding: 32px 24px 64px;
}}
.page-meta {{ font-size: 12px; color: var(--hint); margin-bottom: 24px; }}
h1 {{ font-family: var(--font-display); font-size: 28px; letter-spacing: -0.02em; margin-bottom: 6px; }}
h2 {{ font-family: var(--font-display); font-size: 20px; letter-spacing: -0.01em; margin: 32px 0 12px; }}
h3 {{ font-size: 14px; font-weight: 500; color: var(--text); margin-bottom: 8px; }}
p {{ color: var(--muted); margin-bottom: 12px; line-height: 1.7; }}
.badge {{
  display: inline-block;
  font-size: 11px;
  font-weight: 500;
  border-radius: 4px;
  padding: 2px 8px;
}}
.badge-green {{ background: var(--green-bg); color: var(--green-text); }}
.badge-red {{ background: var(--red-bg); color: var(--red-text); }}
.badge-amber {{ background: var(--amber-bg); color: var(--amber-text); }}
.badge-blue {{ background: var(--blue-bg); color: var(--blue-text); }}
.badge-gray {{ background: var(--gray-bg); color: var(--gray-text); }}
.badge-purple {{ background: var(--purple-bg); color: var(--purple-text); }}
.card {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  margin-bottom: 10px;
}}
.card-header {{
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 16px;
  cursor: pointer;
  user-select: none;
}}
.card-header:hover {{ background: #faf9f6; }}
.card-num {{ font-size: 12px; color: var(--hint); font-family: var(--font-mono); padding-top: 2px; min-width: 20px; }}
.card-content {{ flex: 1; }}
.card-title {{ font-size: 14px; font-weight: 500; line-height: 1.4; margin-bottom: 6px; color: var(--text); }}
.card-meta {{ display: flex; gap: 6px; flex-wrap: wrap; align-items: center; }}
.card-body {{
  display: none;
  padding: 0 16px 14px 48px;
  font-size: 13px;
  color: var(--muted);
  line-height: 1.65;
  border-top: 1px solid var(--border);
  padding-top: 12px;
}}
.card-body.open {{ display: block; }}
.chevron {{ font-size: 14px; color: var(--hint); transition: transform 0.2s; flex-shrink: 0; margin-top: 2px; }}
.chevron.open {{ transform: rotate(180deg); }}
.summary-block {{
  border-radius: var(--radius);
  padding: 14px 16px;
  margin-bottom: 10px;
}}
.summary-block.pos {{ border-left: 3px solid var(--green-border); background: var(--green-bg); }}
.summary-block.neg {{ border-left: 3px solid var(--red-border); background: var(--red-bg); }}
.summary-block.neu {{ border-left: 3px solid var(--gray-border); background: var(--gray-bg); }}
.summary-block h3 {{ font-size: 12px; font-weight: 500; letter-spacing: .04em; text-transform: uppercase; margin-bottom: 6px; }}
.summary-block.pos h3 {{ color: var(--green-text); }}
.summary-block.neg h3 {{ color: var(--red-text); }}
.summary-block.neu h3 {{ color: var(--gray-text); }}
.summary-block p {{ font-size: 13px; margin-bottom: 0; }}
.summary-block.pos p {{ color: #1f4a2a; }}
.summary-block.neg p {{ color: #6a1818; }}
.summary-block.neu p {{ color: #4a4840; }}
.gauge-wrap {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 14px 16px; display: flex; align-items: center; gap: 14px; margin-bottom: 24px; }}
.gauge-label {{ font-size: 13px; color: var(--muted); min-width: 100px; }}
.gauge-track {{ flex: 1; height: 5px; background: var(--border); border-radius: 3px; position: relative; overflow: visible; }}
.gauge-fill {{ position: absolute; left: 0; top: 0; height: 5px; border-radius: 3px; background: linear-gradient(to right, #e05050, #f5b941, #3caa6c); width: 100%; }}
.gauge-dot {{ position: absolute; top: -5px; width: 15px; height: 15px; border-radius: 50%; background: var(--surface); border: 2px solid #d4a520; transform: translateX(-50%); }}
.gauge-value {{ font-size: 13px; font-weight: 500; color: var(--text); min-width: 90px; text-align: right; }}
.section-label {{ font-size: 11px; font-weight: 500; letter-spacing: .06em; text-transform: uppercase; color: var(--hint); border-bottom: 1px solid var(--border); padding-bottom: 8px; margin-bottom: 16px; margin-top: 32px; }}
.section-label:first-of-type {{ margin-top: 0; }}
.para-section {{ margin-bottom: 24px; }}
.para-section h3 {{ font-size: 15px; font-weight: 500; margin-bottom: 8px; color: var(--text); }}
.para-section p {{ font-size: 14px; color: var(--muted); line-height: 1.75; margin-bottom: 0; }}
.cl-entry {{ border: 1px solid var(--border); border-radius: var(--radius); margin-bottom: 10px; overflow: hidden; }}
.cl-header {{ display: flex; align-items: center; gap: 10px; padding: 12px 16px; background: var(--surface); cursor: pointer; }}
.cl-header:hover {{ background: #faf9f6; }}
.cl-date {{ font-size: 12px; font-family: var(--font-mono); color: var(--hint); min-width: 90px; }}
.cl-title {{ font-size: 13px; font-weight: 500; flex: 1; color: var(--text); }}
.cl-body {{ display: none; font-family: var(--font-mono); font-size: 12px; }}
.cl-body.open {{ display: block; }}
.diff-section {{ padding: 10px 16px; border-top: 1px solid var(--border); }}
.diff-label {{ font-size: 10px; font-weight: 500; letter-spacing: .06em; text-transform: uppercase; color: var(--hint); font-family: var(--font-body); margin-bottom: 8px; }}
.diff-line {{ display: flex; gap: 10px; padding: 3px 8px; margin: 0 -8px; font-size: 12px; font-family: var(--font-body); line-height: 1.55; }}
.diff-line.added {{ background: var(--green-bg); }}
.diff-line.removed {{ background: var(--red-bg); }}
.diff-sign {{ min-width: 12px; font-weight: 500; font-family: var(--font-mono); }}
.diff-line.added .diff-sign {{ color: var(--green-text); }}
.diff-line.removed .diff-sign {{ color: var(--red-text); text-decoration: line-through; opacity: 0.7; }}
.diff-line.context .diff-sign {{ color: var(--hint); }}
.diff-text.removed {{ opacity: 0.65; }}
.reason-block {{ padding: 12px 16px; background: var(--gray-bg); border-top: 1px solid var(--border); }}
.reason-label {{ font-size: 10px; font-weight: 500; letter-spacing: .06em; text-transform: uppercase; color: var(--hint); font-family: var(--font-body); margin-bottom: 6px; }}
.reason-text {{ font-size: 12px; color: var(--gray-text); line-height: 1.6; font-family: var(--font-body); }}
.pills {{ display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }}
.pill {{ font-size: 11px; background: var(--surface); border: 1px solid var(--border); border-radius: 4px; padding: 2px 8px; color: var(--muted); font-family: var(--font-body); }}
.cl-empty {{ padding: 12px 16px; font-size: 13px; color: var(--muted); font-family: var(--font-body); border-top: 1px solid var(--border); }}
.metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-bottom: 24px; }}
.metric {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 14px 16px; }}
.metric-label {{ font-size: 11px; color: var(--hint); margin-bottom: 6px; }}
.metric-value {{ font-size: 22px; font-weight: 500; line-height: 1; }}
.metric-value.up {{ color: var(--green-text); }}
.metric-value.down {{ color: var(--red-text); }}
.metric-value.neutral {{ color: var(--purple-text); }}
.metric-sub {{ font-size: 11px; color: var(--hint); margin-top: 4px; }}
footer {{ border-top: 1px solid var(--border); padding: 24px; text-align: center; font-size: 12px; color: var(--hint); }}
</style>
</head>
<body>
<header class="site-header">
  <div class="header-top">
    <div class="header-left">
      <span style="color: var(--text);">May 23, 2026</span>
      <a href="#" class="e-paper">e-Paper</a>
    </div>
    <a href="index.html" class="site-logo">INDIA IT BRIEF</a>
    <div class="header-right">
      <a href="#" style="color:var(--text);text-decoration:none">eBooks</a>
      <a href="#" style="color:var(--text);text-decoration:none">LOGIN</a>
      <a href="#" class="subscribe-btn">SUBSCRIBE</a>
    </div>
  </div>
  <div class="header-bottom">
    <div class="nav">{nav}</div>
  </div>
</header>
<main class="main">
{body}
</main>
<footer>
 
</footer>
<script>
document.querySelectorAll('.card-header').forEach(h => {{
  h.addEventListener('click', () => {{
    const body = h.nextElementSibling;
    const chev = h.querySelector('.chevron');
    const open = body.classList.toggle('open');
    if (chev) chev.classList.toggle('open', open);
  }});
}});
document.querySelectorAll('.cl-header').forEach(h => {{
  h.addEventListener('click', () => {{
    const body = h.nextElementSibling;
    const chev = h.querySelector('.chevron');
    const open = body.classList.toggle('open');
    if (chev) chev.classList.toggle('open', open);
  }});
}});
</script>
</body>
</html>"""


# ── Impact → badge mapping ─────────────────────────────────────────────────────

def _impact_badge(impact: str, label: str) -> str:
    cls = {"pos": "badge-green", "neg": "badge-red", "neu": "badge-gray"}.get(impact, "badge-gray")
    return f'<span class="badge {cls}">{label}</span>'


def _badge(text: str) -> str:
    return f'<span class="badge badge-blue">{text}</span>'


def _geo_badge(geo: str) -> str:
    if "Foreign" in geo:
        return f'<span class="badge badge-purple">🌐 {geo}</span>'
    return f'<span class="badge badge-amber">🇮🇳 {geo}</span>'


def _severity_badge(sev: str) -> str:
    cls = {"major": "badge-red", "moderate": "badge-amber",
           "minor": "badge-green", "none": "badge-gray"}.get(sev, "badge-gray")
    label = {"major": "Major shift", "moderate": "Moderate shift",
             "minor": "Minor shift", "none": "No change"}.get(sev, sev)
    return f'<span class="badge {cls}">{label}</span>'


# ── Daily brief page ───────────────────────────────────────────────────────────

def render_daily(brief: dict, store: dict, today: str) -> str:
    score = brief["sentiment_score"]
    pct = int((score + 1) / 2 * 100)  # map -1..+1 to 0..100%

    # Metrics
    hist = store["sentiment_history"]
    recent_avg = store["sentiment_7d_avg"]
    label_counts = store["sentiment_label_counts"]
    total_days = sum(label_counts.values())

    metrics = f"""
<div class="metrics-grid">
  <div class="metric">
    <div class="metric-label">Today's sentiment</div>
    <div class="metric-value {'up' if score > 0.1 else 'down' if score < -0.1 else 'neutral'}">{score:+.2f}</div>
    <div class="metric-sub">{brief['sentiment_label'].title()}</div>
  </div>
  <div class="metric">
    <div class="metric-label">7-day average</div>
    <div class="metric-value neutral">{recent_avg:+.2f}</div>
    <div class="metric-sub">Rolling window</div>
  </div>
  <div class="metric">
    <div class="metric-label">Headlines analysed</div>
    <div class="metric-value neutral">{len(brief['headlines'])}</div>
    <div class="metric-sub">After filter</div>
  </div>
  <div class="metric">
    <div class="metric-label">Para A version</div>
    <div class="metric-value neutral">v{store['para_a']['version']}</div>
    <div class="metric-sub">Updated {store['para_a']['last_updated'] or 'not yet'}</div>
  </div>
</div>"""

    gauge = f"""
<div class="gauge-wrap">
  <span class="gauge-label">Market mood</span>
  <div class="gauge-track">
    <div class="gauge-fill"></div>
    <div class="gauge-dot" style="left:{pct}%"></div>
  </div>
  <span class="gauge-value">{brief['sentiment_label'].title()}</span>
</div>"""

    # Headlines
    hl_items = ""
    for i, h in enumerate(brief.get("headlines", []), 1):
        hl_items += f"""
<div class="card">
  <div class="card-header">
    <span class="card-num">{i:02d}</span>
    <div class="card-content">
      <div class="card-title">{h.get('text', '')}</div>
      <div class="card-meta">
        {_geo_badge(h.get('geo', 'India'))}
        {_impact_badge(h.get('impact', 'neu'), h.get('impact_label', 'Neutral'))}
        {_badge(h.get('badge', ''))}
      </div>
    </div>
    <span class="chevron">&#8964;</span>
  </div>
  <div class="card-body">{h.get('detail', '')}</div>
</div>"""

    # Summaries
    summaries = f"""
<div class="summary-block pos">
  <h3>Headlines lifting sentiment</h3>
  <p>{brief.get('summary_positive', '')}</p>
</div>
<div class="summary-block neg">
  <h3>Headlines dragging sentiment</h3>
  <p>{brief.get('summary_negative', '')}</p>
</div>
<div class="summary-block neu">
  <h3>Structurally important — not sentiment-moving</h3>
  <p>{brief.get('summary_neutral', '')}</p>
</div>"""

    body = f"""
<h1>India IT Job Market Brief</h1>
<p class="page-meta">Daily update · {today} · For freshers and IT professionals</p>
{metrics}
{gauge}
<div class="section-label">Headlines — tap to expand</div>
{hl_items}
<div class="section-label">Summary — how today affects your job search</div>
{summaries}
"""
    return _shell(f"Daily Brief — {today}", "daily", body)


# ── Para A page ────────────────────────────────────────────────────────────────

def render_para_a(store: dict) -> str:
    para_a = store["para_a"]
    sections_html = ""
    for s in para_a["sections"]:
        modified = s.get("last_modified_date", "")
        modified_tag = f'<span class="badge badge-gray" style="font-size:10px">Updated {modified}</span>' if modified else ""
        sections_html += f"""
<div class="para-section">
  <h3>{s['title']} {modified_tag}</h3>
  <p>{s['content']}</p>
</div>"""

    # Sentiment history mini-chart (last 14 days as text bars)
    hist = store["sentiment_history"][-14:]
    hist_lines = ""
    for e in reversed(hist):
        bar_w = int((e["score"] + 1) / 2 * 100)
        color = "#3caa6c" if e["score"] > 0.1 else "#e05050" if e["score"] < -0.1 else "#d4a520"
        hist_lines += f"""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">
  <span style="font-size:11px;color:var(--hint);font-family:var(--font-mono);min-width:85px">{e['date']}</span>
  <div style="flex:1;height:6px;background:var(--border);border-radius:3px;overflow:hidden">
    <div style="height:6px;width:{bar_w}%;background:{color};border-radius:3px"></div>
  </div>
  <span style="font-size:11px;color:var(--muted);min-width:50px;text-align:right">{e['score']:+.2f} {e['label']}</span>
</div>"""

    body = f"""
<h1>Market Context</h1>
<p class="page-meta">Para A · v{para_a['version']} · Last updated: {para_a.get('last_updated', 'initial')} · Updated only when market shifts</p>

<div class="section-label">Broader view — Indian IT job market</div>
{sections_html}

<div class="section-label">Sentiment history — last 14 days</div>
<div style="background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:16px 18px">
{hist_lines if hist_lines else '<p style="font-size:13px;color:var(--hint)">No history yet — check back after the first few runs.</p>'}
</div>
"""
    return _shell("Market Context", "para-a", body)


# ── Changelog page ─────────────────────────────────────────────────────────────

def render_changelog(store: dict) -> str:
    entries = list(reversed(store.get("changelog", [])))

    if not entries:
        entries_html = '<p style="color:var(--hint);font-size:14px">No changes recorded yet.</p>'
    else:
        entries_html = ""
        for i, entry in enumerate(entries):
            sev = entry.get("severity", "none")
            is_first = i == 0

            # Build diff body
            diff_html = ""
            for section in entry.get("sections", []):
                lines_html = ""
                for line in section.get("lines", []):
                    t = line.get("type", "context")
                    sign = "+" if t == "added" else "−" if t == "removed" else " "
                    text_cls = "removed" if t == "removed" else ""
                    lines_html += f"""
<div class="diff-line {t}">
  <span class="diff-sign">{sign}</span>
  <span class="diff-text {text_cls}">{line.get('text', '')}</span>
</div>"""
                diff_html += f"""
<div class="diff-section">
  <div class="diff-label">{section.get('section_label', '')}</div>
  {lines_html}
</div>"""

            # Reason + source pills
            reason = entry.get("reason", "")
            src_ids = entry.get("source_headline_ids", [])
            pills = "".join(
                f'<span class="pill">hl:{sid}</span>' for sid in src_ids
            )
            reason_block = f"""
<div class="reason-block">
  <div class="reason-label">Why this changed</div>
  <div class="reason-text">{reason}</div>
  {f'<div class="pills">{pills}</div>' if pills else ''}
</div>""" if reason else ""

            no_change = sev == "none"
            body_content = (
                f'<div class="cl-empty">{entry.get("reason", "No shift detected.")}</div>'
                if no_change or not entry.get("sections")
                else diff_html + reason_block
            )

            entries_html += f"""
<div class="cl-entry">
  <div class="cl-header">
    <span class="cl-date">{entry['date']}</span>
    <span class="cl-title">{entry.get('title', '')}</span>
    {_severity_badge(sev)}
    <span class="chevron{'  open' if is_first and not no_change else ''}">&#8964;</span>
  </div>
  <div class="cl-body{'  open' if is_first and not no_change else ''}">
    {body_content}
  </div>
</div>"""

    body = f"""
<h1>Change Log</h1>
<p class="page-meta">Every change to the Market Context (Para A) — git-diff style · Most recent first</p>
<div class="section-label">All changes</div>
{entries_html}
"""
    return _shell("Change Log", "changelog", body)


# ── Main render entry point ────────────────────────────────────────────────────

def render_all(store: dict, brief: dict, today: str, output_path: Path):
    site_path = output_path / "site"
    site_path.mkdir(parents=True, exist_ok=True)

    # Daily — always written
    (site_path / "index.html").write_text(
        render_daily(brief, store, today), encoding="utf-8"
    )
    print(f"  Rendered: index.html")

    # Para A — always written (publisher decides whether to push)
    (site_path / "para-a.html").write_text(
        render_para_a(store), encoding="utf-8"
    )
    print(f"  Rendered: para-a.html")

    # Changelog — always written
    (site_path / "changelog.html").write_text(
        render_changelog(store), encoding="utf-8"
    )
    print(f"  Rendered: changelog.html")
