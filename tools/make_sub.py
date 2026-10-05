"""Tạo 02_script_sub.srt (mỗi dòng sub ngắn, 1 dòng) khớp với âm thanh thật.

Đầu vào trong thư mục video:
  02_script.txt          — mỗi đoạn (cách nhau dòng trống) = 1 file 02_script/N.mp3
  02_script/N.mp3        — âm thanh từng đoạn (ghép liền nhau thành 02_script_full.mp3)
Thông số cắt dòng đọc từ channels/<channel_id>.yaml → subtitle (không hardcode trong code).

Cách canh giờ: tách đoạn thành các cụm theo dấu câu / khoảng trắng (≤ max_chars),
dò các khoảng lặng thật trong mp3, rồi gắn ranh giới cụm có dấu câu vào đúng khoảng lặng gần nhất;
phần còn lại chia theo số âm tiết trong thời gian có tiếng.

    python tools/make_sub.py --channel eundo-malsseum --dir output/2026-10-05_thap-tu-gia-cua-minh
"""
import argparse
import math
import re
import sys
from pathlib import Path

import numpy as np
import yaml

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
HANGUL = re.compile(r"[가-힣]")


def log(msg):
    print(f"[make_sub] {msg}", file=sys.stderr, flush=True)


def load_pcm(path, rate=16000):
    import av

    c = av.open(str(path))
    rs = av.AudioResampler(format="s16", layout="mono", rate=rate)
    out = []
    for fr in c.decode(audio=0):
        for f in rs.resample(fr):
            out.append(f.to_ndarray().ravel())
    c.close()
    return np.concatenate(out).astype(np.float32) / 32768.0


def speech_map(x, rate, db_thr, min_pause):
    """Trả về (t_start, t_end, pauses) với pauses = [(t0, t1, v_before)]; v_before = thời gian có tiếng trước khoảng lặng."""
    fr = int(rate * 0.01)
    n = len(x) // fr
    rms = np.sqrt((x[: n * fr].reshape(n, fr) ** 2).mean(1)) + 1e-9
    voiced = 20 * np.log10(rms) >= db_thr
    idx = np.flatnonzero(voiced)
    if len(idx) == 0:
        return 0.0, n * 0.01, []
    a, b = idx[0], idx[-1] + 1
    pauses, st = [], None
    for i in range(a, b):
        if not voiced[i] and st is None:
            st = i
        elif voiced[i] and st is not None:
            if (i - st) * 0.01 >= min_pause:
                pauses.append((st * 0.01, i * 0.01))
            st = None
    res, acc, prev = [], 0.0, a * 0.01
    for t0, t1 in pauses:
        acc += t0 - prev
        res.append((t0, t1, acc))
        prev = t1
    return a * 0.01, b * 0.01, res


def envelope(x, rate=16000):
    fr = int(rate * 0.01)
    n = len(x) // fr
    return 20 * np.log10(np.sqrt((x[: n * fr].reshape(n, fr) ** 2).mean(1)) + 1e-9)


def locate(env_full, env_seg, expected, search=0.4, probe=6.0):
    """Tìm vị trí (giây) mà đoạn mp3 bắt đầu trong file full: khớp đường năng lượng quanh vị trí dự kiến."""
    m = min(len(env_seg), int(probe * 100))
    q = np.clip(env_seg[:m], -80, 0)
    q = q - q.mean()
    c0 = int(expected * 100)
    best, best_s = c0, -1e18
    for pos in range(max(0, c0 - int(search * 100)), min(len(env_full) - m, c0 + int(search * 100)) + 1):
        w = np.clip(env_full[pos : pos + m], -80, 0)
        s = -np.abs((w - w.mean()) - q).mean()
        if s > best_s:
            best, best_s = pos, s
    return best / 100.0


