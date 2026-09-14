"""
main.py

Root-level convenience entry point: `python main.py`
(equivalent to `python launcher/launch.py`, provided at the root because
some users expect a top-level main.py). launch.bat / launch.sh call this.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from launcher.launch import main

if __name__ == "__main__":
    main()
