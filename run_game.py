"""Game entry point - Run this file to start the game."""
import sys
import os

# Add src to path for proper imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from main import main

if __name__ == "__main__":
    main()
