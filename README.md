<<<<<<< HEAD
# Hecarim Hospital Management System

A comprehensive hospital management system built with Node.js, React, and MongoDB.

## Features

- 🏥 Patient Management
- 📅 Appointment Scheduling
- 📋 Medical Records Management
- 💊 Prescription Management
- 📊 Real-time Dashboard
- 📱 Responsive Design
- 🔒 Role-based Access Control

## Technology Stack

- **Backend:** Node.js, Express.js, MongoDB
- **Frontend:** React.js, Material-UI
- **Database:** MongoDB
- **Caching:** Redis
- **Authentication:** JWT
- **Real-time:** WebSocket
- **Containerization:** Docker
- **CI/CD:** GitHub Actions

## Prerequisites

- Node.js (v16 or higher)
- Docker and Docker Compose
- MongoDB (v5 or higher)
- Git

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/yourusername/hecarim.git
cd hecarim
```

2. Run the setup script:
```bash
chmod +x setup.sh
./setup.sh
```

3. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000
- API Documentation: http://localhost:5000/api-docs

## Development

### Environment Setup

The project includes three environment configurations:
- Development: `.env.development`
- Staging: `.env.staging`
- Production: `.env.production`

To start development:
```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# Start backend development server
cd back-end
npm run dev

# Start frontend development server
cd front-end
npm start
```

### Testing

```bash
# Run backend tests
cd back-end
npm test

# Run frontend tests
cd front-end
npm test
```

## Deployment

### Production Deployment

1. Configure environment variables:
```bash
cp back-end/.env.production back-end/.env
# Edit the environment variables as needed
```

2. Deploy using the deployment script:
```bash
chmod +x deploy.sh
./deploy.sh production
```

### Staging Deployment

```bash
./deploy.sh staging
```

### Manual Deployment

1. Build Docker images:
```bash
docker-compose build
```

2. Start services:
```bash
docker-compose up -d
```

## Directory Structure

```
hecarim/
├── back-end/               # Backend application
│   ├── models/            # Database models
│   ├── routes/            # API routes
│   ├── middleware/        # Custom middleware
│   ├── utils/            # Utility functions
│   └── tests/            # Backend tests
├── front-end/             # Frontend application
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   ├── services/     # API services
│   │   └── utils/        # Utility functions
│   └── public/           # Static files
└── docker/               # Docker configuration
```

## API Documentation

API documentation is available at `/api-docs` when running the server. It's built using OpenAPI/Swagger specification.

## Monitoring

The application includes:
- Health checks endpoint: `/api/health`
- Metrics endpoint: `/api/metrics`
- APM integration
- Error tracking with Sentry

## Backup

Automated backups are configured for production:
- Daily database backups
- File storage backups
- 30-day retention policy

## Security

- JWT authentication
- Role-based access control
- Request rate limiting
- Input validation
- XSS protection
- CSRF protection
- Secure headers

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support


=======
B1: mở Bash đến thư mục => python app.py
B2: mở command prompt chạy lệnh start http://localhost:5000
>>>>>>> 084b452f123727a96592c0e4953bf2054631e667
