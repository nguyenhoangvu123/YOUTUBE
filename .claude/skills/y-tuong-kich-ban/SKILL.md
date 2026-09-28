---
name: y-tuong-kich-ban
description: Sinh 3 phương án ý tưởng video (01_ideas.md) cho 1 kênh, học từ toàn bộ video trước đó của cùng kênh để đảm bảo đồng bộ giọng văn và không lặp nhân vật/vignette đã dùng. Dùng khi người dùng gõ "/y-tuong <channel_id> [gợi ý chủ đề tuỳ chọn]". KHÔNG viết kịch bản đầy đủ — chỉ dừng ở bước ý tưởng, chờ người dùng chọn 1 trong 3 phương án trước khi bàn giao cho skill tao-video.
---

# /y-tuong — Skill lên ý tưởng có học hỏi

## Cú pháp gọi lệnh cố định (dùng đúng cú pháp này để tránh Claude Code hiểu sai ý)

```
/y-tuong <channel_id>
/y-tuong <channel_id> <gợi ý chủ đề/nhân vật>
```

Ví dụ:
```
/y-tuong mun-yeolda
/y-tuong mun-yeolda nhân vật là giáo viên, chủ đề mất học trò
```

Nếu người dùng gõ câu tự do kiểu "tạo ý tưởng video mới cho kênh X về Y"
mà không theo đúng cú pháp trên, TỰ ĐỘNG hiểu là lệnh `/y-tuong <X> <Y>` —
không cần người dùng nhớ chính xác cú pháp, nhưng khi thực thi PHẢI tuân
thủ quy trình bên dưới y hệt như gọi đúng cú pháp.

## Bước 1 — Thu thập ngữ cảnh (bắt buộc, không được bỏ qua)

1. Đọc `CLAUDE.md` (luật chung).
2. Đọc `channels/<channel_id>.yaml`. Nếu không tồn tại, DỪNG LẠI, báo lỗi,
   không tự bịa cấu hình.
3. Đọc `channels/<channel_id>_learnings.md` nếu tồn tại — lấy toàn bộ
   3 mục: "Công thức đã xác nhận hiệu quả", "Lỗi đã từng mắc",
   "Giả thuyết đang thử nghiệm".
4. Quét toàn bộ thư mục `output/*/` — với mỗi thư mục con có
   `06_series_state.json` mang đúng `channel_id` này, đọc ra:
   - `characters_used` → gộp thành 1 danh sách "nhân vật đã dùng"
   - `vignettes_used` → gộp thành 1 danh sách "vignette đã dùng"
   - `promise_for_next_episode` của video GẦN NHẤT (theo `episode_date`
     mới nhất) → đây là lời hứa CHƯA THỰC HIỆN nếu chưa có video nào sau
     đó nhắc lại đúng nội dung này
5. Nếu bước 4 tìm thấy 1 lời hứa chưa thực hiện VÀ người dùng không gõ
   gợi ý chủ đề nào đi ngược lại lời hứa đó → ưu tiên tuyệt đối dùng đúng
   nhân vật/chủ đề đã hứa cho phương án ý tưởng đầu tiên.
   Nếu người dùng gõ gợi ý chủ đề khác hẳn lời hứa → hỏi xác nhận:
   "Tập trước đã hứa kể chuyện [X] ở tập này — bạn có muốn tạm gác lời
   hứa đó để làm chủ đề mới [Y] không, hay ưu tiên giữ đúng lời hứa?"
   rồi chờ người dùng trả lời trước khi đi tiếp.

## Bước 2 — Sinh 3 phương án ý tưởng (không phải 1, không phải 5+)

Mỗi phương án PHẢI có đủ các trường sau, viết ngắn gọn (mỗi phương án
không quá 150 từ):

