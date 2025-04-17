# Hệ thống Quản lý Bệnh viện

Hệ thống quản lý bệnh viện với giao diện tiếng Việt, sử dụng Python Flask và MongoDB.

## Yêu cầu hệ thống

- Python 3.8+
- MongoDB 4.4+
- pip (Python package manager)

## Cài đặt

1. Clone repository:
```bash
git clone [repository_url]
cd [tên folder]
```

2. Tạo môi trường ảo và kích hoạt:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. Cài đặt các gói phụ thuộc:
```bash
pip install -r requirements.txt
```

4. Cấu hình môi trường:
- Tạo file `.env` từ mẫu có sẵn và cập nhật các thông số cần thiết
- Đảm bảo MongoDB đang chạy trên máy local

5. Khởi tạo cơ sở dữ liệu:
```bash
python backend/scripts/init_db.py
```

## Chạy ứng dụng

1. Khởi động server:
```bash
python backend/run.py
```

2. Truy cập ứng dụng tại: `http://localhost:5000`

## Tài khoản mặc định

Hệ thống được khởi tạo với các tài khoản test sau:

1. Bác sĩ:
   - Username: doctor1
   - Password: doctor123

2. Lễ tân:
   - Username: receptionist1
   - Password: receptionist123

3. Bệnh nhân:
   - Username: patient1
   - Password: patient123

## Cấu trúc dự án

```
hospital-management-system/
├── backend/
│   ├── app/
│   │   ├── routes/     # API endpoints
│   │   ├── models/     # Database models
│   │   ├── services/   # Business logic
│   │   └── utils/      # Helper functions
│   ├── config/         # Configuration files
│   ├── scripts/        # Database scripts
│   └── tests/          # Unit tests
├── frontend/
│   ├── static/         # CSS, images
│   └── templates/      # HTML templates
└── requirements.txt    # Python dependencies
```

## API Endpoints

### Authentication Routes
- `POST /auth/login` - Đăng nhập
- `POST /auth/logout` - Đăng xuất
- `GET /auth/me` - Lấy thông tin người dùng hiện tại

### Patient Routes (Cần login với vai trò bệnh nhân)
- `GET /patient/info` - Xem thông tin cá nhân
- `GET /patient/appointments` - Xem lịch hẹn
- `GET /patient/medical-history` - Xem lịch sử khám bệnh

### Doctor Routes (Cần login với vai trò bác sĩ)
- `GET /doctor/patients` - Danh sách bệnh nhân
- `GET /doctor/appointments` - Xem lịch khám
- `PUT /doctor/medical-records` - Cập nhật bệnh án

### Receptionist Routes (Cần login với vai trò lễ tân)
- `POST /receptionist/patients` - Đăng ký bệnh nhân mới
- `POST /receptionist/appointments` - Đặt lịch hẹn
- `GET /receptionist/invoices` - Xem hóa đơn

## Testing

Chạy unit tests:
```bash
pytest backend/tests/
```

## Bảo mật

- Mật khẩu được mã hóa với bcrypt
- JWT authentication cho API
- Role-based access control
- CSRF protection
- Input validation và sanitization

## License

[MIT License](LICENSE)
