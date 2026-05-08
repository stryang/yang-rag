#!/usr/bin/env python
"""Pytest configuration."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load .env for tests
from dotenv import load_dotenv
load_dotenv()

# Set test API key if not set
if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "sk-test-key-for-unit-tests"
