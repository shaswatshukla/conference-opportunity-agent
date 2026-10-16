PYTHON ?= python

.PHONY: discover report test lint calendar fixtures

discover:
	$(PYTHON) -m src.main discover

report:
	$(PYTHON) -m src.main report

fixtures:
	$(PYTHON) -m src.main discover --fixtures

test:
	$(PYTHON) -m unittest discover -s tests -v

lint:
	$(PYTHON) -m ruff check src tests

calendar:
	@echo "Calendar export is pending stage 5; no ICS is generated."
	@exit 1
