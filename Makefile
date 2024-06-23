.PHONY: init
# init development
init:
	python3 -m venv venv

.PHONY: deps
# deps development
deps:
	pip install --upgrade pip
	pip install wheel
	pip install setuptools
	pip install twine
	pip install pytest==8.2.2
	pip install pytest-runner==6.0.1

.PHONY: test
# run tests
test:
	pytest --capture=no

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