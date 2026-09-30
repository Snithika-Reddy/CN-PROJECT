"""Pytest root configuration adding project root to sys.path."""

from pathlib import Path
import sys

# Ensure project root is available to all test modules
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
