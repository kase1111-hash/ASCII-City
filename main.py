#!/usr/bin/env python3
"""
ShadowEngine - A Procedural ASCII Storytelling Game Engine

Run this file to play the test scenario.
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shadowengine.scenarios.test_scenario import run_test_scenario


def main():
    """Main entry point."""
    print()
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║                     SHADOWENGINE                          ║")
    print("║          A Procedural ASCII Storytelling Game             ║")
    print("║                                                           ║")
    print("║                    Phase 1 Prototype                      ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print()

    run_test_scenario()


if __name__ == "__main__":
    main()
