---
name: tao-video
description: Lệnh điều phối duy nhất để sản xuất 1 video hoàn chỉnh (kịch bản, tiêu đề, mô tả, thumbnail) cho 1 kênh trong video-factory. Dùng khi người dùng gõ "/tao-video <channel_id> <chủ đề>" hoặc "tạo video mới cho kênh X về Y". Đọc CLAUDE.md và channels/<channel_id>.yaml trước khi sinh bất kỳ nội dung nào, tuân thủ nghiêm ngặt mọi quy tắc trong đó.
---

# /tao-video — Skill điều phối video-factory

## Input bắt buộc từ người dùng

- `channel_id`: tên file yaml trong `channels/` (không có đuôi .yaml)
- `chủ đề` hoặc `nhân vật`: 1 câu mô tả ngắn nội dung video (vd: "bác sĩ cấp cứu 30 năm, cận tử, motif cửa")
- Nếu thiếu 1 trong 2, DỪNG LẠI và hỏi lại — không tự suy đoán chủ đề.

## Bước 0 — Đọc cấu hình (bắt buộc, không được bỏ qua)

1. Đọc `CLAUDE.md` ở gốc project — đây là luật cao nhất, áp dụng cho mọi kênh.
2. Đọc `channels/<channel_id>.yaml` — nếu file không tồn tại, DỪNG LẠI và báo lỗi,
   không tự bịa cấu hình.
3. Tìm thư mục `output/` gần nhất cùng `channel_id` (so khớp qua `06_series_state.json`
   nếu có trường `channel_id` bên trong, hoặc theo tên slug liên quan).
   Nếu tìm thấy, đọc `06_series_state.json` của video đó để biết:
   - Nhân vật/lời hứa đã đưa ra cho "tập sau"
   - Danh sách nhân vật đã dùng (`characters.reused_pool` không được lặp y hệt
     mô tả đã dùng, trừ khi đúng là tập tiếp nối đã hứa)
4. Tạo thư mục output mới: `output/YYYY-MM-DD_<slug>/` theo đúng quy tắc đặt tên
   trong `CLAUDE.md` mục 2. Lấy ngày hệ thống thực tế, không bịa ngày.

## Bước 0.5 — Đọc kinh nghiệm tích lũy (bắt buộc, ngay sau Bước 0)

1. Đọc `channels/<channel_id>_learnings.md` nếu tồn tại.
2. Mục "Công thức đã xác nhận hiệu quả" → áp dụng làm khung mặc định.
3. Mục "Lỗi đã từng mắc" → coi đây là checklist PHẢI tránh, dùng lại ở
   Bước 2.5 bên dưới.
4. Mục "Hiệu suất thực tế theo từng video" → nếu đã có ≥ 3 dòng dữ liệu,
   ưu tiên công thức/nhân vật có views và sub-gained cao hơn mức trung bình
   của bảng; nếu dữ liệu quá ít, giữ nguyên công thức mặc định đã kiểm
   chứng thủ công.
5. Mục "Giả thuyết đang thử nghiệm" → nếu 1 giả thuyết đã đủ dữ liệu để
   kết luận, đề xuất cập nhật "Công thức đã xác nhận hiệu quả" cho người
   dùng duyệt (không tự sửa mục này, chỉ đề xuất).

## Bước 1 — `01_ideas.md`

**Kiểm tra trước:** nếu người dùng gọi lệnh dạng
`/tao-video <channel_id> --tiếp-tục-từ output/<slug>/01_ideas.md`
(hoặc chỉ rõ đường dẫn 1 file `01_ideas.md` đã có sẵn), ĐỌC file đó và
dùng nguyên làm ý tưởng — KHÔNG viết lại, KHÔNG tự sinh ý tưởng mới,
chuyển thẳng sang Bước 2 với đúng nhân vật/motif/vignette đã chốt trong
file đó. Đây là bàn giao từ skill `y-tuong-kich-ban`.

