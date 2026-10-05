"""Chèn khoảng nghỉ vào giọng đọc đã sinh (không cần sinh lại TTS) để tạo nhịp/cảm xúc.

Đầu vào trong thư mục video: 02_script.txt, 02_script/N.mp3, 02_pauses.json
  02_pauses.json:
    {
      "after_para": {"8": 1.8, "11": 2.0},          # nghỉ THÊM sau đoạn N (giây), cộng vào khoảng lặng tự nhiên của TTS
      "inside":     [{"para": 8, "after": "아내는 웃으며 말했습니다.", "sec": 1.2}]   # nghỉ THÊM sau 1 câu trong đoạn
    }
  Đoạn không có trong after_para dùng pauses.default_sec của channels/<id>.yaml.

Ghi:
  02_script_full_pauses.mp3   — audio đã chèn nghỉ (giữ nguyên 02_script_full.mp3 gốc)
  02_pauses_timeline.json     — để make_sub.py tạo sub khớp (--timeline)

    python tools/add_pauses.py --channel eundo-malsseum --dir output/<thư-mục>
"""
import argparse
import json
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
RATE = 32000


def log(m):
    print(f"[add_pauses] {m}", file=sys.stderr, flush=True)


def load_stereo(path, rate=RATE):
    import av

    c = av.open(str(path))
    rs = av.AudioResampler(format="s16", layout="stereo", rate=rate)
    out = []
    for fr in c.decode(audio=0):
        for f in rs.resample(fr):
            out.append(f.to_ndarray().ravel())
    c.close()
    return np.concatenate(out).astype(np.int16)  # xen kẽ L R


class Mp3Writer:
    """Ghi mp3 theo luồng (tránh giữ cả 30 phút PCM trong RAM)."""

    def __init__(self, path, rate=RATE, bitrate=192000):
        import av

        self.av = av
        self.rate = rate
        self.o = av.open(str(path), "w")
        self.st = self.o.add_stream("libmp3lame", rate=rate)
        self.st.layout = "stereo"
        self.st.bit_rate = bitrate

    def write(self, pcm):
        step = self.rate * 2 * 10
        for i in range(0, len(pcm), step):
            fr = self.av.AudioFrame.from_ndarray(pcm[i : i + step].reshape(1, -1), format="s16", layout="stereo")
            fr.sample_rate = self.rate
            for p in self.st.encode(fr):
                self.o.mux(p)

    def close(self):
        for p in self.st.encode(None):
            self.o.mux(p)
        self.o.close()


def sentences(text):
    return [s.strip() for s in re.findall(r"[^.?!]+[.?!]+[\"”'’]*|[^.?!]+$", text.replace("\n", " ")) if s.strip()]


def silence(sec):
    return np.zeros(int(round(sec * RATE)) * 2, dtype=np.int16)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel", required=True)
    ap.add_argument("--dir", required=True)
    args = ap.parse_args()
    cfg = yaml.safe_load(open(ROOT / "channels" / f"{args.channel}.yaml", encoding="utf-8"))
    pc = cfg.get("pauses") or {}
    sc = cfg["subtitle"]
    d = Path(args.dir)
    plan = json.loads((d / "02_pauses.json").read_text(encoding="utf-8"))
    default = float(plan.get("default_sec", pc.get("default_sec", 0.35)))
    after = {int(k): float(v) for k, v in plan.get("after_para", {}).items()}
    inside = {}
    for it in plan.get("inside", []):
        inside.setdefault(int(it["para"]), []).append(it)
    paras = [p.strip() for p in re.split(r"\n\s*\n", (d / "02_script.txt").read_text(encoding="utf-8")) if p.strip()]

    out = d / "02_script_full_pauses.mp3"
    writer = Mp3Writer(out)
    timeline = []
    pos = 0.0
    added_total = 0.0
    warn = []
    for i, para in enumerate(paras, 1):
        mp3 = d / "02_script" / f"{i}.mp3"
        st = load_stereo(mp3)
        splits = []
        if i in inside:
            x = ms.load_pcm(mp3)
            t0, t1, pauses = ms.speech_map(x, 16000, sc["silence_db"], sc["min_pause_sec"])
            sents = sentences(para)
            lines = [(s, 2) for s in sents]
            times = ms.align(lines, t0, t1, pauses, sc["snap_window_sec"], sc["min_snap_pause_sec"], ms.envelope(x), sc.get("dip_window_sec", 0.0))
            for it in inside[i]:
                k = next((j for j, s in enumerate(sents) if it["after"] in s), None)
                if k is None or k >= len(sents) - 1:
                    warn.append(f"đoạn {i}: không tìm thấy câu (hoặc là câu cuối) '{it['after']}'")
                    continue
                gap = times[k + 1][0] - times[k][1]
                mid = (times[k][1] + times[k + 1][0]) / 2
                if gap < 0.1:
                    warn.append(f"đoạn {i}: sau '{it['after'][:14]}…' không có khoảng lặng thật, cắt ước lượng tại {mid:.2f}s — nên nghe lại")
                splits.append((mid, float(it["sec"])))
            splits.sort()
        # ghép
        cur = 0
        for t, sec in splits:
            idx = int(round(t * RATE)) * 2
            writer.write(st[cur:idx])
            writer.write(silence(sec))
            cur = idx
            added_total += sec
        writer.write(st[cur:])
        seg_len = len(st) / 2 / RATE
        gap_after = after.get(i, default) if i < len(paras) else 0.0
        if gap_after > 0:
            writer.write(silence(gap_after))
            added_total += gap_after
        timeline.append({"para": i, "new_start": round(pos, 3), "seg_len": round(seg_len, 3), "splits": [[round(t, 3), s] for t, s in splits]})
        pos += seg_len + sum(s for _, s in splits) + gap_after
    writer.close()
    (d / "02_pauses_timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=1), encoding="utf-8")
    for w in warn:
        log("CẢNH BÁO " + w)
    log(f"Đã ghi {out} — {pos/60:.1f} phút (thêm {added_total:.0f}s nghỉ). Timeline: 02_pauses_timeline.json")


if __name__ == "__main__":
    main()