```
### Phương án [1/2/3]: <tên ngắn gọi nhớ>

- Nhân vật: <nghề nghiệp/vai trò, KHÔNG dùng tên người thật có thật>
- Nghịch lý mở đầu: <1 câu>
- Hook mở đầu (viết đúng nguyên văn, 2-3 câu, sẽ dùng làm 3 câu đầu tiên
  của kịch bản, ĐỨNG TRƯỚC brand intro): <nghề nghiệp + niềm tin cũ + 1
  câu "twist" hé lộ sự kiện sắp xảy ra nhưng CHƯA giải thích chi tiết —
  kiểu cliffhanger. Tổng không quá ~80 từ tiếng Hàn (~25-30 giây TTS)>
- Motif hình ảnh: <lấy từ motif.core_symbol trong yaml, hoặc đề xuất biến
  thể mới nếu phù hợp — nêu rõ nếu là biến thể mới>
- Câu trích dẫn đóng đinh dự kiến: <1 câu ngắn>
- 3 vignette phụ dự kiến: <liệt kê>
- Vì sao KHÁC với các video trước: <so sánh trực tiếp với danh sách nhân
  vật/vignette đã dùng ở Bước 1.4 — nêu rõ điểm khác biệt, không chỉ nói
  chung chung "mới lạ">
- Rủi ro cần lưu ý (nếu có): <vd: gần giống vignette video X, cần điều
  chỉnh góc nào>

**Bài test bắt buộc trước khi đưa phương án này ra:** đọc riêng phần "Hook
mở đầu" — nếu chỉ đọc đúng đoạn đó mà không thấy tò mò muốn nghe tiếp,
viết lại hook trước khi đưa phương án vào danh sách trình bày.
```

Ít nhất 1 trong 3 phương án PHẢI thử nghiệm biến thể so với công thức
mặc định (nhân vật khác nhóm nghề đã dùng, hoặc góc tiếp cận motif khác)
— để có dữ liệu mới cập nhật vào learnings.md sau này, không lặp lại y
hệt công thức cũ ở cả 3 phương án.

## Bước 3 — Trình bày và chờ người dùng chọn

Sau khi đưa ra 3 phương án, hỏi rõ:
"Bạn chọn phương án nào (1/2/3), hay muốn kết hợp chi tiết từ nhiều
phương án?" — KHÔNG tự ý chọn thay người dùng, KHÔNG tự động chuyển sang
viết kịch bản đầy đủ khi chưa có xác nhận.

## Bước 4 — Chốt `01_ideas.md`

Sau khi người dùng chọn, viết file hoàn chỉnh vào:
`output/YYYY-MM-DD_<slug>/01_ideas.md`

(Tạo thư mục mới theo đúng quy tắc đặt tên trong `CLAUDE.md` mục 2 —
lấy ngày hệ thống thực tế.)

Nội dung file gồm đúng phương án đã chọn, viết đầy đủ chi tiết hơn bản
tóm tắt ở Bước 2 (không giới hạn 150 từ nữa), cộng thêm 1 dòng cuối:

```
[Nguồn: sinh bởi skill y-tuong-kich-ban, đã đối chiếu N video trước
của kênh <channel_id>, không trùng nhân vật/vignette đã dùng]
```

## Bước 5 — Bàn giao

Báo cho người dùng:
"Đã lưu `01_ideas.md`. Để viết kịch bản đầy đủ từ ý tưởng này, gõ:
`/tao-video <channel_id> --tiếp-tục-từ output/<slug>/01_ideas.md`"

KHÔNG tự động gọi tiếp skill `tao-video` — đây là ranh giới cứng giữa
2 skill, tách biệt để người dùng luôn có điểm dừng kiểm tra trước khi
tốn công viết cả kịch bản dài.

## Khi nào dừng và hỏi thay vì tự quyết

- Không tìm thấy `channels/<channel_id>.yaml`
- Lời hứa tập trước (Bước 1.5) mâu thuẫn với gợi ý chủ đề người dùng đưa ra
- Không quét được thư mục `output/` nào (kênh hoàn toàn mới, chưa có video
  nào) → vẫn tiếp tục bình thường, chỉ báo rõ "đây là video đầu tiên của
  kênh, chưa có dữ liệu để đối chiếu trùng lặp"