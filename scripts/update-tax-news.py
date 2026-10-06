#!/usr/bin/env python3
import html, re
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup

INCOME_URL = "https://www.incometax.gov.in/iec/foportal/latest-news"
CBIC_URL = "https://cbic-gst.gov.in/tickers.html"
OUT = "tax-updates.html"

def fetch(url):
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 KJ-Co-Tax-Updater/1.0"})
    with urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "ignore")

def clean(s):
    return re.sub(r"\\s+", " ", BeautifulSoup(s, "html.parser").get_text(" ", strip=True)).strip()

def income_items():
    soup = BeautifulSoup(fetch(INCOME_URL), "html.parser")
    text = soup.get_text("\n", strip=True)
    pattern = re.compile(r"(\\d{2}-[A-Za-z]{3}-\\d{4})\\s+(.*?)(?=\\d{2}-[A-Za-z]{3}-\\d{4}|$)", re.S)
    items=[]
    for m in pattern.finditer(text):
        date, desc = m.groups()
        desc = clean(desc)
        if len(desc) < 30 or "Latest News" in desc:
            continue
        desc = desc[:700]
        items.append({"date": date, "category":"Income Tax", "title":desc.split(". ")[0][:150], "summary":desc, "url":INCOME_URL})
    seen=set(); out=[]
    for x in items:
        k=(x["date"],x["summary"])
        if k not in seen:
            seen.add(k); out.append(x)
    return out[:12]

def cbic_items():
    soup = BeautifulSoup(fetch(CBIC_URL), "html.parser")
    text = soup.get_text("\n", strip=True)
    chunks = re.findall(r"“?\\s*([^“”\\n]+?\\d{2}\\.\\d{2}\\.2026[^“”\\n]*)[”]?", text)
    items=[]
    for desc in chunks:
        desc=clean(desc)
        if len(desc)<35: continue
        m=re.search(r"(\\d{2}\\.\\d{2}\\.2026)", desc)
        date=m.group(1) if m else "2026"
        items.append({"date":date, "category":"GST / CBIC", "title":desc[:150], "summary":desc, "url":CBIC_URL})
    seen=set(); out=[]
    for x in items:
        k=x["summary"]
        if k not in seen:
            seen.add(k); out.append(x)
    return out[:12]

def esc(s): return html.escape(s, quote=True)

def summary_lines(x):
    category = x["category"]
    subject = x["title"].strip()
    source = x["url"]
    if category == "Income Tax":
        return [
            f"CBDT / Income Tax Department update dated {x['date']}.",
            f"The update concerns: {subject}.",
            "Taxpayers should identify whether the change applies to their facts.",
            "The applicable notification, circular, rule or portal instruction should be reviewed.",
            "Relevant forms, reporting fields and filing procedures should be checked.",
            "Existing compliance checklists should be updated where required.",
            "Supporting documents and working papers should be retained.",
            "Any applicable effective date or transition period should be confirmed.",
            "Professionals should reconcile the change with the taxpayer's existing position.",
            "Action: verify the official source before taking a compliance action.",
        ]
    return [
        f"GSTN / CBIC update dated {x['date']}.",
        f"The update concerns: {subject}.",
        "Taxpayers should identify whether the change applies to their GST activities.",
        "The applicable advisory, notification or portal instruction should be reviewed.",
        "Relevant return, registration, invoice, e-way bill or appeal procedures should be checked.",
        "ERP, GSP and portal configurations should be updated where necessary.",
        "Supporting documents and reconciliation workings should be retained.",
        "Any implementation date or transition period should be confirmed.",
        "Tax and IT teams should coordinate where the change affects systems.",
        "Action: verify the official source before taking a compliance action.",
    ]

def card(x):
    lines = "".join(f"<li>{esc(line)}</li>" for line in summary_lines(x))
    return f'''<article class="update-card" data-category="{esc(x["category"])}">
      <div class="update-meta"><span>{esc(x["category"])}</span><time>{esc(x["date"])}</time></div>
      <h3>{esc(x["title"])}</h3>
      <p>{esc(x["summary"])}</p>
      <details><summary>Read 10-line professional summary</summary><ol>{lines}</ol></details>
      <a href="{esc(x["url"])}" target="_blank" rel="noopener">View official source ↗</a>
    </article>'''

