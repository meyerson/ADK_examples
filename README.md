<!-- vscode-markdown-toc -->
* 1. [Getting Started](#GettingStarted)
* 2. [Prerequisites](#Prerequisites)
* 3. [Installation](#Installation)
	* 3.1. [Install Google Cloud CLI (`gcloud`)](#InstallGoogleCloudCLIgcloud)
	* 3.2. [Install Python SDK(s)](#InstallPythonSDKs)
* 4. [Google Cloud Resource Hierarchy](#GoogleCloudResourceHierarchy)
* 5. [Authentication](#Authentication)
		* 5.1. [CLI vs ADC (compact reference)](#CLIvsADCcompactreference)
		* 5.2. [Same vs Different (compact table)](#SamevsDifferentcompacttable)
	* 5.1. [Containers: Credentials (develop like prod)](#Containers:Credentialsdeveloplikeprod)
	* 5.2. [Quick Decision Guide: Local Dev vs. Work SSO](#QuickDecisionGuide:LocalDevvs.WorkSSO)
	* 5.3. [Profiles: Cleanly Separate Personal and Work](#Profiles:CleanlySeparatePersonalandWork)
	* 5.4. [Service Account Keys (When and How)](#ServiceAccountKeysWhenandHow)
	* 5.5. [Verify and Clean Up (avoid lingering state)](#VerifyandCleanUpavoidlingeringstate)
* 6. [Google Cloud Project Setup](#GoogleCloudProjectSetup)
* 7. [Basic Usage (Agents preview)](#BasicUsageAgentspreview)
	* 7.1. [Minimal Local Run Pattern (placeholder)](#MinimalLocalRunPatternplaceholder)
* 8. [Resources](#Resources)
* 9. [License](#License)

<!-- vscode-markdown-toc-config
	numbering=true
	autoSave=true
	/vscode-markdown-toc-config -->
<!-- /vscode-markdown-toc -->
# Google Cloud + ADK On-Ramp

A concise refresher to ramp on Google Cloud fundamentals (resource hierarchy, authentication, profiles, projects) with a light preview of Google ADK (agents) as the end goal. The focus is orientation and clean setup; agents are introduced but not the centerpiece.

##  1. <a name='GettingStarted'></a>Getting Started

This guide helps you confidently start experimenting in Google Cloud: understand how resources are organized, how authentication works across personal vs. work contexts, how to select projects, and how to avoid lingering state. We dangle ADK agents as the eventual destination, but the primary goal is giving you a solid footing before you touch agents.

##  2. <a name='Prerequisites'></a>Prerequisites

- Python 3.x
- Google Cloud account (personal and/or work)
- Google Cloud CLI (`gcloud`) installed
- ADK SDK installed (Python)

##  3. <a name='Installation'></a>Installation

###  3.1. <a name='InstallGoogleCloudCLIgcloud'></a>Install Google Cloud CLI (`gcloud`)
`gcloud` is the Google Cloud CLI, separate from any Python packages. You use it to manage auth, projects, and profiles.

macOS (Homebrew):
```bash
brew install --cask google-cloud-sdk
# Initialize and update
gcloud init
gcloud components update
```

Manual install and docs: https://cloud.google.com/sdk/docs/install

Verify:
```bash
gcloud --version
gcloud config configurations list
```

###  3.2. <a name='InstallPythonSDKs'></a>Install Python SDK(s)
ADK Python package naming may vary; confirm the official package for your environment. Placeholder:
```bash
pip install google-adk
```
Optionally use a virtual environment to isolate Python deps.

##  4. <a name='GoogleCloudResourceHierarchy'></a>Google Cloud Resource Hierarchy

Google Cloud organizes resources in a hierarchical structure. You can think of this as a taxonomy of ownership and placement for all your cloud assets:

1. **Organization** - The root node (represents your company/domain)
2. **Folders** - Optional grouping mechanism (e.g., by department, team, or environment)
3. **Projects** - Core organizational unit where resources are created and billing is tracked
4. **Resources** - Individual services (VMs, databases, storage buckets, etc.)

**Hierarchy (taxonomy):**
```
Organization
  └── Folder (optional, can be nested)
      └── Project
          └── Resources (ADK agents, Cloud Storage, etc.)
```

##  5. <a name='Authentication'></a>Authentication

This section is the hands-on introduction to auth and profiles. The core commands appear here once; later sections reference this section to avoid repetition.

Use a multi‑account approach: first verify your state, create or activate the right profile, and then log in.

```bash
# 1) Inspect profiles and active context
gcloud config configurations list

# If the desired profile is missing, create/activate it
gcloud config configurations create <profile-name>
gcloud config configurations activate <profile-name>

# 2) Inspect current account before logging in
gcloud auth list

# 3) Log in to the intended account (opens browser)
gcloud auth login --account=<you@example.com>

# 4) Create Application Default Credentials (for client libraries)
gcloud auth application-default login

# 5) Set and verify project in this profile
gcloud config set project <your-project-id>
gcloud config get-value project

# Optional: use a service account key for automation/CI
# gcloud auth activate-service-account --key-file=/path/to/key.json
# export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"

# Cleanup: revoke an account or reset ADC if needed
# gcloud auth revoke ACCOUNT_EMAIL
# rm -f ~/.config/gcloud/application_default_credentials.json
```

Tip: Keep one profile per context (e.g., `personal`, `work`). Align CLI auth, ADC, and project within that profile to avoid surprises.

####  5.1. <a name='CLIvsADCcompactreference'></a>CLI vs ADC (compact reference)
- CLI auth: `gcloud auth login --account=<email>`
  - Purpose: authenticate the `gcloud` CLI within the active profile.
  - Use to inspect/manage resources (projects, APIs, IAM) via CLI.
- ADC (apps): `gcloud auth application-default login`
  - Purpose: create credentials for client libraries used by your applications.
  - Writes to ~/.config/gcloud/application_default_credentials.json (standard ADC location).
- Service account creds: `GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json`
  - Purpose: alternative credential source for apps (non‑interactive, CI/CD, or stricter scoping).
  - When set, libraries use this file instead of the user ADC file.

Note on ADC vs Service Account creds
- Both are credential sources that Google client libraries discover via the ADC mechanism.
- User ADC is created via `gcloud auth application-default login` and stored at the standard path.
- Service account creds are injected by setting `GOOGLE_APPLICATION_CREDENTIALS` to a key file; this overrides the user ADC file.
- Choose based on context: user ADC for local interactive dev; service account for non‑interactive/CI or stricter scoping.
 - Client libraries handle tokens automatically: point to a credential source (ADC default file or `GOOGLE_APPLICATION_CREDENTIALS`), and the library mints and attaches `Authorization: Bearer <access_token>` without you manually fetching or injecting tokens.

Local ADC credential substitution (preferred for dev)
- Mount your user ADC file into the container and point `GOOGLE_APPLICATION_CREDENTIALS` at it. Libraries will use your refresh token to obtain access tokens automatically; logs show `user:<email>`.
- Use this to mirror production’s “provide creds at runtime” shape without distributing service account keys. If your user has the needed roles, this is sufficient for local workflows.

Footnote: service account impersonation
- The earlier “mount and point to your ADC file” is not true substitution of a service account identity; it uses your user identity. From the application’s perspective, what matters is that it can perform the required actions. This pattern still lets you develop in a single container/app without forking logic based on how credentials are provided.

Functional difference: private key vs refresh token
- Refresh token: a long‑lived OAuth grant tied to a user; used to fetch short‑lived access tokens, not for signing.
- Private key: cryptographic material used to sign JWT assertions for SA authentication; must be rotated and stored securely.
 - On‑wire header: clients send only `Authorization: Bearer <access_token>`; neither refresh tokens nor private keys are transmitted in API requests.

###  5.1. <a name='Containers:Credentialsdeveloplikeprod'></a>Containers: Credentials (develop like prod)
Develop locally in containers using the same pattern you’d use in production: provide credentials at runtime via a mount + env var. Use whichever source you have access to.

```bash
# Single run pattern (choose the credential source you have):
# Preferred for local dev: user ADC
SRC="$HOME/.config/gcloud/application_default_credentials.json"; DEST="/app/creds.json"
# Alternative (CI/prod): service account key, if org policy requires
# SRC="$HOME/.credentials/sa.json"; DEST="/app/creds.json"

docker run --rm \
  -v "$SRC:$DEST:ro" \
  -e GOOGLE_APPLICATION_CREDENTIALS="$DEST" \
  -e GOOGLE_CLOUD_PROJECT="your-project-id" \
  your-image:latest
```

Guidelines:
- Do not bake credentials into images; bind‑mount read‑only and use env vars.
- If CI/CD manages service accounts and you don’t have local access, use user ADC for local dev; swap to SA/Workload Identity in prod.
<a name="PersonalSAAdvice"></a>Note: You likely don’t need a service account in a personal project for typical local development. Prefer user ADC unless you have a specific non‑interactive need.

Manage via commands, not manual edits:
- Use `gcloud config configurations create|activate`, `gcloud auth login`, `gcloud auth application-default login`, `gcloud config set project`.
- Avoid editing files in ~/.config/gcloud; if needed, reset ADC by deleting ~/.config/gcloud/application_default_credentials.json and re‑running the commands above in the correct profile.

###  5.2. <a name='QuickDecisionGuide:LocalDevvs.WorkSSO'></a>Quick Decision Guide: Local Dev vs. Work SSO
(See [Credentials Map](#CredentialsMap) for choosing a credential type; use the commands in [Authentication](#Authentication) for setup.)
- Personal exploration (local dev): use `gcloud auth application-default login` (ADC). No key files needed, works with Google OAuth in browser.
- Work/SSO environments: prefer organization policies; if SSO blocks user ADC or requires service accounts, use a service account and set `GOOGLE_APPLICATION_CREDENTIALS` to its JSON key.
- CI/CD or non-interactive: always use a service account key (or workload identity if available).

### Addendum: Same vs Different (ADC vs SA)
For deeper comparisons, see the [Credentials Map](#CredentialsMap). This addendum defers to that single source to keep things concise.

| Aspect | User ADC (refresh token) | Service Account (private key) |
|---|---|---|
| Identity type | User (human Google account) | Service account (non‑human principal) |
| Credential material | Refresh token stored in ADC JSON | Private key in SA key JSON |
| Issuance flow | Browser OAuth → refresh token → access tokens | Local JWT signed with private key → access tokens |
| Scope of use | Works wherever the user has IAM roles | Typically scoped to one project; works where SA has roles |
| Portability | Follows the user across projects | Key tied to SA in a specific project |
| Token used for API calls | Short‑lived access tokens (~1h) | Short‑lived access tokens (~1h) |
| Discovery by client libs | Via ADC file | Via `GOOGLE_APPLICATION_CREDENTIALS` or ADC chain |

Notes
- Audit/logging principal: user shows as `user:<email>`; service account shows as `serviceAccount:<name>@<project>.iam.gserviceaccount.com`.
 - When a personal‑project service account is useful (brief): non‑interactive local workloads, tightly scoped least‑privilege access (e.g., one bucket), prod‑like SA policy testing, or deploying a service in your personal project. See the guidance above: [Why not use a personal‑project SA for local dev?](#PersonalSAAdvice)

###  5.x. <a name='CredentialsMap'></a>Credentials Map (ADC vs Service Account vs API Key)
To avoid confusion, here is how the three credential types differ and when to use each.

- ADC (user OAuth refresh token)
  - Source: created via `gcloud auth application-default login` → writes to `~/.config/gcloud/application_default_credentials.json`.
  - Used by: Google Cloud client libraries (Storage, Pub/Sub, IAM, etc.).
  - Behavior: Libraries mint short‑lived OAuth access tokens and attach `Authorization: Bearer <token>` automatically.
  - When to use: Local interactive development; mounting into containers for dev parity; commands like `gcloud auth application-default print-access-token` for manual HTTP tests.

- Service Account credentials (private key JSON)
  - Source: downloaded key for a service account; provided via `GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json`.
  - Used by: Same Google Cloud client libraries when non‑interactive or stricter scoping is required (CI/CD, prod services).
  - Behavior: Libraries sign JWTs locally with the private key to obtain short‑lived access tokens; headers still carry `Authorization: Bearer <token>`.
  - When to use: Automation, CI/CD, or when org policy mandates SAs; avoid baking keys into images, prefer runtime mounts or Workload Identity.

- API Key (Generative AI)
  - Source: static key string provided by the Generative AI service; store as `GOOGLE_API_KEY` in env/.env.
  - Used by: `google-generativeai` SDK and services that explicitly require API keys.
  - Behavior: Configured once (e.g., `genai.configure(api_key=...)`); requests authenticate via API key, not OAuth. Do not use API keys for Google Cloud OAuth‑protected services.
  - When to use: Calling Generative AI models/endpoints; keep separate from ADC/SA flows.

Practical guidance
- Use this section as the single source of truth on credential types.
 - Containers: it’s common to provide both, but each is used for different services.
  - Google Cloud APIs → prefer ADC for dev; SA for CI/prod. API keys are not used for Cloud OAuth APIs.
  - Generative AI → provide `GOOGLE_API_KEY` via env; ADC is not required for Generative AI.
- Headers: only short‑lived access tokens go into `Authorization: Bearer ...`. API keys are sent per the Generative AI client’s configuration.
- Separation of concerns: do not mix API keys and OAuth tokens for the same request.

###  5.3. <a name='Profiles:CleanlySeparatePersonalandWork'></a>Profiles: Cleanly Separate Personal and Work
Use profiles to isolate contexts; create them only once, then switch.

```bash
# List and switch
gcloud config configurations list
gcloud config configurations activate personal
gcloud config configurations activate work
```

Sample `gcloud config configurations list` output:
```bash
NAME      IS_ACTIVE  ACCOUNT                   PROJECT
default   False      you@work.com              work-project-123
personal  True       you@gmail.com             personal-sandbox-001
```
- If `IS_ACTIVE=True` shows the intended `ACCOUNT` and `PROJECT`, you’re ready to interact with that context.
- If only `default` appears, create and activate a new profile, then log in and set a project (see Authentication steps above).
Notes:
- `gcloud auth login` authenticates the CLI; `gcloud auth application-default login` creates ADC for client libraries.
- Prefer matching accounts for CLI and ADC within a profile to reduce confusion.

###  5.4. <a name='ServiceAccountKeysWhenandHow'></a>Service Account Keys (When and How)
- Use for automation, CI, or when org policy requires.
- Create a service account with least privilege (e.g., roles needed by your agent only).
- Download a key and store it outside your repo (e.g., `~/.credentials/my-sa.json`).
- Point libraries at it:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.credentials/my-sa.json"
```

Rotate keys periodically and avoid committing them. Consider Workload Identity Federation for CI to avoid static keys.

###  5.5. <a name='VerifyandCleanUpavoidlingeringstate'></a>Verify and Clean Up (avoid lingering state)
Use [Authentication](#Authentication) for commands; this section only lists quick checks to avoid duplication.

```bash
# Print an access token (manual testing)
gcloud auth application-default print-access-token

# See active account(s)
gcloud auth list

# Check active project
gcloud config get-value project

# Revoke an account
gcloud auth revoke ACCOUNT_EMAIL

# Reset ADC (hard reset)
rm -f ~/.config/gcloud/application_default_credentials.json
```

##  6. <a name='GoogleCloudProjectSetup'></a>Google Cloud Project Setup

**Important:** Before working with ADK, ensure you're using the correct Google Cloud project to avoid accidentally working in a default project.

```bash
# Discover projects
gcloud projects list

# (Org users) Explore hierarchy
gcloud organizations list
gcloud resource-manager folders list --organization=YOUR_ORG_ID

# Select a project (then verify in the [Authentication](#Authentication) block)
gcloud config set project YOUR_PROJECT_ID
gcloud config get-value project

# View current configuration
gcloud config list
```

Best practices:
- Keep separate projects for personal vs work experimentation.
- Enable required APIs per project (e.g., Vertex AI, IAM) before running ADK samples.
- Use labels on resources (e.g., `env=personal`, `team=demo`) for easy cleanup.

##  7. <a name='BasicUsageAgentspreview'></a>Basic Usage (Agents preview)

```python
# Example: Basic ADK setup
from google import adk

# Initialize your agent
agent = adk.Agent()
```

###  7.1. <a name='MinimalLocalRunPatternplaceholder'></a>Minimal Local Run Pattern (placeholder)
Depending on the ADK Python package, init may require project/region and tools. This placeholder shows how ADC is automatically used by the client libraries.

```python
# app.py
import os

# Optional: pin project via env if not using gcloud config
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "YOUR_PROJECT_ID")

from google import adk

def main():
  agent = adk.Agent()  # adjust per ADK docs
  # Example action (replace with real ADK call):
  # response = agent.invoke({"input": "hello"})
  # print(response)
  print("Agent initialized. Configure tools and calls per ADK docs.")

if __name__ == "__main__":
  main()
```

Container-only workflow (no host installs):
- Build image and run with ADC mounted via [Justfile](Justfile).

```bash
# Build container (installs deps inside the image)
just build

# Run container with ADC mounted (replace YOUR_PROJECT_ID)
just run PROJECT_ID=YOUR_PROJECT_ID

# Optional: open a shell in the image
just shell
```

##  8. <a name='Resources'></a>Resources

- [Official ADK Documentation](https://cloud.google.com/adk)
- [API Reference](https://cloud.google.com/adk/docs/reference)
- [ADK Python API Reference](https://google.github.io/adk-docs/api-reference/python/)
 - [gcloud Configurations](https://cloud.google.com/sdk/docs/configurations)
 - [Application Default Credentials](https://cloud.google.com/docs/authentication/provide-credentials-adc)
 - [Service Accounts](https://cloud.google.com/iam/docs/service-accounts)
 - [Project and Resource Hierarchy](https://cloud.google.com/resource-manager/docs/cloud-resource-hierarchy)

##  9. <a name='License'></a>License

MIT

##  10. Programmatic Credentials (API key vs access token)

There are two common credential shapes you may need:
- API key: used by Google Generative AI (via `google-generativeai`).
- OAuth access token: minted automatically from ADC for Google Cloud client libraries.

API key (Generative AI)
- Preferred: store in `.env` and read at runtime. See [Credentials Map](#CredentialsMap) for how API keys differ from ADC/SA.

```python
# Load API key from env (e.g., via python-dotenv)
import os
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
  raise RuntimeError("GOOGLE_API_KEY is not set. Add it to .env or your runtime env.")

import google.generativeai as genai
genai.configure(api_key=api_key)
```

Access token (ADC → Bearer) for manual testing
- Client libraries auto-handle this; you typically do NOT need to fetch tokens.
- For debugging or calling an HTTP API manually, mint a token from ADC:

```python
import google.auth
from google.auth.transport.requests import Request

credentials, project_id = google.auth.default()
credentials.refresh(Request())
print("Access Token:", credentials.token)
print("Project:", project_id)
```

CLI alternative (quick check):
```bash
gcloud auth application-default print-access-token
```

Notes (see [Credentials Map](#CredentialsMap) for detail)
- API keys: only for services that require them (e.g., Generative AI).
- ADC: for Google Cloud services; libraries attach Bearer tokens automatically.
- Service accounts: similar runtime behavior to ADC, but private keys and least‑privilege for automation.

### API Key: Create, Capture, Store (quick how‑to)
- Enable API Keys API (if not already):
```bash
gcloud services enable apikeys.googleapis.com
```
- Create a new key and capture the raw key string (shown only once):
```bash
gcloud services api-keys create --display-name="genai-dev" --format="get(keyString)"
```
- Verify keys (metadata only; does not show the key string again):
```bash
gcloud services api-keys list --format="table(name,displayName,uid,createTime)"
```
- Store the key securely in Secret Manager:
```bash
gcloud secrets create genai-api-key --replication-policy="automatic"
printf "%s" "YOUR_API_KEY" | gcloud secrets versions add genai-api-key --data-file=-
```
- Retrieve at runtime (Python) and configure Generative AI:
```python
from google.cloud import secretmanager
import google.generativeai as genai

client = secretmanager.SecretManagerServiceClient()
name = client.secret_version_path("YOUR_PROJECT_ID", "genai-api-key", "latest")
payload = client.access_secret_version(request={"name": name}).payload.data.decode("utf-8")
genai.configure(api_key=payload)
```
- Optional: inject via env when running a container (never bake into images):
```bash
docker run --rm \
  -e GOOGLE_API_KEY="$(gcloud secrets versions access latest --secret=genai-api-key)" \
  adk-examples:latest
```

Reminder
- You cannot retrieve the raw API key string again after creation; rotate by creating a new key, updating consumers, and deleting the old one.
