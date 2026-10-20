# Setup kênh eundo-malsseum (soạn 2026-10-15)

Lý do: kênh YouTube đang mang tên "열리는 문 | 간증" (định vị lời chứng) nhưng nội dung là bài giảng.
Đổi đồng thời tên + handle + ảnh đại diện + banner + About, rồi đo lại sau 10-14 ngày (≥ 3 video mới).
YouTube giới hạn số lần đổi tên/handle (~2 lần/14 ngày) → chốt trước khi đổi.

## 1. Tên kênh (chọn 1)

| # | Tên | Ghi chú |
|---|---|---|
| ⭐ | 서재의 등불 | Ngắn, hiện đủ trên điện thoại, khớp motif ngọn đèn của kênh |
| 2 | 서재의 등불 · 말씀 쉼터 | Có từ khóa "말씀" giúp tìm kiếm; hơi dài |
| 3 | 노년의 말씀 쉼터 | Nêu rõ đối tượng 60+; ít nét riêng |

- KHÔNG đặt tên có "신성종": kênh không do người thật làm/bảo chứng (xem dòng công bố), tên kênh có thể bị báo mạo danh.
- KHÔNG dùng "평안의 서재" (tên kênh đối thủ).

## 2. Handle (kiểm tra còn trống trong YouTube Studio → Tùy chỉnh → Thông tin cơ bản)

1. `@서재의등불`
2. `@seojae-deungbul`
3. `@말씀쉼터등불`

Handle 3-30 ký tự. Nếu cả 3 đã có người dùng, thêm số hoặc "-yoksa" thay vì dùng tên người thật.

## 3. Ảnh đại diện / banner

- Avatar: ngọn đèn bàn ánh hổ phách trên nền nâu sẫm (#2B1D14 / #E8A33D), không dùng mặt người.
- Banner 2560x1440 (vùng an toàn giữa 1546x423): cửa sổ thư phòng + cây hồng, chữ "서재의 등불" + dòng phụ "노년의 신앙 · 천국 · 사별 위로".

## 4. Mô tả kênh (About) — dán vào Studio

```
서재의 등불

작은 서재의 등불 아래에서, 노년의 성도님들께 위로의 말씀을 전합니다.
천국과 부활, 먼저 떠난 가족에 대한 그리움, 혼자 남은 날들의 외로움.
쉽게 말하기 어려운 질문을 성경의 말씀으로 천천히 함께 읽습니다.

📅 업로드: 매주 화·목·토 새벽
🕯 이런 분께 권합니다: 사별 후 위로가 필요하신 분, 노년의 신앙을 돌아보고 싶으신 분

※ 안내 (꼭 읽어 주세요)
- 이 채널의 설교 속 일화와 대화는 신앙적 메시지 전달을 위해 창작·각색된 내용이며, 실제 있었던 사실이나 특정 인물의 실제 발언이 아닙니다.
- 영상의 음성은 AI 음성이며, 대본은 창작입니다. 영상에 언급되는 신성종 목사님은 이 채널을 제작·감수·출연하거나 보증하지 않으셨습니다.
- 교단마다 견해가 갈리는 주제는 어느 한 쪽이 옳다고 판정하지 않고 균형 있게 다룹니다. 성경 구절은 개역개정 본문을 따릅니다.
- 이 채널은 의학·심리 상담을 대신하지 않습니다. 사별이나 우울로 일상이 힘드시다면 가까운 사람, 의사·상담 전문가에게 이야기하시고, 살고 싶지 않다는 생각이 들면 자살예방 상담전화 109에 도움을 청해 주십시오.

구독하시면 다음 말씀을 가장 먼저 만나실 수 있습니다.
```

(Điều chỉnh dòng "업로드" cho đúng lịch thật trước khi dán. Dòng công bố khớp với mẫu trong 04_description.md.)

## 5. Việc kèm theo trong Studio

- Cài đặt kênh → Nội dung → Quốc gia: Hàn Quốc; Từ khóa kênh: 설교, 노년 신앙, 천국, 사별 위로.
- Video mặc định: bật "Nội dung bị thay đổi hoặc tổng hợp"; danh mục: Con người & Blog hoặc Giáo dục.
- Sau khi dán About: chụp màn hình lưu vào `characters/`-ngoài, rồi điền bằng chứng vào `channels/eundo-malsseum.yaml` (CLAUDE.md mục 1) và điền handle thật vào trường `handle`.
