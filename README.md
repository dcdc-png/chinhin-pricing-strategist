# Fiamma AI Pricing Strategist — User Guide

Welcome to the **Fiamma AI Pricing Strategist**, an intelligent decision-support tool designed to replace manual guesswork with data-driven pricing recommendations. This tool empowers sales managers to maximize profit margins, balance competitiveness, and optimize stock levels across all sales channels.

**Web APP:** https://green-dune-0c54f0e10.2.azurestaticapps.net/

---

## 1. How to Login

The application is secured using Microsoft Entra ID (Azure AD), ensuring that only authorized Fiamma personnel can access the pricing engine and sensitive data.

1. Navigate to the **Fiamma AI Pricing Strategist** web application url.
2. You will see the split-panel landing page highlighting key platform milestones (Decisions, Accuracy, Speed).
3. On the right-hand panel, click the **"Sign in with Microsoft"** button.
4. If you are not already logged into your Microsoft account, a secure Microsoft login prompt will appear.
5. Enter your corporate Fiamma email and password.
6. Upon successful authentication, you will be automatically redirected to your main Pricing Dashboard.

---

## 2. How to Use the Solution

The core of the application is the **Pricing Dashboard**, where you can simulate scenarios, view AI recommendations, and lock in the optimal price for bulk orders. 

Here is a step-by-step workflow when a new order request comes in:

### Step 1: Input Deal Parameters
Use the **Analysis Parameters** panel to select:
* **Customer**: Select from the CRM database.
* **Item**: Select from the product catalogue.

Click **⚡ Analyze Pricing** to trigger the AI analysis.

### Step 2: Review the AI Rationale
The dashboard will display:
* **Interactive Chart**: Visual comparison of actual historical prices vs. the AI's optimal volume discount curve. 
* **Key Metrics**: Recommended price, minimum floor, list price, and max discount %.
* **AI Pricing Rationale**: A plain-English explanation of why the agent recommends this specific price point (considering customer loyalty, stock age, and market demand).

### Step 3: Consult the AI Assistant
If you need further clarification, click the **Chat Icon** in the bottom right corner to speak directly with the Pricing Assistant. You can ask follow-up questions like:
- *"Why is the recommended price higher than last year?"*
- *"Can we offer a better price if they buy 500 units?"*

---

## 3. Local Development Setup

### Prerequisites
1. **Python 3.11+**
2. **Node.js 16+**
3. **Azure Static Web Apps CLI**: `npm install -g @azure/static-web-apps-cli`
4. **Azure Functions Core Tools**: `npm install -g azure-functions-core-tools@4`

### Step-by-Step Guide
1. **Clone and Install**
   ```bash
   git clone <repository-url>
   cd chinhin-pricing-strategist
   pip install -r requirements.txt
   cd frontend
   npm install
   ```

2. **Setup Environment**
   Create a `.env` in the root and `local.settings.json` with your Azure AI Foundry credentials.

3. **Run the Application**
   From the `frontend` directory, run:
   ```bash
   npm run dev:all
   ```
   This command starts the Next.js frontend, the Azure Functions backend, and the SWA emulator simultaneously.
   Access the app at: **http://localhost:4280**

---

## 4. Technical Appendix (Backend)

The backend is built as an **Azure Functions** app using the Python v2 programming model.

### API Reference

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/customers` | List all customers from CRM sheet |
| `GET` | `/api/items` | List all items from Price Sheet |
| `POST` | `/api/pricing` | Run pricing analysis (SSE stream) |
| `POST` | `/api/chat` | Context-aware pricing conversation (SSE stream) |

### Excel Data Requirements
The engine reads from `data.xlsx` with the following sheets: `Price Sheet`, `Sales History`, `Competitor Pricing`, and `CRM Sheet`.
