"""Render a traceable original-PDF region, without interpreting its contents."""
import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import io
import json
import math
from pathlib import Path

MAX_PAGE_PIXELS = 40_000_000


def sha(data):
    return hashlib.sha256(data).hexdigest()


def render(pdf, page_number, rect, scale, out, expected_sha=None, normalized=False):
    pdf, out = Path(pdf), Path(out)
    if out.exists():
        raise ValueError('Output directory must be new; existing evidence is never overwritten')
    if not math.isfinite(scale) or not 1 <= scale <= 8:
        raise ValueError('Scale must be finite and between 1 and 8')
    if rect is not None and (len(rect) != 4 or not all(math.isfinite(n) for n in rect)):
        raise ValueError('Rectangle must contain four finite coordinates')
    if normalized and (rect is None or not (0 <= rect[0] < rect[2] <= 1 and 0 <= rect[1] < rect[3] <= 1)):
        raise ValueError('Normalized rectangle must satisfy 0 <= left < right <= 1 and 0 <= top < bottom <= 1')
    requested_rect = list(rect) if rect is not None else None
    if not isinstance(page_number, int) or isinstance(page_number, bool) or page_number < 1:
        raise ValueError('Use a 1-based physical PDF page number')
    data = pdf.read_bytes()
    source_sha = sha(data)
    if expected_sha is not None and source_sha != expected_sha.lower():
        raise ValueError('Source PDF SHA256 differs from the registered source')
    try:
        import pypdfium2 as pdfium
        from PIL import Image  # dependency check before creating outputs
    except ImportError as exc:
        raise RuntimeError('PDF rendering requires pypdfium2 and Pillow; see references/numeric-review.md') from exc
    with pdfium.PdfDocument(data) as document:
        if page_number > len(document):
            raise ValueError('Physical page number is outside this PDF')
        with closing(document[page_number - 1]) as page:
            rotation = page.get_rotation()
            if rotation != 0:
                raise ValueError('Rotated pages are not supported by this coordinate helper; use a PDF viewer and record its transform')
            width, height = page.get_size()
            if rect is None:
                rect = [0, 0, width, height]
            elif normalized:
                rect = [rect[0] * width, rect[1] * height, rect[2] * width, rect[3] * height]
            left, top, right, bottom = rect
            if not (0 <= left < right <= width and 0 <= top < bottom <= height):
                raise ValueError(f'Rectangle outside page bounds {width} x {height}; use left,top,right,bottom from top-left')
            if math.ceil(width * scale) * math.ceil(height * scale) > MAX_PAGE_PIXELS:
                raise ValueError('Rendering exceeds the conservative 40 million pixel page budget; reduce scale')
            pixel_box = (math.floor(left * scale), math.floor(top * scale),
                         math.ceil(right * scale), math.ceil(bottom * scale))

            def png(render_scale, pixel_crop=None):
                with closing(page.render(scale=render_scale, draw_annots=False)) as bitmap:
                    image = bitmap.to_pil()
                    if pixel_crop is not None:
                        cropped = image.crop(pixel_crop)
                        image.close()
                        image = cropped
                    size = list(image.size)
                    buffer = io.BytesIO()
                    image.save(buffer, format='PNG')
                    image.close()
                    return buffer.getvalue(), size

            region_bytes, region_size = png(scale, pixel_box)
            context_bytes, context_size = (region_bytes, region_size) if requested_rect is None and scale == 1.5 else png(1.5)
    manifest = {
        'schema_version': '1.0',
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'source_pdf_name': pdf.name, 'source_pdf_sha256': source_sha,
        'expected_source_hash_checked': expected_sha is not None,
        'physical_page_one_based': page_number, 'page_size_canvas_units': [width, height],
        'page_rotation_degrees': rotation,
        'coordinate_system': 'top-left origin in displayed unrotated page canvas units; left,top,right,bottom',
        'retained_rectangle': list(rect), 'region_pixel_box_left_top_right_bottom': list(pixel_box),
        'requested_rectangle': requested_rect,
        'requested_coordinate_mode': 'normalized-top-left' if normalized else ('whole-page' if requested_rect is None else 'canvas-top-left'),
        'render_strategy': 'Render full page, then crop outward to integer pixel boundaries without resizing',
        'region_scale_pixels_per_canvas_unit': scale, 'context_scale_pixels_per_canvas_unit': 1.5,
        'annotations_rendered': False,
        'renderer': {'pypdfium2': version('pypdfium2'), 'Pillow': version('Pillow')},
        'script_sha256': sha(Path(__file__).read_bytes()),
        'files': {'region.png': {'sha256': sha(region_bytes), 'pixels': region_size},
                  'context.png': {'sha256': sha(context_bytes), 'pixels': context_size}},
        'numeric_content_verified': False,
        'limitations': 'No OCR or semantic validation. Enlargement cannot recover detail absent from the source. Inspect labels, units, footnotes and version in context; rotated pages require a separate viewer workflow.'
    }
    out.mkdir(parents=True, exist_ok=False)
    for name, content in [('region.png', region_bytes), ('context.png', context_bytes),
                          ('provenance.json', json.dumps(manifest, ensure_ascii=False, indent=2).encode('utf-8'))]:
        with (out / name).open('xb') as stream:
            stream.write(content)
    return manifest


