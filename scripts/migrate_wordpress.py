#!/usr/bin/env python3
"""
migrate_wordpress.py
====================
Converts your WordPress XML export into Hugo-compatible markdown files
with enriched frontmatter.

USAGE
-----
    pip install lxml python-slugify
    python scripts/migrate_wordpress.py \
        --xml   path/to/wordpress-export.xml \
        --posts path/to/existing_posts_md/ \
        --out   content/posts/

The script:
  1. Reads the WordPress XML export for metadata (dates, categories, slugs)
  2. Reads your existing .md files for the body content (already clean markdown)
  3. Merges them into Hugo-formatted posts in --out
  4. Maps old WP categories to your new location IDs (edit LOCATION_MAP below)
  5. Skips the 7 duplicate posts (keeps the -2 versions)

CONFIGURATION — edit these two dicts before running
"""

import os, re, sys, argparse, yaml
from pathlib import Path
from xml.etree import ElementTree as ET

try:
    from slugify import slugify
except ImportError:
    sys.exit("Run: pip install python-slugify")

# ── EDIT THIS: map old WP category names → new location ids ──────────────────
LOCATION_MAP = {
    "Scotland":         "edinburgh",
    "Edinburgh":        "edinburgh",
    "Isle of Skye":     "isle-of-skye",
    "Germany":          "germany",
    "Czech Republic":   "czech-republic",
    "Italy":            "milan",
    "Ireland":          "dublin",
    "Belgium":          "brussels",     # add to locations.yaml if needed
    "The Netherlands":  "amsterdam",    # add to locations.yaml if needed
    "Spain":            "spain",
    "Switzerland":      "switzerland",
    "Canada":           "montreal",
    "Thailand":         "bangkok",
    "Asia":             None,           # too vague — won't assign
    "Argentina":        "buenos-aires",
    "Buenos Aires":     "buenos-aires",
    "South America":    None,
    "Patagonia":        "patagonia",
    "Iguazú":           "iguazu",
    "Chile":            "patagonia",
    "Appalachian Trail":"appalachian-trail-georgia",  # will refine per post
}

# ── Categories to keep as-is (not location-mapped) ───────────────────────────
KEEP_CATEGORIES = {
    "Hiking", "Study Abroad", "Travel Blog", "Gear + Reviews",
    "How-To", "Appalachian Trail", "Europe", "North America",
    "South America", "Asia", "Travel Recommendations",
}

# ── Posts to skip (originals replaced by -2 versions) ────────────────────────
SKIP_SLUGS = {
    "field-hockey",
    "climbing-the-cobbler",
    "germany-day-1",
    "deutschland-day-2-and-3",
    "my-final-days-in-deutschland",
    "isle-of-skye",
    "my-first-rugby-match-and-highland-bus-tour",
    "arthurs-seat-2-0-and-the-first-day-of-classes",
    "samhuinn-fire-festival",
}

# ── Alcohol terms to flag (see remove_alcohol.py for full removal) ────────────
ALCOHOL_PATTERN = re.compile(
    r'\b(wine|beer|pint|pub|brewery|distillery|gin|whisky|whiskey|'
    r'vodka|rum|cocktail|drunk|tipsy|hangover|prosecco|champagne|'
    r'a dram|the dram|dram of|shots? of|booze|boozy|lager|ale|cider|'
    r'espresso martini|happy hour)\b',
    re.IGNORECASE
)


def parse_wp_xml(xml_path: Path) -> dict:
    """Parse WordPress XML and return dict keyed by slug."""
    NS = {
        'wp':      'http://wordpress.org/export/1.2/',
        'content': 'http://purl.org/rss/1.0/modules/content/',
        'dc':      'http://purl.org/dc/elements/1.1/',
        'excerpt': 'http://wordpress.org/export/1.2/excerpt/',
    }

    tree = ET.parse(xml_path)
    root = tree.getroot()
    posts = {}

    for item in root.findall('.//item'):
        post_type = item.findtext('wp:post_type', namespaces=NS)
        status     = item.findtext('wp:status', namespaces=NS)

        if post_type != 'post' or status not in ('publish', 'draft'):
            continue

        slug = item.findtext('wp:post_name', namespaces=NS, default='').strip()
        if not slug:
            continue

        cats, locs = [], []
        for cat in item.findall('category'):
            domain = cat.get('domain', '')
            name   = cat.text or ''
            if domain == 'category':
                if name in KEEP_CATEGORIES:
                    cats.append(name.lower())
                loc_id = LOCATION_MAP.get(name)
                if loc_id:
                    locs.append(loc_id)

        posts[slug] = {
            'title':  item.findtext('title', default='').strip(),
            'date':   item.findtext('wp:post_date', namespaces=NS, default='')[:10],
            'slug':   slug,
            'cats':   sorted(set(cats)),
            'locs':   sorted(set(l for l in locs if l)),
            'status': status,
        }

    return posts


