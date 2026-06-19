.PHONY: install test lint format clean run-validators

install:
	pip install -e .

test:
	pytest tests/ -v

format:
	black src/ tests/
	isort src/ tests/

lint:
	flake8 src/ tests/
	mypy src/ tests/

run-validators:
	python run_validator.py

clean:
	rm -rf .pytest_cache
	rm -rf __pycache__
	rm -rf src/futedata/__pycache__
