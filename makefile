include common.mk

# Our directories
API_DIR = server
DB_DIR = data
SEC_DIR = security
REQ_DIR = .

FORCE:

prod: all_tests github

github: FORCE
	- git commit -a
	git push origin master

all_tests: FORCE
	cd $(API_DIR); make tests
	cd $(DB_DIR); make tests
	cd $(SEC_DIR); make tests
	cd cities; make tests
	cd states; make tests
	cd purchase_requests; make tests
	cd listings; make tests

dev_env: FORCE
	pip install -r $(REQ_DIR)/requirements-dev.txt
	@echo "You should set PYTHONPATH to: "
	@echo $(shell pwd)

docs: FORCE
	cd $(API_DIR); make docs

PYTHON ?= python3
STATES_CSV ?= states/raw_data/states.csv
CITIES_CSV ?= cities/raw_data/cities.csv

.PHONY: load_db
load_db:
	CLOUD_MONGO=0 $(PYTHON) -m data.load_db --states-csv "$(STATES_CSV)" --cities-csv "$(CITIES_CSV)"
