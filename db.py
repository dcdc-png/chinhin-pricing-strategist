"""
db.py – Azure Blob Storage-backed data loader (replaces local EXCEL_PATH logic).

The workbook is loaded once at cold start and cached in the module-level `_db`
dict, exactly as the original load_excel() function worked.

Blob location
  Storage account : resolved via DefaultAzureCredential / managed identity
  Container       : cowhorsergb2f9
  Blob path       : database/data.xlsx

The storage account URL is read from the BLOB_ACCOUNT_URL environment variable
(e.g. https://<account>.blob.core.windows.net).
"""

import os
from io import BytesIO

import pandas as pd
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobClient

BLOB_ACCOUNT_URL = os.getenv("BLOB_ACCOUNT_URL", "")
BLOB_CONTAINER   = os.getenv("BLOB_CONTAINER",   "cowhorsergb2f9")
BLOB_PATH        = os.getenv("BLOB_PATH",        "database/data.xlsx")

_db: dict = {}


def _load_from_blob() -> None:
    """Download the Excel workbook from Blob Storage and populate _db."""
    global _db

    if not BLOB_ACCOUNT_URL:
        print("[WARN] BLOB_ACCOUNT_URL is not set – Excel data unavailable.")
        return

    try:
        credential = DefaultAzureCredential()
        blob_client = BlobClient(
            account_url=BLOB_ACCOUNT_URL,
            container_name=BLOB_CONTAINER,
            blob_name=BLOB_PATH,
            credential=credential,
        )

        print(f"[INFO] Downloading blob: {BLOB_CONTAINER}/{BLOB_PATH}")
        stream = blob_client.download_blob()
        data   = stream.readall()

        xl = pd.ExcelFile(BytesIO(data))
        _db["price"]      = xl.parse("Price Sheet")
        _db["sales"]      = xl.parse("Sales History")
        _db["competitor"] = xl.parse("Competitor Pricing")
        _db["crm"]        = xl.parse("CRM Sheet")

        # normalise column names: strip whitespace
        for key in _db:
            _db[key].columns = _db[key].columns.str.strip()

        print("[INFO] Excel loaded successfully from Blob Storage.")

    except Exception as exc:
        print(f"[ERROR] Failed to load Excel from Blob Storage: {exc}")
        _db = {}


# Cold-start load – runs once when the worker process initialises.
_load_from_blob()


def get_db() -> dict:
    """Return the cached database dict."""
    return _db
