"""Pre-flight check: is the fieldlink atlas present and current?

RSC stages upstream repos in two locations:

  * ``atlas/remote/``  — committed snapshots, always present.
  * ``.fieldlink/merge_stage/`` — fresh pulls from ``fieldlink-pull.sh``.

Fresh pulls are preferred. If ``merge_stage`` is missing or stale relative
to ``.fieldlink.json``, the caller should be told to run the pull script
before feeding basins to the Mandala — the committed snapshot still works,
but live data may have moved.
"""

from __future__ import annotations

import pathlib
from dataclasses import dataclass, field
from typing import List, Optional

from rsc_mandala_bridge._paths import rsc_root as _default_root


@dataclass
class StalenessReport:
    rsc_root: pathlib.Path
    has_fieldlink_config: bool
    has_merge_stage: bool
    has_committed_atlas: bool
    config_newer_than_stage: bool
    staged_file_count: int
    committed_file_count: int
    warnings: List[str] = field(default_factory=list)

    @property
    def usable(self) -> bool:
        """True if any projector input is available (live or committed)."""
        return self.has_merge_stage or self.has_committed_atlas

    @property
    def recommend_pull(self) -> bool:
        """True when the caller should run fieldlink-pull.sh before projecting."""
        if not self.has_fieldlink_config:
            return False
        if not self.has_merge_stage:
            return True
        return self.config_newer_than_stage


def check_atlas_staleness(rsc_root: Optional[pathlib.Path] = None) -> StalenessReport:
    """Inspect the fieldlink staging area and return a structured report.

    The report never raises — callers decide whether to warn, prompt, or
    continue with the committed atlas.
    """
    root = pathlib.Path(rsc_root) if rsc_root is not None else _default_root()
    config = root / ".fieldlink.json"
    stage = root / ".fieldlink" / "merge_stage"
    committed = root / "atlas" / "remote"

    has_config = config.is_file()
    has_stage = stage.is_dir()
    has_committed = committed.is_dir()

    staged_files = _json_files(stage) if has_stage else []
    committed_files = _json_files(committed) if has_committed else []

    warnings: list[str] = []
    config_newer = False
    if has_config and has_stage and staged_files:
        config_mtime = config.stat().st_mtime
        newest_staged = max(p.stat().st_mtime for p in staged_files)
        config_newer = config_mtime > newest_staged
        if config_newer:
            warnings.append(
                ".fieldlink.json is newer than merge_stage; run ./fieldlink-pull.sh"
            )

    if not has_stage and has_config:
        warnings.append(
            ".fieldlink/merge_stage not found; run ./fieldlink-pull.sh for fresh data"
        )

    if not has_stage and not has_committed:
        warnings.append(
            "No atlas available: neither .fieldlink/merge_stage nor atlas/remote exists"
        )

    return StalenessReport(
        rsc_root=root,
        has_fieldlink_config=has_config,
        has_merge_stage=has_stage,
        has_committed_atlas=has_committed,
        config_newer_than_stage=config_newer,
        staged_file_count=len(staged_files),
        committed_file_count=len(committed_files),
        warnings=warnings,
    )


def _json_files(path: pathlib.Path) -> list[pathlib.Path]:
    if not path.is_dir():
        return []
    return [p for p in path.rglob("*.json") if p.is_file()]
