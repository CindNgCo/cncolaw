#!/usr/bin/env python3
"""
build_articles.py
==================
Compiles Markdown files in /content/articles/*.md into a static Articles
section for the Cindy Ng & Co. website:

    /articles/index.html              <- listing page (all articles, newest first)
    /articles/<slug>/index.html       <- one static page per article

WHY A BUILD SCRIPT?
GitHub Pages serves plain static files with no server-side processing (unless
Jekyll is enabled, which this site deliberately does not use, via .nojekyll).
So there is no way for a browser to "list a folder" or run Markdown-to-HTML
conversion on the fly with good SEO. This script is the one-time (well,
run-it-whenever-you-change-something) step that turns your Markdown files
into real, crawlable HTML pages that look exactly like the rest of the site.

HOW TO USE
1. Add or edit a .md file in content/articles/  (see property-spa-guide.md
   for the exact format: a --- front matter block with title/date/summary,
   followed by the article body in Markdown).
2. Run:  python3 build_articles.py
3. Upload the changed files inside /articles/ (and the .md file itself, for
   safekeeping / future edits) to your GitHub repository.

That's it -- you never have to touch any HTML by hand.
"""

import os
import re
import glob
import html
import shutil
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.join(ROOT, "content", "articles")
OUT_DIR = os.path.join(ROOT, "articles")
SITE_URL = "https://www.cncolaw.my"

LOGO_DATA_URI = open(os.path.join(ROOT, "_logo.b64")).read().strip()
FAVICON_DATA_URI = open(os.path.join(ROOT, "_favicon.b64")).read().strip()

WA_PATH = (
    'M.057 24l1.687-6.163a11.867 11.867 0 0 1-1.587-5.946C.16 5.335 5.495 0 12.057 0a11.82 11.82 0 0 1 8.413 3.488 '
    '11.82 11.82 0 0 1 3.48 8.414c-.003 6.557-5.338 11.892-11.893 11.892a11.9 11.9 0 0 1-5.688-1.448L.057 24zm6.597-3.807c'
    '1.676.995 3.276 1.591 5.392 1.592 5.448 0 9.886-4.434 9.889-9.885.002-5.462-4.415-9.89-9.881-9.892-5.452 0-9.887 4.434'
    '-9.889 9.884a9.86 9.86 0 0 0 1.519 5.276l-.999 3.648 3.97-1.223zm11.387-5.464c-.074-.124-.272-.198-.57-.347-.297-.149'
    '-1.758-.868-2.031-.967-.272-.099-.47-.149-.669.149-.198.297-.768.967-.941 1.165-.173.198-.347.223-.644.074-.297-.149'
    '-1.255-.462-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.297-.347.446-.521.151'
    '-.172.2-.296.3-.495.099-.198.05-.372-.025-.521-.075-.148-.669-1.611-.916-2.206-.242-.579-.487-.501-.669-.51l-.57-.01'
    'c-.198 0-.52.074-.792.372s-1.04 1.016-1.04 2.479 1.065 2.876 1.213 3.074c.149.198 2.095 3.2 5.076 4.487.71.306 1.263'
    '.489 1.694.626.712.226 1.36.194 1.872.118.571-.085 1.758-.719 2.006-1.413.248-.695.248-1.29.173-1.414z'
)


def inline_md(text):
    text = html.escape(text, quote=False)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', text)
    return text


def markdown_to_html(body):
    blocks = re.split(r'\n\s*\n', body.strip())
    out = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        m = re.match(r'^(#{1,3})\s+(.*)', block)
        if m:
            level = min(len(m.group(1)) + 1, 4)
            out.append(f'<h{level}>{inline_md(m.group(2).strip())}</h{level}>')
            continue
        if block.startswith('>'):
            lines = [re.sub(r'^>\s?', '', l) for l in block.split('\n')]
            out.append(f'<blockquote>{inline_md(" ".join(lines))}</blockquote>')
            continue
        if re.match(r'^(-|\*)\s+', block):
            items = re.split(r'\n(?=(?:-|\*)\s+)', block)
            lis = "".join(f'<li>{inline_md(re.sub(r"^(-|\*)\s+", "", i).strip())}</li>' for i in items)
            out.append(f'<ul>{lis}</ul>')
            continue
        if re.match(r'^\d+\.\s+', block):
            items = re.split(r'\n(?=\d+\.\s+)', block)
            lis = "".join(f'<li>{inline_md(re.sub(r"^\d+\.\s+", "", i).strip())}</li>' for i in items)
            out.append(f'<ol>{lis}</ol>')
            continue
        if block == '---':
            out.append('<hr/>')
            continue
        out.append(f'<p>{inline_md(" ".join(block.split(chr(10))))}</p>')
    return "\n".join(out)


