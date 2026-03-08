import pandas as pd
import logging
import os
from shared.config import EXCEL_PATH

_db: dict = {}

def load_excel():
    global _db
    if not os.path.exists(EXCEL_PATH):
        logging.warning(f"Excel file not found at '{EXCEL_PATH}'.")
        return
    xl = pd.ExcelFile(EXCEL_PATH)
    _db["price"]      = xl.parse("Price Sheet")
    _db["sales"]      = xl.parse("Sales History")
    _db["competitor"] = xl.parse("Competitor Pricing")
    _db["crm"]        = xl.parse("CRM Sheet")
    for key in _db:
        _db[key].columns = _db[key].columns.str.strip()
    logging.info(f"Loaded Excel: {EXCEL_PATH}")

load_excel()

def get_db() -> dict:
    return _db
