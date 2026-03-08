from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from shared.config import PROJECT_ENDPOINT

def get_openai_client():
    if not PROJECT_ENDPOINT:
        raise RuntimeError("PROJECT_ENDPOINT is not set.")
    return AIProjectClient(
        endpoint=PROJECT_ENDPOINT,
        credential=DefaultAzureCredential(),
    ).get_openai_client()
