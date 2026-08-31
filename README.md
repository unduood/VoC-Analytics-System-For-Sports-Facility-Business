<img width="2245" height="3179" alt="poster - Voice of Customer Analytics System For Sports Facility Business" src="https://github.com/user-attachments/assets/51e8149c-9ed2-4014-8ba6-40a4b8759af9" />


<div align="center">

# 🏟️ VoC Analytics System for Sports Facility Business

**An end-to-end Voice of Customer analytics platform with Thai NLP, real-time dashboards, and human-in-the-loop corrections**

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16-000000?logo=next.js&logoColor=white)](https://nextjs.org)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 📋 Overview

VoC Analytics System is a **full-stack, event-driven analytics platform** designed for sports facility businesses (gyms, fitness clubs, sports complexes). It automatically collects customer feedback from **6 channels**, performs **Thai-language NLP analysis** using fine-tuned transformer models, and presents actionable insights through a **real-time interactive dashboard**.

### Key Capabilities

- 🔄 **Multi-Channel Ingestion** — Email, Instagram, Facebook, Google Forms, Google Maps, and manual entry
- 🤖 **Thai NLP Pipeline** — Sentiment analysis, multi-label intent classification, and aspect-based sentiment analysis across 8 facility aspects
- 📊 **Real-Time Dashboard** — KPI cards, trend charts, radar plots, and distribution visualizations with live WebSocket updates
- ✏️ **Human-in-the-Loop** — Edit ML predictions with full audit trail and instant reversion
- ⚡ **Hybrid Intelligence** — Smart routing: survey ratings bypass ML, star ratings serve as sentiment ground truth, text goes through full NLP pipeline

---

## 🏗️ Architecture

```mermaid
graph TB
    subgraph Sources["📥 Data Sources"]
        S1["📧 Email<br/>(Make.com)"]
        S2["📸 Instagram<br/>(Make.com)"]
        S3["📘 Facebook<br/>(Webhook)"]
        S4["📝 Google Forms"]
        S5["📍 Google Maps<br/>(SerpAPI)"]
        S6["✍️ Manual Entry"]
    end

    subgraph Backend["⚙️ FastAPI Backend · :8000"]
        direction TB
        WH["Webhook Endpoints<br/>+ Auth/Validation"]
        API["REST API<br/>+ Analytics"]
        WS["Socket.IO<br/>Server"]
    end

    subgraph Infra["🗄️ Infrastructure"]
        PG[("PostgreSQL<br/>:5432")]
        RMQ["RabbitMQ<br/>:5672"]
        RD["Redis<br/>:6379"]
    end

    subgraph Worker["🤖 ML Worker"]
        NLP["ThaiNLPService"]
        M1["Sentiment<br/>WangchanBERTa"]
        M2["Intent<br/>PhayaThaiBERT"]
        M3["ABSA<br/>PhayaThaiBERT"]
    end

    subgraph Frontend["🖥️ Next.js Frontend · :3000"]
        D["Dashboard"]
        R["Records & Filters"]
        H["HITL Editor"]
    end

    Sources --> WH
    WH --> PG
    WH --> RMQ
    RMQ --> NLP
    NLP --> M1 & M2 & M3
    Worker --> PG
    Worker -- "Pub/Sub" --> RD
    RD --> WS
    API --> PG
    WS --> Frontend
    API --> Frontend
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|:---|:---|
| **Backend** | Python 3.11 · FastAPI · SQLAlchemy 2.0 (async) · Alembic · Pydantic v2 · Pika |
| **ML Worker** | PyTorch · HuggingFace Transformers · 3 fine-tuned Thai NLP models |
| **Frontend** | Next.js 16 (App Router) · React 19 · TypeScript · Tailwind CSS v4 · TanStack Query v5 · Recharts · Socket.IO |
| **Database** | PostgreSQL 15 |
| **Message Queue** | RabbitMQ 3 |
| **Cache / Pub-Sub** | Redis 7 |
| **Infrastructure** | Docker · Docker Compose |

---

## 🤖 ML Models

Three fine-tuned transformer models handle Thai-language NLP:

| Task | Model | Output |
|:---|:---|:---|
| **Sentiment Analysis** | [`poom-sci/WangchanBERTa-finetuned-sentiment`](https://huggingface.co/poom-sci/WangchanBERTa-finetuned-sentiment) | positive / neutral / negative |
| **Intent Classification** | [`unduood/phayathaibert-intent-classification-sports-facility`](https://huggingface.co/unduood/phayathaibert-intent-classification-sports-facility) | feedback · complaint · question · off_topic (multi-label) |
| **Aspect-Based SA** | [`unduood/phayathaibert-absa-sports-facility-v2`](https://huggingface.co/unduood/phayathaibert-absa-sports-facility-v2) | 8 aspects: Equipment · Staff · Cleanliness · Atmosphere · Price · Location · Programs · Amenities |

### Hybrid Processing Strategy

Not all sources need full ML inference:

| Source | Sentiment | Intent | Aspect SA |
|:---|:---|:---|:---|
| **Google Forms** | From 1–5 rating ✅ | Skipped | From per-aspect ratings ✅ |
| **Google Maps** | From star rating ✅ | ML inference 🤖 | ML inference 🤖 |
| **Text sources** (Email, IG, FB, Manual) | ML inference 🤖 | ML inference 🤖 | ML inference 🤖 |

---

## 📸 Screenshots


<img width="1093" height="852" alt="Screenshot 2026-09-01 012912" src="https://github.com/user-attachments/assets/d9412acc-5029-4de5-b28a-c3560c7ea9d1" />

<img width="1068" height="748" alt="Screenshot 2026-09-01 012928" src="https://github.com/user-attachments/assets/c80ce778-7e0d-4f78-8031-9d091e467ea2" />

<img width="1678" height="897" alt="image03" src="https://github.com/user-attachments/assets/0826858a-47bb-4eb3-b755-d48940916275" />

<img width="1642" height="897" alt="image04" src="https://github.com/user-attachments/assets/44577a0a-ea4b-4607-bb3a-27942138d2b9" />

<img width="1661" height="903" alt="image05" src="https://github.com/user-attachments/assets/cf765253-65b8-4d67-8621-75c82a9b9d4b" />

---

## 📁 Project Structure

```
VoC-Analytics-System-For-Sports-Facility-Business/
├── voc-analytics/
│   ├── backend/                     # FastAPI backend service
│   │   ├── app/
│   │   │   ├── api/v1/endpoints/    # Webhook, feedback, analytics, corrections
│   │   │   ├── models/              # SQLAlchemy models
│   │   │   ├── schemas/             # Pydantic validation schemas
│   │   │   ├── services/            # Business logic layer
│   │   │   ├── websocket/           # Socket.IO + Redis subscriber
│   │   │   ├── main.py              # App entrypoint & lifespan
│   │   │   ├── config.py            # Environment settings
│   │   │   └── database.py          # Async DB engine
│   │   ├── alembic/                 # Database migrations
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── worker/                      # ML inference worker
│   │   ├── app/
│   │   │   ├── models/              # Shared SQLAlchemy models
│   │   │   ├── services/            # Redis publisher
│   │   │   ├── main.py              # RabbitMQ consumer + processing pipeline
│   │   │   ├── nlp_service.py       # Thai NLP model loader & inference
│   │   │   └── database.py          # Async DB session
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── frontend/                    # Next.js dashboard
│   │   ├── src/
│   │   │   ├── app/                 # Pages: dashboard, records, manual
│   │   │   ├── components/          # UI components, charts, editors
│   │   │   ├── context/             # Dashboard date filter context
│   │   │   └── hooks/               # Custom hooks (realtime, feedback, etc.)
│   │   ├── Dockerfile
│   │   └── package.json
│   │
│   ├── docker-compose.yml
│   └── .env.example
│
├── thai_nlp_inference_unified.ipynb  # ML model inference notebook & documentation
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/install/)
- ~3 GB RAM for ML models (first run downloads from HuggingFace)

