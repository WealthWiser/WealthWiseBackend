import io
import re
from pathlib import Path
from typing import Optional, List, Dict, Any
from app.utils.transactions.categories import enrich_transactions
import pandas as pd
import pdfplumber

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

# ---------------- Configuration ----------------
HEADER_ALIASES = {
    "date": ["date", "txn date", "transaction date", "value date"],
    "description": ["description", "narration", "details", "particulars", "remarks"],
    "debit": ["debit", "withdrawal", "dr", "debits"],
    "credit": ["credit", "deposit", "cr", "credits"],
    "amount": ["amount", "txn amount", "transaction amount"],
    "balance": ["balance", "closing balance", "running balance", "bal"],
}

# ---------------- Helpers ----------------
def normalize_header(h: str) -> str:
    return re.sub(r"\s+", " ", (h or "").strip().lower())

def map_headers(cols: List[str]) -> Dict[str, int]:
    cols_norm = [normalize_header(c) for c in cols]
    mapping: Dict[str, int] = {}
    for target, aliases in HEADER_ALIASES.items():
        # exact or loose match
        for i, c in enumerate(cols_norm):
            if c in aliases or any(a in c for a in aliases):
                mapping[target] = i
                break
    return mapping

def to_float(x: Any) -> Optional[float]:
    if x is None:
        return None
    s = str(x).strip().replace(",", "")
    if not s:
        return None
    s = s.replace("(", "-").replace(")", "")
    s = re.sub(r"(₹|\$|€|£|INR|USD|EUR|GBP)", "", s, flags=re.I).strip()
    s = re.sub(r"^[^0-9\-\.]+|[^0-9\.]+$", "", s)
    try:
        return float(s)
    except Exception:
        return None

def norm_date_to_iso(s: str) -> str:
    s = (s or "").strip()
    m = re.match(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})$", s)
    if m:
        d, mth, y = m.groups()
        if len(y) == 2:
            y = "20" + y
        try:
            from datetime import date
            return date(int(y), int(mth), int(d)).isoformat()
        except Exception:
            return s
    return s

def open_pdf_as_bytes(path: str, password: Optional[str]) -> bytes:
    raw = Path(path).read_bytes()
    if password is None and fitz is None:
        return raw
    if password is not None and fitz is None:
        raise RuntimeError("This PDF may be encrypted. Install PyMuPDF (pip install pymupdf).")
    if fitz is not None:
        doc = fitz.open(stream=raw, filetype="pdf")
        try:
            if doc.is_encrypted:
                if not password:
                    raise ValueError("Password required for encrypted PDF")
                if not doc.authenticate(password):
                    raise ValueError("Invalid password")
                return doc.tobytes()
            return raw
        finally:
            doc.close()
    return raw

# ---------------- Core extraction ----------------
def extract_transactions_from_bytes(pdf_bytes: bytes) -> pd.DataFrame:
    print("starting the extraction...\n\n")
    rows = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            tables = []
            primary = page.extract_table()
            if primary: tables.append(primary)
            tables += page.extract_tables()

            for tbl in tables:
                if not tbl or len(tbl) < 2:
                    continue
                header = [normalize_header(h) for h in tbl[0]]
                mapping = map_headers(header)
                if "date" not in mapping or "description" not in mapping:
                    continue
                if not (("amount" in mapping) or ("debit" in mapping) or ("credit" in mapping)):
                    continue

                for r in tbl[1:]:
                    if not r or not any(r):
                        continue
                    get = lambda key: (r[mapping[key]] if key in mapping and mapping[key] < len(r) else None)
                    date = (get("date") or "").strip()
                    desc = (get("description") or "").strip()

                    debit = to_float(get("debit")) if "debit" in mapping else None
                    credit = to_float(get("credit")) if "credit" in mapping else None
                    amount = to_float(get("amount")) if "amount" in mapping else None
                    balance = to_float(get("balance")) if "balance" in mapping else None

                    if amount is None:
                        if debit is not None and credit is None:
                            amount = -abs(debit)
                        elif credit is not None and debit is None:
                            amount = abs(credit)
                        elif debit is not None and credit is not None:
                            amount = abs(credit) if abs(credit) > abs(debit) else -abs(debit)

                    if not re.search(r"\d", date):
                        continue

                    rows.append({
                        "date": date,
                        "description": re.sub(r"\s{2,}", " ", desc),
                        "debit": debit,
                        "credit": credit,
                        "amount": amount,
                        "balance": balance,
                    })

    df = pd.DataFrame(rows, columns=["date", "description", "debit", "credit", "amount", "balance"])
    if df.empty:
        return df

    df["date"] = df["date"].astype(str).apply(norm_date_to_iso)
    df["description"] = df["description"].astype(str).str.replace(r"\s{2,}", " ", regex=True).str.strip()

    def clean_desc_for_key(s: str) -> str:
        return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", s.lower().strip()))

    key_cols = pd.DataFrame({
        "date": df["date"].astype(str),
        "desc_key": df["description"].astype(str).map(clean_desc_for_key),
        "amount": df["amount"].astype(object),
        "balance": df["balance"].astype(object),
    })
    df = df[~key_cols.duplicated(keep="first")].reset_index(drop=True)

    try:
        df["_d"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.sort_values(by=["_d", "amount", "description"], kind="stable").drop(columns=["_d"]).reset_index(drop=True)
    except Exception:
        pass

    return df

def extract_transactions_from_file(path: str, password: Optional[str] = None) -> List[Dict[str, Any]]:
    pdf_bytes = open_pdf_as_bytes(path, password)
    df = extract_transactions_from_bytes(pdf_bytes)
    return enrich_transactions(df)

def extract_transactions_from_uploaded_bytes(pdf_bytes: bytes, password: Optional[str] = None) -> List[Dict[str, Any]]:
    if password and fitz:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        if doc.is_encrypted:
            if not doc.authenticate(password):
                raise ValueError("Invalid password")
            pdf_bytes = doc.tobytes()
        doc.close()
    df = extract_transactions_from_bytes(pdf_bytes)
    # return df.to_dict(orient="records")
    return enrich_transactions(df)

# ---------------- CLI (for testing only) ----------------
# if __name__ == "__main__":
#     import sys
#     if len(sys.argv) < 2:
#         print("Usage: python pdf_extractor.py <statement.pdf> [password]")
#         raise SystemExit(1)

#     path = sys.argv[1]
#     password = sys.argv[2] if len(sys.argv) > 2 else None
#     txns = extract_transactions_from_file(path, password)
#     print(f"Extracted {len(txns)} transactions")
#     for t in txns[:5]:
#         print(t)
