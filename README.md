🚀 HeadStart - AI Powered Learning Recommendation Platform
<div align="center">

!HeadStart Logo

Personalized learning recommendations powered by cutting-edge AI technology

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)
![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green?logo=fastapi)

[🌟 Features](#-key-features) • [🛠️ Tech Stack](#%EF%B8%8F-tech-stack) • [🚀 Quick Start](#-quick-start) • [📖 Documentation](#-api-documentation) • [🤝 Contributing](#-contributing)

</div>

----

🌟 Overview
HeadStart revolutionizes the learning experience by delivering personalized recommendations using advanced AI embeddings, intelligent rerankers, and explainable AI. Our platform seamlessly integrates content from multiple sources including YouTube, arXiv papers, and custom uploads, while empowering administrators with sophisticated content curation tools.

✨ Key Features
<table>
<tr>
<td width="50%">

🎯 Personalized Recommendations
AI-powered content suggestions tailored to individual learner goals and preferences

🔍 Explainable AI
Crystal-clear reasoning behind every recommendation with detailed similarity scores

🌐 Multi-Source Content
Seamless integration with YouTube, arXiv, and custom content uploads

</td>
<td width="50%">

👨‍💼 Admin Dashboard
Comprehensive content curation and user management tools

🔒 Secure & Accessible
WCAG 2.1 AA compliant with enterprise-grade security measures

📱 Mobile-First Design
Responsive interface optimized for all devices and screen sizes

</td>
</tr>
</table>

🛠️ Tech Stack
<div align="center">

| Layer | Technologies |
|-------|-------------|
| **Frontend** | ![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js) ![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?logo=typescript&logoColor=white) ![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?logo=tailwind-css&logoColor=white) |
| **Backend** | ![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white) ![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white) ![Celery](https://img.shields.io/badge/Celery-37B24D?logo=celery&logoColor=white) ![Redis](https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=white) |
| **Database** | ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql&logoColor=white) ![pgvector](https://img.shields.io/badge/pgvector-Vector_Search-FF6B6B) |
| **AI/ML** | ![OpenAI](https://img.shields.io/badge/OpenAI-Embeddings-412991?logo=openai&logoColor=white) ![Custom](https://img.shields.io/badge/Custom-Reranking-FF9500) |
| **Security** | ![OAuth2](https://img.shields.io/badge/OAuth2-PKCE-4285F4) ![JWT](https://img.shields.io/badge/JWT-Tokens-000000?logo=json-web-tokens&logoColor=white) ![Argon2](https://img.shields.io/badge/Argon2id-Hashing-7B68EE) |
| **Infrastructure** | ![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white) ![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?logo=kubernetes&logoColor=white) ![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?logo=github-actions&logoColor=white) |

</div>

🚀 Quick Start
📋 Prerequisites
Before you begin, ensure you have the following installed:

	* 🐳 Docker and Docker Compose
	* 📗 Node.js 18+ (for local frontend development)
	* 🐍 Python 3.11+ (for local backend development)

⚡ Development Setup
<details>
<summary><strong>🔧 Step-by-step setup guide</strong></summary>

1️⃣ Clone the repository
git clone <repository-url>
cd headstart

2️⃣ Set up environment variables
cp .env.example .env
# 📝 Edit .env with your configuration

3️⃣ Start the development environment
docker-compose up -d

4️⃣ Access the application
	* 🌐 Frontend: http://localhost:3000
	* 🔌 Backend API: http://localhost:8000
	* 📚 API Documentation: http://localhost:8000/docs

</details>

💻 Local Development
<details>
<summary><strong>🔨 Backend Development</strong></summary>

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the FastAPI server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

</details>

<details>
<summary><strong>🎨 Frontend Development</strong></summary>

# Navigate to frontend directory
cd src

# Install dependencies
npm install

# Start the development server
npm run dev

</details>

📁 Project Structure
headstart/
├── 🎨 src/                    # Next.js frontend application
│   ├── 🧩 components/         # React components
│   │   ├── 👤 user/           # User-facing components
│   │   └── 👨‍💼 admin/          # Admin-only components
│   ├── 📄 pages/              # Next.js pages
│   │   ├── 👤 user/           # User dashboard pages
│   │   └── 👨‍💼 admin/          # Admin dashboard pages
│   ├── 🎨 styles/             # CSS and styling files
│   └── 🛠️ utils/              # Frontend utilities
├── 🔌 api/                    # FastAPI route handlers
│   ├── 🔐 auth.py             # Authentication endpoints
│   ├── 👤 user.py             # User management endpoints
│   ├── 📚 content.py          # Content management endpoints
│   ├── 🎯 recommendations.py  # Recommendation endpoints
│   └── 👨‍💼 admin.py            # Admin-only endpoints
├── ⚙️ services/               # Backend business logic
│   ├── 🗄️ database.py         # Database connection and utilities
│   ├── 🔐 auth.py             # Authentication services
│   ├── 🤖 recommendations.py  # Recommendation engine
│   └── 📊 content_processing.py # Content ingestion and processing
├── 🔧 config/                 # Configuration management
├── 📝 scripts/                # Database and deployment scripts
├── 🧪 tests/                  # Test suites
└── 📖 docs/                   # Documentation

📖 API Documentation
The API documentation is automatically generated and available at:

	* 🔧 Development: http://localhost:8000/docs
	* 🔍 Interactive Explorer: http://localhost:8000/redoc

🔑 Key API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/register` | 📝 User registration |
| `POST` | `/api/auth/login` | 🔐 User authentication |
| `GET` | `/api/recommendations/feed` | 🎯 Get personalized recommendations |
| `POST` | `/api/content/upload` | 📤 Upload custom content |
| `GET` | `/api/user/dashboard` | 📊 User dashboard data |
| `GET` | `/api/admin/content/pending` | 👨‍💼 Admin content moderation |

🧪 Testing
🏃‍♂️ Running Tests
# 🐍 Backend tests
pytest --cov=. --cov-report=html

# 🎨 Frontend tests
cd src && npm test

# 🔗 Integration tests
pytest tests/integration/

# 🌐 End-to-end tests
cd src && npm run test:e2e

📊 Test Coverage
	* ✅ Unit Tests: 80%+ coverage for new code
	* 🔗 Integration Tests: All API endpoints
	* 🌐 E2E Tests: Critical user flows
	* ♿ Accessibility Tests: WCAG 2.1 AA compliance

🔒 Security
🔐 Encryption
Important: Sensitive information in the .env file is encrypted and stored in the .env.encrypted file.


🔓 Decrypting secrets:

python decrypt_env.py

🔒 Encrypting secrets:

python encrypt_env.py

🛡️ Security Features
<div align="center">

| Security Layer | Implementation |
|----------------|---------------|
| **🔐 Authentication** | OAuth2 PKCE + JWT tokens |
| **🔒 Password Security** | Argon2id hashing |
| **✅ Input Validation** | Pydantic models + sanitization |
| **🛡️ Security Headers** | CSP, HSTS, X-Frame-Options |
| **⏱️ Rate Limiting** | API endpoint protection |
| **🔐 HTTPS** | TLS 1.3 in production |
| **🔍 Dependency Scanning** | Automated vulnerability checks |

</div>

♿ Accessibility
HeadStart is designed to be fully accessible for all users:

	* ✅ WCAG 2.1 AA Compliance: Comprehensive accessibility support
	* 🔊 Screen Reader Support: ARIA labels and semantic HTML
	* ⌨️ Keyboard Navigation: Full keyboard accessibility
	* 🎨 High Contrast: Support for high contrast themes
	* 📱 Responsive Design: Mobile-first, works on all devices

🚀 Deployment
🏭 Production Deployment
<details>
<summary><strong>📦 Docker Deployment</strong></summary>

# Build Docker images
docker build -f Dockerfile.backend -t headstart/backend:latest .
docker build -f Dockerfile.frontend -t headstart/frontend:latest ./src

</details>

<details>
<summary><strong>☸️ Kubernetes Deployment</strong></summary>

# Deploy to Kubernetes
kubectl apply -f k8s/

# Run database migrations
kubectl exec -it deployment/headstart-backend -- alembic upgrade head

</details>

🔧 Environment Variables
See .env.example for all required environment variables. Key variables:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `OPENAI_API_KEY` | OpenAI API key for embeddings |
| `JWT_SECRET` | Secret key for JWT token signing |

🤝 Contributing
We welcome contributions! Here's how to get started:

🔄 Quick Contribution Guide
	1. 🍴 Fork the repository
	2. 🌿 Create a feature branch (git checkout -b feature/amazing-feature)
	3. ✏️ Commit your changes (git commit -m 'Add amazing feature')
	4. 📤 Push to the branch (git push origin feature/amazing-feature)
	5. 🔄 Open a Pull Request

📋 Development Guidelines
	* 🎨 Code Style: ESLint + Prettier (frontend), Black + Ruff (backend)
	* 🧪 Testing: Write comprehensive tests for new features
	* ♿ Accessibility: Ensure WCAG 2.1 AA compliance
	* 📚 Documentation: Update docs as needed
	* 📝 Commits: Follow semantic commit messages

📄 License
This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

🆘 Support
Need help? We're here for you!

	* 🐛 [Create an issue](../../issues) in the GitHub repository
	* 📖 Check the [documentation](./docs)
	* 🔍 Review the [API documentation](/docs) at /docs

----

<div align="center">

🏗️ Built with ❤️ by the HeadStart team

Making personalized learning accessible to everyone

----

Last updated: September 14, 2025

</div>