def parse_front_matter(raw):
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', raw, re.S)
    if not m:
        raise ValueError("Missing --- front matter block")
    fm_raw, body = m.group(1), m.group(2)
    fm = {}
    for line in fm_raw.split('\n'):
        if ':' not in line:
            continue
        k, v = line.split(':', 1)
        fm[k.strip()] = v.strip().strip('"\'')
    return fm, body


def load_articles():
    articles = []
    for path in sorted(glob.glob(os.path.join(CONTENT_DIR, "*.md"))):
        slug = os.path.splitext(os.path.basename(path))[0]
        raw = open(path, encoding="utf-8").read()
        fm, body = parse_front_matter(raw)
        date_obj = datetime.strptime(fm["date"].strip(), "%Y-%m-%d")
        word_count = len(re.findall(r'\w+', body))
        reading_min = max(1, round(word_count / 200))
        articles.append({
            "slug": slug,
            "title": fm["title"].strip(),
            "date": date_obj,
            "date_display": date_obj.strftime("%-d %B %Y"),
            "date_iso": date_obj.strftime("%Y-%m-%d"),
            "summary": fm["summary"].strip(),
            "body_html": markdown_to_html(body),
            "reading_min": reading_min,
        })
    articles.sort(key=lambda a: a["date"], reverse=True)
    return articles


