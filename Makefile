.PHONY: help install lint test test-dataset build run-api run-web run-worker clean

help:
	@echo "DISHA Management Commands:"
	@echo "  make install       Install dependencies across all modules"
	@echo "  make lint          Run formatters and linters"
	@echo "  make test          Run unit and integration test suites"
	@echo "  make test-dataset  Run dataset integrity tests"
	@echo "  make run-api       Start the FastAPI development server"
	@echo "  make run-web       Start the Next.js development server"
	@echo "  make run-worker    Start the background task worker"
	@echo "  make clean         Remove build artifacts and caches"

install:
	cd api && pip install -e .
	cd web && npm install
	cd cli && cargo build

lint:
	ruff check api/ worker/ ml/
	cd web && npm run lint

test: test-dataset
	pytest api/tests worker/tests ml/tests

test-dataset:
	python -m unittest tests/test_dataset.py -v

run-api:
	cd api && uvicorn app.main:app --reload --port 8000

run-web:
	cd web && npm run dev

run-worker:
	cd worker && python main.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf web/.next cli/target contracts/out