Nếu người dùng gọi `/tao-video` trực tiếp không kèm đường dẫn ý tưởng có
sẵn, mới viết ý tưởng thô như bên dưới:
- Nhân vật (kiểm tra chéo với `channels/<id>.yaml` → `characters.policy`:
  nếu người dùng yêu cầu dùng tên người thật có thật, DỪNG LẠI, giải thích
  vi phạm mục 1 của `CLAUDE.md`, đề xuất phương án hư cấu thay thế)
- Nghịch lý/hook chính
- Motif hình ảnh trung tâm (lấy từ `motif.core_symbol` trong yaml kênh)
- 3-5 vignette phụ dự kiến dùng ở đoạn giữa (tránh lặp vignette đã dùng ở
  video trước cùng kênh — so với `06_series_state.json` cũ nếu có)
- Câu trích dẫn "đóng đinh" dự kiến (câu sẽ dùng làm tiêu đề/thumbnail)

## Bước 2 — `02_script.txt`

**Quy tắc bắt buộc về mở đầu (áp dụng trước mọi quy tắc khác trong bước này):**
- 3 câu đầu tiên PHẢI chứa trọn vẹn nghịch lý/hook chính của nhân vật
  (nghề nghiệp + niềm tin cũ + 1 câu "twist" hé lộ sự kiện sắp xảy ra,
  chưa giải thích chi tiết — kiểu cliffhanger).
- Dòng brand intro (giới thiệu kênh, lời hứa series) CHỈ được đặt SAU
  3 câu hook này, không bao giờ đặt trước. Brand intro tối đa 2 câu.
- Tổng số từ tính từ đầu video đến hết câu hook không vượt quá ~80 từ
  tiếng Hàn (tương đương khoảng 25-30 giây ở tốc độ đọc TTS chuẩn của
  kênh) — nếu vượt, cắt bớt phần dẫn dắt, đẩy chi tiết bối cảnh xuống
  đoạn sau hook.
- Hook lấy đúng từ trường "hook_mo_dau" đã chốt sẵn trong `01_ideas.md`
  (xem Bước 1) — không tự sáng tác hook mới ở bước này.

- Viết kịch bản đầy đủ, độ dài theo `video_length_minutes` trong yaml kênh.
- Giọng văn theo đúng `tone` trong yaml kênh.
- Chèn soft CTA ở đúng vị trí `cta.soft_cta.position_pct`, hard CTA ở cuối
  theo `cta.hard_cta.rule` — PHẢI nhắc cụ thể tập sau, không dùng câu chung
  chung kiểu "구독 부탁드립니다" một mình.
- Văn bản sạch, không markdown, không chú thích trong ngoặc — sẵn sàng đưa
  thẳng vào TTS.
- Sau khi viết xong, tự kiểm tra: có câu/số liệu nào không có căn cứ trong
  `01_ideas.md` không? Nếu có, xóa hoặc làm rõ đây là hư cấu trong kịch bản.

## Bước 2.5 — Tự review kịch bản theo checklist (bắt buộc trước khi báo xong Bước 2)

Sau khi viết xong bản nháp `02_script.txt`, đọc lại toàn bộ và tự kiểm tra
từng mục sau. Với mỗi mục KHÔNG đạt, sửa trực tiếp trong văn bản rồi kiểm
tra lại — không chuyển sang Bước 3 khi còn mục chưa đạt.

**A0. Hook mở đầu (giữ chân người xem 30 giây đầu — kiểm tra ĐẦU TIÊN,
đây là lỗi đã từng mắc ở Tập 1, ưu tiên cao nhất trong toàn bộ checklist)**
- [ ] 3 câu đầu tiên chứa trọn nghịch lý + 1 câu "twist" cliffhanger, KHÔNG
      có brand intro hay bối cảnh dài dòng đứng trước
