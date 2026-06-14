import csv
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".codex_deps"))

import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


FINAL_DIR = ROOT / "reports" / "final"
SCREENSHOTS_DIR = ROOT / "reports" / "screenshots"
FIGURES_DIR = ROOT / "reports" / "figures"
ARTIFACTS_DIR = ROOT / "artifacts"
PDF_PATH = FINAL_DIR / "تقرير_مشروع_استرجاع_المعلومات_النهائي.pdf"

TEAM = [
    ("الخضر الديواني", "تجهيز Dataset، إدارة qrels، التدريب على Colab، وتكامل الملفات النهائية."),
    ("نايا سعدون", "المعالجة المسبقة، معالجة الاستعلام، وتحسين الاستعلام."),
    ("حلا العوض", "TF-IDF، LSA Embedding، وتمثيل الوثائق والاستعلامات."),
    ("ليث ضاهر", "BM25، الاسترجاع الهجين التسلسلي والمتوازي، والترتيب."),
    ("نوال صالح", "التقييم، واجهة Streamlit، RAG، وتجهيز التقرير."),
]


def rtl(text):
    return get_display(arabic_reshaper.reshape(str(text)))


def has_arabic(text):
    return bool(re.search(r"[\u0600-\u06ff]", str(text)))


def display(text):
    text = str(text)
    return rtl(text) if has_arabic(text) else text


def read_csv(name):
    with (ARTIFACTS_DIR / name).open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


pdfmetrics.registerFont(TTFont("Arial", "C:/Windows/Fonts/arial.ttf"))
pdfmetrics.registerFont(TTFont("Arial-Bold", "C:/Windows/Fonts/arialbd.ttf"))

styles = getSampleStyleSheet()
TITLE = ParagraphStyle(
    "ArabicTitle",
    parent=styles["Title"],
    fontName="Arial-Bold",
    fontSize=23,
    leading=32,
    alignment=TA_CENTER,
    textColor=colors.HexColor("#1F4E79"),
    spaceAfter=14,
)
SUBTITLE = ParagraphStyle(
    "ArabicSubtitle",
    parent=styles["Heading2"],
    fontName="Arial-Bold",
    fontSize=16,
    leading=23,
    alignment=TA_CENTER,
    textColor=colors.HexColor("#C00000"),
    spaceAfter=12,
)
H1 = ParagraphStyle(
    "ArabicH1",
    parent=styles["Heading1"],
    fontName="Arial-Bold",
    fontSize=16,
    leading=23,
    alignment=TA_RIGHT,
    textColor=colors.HexColor("#1F4E79"),
    spaceBefore=10,
    spaceAfter=8,
)
H2 = ParagraphStyle(
    "ArabicH2",
    parent=styles["Heading2"],
    fontName="Arial-Bold",
    fontSize=13,
    leading=19,
    alignment=TA_RIGHT,
    textColor=colors.HexColor("#404040"),
    spaceBefore=7,
    spaceAfter=5,
)
BODY = ParagraphStyle(
    "ArabicBody",
    parent=styles["BodyText"],
    fontName="Arial",
    fontSize=10.7,
    leading=18,
    alignment=TA_RIGHT,
    spaceAfter=7,
)
BULLET = ParagraphStyle(
    "ArabicBullet",
    parent=BODY,
    rightIndent=12,
    leftIndent=8,
    bulletIndent=0,
    spaceAfter=3,
)
CAPTION = ParagraphStyle(
    "CaptionArabic",
    parent=BODY,
    fontName="Arial-Bold",
    fontSize=9,
    alignment=TA_CENTER,
    textColor=colors.HexColor("#666666"),
    spaceAfter=10,
)
LTR = ParagraphStyle(
    "LTR",
    parent=BODY,
    fontName="Arial",
    fontSize=9.5,
    alignment=TA_LEFT,
    leading=15,
)
CELL_AR = ParagraphStyle(
    "CellArabic",
    parent=BODY,
    fontSize=8.5,
    leading=12,
    alignment=TA_RIGHT,
    spaceAfter=0,
)
CELL_CENTER = ParagraphStyle(
    "CellCenter",
    parent=BODY,
    fontSize=8.5,
    leading=12,
    alignment=TA_CENTER,
    spaceAfter=0,
)
HEADER_CELL = ParagraphStyle(
    "HeaderCell",
    parent=CELL_CENTER,
    fontName="Arial-Bold",
    textColor=colors.white,
)


