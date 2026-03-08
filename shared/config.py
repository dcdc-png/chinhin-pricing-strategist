import os

PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT")
AGENT_NAME      = os.getenv("AZURE_AI_AGENT_NAME", "AI-Pricing-Strategist")
AGENT_VERSION   = os.getenv("AZURE_AI_AGENT_VERSION", "3")
AGENT_MODEL     = os.getenv("AZURE_AI_AGENT_MODEL", "gpt-4.1-nano")
EXCEL_PATH      = os.path.join(os.getcwd(), os.getenv("EXCEL_PATH", "data.xlsx"))
