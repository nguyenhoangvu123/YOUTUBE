"""Nhận dạng giọng nói (faster-whisper) từng đoạn mp3 rồi so với 02_script.txt để bắt chỗ TTS đọc sai/bỏ/thêm chữ.

    python tools/asr_check.py --dir output/2026-10-05_thap-tu-gia-cua-minh [--model large-v3] [--device auto]

Ghi:
  asr_report.md  — danh sách đoạn lệch, xếp theo độ lệch
  asr_raw.json   — văn bản ASR từng đoạn (để chạy lại so sánh không cần nhận dạng lại)
Lưu ý: ASR cũng có thể nghe nhầm; mọi chỗ báo lệch cần nghe lại bằng tai trước khi sửa.
"""
import argparse
import difflib
import json
import re
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

DIGITS = {"0": "영", "1": "일", "2": "이", "3": "삼", "4": "사", "5": "오", "6": "육", "7": "칠", "8": "팔", "9": "구"}


def sino(n):
    """1-999 → cách đọc Hán-Hàn (22 → 이십이, 11 → 십일)."""
    n = int(n)
    if n == 0:
        return "영"
    out = ""
    h, r = divmod(n, 100)
    if h:
        out += ("" if h == 1 else DIGITS[str(h)]) + "백"
    t_, o = divmod(r, 10)
    if t_:
        out += ("" if t_ == 1 else DIGITS[str(t_)]) + "십"
    if o:
        out += DIGITS[str(o)]
    return out


def norm(s):
    s = re.sub(r"\d+", lambda m: sino(m.group()) if len(m.group()) <= 3 else "".join(DIGITS[c] for c in m.group()), s)
    return re.sub(r"[^가-힣]", "", s)


def load_pcm(path, rate=16000):
    import av
    import numpy as np

    c = av.open(str(path))
    rs = av.AudioResampler(format="s16", layout="mono", rate=rate)
    out = []
    for fr in c.decode(audio=0):
        for f in rs.resample(fr):
            out.append(f.to_ndarray().ravel())
    c.close()
    return np.concatenate(out).astype(np.float32) / 32768.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--model", default="large-v2")
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--compute", default="int8")
    args = ap.parse_args()
    d = Path(args.dir)
    paras = [p.strip() for p in re.split(r"\n\s*\n", (d / "02_script.txt").read_text(encoding="utf-8")) if p.strip()]
    raw_path = d / "asr_raw.json"
    raw = json.loads(raw_path.read_text(encoding="utf-8")) if raw_path.is_file() else {}
    from faster_whisper import WhisperModel

    model = WhisperModel(args.model, device=args.device, compute_type=args.compute, cpu_threads=4)
    for i, para in enumerate(paras, 1):
        if str(i) in raw:
            continue
        segs, _ = model.transcribe(
            load_pcm(d / "02_script" / f"{i}.mp3"), language="ko", beam_size=5, temperature=0.0,
            condition_on_previous_text=False, initial_prompt=None,
        )
        raw[str(i)] = " ".join(s.text.strip() for s in segs)
        print(f"[asr] {i}/{len(paras)}", file=sys.stderr, flush=True)
        if i % 3 == 0:
            raw_path.write_text(json.dumps(raw, ensure_ascii=False, indent=1), encoding="utf-8")
    raw_path.write_text(json.dumps(raw, ensure_ascii=False, indent=1), encoding="utf-8")

    rows = []
    for i, para in enumerate(paras, 1):
        a, b = norm(para), norm(raw.get(str(i), ""))
        sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
        ops = [(t, a[i1:i2], b[j1:j2]) for t, i1, i2, j1, j2 in sm.get_opcodes() if t != "equal"]
        rows.append((sm.ratio(), i, para, raw.get(str(i), ""), ops))
    rows.sort()
    tot = sum(len(norm(p)) for p in paras)
    err = sum(max(len(x[1]), len(x[2])) for r in rows for x in r[4])
    out = [f"# ASR check — {d.name}", f"Model: {args.model}. Ký tự Hàn: {tot}, ký tự lệch ≈ {err} ({100*err/tot:.1f}%).", ""]
    for ratio, i, para, asr, ops in rows:
        if ratio >= 0.995:
            continue
        out.append(f"## Đoạn {i} — giống {ratio*100:.1f}%")
        out.append(f"- Kịch bản: {para[:160]}")
        out.append(f"- ASR:      {asr[:160]}")
        out.append("- Lệch: " + "; ".join(f"{t}: '{x}'→'{y}'" for t, x, y in ops[:8]))
        out.append("")
    (d / "asr_report.md").write_text("\n".join(out), encoding="utf-8")
    print(f"[asr] Đã ghi {d/'asr_report.md'} — lệch ≈ {100*err/tot:.1f}%, {sum(1 for r in rows if r[0] < 0.995)} đoạn có chênh", file=sys.stderr)


if __name__ == "__main__":
    main()
