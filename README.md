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

The core of the application is the **Pricing Dashboard**, where you can select specific deals, view AI recommendations, and visualize the optimal price vs. order volume.

Here is a step-by-step workflow when a new order request comes in:

### Step 1: Input Analysis Parameters
Use the **Analysis Parameters** panel to define the current deal you want to analyze. Use the dropdowns to instantly pull in context:
* **Customer**: Select the customer from your database (this automatically retrieves their loyalty tier and price sensitivity).
* **Item**: Select the specific product they are inquiring about.
* Click the **"Analyze Pricing"** button to run the live AI pricing engine.

### Step 2: Evaluate the Pricing Chart
Review the **Price vs Quantity Analysis** chart, which dynamically visualizes:
* **Optimal Price Curve**: The recommended sliding scale for the item's price depending on the order quantity.
* **Historical Data**: A scatter plot of actual past prices paid for this item to help ground your decision.
* **Price Floors & Limits**: Clear horizontal reference lines for your Minimum Price Floor, standard List Price, and the newly calculated Recommended Price.

### Step 3: Review the AI Rationale
Scroll down to the **AI Pricing Rationale** panel to read the AI's transparent reasoning. This section provides the precise recommended price, your maximum allowable percentage discount limit, and a textual breakdown of the logic behind the number.

### Step 4: Consult the Context-Aware AI Assistant
If you need further clarification on margins or want to evaluate edge cases, click the **Floating Chat Icon** in the bottom right corner to open the **Pricing Assistant**.
* Powered by Azure AI Foundry, this chat interface is automatically aware of your currently selected customer, item, and recent pricing analysis.
* Ask natural language questions (e.g., *"What happens to our margin if I offer a RM 100 discount off the recommended price?"*) and the AI will reply using the context of the active deal.

---

## 3. Key Features & Functionality

* **Dynamic Pricing Engine:** Calculates the "Goldilocks" price by analyzing willingness to pay, current stock levels, and historical data, replacing the "Gut-Feel Gamble."
* **Margin Simulator:** Real-time sliders and inputs that project the impact of pricing changes on overall revenue and profit before issuing a quote, speeding up the decision cycle.
* **Multifactor Analysis Chart:** A visual comparison tool mapping out minimum acceptable price, AI optimal price, maximum threshold, and known competitor pricing side-by-side across channels.
* **Smart "Why" Rationale:** Transparent breakdown of the AI's logic with confidence scores and positive/neutral/warning impact indicators, solving the inventory mismatch problem by clearly explaining why specific discounts apply to aging stock over high-demand items.

-----------------------------------------------------------------------------------------------------------------
## 4. Local Development Setup

If you want to run the project locally on your machine, follow these step-by-step instructions:

### Prerequisites
1. **Node.js**: Ensure you have Node.js installed on your machine.
2. **NPM**: Node Package Manager (comes with Node.js).
3. **Azure Static Web Apps CLI (Optional but recommended)**: Required for local authentication emulation.
   ```bash
   npm install -g @azure/static-web-apps-cli
   ```
4. **Azure CLI & Azure Functions Core Tools**: Required for the backend (ensure `az` extension / import is set up as well).

### Step-by-Step Guide
1. **Clone the Repository**
   Open your terminal and clone the project to your local machine:
   ```bash
   git clone <repository-url>
   cd chinhin-pricing-strategist
   ```

2. **Run the Backend (Root Folder)**
   In the root directory, start the backend:
   ```bash
   func start
   ```

3. **Navigate to the Frontend Directory**
   Open a new terminal window/tab and navigate to the `frontend` folder:
   ```bash
   cd frontend
   ```

4. **Run the Frontend Server with Local Emulator**
   Start the application using the local development script. This script automatically runs the Next.js server along with the Azure SWA emulator:
   ```bash
   npm run dev:local
   ```
   
   *Note: If the command above fails, do this first before rerunning it:*
   ```bash
   npm install
   npm run build
   ```

5. **Access the Application**
   Open your web browser and navigate to:
   [http://localhost:3000](http://localhost:3000) - Next.js server
   [http://localhost:4280](http://localhost:4280) - SWA emulator (run this)

   *Note: When running locally with SWA, the Microsoft login button will route you through the SWA CLI local authentication emulator, allowing you to sign in with a mock user profile.*
