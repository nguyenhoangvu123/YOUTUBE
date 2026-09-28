# video-factory — Nội quy chung

Đây là nội quy bắt buộc cho mọi kênh, mọi video sinh ra từ hệ thống này.
Skill `tao-video` PHẢI đọc và tuân thủ file này trước khi sinh bất kỳ nội dung nào.

## 1. Quy tắc chống bịa đặt / không trung thực

- KHÔNG bịa số liệu, thống kê, trích dẫn khoa học/y tế/lịch sử nếu không có
  nguồn trong `01_ideas.md` hoặc tài liệu người dùng cung cấp.
- KHÔNG gán tên, chức danh, hoặc trải nghiệm hư cấu cho một người có thật,
  có tên tuổi cụ thể, còn sống hoặc mới mất gần đây. Nhân vật kể chuyện
  PHẢI là hư cấu hoàn toàn, hoặc ẩn danh hóa (vd: "một mục sư", "một bác sĩ",
  không dùng tên riêng thật của người có thật).
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