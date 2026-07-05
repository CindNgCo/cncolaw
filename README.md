# Cindy Ng & Co. — Firm Website

A single-page website for **Cindy Ng & Co. (CNCO)**, a multi-practice boutique law
firm in Malaysia with offices in Langkawi and Penang.

`index.html` is **fully self-contained** — every image (logo, partner photos, office
signage) is embedded inside the file. No external files are required, so it displays
correctly anywhere: opened locally, in a preview, or hosted online.

## Structure

```
.
├── index.html        # the entire site — HTML + CSS + JS + embedded images
├── assets/           # original source images (for reference / future edits)
│   ├── logo-gold.png      # monogram (gold, transparent)
│   ├── logo-ivory.png     # monogram (ivory, transparent)
│   ├── logo.jpeg          # original logo
│   ├── cnco_background.webp# office signage wall
│   ├── quah.jpeg          # Mr. Quah Chien Chieh
│   ├── cindy.jpeg         # Ms. Cindy Ng
│   └── hee.jpeg           # Mr. Hee Ying Peng
├── .nojekyll
└── README.md
```

> Because the images are embedded in `index.html`, the `assets/` folder is optional —
> you can deploy `index.html` on its own. Keep `assets/` if you want to edit images later.

## Sections

About · Practice Areas · Our Lawyers (3 partners) · How We Can Help ·
Office signage band · Offices · Contact

## Publish on GitHub Pages

1. Create a new repository (e.g. `cncolaw`) and push these files.
2. Go to **Settings → Pages**.
3. Under **Build and deployment → Source**, choose **Deploy from a branch**.
4. Select branch `main` and folder `/ (root)`, then **Save**.
5. Your site goes live at `https://<your-username>.github.io/<repo-name>/`.

Quick push:

```bash
git init
git add .
git commit -m "Cindy Ng & Co. website"
git branch -M main
git remote add origin https://github.com/<your-username>/cncolaw.git
git push -u origin main
```

## Editing

- **Text / contact details** — edit directly in `index.html`.
- **Colours & fonts** — see the `:root` block at the top of the `<style>` section.
- **Replacing an embedded image** — easiest is to edit the source file in `assets/`,
  then re-embed. Ask and I can regenerate the self-contained file for you.

## Articles Section

The site includes a separate Articles/Insights section, kept fully independent
of the homepage.

```
content/articles/*.md      <- write or edit articles here (Markdown + front matter)
build_articles.py          <- compiles the .md files into the static pages below
articles/index.html        <- generated listing page
articles/<slug>/index.html <- one generated page per article
```

### Adding or editing an article

1. Open (or create) a file in `content/articles/`, e.g. `content/articles/my-new-article.md`.
   The filename (without `.md`) becomes the URL slug, e.g. `/articles/my-new-article/`.
2. Use this format:

   ```
   ---
   title: Your Article Title
   date: 2026-08-01
   summary: One or two sentences describing the article, shown on the listing page.
   ---

   Your article body goes here, written in Markdown.

   ## A subheading

   Paragraphs, **bold**, *italic*, [links](https://example.com), lists, and
   > blockquotes are all supported.
   ```
3. Run:
   ```
   python3 build_articles.py
   ```
   This regenerates everything inside `/articles/`.
4. Upload the changed files to GitHub (both the `.md` source file and the
   regenerated files inside `/articles/`).

If you'd rather not run the script yourself, just send Claude the Markdown
(or the changes you want) and ask it to rebuild the Articles section —
Claude will run the script and hand you the updated files to upload, exactly
as with any other change to this site.

### Why a build script, and not "just drop in a file"?

GitHub Pages serves plain static files with no server-side processing, so
there's no way for the site to automatically discover new Markdown files or
convert Markdown to HTML on the fly while also keeping good SEO (search
engines strongly prefer real, pre-rendered HTML over content loaded by
JavaScript after the page loads). `build_articles.py` is a one-step
stand-in for that: it reads every Markdown file and writes out matching,
fully static HTML pages that look identical to the rest of the site,
complete with proper `<title>`, meta description, and Article structured
data for each piece.

### The homepage is unaffected

Only two lines were added to `index.html`: an "Articles" link in the header
navigation and an "Articles" link in the footer's Navigate column. Nothing
else on the homepage was changed.


## Notes

Homepage content is drawn from the firm's official profile (as at
01.01.2026). No external case names were invented — partner write-ups
summarise their stated experience.
