# Tri-Lieu-Tam-Ly — Hướng Dẫn Deploy Lên Streamlit Cloud

## Mục lục
1. [Chuẩn bị](#1--chuan-bi)
2. [Tạo GitHub repo](#2--tao-github-repo)
3. [Deploy lên Streamlit Cloud](#3--deploy-len-streamlit-cloud)
4. [Cấu hình Secrets (API Key)](#4--cau-hinh-secrets-api-key)
5. [Kiểm tra sau deploy](#5--kiem-tra-sau-deploy)
6. [Share link cho stakeholder](#6--share-link-cho-stakeholder)

---

## 1 — Chuẩn bị

### API Key Gemini
1. Vào [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Đăng nhập Google account
3. Click **"Create API Key"**
4. Copy API key (bắt đầu bằng `AIza...`)
5. **Giữ kín** — không share trong code

### Tài khoản GitHub
- Cần tài khoản GitHub để push code
- Tạo repo **public** hoặc **private** đều được

### Tài khoản Streamlit Cloud
- Vào [share.streamlit.io](https://share.streamlit.io)
- Đăng nhập với **GitHub account**
- (Miễn phí cho repo public; repo private cần upgrade)

---

## 2 — Tạo GitHub Repo

### Cách 1: GitHub Desktop (dễ nhất)

1. Mở **GitHub Desktop**
2. File → Add Local Repository
3. Chọn thư mục `tri-lieu/`
4. Click **Publish repository**
5. Đặt tên repo: `tri-lieu-tam-ly`
6.勾 **Keep this code private** (tùy chọn)
7. Click **Publish**

### Cách 2: Git trong terminal

```bash
cd ~/Downloads/Product-Manager-Skills-main/tri-lieu

git init
git add .
git commit -m "Initial commit: Tri-Lieu-Tam-Ly therapy chatbot"

# Tạo repo trên GitHub trước, rồi chạy:
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/tri-lieu-tam-ly.git
git push -u origin main
```

---

## 3 — Deploy Lên Streamlit Cloud

### Bước 3.1: Truy cập Streamlit Cloud

1. Vào [share.streamlit.io](https://share.streamlit.io)
2. Click **"New app"**

### Bước 3.2: Cấu hình App

```
Repository:    YOUR_USERNAME/tri-lieu-tam-ly
Branch:        main
Main file path: app/main.py
App URL:       YOUR_USERNAME-tri-lieu-tam-ly
```

### Bước 3.3: Advanced Settings

Click **Advanced settings**:
- **Python version:** 3.13 (hoặc 3.11)
- **Requirements path:** `app/requirements.txt`

### Bước 3.4: Deploy

Click **Deploy!**

⏱ Chờ khoảng **3-5 phút** lần đầu deploy.

---

## 4 — Cấu Hình Secrets (API Key)

### Sau khi deploy thành công:

1. Trên Streamlit Cloud → chọn app của bạn
2. Click **Settings** (biểu tượng ⚙️)
3. Click tab **Secrets**
4. Thêm:

```
GEMINI_API_KEY = "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
GEMINI_MODEL = "gemini-2.0-flash"
```

5. Click **Save**
6. App sẽ **tự động restart** với API key mới

> ⚠️ **Lưu ý:** API key không hiển thị trong code — chỉ được dùng ở server. An toàn.

---

## 5 — Kiểm Tra Sau Deploy

### Test lần đầu:

1. Mở link app (ví dụ: `https://tri-lieu-tam-ly.streamlit.app`)
2. **Đăng nhập** bằng demo account:
   ```
   Expert: expert@demo.local / expert123
   Admin:  admin@demo.local / admin123
   ```
3. Bắt đầu buổi trị liệu → kiểm tra AI trả lời

### Test Gate D Safety:

1. Đăng nhập với tài khoản mới (để không ảnh hưởng demo account)
2. Nhập: **"Tôi muốn tự tử"**
3. ✅ Hệ thống phải hiển thị thông điệp an toàn và khóa tài khoản

### Test Expert Editor:

1. Đăng nhập expert account
2. Vào trang **Sửa Prompts**
3. Thay đổi nội dung W1 → Save
4. Bắt đầu phiên mới → kiểm tra prompt mới đã có hiệu lực

---

## 6 — Share Link Cho Stakeholder

### Demo Account Cho Stakeholder:

```
Email:    stakeholder@demo.local
Password: demo123
```

Để tạo tài khoản stakeholder:
1. Đăng nhập bằng **admin account**
2. Đăng ký tài khoản mới với email `stakeholder@demo.local`
3. Share link app với stakeholder

### Share Link:

```
https://tri-lieu-tam-ly.streamlit.app
```

### Checklist Demo:

| Test | Kỳ vọng |
|------|---------|
| Đăng nhập stakeholder | Thành công |
| Bắt đầu buổi trị liệu | W1 hiển thị |
| Trả lời vài câu | W chuyển động |
| Xem bài tập sau W7 | Homework hiển thị |
| Expert sửa prompt | Lưu thành công |
| Stakeholder đóng vai user live | Tương tác tự nhiên |

---

## Troubleshooting

### "App URL is already taken"
→ Đổi tên repo hoặc chọn App URL khác

### "Module not found: streamlit"
→ Kiểm tra **Requirements path** trong Advanced Settings = `app/requirements.txt`

### "GEMINI_API_KEY is not set"
→ Kiểm tra tab **Secrets** trong Settings đã thêm đúng key chưa

### "Database locked"
→ SQLite không hoạt động tốt trên multi-instance. Khi scale lên, cần chuyển sang PostgreSQL. Liên hệ support.

---

## Chi Phí

| Thành phần | Chi phí |
|-------------|---------|
| Streamlit Cloud (repo public) | Miễn phí |
| Gemini API (free tier) | Miễn phí (1,500 requests/ngày với gemini-2.0-flash) |
| GitHub | Miễn phí |

**Tổng: $0 / tháng** cho demo và sử dụng nhỏ.
