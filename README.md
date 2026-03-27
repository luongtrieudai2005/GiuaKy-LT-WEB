# TaskFlow — Ứng dụng Quản lý Công việc

Ứng dụng web quản lý công việc (Task Manager) được xây dựng nhằm minh họa các kỹ thuật **triển khai ứng dụng web** bao gồm Docker, Nginx reverse proxy, HTTPS/SSL và CI/CD với GitHub Actions.

---

## Công nghệ sử dụng

| Tầng | Công nghệ |
|---|---|
| Backend | Python 3.11, FastAPI, Uvicorn |
| Cơ sở dữ liệu | MongoDB 7.0 (Beanie ODM + Motor) |
| Frontend | HTML5, CSS3, JavaScript thuần |
| Reverse Proxy | Nginx 1.25 |
| Containerization | Docker, Docker Compose |
| CI/CD | GitHub Actions |
| Xác thực | JWT (JSON Web Token) |

---

## Cấu trúc thư mục

```
task-manager/
├── .github/
│   └── workflows/
│       └── deploy.yml          # Pipeline CI/CD GitHub Actions
├── backend/
│   ├── routers/
│   │   ├── users.py            # Endpoint xác thực (đăng ký, đăng nhập)
│   │   ├── tasks.py            # Endpoint CRUD công việc
│   │   └── categories.py       # Endpoint CRUD danh mục
│   ├── main.py                 # Điểm khởi động ứng dụng FastAPI
│   ├── models.py               # Mô hình document MongoDB (Beanie)
│   ├── schemas.py              # Schema Pydantic cho request/response
│   ├── database.py             # Hàm hỗ trợ JWT và mã hóa mật khẩu
│   ├── requirements.txt        # Danh sách thư viện Python
│   └── Dockerfile              # Image Docker cho backend
├── frontend/
│   ├── index.html              # Giao diện ứng dụng (SPA)
│   ├── style.css               # Stylesheet giao diện tối
│   └── app.js                  # Logic giao tiếp với API
├── nginx/
│   ├── nginx.conf              # Cấu hình reverse proxy và SSL
│   └── ssl/                    # Chứng chỉ SSL (không commit lên git)
│       ├── cert.pem
│       └── key.pem
├── docker-compose.yml          # Điều phối tất cả các service
├── generate-ssl.bat            # Tạo chứng chỉ SSL tự ký (Windows)
├── generate-ssl.sh             # Tạo chứng chỉ SSL tự ký (Linux/Mac)
├── .env.example                # Mẫu biến môi trường
└── README.md
```

---

## Yêu cầu hệ thống

