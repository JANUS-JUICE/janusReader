from pathlib import Path
import sys

# Ensure tests can import the package directly from src/ without installation.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
