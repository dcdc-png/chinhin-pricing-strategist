# Foundry Pricing Backend (Azure Functions)

An **Azure Functions** backend that connects an **Azure AI Foundry** agent to an Excel-based pricing database, serving data for an interactive price-vs-quantity analysis chart.

---

## What It Does

Select a customer and an item in the frontend. The backend pulls together that customer's CRM profile, the item's price and stock data, competitor pricing, and the full sales history between that customer and item. It sends all of this as context to your **AI-Pricing-Strategist** agent on Azure AI Foundry, which streams back:

- A recommended price for that customer
- A minimum price floor (preserving margin)
- A volume discount curve (optimal price at each quantity bracket)
- A plain-English reasoning summary

---

## Project Structure

```text
.
├── function_app.py        # Azure Functions entry point
├── blueprints/            # Route groups (health, pricing, data_endpoints)
├── shared/                # Shared utilities and configurations
├── requirements.txt       # Python dependencies
├── local.settings.json    # Local environment variables
└── data.xlsx              # Your Excel database
```

---

## Prerequisites

- Python 3.10+ or 3.11+
- [Azure Functions Core Tools](https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local)
- An [Azure AI Foundry](https://ai.azure.com) project with an agent named `AI-Pricing-Strategist`
- Azure CLI installed and logged in (`az login`) for local `DefaultAzureCredential` auth
- Your pricing Excel file (`data.xlsx`)

---

## Setup & Local Development

**1. Create and activate a virtual environment:**

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

**2. Install dependencies:**

```bash
pip install -r requirements.txt
```

**3. Configure `local.settings.json`:**
Add your secrets to the `Values` dictionary in `local.settings.json` (do not commit this file):

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "PROJECT_ENDPOINT": "https://<resource-name>.services.ai.azure.com/api/projects/<project-name>",
    "AZURE_AI_AGENT_NAME": "AI-Pricing-Strategist",
    "AZURE_AI_AGENT_VERSION": "3",
    "AZURE_AI_AGENT_MODEL": "gpt-4.1-nano"
  }
}
```

**4. Start the Azure Functions local server:**

```bash
func start
```

Your functions will be available at `http://localhost:7071`.

---

## API Reference

Azure Functions automatically prefixes HTTP routes with `/api/`.

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Health check to verify the function app is running |
| `GET` | `/api/customers` | List all unique customers from the CRM sheet |
| `GET` | `/api/items` | List all available items from the Price Sheet |
| `POST` | `/api/pricing` | Run AI pricing analysis (Server-Sent Events stream) |
| `GET` | `/api/debug/columns` | Returns actual column names from all sheets |

---

### Example Usage

#### 1. Get Customers
Retrieve a list of all customers to populate a dropdown.
```bash
curl http://localhost:7071/api/customers
```

#### 2. Get Items
Retrieve a list of all products.
```bash
curl http://localhost:7071/api/items
```

#### 3. Run Pricing Analysis (`POST /api/pricing`)
Request a pricing analysis for a specific customer and item. 

**Request body:**
```json
{
  "customer_id": "C001",
  "item_code": "ITM-042"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:7071/api/pricing \
     -H "Content-Type: application/json" \
     -d '{"customer_id": "C001", "item_code": "ITM-042"}'
```

**Response:** 
The endpoint streams back Server-Sent Events (SSE). It yields streaming chunks until it outputs the final `result` JSON event:

```json
data: {"type": "result", "data": {"customer_name": "...", "recommended_price": 94.50, ...}}
```

---

## Authentication

Authentication to Azure AI Foundry uses `DefaultAzureCredential` from the Azure Identity SDK. 
- **Locally:** It picks up your `az login` session automatically. 
- **In Azure:** Assign a **managed identity** to the Function App and grant it the **Azure AI Developer** role on your Foundry project.
