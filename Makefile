.PHONY: init
# init development
init:
	python3 -m venv venv

.PHONY: clean
# clean development
clean:
	rm -rf *.csv
	rm -rf *.pickle
	rm -rf *.json
	rm -rf *.txt
	rm -rf zakat/*.csv
	rm -rf zakat/*.pickle
	rm -rf zakat/*.json

.PHONY: deps
# deps development
deps:
	python3 -m pip install --upgrade pip
	python3 -m pip install wheel
	python3 -m pip install setuptools
	python3 -m pip install twine
	python3 -m pip install pytest==8.2.2
	python3 -m pip install pytest-runner==6.0.1
	python3 -m pip install --upgrade twine
	python3 -m pip install build

.PHONY: pytest
# run pytest
pytest:
	pytest --capture=no

.PHONY: test
# run tests
test:
	make clean && python zakat/zakat_tracker.py

.PHONY: deploy
# deploy package
deploy:
	python3 -m build
	python3 -m twine upload --repository zakat dist/*

# show help
help:
	@echo ''
	@echo 'Usage:'
	@echo ' make [target]'
	@echo ''
	@echo 'Targets:'
	@awk '/^[a-zA-Z\-0-9]+:/ { \
	helpMessage = match(lastLine, /^# (.*)/); \
			if (helpMessage) { \
					helpCommand = substr($$1, 0, index($$1, ":")-1); \
					helpMessage = substr(lastLine, RSTART + 2, RLENGTH); \
					printf "\033[36m%-22s\033[0m %s\n", helpCommand,helpMessage; \
			} \
	} \
	{ lastLine = $$0 }' $(MAKEFILE_LIST)

.DEFAULT_GOAL := help