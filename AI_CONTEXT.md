# VoC Sports Facility Analytics - AI Context Document

## Project Overview

**Project Name:** VoC Analytics System
**Purpose:** Voice of Customer (VoC) analytics platform for a sports facility to collect, analyze, and derive insights from customer feedback across multiple channels.

**Version:** 0.2.0 (Data Ingestion Implemented)
**Last Updated:** 2025-12-15

## Project Goal

Build an automated system that:
1. Collects customer feedback from multiple sources (email, Instagram, Facebook, Google Forms, Google Maps, manual entry)
2. Performs machine learning-based analysis on feedback text including:
   - Sentiment analysis (positive/neutral/negative)
   - Intent classification (feedback/question/complaint/off_topic)
   - Aspect-based sentiment analysis for sports facility aspects (equipment, staff, cleanliness, atmosphere, price, location, programs, amenities)
3. Stores analysis results for reporting and insights
4. Provides REST API for data access and management

## Architecture

### System Architecture
**Pattern:** Microservices with message queue-based async processing

**Components:**
1. **Backend Service** (FastAPI)
   - REST API server
   - Feedback ingestion
   - Database management
   - Message publishing to RabbitMQ
   - Port: 8000

2. **Worker Service** (Python)
   - Consumes messages from RabbitMQ
   - Performs ML inference
   - Stores analysis results in database

3. **PostgreSQL Database**
   - Stores feedback records and analysis results
   - Port: 5432

4. **RabbitMQ**
   - Message queue for async task processing
   - Queues: `data_ingestion`, `ml_processing`
   - Port: 5672 (AMQP), 15672 (Management UI)

5. **Redis**
   - Configured but not yet utilized in code
   - Port: 6379

### Technology Stack

**Backend:**
- Python 3.11
- FastAPI 0.109.0 (web framework)
- SQLAlchemy 2.0.25 (ORM with async support)
- Asyncpg 0.29.0 (async PostgreSQL driver)
- Alembic 1.13.1 (database migrations)
- Pika 1.3.2 (RabbitMQ client)
- Pydantic 2.5.3 (data validation)
- Email-validator 2.2.0 (email validation)

**Worker:**
- PyTorch 2.1.2 (ML framework)
- Transformers 4.37.0 (HuggingFace models)
- Same database/queue libraries as backend

**Infrastructure:**
- Docker & Docker Compose
- PostgreSQL 15 Alpine
- RabbitMQ 3 Management Alpine
- Redis 7 Alpine

## Database Schema

### Tables

**1. feedback_records**
- Primary table for all customer feedback
- Columns:
  - `id` (UUID, PK)
  - `source_type` (VARCHAR): email, instagram, facebook, google_form, google_maps, manual
  - `source_id` (VARCHAR): Unique ID from source platform
  - `text_content` (TEXT): Main feedback text
  - `raw_data` (JSONB): Platform-specific metadata
  - `created_at_source` (TIMESTAMP): Original timestamp from source
  - `processing_status` (VARCHAR): pending, processing, completed, failed
  - `created_at`, `updated_at` (TIMESTAMP)
- Constraints:
  - Unique constraint on (source_type, source_id)
- Indexes: source_type, processing_status, created_at

**2. sentiment_results**
- Stores sentiment analysis results
- Columns:
  - `id` (UUID, PK)
  - `feedback_id` (UUID, FK → feedback_records.id, CASCADE)
  - `sentiment` (VARCHAR): positive, neutral, negative
  - `confidence` (FLOAT): 0.0-1.0
  - `created_at` (STRING)
- Indexes: feedback_id, sentiment

**3. intent_results**
- Stores intent classification results
- Columns:
  - `id` (UUID, PK)
  - `feedback_id` (UUID, FK → feedback_records.id, CASCADE)
  - `intent` (VARCHAR): feedback, question, complaint, off_topic
  - `confidence` (FLOAT): 0.0-1.0
  - `created_at` (STRING)
- Indexes: feedback_id, intent

**4. aspect_sentiment_results**
- Stores aspect-based sentiment analysis
- Columns:
  - `id` (UUID, PK)
  - `feedback_id` (UUID, FK → feedback_records.id, CASCADE)
  - `aspect` (VARCHAR): equipment, staff, cleanliness, atmosphere, price, location, programs, amenities
  - `sentiment` (VARCHAR): positive, neutral, negative, none
  - `confidence` (FLOAT): 0.0-1.0
  - `created_at` (STRING)