### Installation

**1. Clone the repository**

```bash
git clone https://github.com/unduood/VoC-Analytics-System-For-Sports-Facility-Business.git
cd VoC-Analytics-System-For-Sports-Facility-Business
```

**2. Configure environment variables**

```bash
cd voc-analytics
cp .env.example .env
```

Edit `.env` and set your secrets:

```env
# Required — change these for production
SECRET_KEY=your-secret-key-here
WEBHOOK_SECRET=your-webhook-secret-here

# Optional — for platform integrations
SERPAPI_KEY=your_serpapi_key              # Google Maps reviews
FACEBOOK_APP_SECRET=your_app_secret      # Facebook webhook
FACEBOOK_PAGE_ACCESS_TOKEN=your_token    # Facebook Graph API
```

**3. Start all services**

```bash
docker-compose up -d
```

**4. Access the application**

| Service | URL |
|:---|:---|
| 🖥️ **Frontend Dashboard** | http://localhost:3000 |
| ⚙️ **Backend API** | http://localhost:8000 |
| 📖 **API Documentation** | http://localhost:8000/docs |
| 🐰 **RabbitMQ Management** | http://localhost:15672 |

> [!NOTE]
> On the first run, the ML worker will download ~1.5 GB of model weights from HuggingFace. These are cached in a Docker volume (`huggingface_cache`) for subsequent runs.