- [ ] Đếm thử số từ từ đầu đến hết câu hook — không vượt quá ~80 từ
- [ ] Đọc thử tách riêng 3 câu đầu: nếu chỉ đọc 3 câu này mà không thấy tò
      mò muốn nghe tiếp, viết lại — bắt buộc đạt mục này trước khi kiểm
      tra các mục còn lại bên dưới

**A. Trùng lặp/thừa ý**
- [ ] Không có 2 câu liền nhau nói cùng 1 ý bằng cách diễn đạt khác nhau
- [ ] Không có 2 vignette liền kề minh họa cùng 1 luận điểm
- [ ] Trong 1 chuỗi vignette (3 vignette trở lên đặt liên tiếp), không quá
      4 vignette — nếu nhiều hơn, cắt bớt hoặc gộp

**B. Chính tả và ngắt câu**
- [ ] Số + đơn vị luôn có khoảng trắng đúng chuẩn tiếng Hàn (vd "오 년",
      không viết dính "오년")
- [ ] Đọc thử thành tiếng (hoặc mô phỏng nhịp TTS) từng câu dài — nếu thấy
      ngắt gượng, kiểm tra lại dấu phẩy

**C. Nhất quán motif**
- [ ] Chỉ 1 biểu tượng trung tâm xuyên suốt toàn bộ kịch bản (lấy từ
      `motif.core_symbol` trong yaml kênh), không trộn lẫn biểu tượng khác
- [ ] Không dùng biểu tượng liệt kê trong `motif.avoid_symbols`

**D. An toàn nội dung**
- [ ] Không có tên người thật, có thể xác định danh tính cụ thể, gán vào
      nhân vật kể chuyện
- [ ] Không có số liệu/thống kê/trích dẫn khoa học không có căn cứ trong
      `01_ideas.md`

**E. CTA**
- [ ] Soft CTA nằm trong khoảng `cta.soft_cta.position_pct`, không quá 3
      câu, không làm gián đoạn mạch cảm xúc đang lên
- [ ] Hard CTA ở cuối nhắc cụ thể nội dung tập sau, không chỉ nói chung
      chung "구독해주세요"

**F. Đối chiếu lỗi cũ (từ `channels/<id>_learnings.md` → "Lỗi đã từng mắc")**
- [ ] Rà lại từng lỗi đã liệt kê trong file learnings, xác nhận kịch bản
      lần này không mắc lại đúng lỗi đó

Nếu mọi mục đều đạt, mới được coi `02_script.txt` là bản hoàn chỉnh và
chuyển sang Bước 3.

## Bước 3 — `03_titles.md`

- Sinh 5-8 phương án theo `title_formulas.preferred` trong yaml kênh.
- Loại bỏ phương án nào rơi vào `title_formulas.avoid`.
- Đánh dấu rõ 1 phương án đề xuất chính (⭐), kèm 1-2 câu lý do ngắn gọn.
- Giới hạn 25-45 ký tự mỗi tiêu đề theo `CLAUDE.md` mục 5.

## Bước 4 — `04_description.md`

- 2 dòng hook đầu (hiện trước nút "thêm")
- Đoạn tóm tắt ngắn
- Dòng công bố nội dung sáng tác — LẤY NGUYÊN VĂN từ
  `description_template.disclosure_line` trong yaml kênh, không viết lại,
  không rút gọn, không di chuyển xuống dưới hashtag.
- Dòng giới thiệu series + CTA
- Hashtag: lấy từ `keywords_default` trong yaml kênh + 2-3 từ khóa riêng
  của chủ đề video này

## Bước 5 — `05_thumb_text.json`

Xuất đúng schema sau để `tools/render_thumb.py` đọc được:

```json
{
  "main_text": "câu ngắn nhất, mạnh nhất trên thumbnail (≤ 14 ký tự)",
  "sub_text": "dòng phụ bổ sung ngữ cảnh (≤ 20 ký tự, có thể để trống)",
  "font_title": "<lấy từ channels/<id>.yaml → fonts.title_kr>",
  "color_main": "<lấy từ channels/<id>.yaml → color_palette.gold>",
  "color_bg_overlay": "<lấy từ channels/<id>.yaml → color_palette.navy>",
  "layout": "<copy nguyên khối channels/<id>.yaml → thumbnail_layout>"
}
```

