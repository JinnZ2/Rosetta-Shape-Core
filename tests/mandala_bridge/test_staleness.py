"""Pre-flight atlas-staleness checks."""

from __future__ import annotations

import os
import pathlib
import time

from rsc_mandala_bridge.staleness import check_atlas_staleness


def test_report_on_empty_layout(tmp_path: pathlib.Path):
    report = check_atlas_staleness(tmp_path)
    assert not report.has_fieldlink_config
    assert not report.has_merge_stage
    assert not report.has_committed_atlas
    assert not report.usable
    assert any("No atlas available" in w for w in report.warnings)


def test_report_prefers_merge_stage(tmp_path: pathlib.Path):
    (tmp_path / ".fieldlink.json").write_text("{}", encoding="utf-8")
    merge = tmp_path / ".fieldlink" / "merge_stage"
    merge.mkdir(parents=True)
    (merge / "a.json").write_text("{}", encoding="utf-8")

    report = check_atlas_staleness(tmp_path)
    assert report.has_merge_stage
    assert report.staged_file_count == 1
    assert report.usable
    assert not report.recommend_pull


def test_report_recommends_pull_when_config_newer(tmp_path: pathlib.Path):
    merge = tmp_path / ".fieldlink" / "merge_stage"
    merge.mkdir(parents=True)
    staged = merge / "a.json"
    staged.write_text("{}", encoding="utf-8")

    past = time.time() - 3600
    os.utime(staged, (past, past))

    config = tmp_path / ".fieldlink.json"
    config.write_text("{}", encoding="utf-8")

    report = check_atlas_staleness(tmp_path)
    assert report.config_newer_than_stage
    assert report.recommend_pull
    assert any("run ./fieldlink-pull.sh" in w for w in report.warnings)


def test_committed_atlas_keeps_bridge_usable(tmp_path: pathlib.Path):
    remote = tmp_path / "atlas" / "remote"
    remote.mkdir(parents=True)
    (remote / "x.json").write_text("{}", encoding="utf-8")

    report = check_atlas_staleness(tmp_path)
    assert report.has_committed_atlas
    assert report.committed_file_count == 1
    assert report.usable


def test_real_repo_report_is_usable():
    """Smoke test against the actual repo root."""
    report = check_atlas_staleness()
    assert report.usable
    # The repo has .fieldlink.json checked in but no merge_stage by default,
    # so a pull recommendation is expected in CI.
    assert report.has_fieldlink_config
