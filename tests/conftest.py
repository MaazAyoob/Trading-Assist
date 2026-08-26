import os
import sys
import pytest

# Add backend to sys.path so tests can import app modules directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
