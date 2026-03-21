# Cấu Hình Streamlit Cloud — Đúng Cách

## Lỗi Thường Gặp

### Sai
```toml
# ❌ SAI — Python version và requirements không phải secrets
[Secrets]
GEMINI_API_KEY = "..."
ALLOWED_EMAILS = "..."

[server]
pythonVersion = "3.13"

[dependencies]
requirementPath = "..."
```

### Đúng
Streamlit Cloud có **2 nơi** cấu hình riêng biệt:

---

## Bước 1: App Settings (KHÔNG phải Secrets)

Khi tạo app hoặc trong Settings của app:

| Trường | Giá trị |
|--------|---------|
| **Python version** | `3.13` |
| **Requirements path** | `app/requirements.txt` |

> Đây là settings thông thường — KHÔNG phải Secrets

---

## Bước 2: Secrets (CHỈ chứa key nhạy cảm)

Trong Settings của app, phần **Secrets**, chỉ thêm **DUY NHẤT** 3 dòng này:

```toml
GEMINI_API_KEY = "AIzaSyB2q7a-cllg4U8ePgEd3EazdXXXXXXX"
GEMINI_MODEL = "gemini-2.0-flash"
ALLOWED_EMAILS = "minhtu.news@gmail.com"
```

> ⚠️ **KHÔNG** có dòng `[Secrets]`, `[server]`, `[dependencies]`
> ⚠️ **KHÔNG** có dấu ngoặc vuông `[]` trong phần Secrets
> ⚠️ **CHỈ** có `KEY = "VALUE"` thuần túy

---

## Kiểm Tra Nhanh

Sau khi save Secrets, **Reboot** app và mở trang login.

Nếu vẫn lỗi, kiểm tra:
1. Mở DevTools (F12 → Console) trên trình duyệt
2. Hoặc click **"Manage app"** → **"Logs"** trên Streamlit Cloud
3. Tìm dòng chứa `GEMINI_API_KEY` hoặc `st.secrets`

---

## Tóm Tắt

| Nơi cấu hình | Chứa gì |
|--------------|---------|
| **App Settings** (thường) | Python version, Requirements path |
| **Secrets** | Chỉ API keys, passwords, whitelist emails |

** tuyệt đối KHÔNG** mix App Settings settings vào Secrets.
