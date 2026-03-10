# HelpDesk Pro - Customer Support Platform

A production-grade customer support platform built with Django, Django REST Framework, Django Channels, React, PostgreSQL, Redis, and Celery. Provides ticket management, live chat, knowledge base, SLA management, canned responses, customer satisfaction surveys, agent performance analytics, and multi-channel support.

## Features

- **Ticket Management**: Create, assign, track, and resolve support tickets with priorities, tags, statuses, and full conversation threads with file attachments.
- **Live Chat**: Real-time WebSocket-based chat between customers and agents with typing indicators, read receipts, and session management.
- **Knowledge Base**: Searchable articles organized by category with rich text content, article feedback, and a public-facing portal.
- **SLA Management**: Define SLA policies with response and resolution time rules per priority. Automated breach detection and escalation via Celery.
- **Canned Responses**: Reusable response templates organized by category for faster agent replies.
- **Customer Satisfaction (CSAT)**: Post-resolution satisfaction surveys with rating collection and analytics.
- **Analytics & Reporting**: Dashboards for ticket volume trends, agent performance metrics, SLA compliance, and CSAT scores.
- **Multi-Channel Support**: Email, chat, web form, and API-based ticket creation with unified inbox.
- **Role-Based Access Control**: Distinct roles for admins, agents, and customers with granular permissions.
- **Team Management**: Organize agents into teams with round-robin or load-balanced ticket assignment.

## Architecture

```
                    +-------------------+
                    |   Nginx (Proxy)   |
                    +--------+----------+
                             |
              +--------------+--------------+
              |                             |
     +--------v--------+          +--------v--------+
     | React Frontend  |          | Django Backend   |
     | (Port 3000)     |          | (Port 8000)      |
     +-----------------+          +--------+---------+
                                           |
                        +------------------+------------------+
                        |                  |                  |
               +--------v------+  +-------v-------+  +------v------+
               | PostgreSQL    |  | Redis         |  | Celery      |
               | (Port 5432)   |  | (Port 6379)   |  | Worker/Beat |
               +---------------+  +---------------+  +-------------+
```

## Tech Stack

| Layer       | Technology                              |
|-------------|-----------------------------------------|
| Backend     | Django 5.0, Django REST Framework 3.15   |
| WebSocket   | Django Channels 4.0, Daphne              |
| Task Queue  | Celery 5.4 with Redis broker             |
| Database    | PostgreSQL 16                            |
| Cache       | Redis 7                                  |
| Frontend    | React 18, Redux Toolkit, React Router 6  |
| HTTP Client | Axios                                    |
| Charts      | Recharts                                 |
| CSS         | Tailwind CSS (via CDN for simplicity)     |
| Proxy       | Nginx                                    |
| Container   | Docker, Docker Compose                   |

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Git

### Setup

1. Clone the repository:
```bash
git clone https://github.com/your-org/helpdesk-pro.git
cd helpdesk-pro
```

2. Copy environment file:
```bash
cp .env.example .env
```

3. Edit `.env` with your settings (the defaults work for local development).

4. Build and start all services:
```bash
docker-compose up --build
```

5. Run database migrations:
```bash
docker-compose exec backend python manage.py migrate
```

6. Create a superuser:
```bash
docker-compose exec backend python manage.py createsuperuser
```

7. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/api/
   - Django Admin: http://localhost:8000/admin/
   - API Documentation: http://localhost:8000/api/schema/