- Indexes: feedback_id, aspect, sentiment

### Database Migrations
- Alembic configured with async support
- Initial migration: `e7dd65e74927` (created 2025-12-14)
- Migration runs automatically on backend container startup via entrypoint.sh

## Code Structure

```
voc-analytics/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app, lifespan, health endpoints, exception handlers
│   │   ├── config.py            # Pydantic settings
│   │   ├── database.py          # SQLAlchemy async engine, session
│   │   ├── rabbitmq.py          # RabbitMQ connection manager
│   │   ├── exceptions.py        # Custom exception classes
│   │   ├── api/                 # API routes
│   │   │   └── v1/
│   │   │       ├── router.py    # Main v1 API router
│   │   │       └── endpoints/
│   │   │           ├── webhooks.py  # Webhook endpoints (email, instagram)
│   │   │           └── feedback.py  # Feedback CRUD endpoints
│   │   ├── services/            # Business logic layer
│   │   │   └── ingestion.py    # Data ingestion service
│   │   ├── models/              # SQLAlchemy models
│   │   │   ├── base.py          # UUIDMixin, TimestampMixin
│   │   │   ├── feedback.py      # FeedbackRecord model
│   │   │   └── analysis.py      # Analysis result models
│   │   └── schemas/             # Pydantic schemas
│   │       ├── feedback.py      # Feedback validation schemas
│   │       ├── analysis.py      # Analysis validation schemas
│   │       └── webhooks.py      # Webhook payload schemas
│   ├── alembic/                 # Database migrations
│   ├── Dockerfile
│   ├── entrypoint.sh            # Runs migrations before app start
│   └── requirements.txt
├── worker/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # RabbitMQ consumer, message processor
│   │   └── config.py            # Worker settings
│   ├── Dockerfile
│   └── requirements.txt
├── docker-compose.yml
├── .env.example
└── .gitignore
```

## Important Technical Decisions

1. **UUID Primary Keys**: All tables use UUID instead of auto-increment integers for better distributed system support and security

2. **Async/Await Pattern**: Backend uses SQLAlchemy async for non-blocking database operations

3. **JSONB for Flexibility**: `raw_data` field in feedback_records uses PostgreSQL JSONB to store platform-specific metadata without schema changes

4. **Message Queue Architecture**: Decouples API from ML processing for scalability and reliability

5. **Database Migrations**: Alembic configured for version-controlled schema changes

6. **Cascade Deletes**: Analysis results cascade delete when feedback is deleted (maintains referential integrity)

7. **Processing Status Tracking**: Feedback records track processing state (pending → processing → completed/failed)

8. **Multi-source Design**: System designed to handle feedback from 6+ different platforms with unified schema

9. **Webhook Security**: Token-based authentication for webhook endpoints using X-Webhook-Token header

10. **Service Layer Pattern**: Business logic separated into service classes (e.g., IngestionService) for better testability and reusability

11. **Global Exception Handling**: Centralized exception handling in FastAPI for consistent error responses

## Current Implementation Status

### ✅ Completed

**Infrastructure:**
- Docker Compose configuration with all services
- PostgreSQL, Redis, RabbitMQ containers configured
- Health checks for all services
- Volume persistence for data

**Backend:**
- FastAPI application structure with layered architecture
- Database connection with async support
- RabbitMQ connection manager
- Configuration management with environment variables
- Complete SQLAlchemy models (4 tables)
- Complete Pydantic schemas for validation (feedback, analysis, webhooks)
- Database migration setup (Alembic)
- Initial migration applied
- Lifespan event handlers (startup/shutdown)
- CORS middleware (development mode - all origins)
- Global exception handling with custom exception classes
- Service layer implementation (IngestionService)
- **API v1 Endpoints:**
  - `POST /api/v1/webhooks/email` - Receive email feedback from Make.com
  - `POST /api/v1/webhooks/instagram` - Receive Instagram comments from Make.com
  - `GET /api/v1/feedback` - List feedback with pagination and filters
  - `GET /api/v1/feedback/{id}` - Get feedback details with analysis results
  - `DELETE /api/v1/feedback/{id}` - Delete feedback record
  - `GET /health` - Health check endpoint
  - `GET /` - Root endpoint
