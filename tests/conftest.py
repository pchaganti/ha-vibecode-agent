"""Pytest configuration and shared fixtures."""
import os
import sys

# Set test environment variables before importing app
os.environ["HA_TOKEN"] = "test-token-for-pytest"
os.environ["HA_URL"] = "http://localhost:8123"
os.environ["CONFIG_PATH"] = "/tmp/ha-test-config"
os.environ["LOG_LEVEL"] = "WARNING"
os.environ["GIT_VERSIONING_AUTO"] = "false"
os.environ["MAX_BACKUPS"] = "5"
