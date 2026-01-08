# Database Schema Improvement Recommendations

## สรุปปัญหาที่พบ

### 1. ตาราง feedback_records
- ❌ คอลัมน์ `id` อยู่ตำแหน่งที่ 7 (ควรอยู่ตำแหน่งแรก)
- ❌ ใน `analysis_summary` JSONB ใช้ชื่อ field `probabilities` ซึ่งควรเป็น `sentiment_probabilities`

### 2. ตาราง sentiment_results
- ❌ คอลัมน์ `id` อยู่ตำแหน่งที่ 5 (ควรอยู่ตำแหน่งแรก)
- ❌ ลำดับคอลัมน์ไม่สม่ำเสมอกับตาราง analysis อื่นๆ

### 3. ตาราง intent_results
- ❌ คอลัมน์ `id` อยู่ตำแหน่งที่ 5 (ควรอยู่ตำแหน่งแรก)
- ❌ ลำดับคอลัมน์ไม่สม่ำเสมอกับตาราง analysis อื่นๆ

### 4. ตาราง aspect_sentiment_results
- ❌ คอลัมน์ `id` อยู่ตำแหน่งที่ 6 (ควรอยู่ตำแหน่งแรก)
- ❌ ลำดับคอลัมน์ไม่สม่ำเสมอกับตาราง analysis อื่นๆ

---

## Best Practices สำหรับการจัดลำดับคอลัมน์

### หลักการจัดลำดับคอลัมน์ (Column Ordering Convention)

```
1. Primary Key (id)              - อยู่ซ้ายสุดเสมอ เพื่อง่ายต่อการอ้างอิง
2. Foreign Keys                  - อยู่ถัดจาก PK เพื่อแสดง relationships
3. Core Data Fields              - ข้อมูลหลักของ entity (ชื่อ, ค่า, status)
4. Additional Attributes         - คุณลักษณะเพิ่มเติม (confidence, source)
5. Edit History                  - ประวัติการแก้ไข (original_*)
6. Audit Timestamps              - created_at, updated_at, updated_by
7. Soft Delete Flag              - is_deleted
8. Comments/Notes                - อยู่ท้ายสุด
```

### ข้อดีของการจัดลำดับที่ดี

✅ **อ่านง่าย** - Developer เห็น id และ FK ทันทีเมื่อ SELECT *
✅ **Debug ง่าย** - ข้อมูลสำคัญอยู่ด้านซ้าย
✅ **สม่ำเสมอ** - ตารางที่คล้ายกันมีโครงสร้างเหมือนกัน
✅ **Maintainable** - ง่ายต่อการทำความเข้าใจและดูแลระบบ
✅ **SQL Convention** - ตามมาตรฐานที่ใช้กันโดยทั่วไป

---

## โครงสร้างที่แนะนำ (Recommended Schema)

### 1. feedback_records (แนะนำ)

```sql
Column Order:
┌─────┬───────────────────┬──────────────────────────┬─────────────────────────┐
│ No. │ Column Name       │ Type                     │ Group                   │
├─────┼───────────────────┼──────────────────────────┼─────────────────────────┤
│  1  │ id                │ UUID                     │ Primary Key             │
│  2  │ source_type       │ VARCHAR(50)              │ Source Info             │
│  3  │ source_id         │ VARCHAR(255)             │ Source Info             │
│  4  │ text_content      │ TEXT                     │ Core Content            │
│  5  │ raw_data          │ JSONB                    │ Additional Content      │
│  6  │ created_at_source │ TIMESTAMP WITH TIME ZONE │ Source Timestamp        │
│  7  │ processing_status │ VARCHAR(20)              │ Status                  │
│  8  │ analysis_summary  │ JSONB                    │ Analysis Summary        │
│  9  │ created_at        │ TIMESTAMP WITH TIME ZONE │ Audit Timestamp         │
│ 10  │ updated_at        │ TIMESTAMP WITH TIME ZONE │ Audit Timestamp         │
└─────┴───────────────────┴──────────────────────────┴─────────────────────────┘

Logical Grouping:
1. PK (id)
2. Source Info (source_type, source_id)
3. Content (text_content, raw_data, created_at_source)
4. Status (processing_status)
5. Analysis (analysis_summary)
6. Audit (created_at, updated_at)
```

### 2. sentiment_results (แนะนำ)

