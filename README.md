# video-factory

Sinh nội dung + thumbnail cho video YouTube theo cấu hình từng kênh (`channels/*.yaml`).

## Cài đặt

```bash
pip install -r requirements.txt
```

Ảnh nền thumbnail được sinh qua **Higgsfield MCP** (kết nối bằng `/mcp` trong
Claude Code), không cần API key. Model/tham số ảnh cấu hình theo kênh ở
`channels/<id>.yaml` → `thumbnail_bg`.

Đặt file font (`.ttf`/`.otf`) vào `fonts/`, ví dụ `NotoSerifKR-Bold.ttf`. Nếu thiếu,
`render_thumb.py` sẽ cảnh báo và dùng font hệ thống.

## Dùng trong Claude Code

Mở project trong Claude Code rồi gõ:

```
/tao-video mun-yeolda
/tao-video mun-yeolda Tập 2: câu chuyện từ góc nhìn người vợ
```

Kết quả nằm trong `output/YYYY-MM-DD_slug/` (xem quy tắc trong `CLAUDE.md`).

## Chạy tay từng công cụ

```bash
python tools/make_bg.py --channel mun-yeolda --params                # in JSON tham số cho Higgsfield generate_image
python tools/make_bg.py --from <url_ảnh_higgsfield> --out output/test/thumb_bg.png   # chuẩn hóa 1280x720
python tools/render_thumb.py --json output/test/05_thumb_text.json \
    --bg output/test/thumb_bg.png --out output/test/thumb_final.png
```

Thêm kênh mới = thêm 1 file `channels/<channel_id>.yaml`, không sửa code.
