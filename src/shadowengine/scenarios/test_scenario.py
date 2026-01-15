"""
Test Scenario - Noir Detective Game

An LLM-driven procedural mystery with full ASCII visuals.
The city generates as you explore. NPCs respond dynamically.
"""

# Re-export the noir detective scenario as the default test scenario
from .study_escape import create_study_escape as create_test_scenario
from .study_escape import run_study_escape as run_test_scenario

__all__ = ['create_test_scenario', 'run_test_scenario']


if __name__ == "__main__":
    run_test_scenario()