def P(text, style=BODY):
    return Paragraph(html.escape(display(text)), style)


def heading(text, level=1):
    return P(text, H1 if level == 1 else H2)


def bullet(text):
    return Paragraph("• " + html.escape(display(text)), BULLET)


def make_table(headers, rows, widths=None):
    data = [[Paragraph(html.escape(display(item)), HEADER_CELL) for item in headers]]
    for row in rows:
        cells = []
        for value in row:
            style = CELL_AR if has_arabic(value) else CELL_CENTER
            cells.append(Paragraph(html.escape(display(value)), style))
        data.append(cells)
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="CENTER")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#9EADBA")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F8FAFC")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EEF3F8")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def picture(path, caption, max_width=17.2 * cm):
    path = Path(path)
    if not path.exists():
        return []
    from PIL import Image as PILImage

    with PILImage.open(path) as source:
        width, height = source.size
    ratio = max_width / width
    img = Image(str(path), width=max_width, height=height * ratio)
    return [img, P(caption, CAPTION)]


def metrics_table(filename, columns, headers):
    rows = []
    for item in read_csv(filename):
        rows.append([item["method"]] + [f"{float(item[column]):.4f}" for column in columns])
    return make_table(headers, rows, [4.3 * cm, 3.0 * cm, 3.0 * cm, 3.0 * cm, 3.0 * cm])


