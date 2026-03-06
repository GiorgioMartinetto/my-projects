.PHONY: check mypy format all
mypy:
	@echo "Running mypy type checks..."
	mypy app/src tests/plan

check:
	@echo "Running code checks..."
	ruff check --fix app/src tests/plan
	$(MAKE) mypy


format:
	@echo "Formatting code..."
	ruff format app/src tests/plan


all:
	@echo "Running all tasks..."
	$(MAKE) format
	$(MAKE) check