`main_text` PHẢI là 1 cụm rút gọn từ tiêu đề đã chọn ở Bước 3 (đánh dấu ⭐),
không được bịa nội dung mới không có trong tiêu đề.

Khi `layout.text_side = "left"` (chữ nằm bên trái, nhân vật bên phải):
- `sub_text` (chữ trắng, nhỏ, ở trên) = vế "ai" của tiêu đề — nghịch lý nhân vật.
  Nếu dài hơn ~10 ký tự, tự ngắt `\n` ở chỗ ngắt nghĩa để không có 1 từ mồ côi ở dòng 2.
- `main_text` (chữ vàng, to, ở dưới) = vế "chuyện gì/cái gì" gây tò mò nhất, có
  thể ngắt dòng bằng `\n` ở chỗ ngắt nghĩa tự nhiên (tối đa 2 dòng).

### Chế độ nhiều dòng — BẮT BUỘC khi yaml kênh có `thumbnail_text_style`

Kiểu thumbnail viral của ngách (mỗi dòng 1 màu/kiểu). Vẫn giữ `main_text`/`sub_text`
ở trên (để kiểm tra chéo), nhưng thêm các trường sau — có `lines` thì
`render_thumb.py` vẽ theo `lines`:

```json
{
  "lines": [
    {"text": "<dòng mồi, ≤ 7 ký tự>", "style": "top"},
    {"text": "<cụm khóa, ≤ 7 ký tự>", "style": "box"},
    {"text": "<câu hỏi/cú chốt, ≤ 7 ký tự>", "style": "hero"}
  ],
  "caption": "<tùy chọn, dòng nhỏ: vd '성경의 대답 | 은도 목사'>",
  "font_title": "<channels/<id>.yaml → thumbnail_text_style.font>",
  "styles": "<copy nguyên khối channels/<id>.yaml → thumbnail_text_style.styles>"
}
```

- Mọi chữ trong `lines` + `caption` PHẢI lấy từ tiêu đề ⭐, không bịa thêm.
- Tuân theo `thumbnail_text_style.line_rules` trong yaml kênh.
- **Chọn variant bố cục** (nếu yaml có `thumbnail_text_style.layout_variants`):
  1. Đọc `thumbnail.variant` và `thumbnail.first_line_keyword` trong
     `06_series_state.json` của video gần nhất cùng kênh.
  2. Chọn variant có `use_when` khớp công thức tiêu đề ⭐, KHÁC variant tập trước.
     Nếu tiêu đề ⭐ chỉ hợp đúng variant tập trước → dùng tiêu đề phương án
     khác trong `03_titles.md` (ghi rõ lý do), hoặc báo người dùng chọn.
  3. `lines[].style` lấy đúng theo `pattern` của variant (cùng thứ tự).
  4. Dòng đầu tiên không mở bằng cùng từ khóa với `first_line_keyword` tập trước.
- Chạy `render_thumb.py` xong, nếu log có "Font không có glyph" → thay ký tự đó
  (vd `·` `—` `…` → `|` `-`) rồi render lại.

## Bước 6 — `06_series_state.json`

```json
{
  "channel_id": "<channel_id>",
  "episode_date": "YYYY-MM-DD",
  "episode_title": "<tiêu đề đã chốt>",
  "characters_used": ["<danh sách nhân vật xuất hiện>"],
  "promise_for_next_episode": "<nội dung đã hứa trong hard CTA, nguyên văn>",
  "vignettes_used": ["<danh sách vignette phụ đã dùng, để tránh lặp>"],
  "thumbnail": {
    "subject": "<mô tả nhân vật>",
    "subject_ref_job_id": "<job_id ảnh nền Higgsfield>",
    "variant": "<A/B/C — variant bố cục chữ đã dùng, nếu kênh có layout_variants>",
    "first_line_keyword": "<từ khóa chính của dòng chữ đầu tiên>",
    "bg_variation": {"time": "...", "season": "...", "object": "...", "expression": "..."}
  }
}
```

