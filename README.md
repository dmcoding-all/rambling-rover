# Rambling Rover — Site Documentation

## Stack at a glance

| Layer | Tool | Cost |
|-------|------|------|
| Static site generator | [Hugo](https://gohugo.io) | Free |
| Hosting & CI/CD | [GitHub Pages](https://pages.github.com) + GitHub Actions | Free |
| Image hosting | [Cloudinary](https://cloudinary.com) | Free tier (25GB) |
| Map | [Leaflet.js](https://leafletjs.com) + CartoDB tiles | Free |
| Domain | `yourusername.github.io/rambling-rover` (or custom domain) | Free |

**Why Hugo + GitHub Pages?**
Hugo builds your entire site into static HTML files in under 1 second — no database, no server, nothing to hack or maintain. GitHub Pages hosts those files for free. You write posts in plain Markdown, push to GitHub, and the site updates automatically in ~90 seconds.

---

## Part A — First-time setup (do this once)

### 1. Install Hugo

**Mac:**
```bash
brew install hugo
```

**Windows:**
Download the `.zip` from https://github.com/gohugoio/hugo/releases
→ Get the `hugo_extended_X.X.X_windows-amd64.zip` version
→ Extract `hugo.exe` and add it to your PATH (search "Edit system environment variables" → Environment Variables → Path → New → paste the folder)

**Verify:**
```bash
hugo version
# should print: hugo v0.128.x extended ...
```

---

### 2. Install Git (if not already)

Download from https://git-scm.com/downloads and install with default settings.

Verify:
```bash
git --version
```

Configure your identity (one-time):
```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

---

### 3. Create your GitHub repository

1. Go to https://github.com and log in
2. Click **+** → **New repository**
3. Name it: `rambling-rover`
4. Set to **Public** (required for free GitHub Pages)
5. Do NOT add a README or .gitignore (you have those already)
6. Click **Create repository**

---

### 4. Connect this folder to GitHub

Open a terminal in the `rambling-rover/` folder (in VSCode: Terminal → New Terminal):

```bash
git init
git add .
git commit -m "Initial site setup"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/rambling-rover.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your actual GitHub username.

---

### 5. Enable GitHub Pages

1. Go to your repo on GitHub → **Settings** → **Pages** (left sidebar)
2. Under "Build and deployment" → Source → select **GitHub Actions**
3. That's it — the workflow in `.github/workflows/deploy.yml` handles everything

Your site will be live at:
`https://YOUR_USERNAME.github.io/rambling-rover/`

⚠ First deployment takes 2–3 minutes. After that, every push deploys in ~90 seconds.

---

### 6. Update `hugo.yaml` with your GitHub username

Open `hugo.yaml` and change line 1:
```yaml
baseURL: "https://YOUR_USERNAME.github.io/rambling-rover/"
```

---

### 7. Set up Cloudinary (image hosting)

1. Go to https://cloudinary.com and create a free account
2. From your Dashboard, note your **Cloud name**
3. Open `hugo.yaml` and update:
```yaml
params:
  cloudinary_cloud: "your_actual_cloud_name"
  cloudinary_base: "https://res.cloudinary.com/your_actual_cloud_name/image/upload"
```

**Cloudinary folder structure to create** (in Cloudinary → Media Library → Create folder):
```
photos/
  edinburgh/
  appalachian-trail/
  buenos-aires/
  ... (one per location)
posts/
  2018/
  2019/
  2023/
locations/
  (cover images for each location card)
```

---

## Part B — Migrating your WordPress content

### Step 1: Run the alcohol removal script

Before anything else, clean the posts:

```bash
pip install python-slugify pyyaml

# Dry run first (see what will change):
python scripts/remove_alcohol.py --posts /path/to/your/posts_md/ --dry-run

# Apply (writes cleaned files, creates .bak backups):
python scripts/remove_alcohol.py --posts /path/to/your/posts_md/
```

After running, search your posts folder for `[REVIEW: alcohol ref]` — these are lines the script flagged for manual review that it couldn't safely auto-rewrite.

---

### Step 2: Run the WordPress migration script

```bash
python scripts/migrate_wordpress.py \
    --xml   /path/to/wordpress-export.xml \
    --posts /path/to/your/posts_md/ \
    --out   content/posts/
```

This will:
- Read metadata from your WordPress XML (dates, slugs, categories)
- Read body content from your existing .md files (already clean markdown)
- Merge them into `content/posts/` with Hugo-compatible frontmatter
- Skip the 7 duplicate originals (keeps the better `-2` versions)
- Flag any posts with alcohol references in the frontmatter comments

After migration, open a few posts in VSCode and check:
- `locations:` is set correctly (see note below)
- `cover:` is empty — you'll fill this in after uploading images
- `description:` is empty — worth filling in for SEO

**Fixing locations for AT posts:**
The AT posts don't have state-level categories, so the script assigns them all to `appalachian-trail-georgia`. Open each AT post and set the correct location:

```yaml
# AT posts — use one of these location ids:
locations:
  - appalachian-trail-georgia     # Days 1-5 (Georgia)
  - appalachian-trail-pennsylvania  # Rocksylvania posts
  - appalachian-trail-new-jersey
  - appalachian-trail-new-york
  - appalachian-trail-vermont
  - appalachian-trail-new-hampshire  # White Mountains posts
  - appalachian-trail-maine        # 100-Mile Wilderness, Katahdin
```

---

### Step 3: Compress and upload images

**Compress your downloaded WordPress images:**
```bash
pip install Pillow tqdm cloudinary

python scripts/compress_and_upload.py \
    --input  /path/to/downloaded/wp-images/ \
    --output /path/to/compressed/output/ \
    --compress-only
```

Check the compressed folder — sizes should be 100–400KB for most photos.

**Upload to Cloudinary:**
```bash
python scripts/compress_and_upload.py \
    --input  /path/to/downloaded/wp-images/ \
    --output /path/to/compressed/output/ \
    --cloud  your_cloud_name \
    --key    your_api_key \
    --secret your_api_secret \
    --prefix posts/
```

Your Cloudinary API key and secret are in the Cloudinary Dashboard → Settings → API Keys.
**Never commit these to GitHub.** Use environment variables instead:

```bash
export CLOUDINARY_CLOUD_NAME=your_cloud
export CLOUDINARY_API_KEY=your_key
export CLOUDINARY_API_SECRET=your_secret

python scripts/compress_and_upload.py \
    --input  /path/to/images/ \
    --output /path/to/compressed/ \
    --prefix posts/
```

**Update post URLs after uploading:**
```bash
python scripts/compress_and_upload.py \
    --update-posts content/posts/ \
    --cloud your_cloud_name
```

---

### Step 4: Add cover images to your posts

For each post, find the image you uploaded to Cloudinary, and add the path to `cover:`:

```yaml
# In your post frontmatter:
cover: "https://res.cloudinary.com/your_cloud/image/upload/w_1400,q_auto,f_auto/posts/2023/vermud-hero.jpg"
```

Hugo uses this for: the post card on the blog list, the hero image on the single post page, and the Open Graph preview image.

---

### Step 5: Create location pages

For each location in `data/locations.yaml`, create a matching file in `content/locations/`:

```bash
hugo new locations/edinburgh.md
hugo new locations/buenos-aires.md
# etc.
```

Then open each file and fill in the `recommendations:` block. See `content/locations/edinburgh.md` as a template.

---

### Step 6: Add your photos

For each location, create a photo gallery file:

```bash
hugo new photos/edinburgh-2018.md
```

Edit the file and add each photo:
```yaml
location: edinburgh
photos:
  - src: "photos/edinburgh/arthurs-seat.jpg"
    caption: "Arthur's Seat at sunrise"
  - src: "photos/edinburgh/royal-mile.jpg"
    caption: "Old Town from Calton Hill"
```

The `src` is the Cloudinary path **after `/upload/`** — just the folder and filename.

---

### Step 7: Preview locally

```bash
hugo server
```

Open http://localhost:1313 — the site auto-refreshes as you make changes.

---

### Step 8: Deploy

```bash
git add .
git commit -m "Add migrated posts and photos"
git push
```

GitHub Actions will build and deploy automatically. Watch progress at:
`https://github.com/YOUR_USERNAME/rambling-rover/actions`

---

## Part C — Adding new content going forward

### Adding a new blog post

```bash
# 1. Create the file
hugo new posts/2024-03-15-your-post-title.md

# 2. Open in VSCode and edit
code content/posts/2024-03-15-your-post-title.md
```

Fill in the frontmatter:
```yaml
title: "Your Post Title"
date: 2024-03-15
locations:
  - edinburgh        # must match an id in data/locations.yaml
categories:
  - hiking
cover: "https://res.cloudinary.com/..."
description: "One or two sentences for SEO."
draft: false
```

Write your post in Markdown below the `---`.

When ready:
```bash
git add content/posts/2024-03-15-your-post-title.md
git commit -m "Add post: Your Post Title"
git push
```

**Markdown quick reference:**
```markdown
## Section heading

Normal paragraph text.

**Bold**, *italic*

> This is a pull quote — great for memorable moments.

[Link text](https://url.com)

![Photo description](https://res.cloudinary.com/your_cloud/image/upload/w_900,q_auto,f_auto/posts/your-image.jpg)

--- (horizontal rule)
```

---

### Adding a new location

1. **Add to `data/locations.yaml`** (copy the template at the bottom of the file):
```yaml
- id: kyoto
  slug: kyoto
  name: Kyoto, Japan
  country: Japan
  continent: Asia
  lat: 35.0116
  lng: 135.7681
  dates: "Apr 2024"
  description: "Ten days exploring temples, bamboo forests, and the backstreets of Gion."
```

2. **Create the location page:**
```bash
hugo new locations/kyoto.md
```

3. **Upload a cover image** to Cloudinary at `locations/kyoto-cover.jpg` and `locations/kyoto-hero.jpg`

4. **Create a photo gallery:**
```bash
hugo new photos/kyoto-2024.md
```

The new location will automatically appear on the world map, the locations grid, and in all filter menus.

---

### Adding new photos

```bash
hugo new photos/kyoto-2024.md
```

Edit the file:
```yaml
location: kyoto
photos:
  - src: "photos/kyoto/fushimi-inari.jpg"
    caption: "Fushimi Inari at dawn"
  - src: "photos/kyoto/arashiyama.jpg"
    caption: "Arashiyama Bamboo Grove"
```

---

### Adding affiliate links

1. Set `has_affiliate_links: true` in the post frontmatter
2. A disclaimer box automatically appears at the top of the post
3. Edit `hugo.yaml` to customise the disclaimer text

---

## Customising the design

All design is in `static/css/main.css`. The key variables at the top of the file control everything:

```css
:root {
  --cream:    #F7F5F0;   /* background */
  --ink:      #1C1C19;   /* text */
  --forest:   #2D5016;   /* accent colour */
  /* ... */
}
```

Change `--forest` to any colour to update all links, highlights, and markers across the site.

---

## Custom domain (optional)

If you ever want `ramblingrover.com` instead of `github.io/rambling-rover`:

1. Buy the domain (Porkbun or Cloudflare Registrar are the cheapest)
2. In GitHub → repo → Settings → Pages → Custom domain → enter your domain
3. In your domain registrar's DNS settings, add:
   ```
   Type: CNAME
   Name: www
   Value: YOUR_USERNAME.github.io
   ```
4. Update `baseURL` in `hugo.yaml` to your custom domain
5. Push and wait ~10 minutes for DNS to propagate

---

## Troubleshooting

**Site shows 404 after pushing:**
- Check that GitHub Pages is set to "GitHub Actions" (not "Deploy from branch")
- Check the Actions tab for build errors

**Map doesn't show:**
- The homepage template sets `has_map: true` — check `content/_index.md` has this
- Open browser console (F12) for JavaScript errors

**Images not showing:**
- Check the Cloudinary cloud name in `hugo.yaml` matches your account exactly
- Test the URL directly in your browser

**Posts not appearing:**
- Check `draft: false` in the post frontmatter
- Check the date isn't in the future

**Running locally but not deploying correctly:**
- The `baseURL` in `hugo.yaml` must match your GitHub Pages URL exactly
- During local dev, Hugo ignores the baseURL — this only matters for deployment

---

## File structure reference

```
rambling-rover/
├── hugo.yaml               ← Site configuration (update baseURL + Cloudinary)
├── content/
│   ├── _index.md           ← Homepage settings
│   ├── posts/              ← Blog posts (one .md per post)
│   ├── locations/          ← Location pages with recommendations
│   └── photos/             ← Photo gallery entries
├── data/
│   └── locations.yaml      ← World map data + location metadata
├── layouts/                ← HTML templates (don't need to touch often)
├── static/
│   ├── css/main.css        ← All styles
│   └── js/                 ← Map + gallery JavaScript
├── scripts/
│   ├── migrate_wordpress.py
│   ├── remove_alcohol.py
│   └── compress_and_upload.py
└── .github/workflows/
    └── deploy.yml          ← Auto-deployment (don't edit)
```
