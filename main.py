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
    print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
    print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
    print("@@@@@@@@@@GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG@@@@@@@@@@@@")
    print("@@@@@@@@@@G                                               G@@@@@@@@@@@@")
    print("@@@@@@@@@@G   ╔═════════════════════════════════════╗    G@@@@@@@@@@@@")
    print("@@@@@@@@@@G   ║         SHADOWENGINE                ║    G@@@@@@@@@@@@")
    print("@@@@@@@@@@G   ║   A Procedural ASCII Game Engine    ║    G@@@@@@@@@@@@")
    print("@@@@@@@@@@G   ║                                     ║    G@@@@@@@@@@@@")
    print("@@@@@@@@@@G   ║       STUDY ROOM ESCAPE             ║    G@@@@@@@@@@@@")
    print("@@@@@@@@@@G   ╚═════════════════════════════════════╝    G@@@@@@@@@@@@")
    print("@@@@@@@@@@G                                               G@@@@@@@@@@@@")
    print("@@@@@@@@@@GLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLG@@@@@@@@@@@@")
    print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
    print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
    print()

    run_test_scenario()


if __name__ == "__main__":
    main()
