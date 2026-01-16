import os
import re
import shutil
import zipfile
from pathlib import Path
from datetime import datetime

# ----------------------------
# Output folders
# ----------------------------
CATEGORY_FOLDERS = {
    "STAAR 3-8 & Alt": "STAAR 3-8 & Alt",
    "STAAR EOC & EOC Alt": "STAAR EOC & EOC Alt",
    "TELPAS": "TELPAS",
    "TELPAS Alt": "TELPAS Alt",
    "Unsorted": "Unsorted",
    "Metadata": "Metadata",
}

# ----------------------------
# Regex patterns (case-insensitive)
# ----------------------------
TELPAS_RE = re.compile(r"TELPAS", re.IGNORECASE)
ALT_RE = re.compile(r"ALT", re.IGNORECASE)

# Grades 3-8 signals in filenames (G03..G08, 3-8, 5-8)
GRADE_3_8_RE = re.compile(
    r"\bG0?[3-8](?:_|$)|"      # G03_ ... G08_
    r"(?:\b3[-_]?8\b)|"        # 3-8 or 38 or 3_8
    r"(?:\b5[-_]?8\b)",        # 5-8 or 58 or 5_8
    re.IGNORECASE
)

# STAAR 3-8 non-alt pattern seen in your Unsorted:
# 0522_G03_ProductionExaminee_....
STAAR_3_8_DATE_GRADE_RE = re.compile(r"^\d{4}_G0?[3-8](?:_|$)", re.IGNORECASE)

# EOC signals:
# - explicit EOC
# - token patterns like _E1_, _E2_, _A1_, _US_, _BI_
EOC_RE = re.compile(r"\bEOC\b|[_\-](E1|E2|A1|US|BI)(?:_|$)", re.IGNORECASE)

EOC_ALT_TOKEN_RE = re.compile(r"ALT[_\-](E1|E2|A1)(?:_|$)", re.IGNORECASE)

# EOC Alt signals:
# - explicit EOCALT
# - EOC + ALT in either order
EOC_ALT_RE = re.compile(r"EOCALT|(\bEOC\b.*ALT)|(ALT.*\bEOC\b)", re.IGNORECASE)

# STAAR Alt signals (3-8 Alt):
# matches: STAAR_ALT, STAAR-ALT, 3-8ALT, 38ALT, 3_8_ALT, ALT_G05, etc.
STAAR_ALT_RE = re.compile(
    r"(STAAR.*ALT)|"
    r"(3[\-_ ]?8[\-_ ]?ALT)|"
    r"(ALT.*3[\-_ ]?8)|"
    r"(ALT[_\- ]?G0?[3-8])",
    re.IGNORECASE
)

STAAR_BAND_RE = re.compile(r"(?:^|[_\-])(?:3[-_]?8|5[-_]?8)(?:[_\-]|$)", re.IGNORECASE)


def safe_mkdir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

def normalize_name(name: str) -> str:
    s = name.strip()
    s = re.sub(r"\s+", " ", s)
    return s

def extract_zip(zip_path: Path, extract_to: Path) -> list[Path]:
    """Extract a zip file to extract_to, return list of extracted file paths."""
    extracted_files: list[Path] = []
    with zipfile.ZipFile(zip_path, "r") as z:
        for member in z.infolist():
            if member.is_dir():
                continue
            out_path = extract_to / member.filename
            safe_mkdir(out_path.parent)
            with z.open(member) as src, open(out_path, "wb") as dst:
                shutil.copyfileobj(src, dst)
            extracted_files.append(out_path)
    return extracted_files

def extract_nested_zips(initial_zip: Path, extract_dir: Path) -> list[Path]:
    """
    Extract initial zip. If it contains zip(s), keep extracting until no new inner zips are found.
    Returns a flat list of all extracted file paths.
    """
    all_files: list[Path] = []
    queue: list[Path] = [initial_zip]
    seen: set[Path] = set()

    while queue:
        zpath = queue.pop(0)
        if zpath in seen:
            continue
        seen.add(zpath)

        files = extract_zip(zpath, extract_dir)
        all_files.extend(files)

        # enqueue any inner zip files
        for f in files:
            if f.is_file() and f.suffix.lower() == ".zip":
                queue.append(f)

    return all_files

