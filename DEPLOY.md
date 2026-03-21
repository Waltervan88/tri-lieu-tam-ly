# Tri-Lieu-Tam-Ly — Hướng Dẫn Deploy Lên Streamlit Cloud

## 1 — Chuẩn bị

### API Key Gemini
1. Vào [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Click **"Create API Key"** → Copy key (bắt đầu `AIza...`)

### Repo đã có sẵn
```
https://github.com/Waltervan88/tri-lieu-tam-ly
```
Mỗi khi có thay đổi mới:
```bash
cd "Tri Lieu Tam Ly V0/tri-lieu"
git add . && git commit -m "mô tả thay đổi"
git push
```

---

## 2 — Deploy Lên Streamlit Cloud

### Bước 1
Truy cập [share.streamlit.io](https://share.streamlit.io) → Đăng nhập GitHub → **New app**

### Bước 2 — Điền thông tin
```
Repository:    Waltervan88/tri-lieu-tam-ly
Branch:       main
Main file:    app/main.py
```

### Bước 3 — Advanced Settings (QUAN TRỌNG)
Click **Advanced settings** (kéo xuống dưới):
```
Python version:      3.13
Requirements path:    app/requirements.txt
```

### Bước 4 — Secrets
Trong cùng phần Advanced settings, phần **Secrets**, thêm:
```toml
GEMINI_API_KEY = "AIzaSy..."      # ← paste key từ AI Studio
GEMINI_MODEL   = "gemini-2.0-flash"
```

### Bước 5
Click **Deploy!** → Đợi 3-5 phút.

---

## 3 — Test Sau Deploy

```
Link app: https://waltervan88-tri-lieu-tam-ly.streamlit.app
Expert:   expert@demo.local / expert123
Admin:    admin@demo.local  / admin123
```

**Test Gate D:** Nhập **"Tôi muốn tự tử"** → Hệ thống phải hiển thị thông điệp an toàn.

---

## 4 — Share Cho Stakeholder

**Link app:** (sẽ có dạng)
```
https://waltervan88-tri-lieu-tam-ly.streamlit.app
```

**Tài khoản demo:**
```
Email:    stakeholder@demo.local
Password: demo123
```

---

## Troubleshooting

| Lỗi | Cách fix |
|------|---------|
| Không thấy Requirements path | Advanced settings → cuộn xuống kỹ |
| "Module not found" | Đảm bảo Requirements path = `app/requirements.txt` |
| "Model not found" (AI Studio) | **BỎ QUA** — AI Studio không chạy được Streamlit code |
| API lỗi trên app | Kiểm tra GEMINI_API_KEY đúng trong Secrets |

---

## Chi Phí: $0/tháng
- Streamlit Cloud (repo public): **Miễn phí**
- Gemini 2.0 Flash API: **Miễn phí** (1,500 req/ngày)
- GitHub: **Miễn phí**
