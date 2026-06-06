#!/usr/bin/env python3
"""
HyperPack - Install any Android icon pack on Xiaomi HyperOS
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hyperpack.cli import main

if __name__ == "__main__":
    main()
