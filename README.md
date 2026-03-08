# Fiamma AI Pricing Strategist — User Guide

Welcome to the **Fiamma AI Pricing Strategist**, an intelligent decision-support tool designed to replace manual guesswork with data-driven pricing recommendations. This tool empowers sales managers to maximize profit margins, balance competitiveness, and optimize stock levels across all sales channels.

1. **Web APP:** https://green-dune-0c54f0e10.2.azurestaticapps.net/
2. **Challenge 9: Video Demo:** https://drive.google.com/drive/folders/1JlMNmcbt-FT_4eGmE7nfPHqVxtKSyeKa

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

### Step 1: Input Deal Parameters (Margin Simulator)
* **Customer** — A dropdown labelled "Select customer...". Choose the dealer or customer account for whom you are preparing the pricing quote.
• **Item** — A dropdown labelled "Select item...". Choose the specific product SKU or item you wish to price.

### Step 2: Review the AI Rationale
Scroll down to the **AI Pricing Rationale** panel to see the exact price recommended by the engine. The AI provides a "Smart Why" rationale, breaking down the factors that influenced the decision. 
Review the individual impact cards to see how the following data points contributed to the final price: 
* **Customer Purchase History**: Adjustments made for loyalty and repeat purchasing behavior.
* **Stock Aging**: Discounts dynamically applied or withheld based on how long the inventory has been sitting in the warehouse.
* **Market Demand**: Price elasticity adjustments based on current product demand.
* **Competitor Pricing**: Strategic positioning to win the deal without needlessly sacrificing margin against competitors.

### Step 3: Finalize the Quote
Use the summarized AI insights to confidently generate a quote for the dealer, knowing exactly how the price balances win-probability against gross margin.

### Step 4: Consult the AI Assistant
If you need further clarification or want to test edge cases, click the **Floating Chat Icon** in the bottom right corner. This opens the *Microsoft AI Foundry Assistant* where you can ask natural language questions (e.g., *"What happens to our margin if I offer a 10% discount to clear aging stock?"*).

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

### Step-by-Step Guide
1. **Clone the Repository**
   Open your terminal and clone the project to your local machine:
   ```bash
   git clone <repository-url>
   cd chinhin-pricing-strategist
   ```

2. **Navigate to the Frontend Directory**
   The application logic is contained within the `frontend` folder:
   ```bash
   cd frontend
   ```

3. **Install Dependencies**
   Install all the required Node.js packages:
   ```bash
   npm install
   ```

4. **Run the Server with Local Emulator**
   Start the application using the local development script. This script automatically runs the Next.js server along with the Azure Static Web Apps (SWA) emulator so that the Microsoft authentication flow works properly on your machine:
   ```bash
   npm run dev:local
   ```

5. **Access the Application**
   Open your web browser and navigate to:
   [http://localhost:3000](http://localhost:3000) - Next.js server
   [http://localhost:4280](http://localhost:4280) - SWA emulator (run this)

   *Note: When running locally with SWA, the Microsoft login button will route you through the SWA CLI local authentication emulator, allowing you to sign in with a mock user profile.*
