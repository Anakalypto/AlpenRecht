.PHONY: run build test ask eval

IMAGE ?= alpenrecht
PORT ?= 5055
# Judges' convention: LLM_NAME / LLM_BASE_URL / LLM_API_KEY from the environment (or a local .env)
ENV_FILE := $(wildcard .env)
DOCKER_ENV = $(if $(ENV_FILE),--env-file .env,) -e LLM_NAME -e LLM_BASE_URL -e LLM_API_KEY

build:
	docker build -t $(IMAGE) .

# Start the web app on http://localhost:$(PORT)/
run: build
	docker run --rm -p $(PORT):5055 $(DOCKER_ENV) $(IMAGE)

# Offline checks: article/annex splitting, citation keys, relevance parsing (no API calls)
test: build
	docker run --rm $(IMAGE) python -m pytest -q tests

# One question in the terminal, e.g.  make ask Q="Ab wann gilt in Chur die Nachtruhe?" PLACE="7000 Chur"
ask: build
	docker run --rm $(DOCKER_ENV) $(IMAGE) python -m alpenrecht ask "$(Q)" --place "$(PLACE)"

# Live: run a question set through the pipeline (needs LLM_API_KEY), e.g. make eval SET=eval/questions_heldout100.json
eval: build
	docker run --rm $(DOCKER_ENV) -v "$(CURDIR)/eval:/app/eval" $(IMAGE) \
	  python eval/accuracy_run.py --set $(SET) --out eval/runs/latest.jsonl --root /app --env /app/.env
