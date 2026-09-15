.PHONY: install playground

install:
	pip install -e .

playground:
	python -c "from google.adk.cli import main; main()" web expense_agent

run-service:
	uvicorn expense_agent.fast_api_app:app --host 127.0.0.1 --port 8080

generate-traces:
	python tests/eval/generate_traces.py

grade:
	agents-cli eval grade --traces artifacts/traces/generated_traces.json --output artifacts/grades/ --config tests/eval/eval_config.yaml

eval:
	python tests/eval/run_eval.py