- **Webhook Security:** Token-based authentication (X-Webhook-Token header)
- **Data Ingestion:** Automatic deduplication based on source_type + source_id
- **Queue Publishing:** Automatic message publishing to RabbitMQ on feedback creation
- **UTF-8 Support:** Full support for Thai and other Unicode text

**Worker:**
- RabbitMQ consumer setup
- Message processing skeleton
- Graceful shutdown handling (SIGINT/SIGTERM)
- QoS configuration (prefetch_count=1)
- Message acknowledgment logic
- Error handling for invalid JSON

**Database:**
- Complete schema defined
- Relationships configured
- Indexes created
- Migration history started

### ⚠️ In Progress / Incomplete

**Worker - Missing Core Logic:**
- **CRITICAL TODO (worker/app/main.py:48)**: Actual ML processing implementation missing
  - No ML model loading
  - No sentiment analysis inference
  - No intent classification inference
  - No aspect-based sentiment analysis inference
  - No database write logic for results
  - Only has placeholder with 1-second sleep

**Integration - Partially Implemented:**
- ✅ Webhook endpoints ready for Make.com integration (Email, Instagram)
- ⚠️ Missing webhook endpoints for:
  - Facebook
  - Google Forms
  - Google Maps
- No automated data collection (relies on Make.com automation)
- No direct API integration (using webhook pattern instead)

**Redis:**
- Configured in docker-compose and settings
- Not used anywhere in code yet
- Potential uses: caching, rate limiting, session storage

**Testing:**
- No test suite
- No unit tests
- No integration tests
- No test fixtures

**Documentation:**
- No API documentation beyond auto-generated FastAPI docs
- No deployment guide
- No development setup instructions
- No example usage

**Security:**
- CORS allows all origins (development only)
- Default credentials in docker-compose (must change for production)
- ✅ Webhook token authentication (X-Webhook-Token header)
- ⚠️ No API key or JWT authentication for feedback endpoints
- ⚠️ No rate limiting
- ✅ Input validation via Pydantic schemas
- ✅ SQL injection protection via SQLAlchemy ORM
- ⚠️ No HTTPS enforcement (development mode)

**Monitoring/Logging:**
- Basic logging configured
- No structured logging
- No metrics/monitoring
- No error tracking
- No performance monitoring

## Known Issues & Inconsistencies

1. **Timestamp Type Inconsistency**:
   - `feedback_records` uses `TIMESTAMP(timezone=True)` for created_at/updated_at
   - Analysis result tables use `String` with server_default='NOW()' for created_at
   - Should standardize to TIMESTAMP across all tables

2. **RabbitMQ Blocking Connection in Async App**:
   - `rabbitmq.py` uses `pika.BlockingConnection`
   - Called from async FastAPI app
   - May cause blocking issues under load
   - Consider using `aio-pika` for async RabbitMQ

3. **ML Queue Not Used**:
   - `ml_processing` queue declared but never used
   - Only `data_ingestion` queue has active consumer

4. **No Database Session in Worker**:
   - Worker needs to write analysis results to database
   - No database session/connection management implemented

5. **Environment Variable Handling**:
   - Settings have defaults that may mask missing .env file
   - No validation that required variables are set

## Development Workflow

### Starting the System

```bash
cd voc-analytics
docker-compose up -d
```

Services available at:
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- RabbitMQ Management: http://localhost:15672 (user: vocuser, pass: vocpassword)
- PostgreSQL: localhost:5432 (user: vocuser, pass: vocpassword, db: vocdb)
- Redis: localhost:6379

### Database Migrations

```bash
# Create new migration
cd backend
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Testing Webhook Endpoints

```bash
# Test email webhook (requires webhook token)
curl -X POST http://localhost:8000/api/v1/webhooks/email \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Token: dev-webhook-secret-change-in-production" \
  -d '{"email_id":"test001","sender_email":"user@example.com","subject":"Feedback","body_text":"Great facility!","received_at":"2024-01-15T10:00:00Z"}'

# Test Instagram webhook
curl -X POST http://localhost:8000/api/v1/webhooks/instagram \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Token: dev-webhook-secret-change-in-production" \
  -d '{"comment_id":"ig123","comment_text":"Amazing gym!","username":"user123","media_id":"m001","media_type":"photo","caption":"New facility","comment_timestamp":"2024-01-15T11:00:00Z","post_timestamp":"2024-01-15T08:00:00Z"}'

