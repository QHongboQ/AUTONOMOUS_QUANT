"""Public entry point for the single active P1 PIT research path.

The pre-shrink contracts/compiler modules remain importable only so the frozen
behavioral oracle tests can run.  They are deliberately not re-exported here.
"""

from .thin_runtime import ResearchReadyUniverse, build_research_ready_universe

__all__ = ["ResearchReadyUniverse", "build_research_ready_universe"]
