"""Chuẩn bị tham số Higgsfield + chuẩn hóa ảnh nền thumbnail về 1280x720 (không chữ).

Ảnh được sinh bằng Higgsfield MCP (Claude gọi tool `generate_image`), script này
KHÔNG gọi API sinh ảnh nào. Có 2 chế độ:

1. In JSON tham số cho `generate_image` (model, aspect_ratio, prompt, ...) dựng từ
   channels/<channel_id>.yaml (thumbnail_bg + color_palette + motif + niche):
       python tools/make_bg.py --channel mun-yeolda --params [--scene "..."]

2. Tải/đọc ảnh Higgsfield trả về, scale + crop về 1280x720, lưu PNG:
       python tools/make_bg.py --from <url_hoặc_đường_dẫn_ảnh> --out output/2026-09-23_bac-si-canh-cua/thumb_bg.png
"""
import argparse
import io
import json
import sys
import urllib.request
from pathlib import Path

# Console Windows mặc định cp1252 → không in được tiếng Việt/Hàn.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
CHANNELS_DIR = ROOT / "channels"
TARGET_SIZE = (1280, 720)


def log(msg):
    print(f"[make_bg] {msg}", file=sys.stderr, flush=True)


def fail(msg, code=1):
    print(f"[make_bg] LỖI: {msg}", file=sys.stderr, flush=True)
    sys.exit(code)


def parse_args():
    p = argparse.ArgumentParser(
        description="In tham số Higgsfield generate_image từ channels/<id>.yaml, hoặc chuẩn hóa ảnh về 1280x720."
    )
    p.add_argument("--channel", help="channel_id, ứng với file channels/<channel_id>.yaml (dùng với --params)")
    p.add_argument("--scene", default="", help="(Tùy chọn) bối cảnh nền lấy từ kịch bản tập này, tiếng Anh")
    p.add_argument("--subject", default="", help="(Tùy chọn) nhân vật chính trên thumbnail (hư cấu), tiếng Anh")
    p.add_argument("--ref", default="", help="(Tùy chọn) job_id/media_id ảnh cũ để giữ nguyên gương mặt nhân vật")
    p.add_argument("--params", action="store_true", help="In JSON tham số cho Higgsfield generate_image ra stdout")
    p.add_argument("--from", dest="src", help="URL hoặc đường dẫn ảnh do Higgsfield sinh ra")
    p.add_argument("--out", help="Đường dẫn file PNG đầu ra (vd: output/.../thumb_bg.png), dùng với --from")
    args = p.parse_args()
    if args.params:
        if not args.channel:
            p.error("--params cần --channel")
    elif args.src:
        if not args.out:
            p.error("--from cần --out")
    else:
        p.error("Chọn 1 chế độ: --params hoặc --from")
    return args


