#!/usr/bin/env python3
"""
compress_and_upload.py
======================
Batch-compresses your local images and uploads them to Cloudinary.
Also updates image URLs in your markdown posts from old WordPress
domains to new Cloudinary URLs.

SETUP
-----
    pip install Pillow cloudinary requests tqdm

    Set these environment variables (or pass as args):
        CLOUDINARY_CLOUD_NAME=your_cloud_name
        CLOUDINARY_API_KEY=your_api_key
        CLOUDINARY_API_SECRET=your_api_secret

USAGE
-----
    # 1. Compress only (no upload) — good first check:
    python scripts/compress_and_upload.py \
        --input  /path/to/your/image/folder/ \
        --output /path/to/compressed/output/ \
        --compress-only

    # 2. Compress + upload to Cloudinary:
    python scripts/compress_and_upload.py \
        --input  /path/to/your/image/folder/ \
        --output /path/to/compressed/output/ \
        --cloud  your_cloud_name \
        --key    your_api_key \
        --secret your_api_secret \
        --prefix posts/

    # 3. After uploading, update post URLs:
    python scripts/compress_and_upload.py \
        --update-posts content/posts/ \
        --cloud your_cloud_name

COMPRESSION TARGETS
-------------------
    Cover images:  max 1600px wide, ~85 quality  →  typically 150–400KB
    Gallery photos: max 2000px wide, ~88 quality  →  typically 200–600KB
    Thumbnails:    max 600px wide,  ~82 quality  →  typically 30–80KB

Cloudinary also applies its own automatic optimization on top of this.
"""

import os, re, sys, argparse, json, time
from pathlib import Path
from collections import defaultdict

try:
    from PIL import Image, ImageOps
    from tqdm import tqdm
except ImportError:
    sys.exit("Run: pip install Pillow tqdm")

# ── Old image domain patterns to rewrite in posts ────────────────────────────
OLD_DOMAINS = [
    r'https?://dcabroad\.wordpress\.com/wp-content/uploads/[^\s\)\"\']+',
    r'https?://theramblingrover\.com/wp-content/uploads/[^\s\)\"\']+',
    r'https?://i[012]\.wp\.com/theramblingrover\.com/wp-content/uploads/[^\s\)\"\']+',
    r'https?://photos\.thetrek\.co/[^\s\)\"\']+',
]
OLD_URL_RE = re.compile('(' + '|'.join(OLD_DOMAINS) + ')', re.IGNORECASE)

# Image quality settings by type
QUALITY = {
    'cover':   {'max_w': 1600, 'max_h': 1200, 'q': 85},
    'gallery': {'max_w': 2000, 'max_h': 1600, 'q': 88},
    'thumb':   {'max_w': 600,  'max_h': 500,  'q': 82},
}

SUPPORTED_EXTS = {'.jpg', '.jpeg', '.png', '.webp', '.heic', '.tiff', '.tif'}


def compress_image(src: Path, dst: Path, profile: str = 'gallery') -> dict:
    """Compress a single image and save to dst. Returns stats dict."""
    cfg = QUALITY[profile]

    try:
        img = Image.open(src)
        img = ImageOps.exif_transpose(img)  # auto-rotate based on EXIF

        # Convert to RGB (handles RGBA, P, CMYK etc.)
        if img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')

        orig_w, orig_h = img.size
        img.thumbnail((cfg['max_w'], cfg['max_h']), Image.LANCZOS)
        new_w, new_h = img.size

        dst.parent.mkdir(parents=True, exist_ok=True)
        save_kwargs = {'optimize': True}
        ext = dst.suffix.lower()
        if ext in ('.jpg', '.jpeg'):
            save_kwargs['quality'] = cfg['q']
            save_kwargs['progressive'] = True
        elif ext == '.png':
            save_kwargs['compress_level'] = 7
        elif ext == '.webp':
            save_kwargs['quality'] = cfg['q']

        img.save(dst, **save_kwargs)

        orig_kb = src.stat().st_size / 1024
        new_kb  = dst.stat().st_size / 1024
        saving  = (1 - new_kb / orig_kb) * 100 if orig_kb > 0 else 0

        return {
            'src': str(src), 'dst': str(dst),
            'orig_size': f'{orig_kb:.0f}KB', 'new_size': f'{new_kb:.0f}KB',
            'saving': f'{saving:.0f}%',
            'orig_dims': f'{orig_w}×{orig_h}',
            'new_dims':  f'{new_w}×{new_h}',
            'ok': True,
        }
    except Exception as e:
        return {'src': str(src), 'ok': False, 'error': str(e)}


def upload_to_cloudinary(local_path: Path, public_id: str,
                          cloud: str, api_key: str, api_secret: str) -> dict:
    """Upload one file to Cloudinary and return response."""
    try:
        import cloudinary
        import cloudinary.uploader
        cloudinary.config(cloud_name=cloud, api_key=api_key, api_secret=api_secret)
        result = cloudinary.uploader.upload(
            str(local_path),
            public_id=public_id,
            overwrite=True,
            resource_type='image',
            use_filename=False,
        )
        return {'ok': True, 'url': result['secure_url'], 'public_id': result['public_id']}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


