"""Ghép chữ lên ảnh nền để tạo thumbnail YouTube 1280x720.

Đọc schema 05_thumb_text.json:
    {
      "main_text": "...",
      "sub_text": "...",
      "font_title": "...",
      "color_main": "#F5A623",
      "color_bg_overlay": "#0A1128",
      "layout": {"text_side": "left", "text_width_pct": 55, "main_max_px": 150, "sub_max_px": 64}
    }
    layout lấy từ channels/<id>.yaml → thumbnail_layout; bỏ trống = chữ căn giữa ở đáy.

Chế độ nhiều dòng (khuyên dùng — kiểu thumbnail viral Hàn: mỗi dòng 1 màu/kiểu riêng):
    {
      "lines": [
        {"text": "천국에서", "style": "top"},
        {"text": "먼저 간 가족", "style": "box"},
        {"text": "알아볼까요?", "style": "hero"}
      ],
      "caption": "성경의 대답 · 은도 목사",       (tùy chọn, dòng nhỏ dưới cùng)
      "font_title": "BlackHanSans-Regular.ttf",
      "styles": { "<tên>": {"color": "#FFFFFF" | "gradient": ["#FFE259", "#FFA751"],
                            "box": "#E0141E" (tùy chọn), "scale": 1.0,
                            "stroke": "#000000", "stroke_ratio": 0.08} },
      "color_bg_overlay": "#2B1D14",
      "layout": {...}
    }
    styles lấy nguyên khối từ channels/<id>.yaml → thumbnail_text_style.styles.
    Có "lines" thì bỏ qua main_text/sub_text.

Ví dụ:
    python tools/render_thumb.py --json output/.../05_thumb_text.json \
        --bg output/.../thumb_bg.png --out output/.../thumb_final.png
"""
import argparse
import json
import re
import sys
from pathlib import Path

# Console Windows mặc định cp1252 → không in được tiếng Việt/Hàn.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
FONTS_DIR = ROOT / "fonts"
SIZE = (1280, 720)
MARGIN_X = 70
MARGIN_BOTTOM = 50
FONT_EXTS = (".ttf", ".otf", ".ttc")

# Font hệ thống dự phòng (ưu tiên font có hỗ trợ tiếng Hàn / tiếng Việt).
SYSTEM_FALLBACK_FONTS = [
    "C:/Windows/Fonts/malgunbd.ttf",
    "C:/Windows/Fonts/malgun.ttf",
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/Library/Fonts/Arial Bold.ttf",
]


def log(msg):
    print(f"[render_thumb] {msg}", flush=True)


def warn(msg):
    print(f"[render_thumb] CẢNH BÁO: {msg}", file=sys.stderr, flush=True)


def fail(msg, code=1):
    print(f"[render_thumb] LỖI: {msg}", file=sys.stderr, flush=True)
    sys.exit(code)


def parse_args():
    p = argparse.ArgumentParser(description="Ghép main_text/sub_text lên ảnh nền, xuất thumbnail 1280x720.")
    p.add_argument("--json", required=True, help="Đường dẫn 05_thumb_text.json")
    p.add_argument("--bg", required=True, help="Đường dẫn ảnh nền thumb_bg.png")
    p.add_argument("--out", required=True, help="Đường dẫn file đầu ra thumb_final.png")
    return p.parse_args()


