#!/usr/bin/env python3
"""
Accordo Agent CLI Runner

This script allows running the CLI directly without pip install.

Usage:
    ./accordo.py generate "description"
    ./accordo.py validate file.cto
    ./accordo.py --help
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.cli.main import main

if __name__ == "__main__":
    main()