def page_decor(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#D9E2F3"))
    canvas.line(2 * cm, A4[1] - 1.25 * cm, A4[0] - 2 * cm, A4[1] - 1.25 * cm)
    canvas.setFont("Arial", 8)
    canvas.setFillColor(colors.HexColor("#666666"))
    if doc.page > 1:
        canvas.drawRightString(A4[0] - 2 * cm, A4[1] - 0.95 * cm, rtl("مشروع نظم استرجاع المعلومات 2026"))
        canvas.drawCentredString(A4[0] / 2, 0.85 * cm, str(doc.page))
    canvas.restoreState()


def build_pdf():
    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=A4,
        rightMargin=1.8 * cm,
        leftMargin=1.8 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.5 * cm,
        title="تقرير مشروع نظم استرجاع المعلومات 2026",
        author="فريق مشروع نظم استرجاع المعلومات",
    )
    story = []

    story.extend(
        [
            Spacer(1, 3.2 * cm),
            P("مشروع عملي نظم استرجاع المعلومات 2026", TITLE),
            P("بناء نظام استرجاع معلومات طبي", TITLE),
            P("Information Retrieval System", SUBTITLE),
            Spacer(1, 0.8 * cm),
            P("ClinicalTrials 2017 / TREC Precision Medicine 2017", SUBTITLE),
            P("عدد الوثائق: 241,006", TITLE),
            Spacer(1, 1 * cm),
            P("إعداد الفريق", H1),
        ]
    )
    for name, _ in TEAM:
        story.append(P(name, SUBTITLE))
    story.extend([Spacer(1, 0.8 * cm), P("التاريخ: 14 حزيران 2026", BODY), PageBreak()])

    contents = [
        "1. الملخص التنفيذي",
        "2. أهداف المشروع",
        "3. توصيف Dataset",
        "4. مراحل تنفيذ المشروع",
        "5. المعالجة المسبقة ومعالجة الاستعلام",
        "6. نماذج الاسترجاع",
        "7. الفهرسة والتخزين",
        "8. بنية النظام وفق SOA",
        "9. واجهات التشغيل",
        "10. الميزة الإضافية Grounded RAG",
        "11. منهجية التقييم",
        "12. التقييم الأساسي",
        "13. Query Refinement",
        "14. Sentence-BERT",
        "15. تقييم RAG",
        "16. لقطات النسخة التنفيذية",
        "17. الاختبارات",
        "18. تقسيم العمل",
        "19. طريقة التشغيل",
        "20. GitHub وبنية المشروع",
        "21. التحسينات المستقبلية",
        "22. الخلاصة",
        "23. المصادر",
    ]
    story.append(heading("جدول المحتويات"))
    story.extend(P(item, BODY) for item in contents)
    story.append(PageBreak())

    story.append(heading("1. الملخص التنفيذي"))
    story.append(
        P(
            "يقدم هذا المشروع نظام استرجاع معلومات متخصصاً في التجارب السريرية الطبية. يقبل النظام "
            "استعلام المستخدم باللغة الطبيعية، ويطبق المعالجة المسبقة نفسها المستخدمة للوثائق، ثم "
            "يسترجع ويرتب الوثائق باستخدام TF-IDF وBM25 وLSA Embedding والتمثيل الهجين التسلسلي والمتوازي. "
            "يتضمن النظام Sentence-BERT لإعادة ترتيب نتائج BM25 وميزة Extractive Grounded RAG لإنتاج "
            "إجابة مستندة إلى الأدلة مع مصادر واضحة."
        )
    )
    story.append(
        P(
            "تم تنفيذ المشروع بلغة Python وفق SOA، مع واجهة Streamlit وREST API باستخدام FastAPI. "
            "تُحفظ النصوص الأصلية في SQLite ويُقرأ النص حسب doc_id لحظة الاستعلام. أما الفهارس والنماذج "
            "فحُفظت في artifacts جاهزة للتشغيل دون إعادة تدريب أثناء المقابلة."
        )
    )

    story.append(heading("2. أهداف المشروع"))
    goals = [
        "بناء محرك بحث يعيد الوثائق الطبية الأكثر صلة باستعلام المستخدم.",
        "تنفيذ TF-IDF وBM25 وEmbedding وHybrid Serial وHybrid Parallel.",
        "تطبيق معالجة مسبقة موحدة للوثائق والاستعلامات.",
        "توفير Query Refinement وتصحيح إملائي وتوسعة بالمرادفات.",
        "التحكم بمعاملات BM25 واختيار نموذج الاسترجاع من الواجهة.",
        "تقييم النماذج باستخدام qrels ومقاييس IR القياسية.",
        "إضافة RAG وتقييم جودة المصادر والـgrounding.",
        "تطبيق SOA وخدمات مستقلة وREST API قابلة للاختبار.",
    ]
    story.extend(bullet(item) for item in goals)

    story.append(heading("3. توصيف Dataset"))
    story.append(
        P(
            "اعتمدت Dataset واحدة بناءً على التوضيح النهائي للمعيدة، وهي "
            "clinicaltrials/2017/trec-pm-2017 من مكتبة ir_datasets. تمثل لقطة من ClinicalTrials.gov "
            "لمسار TREC 2017 Precision Medicine، وتحتوي على وثائق واستعلامات وqrels رسمية."
        )
    )
    story.append(
        make_table(
            ["الخاصية", "القيمة"],
            [
                ["معرف Dataset", "clinicaltrials/2017/trec-pm-2017"],
                ["عدد الوثائق", "241,006"],
                ["عدد الاستعلامات", "30"],
                ["عدد qrels", "13,019"],
                ["اللغة", "الإنجليزية"],
                ["حقول الوثيقة", "title, condition, summary, detailed_description, eligibility"],
                ["حقول query", "disease, gene, demographic, other"],
            ],
            [6 * cm, 11 * cm],
        )
    )
    story.append(
        P(
            "تم دمج جميع حقول الوثيقة في حقل نمذجة واحد للفهرسة، بينما حُفظ النص الأصلي الكامل في SQLite. "
            "وقت البحث يرجع النظام doc_id ثم يقرأ النص غير المنظف من قاعدة البيانات، وهو شرط أساسي لضمان "
            "سرعة الاسترجاع وصحة العرض."
        )
    )

    story.append(heading("4. مراحل تنفيذ المشروع"))
    stages = [
        ["1", "تحميل البيانات", "تحميل docs وqueries وqrels باستخدام ir_datasets."],
        ["2", "التخزين", "دمج الحقول وحفظ النصوص الأصلية في SQLite على دفعات."],
        ["3", "Preprocessing", "lowercase وtokenization وإزالة stop words والرموز."],
        ["4", "Indexing", "بناء TF-IDF وBM25 sparse وLSA embeddings."],
        ["5", "Query Processing", "تطبيق المعالجة نفسها وتمثيل query حسب النموذج."],
        ["6", "Retrieval", "المطابقة والترتيب وإرجاع Top K."],
        ["7", "BERT Reranking", "إعادة ترتيب أفضل 50 مرشحاً من BM25."],
        ["8", "RAG", "اختيار الجمل الأكثر ارتباطاً وإضافة citations."],
        ["9", "Evaluation", "حساب المقاييس وتوليد CSV والرسوم."],
        ["10", "Deployment", "تشغيل Streamlit وFastAPI من artifacts الجاهزة."],
    ]
    story.append(make_table(["المرحلة", "الاسم", "الوصف"], stages, [1.5 * cm, 4 * cm, 11.5 * cm]))

    story.append(heading("5. المعالجة المسبقة ومعالجة الاستعلام"))
    story.append(
        P(
            "تنفذ TextProcessor تحويل النص إلى lowercase واستخراج الكلمات والأرقام وإزالة stop words "
            "والرموز والكلمات القصيرة. تُستخدم الوظيفة نفسها للوثائق والاستعلامات. وعند بناء TF-IDF يتم "
            "تمرير النص المنظف مع tokenizer=str.split وتعطيل tokenization وlowercase الافتراضيين لمنع "
            "حدوث معالجة مزدوجة."
        )
    )
    story.append(heading("5.1 Query Refinement", 2))
    story.append(
        P(
            "تقوم Query Refinement Service بتصحيح أخطاء شائعة مثل diabetis إلى diabetes، ثم تضيف عدداً "
            "محدوداً من المرادفات. أبقيت الميزة اختيارية لأن التقييم أثبت أنها قد تحسن TF-IDF، لكنها قد "
            "تضيف كلمات عامة تقلل دقة BM25 في الاستعلامات الجينية والطبية الدقيقة."
        )
    )

    story.append(heading("6. نماذج تمثيل واسترجاع الوثائق"))
    story.append(
        make_table(
            ["الطريقة", "النوع", "آلية العمل"],
            [
                ["TF-IDF", "VSM", "حساب cosine similarity بين query والوثائق."],
                ["BM25", "Probabilistic", "نموذج sparse مع k1 وb قابلين للتغيير."],
                ["LSA Embedding", "TruncatedSVD", "ضغط TF-IDF إلى 64 بعداً دلالياً."],
                ["Hybrid Parallel", "Fusion", "دمج درجات TF-IDF وBM25 وLSA."],
                ["Hybrid Serial", "Reranking", "BM25 يجلب المرشحين ثم LSA يعيد ترتيبهم."],
                ["Sentence-BERT", "Semantic Reranking", "إعادة ترتيب أفضل 50 مرشحاً من BM25."],
            ],
            [4 * cm, 4 * cm, 9 * cm],
        )
    )
    story.append(
        P(
            "يستخدم Hybrid Parallel أوزاناً افتراضية 0.25 لـTF-IDF و0.60 لـBM25 والباقي لـLSA. "
            "أما Hybrid Serial فيجمع درجة BM25 مع درجة LSA للمرشحين. Sentence-BERT يستخدم نموذج "
            "all-MiniLM-L6-v2 محلياً ولا يعيد بناء الفهرس."
        )
    )

    story.append(heading("7. الفهرسة والتخزين"))
    story.append(
        P(
            "بُني TF-IDF بحد أقصى 30,000 feature وmin_df=2 وmax_df=0.95 وبنوع float32. استخدم BM25 "
            "مصفوفة sparse بنفس vocabulary. حُفظ الفهرس في search_index.joblib بحجم يقارب 382MB، وحُفظت "
            "241,006 وثيقة أصلية في documents.sqlite بحجم يقارب 1.1GB."
        )
    )
    storage = [
        "documents.sqlite: النصوص الأصلية مع فهرس على doc_id.",
        "search_index.joblib: TF-IDF وSVD وembedding matrix وBM25.",
        "dataset_metadata.json: تعريف Dataset ومعاملات البناء.",
        "evaluation_metrics*.csv: تقارير التقييم المختلفة.",
    ]
    story.extend(bullet(item) for item in storage)

    story.append(PageBreak())
    story.append(heading("8. بنية النظام وفق SOA"))
    story.append(
        P(
            "قُسم النظام إلى خدمات مستقلة ذات مسؤوليات واضحة. ServiceContainer يحمل الفهرس وقاعدة البيانات "
            "مرة واحدة ويحقنها في RetrievalService وRagService. تستخدم Streamlit وFastAPI الحاوية نفسها، "
            "وبذلك تبقى الواجهات منفصلة عن تفاصيل الفهرسة والتخزين وتزداد قابلية الصيانة وإعادة الاستخدام."
        )
    )
    story.extend(picture(FINAL_DIR / "system_architecture.png", "الشكل 1: System Architecture وفق SOA"))
    services = [
        ["Data Service", "data_service.py", "تحميل Dataset وqrels ودمج الحقول."],
        ["Document Store", "database.py", "حفظ واسترجاع النص الأصلي من SQLite."],
        ["Preprocessing", "text_processing.py", "تنظيف النصوص والاستعلامات."],
        ["Query Refinement", "query_refinement.py", "التصحيح الإملائي والمرادفات."],
        ["Indexing", "indexing_service.py", "بناء TF-IDF وBM25 وLSA."],
        ["Retrieval", "retrieval_service.py", "البحث والترتيب والهجين وBERT."],
        ["Evaluation", "evaluation_service.py", "حساب مقاييس IR."],
        ["RAG", "rag_service.py", "إجابة مؤرضة ومصادر وأدلة."],
        ["API Gateway", "api.py", "واجهات health/search/rag/metrics."],
        ["UI", "app.py", "واجهة Streamlit."],
    ]
    story.append(make_table(["الخدمة", "الملف", "المسؤولية"], services, [4 * cm, 4 * cm, 9 * cm]))

    story.append(heading("9. واجهات التشغيل"))
    story.append(heading("9.1 Streamlit UI", 2))
    story.append(
        P(
            "تتيح اختيار Retrieval method وTop K ومعاملات BM25 k1 وb، وتشغيل Query Refinement، "
            "والتنقل بين Search وRAG Chat وEvaluation."
        )
    )
    story.append(heading("9.2 FastAPI Gateway", 2))
    story.append(
        make_table(
            ["Endpoint", "الوظيفة"],
            [
                ["GET /health", "فحص الجاهزية وعدد الوثائق."],
                ["POST /search", "تنفيذ البحث مع النموذج والمعاملات."],
                ["POST /rag", "إرجاع الإجابة والأدلة والمصادر."],
                ["GET /metrics", "إرجاع تقارير التقييم بصيغة JSON."],
            ],
            [5 * cm, 12 * cm],
        )
    )
    story.append(P("توثيق OpenAPI التفاعلي متاح على http://127.0.0.1:8000/docs."))

    story.append(heading("10. الميزة الإضافية: Grounded RAG"))
    story.append(
        P(
            "تسترجع RAG Service أفضل الوثائق، ثم تقسم النص إلى جمل وتختار الجملة ذات أكبر تقاطع مع كلمات "
            "السؤال. تعرض أفضل ثلاثة أدلة مرقمة، ثم تعرض المصادر مع doc_id وscore. هذا التصميم Extractive "
            "RAG، لذلك لا يولد ادعاءات خارج الوثائق الأصلية."
        )
    )

    story.append(heading("11. منهجية التقييم"))
    story.append(
        P(
            "استُخدمت qrels الرسمية لـ29 استعلاماً. استرجع النظام أفضل 1000 وثيقة لكل query لحساب "
            "MAP@1000 وRecall@1000، بينما حُسب nDCG@10 وPrecision@10 على أول عشر نتائج."
        )
    )
    measures = [
        "MAP@1000: متوسط Average Precision عبر الاستعلامات حتى عمق 1000.",
        "nDCG@10: جودة ترتيب أول عشر نتائج مع درجات الملاءمة.",
        "Precision@10: نسبة الوثائق الملائمة ضمن أول عشر نتائج.",
        "Recall@1000: نسبة الوثائق الملائمة المسترجعة حتى عمق 1000.",
    ]
    story.extend(bullet(item) for item in measures)

    story.append(heading("12. نتائج التقييم الأساسية"))
    story.append(
        metrics_table(
            "evaluation_metrics.csv",
            ["map_at_1000", "ndcg_at_10", "precision_at_10", "recall_at_1000"],
            ["Method", "MAP@1000", "nDCG@10", "P@10", "Recall@1000"],
        )
    )
    story.append(
        P(
            "حقق BM25 أفضل MAP وPrecision وRecall، بينما حقق Hybrid Serial أفضل nDCG@10. يرجع ذلك إلى "
            "قدرة BM25 على التعامل مع تكرار المصطلحات وطول الوثيقة، وقدرة إعادة الترتيب التسلسلية على رفع "
            "الوثائق شديدة الملاءمة إلى المراتب الأولى. كانت LSA ضعيفة بسبب ضغط المصطلحات الطبية إلى 64 بعداً."
        )
    )
    story.extend(picture(FIGURES_DIR / "evaluation_metrics.png", "الشكل 2: مقارنة نماذج الاسترجاع الأساسية"))

    story.append(heading("13. تقييم Query Refinement"))
    story.append(
        metrics_table(
            "evaluation_metrics_refined.csv",
            ["map_at_1000", "ndcg_at_10", "precision_at_10", "recall_at_1000"],
            ["Method", "MAP@1000", "nDCG@10", "P@10", "Recall@1000"],
        )
    )
    story.append(
        P(
            "حسنت الميزة بعض نتائج TF-IDF وRecall الخاص بـLSA، لكنها خفضت MAP وRecall في BM25 والهجين. "
            "السبب هو أن المرادفات العامة قد تزيد الضجيج في استعلامات الأمراض والجينات، لذلك بقي الخيار "
            "قابلاً للتفعيل والإيقاف من الواجهة."
        )
    )

    story.append(heading("14. تقييم Sentence-BERT"))
    story.append(
        metrics_table(
            "evaluation_metrics_bert.csv",
            ["map_at_10", "ndcg_at_10", "precision_at_10", "recall_at_10"],
            ["Method", "MAP@10", "nDCG@10", "P@10", "Recall@10"],
        )
    )
    story.append(
        P(
            "حقق BERT nDCG@10=0.2474 وP@10=0.2655، وتفوق دلالياً على LSA. استخدم كمرحلة reranking فوق "
            "أفضل 50 نتيجة من BM25 لتقليل زمن التنفيذ وحجم التخزين."
        )
    )

    story.append(heading("15. تقييم RAG قبل وبعد الميزة الإضافية"))
    rag = read_csv("rag_evaluation_metrics.csv")[0]
    story.append(
        make_table(
            ["Source P@5", "Source Recall@5", "Query Coverage", "Citation Coverage", "Groundedness"],
            [[
                f"{float(rag['source_precision_at_5']):.4f}",
                f"{float(rag['source_recall_at_5']):.4f}",
                f"{float(rag['answer_query_coverage']):.4f}",
                f"{float(rag['citation_coverage']):.4f}",
                f"{float(rag['groundedness']):.4f}",
            ]],
            [3.4 * cm] * 5,
        )
    )
    story.append(
        P(
            "قبل RAG يعرض النظام الوثائق فقط، وبعدها يعرض إجابة وأدلة ومصادر. Groundedness=1.0 يثبت أن "
            "كل جملة دليل موجودة في الوثائق الأصلية. Citation Coverage=0.6 لأن الإجابة تستخدم أفضل ثلاثة "
            "أدلة من خمسة مصادر."
        )
    )

    story.append(PageBreak())
    story.append(heading("16. لقطات النسخة التنفيذية"))
    story.extend(picture(SCREENSHOTS_DIR / "final_search.png", "الشكل 3: البحث الهجين وعرض الوثائق الأصلية"))
    story.append(PageBreak())
    story.extend(picture(SCREENSHOTS_DIR / "final_rag.png", "الشكل 4: Grounded RAG مع citations"))
    story.append(PageBreak())
    story.extend(
        picture(
            SCREENSHOTS_DIR / "final_base_refined_evaluation.png",
            "الشكل 5: التقييم الأساسي وتقييم Query Refinement",
        )
    )
    story.append(PageBreak())
    story.extend(
        picture(
            SCREENSHOTS_DIR / "final_bert_rag_evaluation.png",
            "الشكل 6: تقييم Sentence-BERT وRAG",
        )
    )
    story.append(PageBreak())
    story.extend(picture(SCREENSHOTS_DIR / "final_evaluation_chart.png", "الشكل 7: الرسم البياني النهائي"))

    story.append(heading("17. الاختبارات وضمان الجودة"))
    story.append(
        P(
            "أضيفت اختبارات مستقلة باستخدام unittest لخدمة SQLite والمعالجة المسبقة وتحسين الاستعلام "
            "ومقاييس التقييم وRAG grounding. نجحت الاختبارات الأربعة، كما نجح compile واختبار REST API "
            "والبحث باستخدام BM25 وBERT على الفهرس الكامل."
        )
    )
    story.append(P(r"أمر الاختبار: .\run_tests.cmd"))

    story.append(heading("18. تقسيم العمل بين أعضاء الفريق"))
    story.append(make_table(["العضو", "المهام"], TEAM, [5 * cm, 12 * cm]))

    story.append(heading("19. النسخة التنفيذية وطريقة التشغيل"))
    story.append(
        P(
            "النسخة التنفيذية جاهزة للمقابلة دون إعادة التدريب. يجب الاحتفاظ بمجلد artifacts على جهاز "
            "العرض لأن الفهرس وقاعدة البيانات أكبر من حدود GitHub."
        )
    )
    story.append(
        make_table(
            ["المكون", "الأمر / الرابط"],
            [
                ["واجهة Streamlit", r".\run_app.cmd ثم http://localhost:8501"],
                ["REST API", r".\run_api.cmd ثم http://127.0.0.1:8000/docs"],
                ["الاختبارات", r".\run_tests.cmd"],
                ["CLI", 'python scripts\\search.py "lung cancer EGFR adult" --method bm25 --top-k 10'],
            ],
            [5 * cm, 12 * cm],
        )
    )
    story.append(
        P(
            "يوفر المشروع محرك البحث عبر واجهتين تنفيذيتين: Streamlit للمستخدم وFastAPI للتكامل. "
            "ومن كل واجهة يمكن الاستعلام باستخدام النماذج الأساسية والهجينة."
        )
    )

    story.append(heading("20. GitHub وبنية المشروع"))
    story.append(P("رابط GitHub: https://github.com/khaderaldiwani/ir_project"))
    story.append(
        make_table(
            ["المسار", "المحتوى"],
            [
                ["src/ir_project/services", "الخدمات المستقلة."],
                ["scripts", "التحضير والبحث والتقييم."],
                ["notebooks", "نوت بوك Colab للتدريب."],
                ["artifacts", "metadata وCSV؛ الملفات الضخمة مستثناة من Git."],
                ["reports", "التقرير والصور والرسوم."],
                ["app.py", "واجهة Streamlit."],
                ["api.py", "FastAPI Gateway."],
                ["README.md", "شرح البنية والتشغيل."],
            ],
            [6 * cm, 11 * cm],
        )
    )

    story.append(heading("21. القيود والتحسينات المستقبلية"))
    improvements = [
        "استخدام Biomedical Sentence-BERT متخصص بالمجال الطبي.",
        "إضافة Learning to Rank لتعلم أوزان الدمج.",
        "إضافة مولد لغوي محلي مع الحفاظ على evidence وcitations.",
        "نقل قاعدة البيانات إلى PostgreSQL أو MongoDB عند التشغيل الموزع.",
        "إضافة cache للاستعلامات وقياس زمن الاستجابة.",
    ]
    story.extend(bullet(item) for item in improvements)

    story.append(heading("22. الخلاصة"))
    story.append(
        P(
            "تم بناء نظام استرجاع معلومات متكامل على Dataset كاملة تتجاوز 200 ألف وثيقة. يحقق النظام "
            "المعالجة والفهرسة وتمثيلات TF-IDF وBM25 وEmbedding والتمثيل الهجين والاسترجاع والترتيب "
            "وتحسين الاستعلام والتقييم. كما يطبق SOA عملياً عبر خدمات مستقلة وServiceContainer وFastAPI، "
            "ويقدم نسخة تنفيذية مستقرة. أظهرت النتائج تفوق BM25 وHybrid Serial، وفائدة BERT كـreranker، "
            "وحقق RAG groundedness كاملاً مع مصادر واضحة."
        )
    )

    story.append(heading("23. المصادر والمراجع"))
    references = [
        "IR Datasets Clinical Trials: https://ir-datasets.com/clinicaltrials.html",
        "Roberts, K. et al. Overview of the TREC 2017 Precision Medicine Track, TREC 2017.",
        "TREC Precision Medicine: https://trec.nist.gov/data/precmed.html",
        "Robertson, S. and Zaragoza, H. BM25 and Beyond, 2009. https://doi.org/10.1561/1500000019",
        "scikit-learn TfidfVectorizer: https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html",
        "scikit-learn TruncatedSVD: https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.TruncatedSVD.html",
        "Reimers, N. and Gurevych, I. Sentence-BERT, 2019: https://arxiv.org/abs/1908.10084",
        "Sentence Transformers: https://www.sbert.net/",
        "FastAPI: https://fastapi.tiangolo.com/",
        "Streamlit: https://docs.streamlit.io/",
        "SQLite: https://www.sqlite.org/docs.html",
    ]
    for index, reference in enumerate(references, 1):
        story.append(Paragraph(f"{index}. {html.escape(reference)}", LTR))

    doc.build(story, onFirstPage=page_decor, onLaterPages=page_decor)
    print(PDF_PATH)


if __name__ == "__main__":
    build_pdf()
