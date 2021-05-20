setup:
	python -m venv .venv && . .venv/bin/activate
	pip install --upgrade pip
	pip install -r requirements.dev
	pip install -r requirements.txt

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test:
	rm -f .coverage
	rm -f .coverage.*

clean: clean-pyc clean-test

test: clean
	. .venv/bin/activate
	PYTHONPATH=. pytest tests --cov=lexupdater --cov-report=term-missing

mypy:
	. .venv/bin/activate
	PYTHONPATH=. mypy lexupdater

lint:
	. .venv/bin/activate
	PYTHONPATH=. pylint lexupdater -j 4 --reports=y

check: test
