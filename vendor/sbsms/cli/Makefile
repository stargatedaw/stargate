.PHONY: all check-dir build

all: check-dir build

check-dir:
	@if [ -d "vendor/sbsms/cli" ]; then \
		ls -l vendor/sbsms/cli; \
	else \
		echo "Directory vendor/sbsms/cli does not exist."; \
	fi

build:
	@if [ -d "vendor/sbsms/cli" ]; then \
		make -C /workspaces/stargate/vendor/sbsms/cli; \
	fi