def batch_compress(input_dir: Path, output_dir: Path, profile: str = 'gallery') -> list:
    """Compress all images in input_dir to output_dir."""
    images = [
        p for p in sorted(input_dir.rglob('*'))
        if p.suffix.lower() in SUPPORTED_EXTS and not p.name.startswith('.')
    ]

    print(f"\n🗜  Compressing {len(images)} images ({profile} profile)...")
    results = []

    for img_path in tqdm(images, unit='img'):
        rel      = img_path.relative_to(input_dir)
        out_path = (output_dir / rel).with_suffix('.jpg')
        result   = compress_image(img_path, out_path, profile)
        results.append(result)

    ok    = [r for r in results if r['ok']]
    fail  = [r for r in results if not r['ok']]
    saved = sum(
        float(r['orig_size'].rstrip('KB')) - float(r['new_size'].rstrip('KB'))
        for r in ok if 'orig_size' in r
    )

    print(f"\n{'─'*50}")
    print(f"✅ Compressed: {len(ok)}  ❌ Failed: {len(fail)}")
    print(f"💾 Estimated space saved: ~{saved/1024:.1f} MB")
    if fail:
        print("Failures:")
        for f in fail:
            print(f"  {f['src']}: {f.get('error','unknown')}")
    return results


def batch_upload(compressed_dir: Path, prefix: str,
                 cloud: str, api_key: str, api_secret: str) -> dict:
    """Upload all compressed images to Cloudinary. Returns {local_path: cloudinary_url}."""
    try:
        import cloudinary
    except ImportError:
        sys.exit("Run: pip install cloudinary")

    images = sorted(compressed_dir.rglob('*.jpg'))
    mapping = {}

    print(f"\n☁️  Uploading {len(images)} images to Cloudinary...")
    for img_path in tqdm(images, unit='img'):
        rel       = img_path.relative_to(compressed_dir)
        public_id = (prefix.rstrip('/') + '/' + str(rel).replace('\\', '/').rstrip('.jpg'))
        result    = upload_to_cloudinary(img_path, public_id, cloud, api_key, api_secret)

        if result['ok']:
            mapping[str(rel)] = result['url']
        else:
            print(f"\n  ❌ {img_path.name}: {result.get('error','')}")
        time.sleep(0.1)  # rate limiting

    # Save mapping to JSON for the post-update step
    mapping_file = compressed_dir.parent / 'cloudinary_mapping.json'
    with open(mapping_file, 'w') as f:
        json.dump(mapping, f, indent=2)

    print(f"\n✅ Uploaded {len(mapping)} images")
    print(f"📋 URL mapping saved to: {mapping_file}")
    return mapping


def update_post_urls(posts_dir: Path, cloud: str):
    """Replace old WordPress image URLs with Cloudinary auto-URLs in all posts."""
    mapping_file = posts_dir.parent.parent / 'cloudinary_mapping.json'
    if not mapping_file.exists():
        # If no mapping file, just replace with a placeholder
        print("No cloudinary_mapping.json found — will insert placeholder URLs")
        mapping = {}
    else:
        with open(mapping_file) as f:
            mapping = json.load(f)

    md_files = sorted(posts_dir.glob('*.md'))
    updated  = 0
    base_url = f"https://res.cloudinary.com/{cloud}/image/upload"

    for md_path in md_files:
        content = md_path.read_text(encoding='utf-8', errors='replace')

        def replace_url(m):
            old_url = m.group(0)
            # Extract filename from old URL
            filename = Path(old_url.split('?')[0]).stem
            # Look for a match in the mapping
            for rel_path, cl_url in mapping.items():
                if filename in rel_path:
                    # Return Cloudinary URL with auto-optimization transforms
                    public_id = cl_url.split('/upload/')[-1]
                    return f"{base_url}/w_900,q_auto,f_auto/{public_id}"
            # No match found — leave a visible placeholder
            return f"[IMAGE-NEEDED: {Path(old_url).name}]"

        new_content = OLD_URL_RE.sub(replace_url, content)
        if new_content != content:
            md_path.write_text(new_content, encoding='utf-8')
            updated += 1

    print(f"\n✅ Updated image URLs in {updated}/{len(md_files)} posts")
    print("Search posts for [IMAGE-NEEDED: to find URLs that couldn't be matched")


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Compress images and upload to Cloudinary')
    ap.add_argument('--input',         help='Input image folder')
    ap.add_argument('--output',        help='Output folder for compressed images')
    ap.add_argument('--compress-only', action='store_true')
    ap.add_argument('--profile',       default='gallery',
                    choices=['cover','gallery','thumb'])
    ap.add_argument('--cloud',         default=os.environ.get('CLOUDINARY_CLOUD_NAME',''))
    ap.add_argument('--key',           default=os.environ.get('CLOUDINARY_API_KEY',''))
    ap.add_argument('--secret',        default=os.environ.get('CLOUDINARY_API_SECRET',''))
    ap.add_argument('--prefix',        default='photos/', help='Cloudinary folder prefix')
    ap.add_argument('--update-posts',  help='Path to content/posts/ to rewrite URLs')
    args = ap.parse_args()

    if args.update_posts:
        update_post_urls(Path(args.update_posts), args.cloud)
        sys.exit(0)

    if not args.input or not args.output:
        ap.print_help()
        sys.exit(1)

    results = batch_compress(Path(args.input), Path(args.output), args.profile)

    if not args.compress_only:
        if not all([args.cloud, args.key, args.secret]):
            print("\n⚠  Cloudinary credentials missing. Use --cloud, --key, --secret")
            print("   Or set env vars CLOUDINARY_CLOUD_NAME / API_KEY / API_SECRET")
            sys.exit(1)
        batch_upload(Path(args.output), args.prefix, args.cloud, args.key, args.secret)
