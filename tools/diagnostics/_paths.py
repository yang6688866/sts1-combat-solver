"""Where the recorded game data lives, resolved in one place.

The test logs are not part of the repo: a player exports them from a running
game, and they sit outside the checkout. Hardcoding that path per script broke
every one of them the moment the directory moved, so resolve it once here.

  STS_TEST_LOGS  directory with sts1-test-<seed>.jsonl and the F6
                 sts1-state_divergence-*.json exports
                 defaults to E:\\sts-devkit\\test-logs

  STS_RUNS       the mod's own runs/ directory, whose request records carry the
                 RNG state that the .jsonl behaviour logs omit
                 defaults to %LOCALAPPDATA%\\STS1CombatSolver\\runs

The card/potion/relic tables are wiki exports kept in the repo, so they resolve
from this file's own location and never move.
"""
import os
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
DATA = TOOLS / "data"

LOG_DIR = Path(os.environ.get("STS_TEST_LOGS", r"E:\sts-devkit\test-logs"))
RUNS_DIR = Path(
    os.environ.get(
        "STS_RUNS",
        Path(os.environ.get("LOCALAPPDATA", r"C:\Users\yang\AppData\Local"))
        / "STS1CombatSolver"
        / "runs",
    )
)


def behaviour_logs():
    """Every recorded run, oldest file first. Empty list if the directory moved."""
    return sorted(LOG_DIR.glob("sts1-test-*.jsonl"))


def divergence_exports(pattern="*.json"):
    """F6 exports, the only recordings that carry real RNG state."""
    return sorted(LOG_DIR.glob(pattern))
