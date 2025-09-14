# HeadStart - AI Powered Learning Recommendation Platform

## Overview

HeadStart delivers personalized learning recommendations using AI embeddings, rerankers, and explainable AI. The platform helps learners discover relevant content from multiple sources including YouTube, arXiv papers, and custom uploads, while providing administrators with powerful content curation tools.

## Key Features

- **Personalized Recommendations**: AI-powered content suggestions based on learner goals and preferences
- **Explainable AI**: Clear reasoning behind each recommendation with similarity scores
- **Multi-Source Content**: Integration with YouTube, arXiv, and custom content uploads
- **Admin Dashboard**: Comprehensive content curation and user management tools
- **Secure & Accessible**: WCAG 2.1 AA compliant with robust security measures
- **Mobile-First Design**: Responsive interface optimized for all devices

## Tech Stack

- **Frontend**: Next.js 14 + TypeScript + Tailwind CSS
- **Backend**: FastAPI (Python 3.11) + Celery + Redis
- **Database**: PostgreSQL 15 + pgvector for vector similarity search
- **AI/ML**: OpenAI embeddings + custom reranking algorithms
- **Auth**: OAuth2 PKCE + JWT + Argon2id password hashing
- **Infrastructure**: Docker + Kubernetes + GitHub Actions CI/CD

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd headstart
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the development environment**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Local Development

#### Backend Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the FastAPI server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Development
```bash
# Navigate to frontend directory
cd src

# Install dependencies
npm install

# Start the development server
npm run dev
```

## Project Structure

```
headstart/
├── src/                          # Next.js frontend application
│   ├── components/              # React components
│   │   ├── user/               # User-facing components
│   │   └── admin/              # Admin-only components
│   ├── pages/                  # Next.js pages
│   │   ├── user/               # User dashboard pages
│   │   └── admin/              # Admin dashboard pages
│   ├── styles/                 # CSS and styling files
│   └── utils/                  # Frontend utilities
├── api/                        # FastAPI route handlers
│   ├── auth.py                # Authentication endpoints
│   ├── user.py                # User management endpoints
│   ├── content.py             # Content management endpoints
│   ├── recommendations.py     # Recommendation endpoints
│   └── admin.py               # Admin-only endpoints
├── services/                   # Backend business logic
│   ├── database.py            # Database connection and utilities
│   ├── auth.py                # Authentication services
│   ├── recommendations.py     # Recommendation engine
│   └── content_processing.py  # Content ingestion and processing
├── config/                     # Configuration management
│   └── settings.py            # Application settings
├── scripts/                    # Database and deployment scripts
├── tests/                      # Test suites
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   └── e2e/                   # End-to-end tests
└── docs/                       # Documentation
```

## API Documentation

The API documentation is automatically generated and available at:
- **Development**: http://localhost:8000/docs
- **Interactive API Explorer**: http://localhost:8000/redoc

### Key API Endpoints

- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User authentication
- `GET /api/recommendations/feed` - Get personalized recommendations
- `POST /api/content/upload` - Upload custom content
- `GET /api/user/dashboard` - User dashboard data
- `GET /api/admin/content/pending` - Admin content moderation

## Testing

### Running Tests

```bash
# Backend tests
pytest --cov=. --cov-report=html

# Frontend tests
cd src && npm test

# Integration tests
pytest tests/integration/

# End-to-end tests
cd src && npm run test:e2e
```

### Test Coverage

- **Unit Tests**: 80%+ coverage for new code
- **Integration Tests**: All API endpoints
- **E2E Tests**: Critical user flows
- **Accessibility Tests**: WCAG 2.1 AA compliance

## Security

### Encryption

Sensitive information in the `.env` file is encrypted and stored in the `.env.encrypted` file. To run the application, you must first decrypt the secrets and generate the `.env` file.

**Decrypting secrets:**

```bash
python decrypt_env.py
```

This will create a `.env` file with the decrypted secrets. You can then run the application as usual.

**Encrypting secrets:**

If you make any changes to the sensitive information in the `.env` file, you must encrypt the file again to update the `.env.encrypted` file.

```bash
python encrypt_env.py
```

HeadStart implements comprehensive security measures:

- **Authentication**: OAuth2 PKCE + JWT tokens
- **Password Security**: Argon2id hashing
- **Input Validation**: Pydantic models + sanitization
- **Security Headers**: CSP, HSTS, X-Frame-Options
- **Rate Limiting**: API endpoint protection
- **HTTPS**: TLS 1.3 in production
- **Dependency Scanning**: Automated vulnerability checks

## Accessibility

The platform is designed to be fully accessible:

- **WCAG 2.1 AA Compliance**: Comprehensive accessibility support
- **Screen Reader Support**: ARIA labels and semantic HTML
- **Keyboard Navigation**: Full keyboard accessibility
- **High Contrast**: Support for high contrast themes
- **Responsive Design**: Mobile-first, works on all devices

## Deployment

### Production Deployment

1. **Build Docker images**
   ```bash
   docker build -f Dockerfile.backend -t headstart/backend:latest .
   docker build -f Dockerfile.frontend -t headstart/frontend:latest ./src
   ```

2. **Deploy to Kubernetes**
   ```bash
   kubectl apply -f k8s/
   ```

3. **Run database migrations**
   ```bash
   kubectl exec -it deployment/headstart-backend -- alembic upgrade head
   ```

### Environment Variables

See `.env.example` for all required environment variables. Key variables:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `OPENAI_API_KEY`: OpenAI API key for embeddings
- `JWT_SECRET`: Secret key for JWT token signing

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow the established code style (ESLint + Prettier for frontend, Black + Ruff for backend)
- Write comprehensive tests for new features
- Ensure accessibility compliance
- Update documentation as needed
- Follow semantic commit messages

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions:
- Create an issue in the GitHub repository
- Check the [documentation](docs/)
- Review the API documentation at `/docs`

---

**Built with ❤️ by the HeadStart team**

// Updated 2025-09-05: Comprehensive README with setup instructions and project overview