SHARED_CSS = """
:root{
  --paper:#fcfbf7;--paper-2:#ffffff;--paper-3:#f3ecd9;
  --ink:#0c0c0e;--black:#060607;
  --parchment:#182a4e;--ivory:#2c3550;
  --muted:#55607c;--muted-2:#6d7690;
  --gold:#95660a;--gold-deep:#7a5306;--gold-soft:#8c5f08;
  --line:rgba(149,102,10,.36);--line-soft:rgba(149,102,10,.16);
  --maxw:1180px;--radius:4px;
  --ease:cubic-bezier(.22,.61,.36,1);
  --display:"Fraunces",Georgia,serif;
  --body:"Archivo",system-ui,-apple-system,sans-serif;
}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{background:var(--paper);color:var(--ivory);font-family:var(--body);line-height:1.65;-webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration:none}
img{display:block;max-width:100%}
.wrap{max-width:var(--maxw);margin:0 auto;padding:0 28px}
h1,h2,h3,h4{font-family:var(--display);font-weight:400;line-height:1.12;letter-spacing:-.01em;color:var(--parchment)}
.section-pad{padding:clamp(48px,8vw,96px) 0}
.eyebrow{font-family:var(--body);font-size:.72rem;font-weight:600;letter-spacing:.32em;text-transform:uppercase;color:var(--gold)}
.eyebrow .mark{color:var(--muted-2);font-weight:500}
.skip-link{position:fixed;top:-64px;left:16px;z-index:120;background:var(--parchment);color:#fdfaf3;padding:11px 18px;border-radius:6px;font-size:.82rem;transition:top .2s ease}
.skip-link:focus{top:16px}
a:focus-visible,button:focus-visible{outline:2px solid var(--gold-deep);outline-offset:3px;border-radius:4px}

header{position:fixed;top:0;left:0;right:0;z-index:60;backdrop-filter:blur(10px);background:rgba(252,251,247,.92);border-bottom:1px solid var(--line-soft)}
.nav{display:flex;align-items:center;justify-content:space-between;height:74px}
.brand{display:flex;align-items:center;gap:13px}
.brand img{height:34px;width:auto}
.brand-text{display:flex;flex-direction:column;line-height:1}
.brand-text .name{font-family:var(--display);font-size:1.06rem;color:var(--parchment)}
.brand-text .sub{font-size:.6rem;letter-spacing:.34em;text-transform:uppercase;color:var(--muted);margin-top:5px}
.nav-links{display:flex;align-items:center;gap:34px}
.nav-links a{font-size:.78rem;letter-spacing:.13em;text-transform:uppercase;color:var(--muted);font-weight:500}
.nav-links a:hover,.nav-links a.active{color:var(--parchment)}
.nav-cta{border:1px solid var(--line);color:var(--gold-soft);padding:9px 18px;border-radius:var(--radius);font-size:.72rem;letter-spacing:.16em;text-transform:uppercase}
.nav-cta:hover{background:var(--gold);color:#fdfaf3;border-color:var(--gold)}
.menu-btn{display:none;background:none;border:0;cursor:pointer;padding:8px;color:var(--ivory)}
@media(max-width:680px){
  .nav-links{position:fixed;inset:74px 0 auto 0;flex-direction:column;align-items:stretch;background:rgba(252,251,247,.98);border-bottom:1px solid var(--line);max-height:0;overflow:hidden;transition:max-height .35s ease}
  .nav-links.open{max-height:420px}
  .nav-links a{padding:16px 28px;border-top:1px solid var(--line-soft)}
  .nav-links .nav-cta{margin:16px 28px;text-align:center}
  .menu-btn{display:block}
}

.btn{display:inline-flex;align-items:center;gap:10px;font-size:.76rem;letter-spacing:.16em;text-transform:uppercase;font-weight:600;padding:14px 26px;border-radius:var(--radius)}
.btn-primary{background:linear-gradient(135deg,#c2921b,#8a5d07);color:#fdfaf3}
.btn-primary:hover{background:linear-gradient(135deg,#d4a52c,#95660a)}
.btn-ghost{border:1px solid rgba(24,42,78,.35);color:#182a4e}
.btn-ghost:hover{background:#182a4e;border-color:#182a4e;color:#fff}

.page-hero{padding:150px 0 56px;background:linear-gradient(180deg,var(--paper-3),var(--paper))}
.page-hero .eyebrow{display:block;margin-bottom:16px}
.page-hero h1{font-size:clamp(2.1rem,4.6vw,3.2rem)}
.page-hero p{color:var(--muted);margin-top:16px;max-width:60ch}
.breadcrumb{font-size:.78rem;color:var(--muted-2);margin-bottom:18px}
.breadcrumb a{color:var(--gold-deep)}
.breadcrumb a:hover{color:var(--gold)}

.article-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:1px;background:var(--line-soft);border:1px solid var(--line-soft);margin-top:8px}
.acard{background:var(--paper-2);padding:34px 32px;display:flex;flex-direction:column;transition:background .3s var(--ease)}
.acard:hover{background:#fff;box-shadow:0 22px 50px -34px rgba(24,42,78,.3)}
.acard .adate{font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;color:var(--gold-deep);font-weight:600}
.acard h2{font-size:1.4rem;margin:14px 0 12px;line-height:1.25}
.acard p{color:var(--muted);font-size:.92rem;flex:1}
.acard .aread{margin-top:20px;font-size:.74rem;letter-spacing:.1em;text-transform:uppercase;color:var(--gold);font-weight:600}
.empty-state{padding:60px 32px;text-align:center;color:var(--muted);background:var(--paper-2);border:1px solid var(--line-soft)}
@media(max-width:820px){.article-grid{grid-template-columns:1fr}}

.article-body{max-width:720px;margin:0 auto;padding:0 28px}
.article-meta{display:flex;gap:16px;flex-wrap:wrap;font-size:.78rem;letter-spacing:.08em;text-transform:uppercase;color:var(--muted-2);margin:18px 0 30px}
.article-meta strong{color:var(--gold-deep)}
.prose{font-size:1.05rem;color:#333c58;line-height:1.85}
.prose h2{font-size:1.55rem;margin:40px 0 16px;color:var(--parchment)}
.prose h3{font-size:1.25rem;margin:32px 0 14px;color:var(--parchment)}
.prose p{margin-bottom:20px}
.prose ul,.prose ol{margin:0 0 20px 22px}
.prose li{margin-bottom:9px}
.prose blockquote{border-left:3px solid var(--gold);padding:6px 22px;margin:28px 0;font-family:var(--display);font-style:italic;font-size:1.15rem;color:var(--parchment)}
.prose a{color:var(--gold-deep);border-bottom:1px solid var(--line)}
.prose a:hover{color:var(--gold)}
.prose hr{border:0;border-top:1px solid var(--line-soft);margin:36px 0}
.prose em{color:var(--muted)}
.article-cta{margin-top:48px;padding:32px;background:var(--paper-3);border-radius:var(--radius);text-align:center}
.article-cta h3{font-size:1.3rem;margin-bottom:10px}
.article-cta p{color:var(--muted);margin-bottom:20px}
.back-link{display:inline-flex;align-items:center;gap:8px;margin:40px 0 8px;font-size:.78rem;letter-spacing:.12em;text-transform:uppercase;color:var(--gold-deep);font-weight:600}
.back-link:hover{color:var(--gold)}

footer{background:var(--paper-3);padding:56px 0 32px;margin-top:64px}
.foot-top{display:grid;grid-template-columns:1.4fr 1fr 1fr;gap:40px;align-items:start}
.foot-brand img{height:38px;margin-bottom:16px}
.foot-brand .fn{font-family:var(--display);font-size:1.3rem;color:var(--parchment)}
.foot-brand p{color:var(--muted-2);font-size:.86rem;margin-top:10px;max-width:38ch}
.foot-col h4{font-size:.72rem;letter-spacing:.2em;text-transform:uppercase;color:var(--gold);font-weight:600;margin-bottom:16px}
.foot-col a,.foot-col p{display:block;color:var(--muted);font-size:.88rem;margin-bottom:10px}
.foot-col a:hover{color:var(--gold-soft)}
.foot-bottom{margin-top:40px;padding-top:20px;border-top:1px solid var(--line-soft);display:flex;justify-content:space-between;flex-wrap:wrap;gap:12px;font-size:.74rem;color:var(--muted-2)}
@media(max-width:820px){.foot-top{grid-template-columns:1fr 1fr}.foot-brand{grid-column:1/-1}}
@media(max-width:600px){.foot-top{grid-template-columns:1fr}}

.wa-widget{position:fixed;right:22px;bottom:22px;z-index:90;display:flex;flex-direction:column;align-items:flex-end;gap:12px}
.wa-fab{width:56px;height:56px;border-radius:50%;background:#1faa53;color:#fff;border:0;cursor:pointer;display:flex;align-items:center;justify-content:center;box-shadow:0 14px 32px -12px rgba(24,140,69,.6)}
.wa-fab svg{width:28px;height:28px}
.wa-pop{background:var(--paper-2);border:1px solid var(--line);border-radius:12px;padding:16px;box-shadow:0 26px 60px -30px rgba(50,38,14,.5);min-width:238px}
.wa-pop-t{font-size:.7rem;letter-spacing:.12em;text-transform:uppercase;color:var(--muted-2);font-weight:600;margin-bottom:4px}
.wa-pop a{display:block;padding:11px 13px;border:1px solid var(--line-soft);border-radius:8px;margin-top:9px;font-size:.9rem;color:var(--ivory)}
.wa-pop a:hover{background:var(--gold);color:#fff;border-color:var(--gold)}
"""

