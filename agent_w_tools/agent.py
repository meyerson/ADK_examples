from google.adk.agents import Agent
from google.cloud import secretmanager
import os
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path

def _load_local_env() -> None:
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=False)

_load_local_env()

project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "adk-explorer-2025")
genai_api_key_secret_name = os.getenv("GENAI_API_KEY_SECRET_NAME", "genai-api-key")

# Configure Generative AI from Secret Manager and export to env for downstream libs
def configure_genai_api_key(project_id: str, secret_id: str, version: str = "latest") -> None:
    client = secretmanager.SecretManagerServiceClient()
    name = client.secret_version_path(project_id, secret_id, version)
    payload = client.access_secret_version(request={"name": name}).payload.data.decode("utf-8")
    os.environ["GOOGLE_API_KEY"] = payload
    # genai.configure(api_key=payload)  # optional if global config is preferred

configure_genai_api_key(project_id=project_id, secret_id=genai_api_key_secret_name)


def create_agent():
    return Agent(
        name="agent_w_tools",
        model="gemini-2.5-flash",
        description="Agent with tools enabled",
        instruction=(
            "You are a helpful assistant with access to tools. "
            "Use tools when appropriate and explain your steps succinctly."
        ),
        # tools=[]  # Placeholder: add tool declarations when ready
    )


root_agent = create_agent()
