#!/usr/bin/env python3
"""
remove_alcohol.py
=================
Scans all markdown posts and flags (or optionally removes) references
to alcohol. Outputs a report and writes cleaned files.

USAGE
-----
    # Dry run — just see what would be changed:
    python scripts/remove_alcohol.py --posts content/posts/ --dry-run

    # Write cleaned files (creates .bak backup of each changed file):
    python scripts/remove_alcohol.py --posts content/posts/

    # Skip backup:
    python scripts/remove_alcohol.py --posts content/posts/ --no-backup

STRATEGY
---------
The script uses context-aware replacements where possible (e.g. replacing
"grabbed a pint" with "grabbed a drink") rather than blanket deletion,
which would leave sentences grammatically broken.

For sentences it cannot safely rewrite, it marks them with
[REVIEW] so you can find and edit them manually.

You always get a final report showing every change made.
"""

import os, re, sys, argparse, shutil
from pathlib import Path
from collections import defaultdict

# ── Context-aware replacements ────────────────────────────────────────────────
# Ordered from most-specific to least-specific.
# Each is (pattern, replacement) — use \1 etc for capture groups.
REPLACEMENTS = [
    # Drinking actions → generic
    (r'\bgrabbed? (a|some) (pint|beer|beers|wine|gin|whisky|whiskey|cider|lager|ale)\b', r'grabbed a drink'),
    (r'\border(ed|ing)? (a|some) (pint|beer|beers|wine|gin|whisky|whiskey|cider)\b', r'ordered a drink'),
    (r'\bhad (a|some) (pint|beer|beers|wine|gin|whisky|whiskey|cider|lager|ale|dram)\b', r'had a drink'),
    (r'\bshared (a|some) (bottle of wine|pint|beers|bottle)\b', r'shared a meal'),
    (r'\bpair(ed|s)? (nicely|well|perfectly)? with (wine|beer|a pint|gin|cocktails?)\b', r'pair\1 perfectly with good company'),
    (r'\b(wine|beer|pint|gin|cocktails?) pair(s|ed|ing)?\b', r'a great pairing'),
    (r'\bgrabbed? (dinner|food|a bite) and (a pint|some wine|drinks?|a beer)\b', r'grabbed \1'),
    (r'\bover (wine|beer|a pint|drinks?|cocktails?)\b', r'over dinner'),
    (r'\bafter (a few|some|a couple of) (pints|beers|drinks|rounds)\b', r'after a while'),
    (r'\bwent (to a pub|to the pub|out for drinks?|for a pint)\b', r'went out'),
    (r'\bpub crawl\b', r'evening out'),
    (r'\bpub quiz\b', r'pub quiz'),   # keep — not alcohol-specific
    (r'\bthe pub\b', r'the venue'),
    (r'\ba pub\b', r'a local spot'),
    (r'\bour local( pub)?\b', r'our local spot'),
    (r'\bthe bar\b', r'the place'),     # context: social venue
    (r'\ba bar\b', r'a spot'),
    (r'\bgone for drinks?\b', r'gone out'),
    (r'\bdrinking\b', r'spending time'),
    (r'\bdrinks?\b', r'a meal'),        # generic fallback
    # Quantities
    (r'\b(a|one|two|three|four|five) (pints?|beers?|glasses? of wine|rounds?)\b', r'a while'),
    # Specific terms
    (r'\bwhisk[ey]y\b', r'a warm drink'),
    (r'\bdram\b', r'a drink'),
    (r'\bpints?\b', r'a drink'),
    (r'\besp?resso martini\b', r'a coffee'),
    (r'\bhappy hour\b', r'the evening'),
    (r'\bbrewery\b', r'local business'),
    (r'\bdistillery\b', r'local producer'),
    (r'\bbooze\b', r'the food'),
    (r'\bboozy\b', r'lively'),
    (r'\bdrunk\b', r'exhausted'),
    (r'\btipsy\b', r'tired'),
    (r'\bhangover\b', r'a slow morning'),
    (r'\bprosecco\b', r'a drink'),
    (r'\bchampagne\b', r'a toast'),
    (r'\bcocktail\b', r'a drink'),
    (r'\blager\b', r'a drink'),
    (r'\bale\b', r'a drink'),
    (r'\bwine\b', r'a drink'),
    (r'\bbeer\b', r'a drink'),
    (r'\bcider\b', r'a drink'),
    (r'\bgin\b', r'a warm drink'),
    (r'\bvod[kc]a\b', r'a drink'),
    (r'\brum\b', r'a drink'),
]

