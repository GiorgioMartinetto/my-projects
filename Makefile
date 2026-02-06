.PHONY: check
check:
	@echo "Running code checks..."
	ruff check --fix app/src tests/plan

.PHONY: format
format:
	@echo "Formatting code..."
	ruff format app/src tests/plan

.PHONY: all
all:
	@echo "Running all tasks..."
	$(MAKE) check
	$(MAKE) format

