import argparse
import gzip
import os
import tarfile
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "msmarco"

URLS = {
    "qrels": "https://trec.nist.gov/data/deep/2019qrels-pass.txt",
    "queries": "https://msmarco.z22.web.core.windows.net/msmarcoranking/msmarco-test2019-queries.tsv.gz",
    "collection_archive": "https://msmarco.z22.web.core.windows.net/msmarcoranking/collectionandqueries.tar.gz",
}


def download(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 0:
        print(f"exists: {path}")
        return
    tmp = path.with_suffix(path.suffix + ".download")
    print(f"downloading: {url}")
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 IR-Project/1.0"})
    with urllib.request.urlopen(request) as response, tmp.open("wb") as file:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            file.write(chunk)
    os.replace(tmp, path)
    print(f"saved: {path}")


def gunzip(source: Path, target: Path) -> None:
    if target.exists() and target.stat().st_size > 0:
        print(f"exists: {target}")
        return
    with gzip.open(source, "rb") as src, target.open("wb") as dst:
        while True:
            chunk = src.read(1024 * 1024)
            if not chunk:
                break
            dst.write(chunk)
    print(f"extracted: {target}")


def extract_collection(archive: Path, target: Path) -> None:
    if target.exists() and target.stat().st_size > 0:
        print(f"exists: {target}")
        return
    with tarfile.open(archive, "r:gz") as tar:
        member = next((item for item in tar.getmembers() if item.name.endswith("collection.tsv")), None)
        if member is None:
            raise RuntimeError("collection.tsv was not found in archive")
        source = tar.extractfile(member)
        if source is None:
            raise RuntimeError("Could not extract collection.tsv")
        with target.open("wb") as dst:
            while True:
                chunk = source.read(1024 * 1024)
                if not chunk:
                    break
                dst.write(chunk)
    print(f"extracted: {target}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Download local MS MARCO files for the project.")
    parser.add_argument("--skip-collection", action="store_true", help="Only download small qrels and queries files.")
    args = parser.parse_args()

    RAW.mkdir(parents=True, exist_ok=True)
    download(URLS["qrels"], RAW / "qrels.txt")
    queries_gz = RAW / "queries.tsv.gz"
    download(URLS["queries"], queries_gz)
    gunzip(queries_gz, RAW / "queries.tsv")

    if not args.skip_collection:
        archive = RAW / "collectionandqueries.tar.gz"
        download(URLS["collection_archive"], archive)
        extract_collection(archive, RAW / "collection.tsv")


if __name__ == "__main__":
    main()