def overview(pdf, page_number, out, expected_sha=None):
    """Create an unannotated whole-page record and a separate navigation aid."""
    manifest = render(pdf, page_number, None, 1.5, out, expected_sha)
    from PIL import Image, ImageDraw
    out = Path(out)
    with Image.open(out / 'context.png') as source:
        source = source.convert('RGBA')
        width, height = source.size
        margin = 56
        canvas = Image.new('RGBA', (width + margin * 2, height + margin * 2), 'white')
        canvas.paste(source, (margin, margin))
        source.close()
        overlay = Image.new('RGBA', canvas.size)
        draw = ImageDraw.Draw(overlay)
        draw.text((margin, 4), 'LOCATOR ONLY - annotated. Read unannotated context/region for evidence.', fill=(0, 0, 0, 255))
        for i in range(11):
            x, y = margin + round(width * i / 10), margin + round(height * i / 10)
            draw.line((x, margin, x, margin + height), fill=(0, 90, 180, 45))
            draw.line((margin, y, margin + width, y), fill=(0, 90, 180, 45))
            draw.text((x - 8, margin - 22), f'{i/10:.1f}', fill=(0, 60, 150, 255))
            draw.text((6, y - 5), f'{i/10:.1f}', fill=(0, 60, 150, 255))
        draw.rectangle((margin, margin, margin + width, margin + height), outline=(0, 60, 150, 255), width=1)
        final = Image.alpha_composite(canvas, overlay).convert('RGB')
        final.save(out / 'locator.png', format='PNG')
        final.close()
        overlay.close()
        canvas.close()
    note = {'schema_version': 'paperscope-locator/1.0',
            'source_pdf_sha256': manifest['source_pdf_sha256'],
            'physical_page_one_based': page_number,
            'page_size_canvas_units': manifest['page_size_canvas_units'],
            'unannotated_context_sha256': manifest['files']['context.png']['sha256'],
            'locator_sha256': sha((out / 'locator.png').read_bytes()),
            'locator_page_origin_pixels': [margin, margin],
            'locator_page_size_pixels': [width, height],
            'coordinate_system': 'Fractions of the ORIGINAL page, left/top=0, right/bottom=1; exclude locator margins.',
            'annotations_added': 'Navigation grid and fractional rulers; locator is not an unmodified source image.',
            'numeric_content_verified': False}
    with (out / 'locator-provenance.json').open('x', encoding='utf-8') as stream:
        json.dump(note, stream, ensure_ascii=False, indent=2)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf', required=True)
    parser.add_argument('--page', type=int, required=True)
    region = parser.add_mutually_exclusive_group(required=True)
    region.add_argument('--rect', type=float, nargs=4, metavar=('LEFT', 'TOP', 'RIGHT', 'BOTTOM'))
    region.add_argument('--rect-normalized', type=float, nargs=4, metavar=('LEFT', 'TOP', 'RIGHT', 'BOTTOM'))
    region.add_argument('--overview', action='store_true', help='Whole page at 1.5x plus a separate annotated fractional locator')
    parser.add_argument('--scale', type=float, default=5)
    parser.add_argument('--expected-sha256')
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    try:
        if args.overview:
            result = overview(args.pdf, args.page, args.out, args.expected_sha256)
        else:
            result = render(args.pdf, args.page, args.rect_normalized if args.rect_normalized is not None else args.rect,
                            args.scale, args.out, args.expected_sha256, normalized=args.rect_normalized is not None)
    except (ValueError, RuntimeError, OSError) as exc:
        parser.exit(2, f'Render failed: {exc}\n')
    print(json.dumps({'out': str(Path(args.out)), 'source_pdf_sha256': result['source_pdf_sha256'],
                      'page_size_canvas_units': result['page_size_canvas_units'],
                      'retained_rectangle': result['retained_rectangle'],
                      'requested_coordinate_mode': result['requested_coordinate_mode'],
                      'locator_path': str(Path(args.out) / 'locator.png') if args.overview else None,
                      'numeric_content_verified': False}, ensure_ascii=False))


if __name__ == '__main__':
    main()
