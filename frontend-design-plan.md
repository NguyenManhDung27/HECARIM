# Kế hoạch Thiết kế Giao diện

## 1. Cấu trúc Thư mục
```
frontend/
├── static/
│   ├── css/
│   │   ├── base.css         # CSS chung
│   │   ├── components.css   # CSS cho các component
│   │   └── layout.css       # CSS cho layout
│   └── images/              # Hình ảnh và icons
└── templates/
    ├── base.html           # Template cơ sở
    ├── auth/              
    │   ├── login.html      # Trang đăng nhập
    │   └── register.html   # Trang đăng ký
    ├── doctor/
    │   ├── dashboard.html  # Trang chủ bác sĩ
    │   ├── patients.html   # Danh sách bệnh nhân
    │   ├── schedule.html   # Lịch làm việc
    │   └── prescription.html # Kê đơn thuốc
    ├── receptionist/
    │   ├── dashboard.html  # Trang chủ lễ tân
    │   ├── appointments.html # Quản lý lịch hẹn
    │   ├── patients.html   # Quản lý bệnh nhân
    │   └── billing.html    # Thanh toán
    └── patient/
        ├── dashboard.html  # Trang chủ bệnh nhân
        ├── appointments.html # Lịch hẹn
        ├── records.html    # Hồ sơ bệnh án
        └── prescriptions.html # Đơn thuốc
```

## 2. Thiết kế Layout

### 2.1 Layout Chung
- Header với logo và menu điều hướng
- Sidebar cho menu chức năng
- Main content area
- Footer với thông tin liên hệ

### 2.2 Components Chung
- Buttons (Primary, Secondary, Danger)
- Forms và Input fields
- Tables cho hiển thị dữ liệu
- Cards cho hiển thị thông tin
- Modals cho các form pop-up
- Alerts cho thông báo

## 3. Chi tiết Giao diện từng Phần

### 3.1 Giao diện Bác sĩ
```html
<!-- Dashboard -->
- Thống kê tổng quan
- Lịch khám hôm nay
- Danh sách bệnh nhân cần theo dõi

<!-- Kê đơn thuốc -->
- Form kê đơn với autocomplete
- Bảng thuốc đã kê
- Hướng dẫn sử dụng

<!-- Lịch làm việc -->
- Calendar view theo tuần/tháng
- Danh sách cuộc hẹn
- Form đặt/sửa lịch
```

### 3.2 Giao diện Lễ tân
```html
<!-- Dashboard -->
- Thống kê lượt khám
- Danh sách chờ khám
- Thông báo quan trọng

<!-- Quản lý lịch hẹn -->
- Calendar view
- Form đặt lịch
- Danh sách lịch hẹn

<!-- Thanh toán -->
- Form tạo hóa đơn
- Bảng giá dịch vụ
- Chi tiết thanh toán
```

### 3.3 Giao diện Bệnh nhân
```html
<!-- Dashboard -->
- Thông tin cá nhân
- Lịch hẹn sắp tới
- Thông báo quan trọng

<!-- Hồ sơ bệnh án -->
- Timeline lịch sử khám
- Chi tiết đơn thuốc
- Kết quả xét nghiệm
```

## 4. Màu sắc và Typography

### 4.1 Bảng màu
```css
:root {
  --primary: #2D87C8;     /* Màu chủ đạo */
  --secondary: #6BB9F0;   /* Màu phụ */
  --success: #27AE60;     /* Màu thành công */
  --warning: #F1C40F;     /* Màu cảnh báo */
  --danger: #E74C3C;      /* Màu nguy hiểm */
  --text: #2C3E50;        /* Màu chữ chính */
  --text-light: #7F8C8D;  /* Màu chữ phụ */
  --bg: #F5F6FA;          /* Màu nền */
  --white: #FFFFFF;       /* Màu trắng */
}
```

### 4.2 Typography
```css
body {
  font-family: 'Inter', sans-serif;
  font-size: 14px;
  line-height: 1.5;
  color: var(--text);
}

h1, h2, h3, h4, h5, h6 {
  font-family: 'Montserrat', sans-serif;
}
```

## 5. Responsive Design
- Mobile: < 768px
- Tablet: 768px - 1024px
- Desktop: > 1024px

## 6. Accessibility
- ARIA labels cho các elements
- Tương phản màu sắc phù hợp
- Keyboard navigation
- Screen reader support

## 7. Thứ tự triển khai

1. Tạo base template và CSS foundation
2. Xây dựng các components chung
3. Triển khai giao diện từng role theo thứ tự:
   - Bác sĩ
   - Lễ tân
   - Bệnh nhân
4. Testing và tối ưu responsive