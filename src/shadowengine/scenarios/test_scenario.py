"""
Test Scenario - Study Room Escape Game

A puzzle-based escape room experience with full ASCII visuals.
Find clues, solve puzzles, and escape the locked study!
"""

# Re-export the escape room scenario as the default test scenario
from .study_escape import create_study_escape as create_test_scenario
from .study_escape import run_study_escape as run_test_scenario

__all__ = ['create_test_scenario', 'run_test_scenario']


if __name__ == "__main__":
    run_test_scenario()
