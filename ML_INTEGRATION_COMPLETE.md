# 🤖 ML Integration Complete - Summary

## ✅ สิ่งที่ทำเสร็จแล้ว

### 1. **NLP Service Module** (`worker/app/nlp_service.py`)
สร้าง service module ที่รวม 3 ML models:
- ✅ **ABSAService** - Aspect-Based Sentiment Analysis (8 aspects)
- ✅ **IntentClassificationService** - Intent Classification (multi-label)
- ✅ **SentimentAnalysisService** - Overall Sentiment Analysis
- ✅ **ThaiNLPService** - Unified service ที่รวมทั้ง 3 models
- ✅ Singleton pattern สำหรับ performance

**Models ที่ใช้:**
1. `unduood/phayathaibert-absa-sports-facility-v2` - ABSA
2. `unduood/phayathaibert-intent-classification-sports-facility` - Intent
3. `poom-sci/WangchanBERTa-finetuned-sentiment` - Sentiment

### 2. **Database Integration** (`worker/app/database.py` + `worker/app/models/`)
- ✅ สร้าง async database session management
- ✅ Copy models จาก backend มาที่ worker
- ✅ **แก้ไข timestamp bug** - เปลี่ยนจาก String เป็น TIMESTAMP(timezone=True)

**Files Created:**
- `worker/app/database.py` - Database connection และ session factory
- `worker/app/models/__init__.py` - Model exports
- `worker/app/models/base.py` - UUIDMixin, TimestampMixin
- `worker/app/models/feedback.py` - FeedbackRecord model
- `worker/app/models/analysis.py` - SentimentResult, IntentResult, AspectSentimentResult (FIXED)

### 3. **Worker Processing Logic** (`worker/app/main.py`)
- ✅ โหลด ML models ตอน startup (pre-loading)
- ✅ Implement `process_feedback_analysis()` - async function สำหรับ ML processing
- ✅ Fetch feedback จาก database
- ✅ Run ML inference
- ✅ Store results ใน 3 tables: sentiment_results, intent_results, aspect_sentiment_results
- ✅ Update processing_status (pending → processing → completed/failed)
- ✅ Error handling และ rollback

**Processing Flow:**
```
1. Receive message from RabbitMQ {record_id, action}
2. Fetch FeedbackRecord from database
3. Update status to "processing"
4. Run ML analysis (ABSA + Intent + Sentiment)
5. Store results in database
6. Update status to "completed"
7. Acknowledge message
```

### 4. **Dependencies Update** (`worker/requirements.txt`)
- ✅ เพิ่ม `huggingface_hub>=0.16.0` สำหรับโหลด model configs

### 5. **Database Migration** (แก้ไข Timestamp Bug)
- ✅ สร้าง migration: `197265c769fa_fix_timestamp_types_in_analysis_tables.py`
- ✅ ALTER TABLE สำหรับ 3 tables (sentiment_results, intent_results, aspect_sentiment_results)
- ✅ เปลี่ยน `created_at` จาก String เป็น TIMESTAMP WITH TIME ZONE

**Backend Models Fixed:**
- ✅ `backend/app/models/analysis.py` - แก้ไข created_at type ใน 3 classes

---

## 📋 การทดสอบระบบ

### Prerequisites
1. Docker และ Docker Compose ติดตั้งแล้ว
2. ทุก services (postgres, rabbitmq, backend, worker) รันอยู่

### ขั้นตอนการทดสอบ

#### 1. **Run Database Migration (แก้ไข Timestamp)**
```bash
cd "C:\Users\unduood\Desktop\VoC Sports Facility\voc-analytics"

# ถ้ารัน Docker
docker-compose exec backend alembic upgrade head

# หรือถ้ารัน local
cd backend
alembic upgrade head
```

**Expected Output:**
```
INFO  [alembic.runtime.migration] Running upgrade e7dd65e74927 -> 197265c769fa, fix_timestamp_types_in_analysis_tables
```

#### 2. **Rebuild Worker Docker Image** (เพื่อให้มี code ใหม่)
```bash
cd "C:\Users\unduood\Desktop\VoC Sports Facility\voc-analytics"

# Stop worker
docker-compose stop worker

# Rebuild และ start
docker-compose up -d --build worker

# ดู logs
docker-compose logs -f worker
```

**Expected Output (Worker Logs):**
```
============================================================
🤖 Initializing ML models...
============================================================
Loading ABSA model from unduood/phayathaibert-absa-sports-facility-v2...
✅ ABSAService loaded - Aspects: ['Equipment', 'Staff', ...]
Loading Intent model from unduood/phayathaibert-intent-classification-sports-facility...
✅ IntentClassificationService loaded - Labels: ['feedback', 'complaint', 'question', 'off_topic']
Loading Sentiment model from poom-sci/WangchanBERTa-finetuned-sentiment...
✅ SentimentAnalysisService loaded - Labels: ['pos', 'neg', 'neu']
============================================================
✅ All models loaded successfully!
============================================================
Worker is ready. Waiting for messages on queue 'data_ingestion'...
```

