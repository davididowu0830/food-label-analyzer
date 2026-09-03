"""
main.py
=======
Entry point for the Food Label Analyzer application.
"""
import os
import sys

# Force the project root directory into Python's search path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.app_ui import run_app

if __name__ == "__main__":
    run_app()