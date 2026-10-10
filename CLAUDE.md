# video-factory — Nội quy chung

Đây là nội quy bắt buộc cho mọi kênh, mọi video sinh ra từ hệ thống này.
Skill `tao-video` PHẢI đọc và tuân thủ file này trước khi sinh bất kỳ nội dung nào.

## 1. Quy tắc chống bịa đặt / không trung thực

- KHÔNG bịa số liệu, thống kê, trích dẫn khoa học/y tế/lịch sử nếu không có
  nguồn trong `01_ideas.md` hoặc tài liệu người dùng cung cấp.
- Được phép dùng tên người có thật (vd: 신성종 목사) làm nhân vật/người dẫn chuyện,
  theo quyết định của chủ dự án (cập nhật 2026-10-09). Điều kiện đi kèm:
  - Không bịa tiểu sử, chức danh, hội thánh, số liệu hay lời trích dẫn rồi trình bày
    như sự thật về người đó. Mọi chi tiết đời thực chỉ dùng khi có nguồn trong
    `01_ideas.md` hoặc tài liệu người dùng cung cấp.
  - Phần sáng tác/hư cấu (lời kể, tình huống, hội thoại) phải được công bố rõ trong
    `04_description.md` (xem dòng công bố bên dưới), không để người xem tưởng là
    lời/việc có thật của người đó.
  - Không đặt vào miệng người có thật nội dung xúc phạm, sai lệch giáo lý, hoặc
    gây hại cho danh dự của họ.
  - Người khác (không phải nhân vật chính đã được chủ dự án chỉ định) vẫn nên
    ẩn danh hóa ("một mục sư", "một bác sĩ").
- Mỗi video BẮT BUỘC có dòng công bố nội dung sáng tác/chuyển thể trong
  `04_description.md`, đặt trước phần hashtag, không giấu ở cuối cùng.
- Mỗi kênh BẮT BUỘC có dòng công bố tương tự trong phần mô tả kênh (About) —
  kiểm tra 1 lần khi setup kênh, lưu bằng chứng đã thêm vào `channels/*.yaml`.

## 2. Quy tắc đặt tên file (không được đổi)

```
output/YYYY-MM-DD_slug-khong-dau/
├── 01_ideas.md
├── 02_script.txt
├── 03_titles.md
├── 04_description.md
├── 05_thumb_text.json
├── 06_series_state.json
├── thumb_bg.png
└── thumb_final.png
```

- `slug-khong-dau`: chữ thường, không dấu tiếng Việt/Hàn, nối bằng gạch ngang,
  tối đa 5 từ, mô tả nhân vật/chủ đề chính (vd: `bac-si-canh-cua`).
- Ngoài 8 file trên, được thêm file phát sinh khi dựng giọng/sub (cùng thư mục video, tiền tố `02_`):
  `02_script/N.mp3`, `02_script_full.mp3`, `02_script_full.srt`, `02_pauses.json`,
  `02_script_full_pauses.mp3`, `02_script_sub_pauses.srt`, `voice_report.md`, `asr_report.md`...
  Không commit file mp3 (nặng, sinh lại được).
- Không thêm/bớt số thứ tự, không đổi tên file giữa các video khác nhau —
  `tools/render_thumb.py` và các script khác phụ thuộc vào tên cố định này.

## 3. Quy tắc cấu hình theo kênh

- KHÔNG hardcode giọng văn, font, màu, độ dài video trong code Python.
- Mọi thông số theo kênh đọc từ đúng `channels/<channel_id>.yaml` tương ứng.
- Thêm kênh mới = thêm 1 file YAML mới, không sửa `tools/*.py`.

## 4. Quy tắc liên tục series (continuity)

- Nếu kịch bản (`02_script.txt`) có nhắc đến tập tiếp theo (soft CTA / hard CTA),
  PHẢI ghi lại lời hứa đó vào `06_series_state.json` của chính video đó.
- Trước khi viết `01_ideas.md` cho video mới của cùng 1 kênh, PHẢI đọc
  `06_series_state.json` của video gần nhất cùng kênh để không lệch lời hứa
  đã đưa ra ("다음 이야기는 아내의 시선에서..." → tập sau phải đúng nhân vật này).

## 5. Quy tắc tiêu đề / thumbnail

- Tiêu đề: 25-45 ký tự, ưu tiên công thức đã chứng minh hiệu quả (xem
  `channels/<id>.yaml` → `title_formulas`).
- Không dùng từ khóa gây hiểu lầm y tế/tài chính nghiêm trọng (clickbait
  vượt quá nội dung thực tế của video).

## 6. Quy trình bắt buộc khi chạy `tao-video`

1. Đọc `CLAUDE.md` (file này) + `channels/<id>.yaml`
2. Đọc `06_series_state.json` của video gần nhất cùng kênh (nếu có)
3. Sinh `01_ideas.md` → `02_script.txt` → `03_titles.md` → `04_description.md`
   → `05_thumb_text.json` → `06_series_state.json`
4. Sinh ảnh nền bằng Higgsfield MCP (`generate_image`, tham số lấy từ
   `tools/make_bg.py --params`, cấu hình ở `channels/<id>.yaml` → `thumbnail_bg`),
   rồi `tools/make_bg.py --from` chuẩn hóa → `thumb_bg.png`
5. Gọi `tools/render_thumb.py` ghép chữ → `thumb_final.png`
6. Kiểm tra chéo: tiêu đề trong `03_titles.md` khớp chữ trên `thumb_final.png`
7. Sau kịch bản: viết `02_pauses.json` (kế hoạch khoảng nghỉ). Khi người dùng đã sinh giọng:
   `tools/voice_check.py` → `tools/asr_check.py` → `tools/add_pauses.py` → `tools/make_sub.py`
   (chi tiết: skill `tao-video` Bước 2.6-2.7)