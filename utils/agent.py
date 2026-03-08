import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()

def get_openai_client():
    """
    Initializes and returns the Azure AI Project client using DefaultAzureCredential.
    """
    project_endpoint = os.environ.get("PROJECT_ENDPOINT")
    if not project_endpoint:
        raise RuntimeError("PROJECT_ENDPOINT is not set in environment variables.")
        
    project_client = AIProjectClient(
        endpoint=project_endpoint,
        credential=DefaultAzureCredential(),
    )
    
    return project_client.get_openai_client()