```sql
Column Order:
┌─────┬─────────────────────┬──────────────────────────┬─────────────────────────┐
│ No. │ Column Name         │ Type                     │ Group                   │
├─────┼─────────────────────┼──────────────────────────┼─────────────────────────┤
│  1  │ id                  │ UUID                     │ Primary Key             │
│  2  │ feedback_id         │ UUID (FK)                │ Foreign Key             │
│  3  │ sentiment           │ VARCHAR(20)              │ Core Field              │
│  4  │ confidence          │ FLOAT                    │ Probability             │
│  5  │ source              │ VARCHAR(20)              │ Audit Source            │
│  6  │ original_sentiment  │ VARCHAR(20)              │ Edit History            │
│  7  │ original_confidence │ FLOAT                    │ Edit History            │
│  8  │ created_at          │ TIMESTAMP WITH TIME ZONE │ Audit Timestamp         │
│  9  │ updated_at          │ TIMESTAMP WITH TIME ZONE │ Audit Timestamp         │
│ 10  │ updated_by          │ UUID                     │ Audit User              │
│ 11  │ is_deleted          │ BOOLEAN                  │ Soft Delete             │
│ 12  │ notes               │ TEXT                     │ Comments                │
└─────┴─────────────────────┴──────────────────────────┴─────────────────────────┘

Logical Grouping:
1. PK (id)
2. FK (feedback_id)
3. Core Data (sentiment, confidence)
4. Audit Source (source)
5. Edit History (original_*)
6. Timestamps (created_at, updated_at, updated_by)
7. Soft Delete (is_deleted)
8. Notes (notes)
```

### 3. intent_results (แนะนำ)

```sql
Column Order:
┌─────┬─────────────────────┬──────────────────────────┬─────────────────────────┐
│ No. │ Column Name         │ Type                     │ Group                   │
├─────┼─────────────────────┼──────────────────────────┼─────────────────────────┤
│  1  │ id                  │ UUID                     │ Primary Key             │
│  2  │ feedback_id         │ UUID (FK)                │ Foreign Key             │
│  3  │ intent              │ VARCHAR(50)              │ Core Field              │
│  4  │ confidence          │ FLOAT                    │ Probability             │
│  5  │ source              │ VARCHAR(20)              │ Audit Source            │
│  6  │ original_intent     │ VARCHAR(50)              │ Edit History            │
│  7  │ original_confidence │ FLOAT                    │ Edit History            │
│  8  │ created_at          │ TIMESTAMP WITH TIME ZONE │ Audit Timestamp         │
│  9  │ updated_at          │ TIMESTAMP WITH TIME ZONE │ Audit Timestamp         │
│ 10  │ updated_by          │ UUID                     │ Audit User              │
│ 11  │ is_deleted          │ BOOLEAN                  │ Soft Delete             │
│ 12  │ notes               │ TEXT                     │ Comments                │
└─────┴─────────────────────┴──────────────────────────┴─────────────────────────┘

Logical Grouping:
1. PK (id)
2. FK (feedback_id)
3. Core Data (intent, confidence)
4. Audit Source (source)
5. Edit History (original_*)
6. Timestamps (created_at, updated_at, updated_by)
7. Soft Delete (is_deleted)
8. Notes (notes)
```

### 4. aspect_sentiment_results (แนะนำ)

```sql
Column Order:
┌─────┬─────────────────────┬──────────────────────────┬─────────────────────────┐
│ No. │ Column Name         │ Type                     │ Group                   │
├─────┼─────────────────────┼──────────────────────────┼─────────────────────────┤
│  1  │ id                  │ UUID                     │ Primary Key             │
│  2  │ feedback_id         │ UUID (FK)                │ Foreign Key             │
│  3  │ aspect              │ VARCHAR(50)              │ Core Field 1            │
│  4  │ sentiment           │ VARCHAR(20)              │ Core Field 2            │
│  5  │ confidence          │ FLOAT                    │ Probability             │
│  6  │ source              │ VARCHAR(20)              │ Audit Source            │
│  7  │ original_sentiment  │ VARCHAR(20)              │ Edit History            │
│  8  │ original_confidence │ FLOAT                    │ Edit History            │
│  9  │ created_at          │ TIMESTAMP WITH TIME ZONE │ Audit Timestamp         │
│ 10  │ updated_at          │ TIMESTAMP WITH TIME ZONE │ Audit Timestamp         │
│ 11  │ updated_by          │ UUID                     │ Audit User              │
│ 12  │ is_deleted          │ BOOLEAN                  │ Soft Delete             │
│ 13  │ notes               │ TEXT                     │ Comments                │
└─────┴─────────────────────┴──────────────────────────┴─────────────────────────┘

Logical Grouping:
1. PK (id)
2. FK (feedback_id)
3. Core Data (aspect, sentiment, confidence)
4. Audit Source (source)
5. Edit History (original_*)
6. Timestamps (created_at, updated_at, updated_by)
7. Soft Delete (is_deleted)
8. Notes (notes)
```

---

## การแก้ไข analysis_summary JSONB Structure

### ปัญหาปัจจุบัน