Cài đặt các phần mềm sau trước khi chạy dự án:

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (đã bao gồm Docker Compose)
- [OpenSSL](https://slproweb.com/products/Win32OpenSSL.html) — để tạo chứng chỉ SSL
  - Người dùng Windows có Git Bash đã có sẵn OpenSSL

---

## Hướng dẫn chạy với Docker (Khuyến nghị)

### Bước 1 — Clone repository

```bash
git clone https://github.com/your-username/taskmanager.git
cd taskmanager
```

### Bước 2 — Tạo file cấu hình môi trường

```bash
cp .env.example .env
```

Mở file `.env` và điền các giá trị thực. Các biến quan trọng:

```env
MONGO_ROOT_USERNAME=admin
MONGO_ROOT_PASSWORD=mat_khau_manh_cua_ban

# Phải khớp với thông tin đăng nhập MongoDB ở trên
MONGODB_URL=mongodb://admin:mat_khau_manh_cua_ban@mongo:27017/?authSource=admin

MONGODB_DB_NAME=taskmanager
SECRET_KEY=khoa_bi_mat_ngau_nhien
ACCESS_TOKEN_EXPIRE_MINUTES=60
ALLOWED_ORIGINS=https://localhost
DOMAIN=localhost
```

Tạo `SECRET_KEY` ngẫu nhiên bằng lệnh:
```bash
openssl rand -hex 32
```

### Bước 3 — Tạo chứng chỉ SSL (chỉ chạy một lần)

**Windows:**
```bat
generate-ssl.bat
```

**Linux / Mac / Git Bash:**
```bash
bash generate-ssl.sh
```

Lệnh này tạo ra hai file `nginx/ssl/cert.pem` và `nginx/ssl/key.pem`.

### Bước 4 — Build và khởi động tất cả service

```bash
docker compose up --build
```

Khi tất cả service sẵn sàng, terminal sẽ hiển thị:
```
mongo    | MongoDB starting...
fastapi  | Connected to MongoDB: taskmanager
fastapi  | INFO: Uvicorn running on http://0.0.0.0:8000
nginx    | ready for start up
```

### Bước 5 — Mở ứng dụng trên trình duyệt

| Địa chỉ | Mô tả |
|---|---|
| `https://localhost` | Giao diện chính của ứng dụng TaskFlow |
| `https://localhost/api/docs` | Swagger UI — tài liệu và test API |
| `https://localhost/api/health` | Kiểm tra trạng thái hệ thống |

> **Lưu ý:** Trình duyệt sẽ hiện cảnh báo bảo mật do dùng chứng chỉ SSL tự ký.
> Bấm **Nâng cao → Tiếp tục đến localhost** để vào ứng dụng.
> Đây là hành vi bình thường với môi trường phát triển cục bộ.

---

## Hướng dẫn chạy cục bộ (không dùng Docker)

Phù hợp cho việc phát triển và debug.

### Bước 1 — Khởi động MongoDB

```bash
docker run -d -p 27017:27017 --name mongo-local mongo:7.0
```

### Bước 2 — Tạo và kích hoạt môi trường ảo Python

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / Mac
source venv/bin/activate
```

### Bước 3 — Cài đặt thư viện

```bash
pip install -r requirements.txt
```

### Bước 4 — Tạo file `.env` trong thư mục `backend/`

```env
MONGODB_URL=mongodb://localhost:27017/
MONGODB_DB_NAME=taskmanager
SECRET_KEY=dev_secret_key_local
ACCESS_TOKEN_EXPIRE_MINUTES=60
ALLOWED_ORIGINS=http://localhost:8000
```

### Bước 5 — Khởi động server

```bash
python -m uvicorn main:app --reload
```

Mở trình duyệt tại `http://localhost:8000`.

> **Lưu ý:** Khi chạy cục bộ (không qua Docker + Nginx), biến `API_BASE`
> trong `frontend/app.js` phải được đặt thành `''` (chuỗi rỗng).
> Khi chạy qua Docker + Nginx, đặt thành `'/api'`.

---

## Danh sách API

### Xác thực

| Phương thức | Đường dẫn | Mô tả |
|---|---|---|
| POST | `/auth/register` | Tạo tài khoản mới |
| POST | `/auth/login` | Đăng nhập, trả về JWT token |
| GET | `/auth/me` | Lấy thông tin người dùng hiện tại |

### Công việc (Tasks)

| Phương thức | Đường dẫn | Mô tả |
|---|---|---|
| GET | `/tasks/` | Lấy danh sách công việc (hỗ trợ lọc theo `?status=`, `?priority=`, `?category_id=`) |
| POST | `/tasks/` | Tạo công việc mới |
| GET | `/tasks/{id}` | Lấy chi tiết một công việc |
| PATCH | `/tasks/{id}` | Cập nhật một phần công việc |
| DELETE | `/tasks/{id}` | Xóa công việc |

### Danh mục (Categories)

| Phương thức | Đường dẫn | Mô tả |
|---|---|---|
| GET | `/categories/` | Lấy danh sách danh mục |
| POST | `/categories/` | Tạo danh mục mới |
| PATCH | `/categories/{id}` | Cập nhật danh mục |
| DELETE | `/categories/{id}` | Xóa danh mục (công việc thuộc danh mục sẽ không bị xóa) |

Tất cả các endpoint ngoại trừ `/auth/register` và `/auth/login` đều yêu cầu header:
```
Authorization: Bearer <jwt_token>
```

---

## Pipeline CI/CD

Pipeline GitHub Actions (`.github/workflows/deploy.yml`) tự động chạy mỗi khi có push lên nhánh `main`:

```
Push lên nhánh main
        │
        ▼
Job 1: Chạy tests ── thất bại ──→ Pipeline dừng lại
        │ thành công
        ▼
Job 2: Build Docker image ── thất bại ──→ Pipeline dừng lại
        │ thành công
        ▼
Job 3: Deploy lên VPS (cần cấu hình secrets)
```

Để kích hoạt job deploy, thêm các secrets sau vào repository GitHub
(**Settings → Secrets and variables → Actions**):

| Secret | Giá trị |
|---|---|
| `VPS_HOST` | Địa chỉ IP hoặc domain của server |
| `VPS_USER` | Tên người dùng SSH (ví dụ: `ubuntu`) |
| `VPS_SSH_KEY` | Nội dung private key SSH (`~/.ssh/id_rsa`) |

---

## Kiến trúc triển khai

```
Internet
    │
    ▼ cổng 443 (HTTPS)
┌─────────────────────────────────────────────┐
│  Nginx (reverse proxy)                      │
│  - Kết thúc SSL (chứng chỉ Let's Encrypt)  │
│  - Phục vụ file tĩnh frontend              │
│  - Chuyển tiếp /api/* → FastAPI:8000       │
└──────────────────┬──────────────────────────┘
                   │ Docker internal network
         ┌─────────┴──────────┐
         ▼                    ▼
    ┌─────────┐         ┌──────────┐
    │ FastAPI │────────▶│ MongoDB  │
    │  :8000  │         │  :27017  │
    └─────────┘         └──────────┘
```

---

## Dừng ứng dụng

```bash
# Dừng tất cả container (giữ lại dữ liệu)
docker compose down

# Dừng và xóa toàn bộ dữ liệu (reset hoàn toàn)
docker compose down -v
```

---

## Thành viên nhóm

| Họ và tên | MSSV | Vai trò |
|---|---|---|
| [Thành viên 1] | [MSSV] | [Vai trò] |
| [Thành viên 2] | [MSSV] | [Vai trò] |

**Môn học:** Lập trình Web và Ứng dụng (503073)
**Trường:** Đại học Tôn Đức Thắng — Khoa Công nghệ Thông tin
**Học kỳ:** 2 — Năm học 2025–2026