#### 3. **ทดสอบส่ง Feedback ผ่าน Webhook**

**Option A: ใช้ curl (Windows PowerShell)**
```powershell
# ตั้งค่า webhook secret
$WEBHOOK_SECRET = "dev-webhook-secret-12345"

# ส่ง email feedback
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/webhooks/email" `
  -Method POST `
  -Headers @{"X-Webhook-Token"=$WEBHOOK_SECRET; "Content-Type"="application/json"} `
  -Body (@{
    email_id = "test-001"
    sender_email = "customer@example.com"
    subject = "ชอบมาก"
    body = "อุปกรณ์ออกกำลังกายดีมาก พนักงานน่ารัก แต่ที่จอดรถน้อยไป มีโปรโมชั่นใหม่ไหมครับ"
    received_at = "2025-01-07T12:00:00Z"
  } | ConvertTo-Json)
```

**Option B: ใช้ Python**
```python
import requests

WEBHOOK_SECRET = "dev-webhook-secret-12345"

response = requests.post(
    "http://localhost:8000/api/v1/webhooks/email",
    headers={"X-Webhook-Token": WEBHOOK_SECRET},
    json={
        "email_id": "test-001",
        "sender_email": "customer@example.com",
        "subject": "ชอบมาก",
        "body": "อุปกรณ์ออกกำลังกายดีมาก พนักงานน่ารัก แต่ที่จอดรถน้อยไป มีโปรโมชั่นใหม่ไหมครับ",
        "received_at": "2025-01-07T12:00:00Z"
    }
)
print(response.json())
```

**Expected Response:**
```json
{
  "status": "success",
  "message": "Email feedback ingested successfully",
  "record_id": "..."
}
```

#### 4. **ตรวจสอบ Worker Logs**
```bash
docker-compose logs -f worker
```

**Expected Output:**
```
Received message: {'record_id': '...', 'action': 'analyze', 'timestamp': '...'}
Fetching feedback record: ...
Processing feedback: อุปกรณ์ออกกำลังกายดีมาก พนักงานน่ารัก...
Running ML analysis...
Sentiment: pos (0.95)
Intent: ['feedback', 'question']
Aspects analyzed: 3 found
✅ Successfully processed feedback: ...
Message acknowledged
```

#### 5. **ตรวจสอบผลลัพธ์ใน Database**

**Option A: ใช้ psql**
```bash
docker-compose exec postgres psql -U vocuser -d vocdb

-- ดู feedback record
SELECT id, text_content, processing_status FROM feedback_records ORDER BY created_at DESC LIMIT 1;

-- ดู sentiment result
SELECT * FROM sentiment_results ORDER BY created_at DESC LIMIT 1;

-- ดู intent results
SELECT * FROM intent_results ORDER BY created_at DESC LIMIT 5;