WA_WIDGET_HTML = f"""
<div class="wa-widget">
  <div class="wa-pop" id="waPop" role="dialog" aria-label="Chat with an office on WhatsApp" hidden>
    <p class="wa-pop-t">Chat on WhatsApp</p>
    <a href="https://wa.me/6049611745" target="_blank" rel="noopener">Langkawi &middot; 04-961 1745</a>
    <a href="https://wa.me/6045108411" target="_blank" rel="noopener">Penang &middot; 04-510 8411</a>
  </div>
  <button class="wa-fab" id="waFab" aria-expanded="false" aria-controls="waPop" aria-label="Chat on WhatsApp">
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="{WA_PATH}"/></svg>
  </button>
</div>
"""

SHARED_JS = """
const waFab = document.getElementById('waFab');
const waPop = document.getElementById('waPop');
function waToggle(open){
  const willOpen = open !== undefined ? open : waPop.hasAttribute('hidden');
  if (willOpen) waPop.removeAttribute('hidden'); else waPop.setAttribute('hidden','');
  waFab.setAttribute('aria-expanded', willOpen);
}
waFab.addEventListener('click', (e) => { e.stopPropagation(); waToggle(); });
document.addEventListener('click', (e) => { if (!waPop.hasAttribute('hidden') && !waPop.contains(e.target) && e.target !== waFab) waToggle(false); });
document.addEventListener('keydown', (e) => { if (e.key === 'Escape') waToggle(false); });
const menuBtn = document.getElementById('menu-btn');
const navLinks = document.getElementById('nav-links');
if (menuBtn) {
  menuBtn.addEventListener('click', () => {
    const open = navLinks.classList.toggle('open');
    menuBtn.setAttribute('aria-expanded', open);
  });
}
"""