def split_lines(text, max_chars, min_chars):
    """Cắt đoạn thành các cụm. Trả về [(chuỗi, strength)] — strength: 2 hết câu, 1 dấu phẩy, 0 không dấu."""
    sents = re.findall(r"[^.?!]+[.?!]+[\"”'’]*|[^.?!]+$", text.replace("\n", " ").strip())
    clauses = []
    for s in sents:
        s = s.strip()
        if not s:
            continue
        parts = re.findall(r"[^,]+,[\"”'’]*|[^,]+$", s)
        for j, p in enumerate(parts):
            p = p.strip()
            if not p:
                continue
            strength = 2 if j == len(parts) - 1 else 1
            clauses.append([p, strength])
    # gộp cụm quá ngắn với cụm kế bên (nếu vẫn ≤ max_chars)
    merged = []
    for c in clauses:
        if merged and len(c[0]) < min_chars and merged[-1][1] == 1 and len(merged[-1][0]) + 1 + len(c[0]) <= max_chars:
            merged[-1] = [merged[-1][0] + " " + c[0], c[1]]
        elif merged and len(merged[-1][0]) < min_chars and merged[-1][1] == 1 and len(merged[-1][0]) + 1 + len(c[0]) <= max_chars:
            merged[-1] = [merged[-1][0] + " " + c[0], c[1]]
        else:
            merged.append(c)
    out = []
    for text_, strength in merged:
        if len(text_) <= max_chars:
            out.append((text_, strength))
            continue
        words = text_.split(" ")
        k = math.ceil(len(text_) / max_chars)
        while True:  # chia đều k phần theo ranh giới từ
            target = len(text_) / k
            chunks, cur = [], ""
            for w in words:
                cand = (cur + " " + w).strip()
                if cur and len(cand) > target + 1.5:
                    chunks.append(cur)
                    cur = w
                else:
                    cur = cand
            chunks.append(cur)
            if max(len(c) for c in chunks) <= max_chars or k > len(words):
                break
            k += 1
        for j, c in enumerate(chunks):
            out.append((c, strength if j == len(chunks) - 1 else 0))
    return out


def align(lines, t_start, t_end, pauses, snap_window, min_snap, env=None, dip_window=0.0):
    """Gán (start, end) cho từng cụm trong 1 đoạn. Thời gian tương đối đầu file mp3 của đoạn."""
    weights = [max(1, len(HANGUL.findall(l[0]))) for l in lines]
    S_total = sum(weights)
    V_total = (t_end - t_start) - sum(p[1] - p[0] for p in pauses)

    def v_to_t(v):
        t = t_start + v
        for p0, p1, vb in pauses:
            if vb <= v:
                t += p1 - p0
        return t

    bounds = []  # (end_time_of_line_k, start_time_of_line_k+1)
    v_prev, S_prev, pi = 0.0, 0, 0
    cum = 0
    for k in range(len(lines) - 1):
        cum += weights[k]
        v_est = v_prev + (V_total - v_prev) * (cum - S_prev) / max(1, S_total - S_prev)
        strength = lines[k][1]
        snapped = None
        if strength >= 1:
            best = None
            for j in range(pi, len(pauses)):
                p0, p1, vb = pauses[j]
                if vb < v_prev - 1e-6:
                    continue
                if vb > v_est + snap_window:
                    break
                dur = p1 - p0
                if dur < (min_snap if strength == 2 else min_snap) or abs(vb - v_est) > snap_window:
                    continue
                if best is None or abs(vb - v_est) < abs(pauses[best][2] - v_est):
                    best = j
            if best is not None:
                snapped = best
        if snapped is not None:
            p0, p1, vb = pauses[snapped]
            bounds.append((p0, p1))
            v_prev, S_prev, pi = vb, cum, snapped + 1
        else:
            t = v_to_t(v_est)
            if env is not None and dip_window > 0:  # kéo về chỗ năng lượng thấp nhất gần đó (khe giữa 2 âm tiết)
                lo, hi = max(0, int((t - dip_window) * 100)), min(len(env) - 1, int((t + dip_window) * 100))
                if hi - lo >= 4:
                    seg = np.convolve(env[lo : hi + 1], np.ones(3) / 3, mode="same")
                    j = int(np.argmin(seg))
                    if np.median(seg) - seg[j] >= 4.0:
                        t = (lo + j) / 100.0
            bounds.append((t, t + 0.02))
            v_prev, S_prev = v_est, cum
    res = []
    s = t_start
    for k in range(len(lines)):
        e = bounds[k][0] if k < len(bounds) else t_end
        res.append((s, e))
        if k < len(bounds):
            s = bounds[k][1]
    return res


