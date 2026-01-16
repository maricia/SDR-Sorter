import re
import shutil
import zipfile
from pathlib import Path
from datetime import datetime

# ----------------------------
# Dropdown folder names (exact)
# ----------------------------
TH_FOLDERS_3_8 = [
    "2023-Current 3-8 Data",
    "2021-2022 3-8 Data",
    "2020 3-8 Data",
    "2019 3-8 Data",
    "2018 3-8 Data",
    "2017 3-8 Data",
    "2016 3-8 Data",
    "2015 3-8 Data",
    "2014 3-8 Data",
]

TH_FOLDERS_EOC = [
    "2018-Current EOC Data",
    "2017 EOC Data",
    "2016 EOC Data",
    "2015 EOC Data",
    "2014 EOC Data",
]

UNSORTED_FOLDER = "Unsorted"

# ----------------------------
# Regex patterns (case-insensitive)
# ----------------------------
TELPAS_RE = re.compile(r"TELPAS", re.IGNORECASE)
ALT_RE = re.compile(r"ALT", re.IGNORECASE)

# 3–8 signals
STAAR_BAND_RE = re.compile(r"(?:^|[_\-])(?:3[-_]?8|5[-_]?8)(?:[_\-]|$)", re.IGNORECASE)
STAAR_DATE_GRADE_RE = re.compile(r"^\d{4}_G0?[3-8](?:_|$)", re.IGNORECASE)  # e.g., 0522_G03_
GRADE_3_8_RE = re.compile(r"\bG0?[3-8](?:_|$)", re.IGNORECASE)
STAAR_3_8_ALT_DATE_GRADE_RE = re.compile(r"^\d{4}_ALT_G0?[3-8](?:_|$)", re.IGNORECASE)
STAAR_BAND_ALT_RE = re.compile(r"(?:^|[_\-])(?:3[-_]?8ALT)(?:[_\-]|$)", re.IGNORECASE)

# EOC signals (your export tokens)
EOC_TOKEN_RE = re.compile(r"\bEOC\b|[_\-](E1|E2|A1|US|BI)(?:_|$)", re.IGNORECASE)
EOC_ALT_TOKEN_RE = re.compile(r"EOCALT|ALT[_\-](E1|E2|A1)(?:_|$)|(\bEOC\b.*ALT)|(ALT.*\bEOC\b)", re.IGNORECASE)

# Year patterns
YEAR_4DIGIT_RE = re.compile(r"(20\d{2})")          # e.g., 20240624...
MMYY_PREFIX_RE  = re.compile(r"^(?:SF_|PF_)?(\d{4})[_\-]")  # e.g., SF_1521_..., 0522_...


def safe_mkdir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

def extract_zip(zip_path: Path, extract_to: Path) -> list[Path]:
    extracted = []
    with zipfile.ZipFile(zip_path, "r") as z:
        for member in z.infolist():
            if member.is_dir():
                continue
            out_path = extract_to / member.filename
            safe_mkdir(out_path.parent)
            with z.open(member) as src, open(out_path, "wb") as dst:
                shutil.copyfileobj(src, dst)
            extracted.append(out_path)
    return extracted

def extract_nested_zips(initial_zip: Path, extract_dir: Path) -> list[Path]:
    all_files = []
    queue = [initial_zip]
    seen = set()

    while queue:
        zpath = queue.pop(0)
        if zpath in seen:
            continue
        seen.add(zpath)

        files = extract_zip(zpath, extract_dir)
        all_files.extend(files)

        for f in files:
            if f.is_file() and f.suffix.lower() == ".zip":
                queue.append(f)

    return all_files

def classify_type(filename: str) -> str:
    """
    Returns: "3-8" or "EOC" or "SKIP"
    TestHound sorter ignores TELPAS/TELPAS Alt (you can change if needed).
    """
    fn = filename

    # If you DO want TELPAS in TestHound, delete these two lines and handle separately
    if TELPAS_RE.search(fn):
        return "SKIP"

    # EOC first
    if EOC_ALT_TOKEN_RE.search(fn) or EOC_TOKEN_RE.search(fn):
        return "EOC"

    # 3–8 next
    if (
    STAAR_BAND_ALT_RE.search(fn)               # 3-8ALT
    or STAAR_BAND_RE.search(fn)                # 3-8 or 5-8
    or STAAR_3_8_ALT_DATE_GRADE_RE.search(fn)  # 0422_ALT_G05...
    or STAAR_DATE_GRADE_RE.search(fn)          # 0522_G03...
    or GRADE_3_8_RE.search(fn)
):
        return "3-8"


