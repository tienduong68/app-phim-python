# 🎬 Phim Ông Tiến

Ứng dụng xem phim desktop viết bằng **Python + Flet**, sử dụng API từ [phimapi.com](https://phimapi.com).

## 📥 Tải về & Sử dụng ngay (Windows)

> Không cần cài Python hay bất kỳ thứ gì — tải về và chạy luôn!

➡️ **[Tải PhimOngTien.exe tại đây (GitHub Releases)](https://github.com/tienduong68/app-phim-python/releases/latest)**

### ⚠️ Windows báo "isn't commonly downloaded"?

Đây là cảnh báo bình thường với phần mềm chưa được ký số. Để chạy app:

**Cách 1 — Qua trình duyệt khi tải:**
1. Click **"..."** (ba chấm) cạnh file vừa tải
2. Chọn **Keep** → **Show more** → **Keep anyway**

**Cách 2 — Qua Windows Explorer:**
1. Chuột phải vào file `.exe` → **Properties**
2. Ở dưới cùng, check vào ô **Unblock**
3. Click **OK** rồi mở file bình thường


## ✨ Tính năng

- 🆕 Xem phim mới cập nhật theo thời gian thực
- 🎬 Lọc theo loại: Phim Lẻ, Phim Bộ, Hoạt Hình, TV Shows, Vietsub
- 🏷️ Lọc theo thể loại (Hành Động, Tình Cảm, Kinh Dị...)
- 🌏 Lọc theo quốc gia (Hàn Quốc, Trung Quốc, Âu Mỹ...)
- 📅 Lọc theo năm phát hành (2010 → nay)
- 🔍 Tìm kiếm phim theo tên
- ▶️ Xem phim ngay trong trình duyệt (HLS player)
- 📄 Phân trang

## 🛠️ Cài đặt & Chạy

### Yêu cầu
- Python 3.10+
- pip

### Cài dependencies
```bash
pip install -r requirements.txt
```

### Chạy app
```bash
python app_phim.py
```

## 📦 Build thành file .exe (Windows)

```bash
pip install flet
flet pack app_phim.py --name "PhimOngTien"
```

File `.exe` sẽ nằm trong thư mục `dist/`.

## 🔌 API sử dụng

| Endpoint | Mô tả |
|----------|-------|
| `GET /danh-sach/phim-moi-cap-nhat` | Phim mới cập nhật |
| `GET /v1/api/danh-sach/phim-le` | Phim lẻ |
| `GET /v1/api/danh-sach/phim-bo` | Phim bộ |
| `GET /v1/api/danh-sach/hoat-hinh` | Hoạt hình |
| `GET /v1/api/danh-sach/tv-shows` | TV Shows |
| `GET /v1/api/danh-sach/phim-vietsub` | Phim Vietsub |
| `GET /v1/api/tim-kiem?keyword=...` | Tìm kiếm |
| `GET /v1/api/the-loai/{slug}` | Lọc thể loại |
| `GET /v1/api/quoc-gia/{slug}` | Lọc quốc gia |
| `GET /v1/api/nam/{year}` | Lọc theo năm |
| `GET /phim/{slug}` | Chi tiết + link xem |

Nguồn API: [phimapi.com](https://phimapi.com) — [phimimg.com](https://phimimg.com) (CDN ảnh)

## 📄 License

MIT
