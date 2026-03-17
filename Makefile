.PHONY: check mypy format all
mypy:
	@echo "Running mypy type checks..."
	mypy app/src

check:
	@echo "Running code checks..."
	ruff check --fix app/src
	$(MAKE) mypy


format:
	@echo "Formatting code..."
	ruff format app/src


all:
	@echo "Running all tasks..."
	$(MAKE) format
	$(MAKE) check