```json
{
  "sentiment": {
    "label": "pos",
    "confidence": 0.9026,
    "probabilities": {              ← ❌ ชื่อไม่ชัดเจน
      "pos": 0.9026,
      "neg": 0.0052,
      "neu": 0.0922
    }
  }
}
```

### โครงสร้างที่แนะนำ

```json
{
  "sentiment": {
    "label": "pos",
    "confidence": 0.9026,
    "sentiment_probabilities": {    ← ✅ ชัดเจนว่าเป็น probabilities ของ sentiment
      "pos": 0.9026,
      "neg": 0.0052,
      "neu": 0.0922
    },
    "source": "model",
    "edited": false
  },
  "intents": [
    {
      "label": "Feedback",
      "confidence": 0.9977,
      "source": "model",
      "edited": false
    }
  ],
  "aspects": [
    {
      "aspect": "Equipment",
      "aspect_thai": "อุปกรณ์",
      "sentiment": "positive",
      "confidence": 0.9998,
      "source": "model",
      "edited": false
    }
  ],
  "summary_stats": {
    "total_aspects_analyzed": 8,
    "aspects_with_sentiment": 4,
    "positive_aspects": 4,
    "negative_aspects": 0,
    "neutral_aspects": 0,
    "model_predictions": 4,
    "user_corrections": 0,
    "user_additions": 0
  }
}
```

### เหตุผลในการเปลี่ยนชื่อ

✅ **ชัดเจนขึ้น**: `sentiment_probabilities` บอกได้ทันทีว่าเป็น probabilities ของโมเดล sentiment analysis
✅ **แยกจาก ABSA**: ไม่สับสนกับ confidence scores ของ aspect-based sentiment
✅ **Maintainable**: ถ้ามีโมเดลอื่นเพิ่มเติมในอนาคต เช่น `intent_probabilities` จะมี naming pattern ที่สม่ำเสมอ
✅ **Self-documenting**: อ่านโค้ดแล้วเข้าใจทันทีโดยไม่ต้องดู documentation

---

## วิธีการ Migrate Database Schema

### Option 1: PostgreSQL Column Reordering (Recreate Table) ⚠️

**คำเตือน**: PostgreSQL ไม่รองรับการจัดเรียงคอลัมน์ใหม่โดยตรง ต้อง recreate table

```sql
-- Step 1: สร้างตารางใหม่ด้วยลำดับที่ถูกต้อง
CREATE TABLE feedback_records_new (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type VARCHAR(50) NOT NULL,
    source_id VARCHAR(255),
    text_content TEXT NOT NULL,
    raw_data JSONB,
    created_at_source TIMESTAMP WITH TIME ZONE,
    processing_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    analysis_summary JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Step 2: Copy ข้อมูลจากตารางเก่า
INSERT INTO feedback_records_new
SELECT
    id, source_type, source_id, text_content, raw_data,
    created_at_source, processing_status, analysis_summary,
    created_at, updated_at
FROM feedback_records;

-- Step 3: Drop ตารางเก่าและ rename ตารางใหม่
DROP TABLE feedback_records CASCADE;
ALTER TABLE feedback_records_new RENAME TO feedback_records;

-- Step 4: Recreate indexes, constraints, và foreign keys
-- (ดูรายละเอียดใน migration script ด้านล่าง)
```

### Option 2: ไม่ Migrate (แนะนำ) ✅

**เหตุผล**:
- การจัดเรียงคอลัมน์ใน PostgreSQL **ไม่มีผลต่อ Performance**
- Downtime และความเสี่ยงสูง
- ใช้งานได้ปกติ เพียงแค่ไม่สวยงามเมื่อ `SELECT *`

**ข้อแนะนำ**:
1. ✅ **ปล่อยให้โครงสร้างตารางเป็นอย่างปัจจุบัน** (ไม่ต้อง migrate)
2. ✅ **ใช้ SELECT explicit columns แทน SELECT *** ใน production code
3. ✅ **แก้ชื่อ `probabilities` → `sentiment_probabilities`** (แก้ใน worker code เท่านั้น)
4. ✅ **ใช้โครงสร้างที่แนะนำสำหรับตารางใหม่ในอนาคต**

---

## แนวทางที่แนะนำ (Recommended Approach)

### 1. ไม่ต้อง Migrate ตารางที่มีอยู่ ✅

**เหตุผล**:
- ไม่มี performance impact
- Downtime และความเสี่ยงไม่คุ้มค่า
- ข้อมูลมีอยู่แล้ว ทำงานได้ปกติ

### 2. แก้ชื่อ field ใน JSONB (analysis_summary) ✅

แก้ไขใน: `voc-analytics/worker/app/main.py`

