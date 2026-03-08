# Foundry Pricing Backend

A FastAPI backend that connects an **Azure AI Foundry** agent to an Excel-based pricing database, serving a browser UI with an interactive price-vs-quantity analysis chart.

---

## What It Does

Select a customer and an item in the browser. The backend pulls together that customer's CRM profile, the item's price and stock data, competitor pricing, and the full sales history between that customer and item. It sends all of this as context to your **AI-Pricing-Strategist** agent on Azure AI Foundry, which returns:

- A recommended price for that customer
- A minimum price floor (preserving margin)
- A volume discount curve (optimal price at each quantity bracket)
- A plain-English reasoning summary
- A maximum discount ceiling for that customer

These are rendered as an interactive chart alongside the actual historical prices paid.

---

## Project Structure

```
.
├── main.py               # FastAPI application
├── requirements.txt      # Python dependencies
├── .env                  # Your environment variables (not committed)
├── .env.example          # Template for .env
├── data.xlsx             # Your Excel database (not committed)
└── static/
    └── index.html        # Browser UI (served by FastAPI)
```

---

## Prerequisites

- Python 3.11+
- An [Azure AI Foundry](https://ai.azure.com) project with an agent named `AI-Pricing-Strategist` (or your own agent name)
- Azure CLI installed and logged in (`az login`) for local `DefaultAzureCredential` auth
- Your pricing Excel file with the four sheets described below

---

## Setup

**1. Clone / copy the project files into a folder.**

**2. Create and activate a virtual environment:**

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

**3. Install dependencies:**

```bash
pip install -r requirements.txt
```

**4. Copy `.env.example` to `.env` and fill in your values:**

```dotenv
PROJECT_ENDPOINT=https://<resource-name>.services.ai.azure.com/api/projects/<project-name>
AZURE_AI_AGENT_NAME=AI-Pricing-Strategist
AZURE_AI_AGENT_VERSION=3
AZURE_AI_AGENT_MODEL=gpt-4.1-nano
EXCEL_PATH=data.xlsx
```

| Variable | Where to find it |
|---|---|
| `PROJECT_ENDPOINT` | Foundry portal → your project → Libraries → Foundry tab |
| `AZURE_AI_AGENT_NAME` | Foundry portal → Agents → your agent's display name |
| `AZURE_AI_AGENT_VERSION` | Foundry portal → Agents → your agent → version number |
| `AZURE_AI_AGENT_MODEL` | Foundry portal → Agents → your agent → model deployment |
| `EXCEL_PATH` | Path to your Excel file, relative to `main.py` or absolute |

**5. Place your Excel file** in the project folder (default expected name: `data.xlsx`).

**6. Start the server:**

```bash
uvicorn main:app --reload
```

**7. Open the UI:** [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## Excel File Requirements

The workbook must contain exactly these four sheet names:

### Price Sheet
| Column | Description |
|---|---|
| Item Code | Unique item identifier |
| Item Name | Display name |
| Category | Product category |
| Unit | Unit of measure |
| List Price (RM) | Standard list price |
| Min Order Qty | Minimum order quantity |
| Stock Qty | Current stock level |
| Date Received | Date stock was received |
| Stock Age (Days) | Age of current stock |
| Age Bracket | Categorised stock age |

### Sales History
| Column | Description |
|---|---|
| Txn ID | Transaction ID |
| Date | Transaction date |
| Customer ID | Customer identifier |
| Customer Name | Customer display name |
| Item Code | Item identifier |
| Item Name | Item display name |
| Qty Ordered | Quantity in this transaction |
| Unit Price Given (RM) | Actual price charged |
| List Price (RM) | List price at time of sale |
| Discount % | Discount applied |
| Total Value (RM) | Line total |

### Competitor Pricing
| Column | Description |
|---|---|
| Item Code | Item identifier |
| Item Name | Item display name |
| Unit | Unit of measure |
| Our List Price (RM) | Our current list price |
| Comp A Price (RM) | Competitor A price |
| Comp B Price (RM) | Competitor B price |
| Comp C Price (RM) | Competitor C price |
| Market Low (RM) | Lowest market price |
| Market High (RM) | Highest market price |

### CRM Sheet
| Column | Description |
|---|---|
| Customer ID | Unique customer identifier |
| Customer Name | Display name |
| Loyalty Tier | e.g. Gold, Silver, Bronze |
| Avg Monthly Spend (RM) | Average monthly spend |
| Txn Count (12M) | Transactions in last 12 months |
| Price Sensitivity | e.g. High, Medium, Low |
| Preferred Category | Preferred product category |
| Avg Discount Requested % | Historical average discount requested |
| On-Time Payment % | Payment reliability |
| Credit Limit (RM) | Credit limit |
| Account Manager | Assigned account manager |

> **Tip:** If you get a `KeyError` on column names, visit `http://127.0.0.1:8000/api/debug/columns` after starting the server. It returns the actual column names read from your file so you can spot any mismatches.

---

## API Reference

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Serves the browser UI |
| `GET` | `/health` | Health check |
| `GET` | `/api/customers` | List all customers from CRM sheet |
| `GET` | `/api/items` | List all items from Price Sheet |
| `POST` | `/api/pricing` | Run pricing analysis (SSE stream) |
| `GET` | `/api/debug/columns` | Returns actual column names from all sheets |

### `POST /api/pricing`

**Request body:**
```json
{
  "customer_id": "C001",
  "item_code": "ITM-042"
}
```

**Response:** Server-Sent Events stream. The single meaningful event is:

```json
{
  "type": "result",
  "data": {
    "customer_name": "...",
    "item_name": "...",
    "loyalty_tier": "Gold",
    "price_sensitivity": "Medium",
    "list_price": 100.00,
    "market_low": 82.00,
    "market_high": 105.00,
    "min_price": 88.00,
    "recommended_price": 94.50,
    "discount_ceiling": 8,
    "optimal_price_points": [{"qty": 10, "price": 96.00}, ...],
    "actual_points": [{"qty": 20, "price": 91.00}, ...],
    "reasoning": "..."
  }
}
```

On error, the stream emits `{"type": "error", "message": "..."}`.

---

## Authentication

Authentication uses `DefaultAzureCredential` from the Azure Identity SDK. Locally, it picks up your `az login` session automatically. In a hosted Azure environment (App Service, Container Apps, VM), assign a **managed identity** to the resource and grant it the **Azure AI Developer** role on your Foundry project.