def load_channel(channel_id):
    import yaml

    path = CHANNELS_DIR / f"{channel_id}.yaml"
    if not path.is_file():
        fail(f"Không tìm thấy file cấu hình kênh: {path}")
    try:
        with open(path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        fail(f"File YAML không hợp lệ ({path}): {e}")
    log(f"Đã đọc cấu hình kênh: {path}")
    return cfg


def pick_color(palette, key):
    """Lấy màu theo key; nếu không có key chính xác thì lấy key đầu tiên chứa chuỗi đó (vd: glow -> glow_white_gold)."""
    if key in palette:
        return palette[key]
    for k, v in palette.items():
        if key in k:
            return v
    return None


def current_character(cfg):
    """Khối character.current trong yaml kênh (nhân vật cố định trên thumbnail), {} nếu kênh không dùng."""
    return ((cfg.get("character") or {}).get("current")) or {}


def check_character_rotation(cfg, channel_id):
    """Đếm số video đã dùng nhân vật hiện tại (06_series_state.json → thumbnail.character_id), nhắc khi đủ hạn."""
    character = current_character(cfg)
    limit = (cfg.get("character") or {}).get("rotate_after_videos")
    if not character.get("id") or not limit:
        return
    used = 0
    for state_path in (ROOT / "output").glob("*/06_series_state.json"):
        try:
            state = json.loads(state_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            continue
        if state.get("channel_id") == channel_id and \
                (state.get("thumbnail") or {}).get("character_id") == character["id"]:
            used += 1
    log(f"Nhân vật {character['id']}: đã dùng {used}/{limit} video.")
    if used >= int(limit):
        print(f"[make_bg] CẢNH BÁO: nhân vật {character['id']} đã đủ {used}/{limit} video — "
              f"nên tạo nhân vật mới (xem character trong channels/{channel_id}.yaml).",
              file=sys.stderr, flush=True)


def build_prompt(cfg, scene="", subject="", ref=""):
    palette = cfg.get("color_palette") or {}
    motif = cfg.get("motif") or {}
    bg_cfg = cfg.get("thumbnail_bg") or {}

    navy = pick_color(palette, "navy")
    gold = pick_color(palette, "gold")
    glow = pick_color(palette, "glow")
    core_symbol = motif.get("core_symbol")

    missing = [n for n, v in (("color_palette.navy", navy), ("color_palette.gold", gold),
                              ("color_palette.glow*", glow), ("motif.core_symbol", core_symbol)) if not v]
    if missing:
        fail(f"Thiếu trường bắt buộc trong YAML kênh: {', '.join(missing)}")

    lines = [bg_cfg.get("style") or "Cinematic YouTube thumbnail background, 16:9 landscape."]
    if bg_cfg.get("composition"):
        lines.append(f"Composition: {bg_cfg['composition']}")

    character = current_character(cfg)
    if subject:
        lines.append(f"Main subject: {subject}.")
        if character.get("description"):
            lines.append(f"Main subject identity (fixed recurring character): {character['description']}")
        if ref:
            lines.append("The main subject MUST be the exact same person as in the reference image: "
                         "same face, hair, eyebrows, skin marks and age. Only pose, expression, lighting "
                         "and setting may change.")
        if bg_cfg.get("subject_style"):
            lines.append(f"Subject styling: {bg_cfg['subject_style']}")
        lines.append(f"Background behind the subject must clearly include the channel motif: {core_symbol}.")
    else:
        lines.append(f"Central visual motif: {core_symbol}, rendered as the clear focal point.")

    if scene:
        lines.append(f"Background scene (from this episode's story): {scene}.")
    lines += [
        f"Color palette: deep dominant background in {navy}, accent highlights in {gold}, soft glowing light in {glow}.",
        "Moody, atmospheric, emotional lighting with strong contrast and gentle volumetric haze.",
    ]
    if cfg.get("niche"):
        lines.append(f"Thematic mood inspired by: {cfg['niche']}.")
    avoid = motif.get("avoid_symbols") or []
    if avoid:
        lines.append("Avoid these compositions: " + "; ".join(str(a) for a in avoid) + ".")
    lines.append(
        "ABSOLUTELY NO text, no letters, no words, no numbers, no captions, no logos, no watermarks, "
        "no signatures anywhere in the image. Pure imagery only."
    )
    return "\n".join(lines)


def build_params(cfg, scene="", subject="", ref=""):
    """Dựng tham số cho Higgsfield generate_image từ khối thumbnail_bg trong yaml kênh."""
    bg_cfg = cfg.get("thumbnail_bg") or {}
    model = bg_cfg.get("model")
    if not model:
        fail("Thiếu thumbnail_bg.model trong YAML kênh (model Higgsfield, xem models_explore).")

    if not ref and subject and current_character(cfg).get("ref_job_id"):
        ref = current_character(cfg)["ref_job_id"]
        log(f"Dùng ảnh tham chiếu nhân vật cố định {current_character(cfg).get('id')}: {ref}")

    params = {
        "model": model,
        "aspect_ratio": bg_cfg.get("aspect_ratio", "16:9"),
        "count": 1,
        "prompt": build_prompt(cfg, scene, subject, ref),
    }
    if ref:
        role = bg_cfg.get("reference_role")
        if not role:
            fail("Có --ref nhưng thiếu thumbnail_bg.reference_role trong YAML kênh.")
        params["medias"] = [{"value": ref, "role": role}]
    params.update(bg_cfg.get("params") or {})

    palette_param = bg_cfg.get("palette_param")
    if palette_param:
        colors = [str(v) for v in (cfg.get("color_palette") or {}).values()]
        if colors:
            params[palette_param] = colors
    return params


def cover_resize(img, size):
    """Scale + center-crop ảnh về đúng kích thước size, giữ tỉ lệ."""
    from PIL import Image

    tw, th = size
    scale = max(tw / img.width, th / img.height)
    new = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    left = (new.width - tw) // 2
    top = (new.height - th) // 2
    return new.crop((left, top, left + tw, top + th))


def read_source(src):
    if src.startswith(("http://", "https://")):
        log(f"Đang tải ảnh: {src}")
        req = urllib.request.Request(src, headers={"User-Agent": "video-factory/make_bg"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.read()
    path = Path(src)
    if not path.is_file():
        fail(f"Không tìm thấy file ảnh: {path}")
    return path.read_bytes()


def normalize(src, out):
    from PIL import Image

    try:
        data = read_source(src)
    except Exception as e:
        fail(f"Không tải được ảnh: {type(e).__name__}: {e}")
    try:
        img = Image.open(io.BytesIO(data)).convert("RGB")
    except Exception as e:
        fail(f"Không đọc được ảnh: {e}")
    log(f"Nhận ảnh {img.width}x{img.height}, chuẩn hóa về {TARGET_SIZE[0]}x{TARGET_SIZE[1]}.")
    img = cover_resize(img, TARGET_SIZE)

    out = Path(out)
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        img.save(out, "PNG")
    except OSError as e:
        fail(f"Không lưu được file {out}: {e}")
    log(f"Đã lưu ảnh nền: {out.resolve()}")


def main():
    args = parse_args()
    if args.params:
        cfg = load_channel(args.channel)
        check_character_rotation(cfg, args.channel)
        print(json.dumps(build_params(cfg, args.scene, args.subject, args.ref), ensure_ascii=False, indent=2))
    else:
        normalize(args.src, args.out)


if __name__ == "__main__":
    main()