## Bước 7 — Sinh ảnh

Ảnh nền sinh bằng **Higgsfield MCP**. Chỉ sinh NỀN, không chữ — chữ do Pillow
xử lý ở bước sau để đảm bảo font thật, không lỗi chữ Hàn/Việt do model ảnh vẽ sai.
Model và tham số lấy từ `channels/<channel_id>.yaml` → `thumbnail_bg`, không tự chọn.

1. Soạn 2 mô tả tiếng Anh từ `01_ideas.md` + `02_script.txt` (không bịa chi tiết
   không có trong kịch bản):
   - `--subject`: người kể chuyện của tập (tuổi, nghề, trang phục đúng vai trong
     truyện, cảm xúc ở khoảnh khắc cao trào). Nhân vật PHẢI hư cấu — KHÔNG ghi tên,
     KHÔNG mô tả giống bất kỳ người có thật nào (mục sư, bác sĩ, người nổi tiếng),
     kể cả khi người dùng yêu cầu "giống mục sư X" → giải thích mục 1 `CLAUDE.md`,
     chỉ lấy phong thái chung.
   - `--scene`: bối cảnh nền của khoảnh khắc then chốt trong kịch bản, có motif
     `motif.core_symbol`, không có biểu tượng trong `motif.avoid_symbols`.
   - `--ref`: nếu nhân vật đã xuất hiện trên thumbnail tập trước (tra
     `thumbnail.subject_ref_job_id` trong `06_series_state.json` cũ), truyền job_id
     đó để giữ nguyên gương mặt. Nhân vật mới → bỏ trống.

   Dựng tham số:
   `python tools/make_bg.py --channel <channel_id> --params --subject "..." --scene "..." [--ref <job_id>]`
   → in ra JSON (`model`, `aspect_ratio`, `count`, `prompt`, tham số riêng của model).
2. Gọi tool `generate_image` của Higgsfield MCP với `params` = NGUYÊN VĂN JSON ở
   trên — không sửa prompt, không đổi model.
   - Nếu tool trả về `unlim_choice`: hỏi người dùng dùng lượt miễn phí hay credit,
     rồi gọi lại kèm `use_unlim` theo câu trả lời.
   - Nếu có `recovery_tool`: gọi ngay theo hướng dẫn của tool.
   - Nếu job chưa xong: `jobs_wait` với job_id đã trả về (không gửi lại request
     khi chưa biết kết quả job cũ). Lấy URL ảnh kết quả.
   - Mở ảnh ra xem. Nếu ảnh có chữ/logo, vi phạm `motif.avoid_symbols`, hoặc nhân
     vật lấn sang nửa trái (chỗ đặt chữ): sinh lại 1 lần với mô tả rõ hơn; vẫn lỗi
     thì báo người dùng, không tự sinh tiếp.
   - Ghi job_id ảnh đã dùng vào `06_series_state.json` →
     `"thumbnail": {"subject": "<mô tả nhân vật>", "subject_ref_job_id": "<job_id>"}`
     để tập sau dùng lại gương mặt qua `--ref`.
   - **Nhân vật cố định** (nếu yaml có khối `character.current`):
     - KHÔNG truyền `--ref` — `make_bg.py` tự dùng `character.current.ref_job_id` và tự
       chèn mô tả gương mặt vào prompt. `--subject` chỉ mô tả tư thế/biểu cảm/đồ vật,
       không mô tả lại tóc/mặt/tuổi.
     - Mở ảnh kết quả, so với `character.current.local_master`: nếu gương mặt lệch rõ
       (tóc, lông mày, đeo kính...), sinh lại 1 lần; vẫn lệch thì báo người dùng.
     - Ghi `thumbnail.character_id` = `character.current.id` vào `06_series_state.json`
       (make_bg.py đếm trường này để biết đã dùng bao nhiêu video).
     - Nếu `make_bg.py` in "CẢNH BÁO: nhân vật ... đã đủ N/10 video" → DỪNG, báo người
       dùng và hỏi có tạo nhân vật mới không. Nếu đồng ý: sinh ảnh chân dung gốc mới
       (chính diện, ngang ngực, nền xám trơn, hư cấu hoàn toàn, khác nhân vật cũ và khác
       mọi người thật) → tải về `characters/<channel_id>/<id_mới>/master.png` → chuyển
       khối `current` cũ xuống `character.history` → điền khối `current` mới.
     - Nếu Higgsfield báo lỗi không tìm thấy `ref_job_id` (hết hạn): `media_upload`
       lại file `local_master`, điền media_id mới vào `ref_job_id`, chạy lại.
   - Nếu yaml có `thumbnail_bg.variation_rules`: khi soạn `--subject`/`--scene` ở
     bước 1, đọc `thumbnail.bg_variation` của tập trước và đổi thời điểm / đồ vật /
     biểu cảm theo đúng các rule đó (mùa khớp ngày đăng), rồi ghi lựa chọn mới vào
     `thumbnail.bg_variation`.