def header_html(active):
    def link(href, label, key):
        cls = ' class="active"' if key == active else ''
        return f'<a href="{href}"{cls}>{label}</a>'
    return f"""
<header id="site-header">
  <div class="wrap">
    <nav class="nav" aria-label="Primary">
      <a class="brand" href="/" aria-label="Cindy Ng & Co. home">
        <img src="{LOGO_DATA_URI}" alt="" />
        <span class="brand-text">
          <span class="name">Cindy Ng &amp; Co.</span>
          <span class="sub">Advocates &amp; Solicitors</span>
        </span>
      </a>
      <div class="nav-links" id="nav-links">
        {link('/#about', 'About', 'about')}
        {link('/#practice', 'Practice', 'practice')}
        {link('/#lawyers', 'Our Lawyers', 'lawyers')}
        {link('/#offices', 'Offices', 'offices')}
        {link('/articles/', 'Articles', 'articles')}
        <a class="nav-cta" href="/#enquiry">Book a Consultation</a>
      </div>
      <button class="menu-btn" id="menu-btn" aria-label="Open menu" aria-expanded="false" aria-controls="nav-links">
        <svg width="26" height="26" viewBox="0 0 26 26" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M3 7h20M3 13h20M3 19h20"/></svg>
      </button>
    </nav>
  </div>
</header>
"""


def footer_html():
    return f"""
<footer>
  <div class="wrap">
    <div class="foot-top">
      <div class="foot-brand">
        <img src="{LOGO_DATA_URI}" alt="Cindy Ng & Co. monogram" />
        <div class="fn">Cindy Ng &amp; Co.</div>
        <p>A multi-practice boutique law firm in Malaysia, committed to high-quality, client-focused legal services since 2023.</p>
      </div>
      <div class="foot-col">
        <h4>Navigate</h4>
        <a href="/#about">About</a>
        <a href="/#practice">Practice Areas</a>
        <a href="/#lawyers">Our Lawyers</a>
        <a href="/#offices">Offices</a>
        <a href="/articles/">Articles</a>
        <a href="/#enquiry">Book a Consultation</a>
      </div>
      <div class="foot-col">
        <h4>Contact</h4>
        <p>Langkawi &middot; <a href="tel:+6049611745">04-961 1745</a></p>
        <p>Penang &middot; <a href="tel:+6045108411">04-510 8411</a></p>
        <a href="mailto:cindylgk@cncolaw.my">cindylgk@cncolaw.my</a>
        <a href="mailto:cindypg@cncolaw.my">cindypg@cncolaw.my</a>
      </div>
    </div>
    <div class="foot-bottom">
      <span>&copy; 2026 Cindy Ng &amp; Co. (CNCO) &middot; Advocates &amp; Solicitors, Malaysia</span>
      <span>Established 23 January 2023</span>
    </div>
  </div>
</footer>
"""


def page_shell(title, description, canonical_path, body_inner, active_nav, extra_head=""):
    canonical = f"{SITE_URL}{canonical_path}"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}" />
