import os
from pathlib import Path

from dotenv import load_dotenv
from google.cloud import secretmanager
from litellm import completion as llm_chat
from litellm import responses as llm_responses  # available if we switch to responses API

from google.adk.agents import Agent
from google.adk.tools.google_api_tool import GmailToolset
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.google_search_tool import GoogleSearchTool

def _load_local_env() -> None:
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=False)

_load_local_env()

project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "adk-explorer-2025")

# Map of target env var -> default Secret Manager secret ID.
# At runtime you can override the secret ID for a given env var
# by setting an env var named "<TARGET_ENV>_SECRET_NAME", in the .env file or otherwise.
SECRETS_CONFIG: dict[str, str] = {
    "GOOGLE_API_KEY": "genai-api-key",
    "OPENROUTER_API_KEY": "openrouter-api-key",
}


def configure_secrets_from_secret_manager(
    project_id: str,
    secrets: list[tuple[str, str]],
    version: str = "latest",
) -> None:
    """Load one or more secrets from Secret Manager into environment variables.

    Args:
        project_id: Google Cloud project ID.
        secrets: List of (secret_id, env_var_name) tuples.
        version: Secret version to load (defaults to "latest").
    """

    client = secretmanager.SecretManagerServiceClient()

    for secret_id, env_var_name in secrets:
        name = client.secret_version_path(project_id, secret_id, version)
        value = client.access_secret_version(request={"name": name}).payload.data.decode("utf-8")
        os.environ[env_var_name] = value


configure_secrets_from_secret_manager(
    project_id=project_id,
    secrets=[
        (
            os.getenv(f"{target_env}_SECRET_NAME", default_secret_id),
            target_env,
        )
        for target_env, default_secret_id in SECRETS_CONFIG.items()
    ],
)


def send_sms(phone_number: str, body: str) -> dict:
    """
    This tool sends an SMS message to the specified phone number.

    Args:
        phone_number: Destination phone number.
        body: Text content of the SMS.

    Returns:
        A status payload describing the stubbed SMS.
    """

    return {
        "status": "stubbed_sms",
        "phone_number": phone_number,
        "body": body,
    }


def get_russian_prison_joke() -> dict:
    """Generate a light, non-violent joke using LiteLLM's responses API.

    The main agent continues using Gemini 2.5 Flash; this tool delegates
    joke generation to a separate model (e.g., Gemma 3 12B) via LiteLLM.
    """

    prompt = (
        "Tell me a Russian prison joke, in Russian."
    )

    try:
        # see supported models https://github.com/BerriAI/litellm/blob/main/model_prices_and_context_window.json
        response = llm_chat(
            model="openrouter/google/gemini-2.0-flash-001",
            messages=[{"role": "user", "content": prompt}],
            base_url="https://openrouter.ai/api/v1",
        )
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": repr(exc)}

    return {
        "status": "success",
        "raw_response": str(response),
    }


def create_agent():
    return Agent(
        name="agent_w_tools",
        model="gemini-2.5-flash",
        description="Agent with tools enabled",
        instruction=(
            "You are a helpful assistant with access to tools. "
            "Use tools when appropriate and explain your steps succinctly."
        ),
        tools=[
            GoogleSearchTool(bypass_multi_tools_limit=True),
            GmailToolset(tool_name_prefix="gmail_"),
            FunctionTool(send_sms),
            FunctionTool(get_russian_prison_joke),
        ],
    )


root_agent = create_agent()