3. Chuẩn hóa về 1280x720 và lưu đúng tên file:
   `python tools/make_bg.py --from "<url_ảnh_higgsfield>" --out output/<slug>/thumb_bg.png`
4. Chạy `python tools/render_thumb.py --json output/<slug>/05_thumb_text.json
   --bg output/<slug>/thumb_bg.png --out output/<slug>/thumb_final.png`

## Bước 8 — Kiểm tra chéo cuối cùng (bắt buộc trước khi báo hoàn thành)

- [ ] Tên file đúng 100% theo `CLAUDE.md` mục 2
- [ ] `main_text` trong thumbnail khớp nghĩa với tiêu đề ⭐ đã chọn
- [ ] Dòng công bố sáng tác có mặt nguyên văn trong `04_description.md`
- [ ] Không có tên người thật cụ thể nào trong `02_script.txt`
- [ ] `06_series_state.json` đã ghi lại lời hứa tập sau (nếu kịch bản có hứa)

Nếu bất kỳ mục nào không đạt, KHÔNG báo hoàn thành — sửa lại trước.

## Bước 9 — Đóng vòng lặp học hỏi (nhắc người dùng, không tự động)

Sau khi báo hoàn thành 8 bước trên, luôn kết thúc bằng lời nhắc:

> "Sau khi video này lên sóng và có số liệu (48h–7 ngày), hãy quay lại điền
> vào bảng 'Hiệu suất thực tế' trong `channels/<channel_id>_learnings.md`.
> Nếu phát hiện lỗi mới trong quá trình dựng/đăng video (không phải lỗi đã
> liệt kê sẵn), thêm luôn vào mục 'Lỗi đã từng mắc' để video sau tránh."

Đây là bước con người phải làm tay (nhập số liệu thật từ YouTube Studio) —
`tao-video` không tự bịa số liệu để điền vào bảng này.

## Khi nào phải dừng và hỏi người dùng thay vì tự quyết

- Thiếu `channel_id` hoặc file yaml tương ứng không tồn tại
- Người dùng yêu cầu dùng tên/trải nghiệm của người có thật cụ thể
- Chủ đề mâu thuẫn trực tiếp với `title_formulas.avoid` hoặc
  `motif.avoid_symbols` trong yaml kênh mà không có lý do rõ ràng được nêu
- Tìm thấy `06_series_state.json` cũ có lời hứa chưa thực hiện nhưng chủ đề
  video mới không khớp lời hứa đó — hỏi xác nhận có cố ý bỏ lời hứa cũ không