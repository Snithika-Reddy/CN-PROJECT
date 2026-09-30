"""Convenience wrapper to run Power BI Desktop Auto-Refresher."""

import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from src.powerbi.auto_refresh import main

if __name__ == "__main__":
    main()