```python
# ❌ Before (ปัจจุบัน)
analysis_summary = {
    "sentiment": {
        "label": sentiment_label,
        "confidence": sentiment_confidence,
        "probabilities": sentiment_probs,  # ← เปลี่ยนที่นี่
        # ...
    }
}

# ✅ After (แนะนำ)
analysis_summary = {
    "sentiment": {
        "label": sentiment_label,
        "confidence": sentiment_confidence,
        "sentiment_probabilities": sentiment_probs,  # ← ใช้ชื่อใหม่
        # ...
    }
}
```

### 3. ใช้ Explicit Column Selection ใน Code ✅

```python
# ❌ Bad - ใช้ SELECT *
feedback = session.execute(
    select(FeedbackRecord)
).scalars().all()

# ✅ Good - ระบุคอลัมน์ที่ต้องการชัดเจน
feedback = session.execute(
    select(
        FeedbackRecord.id,
        FeedbackRecord.source_type,
        FeedbackRecord.text_content,
        FeedbackRecord.processing_status,
        FeedbackRecord.analysis_summary
    )
).all()
```

### 4. Update ORM Models ให้สอดคล้อง (ไม่บังคับ)

แก้ใน: `backend/app/models/*.py`

เปลี่ยนลำดับการประกาศ fields ใน SQLAlchemy models ให้ตรงกับโครงสร้างที่แนะนำ
(ไม่กระทบ database schema ที่มีอยู่ แค่ทำให้โค้ดอ่านง่ายขึ้น)

```python
class SentimentResult(Base, UUIDMixin):
    __tablename__ = "sentiment_results"

    # ✅ เรียงตามลำดับที่แนะนำ (แต่ไม่เปลี่ยน DB schema)
    # 1. PK - มาจาก UUIDMixin
    # 2. FK
    feedback_id: Mapped[UUID] = mapped_column(...)

    # 3. Core Data
    sentiment: Mapped[str] = mapped_column(...)
    confidence: Mapped[Optional[float]] = mapped_column(...)

    # 4. Audit Source
    source: Mapped[str] = mapped_column(...)

    # 5. Edit History
    original_sentiment: Mapped[Optional[str]] = mapped_column(...)
    original_confidence: Mapped[Optional[float]] = mapped_column(...)

    # 6. Timestamps
    created_at: Mapped[datetime] = mapped_column(...)
    updated_at: Mapped[Optional[datetime]] = mapped_column(...)
    updated_by: Mapped[Optional[UUID]] = mapped_column(...)

    # 7. Soft Delete
    is_deleted: Mapped[bool] = mapped_column(...)

    # 8. Notes
    notes: Mapped[Optional[str]] = mapped_column(...)
```

### 5. Document เพื่ออ้างอิงในอนาคต ✅

เก็บเอกสารนี้ไว้เป็น reference สำหรับ:
- การสร้างตารางใหม่ในอนาคต
- การ review database schema
- การอบรม developer ใหม่

---

## Summary & Action Items

### ✅ ทำได้เลย (Low Risk, High Value)

1. **แก้ชื่อ `probabilities` → `sentiment_probabilities`** ใน worker code
   - File: `voc-analytics/worker/app/main.py`
   - Impact: ไม่มี breaking change (field ใหม่ถูกเพิ่ม, field เก่ายังใช้ได้)

2. **ใช้ explicit column selection** ใน SQL queries
   - แทนที่ `SELECT *` ด้วยการระบุ columns ชัดเจน
   - Impact: Performance ดีขึ้น, maintainable

3. **Update ORM models** ให้เรียงลำดับตามโครงสร้างที่แนะนำ
   - ไม่กระทบ database schema
   - ทำให้โค้ดอ่านง่ายขึ้น

### ⚠️ ไม่แนะนำ (High Risk, Low Value)

4. **Migrate database schema** เพื่อจัดเรียงคอลัมน์ใหม่
   - Requires downtime
   - High risk of data loss
   - No performance benefit
   - ปล่อยให้เป็นตามปัจจุบันดีกว่า

### 📋 สำหรับตารางใหม่ในอนาคต

5. **ใช้โครงสร้างที่แนะนำในเอกสารนี้** เมื่อสร้างตารางใหม่
   - ตั้งแต่ตอนออกแบบ migration แรก
   - ทำให้ระบบมีความสม่ำเสมอมากขึ้นเรื่อยๆ

---

## References

- [PostgreSQL Column Ordering Best Practices](https://wiki.postgresql.org/wiki/Don%27t_Do_This#Don.27t_use_SELECT_.2A)
- [SQLAlchemy Column Ordering](https://docs.sqlalchemy.org/en/20/faq/metadata_schema.html)
- [Database Normalization Guidelines](https://en.wikipedia.org/wiki/Database_normalization)

---

**Created**: 2026-01-08
**Author**: VoC Analytics Team
**Status**: Recommendation Document