---

## 📡 API Endpoints

### Webhook Ingestion

All webhook endpoints require `X-Webhook-Token` header authentication.

| Method | Endpoint | Description |
|:---|:---|:---|
| `POST` | `/api/v1/webhooks/email` | Email feedback via Make.com |
| `POST` | `/api/v1/webhooks/instagram` | Instagram comments via Make.com |
| `GET/POST` | `/api/v1/webhooks/facebook` | Facebook Page webhook (HMAC-SHA256) |
| `POST` | `/api/v1/webhooks/google-form` | Google Forms responses |

### Feedback Management

| Method | Endpoint | Description |
|:---|:---|:---|
| `GET` | `/api/v1/feedback` | List with filters, search, and pagination |
| `GET` | `/api/v1/feedback/{id}` | Detail with all analysis results |
| `POST` | `/api/v1/feedback/manual` | Submit manual feedback |
| `DELETE` | `/api/v1/feedback/{id}` | Delete feedback + cascading analysis |

### Analytics & Corrections

| Method | Endpoint | Description |
|:---|:---|:---|
| `GET` | `/api/v1/analytics/overview` | Dashboard KPIs, distributions, aspect scores |
| `GET` | `/api/v1/analytics/trends` | Sentiment trends with auto-granularity |
| `POST` | `/api/v1/google-maps/fetch-reviews` | Fetch Google Maps reviews via SerpAPI |
| `PATCH` | `/api/v1/feedback/{id}/analysis` | Human-in-the-loop corrections |

### System

| Method | Endpoint | Description |
|:---|:---|:---|
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Swagger UI |

---

## 🔗 Integrations

### Make.com (formerly Integromat)

Email and Instagram ingestion use [Make.com](https://www.make.com/) automation scenarios:

1. **Email → Webhook**: Gmail/Outlook trigger → HTTP POST to `/api/v1/webhooks/email`
2. **Instagram → Webhook**: Instagram trigger → HTTP POST to `/api/v1/webhooks/instagram`

Set `X-Webhook-Token` in the HTTP module header to match your `WEBHOOK_SECRET` in `.env`.

### Facebook Page Webhook

Direct webhook integration with [Facebook Graph API](https://developers.facebook.com/docs/graph-api/webhooks/):

- Automatic subscription verification (`hub.challenge`)
- HMAC-SHA256 signature validation (`X-Hub-Signature-256`)
- Handles comment `add`, `edited`, and `remove` events

### Google Forms

Receives structured survey responses via webhook (`POST /api/v1/webhooks/google-form`):

- Accepts 1–5 satisfaction ratings for overall experience and 8 facility aspects (equipment, staff, cleanliness, etc.)
- Ratings are converted directly to sentiment (1–2 → negative, 3 → neutral, 4–5 → positive) — **no ML inference needed**
- Supports optional demographic fields (age group, visit frequency)

### Google Maps Reviews

Fetches reviews via [SerpAPI](https://serpapi.com/) with smart delta updates (detects edited reviews, re-analyzes changed content).

---

## 📓 ML Notebook

The [`thai_nlp_inference_unified.ipynb`](thai_nlp_inference_unified.ipynb) notebook documents and demonstrates the ML inference pipeline:

- Model configuration and HuggingFace repository mapping
- Production-ready service classes (`ABSAService`, `IntentClassificationService`, `SentimentAnalysisService`)
- Unified `ThaiNLPService` with lazy-loading and singleton pattern
- Interactive test suites on sample Thai facility reviews
- FastAPI integration code and Docker deployment guide

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
