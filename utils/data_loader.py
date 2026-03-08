import os
import io
import pandas as pd
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

load_dotenv()

_db: dict = {}

def load_excel() -> dict:
    """
    Loads data from data.xlsx in Azure Blob Storage.
    Caches the parsed sheets in a global _db dictionary to avoid 
    repeated downloads across function invocations on the same instance.
    """
    global _db
    if _db:
        return _db
        
    connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    container_name = os.environ.get("AZURE_STORAGE_CONTAINER_NAME", "data")
    blob_name = os.environ.get("EXCEL_PATH", "data.xlsx")

    # Fallback to local file if no storage connection exists (useful for dev)
    if not connection_string:
        local_path = blob_name
        if os.path.exists(local_path):
            print(f"[INFO] Storage connection not found. Loading local Excel: {local_path}")
            excel_data = local_path
        else:
            print(f"[WARN] Connection string not found and local file '{local_path}' missing.")
            return {}
    else:
        try:
            print(f"[INFO] Downloading {blob_name} from Azure Blob Storage...")
            blob_service_client = BlobServiceClient.from_connection_string(connection_string)
            blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
            
            stream = blob_client.download_blob().readall()
            excel_data = io.BytesIO(stream)
            print("[INFO] Excel downloaded successfully.")
        except Exception as e:
            print(f"[ERROR] Failed to download from blob storage: {e}")
            return {}

    try:
        xl = pd.ExcelFile(excel_data)
        _db["price"]      = xl.parse("Price Sheet")
        _db["sales"]      = xl.parse("Sales History")
        _db["competitor"] = xl.parse("Competitor Pricing")
        _db["crm"]        = xl.parse("CRM Sheet")
        
        # normalize column names: strip whitespace
        for key in _db:
            _db[key].columns = _db[key].columns.str.strip()
            
        print("[INFO] Excel sheets parsed and cached.")
    except Exception as e:
        print(f"[ERROR] Failed to parse Excel: {e}")
        
    return _db

def get_db():
    if not _db:
        return load_excel()
    return _db