def build_frontmatter(wp_meta: dict, alcohol_found: list) -> str:
    """Build Hugo YAML frontmatter string."""
    fm = {
        'title':               wp_meta['title'],
        'date':                wp_meta['date'],
        'slug':                wp_meta['slug'].rstrip('-2'),
        'draft':               wp_meta['status'] == 'draft',
        'locations':           wp_meta['locs'] or [],
        'categories':          wp_meta['cats'] or [],
        'cover':               '',
        'description':         '',
        'has_affiliate_links': False,
    }

    lines = ['---']
    lines.append(f'title: {yaml.dump(fm["title"], default_flow_style=False).strip()}')
    lines.append(f'date: {fm["date"]}')
    lines.append(f'slug: {fm["slug"]}')
    lines.append(f'draft: {"true" if fm["draft"] else "false"}')
    lines.append('locations:')
    for loc in fm['locations']:
        lines.append(f'  - {loc}')
    lines.append('categories:')
    for cat in fm['categories']:
        lines.append(f'  - {cat}')
    lines.append(f'cover: ""')
    lines.append(f'description: ""')
    lines.append(f'has_affiliate_links: false')
    if alcohol_found:
        lines.append('# ⚠ ALCOHOL REFS FLAGGED — review before publishing:')
        for a in alcohol_found[:8]:
            lines.append(f'#   {a}')
    lines.append('---')
    return '\n'.join(lines) + '\n\n'


def migrate(xml_path: Path, md_dir: Path, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"📖 Parsing WordPress XML: {xml_path}")
    wp_posts = parse_wp_xml(xml_path)
    print(f"   Found {len(wp_posts)} published/draft posts in XML\n")

    md_files = sorted(md_dir.glob('*.md'))
    skipped, written, flagged = 0, 0, 0

    for md_file in md_files:
        raw_slug = re.sub(r'^\d{4}-\d{2}-\d{2}-', '', md_file.stem)

        # Skip original if -2 version exists
        if raw_slug in SKIP_SLUGS:
            print(f"   ⏭  Skipping (replaced by -2 version): {md_file.name}")
            skipped += 1
            continue

        # Normalise slug for -2 variants
        canonical_slug = raw_slug.rstrip('-2')

        # Read existing markdown body (strip old frontmatter)
        content = md_file.read_text(encoding='utf-8', errors='replace')
        fm_match = re.match(r'^---\n.*?\n---\n?', content, re.DOTALL)
        body = content[fm_match.end():].strip() if fm_match else content.strip()

        # Detect alcohol references in body
        alcohol_hits = list({m.group(0).lower() for m in ALCOHOL_PATTERN.finditer(body)})

        # Get WP metadata; fall back to filename-derived values
        wp_meta = wp_posts.get(raw_slug) or wp_posts.get(canonical_slug) or {}
        if not wp_meta:
            # Extract date from filename
            date_match = re.match(r'^(\d{4}-\d{2}-\d{2})', md_file.stem)
            wp_meta = {
                'title':  canonical_slug.replace('-', ' ').title(),
                'date':   date_match.group(1) if date_match else '2023-01-01',
                'slug':   canonical_slug,
                'cats':   [],
                'locs':   [],
                'status': 'publish',
            }

        # Build output
        front = build_frontmatter(wp_meta, alcohol_hits)
        output = front + body + '\n'

        # Filename: YYYY-MM-DD-slug.md
        out_name = f"{wp_meta['date']}-{canonical_slug}.md"
        out_path = out_dir / out_name
        out_path.write_text(output, encoding='utf-8')

        status_icon = '⚠' if alcohol_hits else '✓'
        print(f"   {status_icon}  {out_name}")
        if alcohol_hits:
            print(f"       alcohol refs: {', '.join(alcohol_hits[:5])}")
            flagged += 1
        written += 1

    print(f"\n{'─'*52}")
    print(f"✅ Written:  {written} posts  →  {out_dir}/")
    print(f"⏭  Skipped:  {skipped} (duplicate originals)")
    print(f"⚠  Flagged:  {flagged} posts have alcohol references")
    print(f"\nNEXT STEPS:")
    print(f"  1. Review flagged posts (search TODO-ALCOHOL in files)")
    print(f"  2. Add `cover:` image paths once you've uploaded to Cloudinary")
    print(f"  3. Add `description:` for each post (used for SEO)")
    print(f"  4. Set correct `locations:` for posts where it couldn't be inferred")


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Migrate WordPress export to Hugo posts')
    ap.add_argument('--xml',   required=True, help='Path to WordPress .xml export')
    ap.add_argument('--posts', required=True, help='Path to folder of existing .md files')
    ap.add_argument('--out',   default='content/posts', help='Hugo output directory')
    args = ap.parse_args()

    migrate(
        xml_path=Path(args.xml),
        md_dir=Path(args.posts),
        out_dir=Path(args.out),
    )
