# OpenVPN Logger Makefile

.PHONY: help install test demo clean setup validate run analyze

# Default target
help:
	@echo "OpenVPN Logger - Available commands:"
	@echo ""
	@echo "Setup:"
	@echo "  make setup      - Initialize configuration and install dependencies"
	@echo "  make install    - Install Python dependencies"
	@echo "  make validate   - Validate configuration"
	@echo ""
	@echo "Testing:"
	@echo "  make test       - Run setup tests"
	@echo "  make demo       - Set up demo environment"
	@echo ""
	@echo "Running:"
	@echo "  make run        - Start the OpenVPN logger"
	@echo "  make analyze    - Run data analysis"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean      - Clean up generated files"
	@echo "  make help       - Show this help message"

# Setup targets
setup: install
	@echo "Setting up OpenVPN Logger..."
	@python3 config.py init
	@echo "Setup complete! Edit .env file with your configuration."

install:
	@echo "Installing Python dependencies..."
	@pip3 install -r requirements.txt
	@echo "Dependencies installed."

validate:
	@echo "Validating configuration..."
	@python3 config.py validate

# Testing targets
test:
	@echo "Running setup tests..."
	@python3 test_setup.py

demo:
	@echo "Setting up demo environment..."
	@python3 demo.py --setup

# Running targets
run:
	@echo "Starting OpenVPN Logger..."
	@python3 openvpn_logger.py

analyze:
	@echo "Running data analysis..."
	@python3 analyzer.py

# Maintenance targets
clean:
	@echo "Cleaning up generated files..."
	@rm -f demo_openvpn.log demo_status.log
	@rm -f .env.demo
	@echo "Cleanup complete."

# Service management (requires sudo)
install-service:
	@echo "Installing systemd service..."
	@sudo cp openvpn-logger.service /etc/systemd/system/
	@sudo systemctl daemon-reload
	@echo "Service installed. Use 'sudo systemctl start openvpn-logger' to start."

start-service:
	@echo "Starting OpenVPN Logger service..."
	@sudo systemctl start openvpn-logger
	@sudo systemctl status openvpn-logger

stop-service:
	@echo "Stopping OpenVPN Logger service..."
	@sudo systemctl stop openvpn-logger

enable-service:
	@echo "Enabling OpenVPN Logger service..."
	@sudo systemctl enable openvpn-logger

disable-service:
	@echo "Disabling OpenVPN Logger service..."
	@sudo systemctl disable openvpn-logger

service-status:
	@sudo systemctl status openvpn-logger

service-logs:
	@sudo journalctl -u openvpn-logger -f

# Development targets
format:
	@echo "Formatting Python code..."
	@python3 -m black *.py

lint:
	@echo "Running linter..."
	@python3 -m flake8 *.py

# Quick start for development
dev-setup: setup demo
	@echo "Development environment ready!"
	@echo "Run 'make run' to start the logger"
	@echo "Run 'make analyze' to analyze data"

# Production setup
prod-setup: install validate
	@echo "Production setup complete!"
	@echo "Edit .env file with production configuration"
	@echo "Run 'make install-service' to install as system service"