def load_spec(path):
    try:
        with open(path, encoding="utf-8-sig") as f:  # -sig: chấp nhận file có BOM (Notepad/PowerShell trên Windows)
            spec = json.load(f)
    except FileNotFoundError:
        fail(f"Không tìm thấy file JSON: {path}")
    except json.JSONDecodeError as e:
        fail(f"JSON không hợp lệ ({path}): {e}")
    if not isinstance(spec, dict):
        fail("JSON phải là một object.")
    if spec.get("lines"):
        if not isinstance(spec["lines"], list) or not all(
                isinstance(l, dict) and str(l.get("text", "")).strip() for l in spec["lines"]):
            fail("lines phải là danh sách object có 'text' không trống.")
        if not isinstance(spec.get("styles"), dict) or not spec["styles"]:
            fail("Chế độ lines cần khối 'styles' (copy từ channels/<id>.yaml → thumbnail_text_style.styles).")
        for l in spec["lines"]:
            if l.get("style") not in spec["styles"]:
                fail(f"Dòng {l.get('text')!r} dùng style {l.get('style')!r} không có trong 'styles'.")
    elif not str(spec.get("main_text", "")).strip():
        fail("main_text trống — thumbnail bắt buộc có chữ chính.")
    return spec


def parse_color(value, default, field):
    if isinstance(value, str) and re.fullmatch(r"#?[0-9a-fA-F]{6}", value.strip()):
        h = value.strip().lstrip("#")
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    warn(f"{field}={value!r} không phải mã màu #RRGGBB hợp lệ, dùng mặc định {default}.")
    return parse_color(default, default, field)


def _norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def find_font_file(font_title):
    """Tìm file font trong fonts/ khớp với font_title.

    font_title có thể là tên file ("NotoSerifKR-Bold.ttf") hoặc tên font ("Noto Serif KR",
    "Cinzel + Noto Serif KR"). Thử từng tên, ưu tiên bản Bold/Black.
    """
    if not font_title or not FONTS_DIR.is_dir():
        return None
    files = [f for f in FONTS_DIR.rglob("*") if f.suffix.lower() in FONT_EXTS]
    if not files:
        return None

    direct = FONTS_DIR / font_title
    if direct.is_file():
        return direct

    candidates = [c for c in re.split(r"[+,/|]", font_title) if c.strip()]
    # Font có "KR" (hỗ trợ tiếng Hàn) được thử trước.
    candidates.sort(key=lambda c: 0 if "kr" in c.lower() else 1)
    weight_rank = ("black", "extrabold", "bold", "semibold", "medium", "regular")

    for cand in candidates:
        key = _norm(re.sub(r"\(.*?\)", "", cand))
        if not key:
            continue
        matches = [f for f in files if _norm(f.stem).startswith(key)]
        if matches:
            def rank(f):
                stem = _norm(f.stem)
                for i, w in enumerate(weight_rank):
                    if w in stem:
                        return i
                return len(weight_rank)
            return sorted(matches, key=rank)[0]
    return None


def resolve_font_path(font_title):
    path = find_font_file(font_title)
    if path:
        log(f"Dùng font: {path}")
        return str(path)
    warn(f"Không tìm thấy file font cho font_title={font_title!r} trong {FONTS_DIR}.")
    for fb in SYSTEM_FALLBACK_FONTS:
        if Path(fb).is_file():
            warn(f"Fallback sang font hệ thống: {fb}")
            return fb
    warn("Không có font hệ thống dự phòng, dùng font mặc định của Pillow (chất lượng thấp).")
    return None


def load_font(path, size):
    from PIL import ImageFont

    if path:
        try:
            return ImageFont.truetype(path, size)
        except OSError as e:
            warn(f"Không load được font {path}: {e}. Dùng font mặc định của Pillow.")
    return ImageFont.load_default(size=size)


def text_width(draw, text, font, stroke=0):
    if not text:
        return 0
    l, _, r, _ = draw.textbbox((0, 0), text, font=font, stroke_width=stroke)
    return r - l


def wrap_text(draw, text, font, max_w, stroke=0):
    """Wrap theo từ; từ nào dài hơn max_w thì cắt theo ký tự. Giữ nguyên \\n người dùng tự đặt."""
    lines = []
    for para in str(text).split("\n"):
        words = para.split()
        if not words:
            lines.append("")
            continue
        cur = ""
        for word in words:
            trial = f"{cur} {word}" if cur else word
            if text_width(draw, trial, font, stroke) <= max_w:
                cur = trial
                continue
            if cur:
                lines.append(cur)
                cur = ""
            # Từ đơn lẻ vẫn quá rộng → cắt theo ký tự.
            for ch in word:
                if text_width(draw, cur + ch, font, stroke) <= max_w or not cur:
                    cur += ch
                else:
                    lines.append(cur)
                    cur = ch
        lines.append(cur)
    return lines


