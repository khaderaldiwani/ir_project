from pathlib import Path
import os


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
ARTIFACTS_DIR = ROOT_DIR / "artifacts"
REPORTS_DIR = ROOT_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
TMP_DIR = ROOT_DIR / ".tmp"

DEFAULT_DATASET_ID = "clinicaltrials/2017/trec-pm-2017"
DEFAULT_MAX_DOCS = 0
DEFAULT_MAX_QUERIES = 0
TOP_K = 10

os.environ.setdefault("IR_DATASETS_HOME", str(RAW_DIR / "ir_datasets"))
os.environ.setdefault("TMP", str(TMP_DIR))
os.environ.setdefault("TEMP", str(TMP_DIR))
os.environ.setdefault("MPLCONFIGDIR", str(TMP_DIR / "matplotlib"))


def ensure_dirs() -> None:
    for path in [RAW_DIR, PROCESSED_DIR, ARTIFACTS_DIR, REPORTS_DIR, FIGURES_DIR, TMP_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def resolve_artifact_path(saved_path: str | Path, fallback_name: str) -> Path:
    path = Path(saved_path)
    raw_path = str(saved_path).replace("\\", "/")
    if raw_path.startswith("/content/") or raw_path.startswith("content/"):
        fallback = ARTIFACTS_DIR / fallback_name
        if fallback.exists():
            return fallback
    if path.exists():
        return path
    fallback = ARTIFACTS_DIR / fallback_name
    if fallback.exists():
        return fallback
    return path