def fmt(t):
    ms = int(round(t * 1000))
    h, r = divmod(ms, 3600000)
    m, r = divmod(r, 60000)
    s, ms = divmod(r, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main():
    ap = argparse.ArgumentParser(description="Tạo 02_script_sub.srt khớp âm thanh thật.")
    ap.add_argument("--channel", required=True)
    ap.add_argument("--dir", required=True, help="thư mục video, vd output/2026-10-05_thap-tu-gia-cua-minh")
    ap.add_argument("--audio", default="02_script_full.mp3", help="file audio đầy đủ trong thư mục video để canh vị trí")
    ap.add_argument("--timeline", default="", help="02_pauses_timeline.json (do add_pauses.py ghi) khi audio đã chèn nghỉ")
    ap.add_argument("--out", default="02_script_sub.srt", help="tên file srt đầu ra")
    args = ap.parse_args()

    cfg = yaml.safe_load(open(ROOT / "channels" / f"{args.channel}.yaml", encoding="utf-8"))
    sc = cfg.get("subtitle")
    if not sc:
        sys.exit("[make_sub] LỖI: channels/%s.yaml chưa có khối 'subtitle'" % args.channel)
    d = Path(args.dir)
    text = (d / "02_script.txt").read_text(encoding="utf-8")
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    seg_dir = d / "02_script"
    from mutagen.mp3 import MP3

    rate = 16000
    full_mp3 = d / args.audio
    env_full = envelope(load_pcm(full_mp3, rate)) if full_mp3.is_file() else None
    offset = 0.0
    drifts = []
    tl = {}
    if args.timeline:
        import json

        tl = {r["para"]: r for r in json.loads((d / args.timeline).read_text(encoding="utf-8"))}
    blocks = []
    report = []
    for i, para in enumerate(paras, 1):
        mp3 = seg_dir / f"{i}.mp3"
        if not mp3.is_file():
            sys.exit(f"[make_sub] LỖI: thiếu {mp3}")
        dur = MP3(str(mp3)).info.length
        x = load_pcm(mp3, rate)
        t0, t1, pauses = speech_map(x, rate, sc["silence_db"], sc["min_pause_sec"])
        splits = tl[i]["splits"] if tl else []
        expected = tl[i]["new_start"] if tl else offset
        if env_full is not None:
            probe = min(6.0, splits[0][0] - 0.2) if splits else 6.0  # chỉ dò phần trước chỗ chèn nghỉ đầu tiên
            pos = locate(env_full, envelope(x), expected, probe=probe) if probe >= 1.0 else expected
            drifts.append(pos - expected)
            base = pos
        else:
            base = expected

        def mp(v, _s=splits):
            return v + sum(sec for ts_, sec in _s if ts_ <= v)

        lines = split_lines(para, sc["max_chars"], sc["min_chars"])
        times = align(lines, t0, t1, pauses, sc["snap_window_sec"], sc["min_snap_pause_sec"], envelope(x), sc.get("dip_window_sec", 0.0))
        for (txt, _), (a, b) in zip(lines, times):
            blocks.append((base + mp(a), base + max(mp(b), mp(a) + 0.3), txt))
        report.append((i, dur, len(lines), len(pauses)))
        offset += dur
    # chống chồng lấn: kết thúc ≤ bắt đầu dòng sau − 0.02 (trừ khi cùng cụm liền nhau)
    out = []
    for k, (a, b, t) in enumerate(blocks):
        if k + 1 < len(blocks):
            b = min(b, blocks[k + 1][0] - 0.02)
        if b <= a:
            b = a + 0.3
        out.append((a, b, t))
    path = d / args.out
    with open(path, "w", encoding="utf-8") as f:
        for n, (a, b, t) in enumerate(out, 1):
            f.write(f"{n}\n{fmt(a)} --> {fmt(b)}\n{t}\n\n")
    if drifts:
        log(f"Lệch vị trí đoạn so với tổng độ dài header: min {min(drifts):+.2f}s, max {max(drifts):+.2f}s")
    L = [len(t) for _, _, t in out]
    log(f"Đã ghi {path} — {len(out)} dòng, TB {sum(L)/len(L):.1f} ký tự, tối đa {max(L)}, tổng {fmt(offset)}")


if __name__ == "__main__":
    main()