### Development Without Docker

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
export DJANGO_SETTINGS_MODULE=config.settings.dev
python manage.py migrate
python manage.py runserver
```

#### Frontend

```bash
cd frontend
npm install
npm start
```

#### Celery Worker and Beat

```bash
cd backend
celery -A config worker -l info
celery -A config beat -l info
```

## API Endpoints

### Authentication
| Method | Endpoint              | Description          |
|--------|-----------------------|----------------------|
| POST   | /api/auth/register/   | Register new user    |
| POST   | /api/auth/login/      | Login and get tokens |
| POST   | /api/auth/refresh/    | Refresh JWT token    |
| GET    | /api/auth/me/         | Get current user     |

### Tickets
| Method | Endpoint                          | Description            |
|--------|-----------------------------------|------------------------|
| GET    | /api/tickets/                     | List tickets           |
| POST   | /api/tickets/                     | Create ticket          |
| GET    | /api/tickets/{id}/                | Get ticket detail      |
| PATCH  | /api/tickets/{id}/                | Update ticket          |
| POST   | /api/tickets/{id}/messages/       | Add message to ticket  |
| POST   | /api/tickets/{id}/assign/         | Assign ticket          |
| POST   | /api/tickets/{id}/close/          | Close ticket           |

### Live Chat
| Method | Endpoint                    | Description           |
|--------|-----------------------------|-----------------------|
| GET    | /api/chat/sessions/         | List chat sessions    |
| POST   | /api/chat/sessions/         | Start chat session    |
| GET    | /api/chat/sessions/{id}/    | Get session messages  |
| WS     | /ws/chat/{session_id}/      | WebSocket chat        |

### Knowledge Base
| Method | Endpoint                      | Description          |
|--------|-------------------------------|----------------------|
| GET    | /api/kb/articles/             | List articles        |
| POST   | /api/kb/articles/             | Create article       |
| GET    | /api/kb/articles/{slug}/      | Get article          |
| GET    | /api/kb/categories/           | List categories      |
| POST   | /api/kb/articles/{id}/feedback/ | Submit feedback    |

### SLA
| Method | Endpoint              | Description          |
|--------|-----------------------|----------------------|
| GET    | /api/sla/policies/    | List SLA policies    |
| POST   | /api/sla/policies/    | Create SLA policy    |
| GET    | /api/sla/breaches/    | List SLA breaches    |

### Analytics
| Method | Endpoint                        | Description            |
|--------|---------------------------------|------------------------|
| GET    | /api/analytics/overview/        | Dashboard overview     |
| GET    | /api/analytics/tickets/         | Ticket statistics      |
| GET    | /api/analytics/agents/          | Agent performance      |
| GET    | /api/analytics/sla/             | SLA compliance         |
| GET    | /api/analytics/csat/            | CSAT scores            |

## Environment Variables

See `.env.example` for all available configuration options.

## Project Structure

```
helpdesk-pro/
├── backend/
│   ├── config/              # Django project configuration
│   │   ├── settings/        # Split settings (base, dev, prod)
│   │   ├── urls.py          # Root URL configuration
│   │   ├── wsgi.py          # WSGI entry point
│   │   ├── asgi.py          # ASGI entry point (WebSocket)
│   │   ├── celery.py        # Celery configuration
│   │   └── routing.py       # WebSocket routing
│   ├── apps/
│   │   ├── accounts/        # User, Agent, Customer, Team models
│   │   ├── tickets/         # Ticket management
│   │   ├── live_chat/       # Real-time chat
│   │   ├── knowledge_base/  # KB articles and categories
│   │   ├── sla/             # SLA policies and breach tracking
│   │   ├── canned_responses/# Reusable response templates
│   │   ├── satisfaction/    # CSAT surveys
│   │   └── analytics/       # Reporting and dashboards
│   ├── utils/               # Shared utilities
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── api/             # API client and service modules
│   │   ├── components/      # Reusable React components
│   │   ├── pages/           # Page-level components
│   │   ├── store/           # Redux store and slices
│   │   ├── hooks/           # Custom React hooks
│   │   └── styles/          # Global CSS
│   └── package.json
├── nginx/
│   └── nginx.conf
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

## Testing

```bash
# Backend tests
docker-compose exec backend python manage.py test

# Frontend tests
docker-compose exec frontend npm test
```

## License

MIT License. See LICENSE file for details.
