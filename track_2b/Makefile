.PHONY: run build test ask eval

IMAGE ?= alpenrecht
PORT ?= 5055
# Judges' convention: LLM_NAME / LLM_BASE_URL / LLM_API_KEY from the environment (or a local .env)
# HOST/PORT are fixed inside the container, so a PORT line in .env cannot move the listener; pick the host port with make run PORT=8080
ENV_FILE := $(wildcard .env)
DOCKER_ENV = $(if $(ENV_FILE),--env-file .env,) -e LLM_NAME -e LLM_BASE_URL -e LLM_API_KEY -e HOST=0.0.0.0 -e PORT=5055
# Git Bash on Windows: keep container paths such as /app from being rewritten to C:/Program Files/Git/app
export MSYS_NO_PATHCONV := 1
export MSYS2_ARG_CONV_EXCL := *

build:
	docker build -t $(IMAGE) .

# Start the web app on http://localhost:$(PORT)/
run: build
	@echo "Alpenrecht: open http://localhost:$(PORT)/  (Ctrl+C to stop)"
	docker run --rm -p $(PORT):5055 $(DOCKER_ENV) $(IMAGE)

# Offline checks: article/annex splitting, citation keys, relevance parsing (no API calls)
test: build
	docker run --rm $(IMAGE) python -m pytest -q tests

# One question in the terminal, e.g.  make ask Q="Ab wann gilt in Chur die Nachtruhe?" PLACE="7000 Chur"
ask: build
	docker run --rm $(DOCKER_ENV) $(IMAGE) python -m alpenrecht ask "$(Q)" --place "$(PLACE)"

# Live: run a question set through the pipeline (needs LLM_API_KEY), e.g. make eval SET=eval/questions_heldout100.json
# Each set writes its own eval/runs/<set>.jsonl (the runner skips ids already in that file, so a rerun resumes).
ifneq ($(filter eval,$(MAKECMDGOALS)),)
ifndef SET
$(error SET is required, e.g. make eval SET=eval/questions_heldout100.json)
endif
endif
OUT ?= eval/runs/$(basename $(notdir $(SET))).jsonl
eval: build
	docker run --rm $(DOCKER_ENV) -v "$(CURDIR)/eval:/app/eval" $(IMAGE) \
	  python eval/accuracy_run.py --set $(SET) --out $(OUT) --root /app