# List feedback
curl http://localhost:8000/api/v1/feedback

# List with filters
curl "http://localhost:8000/api/v1/feedback?source_type=email&page=1&page_size=10"

# Get specific feedback
curl http://localhost:8000/api/v1/feedback/{feedback_id}
```

## Next Steps for Development

### High Priority

1. **✅ COMPLETED: Data Ingestion Endpoints**
   - ✅ Email webhook endpoint
   - ✅ Instagram webhook endpoint
   - ✅ Feedback CRUD endpoints
   - ✅ Webhook security
   - ✅ Duplicate handling

2. **Implement Worker ML Processing** (worker/app/main.py:48) - **CRITICAL**
   - Load pre-trained transformer models (or train custom models)
   - Implement sentiment analysis
   - Implement intent classification
   - Implement aspect-based sentiment analysis
   - Add database session management in worker
   - Store analysis results in database
   - Update processing_status field

3. **Configure Make.com Automation**
   - Set up Email → Webhook scenario
   - Set up Instagram → Webhook scenario
   - Test end-to-end data flow
   - Configure error handling in Make.com

4. **Additional Webhook Endpoints**
   - POST /api/v1/webhooks/facebook
   - POST /api/v1/webhooks/google_form
   - POST /api/v1/webhooks/google_maps

5. **Fix Timestamp Inconsistency**
   - Update analysis models to use TIMESTAMP instead of String
   - Create and run migration

### Medium Priority

6. **Enhanced Feedback Endpoints**
   - PUT /api/v1/feedback/{id} (update feedback)
   - POST /api/v1/feedback (manual feedback creation)
   - POST /api/v1/feedback/{id}/reanalyze (trigger re-analysis)

7. **Analytics Endpoints**
   - GET /api/v1/analytics/sentiment-summary
   - GET /api/v1/analytics/trends
   - GET /api/v1/analytics/aspect-breakdown

8. **Add Redis Caching**
   - Cache frequently accessed feedback/analysis
   - Implement cache invalidation
   - Cache analytics results

9. **Add API Authentication**
   - Implement API key or JWT authentication for feedback endpoints
   - Role-based access control
   - Keep webhook token auth separate

10. **Write Tests**
    - Unit tests for services
    - Integration tests for API endpoints
    - Worker processing tests
    - Webhook authentication tests

### Low Priority

11. **Improve Monitoring**
    - Add structured logging
    - Add metrics (Prometheus)
    - Add error tracking (Sentry)

12. **Documentation**
    - API usage guide
    - Make.com setup guide
    - Deployment guide
    - Architecture diagrams

13. **Frontend Development**
    - Dashboard for viewing feedback
    - Analytics visualizations
    - Admin panel

## Configuration Reference

### Environment Variables

Required variables (defined in .env.example):

```
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db
REDIS_URL=redis://host:port/db
RABBITMQ_URL=amqp://user:pass@host:port/
SECRET_KEY=your-secret-key-here
WEBHOOK_SECRET=your-webhook-secret-here
API_V1_PREFIX=/api/v1
PROJECT_NAME=VoC Analytics System
ENVIRONMENT=development
DEBUG=True
```

**Important Security Notes:**
- `WEBHOOK_SECRET`: Used for authenticating webhook requests via X-Webhook-Token header
- Both `SECRET_KEY` and `WEBHOOK_SECRET` must be changed in production
- Use strong, randomly generated secrets (min 32 characters)

### Queue Names
- `data_ingestion`: Receives new feedback for processing
- `ml_processing`: (Declared but not used yet)

### Processing Status Values
- `pending`: Feedback received, awaiting processing
- `processing`: Currently being analyzed
- `completed`: Analysis finished successfully
- `failed`: Analysis encountered error

### Source Types
- `email`: Email feedback
- `instagram`: Instagram comments/DMs
- `facebook`: Facebook posts/comments
- `google_form`: Google Forms responses
- `google_maps`: Google Maps reviews
- `manual`: Manually entered feedback

### Aspect Categories
Pre-defined aspects for sports facility feedback:
- `equipment`: Gym equipment, sports gear
- `staff`: Employees, trainers, customer service
- `cleanliness`: Hygiene, maintenance
- `atmosphere`: Environment, ambiance
- `price`: Pricing, value for money
- `location`: Accessibility, parking
- `programs`: Classes, training programs
- `amenities`: Facilities (showers, lockers, etc.)

## API Endpoints Reference

### Webhook Endpoints (POST)
**Authentication:** Requires `X-Webhook-Token` header

- `POST /api/v1/webhooks/email`
  - Receives email feedback from Make.com
  - Payload: EmailWebhookPayload (email_id, sender_email, subject, body_text, received_at)
  - Returns: WebhookResponse (status, message, record_id, source_type)
  - Automatically creates feedback record and publishes to queue
  - Handles duplicates gracefully

- `POST /api/v1/webhooks/instagram`
  - Receives Instagram comments from Make.com
  - Payload: InstagramWebhookPayload (comment_id, comment_text, username, media_id, etc.)
  - Returns: WebhookResponse
  - Automatically creates feedback record and publishes to queue
  - Handles duplicates gracefully

### Feedback Endpoints (GET, DELETE)
**Authentication:** None (public - should add auth in production)

- `GET /api/v1/feedback`
  - List feedback records with pagination
  - Query params: page (default: 1), page_size (default: 20, max: 100), source_type, processing_status
  - Returns: FeedbackListResponse (items, total, page, page_size, total_pages)

- `GET /api/v1/feedback/{feedback_id}`
  - Get single feedback record with all analysis results
  - Returns: FeedbackDetailResponse (includes sentiment_results, intent_results, aspect_sentiment_results)
  - 404 if not found

- `DELETE /api/v1/feedback/{feedback_id}`
  - Hard delete feedback record (cascades to analysis results)
  - Returns: 204 No Content on success
  - 404 if not found

### System Endpoints
- `GET /health` - Health check (returns status, service name, environment, version)
- `GET /` - Root endpoint (returns welcome message and API info)
- `GET /docs` - Swagger UI documentation
- `GET /redoc` - ReDoc documentation

## Git Repository Status

**Current Branch:** main
**Recent Commits:**
- `4c5f063`: feat: Initialize VoC Analytics infrastructure and database schema
- `f2f0637`: First commit

**Git Status:** Clean (no uncommitted changes)

## ML Model Considerations

The worker requires ML models for:
1. **Sentiment Analysis**: Text → {positive, neutral, negative} + confidence
2. **Intent Classification**: Text → {feedback, question, complaint, off_topic} + confidence
3. **Aspect-Based Sentiment**: Text → Multiple {aspect, sentiment} pairs + confidence

**Model Options:**
- Fine-tune BERT-based models for each task
- Use zero-shot classification (e.g., facebook/bart-large-mnli)
- Multi-task learning approach
- Consider multilingual support if needed

**Model Storage:**
- Models not currently in repository (.pt/.pth files commented out in .gitignore)
- Decide: commit models or download at runtime
- Worker Dockerfile has PyTorch/Transformers installed

## Critical Questions to Resolve

1. **ML Models**: Use pre-trained models or train custom models on sports facility domain?
   - Consider: WangchanBERTa for Thai language support
   - Or multilingual models (mBERT, XLM-RoBERTa)

2. **✅ ANSWERED: Platform Integration**: Using webhook pattern via Make.com
   - Email and Instagram webhooks implemented
   - Remaining: Facebook, Google Forms, Google Maps

3. **✅ ANSWERED: Processing Pattern**: Real-time async processing via RabbitMQ queue

4. **Authentication for Feedback Endpoints**: Add API key or JWT auth?
   - Webhook endpoints already secured with token auth
   - Feedback endpoints currently public

5. **Rate Limiting**: How to prevent API abuse?
   - Especially important for public feedback endpoints

6. **Data Retention**: How long to keep feedback? Archive strategy?

7. **Redis Use Case**: What specific feature needs Redis caching?
   - Analytics results caching?
   - Rate limiting storage?
   - Session management (if adding auth)?

8. **Frontend**: Will there be a web UI? Technology stack?

## Contact & Resources

**Repository:** Local (not pushed to remote)
**Working Directory:** C:\Users\unduood\Desktop\VoC Sports Facility

This document should be updated as the project evolves.