def extract_year(filename: str) -> int | None:
    """
    Prefer 4-digit year (2024) if present; else use MMYY prefix (e.g., 0522 -> 2022).
    """
    fn = filename

    m4 = YEAR_4DIGIT_RE.search(fn)
    if m4:
        return int(m4.group(1))

    mmyy = MMYY_PREFIX_RE.search(fn)
    if mmyy:
        mm_yy = mmyy.group(1)   # "0522"
        yy = int(mm_yy[-2:])    # 22
        # assume 2000s
        return 2000 + yy

    return None

def pick_folder(data_type: str, year: int | None) -> str:
    if year is None:
        return UNSORTED_FOLDER

    if data_type == "3-8":
        if year >= 2023:
            return "2023-Current 3-8 Data"
        if year in (2021, 2022):
            return "2021-2022 3-8 Data"
        if year in (2020, 2019, 2018, 2017, 2016, 2015, 2014):
            return f"{year} 3-8 Data"
        return UNSORTED_FOLDER

    if data_type == "EOC":
        if year >= 2018:
            return "2018-Current EOC Data"
        if year in (2017, 2016, 2015, 2014):
            return f"{year} EOC Data"
        return UNSORTED_FOLDER

    return UNSORTED_FOLDER

def move_file(src: Path, dest_folder: Path) -> None:
    safe_mkdir(dest_folder)
    target = dest_folder / src.name

    if target.exists():
        stem, suf = target.stem, target.suffix
        i = 1
        while True:
            candidate = dest_folder / f"{stem}__dup{i}{suf}"
            if not candidate.exists():
                target = candidate
                break
            i += 1

    shutil.move(str(src), str(target))

def sort_testhound(zip_file: str, output_dir: str) -> None:
    zip_path = Path(zip_file).expanduser().resolve()
    out_root = Path(output_dir).expanduser().resolve()
    safe_mkdir(out_root)

    # Create all dropdown folders
    for name in TH_FOLDERS_3_8 + TH_FOLDERS_EOC + [UNSORTED_FOLDER]:
        safe_mkdir(out_root / name)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    extract_dir = out_root / f"Extracted_{zip_path.stem}_{stamp}"
    safe_mkdir(extract_dir)

    extracted = extract_nested_zips(zip_path, extract_dir)

    unsorted_list = []
    counts = {}

    for fpath in extracted:
        if not fpath.is_file():
            continue
        if fpath.suffix.lower() == ".zip":
            continue

        dtype = classify_type(fpath.name)
        year = extract_year(fpath.name)
        folder_name = pick_folder(dtype, year)
        
        if fpath.name.lower() in ("readme.txt", "nomatch.csv"):
            continue
        
        # Treat SKIP as Unsorted unless you want a separate folder
        if dtype == "SKIP":
            continue

        move_file(fpath, out_root / folder_name)
        counts[folder_name] = counts.get(folder_name, 0) + 1

        if folder_name == UNSORTED_FOLDER:
            unsorted_list.append(fpath.name)
    # Log
    log_path = out_root / "UnsortedFiles.txt"
    with open(log_path, "w", encoding="utf-8") as f:
        if unsorted_list:
            f.write("Unsorted files:\n")
            for name in sorted(set(unsorted_list)):
                f.write(name + "\n")
        else:
            f.write("No unsorted files.\n")

    # Uncomment when you're happy
    # shutil.rmtree(extract_dir)

    print("\nTestHound sort complete:")
    for k in sorted(counts.keys()):
        print(f"  {k}: {counts[k]}")
    print(f"\nUnsorted log: {log_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python TestHoundSDRSorterV4.py <zip_file_path> <output_directory>")
        raise SystemExit(1)

    sort_testhound(sys.argv[1], sys.argv[2])