<link rel="canonical" href="{canonical}" />
<meta name="theme-color" content="#fcfbf7" />
<meta property="og:type" content="article" />
<meta property="og:site_name" content="Cindy Ng &amp; Co." />
<meta property="og:title" content="{html.escape(title)}" />
<meta property="og:description" content="{html.escape(description)}" />
<meta property="og:url" content="{canonical}" />
<meta property="og:image" content="{SITE_URL}/og-image.jpg" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{html.escape(title)}" />
<meta name="twitter:description" content="{html.escape(description)}" />
<link rel="icon" type="image/png" href="{FAVICON_DATA_URI}" />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,500;0,9..144,600;1,9..144,400;1,9..144,500&family=Archivo:wght@400;500;600&display=swap" rel="stylesheet" />
<style>{SHARED_CSS}</style>
{extra_head}
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
{header_html(active_nav)}
<main id="main">
{body_inner}
</main>
{footer_html()}
{WA_WIDGET_HTML}
<script>{SHARED_JS}</script>
</body>
</html>"""


def build_listing_page(articles):
    if articles:
        cards = "\n".join(f"""
      <a class="acard" href="/articles/{a['slug']}/">
        <span class="adate">{a['date_display']}</span>
        <h2>{html.escape(a['title'])}</h2>
        <p>{html.escape(a['summary'])}</p>
        <span class="aread">Read Article &rarr;</span>
      </a>""" for a in articles)
        grid = f'<div class="article-grid">{cards}</div>'
    else:
        grid = '<div class="empty-state">No articles published yet -- check back soon.</div>'

    body = f"""
<section class="page-hero">
  <div class="wrap">
    <span class="eyebrow">Insights</span>
    <h1>Articles &amp; Legal Updates</h1>
    <p>Practical, plain-English guides from Cindy Ng &amp; Co. on property, banking, family, and general legal matters in Malaysia.</p>
  </div>
</section>
<section class="section-pad">
  <div class="wrap">
    {grid}
  </div>
</section>
"""
    html_out = page_shell(
        title="Articles & Legal Updates | Cindy Ng & Co.",
        description="Practical legal articles and updates from Cindy Ng & Co., a boutique law firm in Langkawi and Penang, Malaysia.",
        canonical_path="/articles/",
        body_inner=body,
        active_nav="articles",
    )
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_out)


def build_article_page(article):
    desc = html.escape(article['summary']).replace('"', '&quot;')
    title_esc = html.escape(article['title']).replace('"', '&quot;')
    jsonld = f"""<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "{title_esc}",
  "datePublished": "{article['date_iso']}",
  "description": "{desc}",
  "author": {{"@type": "Organization", "name": "Cindy Ng & Co."}},
  "publisher": {{"@type": "Organization", "name": "Cindy Ng & Co."}},
  "mainEntityOfPage": "{SITE_URL}/articles/{article['slug']}/"
}}
</script>"""

    body = f"""
<section class="page-hero" style="padding-bottom:0">
  <div class="wrap article-body" style="max-width:720px">
    <p class="breadcrumb"><a href="/articles/">Articles</a> / {html.escape(article['title'])}</p>
    <span class="eyebrow">Insights</span>
    <h1 style="margin-top:14px">{html.escape(article['title'])}</h1>
    <div class="article-meta">
      <span>{article['date_display']}</span>
      <span><strong>&middot;</strong> {article['reading_min']} min read</span>
    </div>
  </div>
</section>
<section class="section-pad" style="padding-top:0">
  <div class="article-body">
    <div class="prose">
      {article['body_html']}
    </div>
    <div class="article-cta">
      <h3>Need advice on this?</h3>
      <p>Our lawyers are happy to discuss your specific situation.</p>
      <a class="btn btn-primary" href="/#enquiry">Book a Consultation</a>
    </div>
    <a class="back-link" href="/articles/">&larr; Back to Articles</a>
  </div>
</section>
"""
    html_out = page_shell(
        title=f"{article['title']} | Cindy Ng & Co.",
        description=article['summary'],
        canonical_path=f"/articles/{article['slug']}/",
        body_inner=body,
        active_nav="articles",
        extra_head=jsonld,
    )
    out_folder = os.path.join(OUT_DIR, article['slug'])
    os.makedirs(out_folder, exist_ok=True)
    with open(os.path.join(out_folder, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_out)


def main():
    articles = load_articles()
    if os.path.isdir(OUT_DIR):
        shutil.rmtree(OUT_DIR)
    os.makedirs(OUT_DIR, exist_ok=True)
    build_listing_page(articles)
    for a in articles:
        build_article_page(a)
    print(f"Built {len(articles)} article page(s) + listing page into /articles/")
    for a in articles:
        print(f"  - /articles/{a['slug']}/   ({a['date_display']}) {a['title']}")


if __name__ == "__main__":
    main()