def main():
    items = income_items() + cbic_items()
    now = datetime.now(timezone.utc).astimezone()
    cards = "\n".join(card(x) for x in items)
    generated = now.strftime("%d %b %Y, %I:%M %p %Z")
    page=f'''<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Latest GST and Income Tax updates compiled from official Indian government sources by K&J Co.">
<title>GST & Income Tax Updates | K&J Co</title>
<link rel="stylesheet" href="style.css?v=tax-auto-1">
<style>
.tax-hero{{background:var(--dark);color:#fff;padding:90px 0 75px}}.tax-hero h1{{font:500 clamp(44px,6vw,70px)/1.05 Georgia,serif;margin:0 0 20px;letter-spacing:-2px}}.tax-hero h1 em{{color:var(--accent2);font-style:normal}}.tax-hero p{{max-width:720px;color:#b9c3bd}}.tax-status{{margin-top:28px;font-size:11px;letter-spacing:1.4px;color:var(--accent2)}}.tax-controls{{display:flex;gap:10px;flex-wrap:wrap;margin:0 0 35px}}.tax-filter{{border:1px solid var(--line);background:var(--paper);padding:10px 16px;font-size:11px;cursor:pointer;color:var(--ink)}}.tax-filter.active,.tax-filter:hover{{background:var(--ink);color:#fff;border-color:var(--ink)}}.updates-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:18px}}.update-card{{border:1px solid var(--line);background:#fff;padding:27px;display:flex;flex-direction:column;min-height:270px}}.update-meta{{display:flex;justify-content:space-between;gap:15px;font-size:9px;letter-spacing:1.3px;text-transform:uppercase;color:var(--accent);font-weight:800}}.update-meta time{{color:var(--muted)}}.update-card h3{{font:500 22px/1.25 Georgia,serif;margin:18px 0 12px}}.update-card p{{font-size:12px;color:var(--muted);margin:0 0 20px}}.update-card a{{margin-top:auto;color:var(--ink);font-size:11px;font-weight:700;text-decoration:none}}.update-card a:hover{{color:var(--accent)}}.source-box{{background:var(--cream);border:1px solid var(--line);padding:28px;margin-top:40px}}.source-box h3{{font:500 25px Georgia,serif;margin:0 0 10px}}.source-box p{{color:var(--muted);font-size:12px}}.source-links{{display:flex;gap:12px;flex-wrap:wrap}}.source-links a{{border:1px solid var(--line);padding:10px 13px;color:var(--ink);text-decoration:none;font-size:11px;background:var(--paper)}}.disclaimer{{font-size:11px;color:var(--muted);margin-top:25px}}@media(max-width:650px){{.updates-grid{{grid-template-columns:1fr}}.update-card{{min-height:0}}}}
</style></head><body>
<div class="topbar"><div class="container topbar-inner"><span>CHARTERED ACCOUNTANTS · HYDERABAD & NELLORE</span><a href="tel:+918712313183">+91 87123 13183</a></div></div>
<header class="nav"><div class="container nav-inner"><a class="logo" href="index.html"><span>K&J</span> Co <small>CHARTERED ACCOUNTANTS</small></a>
<nav aria-label="Primary navigation"><a href="index.html#about">About</a><a href="index.html#services">Services</a><a href="index.html#partners">Partners</a><a href="tax-updates.html">Tax Updates</a><a href="index.html#contact">Contact</a></nav>
<a class="nav-cta" href="index.html#contact">Book a Consultation <span>↗</span></a></div></header>
<section class="tax-hero"><div class="container"><p class="eyebrow">OFFICIAL TAX NEWS · INDIA</p><h1>GST & Income Tax <em>Updates.</em></h1><p>Latest notices, advisories and taxpayer announcements sourced from official government portals. The page is refreshed automatically by K&J Co.</p><div class="tax-status">LAST AUTOMATIC UPDATE · {esc(generated)}</div></div></section>
<main class="section"><div class="container"><div class="tax-controls"><button class="tax-filter active" data-filter="all">ALL UPDATES</button><button class="tax-filter" data-filter="Income Tax">INCOME TAX</button><button class="tax-filter" data-filter="GST / CBIC">GST / CBIC</button></div>
<div class="updates-grid">{cards}</div>
<div class="source-box"><h3>Official sources</h3><p>Always verify the applicable notification, circular, rule, act and effective date on the official portal before relying on an update.</p><div class="source-links"><a href="https://www.incometax.gov.in/iec/foportal/latest-news" target="_blank" rel="noopener">Income Tax · Latest News ↗</a><a href="https://www.gst.gov.in/" target="_blank" rel="noopener">GST Portal ↗</a><a href="https://tutorial.gst.gov.in/" target="_blank" rel="noopener">GSTN Tutorials ↗</a><a href="https://cbic-gst.gov.in/tickers.html" target="_blank" rel="noopener">CBIC GST Tickers ↗</a></div><p class="disclaimer">This page is for general information only and is not a substitute for professional advice. K&J Co is not responsible for decisions taken solely on the basis of this page.</p></div>
</div></main>
<footer><div class="container footer-grid"><div><div class="logo"><span>K&J</span> Co <small>CHARTERED ACCOUNTANTS</small></div><p>Professionalism · Integrity · Insight</p></div><div class="footer-links"><a href="index.html">Home</a><a href="tax-updates.html">Tax Updates</a><a href="index.html#contact">Contact</a></div><p class="copyright">© 2026 K&J Co. Chartered Accountants.<br>All rights reserved.</p></div></footer>
<script>document.querySelectorAll('.tax-filter').forEach(b=>b.addEventListener('click',()=>{{document.querySelectorAll('.tax-filter').forEach(x=>x.classList.remove('active'));b.classList.add('active');const f=b.dataset.filter;document.querySelectorAll('.update-card').forEach(c=>c.style.display=(f==='all'||c.dataset.category===f)?'flex':'none')}}));</script>
</body></html>'''
    with open(OUT,"w",encoding="utf-8") as f: f.write(page)

if __name__=="__main__":
    main()