-- ดู aspect sentiment results
SELECT aspect, sentiment, confidence FROM aspect_sentiment_results ORDER BY created_at DESC LIMIT 10;
```

**Option B: ใช้ API**
```bash
# GET feedback detail (รวม analysis results)
curl http://localhost:8000/api/v1/feedback/{record_id}
```

**Expected JSON Response:**
```json
{
  "id": "...",
  "source_type": "email",
  "text_content": "อุปกรณ์ออกกำลังกายดีมาก...",
  "processing_status": "completed",
  "created_at": "2025-01-07T12:00:00Z",
  "sentiment_results": [
    {
      "sentiment": "pos",
      "confidence": 0.95,
      "created_at": "2025-01-07T12:00:05Z"
    }
  ],
  "intent_results": [
    {"intent": "feedback", "confidence": 0.92},
    {"intent": "question", "confidence": 0.67}
  ],
  "aspect_sentiment_results": [
    {"aspect": "Equipment", "sentiment": "positive", "confidence": 0.94},
    {"aspect": "Staff", "sentiment": "positive", "confidence": 0.89},
    {"aspect": "Location", "sentiment": "negative", "confidence": 0.78}
  ]
}
```

---

## 🐛 Troubleshooting

### Issue: Worker ไม่โหลด Models
**Symptoms:** Worker crash หรือ error "Failed to load ML models"

**Solutions:**
1. ตรวจสอบ internet connection (ต้อง download models จาก HuggingFace)
2. ตรวจสอบ RAM (แต่ละ model ใช้ ~500MB-1GB)
3. ดู detailed error logs:
   ```bash
   docker-compose logs worker | grep -i error
   ```

### Issue: Database Connection Error
**Symptoms:** "could not connect to server", "connection refused"

**Solutions:**
1. ตรวจสอบว่า PostgreSQL รันอยู่:
   ```bash
   docker-compose ps postgres
   ```
2. ตรวจสอบ DATABASE_URL ใน worker config:
   ```bash
   docker-compose exec worker env | grep DATABASE
   ```

### Issue: RabbitMQ Connection Failed
**Symptoms:** "Connection refused", "Could not connect to RabbitMQ"

**Solutions:**
1. ตรวจสอบว่า RabbitMQ รันอยู่:
   ```bash
   docker-compose ps rabbitmq
   ```
2. เข้า Management UI: http://localhost:15672 (user: vocuser, pass: vocpassword)
3. ตรวจสอบ queue "data_ingestion" ใน Queues tab

### Issue: Models โหลดช้า
**Expected:** การโหลด models ครั้งแรกใช้เวลา 2-5 นาที (download + load)

**Tips:**
- Models จะถูก cache ไว้ใน Docker volume
- ครั้งต่อไปจะโหลดเร็วขึ้น (ไม่ต้อง download ใหม่)

---

## 📊 Performance Notes

### Resource Usage (per Worker)
- **RAM:** ~2-3 GB (3 models loaded)
- **CPU:** Spike during inference, idle when waiting
- **Disk:** ~2 GB (model files cached)

### Processing Speed
- **GPU (CUDA):** ~1-2 seconds per feedback
- **CPU:** ~3-5 seconds per feedback

### Scaling
- เพิ่ม worker instances: แก้ไข `docker-compose.yml`
  ```yaml
  worker:
    deploy:
      replicas: 3  # เพิ่มเป็น 3 workers
  ```
- RabbitMQ จะ load balance ให้อัตโนมัติ (round-robin)

---

## 🔄 Data Flow Summary

```
┌─────────────┐
│ Make.com    │
└──────┬──────┘
       │ HTTP POST
       ▼
┌─────────────────────────────────────────┐
│ FastAPI Backend                         │
│  POST /api/v1/webhooks/{source}         │
│    1. Validate webhook token            │
│    2. Create FeedbackRecord (pending)   │
│    3. Publish to RabbitMQ               │
└──────┬──────────────────────────────────┘
       │ AMQP Message
       │ {record_id, action}
       ▼
┌─────────────────────────────────────────┐
│ RabbitMQ Queue: data_ingestion          │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│ Worker (ML Processing)                  │
│  1. Fetch FeedbackRecord                │
│  2. Update status: processing           │
│  3. Run ML Analysis:                    │
│     • Sentiment Analysis                │
│     • Intent Classification             │
│     • Aspect-Based Sentiment            │
│  4. Store Results:                      │
│     • sentiment_results                 │
│     • intent_results                    │
│     • aspect_sentiment_results          │
│  5. Update status: completed            │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│ PostgreSQL Database                     │
│  • feedback_records (completed)         │
│  • sentiment_results                    │
│  • intent_results                       │
│  • aspect_sentiment_results             │
└─────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│ API: GET /api/v1/feedback/{id}          │
│ Returns feedback + analysis results     │
└─────────────────────────────────────────┘
```

---

## 📝 Next Steps (Optional Improvements)

1. **Monitoring & Metrics**
   - Add Prometheus metrics (processing time, success rate)
   - Add health check endpoint in worker
   - Grafana dashboard

2. **Error Handling**
   - Dead letter queue สำหรับ failed messages
   - Retry mechanism with exponential backoff
   - Alert notifications (email/Slack)

3. **Performance Optimization**
   - Batch processing (process multiple feedbacks at once)
   - Model quantization (reduce RAM usage)
   - GPU support (faster inference)

4. **Testing**
   - Unit tests สำหรับ NLP service
   - Integration tests สำหรับ worker
   - Load testing

5. **Production Readiness**
   - Change default credentials
   - Add API authentication
   - Rate limiting
   - CORS configuration
   - HTTPS/SSL

---

## 🎉 Summary

**Status:** ✅ **ML Integration Complete and Ready for Testing**

**What Works:**
- ✅ 3 ML models integrated (ABSA, Intent, Sentiment)
- ✅ Full pipeline from webhook → ML analysis → database
- ✅ Automatic processing via RabbitMQ
- ✅ Timestamp bug fixed
- ✅ Database migration created

**Ready to:**
1. Run migration (`alembic upgrade head`)
2. Rebuild worker (`docker-compose up -d --build worker`)
3. Send test feedback via webhook
4. See ML results in database

**Next:** Follow the testing steps above to verify everything works! 🚀