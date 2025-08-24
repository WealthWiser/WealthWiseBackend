import re
import pandas as pd
import numpy as np
# ---------------- MCC Code Map ----------------
MCC_MAP = {
    "5541": "Service Stations (without Ancillary services)",
    "5411": "Grocery Stores, Supermarkets",
    "4111": "Local/Suburban Commuter Passenger Transport/Ferries",
    "5921": "Package Stores, Beer, Wine, Liquor",
    "5812": "Eating Places and Restaurants",
    "5311": "Department Stores",
    "9399": "Government Services, Not Elsewhere Classified",
    "5912": "Drug Stores and Pharmacies",
    "8062": "Hospitals",
    "5699": "Miscellaneous Apparel and Accessory Stores",
    "5813": "Drinking Places (Alcoholic Bev) - Bars, Taverns",
    "5651": "Family Clothing Stores",
    "5944": "Jewellery, Watches, Clocks and Silverware Stores",
    "7011": "Lodging - Hotels, Motels, Resorts",
    "5814": "Fast Food Restaurants",
    "5691": "Men's and Women's Clothing Stores",
    "5732": "Radio, Television and Stereo Stores",
    "5983": "Gas / Fuel Station",
    "4814": "Telecommunication Services",
    "5462": "Bakeries",
    "4812": "Telecomm Equipment including Telephone Sales",
    "5661": "Shoe Stores",
    "5722": "Household Appliance Stores",
    "5499": "Misc Food/Convenience Stores/Speciality Markets",
    "8299": "Schools and Educational Services",
    "4900": "Utilities - Electric/Gas/Heating Oil/Sanitary/Water",
    "7832": "Motion Picture Theatres",
    "5511": "Auto and Truck Dealers (New and Used) Sales, Service",
    "5441": "Candy, Nut, Confectionery Stores",
    "5047": "Dental/Laboratory/Medical/Ophthalmic Hospital Supply"
}


# ---------------- Transaction Parser ----------------
def parse_transaction(line: str) -> dict:
    line = (line or "").strip()
    result = {
        "raw": line,
        "transaction_type": "Unknown",
        "direction": "Unknown",
        "transaction_id": None,
        "counterparty": None,
        "category": "Unknown"
    }

    # 1. Direction & Type detection
    if line.startswith("UPIOUT") or "DR/" in line or "Sent" in line:
        result["direction"] = "Sent"
        result["transaction_type"] = "UPI"
    elif line.startswith("UPI IN") or "CR/" in line:
        result["direction"] = "Received"
        result["transaction_type"] = "UPI"
    elif line.startswith("NFT") or line.startswith("NEFT"):
        result["direction"] = "Sent"
        result["transaction_type"] = "Bank Transfer"
    elif line.startswith("IFN"):
        result["direction"] = "Received"
        result["transaction_type"] = "Bank Transfer"
    elif "Refund" in line:
        result["direction"] = "Received"
        result["transaction_type"] = "Refund"
    elif "VisaDRefund" in line:
        result["direction"] = "Received"
        result["transaction_type"] = "Card Refund"

    # 2. Extract transaction ID
    match_id = re.search(r"(UPIOUT|UPI IN|UPI/|NFT|IFN)[/ ]?([A-Za-z0-9]+)", line)
    if match_id:
        result["transaction_id"] = match_id.group(2)

    # 3. Extract counterparty
    match_upi = re.search(r"([\w\.\-]+@[\w]+)", line)
    if match_upi:
        result["counterparty"] = match_upi.group(1)
    else:
        words = line.split()
        if len(words) > 1:
            result["counterparty"] = words[1:]

    # 4. Extract MCC
    match_mcc = re.search(r"/(\d{4})$", line)
    if match_mcc:
        mcc = match_mcc.group(1)
        result["category"] = MCC_MAP.get(mcc, f"Unknown ({mcc})")

    return result

import math

def clean_value(v):
    """Convert pandas/numpy values to JSON-safe Python values."""
    if v is None:
        return None
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    if isinstance(v, (np.generic,)):  # catches numpy types
        return v.item()
    return v
# ---------------- Helper: Enhance DataFrame ----------------
def enrich_transactions(df: pd.DataFrame) -> list[dict]:
    """
    Takes a DataFrame from extract_transactions_from_bytes
    and returns list of dict rows with 'categories' field added.
    """
    # Replace infinities with NaN
    df = df.replace([np.inf, -np.inf], np.nan)

    records = df.to_dict(orient="records")
    enriched = []
    for rec in records:
        # Clean each value
        clean_rec = {k: clean_value(v) for k, v in rec.items()}

        # Add categories
        desc = clean_rec.get("description", "")
        clean_rec["categories"] = parse_transaction(desc)

        enriched.append(clean_rec)

    return enriched