def categorize(filename: str) -> str:
    """
    Priority rules:
      1) TELPAS Alt (TELPAS + ALT)
      2) TELPAS
      3) EOC Alt (EOCALT or EOC+ALT)
      4) EOC (E1/E2/A1/US/BI tokens)
      5) STAAR 3-8 & Alt (STAAR Alt patterns OR MMYY_G03..G08)
      6) Unsorted
    """
    fn = normalize_name(filename)

    has_telpas = bool(TELPAS_RE.search(fn))
    has_alt = bool(ALT_RE.search(fn))
    has_eoc = bool(EOC_RE.search(fn))
    has_eoc_alt = bool(EOC_ALT_RE.search(fn))
    has_staar_alt = bool(STAAR_ALT_RE.search(fn))
    has_grade_3_8 = bool(GRADE_3_8_RE.search(fn))
    has_staar_3_8_date_grade = bool(STAAR_3_8_DATE_GRADE_RE.search(fn))
    has_eoc_alt_token = bool(EOC_ALT_TOKEN_RE.search(fn))
    has_staar_band = bool(STAAR_BAND_RE.search(fn))
    
    lower = fn.lower()
    if lower in ("readme.txt", "nomatch.csv") or lower.endswith((".csv", ".md")):
        return "Metadata"

    # 1) TELPAS Alt
    if has_telpas and has_alt:
        return "TELPAS Alt"

    # 2) TELPAS
    if has_telpas:
        return "TELPAS"

    # 3) EOC Alt
    if has_eoc_alt or has_eoc_alt_token or (has_alt and has_eoc):
        return "STAAR EOC & EOC Alt"

    # 4) EOC
    if has_eoc:
        return "STAAR EOC & EOC Alt"

    # 5) STAAR 3-8 & Alt
    # - explicit staar alt patterns (3-8ALT, STAAR ALT, ALT_Gxx)
    # - or the common non-alt pattern: MMYY_G03..G08_...
    if has_staar_alt or has_staar_3_8_date_grade or has_staar_band:
        return "STAAR 3-8 & Alt"

    return "Unsorted"

def move_file(src: Path, dest_folder: Path) -> Path:
    """Move file into dest_folder; if name conflict, add suffix."""
    safe_mkdir(dest_folder)
    target = dest_folder / src.name

    if target.exists():
        stem = target.stem
        suffix = target.suffix
        i = 1
        while True:
            candidate = dest_folder / f"{stem}__dup{i}{suffix}"
            if not candidate.exists():
                target = candidate
                break
            i += 1

    shutil.move(str(src), str(target))
    return target

def sort_zip(zip_file: str, output_dir: str) -> None:
    zip_path = Path(zip_file).expanduser().resolve()
    out_root = Path(output_dir).expanduser().resolve()

    if not zip_path.exists():
        raise FileNotFoundError(f"ZIP not found: {zip_path}")

    safe_mkdir(out_root)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    extract_dir = out_root / f"Extracted_{zip_path.stem}_{stamp}"
    safe_mkdir(extract_dir)

    category_paths = {k: out_root / v for k, v in CATEGORY_FOLDERS.items()}
    for p in category_paths.values():
        safe_mkdir(p)

    # Extract initial + nested zips
    extracted = extract_nested_zips(zip_path, extract_dir)

    # DEBUG (optional): show a few extracted names
    #print("First 30 extracted:")
    for p in extracted[:30]:
        print("  ", p.name)
    hits = [p.name for p in extracted if re.match(r"^\d{4}_G0?[3-8](?:_|$)", p.name, re.IGNORECASE)]
    #print(f"\nFound MMYY_G03-08 files: {len(hits)}")
    for n in hits[:20]:
        print("  HIT:", n)
    band_hits = [p.name for p in extracted if STAAR_BAND_RE.search(p.name)]
    #print(f"\nFound STAAR band (3-8/5-8) files: {len(band_hits)}")
    for n in band_hits[:20]:
        print("  BAND HIT:", n)

    unsorted_list = []
    moved_count = {k: 0 for k in CATEGORY_FOLDERS.keys()}

    for fpath in extracted:
        if not fpath.is_file():
            continue

        # Skip zip files (they are just containers)
        if fpath.suffix.lower() == ".zip":
            continue

        category = categorize(fpath.name)
        dest = category_paths[category]
        move_file(fpath, dest)
        moved_count[category] += 1

        if category == "Unsorted":
            unsorted_list.append(fpath.name)

    log_path = out_root / "UnsortedFiles.txt"
    with open(log_path, "w", encoding="utf-8") as f:
        if unsorted_list:
            f.write("Unsorted files:\n")
            for name in sorted(set(unsorted_list)):
                f.write(name + "\n")
        else:
            f.write("No unsorted files.\n")

    # Keep extracted folder for debugging; delete later once confirmed
    #shutil.rmtree(extract_dir)

    print("\nSort complete:")
    for cat in ["STAAR 3-8 & Alt", "STAAR EOC & EOC Alt", "TELPAS", "TELPAS Alt", "Unsorted"]:
        print(f"  {cat}: {moved_count[cat]}")
    print(f"\nUnsorted log: {log_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python SDRSorterV4.py <zip_file_path> <output_directory>")
        raise SystemExit(1)

    sort_zip(sys.argv[1], sys.argv[2])
