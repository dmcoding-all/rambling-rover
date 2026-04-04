---
title: "{{ replace .Name "-" " " | title }}"
date: {{ .Date }}
slug: {{ .Name }}
draft: false

# WHERE — must match an `id` from data/locations.yaml (can be multiple)
locations:
  - edinburgh

# WHAT — pick from: hiking, appalachian trail, study abroad, travel blog,
#        gear + reviews, south america, europe, asia, north america
categories:
  - travel blog

# COVER — Cloudinary path (after /upload/), without leading slash
# e.g. posts/2023/my-post-cover.jpg
cover: ""

# DESCRIPTION — used for SEO and Open Graph (1–2 sentences)
description: ""

# Set true if this post contains Amazon or other affiliate links
has_affiliate_links: false

# THETREK — if this was cross-posted to TheTrek.co, add the URL
thetrek_url: ""
---

<!-- 
HOW TO ADD A NEW POST
=====================
1. Run: hugo new posts/YYYY-MM-DD-your-post-title.md
2. Fill in the frontmatter above (especially locations, categories, cover)
3. Write your post in markdown below this comment
4. Upload your cover image to Cloudinary first (see scripts/upload_to_cloudinary.py)
5. Add the Cloudinary path to the `cover` field above (just the path, not the full URL)
6. When ready, change `draft: false` above
7. Commit and push to GitHub — the site auto-deploys in ~2 minutes

MARKDOWN QUICK REFERENCE
=========================
# Heading 1 (don't use — reserved for post title)
## Heading 2
### Heading 3
**bold**, *italic*, ~~strikethrough~~

Image (hosted on Cloudinary):
![Alt text](https://res.cloudinary.com/YOUR_CLOUD/image/upload/w_900,q_auto,f_auto/posts/2023/filename.jpg)

Link: [link text](https://url.com)

Affiliate link (add has_affiliate_links: true to frontmatter):
[Buy on REI](https://affiliate-link.com)

Blockquote:
> This is a pull quote — great for memorable trail moments.
-->

Write your post here…
