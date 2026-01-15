set dotenv-load
set shell := ["bash", "-cu"]

adc_path := "${HOME}/.config/gcloud/application_default_credentials.json"
# Default agent path on host; can be overridden to swap agents
# Point to the 'reluctant_agent' folder by default
agent_path := "${AGENT_PATH:-${PWD}/}"

setup_just:
	just --list

build:
	docker build -t adk-examples:latest .

shell:
	SRC="{{adc_path}}"; \
	DEST="/app/creds.json"; \
		ENV_FILE_ARG=""; \
		if [ -f "{{agent_path}}/.env" ]; then ENV_FILE_ARG="--env-file {{agent_path}}/.env"; fi; \
		docker run --rm -it \
		  -v "$SRC:$DEST:ro" \
		  -v "{{agent_path}}:/app/agents:ro" \
		  -p 8000:8000 \
			$ENV_FILE_ARG \
		  -e GOOGLE_APPLICATION_CREDENTIALS="$DEST" \
		  adk-examples:latest /bin/bash

web:
	SRC="{{adc_path}}"; \
	DEST="/app/creds.json"; \
		ENV_FILE_ARG=""; \
		if [ -f "{{agent_path}}/.env" ]; then ENV_FILE_ARG="--env-file {{agent_path}}/.env"; fi; \
		docker run --rm \
		  -v "$SRC:$DEST:ro" \
		  -v "{{agent_path}}:/app/agents:ro" \
		  -p 8000:8000 \
			$ENV_FILE_ARG \
		  -e GOOGLE_APPLICATION_CREDENTIALS="$DEST" \
			-w /app/agents \
		  adk-examples:latest adk web --reload_agents --host 0.0.0.0 --port 8000
