"""Đo giọng đọc TTS bằng số liệu âm thanh (không thay được việc nghe bằng tai).

    python tools/voice_check.py --channel eundo-malsseum --dir output/<thư-mục> [--audio 02_script_full.mp3]

Báo: độ dài, tỷ lệ có tiếng, tốc độ (âm tiết/giây), khoảng nghỉ (≥ 0,15s / ≥ 1s / ≥ 1,5s), độ to,
cao độ (F0) — so với giọng mẫu trong channels/<id>.yaml → voice.measured. Nếu có thư mục 02_script/ (mp3 từng đoạn)
thì thêm độ biến thiên tốc độ giữa các đoạn và khoảng lặng nối đoạn. Ghi voice_report.md.
"""
import argparse
import re
import sys
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_sub as ms  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
RATE = 16000


def f0_track(x):
    fr, hop = int(0.04 * RATE), int(0.1 * RATE)
    lo, hi = int(RATE / 300), int(RATE / 70)
    out = []
    for i in range(0, len(x) - fr, hop):
        w = x[i : i + fr]
        if np.sqrt((w**2).mean()) < 0.02:
            continue
        w = w - w.mean()
        ac = np.correlate(w, w, "full")[fr - 1 :]
        if ac[0] <= 0:
            continue
        k = lo + int(np.argmax(ac[lo:hi]))
        if ac[k] / ac[0] > 0.5:
            out.append(RATE / k)
    return np.array(out)


def pause_runs(db, thr, min_len=0.15):
    voiced = db >= thr
    idx = np.flatnonzero(voiced)
    if len(idx) == 0:
        return np.array([])
    runs, st = [], None
    for i in range(idx[0], idx[-1] + 1):
        if not voiced[i] and st is None:
            st = i
        elif voiced[i] and st is not None:
            if (i - st) * 0.01 >= min_len:
                runs.append((i - st) * 0.01)
            st = None
    return np.array(runs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel", required=True)
    ap.add_argument("--dir", required=True)
    ap.add_argument("--audio", default="02_script_full.mp3")
    args = ap.parse_args()
    cfg = yaml.safe_load(open(ROOT / "channels" / f"{args.channel}.yaml", encoding="utf-8"))
    ref = (cfg.get("voice") or {}).get("measured") or {}
    thr = (cfg.get("subtitle") or {}).get("silence_db", -45)
    d = Path(args.dir)
    script = (d / "02_script.txt").read_text(encoding="utf-8")
    syl = len(re.findall("[가-힣]", script))

    x = ms.load_pcm(d / args.audio, RATE)
    db = ms.envelope(x, RATE)
    dur = len(x) / RATE
    voiced = db >= thr
    speech = voiced.sum() * 0.01
    runs = pause_runs(db, thr)
    ff = f0_track(x)
    f0m = float(np.median(ff))
    f0r = float(np.percentile(12 * np.log2(ff / f0m), 95) - np.percentile(12 * np.log2(ff / f0m), 5))
    L = [f"# Voice check — {d.name} ({args.audio})", ""]
    L.append(f"- Độ dài: {dur/60:.1f} phút (yaml kênh: {cfg.get('video_length_minutes')})")
    L.append(f"- Tốc độ tổng: {syl/dur:.2f} âm tiết/giây (giọng mẫu {ref.get('syllables_per_sec','?')}); khi đang nói {syl/speech:.2f}")
    L.append(f"- Có tiếng: {100*speech/dur:.0f}% thời lượng")
    L.append(f"- Khoảng nghỉ ≥ 0,15s: {len(runs)} ({len(runs)/(dur/60):.1f}/phút); ≥ 1s: {(runs>=1).sum()}; ≥ 1,5s: {(runs>=1.5).sum()}")
    L.append(f"- Độ to (có tiếng): trung vị {np.median(db[voiced]):.1f} dB, p10 {np.percentile(db[voiced],10):.1f}, p90 {np.percentile(db[voiced],90):.1f}")
    L.append(f"- Cao độ: trung vị {f0m:.0f} Hz (giọng mẫu {ref.get('f0_median_hz','?')}), biên độ {f0r:.1f} nửa cung (giọng mẫu {ref.get('pitch_range_semitones','?')})")
    flags = []
    if ref.get("f0_median_hz") and abs(f0m - ref["f0_median_hz"]) > 12:
        flags.append("Cao độ lệch > 12 Hz so với giọng mẫu — có thể sai giọng/tham số TTS")
    if ref.get("syllables_per_sec") and abs(syl / dur - ref["syllables_per_sec"]) / ref["syllables_per_sec"] > 0.12:
        flags.append("Tốc độ tổng lệch > 12% so với giọng mẫu")
    if (runs >= 1.5).sum() < dur / 60 / 3:
        flags.append("Ít khoảng nghỉ dài (≥ 1,5s) — nhịp có thể phẳng; xem tools/add_pauses.py + 02_pauses.json")

    seg_dir = d / "02_script"
    paras = [p.strip() for p in re.split(r"\n\s*\n", script) if p.strip()]
    if args.audio == "02_script_full.mp3" and seg_dir.is_dir():
        rates, joins = [], []
        for i, p in enumerate(paras, 1):
            f = seg_dir / f"{i}.mp3"
            if not f.is_file():
                break
            xs = ms.load_pcm(f, RATE)
            e = ms.envelope(xs, RATE)
            v = e >= thr
            ix = np.flatnonzero(v)
            if len(ix) == 0:
                continue
            rates.append(len(re.findall("[가-힣]", p)) / (v.sum() * 0.01))
            joins.append((ix[0] + (len(e) - 1 - ix[-1])) * 0.01)
        if rates:
            r = np.array(rates)
            L.append(f"- Tốc độ giữa các đoạn: TB {r.mean():.2f}, độ lệch chuẩn {r.std():.2f} (thấp < 0,6 = đọc rất đều); lặng nối đoạn TB {np.mean(joins):.2f}s")
            if r.std() < 0.6:
                flags.append("Tốc độ rất đều giữa các đoạn — cao trào không được đọc chậm hơn; cân nhắc giảm tốc đoạn cao trào khi sinh TTS")
    L.append("")
    L.append("## Cần xem")
    L += [f"- {f}" for f in flags] or ["- Không có cờ đỏ về số đo."]
    L.append("")
    L.append("Lưu ý: số đo không thay được việc nghe — cần nghe tại các mốc cao trào, câu trích Kinh Thánh, số chương/câu.")
    (d / "voice_report.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