def layout_block(draw, text, font_path, max_size, min_size, max_w, max_h, max_lines, stroke_ratio):
    """Giảm cỡ chữ dần tới khi khối chữ vừa khung. Trả về (font, lines, line_h, stroke, block_h)."""
    size = max_size
    while True:
        font = load_font(font_path, size)
        stroke = max(1, round(size * stroke_ratio))
        lines = wrap_text(draw, text, font, max_w, stroke)
        asc, desc = font.getmetrics()
        line_h = round((asc + desc) * 1.12)
        block_h = line_h * len(lines)
        fits = block_h <= max_h and len(lines) <= max_lines
        if fits or size <= min_size:
            if not fits:
                warn(f"Chữ quá dài, đã giảm tới cỡ tối thiểu {size}px nhưng vẫn có thể chật: {text[:40]!r}...")
            return font, lines, line_h, stroke, block_h
        size -= 4


def draw_block(img, lines, font, line_h, stroke, top, fill, stroke_fill, left=None):
    """Vẽ khối chữ. left=None → căn giữa theo chiều ngang; left=x → căn trái tại x."""
    from PIL import Image, ImageDraw, ImageFilter

    W, _ = img.size

    def line_x(draw, line):
        if left is not None:
            return left
        return (W - text_width(draw, line, font, stroke)) / 2

    # Bóng đổ mềm: vẽ chữ đen lên layer riêng, blur rồi dán dưới chữ chính.
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    offset = max(3, line_h // 25)
    y = top
    for line in lines:
        sd.text((line_x(sd, line) + offset, y + offset), line, font=font, fill=(0, 0, 0, 180),
                stroke_width=stroke, stroke_fill=(0, 0, 0, 180))
        y += line_h
    shadow = shadow.filter(ImageFilter.GaussianBlur(max(2, line_h // 18)))
    img.alpha_composite(shadow)

    d = ImageDraw.Draw(img)
    y = top
    for line in lines:
        d.text((line_x(d, line), y), line, font=font, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
        y += line_h


def missing_glyphs(font, text):
    """Ký tự font không có glyph (Pillow vẽ ra ô trống/ô .notdef) — vd Black Han Sans thiếu '·', '—', '…'."""
    from PIL import Image

    def raster(ch):
        m = font.getmask(ch)
        im = Image.new("L", m.size)
        if m.size[0] * m.size[1]:
            im.putdata(list(m))
        return im.tobytes(), m.getbbox()

    notdef = raster("￿")[0]
    out = []
    for ch in set(text):
        if ch.isspace():
            continue
        data, bbox = raster(ch)
        if bbox is None or data == notdef:
            out.append(ch)
    return out


def _line_metrics(font, text, stroke):
    """bbox thực của dòng chữ (kể cả viền) → (offset_x, offset_y, w, h)."""
    l, t, r, b = font.getbbox(text, stroke_width=stroke)
    return l, t, r - l, b - t


def _style_for(spec, name, base_size):
    st = spec["styles"][name]
    size = max(12, round(base_size * float(st.get("scale", 1.0))))
    grad = st.get("gradient")
    if isinstance(grad, list) and len(grad) >= 2:
        fill = [parse_color(c, "#FFFFFF", f"styles.{name}.gradient") for c in grad[:2]]
    else:
        fill = parse_color(st.get("color", "#FFFFFF"), "#FFFFFF", f"styles.{name}.color")
    box = parse_color(st["box"], "#E0141E", f"styles.{name}.box") if st.get("box") else None
    return {
        "size": size,
        "fill": fill,
        "box": box,
        "stroke_fill": parse_color(st.get("stroke", "#000000"), "#000000", f"styles.{name}.stroke"),
        "stroke_ratio": float(st.get("stroke_ratio", 0.08)),
        "box_pad": float(st.get("box_pad", 0.14)),
    }


def plan_lines(spec, font_path, base_size, max_w):
    """Tính cỡ chữ từng dòng: theo scale của style, tự thu nhỏ riêng dòng nào vượt max_w."""
    items = list(spec["lines"])
    if str(spec.get("caption") or "").strip():
        items.append({"text": spec["caption"].strip(), "style": "caption" if "caption" in spec["styles"] else None})
    planned = []
    for it in items:
        name = it.get("style")
        if name is None:  # caption không có style riêng → chữ trắng nhỏ
            st = {"size": max(20, round(base_size * 0.36)), "fill": (255, 255, 255), "box": None,
                  "stroke_fill": (0, 0, 0), "stroke_ratio": 0.08, "box_pad": 0.14}
        else:
            st = _style_for(spec, name, base_size)
        size = st["size"]
        while True:
            font = load_font(font_path, size)
            stroke = max(1, round(size * st["stroke_ratio"]))
            ox, oy, w, h = _line_metrics(font, it["text"], stroke)
            pad = round(size * st["box_pad"]) if st["box"] else 0
            if w + 2 * pad <= max_w or size <= 24:
                break
            size -= 2
        miss = missing_glyphs(font, it["text"])
        if miss:
            warn(f"Font không có glyph cho {''.join(sorted(miss))!r} trong dòng {it['text']!r} → sẽ hiện ô trống. "
                 f"Thay bằng ký tự khác (vd '|' hoặc '-').")
        planned.append({**st, "text": it["text"], "font": font, "stroke": stroke,
                        "ox": ox, "oy": oy, "w": w, "h": h, "pad": pad})
    return planned


def draw_lines(img, planned, left, top, gap):
    """Vẽ lần lượt: bóng đổ mờ → hộp màu (nếu có) → viền → chữ (màu đặc hoặc gradient dọc)."""
    from PIL import Image, ImageDraw, ImageFilter

    W, H = img.size
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    y = top
    for p in planned:
        off = max(3, p["size"] // 22)
        if p["box"]:
            sd.rectangle([left + off, y + off, left + p["w"] + 2 * p["pad"] + off, y + p["h"] + 2 * p["pad"] + off],
                         fill=(0, 0, 0, 170))
        tx, ty = left + p["pad"] - p["ox"], y + p["pad"] - p["oy"]
        sd.text((tx + off, ty + off), p["text"], font=p["font"], fill=(0, 0, 0, 200),
                stroke_width=p["stroke"], stroke_fill=(0, 0, 0, 200))
        y += p["h"] + 2 * p["pad"] + gap
    img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(6)))

    d = ImageDraw.Draw(img)
    y = top
    for p in planned:
        bh = p["h"] + 2 * p["pad"]
        if p["box"]:
            d.rectangle([left, y, left + p["w"] + 2 * p["pad"], y + bh], fill=p["box"])
        tx, ty = left + p["pad"] - p["ox"], y + p["pad"] - p["oy"]
        # Viền = mặt nạ chữ "nở" ra (blur + ngưỡng), KHÔNG dùng stroke_width của Pillow:
        # FreeType stroker bỏ sót nét ở vài font Hàn (vd nét ㅏ của '아' trong Black Han Sans).
        mask = Image.new("L", img.size, 0)
        ImageDraw.Draw(mask).text((tx, ty), p["text"], font=p["font"], fill=255)
        img.paste(Image.new("RGBA", img.size, p["stroke_fill"] + (255,)), (0, 0), dilate(mask, p["stroke"]))
        d = ImageDraw.Draw(img)
        if isinstance(p["fill"], list):
            c1, c2 = p["fill"]
            grad = Image.new("RGBA", (1, H))
            y0, y1 = y + p["pad"], y + p["pad"] + p["h"]
            for yy in range(H):
                k = min(1.0, max(0.0, (yy - y0) / max(1, y1 - y0)))
                grad.putpixel((0, yy), tuple(round(a + (b - a) * k) for a, b in zip(c1, c2)) + (255,))
            img.paste(grad.resize(img.size), (0, 0), mask)
        else:
            img.paste(Image.new("RGBA", img.size, p["fill"] + (255,)), (0, 0), mask)
        d = ImageDraw.Draw(img)
        y += bh + gap


def dilate(mask, radius):
    """Nở mặt nạ chữ thêm ~radius px với góc bo tròn (Gaussian blur + ngưỡng), chỉ cần Pillow."""
    from PIL import ImageFilter

    if radius <= 0:
        return mask
    # Với sigma = r/2, mép thẳng tại khoảng cách r còn ~2.3% độ sáng → ngưỡng 6/255 ≈ nở đúng r px.
    grown = mask.filter(ImageFilter.GaussianBlur(radius / 2)).point(lambda v: 255 if v > 6 else 0)
    return grown.filter(ImageFilter.GaussianBlur(1))  # khử răng cưa mép viền


def render_lines_mode(bg, spec, side, text_width_pct, main_max_px, font_path):
    W, H = bg.size
    max_w = int(W * text_width_pct / 100) - MARGIN_X if side == "left" else W - 2 * MARGIN_X
    max_h = int(H * 0.86)
    base = main_max_px
    while True:
        planned = plan_lines(spec, font_path, base, max_w)
        gap = max(6, round(base * 0.10))
        total_h = sum(p["h"] + 2 * p["pad"] for p in planned) + gap * (len(planned) - 1)
        if total_h <= max_h or base <= 40:
            break
        base -= 4
    top = max(20, int((H - total_h) / 2)) if side == "left" else max(20, H - MARGIN_BOTTOM - total_h)
    if side == "left":
        draw_lines(bg, planned, MARGIN_X, top, gap)
    else:  # bottom_center: vẽ từng dòng căn giữa
        y = top
        for p in planned:
            draw_lines(bg, [p], int((W - p["w"] - 2 * p["pad"]) / 2), y, 0)
            y += p["h"] + 2 * p["pad"] + gap
    return planned


def apply_overlay(bg, color, side, text_width_pct, max_alpha=225):
    """Gradient màu color_bg_overlay để chữ luôn đọc được: từ trái sang (side=left) hoặc từ giữa xuống đáy."""
    from PIL import Image, ImageDraw

    W, H = bg.size
    overlay = Image.new("RGBA", bg.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    if side == "left":
        # Đậm tối đa ở mép trái, nhạt dần về 0 sau vùng chữ một đoạn để chuyển mượt sang nhân vật.
        grad_end = min(W, int(W * (text_width_pct + 15) / 100))
        for x in range(grad_end):
            alpha = int(max_alpha * (1 - x / grad_end) ** 1.1)
            od.line([(x, 0), (x, H)], fill=(*color, alpha))
    else:
        grad_start = int(H * 0.38)
        for y in range(grad_start, H):
            alpha = int(215 * ((y - grad_start) / (H - grad_start)) ** 1.3)
            od.line([(0, y), (W, y)], fill=(*color, alpha))
    bg.alpha_composite(overlay)


def main():
    args = parse_args()
    from PIL import Image, ImageDraw

    spec = load_spec(args.json)
    main_text = str(spec.get("main_text", "")).strip()
    sub_text = str(spec.get("sub_text") or "").strip()
    color_main = parse_color(spec.get("color_main"), "#F5A623", "color_main")
    color_overlay = parse_color(spec.get("color_bg_overlay"), "#0A1128", "color_bg_overlay")

    try:
        bg = Image.open(args.bg).convert("RGBA")
    except FileNotFoundError:
        fail(f"Không tìm thấy ảnh nền: {args.bg}")
    except OSError as e:
        fail(f"Không đọc được ảnh nền {args.bg}: {e}")

    if bg.size != SIZE:
        log(f"Ảnh nền {bg.width}x{bg.height} → chuẩn hóa về {SIZE[0]}x{SIZE[1]} (scale + crop giữa).")
        scale = max(SIZE[0] / bg.width, SIZE[1] / bg.height)
        bg = bg.resize((round(bg.width * scale), round(bg.height * scale)), Image.LANCZOS)
        left, top = (bg.width - SIZE[0]) // 2, (bg.height - SIZE[1]) // 2
        bg = bg.crop((left, top, left + SIZE[0], top + SIZE[1]))

    W, H = SIZE
    layout = spec.get("layout") or {}
    side = layout.get("text_side", "bottom_center")
    if side not in ("left", "bottom_center"):
        warn(f"layout.text_side={side!r} không hỗ trợ, dùng bottom_center.")
        side = "bottom_center"
    text_width_pct = float(layout.get("text_width_pct", 55))
    main_max_px = int(layout.get("main_max_px", 130))

    apply_overlay(bg, color_overlay, side, text_width_pct, int(layout.get("overlay_alpha", 225)))

    font_path = resolve_font_path(spec.get("font_title"))

    if spec.get("lines"):
        planned = render_lines_mode(bg, spec, side, text_width_pct, main_max_px, font_path)
        save(bg, args.out)
        log("lines: " + " | ".join(f"{p['text']} @{p['font'].size}px" for p in planned))
        return

    measure = ImageDraw.Draw(bg)
    if side == "left":
        max_w = int(W * text_width_pct / 100) - MARGIN_X
        main_max_h = int(H * 0.62)
    else:
        max_w = W - 2 * MARGIN_X
        main_max_h = int(H * 0.50)

    m_font, m_lines, m_lh, m_stroke, m_h = layout_block(
        measure, main_text, font_path, max_size=main_max_px, min_size=48,
        max_w=max_w, max_h=main_max_h, max_lines=3, stroke_ratio=0.06)

    s_lines, s_h, gap = [], 0, 0
    if sub_text:
        sub_max_px = int(layout.get("sub_max_px", max(32, int(m_font.size * 0.45))))
        s_font, s_lines, s_lh, s_stroke, s_h = layout_block(
            measure, sub_text, font_path, max_size=sub_max_px, min_size=24,
            max_w=max_w, max_h=int(H * 0.22), max_lines=2, stroke_ratio=0.07)
        gap = 18

    total_h = s_h + gap + m_h
    if side == "left":
        # Căn giữa theo chiều dọc, lệch lên nhẹ (mắt người xem đọc từ trên-trái).
        top = max(20, int((H - total_h) / 2 - H * 0.03))
        left = MARGIN_X
    else:
        top = max(20, H - MARGIN_BOTTOM - total_h)
        left = None

    if s_lines:
        draw_block(bg, s_lines, s_font, s_lh, s_stroke, top, fill=(255, 255, 255),
                   stroke_fill=color_overlay, left=left)
        top += s_h + gap
    draw_block(bg, m_lines, m_font, m_lh, m_stroke, top, fill=color_main, stroke_fill=(0, 0, 0), left=left)

    save(bg, args.out)
    log(f"main_text: {len(m_lines)} dòng @ {m_font.size}px | sub_text: {len(s_lines)} dòng")


def save(img, path):
    out = Path(path)
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        img.convert("RGB").save(out, "PNG")
    except OSError as e:
        fail(f"Không lưu được file {out}: {e}")
    log(f"Đã lưu thumbnail {img.width}x{img.height}: {out.resolve()}")


if __name__ == "__main__":
    main()
