# شرح استخدام Colab للمشروع

يستخدم Colab للتدريب وبناء الفهارس والتقييم فقط. بعد انتهاء التدريب نحفظ `artifacts` و`reports`، ثم تعمل نسخة العرض المحلية من الملفات الجاهزة دون إعادة التدريب.

## Dataset النهائية

- `clinicaltrials/2017/trec-pm-2017`
- عدد الوثائق: `241,006`
- تم استخدام Dataset كاملة.
- تحتوي على queries وqrels للتقييم الرسمي.

## التدريب الكامل

```bash
PYTHONPATH=src python scripts/prepare.py \
  --dataset clinicaltrials/2017/trec-pm-2017 \
  --max-docs 0 \
  --max-queries 0 \
  --embedding-dims 64 \
  --max-features 30000 \
  --min-df 2 \
  --max-df 0.95
```

## التقييم

```bash
PYTHONPATH=src python scripts/evaluate.py \
  --dataset clinicaltrials/2017/trec-pm-2017 \
  --max-queries 0 \
  --depth 1000

PYTHONPATH=src python scripts/evaluate.py \
  --dataset clinicaltrials/2017/trec-pm-2017 \
  --max-queries 0 \
  --depth 1000 \
  --refine

PYTHONPATH=src python scripts/evaluate_bert.py
PYTHONPATH=src python scripts/evaluate_rag.py
```

## العرض المحلي

بعد تنزيل `artifacts` و`reports` إلى المشروع:

```powershell
.\run_app.cmd
```

ولتشغيل REST API:

```powershell
.\run_api.cmd
```

## نقاط يجب فهمها

- raw text محفوظ في SQLite ويُقرأ حسب `doc_id` وقت query.
- TF-IDF وBM25 مبنيان على النص المنظف لكامل Dataset.
- LSA هو embedding baseline خفيف.
- Sentence-BERT يعيد ترتيب أفضل مرشحي BM25 دلالياً.
- Hybrid Parallel يستخدم score fusion.
- Hybrid Serial يستخدم BM25 ثم embedding reranking.
- RAG يبني إجابة مؤرضة مع evidence وcitations من الوثائق الأصلية.