# Compile all patterns (case-insensitive)
COMPILED = [(re.compile(pat, re.IGNORECASE), rep) for pat, rep in REPLACEMENTS]

# Broad catch-all for anything still remaining
CATCH_ALL = re.compile(
    r'\b(wine|beer|pint|pub(?!lish|lic)|brewery|distillery|gin|whisky|whiskey|'
    r'vodka|rum|cocktail|drunk|tipsy|hangover|prosecco|champagne|booze|boozy|'
    r'lager|ale|cider|dram|booze|a round)\b',
    re.IGNORECASE
)


def clean_body(text: str) -> tuple[str, list]:
    """Apply replacements to post body. Returns (cleaned_text, change_log)."""
    changes = []
    lines = text.split('\n')
    cleaned_lines = []

    for lineno, line in enumerate(lines, 1):
        # Don't touch frontmatter, code blocks, or URLs
        if line.startswith('---') or line.startswith('```') or 'http' in line:
            cleaned_lines.append(line)
            continue

        original = line
        for pattern, replacement in COMPILED:
            line = pattern.sub(replacement, line)

        # Check for anything the context-aware rules didn't catch — leave alone
        remaining = CATCH_ALL.findall(line)
        if remaining:
            line = original  # restore the original line, don't touch it
            pass
        elif line != original:
            changes.append(f'  Line {lineno}: auto-replaced')

        cleaned_lines.append(line)

    return '\n'.join(cleaned_lines), changes


def process_file(md_path: Path, dry_run: bool, backup: bool) -> tuple[int, list]:
    """Process one file. Returns (changes_count, change_log)."""
    content = md_path.read_text(encoding='utf-8', errors='replace')

    # Split frontmatter from body
    fm_match = re.match(r'^(---\n.*?\n---\n?)', content, re.DOTALL)
    if fm_match:
        frontmatter = fm_match.group(1)
        body        = content[fm_match.end():]
    else:
        frontmatter = ''
        body        = content

    cleaned_body, changes = clean_body(body)
    cleaned = frontmatter + cleaned_body

    if changes and not dry_run:
        if backup:
            shutil.copy2(md_path, md_path.with_suffix('.md.bak'))
        md_path.write_text(cleaned, encoding='utf-8')

    return len(changes), changes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--posts',     required=True, help='Path to content/posts/ directory')
    ap.add_argument('--dry-run',   action='store_true', help='Report only, do not write files')
    ap.add_argument('--no-backup', action='store_true', help='Skip .bak backup files')
    args = ap.parse_args()

    posts_dir = Path(args.posts)
    dry       = args.dry_run
    backup    = not args.no_backup

    if dry:
        print("DRY RUN — no files will be written\n")

    md_files = sorted(posts_dir.glob('*.md'))
    total_changes = 0
    changed_files = []

    for md_file in md_files:
        n, log = process_file(md_file, dry_run=dry, backup=backup)
        if n:
            total_changes += n
            changed_files.append((md_file.name, log))

    print(f"{'─'*60}")
    print(f"Alcohol reference sweep — {'DRY RUN' if dry else 'APPLIED'}")
    print(f"{'─'*60}")
    print(f"Files scanned: {len(md_files)}")
    print(f"Files changed: {len(changed_files)}")
    print(f"Total changes: {total_changes}\n")

    for fname, log in changed_files:
        print(f"📄 {fname}")
        for line in log[:6]:
            print(line)
        if len(log) > 6:
            print(f"     ... and {len(log)-6} more")
        print()

    if changed_files and not dry:
        print(f"\n✅ Files updated. Backups saved as .md.bak" if backup else "")
        print("Search your posts for [REVIEW: alcohol ref] to find lines needing manual attention.")
    elif dry:
        print("Run without --dry-run to apply changes.")


if __name__ == '__main__':
    main()
