# رفع المشروع على GitHub

## ماذا نرفع؟

- الكود داخل `src/`
- السكربتات داخل `scripts/`
- الواجهة `app.py`
- `README.md`
- `requirements.txt`
- التقرير `reports/report_ar.md`
- صورة التقييم `reports/figures/evaluation_metrics.png`
- نتائج التقييم الصغيرة `artifacts/evaluation_metrics.csv`
- ملف metadata الصغير `artifacts/dataset_metadata.json`
- Notebook التدريب على Colab داخل `notebooks/`

## ماذا لا نرفع؟

- Dataset الكاملة.
- `collection.tsv`
- `collectionandqueries.tar.gz`
- قاعدة SQLite.
- ملف الفهرس `search_index.joblib`.
- مجلد `.codex_deps`.

هذه الملفات كبيرة، وGitHub قد يرفضها أو تجعل المستودع غير عملي.

## أوامر الرفع

```powershell
git add .
git commit -m "Complete information retrieval system"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

استبدل:

- `YOUR_USERNAME` باسم حساب GitHub.
- `YOUR_REPOSITORY` باسم الريبو.

## ملاحظة مهمة في README

الـ README يشرح كيف يتم تنزيل Dataset وبناء الملفات الثقيلة محلياً، لذلك لا نحتاج رفعها على GitHub.
