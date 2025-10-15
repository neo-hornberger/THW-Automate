.PHONY: build
build:
	docker build -t thw-automation .

.PHONY: run
run:
	docker run -v $(PWD)/config.toml:/app/config.toml --rm -it thw-automation
