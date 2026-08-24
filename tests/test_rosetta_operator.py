"""Tests for the Rosetta operator stack — T1 rosetta, T2 families, T3 entry,
T4 scope, T5 gate log, plus gap_scan."""
import datetime
import json
import pathlib

import pytest
from jsonschema import Draft202012Validator

from rosetta_shape_core import curiosity as cur
from rosetta_shape_core import entry as entry_mod
from rosetta_shape_core import families as fam
from rosetta_shape_core import gap_scan as gs
from rosetta_shape_core import gate_log as gl
from rosetta_shape_core import holding as hold
from rosetta_shape_core import lid_import as lid
from rosetta_shape_core import provenance as prov
from rosetta_shape_core import rosetta as rop
from rosetta_shape_core import scope as sc
from rosetta_shape_core import shape_read as sr
from rosetta_shape_core import tier_check as tier
from rosetta_shape_core import transfer as tr

ROOT = pathlib.Path(__file__).resolve().parents[1]

MODULES = [rop, fam, entry_mod, sc, gl, tr, prov, lid, tier, hold, cur, sr, gs]


# ── every module carries its own selftest ─────────────────────────

@pytest.mark.parametrize("module", MODULES, ids=lambda m: m.__name__.rsplit(".", 1)[-1])
def test_module_selftest_passes(module):
    assert module.selftest() == []


@pytest.mark.parametrize("module", MODULES, ids=lambda m: m.__name__.rsplit(".", 1)[-1])
def test_module_selftest_cli_exits_zero(module, capsys):
    assert module.main(["--selftest"]) == 0
    assert "FAIL" not in capsys.readouterr().out


@pytest.mark.parametrize("module", MODULES, ids=lambda m: m.__name__.rsplit(".", 1)[-1])
def test_module_states_the_constraints(module):
    """Each file restates the repo constraints at the top. That is the spec."""
    doc = module.__doc__ or ""
    assert "CONSTRAINTS" in doc
    assert "markers to explore" in doc
    assert "no moral labels" in doc


@pytest.mark.parametrize("module", MODULES, ids=lambda m: m.__name__.rsplit(".", 1)[-1])
def test_modules_are_stdlib_only(module):
    """Phone-buildable: no third-party imports in the operator stack."""
    src = pathlib.Path(module.__file__).read_text(encoding="utf-8")
    for line in src.splitlines():
        line = line.strip()
        if line.startswith("import ") or line.startswith("from "):
            root = line.split()[1].split(".")[0]
            assert root in {
                "__future__", "argparse", "dataclasses", "datetime", "json",
                "pathlib", "re", "statistics", "sys", "tempfile", "typing", "math",
                "rosetta_shape_core",
            }, f"{module.__name__}: non-stdlib import {root!r}"


# ── T2 families ───────────────────────────────────────────────────

def test_seed_families_are_marked_spec_derived_not_authored():
    """The nine came in with the build spec. Nothing may quietly claim AUTHOR."""
    for f in fam.FAMILIES.values():
        assert f.provenance.get("concept") == prov.SPEC, f.id
        assert f.provenance.get("record") == prov.MODEL, f.id


def test_seed_families_survive_their_own_falsifier():
    assert fam.audit_families() == []


def test_every_family_decomposes_to_named_physical_terms():
    for f in fam.FAMILIES.values():
        assert f.decomposition
        assert set(f.decomposition) <= fam.PHYSICAL_TERMS


def test_family_with_no_physical_decomposition_is_misfiled():
    findings = fam.audit_family(fam.Family("VIBES", "a feeling", ("mood",),
                                           provenance=prov.make(prov.MODEL)))
    assert any("mis-filed" in f for f in findings)


def test_register_family_rejects_a_misfiled_family():
    with pytest.raises(ValueError):
        fam.register_family(fam.Family("HUNCH", "a hunch", ("intuition",),
                                       provenance=prov.make(prov.MODEL)))
    assert "HUNCH" not in fam.FAMILIES


def test_register_family_rejects_a_family_with_no_provenance():
    with pytest.raises(ValueError):
        fam.register_family(fam.Family("UNMARKED", "a term", ("length",)))
    assert "UNMARKED" not in fam.FAMILIES


def test_register_family_accepts_a_new_physical_term_and_resolves_it():
    surface = fam.Family("CAPILLARITY", "rise against gravity in a narrow channel",
                         ("surface_tension", "length", "density", "gravitational_field"),
                         ("capillary",), provenance=prov.make(prov.MODEL))
    try:
        fam.register_family(surface)
        assert fam.resolve("capillary") == "CAPILLARITY"
        assert fam.audit_families() == []
    finally:
        fam.FAMILIES.pop("CAPILLARITY", None)
        fam._reindex()
    assert fam.resolve("capillary") is None


def test_register_family_rejects_duplicates():
    with pytest.raises(ValueError):
        fam.register_family(fam.FAMILIES["FLOW"])


@pytest.mark.parametrize("term,expected", [
    ("gravity", "GRAVITY_LOAD"), ("load", "GRAVITY_LOAD"), ("heat", "THERMAL_EXCHANGE"),
    ("STRAIN", "STRAIN"), ("deformation", "STRAIN"), ("phase", "PHASE"),
])
def test_alias_resolution(term, expected):
    assert fam.resolve(term) == expected


def test_resolve_does_not_invent_families():
    assert fam.resolve("astrology") is None
    assert fam.resolve("") is None


# ── T3 entry ──────────────────────────────────────────────────────

def test_shipped_entries_validate():
    assert entry_mod.validate_file() == []


HAND_WRITTEN = ROOT / "data" / "rosetta" / "entries.jsonl"


def test_hand_written_entries_are_lint_clean():
    assert entry_mod.lint_file(HAND_WRITTEN) == []


def test_lint_advisories_on_imported_entries_are_advisory_only():
    """'greedy' fires on the epsilon-greedy entry. That is what advisory means."""
    findings = entry_mod.lint_file()
    assert entry_mod.validate_file() == [], "an advisory must never become an error"
    for f in findings:
        assert "ENTRY.LID_" in f, f


def test_entries_validate_against_the_json_schema():
    schema = json.loads((ROOT / "schema" / "rosetta_entry.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    raws = entry_mod.load_raw()
    assert raws
    for d in raws:
        assert list(validator.iter_errors(d)) == [], d.get("id")


def test_entry_requires_forcing_terms_that_resolve():
    bad = {
        "source_system": "x", "configuration": "y", "move_ported": "z",
        "forcing_terms": ["astrology"], "scope": {"produces": [], "stops": []},
    }
    assert any("resolves to no family" in e for e in entry_mod.validate_entry(bad))


def test_entry_must_report_where_it_stops():
    d = {
        "source_system": "x", "configuration": "y", "move_ported": "z",
        "forcing_terms": ["FLOW"], "scope": {"produces": ["here"]},
    }
    assert any("scope.stops missing" in e for e in entry_mod.validate_entry(d))


def test_entry_rejects_unknown_fields():
    d = {
        "source_system": "x", "configuration": "y", "move_ported": "z",
        "forcing_terms": ["FLOW"], "scope": {"produces": [], "stops": []},
        "conclusion": "defended",
    }
    assert any("unknown field: conclusion" in e for e in entry_mod.validate_entry(d))


def test_lint_flags_intent_attribution_and_moral_labels():
    d = {"configuration": "the crystal wants to reach the lowest energy",
         "move_ported": "a good move", "scope": {}}
    findings = entry_mod.lint_entry(d)
    assert any("intent attribution" in f for f in findings)
    assert any("moral label" in f for f in findings)


def test_entry_without_provenance_is_rejected():
    d = {
        "source_system": "x", "configuration": "y", "move_ported": "z",
        "forcing_terms": ["FLOW"], "scope": {"produces": ["a"], "stops": ["b"]},
    }
    assert any("provenance" in e for e in entry_mod.validate_entry(d))
    d["provenance"] = {"concept": "MINE", "record": "MODEL"}
    assert any("not one of" in e for e in entry_mod.validate_entry(d))


def test_shipped_entries_record_where_they_came_from():
    """The attribution is a regression guard: nothing drifts to AUTHOR."""
    got = {e.key: (e.provenance["concept"], e.provenance["record"])
           for e in entry_mod.load_entries(HAND_WRITTEN)}
    assert got == {
        "ENTRY.GRASS_RECONFIGURATION": (prov.AUTHOR, prov.MODEL),
        "ENTRY.HONEYCOMB_PARTITION": (prov.AUTHOR, prov.MODEL),
        "ENTRY.CRYSTAL_HABIT": (prov.AUTHOR, prov.MODEL),
        "ENTRY.MYCELIAL_ROUTING": (prov.SPEC, prov.MODEL),
        "ENTRY.TRABECULAR_ALIGNMENT": (prov.MODEL, prov.MODEL),
        "ENTRY.SOAP_FILM_SPAN": (prov.MODEL, prov.MODEL),
    }


def test_stops_may_be_strings_or_objects_and_normalise_the_same():
    bare = entry_mod.Entry.from_dict({"source_system": "x", "scope": {"stops": ["it stops"]}})
    assert bare.stop_records == [{"id": "stop_0", "says": "it stops"}]
    named = entry_mod.Entry.from_dict(
        {"source_system": "x", "scope": {"stops": [{"id": "here", "says": "it stops"}]}})
    assert named.stop_ids == ["here"]
    assert named.stops == bare.stops == ["it stops"]
    assert named.stop("here")["says"] == "it stops"
    assert named.stop("nope") is None


def test_duplicate_stop_ids_are_rejected():
    d = {
        "source_system": "x", "configuration": "y", "move_ported": "z",
        "forcing_terms": ["FLOW"], "forcing_dominant": ["FLOW"],
        "provenance": {"concept": "MODEL", "record": "MODEL"},
        "scope": {"produces": ["a"], "stops": [{"id": "dup", "says": "one"},
                                               {"id": "dup", "says": "two"}]},
    }
    assert any("duplicate stop id" in e for e in entry_mod.validate_entry(d))


def test_every_shipped_stop_has_an_explicit_id():
    for e in entry_mod.load_entries():
        assert e.stop_ids and not any(sid.startswith("stop_") for sid in e.stop_ids), e.key


def test_entry_key_derivation_and_uniqueness():
    assert entry_mod.Entry.from_dict({"source_system": "grass blade"}).key == "ENTRY.GRASS_BLADE"
    keys = [e.key for e in entry_mod.load_entries()]
    assert len(keys) == len(set(keys))


def test_gate_history_dict_is_normalised_to_a_list():
    e = entry_mod.Entry.from_dict({
        "source_system": "x",
        "gate_history": {"date": "2025-01-01", "model": "m", "register": "r"},
    })
    assert isinstance(e.gate_history, list) and len(e.gate_history) == 1


def test_bad_jsonl_line_reports_its_line_number(tmp_path):
    p = tmp_path / "entries.jsonl"
    p.write_text('{"source_system": "ok"}\nnot json\n', encoding="utf-8")
    with pytest.raises(ValueError) as exc:
        entry_mod.load_raw(p)
    assert ":2:" in str(exc.value)


# ── T4 scope ──────────────────────────────────────────────────────

def test_platonic_solids_satisfy_euler():
    for tok in ("TETRAHEDRON", "CUBE", "OCTAHEDRON", "DODECAHEDRON", "ICOSAHEDRON"):
        p = sc.SHAPE_PROPERTIES[tok]
        assert p["vertices"] - p["edges"] + p["faces"] == 2


def test_duals_are_mutual():
    for tok, p in sc.SHAPE_PROPERTIES.items():
        dual = p.get("dual")
        if dual:
            assert sc.SHAPE_PROPERTIES[dual]["dual"] == tok


def test_no_observations_is_not_adequate():
    assert sc.classify([]).status == sc.NO_DATA


def test_holding_everywhere_is_adequate_at_this_scope():
    v = sc.classify([sc.Observation("HEXAGON", "tiles_plane", True)])
    assert v.status == sc.ADEQUATE
    assert "untested outside" in v.reading


def test_failing_everywhere_grades_the_token_a_placeholder():
    v = sc.classify([sc.Observation("BLOB", "vertices", False), sc.Observation("BLOB", "edges", False)])
    assert v.status == sc.PLACEHOLDER
    assert "no structural claim" in v.reading


def test_failing_past_a_scale_measures_a_boundary():
    v = sc.classify([
        sc.Observation("OCTAHEDRON", "p", True, scale=1.0),
        sc.Observation("OCTAHEDRON", "p", True, scale=2.0),
        sc.Observation("OCTAHEDRON", "p", False, scale=5.0),
    ])
    assert (v.status, v.boundary_scale, v.direction) == (sc.BOUNDED, 5.0, "above")


def test_failing_below_a_scale_is_also_a_boundary():
    v = sc.classify([
        sc.Observation("X", "p", False, scale=0.1),
        sc.Observation("X", "p", True, scale=2.0),
    ])
    assert (v.status, v.boundary_scale, v.direction) == (sc.BOUNDED, 0.1, "below")


def test_interleaved_scales_are_indeterminate():
    v = sc.classify([
        sc.Observation("X", "p", True, scale=1.0),
        sc.Observation("X", "p", False, scale=2.0),
        sc.Observation("X", "p", True, scale=3.0),
    ])
    assert v.status == sc.INDETERMINATE


def test_condition_separable_observations_are_bounded_without_a_scale():
    v = sc.classify([
        sc.Observation("HEXAGON", "tiles", True, condition="flat region"),
        sc.Observation("HEXAGON", "tiles", False, condition="closed surface"),
    ])
    assert v.status == sc.BOUNDED and v.boundary_scale is None
    assert "closed surface" in v.failing_conditions


def test_shipped_observations_grade_both_carried_tokens():
    vs = sc.verdicts()
    assert vs["HEXAGON"].status == sc.BOUNDED
    assert vs["OCTAHEDRON"].status == sc.BOUNDED
    assert vs["OCTAHEDRON"].boundary_scale == 3.0


def test_repo_audit_criterion_every_entry_reports_a_stop():
    assert sc.audit_entries() == []


def test_audit_flags_an_entry_that_never_stops():
    e = entry_mod.Entry(source_system="x", configuration="y", scope={"produces": ["everywhere"], "stops": []})
    findings = sc.audit_entries([e])
    assert findings and "this is the flag" in findings[0]


def test_carried_tokens_have_formal_properties_to_predict_from():
    assert sc.audit_tokens() == []


# ── stops: asserted vs measured ───────────────────────────────────

def test_a_stop_nobody_carried_to_reads_asserted():
    st = sc.stop_status()
    hexagon = {r["id"]: r["status"] for r in st["ENTRY.HONEYCOMB_PARTITION"]}
    assert hexagon["cost_not_on_wall_length"] == sc.ASSERTED


def test_a_transfer_that_broke_at_a_stated_stop_measures_it():
    st = sc.stop_status()
    hexagon = {r["id"]: r for r in st["ENTRY.HONEYCOMB_PARTITION"]}
    assert hexagon["closed_surface"]["status"] == sc.MEASURED
    assert any("transfer" in ev for ev in hexagon["closed_surface"]["evidence"])


def test_an_observation_on_a_stop_measures_it():
    st = sc.stop_status()
    bone = {r["id"]: r for r in st["ENTRY.TRABECULAR_ALIGNMENT"]}
    assert bone["no_set_point_under_unloading"]["status"] == sc.MEASURED
    assert any("observation" in ev for ev in bone["no_set_point_under_unloading"]["evidence"])


def test_producing_past_a_stated_stop_contests_it():
    e = entry_mod.Entry(source_system="x", configuration="y", id="ENTRY.X",
                        scope={"produces": ["a"], "stops": [{"id": "s", "says": "it stops"}]})
    t = tr.Transfer(to_problem="p", outcome=tr.BROKE, from_entry="ENTRY.X",
                    produced_past="s", verdict_on=tr.ENTRY_SCOPE)
    st = sc.stop_status([e], [], [t])
    assert st["ENTRY.X"][0]["status"] == sc.CONTESTED
    assert sc.contested_stops(st)


def test_the_corpus_reports_its_own_measured_ratio_honestly():
    counts = sc.stop_tally()
    assert counts[sc.MEASURED] > 0, "no stop has been carried to — the criterion has no floor"
    assert counts[sc.ASSERTED] > counts[sc.MEASURED], "most stops are still claims; say so"
    assert counts[sc.CONTESTED] == 0


def test_an_observation_may_target_a_stop_instead_of_a_token():
    stop_obs = [o for o in sc.load_observations() if o.stop]
    assert stop_obs
    assert all(not o.shape_token for o in stop_obs)
    assert "" not in sc.by_token()


def test_properties_does_not_invent_a_shape():
    assert sc.properties("NOT_A_SHAPE") == {}


# ── T1 rosetta ────────────────────────────────────────────────────

def test_docstring_carries_the_not():
    doc = rop.__doc__
    assert "WHAT THE OPERATOR IS NOT" in doc
    for word in ("animacy", "sentience", "agency", "interior"):
        assert word in doc


def test_shared_forcing_licenses_transfer():
    ms = rop.run(rop.Problem(["flow", "strain"]))
    assert ms
    assert all(m.licensing == rop.SHARED_FORCING for m in ms)
    assert ms[0].entry_key == "ENTRY.GRASS_RECONFIGURATION"
    assert ms[0].shared_terms == ["FLOW", "STRAIN"]


def test_no_shared_term_is_shared_form_and_withheld_by_default():
    p = rop.Problem(["resonance"])
    assert rop.run(p) == []
    leads = rop.run(p, include_unlicensed=True)
    assert leads and all(m.licensing == rop.SHARED_FORM for m in leads)
    assert "coincidence until a mechanism appears" in leads[0].reading.lower()


def test_matches_are_sorted_by_shared_forcing_count():
    ms = rop.run(rop.Problem(["gravity", "strain", "pressure"]))
    counts = [len(m.shared_terms) for m in ms]
    assert counts == sorted(counts, reverse=True)


def test_a_match_carries_the_stops_with_the_move():
    ms = rop.run(rop.Problem(["strain", "pressure"]))
    honeycomb = next(m for m in ms if m.entry_key == "ENTRY.HONEYCOMB_PARTITION")
    assert honeycomb.move_ported.startswith("when partitioning a plane")
    assert any("Euler" in s for s in honeycomb.stops)
    assert honeycomb.token_status == sc.BOUNDED


def test_licensing_never_claimed_without_a_shared_term():
    for fid in fam.FAMILIES:
        for m in rop.run(rop.Problem([fid], dominant_terms=[fid]), include_unlicensed=True):
            assert (m.licensing == rop.SHARED_FORM) == (not m.shared_terms)
            if m.licensing == rop.SHARED_DOMINANT:
                assert m.shared_dominant


# ── dominance: the fix for a criterion that licensed almost everything ──

def test_presence_alone_cannot_reach_the_top_grade():
    """No dominant term named on the problem side — nothing can grade DOMINANT."""
    for m in rop.run(rop.Problem(["strain"]), include_weak=True, include_unlicensed=True):
        assert m.licensing != rop.SHARED_DOMINANT


def test_a_term_that_shapes_neither_side_grades_weak_and_is_withheld():
    weak = rop.run(rop.Problem(["strain"]), include_weak=True)
    graded_weak = [m for m in weak if m.licensing == rop.SHARED_PRESENT]
    assert graded_weak, "strain sets neither the bare problem nor grass — expected SHARED_PRESENT"
    assert not [m for m in rop.run(rop.Problem(["strain"])) if m.licensing == rop.SHARED_PRESENT]


def test_dominance_selects_exactly_the_entries_the_term_shapes():
    entries = entry_mod.load_entries()
    top = {m.entry_key for m in rop.run(rop.Problem(["strain"], dominant_terms=["strain"]), entries)
           if m.licensing == rop.SHARED_DOMINANT}
    assert top == {e.key for e in entries if "STRAIN" in e.dominant}
    assert "ENTRY.GRASS_RECONFIGURATION" not in top


def test_one_sided_dominance_is_licensed_but_not_top_grade():
    """Strain sets the problem and not grass: shared, one-sided, still worth porting."""
    ms = rop.run(rop.Problem(["strain"], dominant_terms=["strain"]))
    grass = next(m for m in ms if m.entry_key == "ENTRY.GRASS_RECONFIGURATION")
    assert grass.licensing == rop.SHARED_FORCING
    assert grass.shared_dominant == []


def test_matches_sort_strongest_grade_first():
    ms = rop.run(rop.Problem(["flow", "strain"], dominant_terms=["flow"]),
                 include_weak=True, include_unlicensed=True)
    grades = [rop.GRADES.index(m.licensing) for m in ms]
    assert grades == sorted(grades)


def test_problem_dominant_must_be_among_its_own_forcing_terms():
    assert rop.Problem(["flow"], dominant_terms=["strain"]).dominant == []


def test_entry_requires_a_dominant_term_inside_its_forcing_set():
    base = {
        "source_system": "x", "configuration": "y", "move_ported": "z",
        "forcing_terms": ["FLOW"], "scope": {"produces": ["a"], "stops": ["b"]},
        "provenance": {"concept": "MODEL", "record": "MODEL"},
    }
    assert any("forcing_dominant" in e for e in entry_mod.validate_entry(base))
    assert any("forcing_dominant is empty" in e
               for e in entry_mod.validate_entry({**base, "forcing_dominant": []}))
    assert any("not in forcing_terms" in e
               for e in entry_mod.validate_entry({**base, "forcing_dominant": ["STRAIN"]}))
    assert entry_mod.validate_entry({**base, "forcing_dominant": ["FLOW"]}) == []


def test_every_transferable_entry_names_what_sets_its_configuration():
    for e in entry_mod.load_entries():
        if not e.transferable:
            continue
        assert e.dominant, e.key
        assert set(e.dominant) <= set(e.families), e.key


def test_an_entry_with_open_forcing_cannot_license_anything():
    waiting = rop.open_entries()
    assert waiting, "the imported corpus should be waiting on someone to name its loads"
    for e in waiting:
        assert e.status_of("forcing_terms") in entry_mod.EXCUSES_EMPTY, e.key


def test_unresolved_problem_terms_are_reported_not_silently_dropped():
    p = rop.Problem(["flow", "astrology"])
    assert p.families == ["FLOW"]
    assert p.unresolved == ["astrology"]


def test_by_source_is_the_what_would_x_do_here_lookup():
    assert "ENTRY.GRASS_RECONFIGURATION" in [e.key for e in rop.by_source("grass")]
    assert [e.key for e in rop.by_source("gecko")] == [
        "ENTRY.LID_GECKO_SETAE_ADHESION",
        "ENTRY.LID_GECKO_SELF_CLEANING_LOCOMOTION",
        "ENTRY.LID_GECKO_DIRECTIONAL_GRIP",
    ]
    assert rop.by_source("telephone") == []


# ── T5 gate log ───────────────────────────────────────────────────

def test_gate_log_ships_empty_and_valid():
    assert gl.validate_file() == []
    assert gl.load_records() == []


def test_gate_record_requires_a_date_a_model_and_a_register():
    for missing in ("date", "model", "register", "key"):
        d = {"date": "2025-01-01", "key": "k", "model": "m", "register": "r"}
        d.pop(missing)
        assert any(missing in e for e in gl.validate_record(d))


def test_gate_record_date_must_be_iso():
    assert any("ISO date" in e for e in gl.validate_record(
        {"date": "01/01/2025", "key": "k", "model": "m", "register": "r"}))


def test_gate_records_validate_against_the_json_schema():
    schema = json.loads((ROOT / "schema" / "gate_log.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    rec = gl.GateRecord("2025-01-01", "a-slug", "some-model", "the register", refused=["the other register"])
    assert list(validator.iter_errors(rec.to_dict())) == []
    for d in gl.load_raw():
        assert list(validator.iter_errors(d)) == []


def test_append_record_round_trips(tmp_path):
    p = tmp_path / "gate_log.jsonl"
    rec = gl.GateRecord("2025-03-04", "a-term", "a-model", "the register it unlocked",
                        refused=["the register it would not hold"], slug="ENTRY.HONEYCOMB_PARTITION")
    gl.append_record(rec, p)
    back = gl.load_records(p)
    assert len(back) == 1 and back[0].to_dict() == rec.to_dict()
    assert gl.validate_file(p) == []


def test_append_record_refuses_an_invalid_record(tmp_path):
    with pytest.raises(ValueError):
        gl.append_record(gl.GateRecord("nope", "k", "m", "r"), tmp_path / "g.jsonl")


def test_renaming_a_slug_orphans_its_gate_record():
    orphan = gl.GateRecord("2025-01-01", "k", "m", "r", slug="ENTRY.RENAMED_AWAY")
    findings = gl.check_slugs([orphan])
    assert findings and "orphaned" in findings[0]
    assert gl.check_slugs([gl.GateRecord("2025-01-01", "k", "m", "r", slug="ENTRY.HONEYCOMB_PARTITION")]) == []


def test_entry_gate_history_is_harvested_into_the_log():
    e = entry_mod.Entry(
        source_system="x", configuration="y",
        id="ENTRY.X",
        gate_history=[{"date": "2024-02-02", "model": "m", "register": "the register", "key": "a-glyph"}],
    )
    recs = gl.from_entries([e])
    assert len(recs) == 1
    assert (recs[0].model, recs[0].key, recs[0].entry) == ("m", "a-glyph", "ENTRY.X")
    assert gl.validate_record(recs[0].to_dict()) == []


def test_summary_reports_the_window_and_the_refusals():
    recs = [
        gl.GateRecord("2024-06-01", "a", "model-one", "register-one", refused=["r"]),
        gl.GateRecord("2025-01-01", "b", "model-two", "register-two", refused=["r"]),
    ]
    s = gl.summary(recs)
    assert s["records"] == 2
    assert (s["first"], s["last"]) == ("2024-06-01", "2025-01-01")
    assert s["refusals"] == {"r": 2}
    assert s["models"] == ["model-one", "model-two"]


# ── gap_scan ──────────────────────────────────────────────────────

def test_shipped_instances_are_closed_and_valid():
    paths = gs.list_instances()
    assert paths
    for p in paths:
        d = json.loads(p.read_text(encoding="utf-8"))
        assert gs.validate_instance(d) == []
        assert d.get("closed") is True


@pytest.mark.parametrize("name", ["clockwork", "telegraph_brain"])
def test_closed_instances_fire_every_shape_class(name):
    report = gs.scan_instance(name)
    assert report.fired == ["G1", "G2", "G3", "G4"]


def test_clockwork_reports_the_expected_shape():
    r = gs.scan_instance("clockwork")
    g = {x.id: x for x in r.gaps}
    assert "field" in g["G1"].items
    assert any("absolute time" in i for i in g["G2"].items)
    assert g["G4"].items == ["the setter who wound it"]
    assert r.provenance["orbital period"] == gs.MEASURED
    assert r.provenance["initial setting"] == gs.UNTRACED


def test_g1_reports_only_terms_the_criterion_cannot_register():
    g = gs.g1_missing_slot(
        gs.Frame("c", requires=["a", "b"]),
        gs.Criterion("crit", registers=["a"]),
        probes=["c", "a"],
    )
    assert g.fired and g.items == ["b", "c"]


def test_g2_reports_apparatus_and_untraced_operands_only():
    g = gs.g2_imported_boundary([
        gs.Operand("m", gs.MEASURED), gs.Operand("k", gs.APPARATUS), gs.Operand("u", gs.UNTRACED)])
    assert g.fired and len(g.items) == 2
    assert not gs.g2_imported_boundary([gs.Operand("m", gs.MEASURED)]).fired


def test_g3_fires_only_when_the_world_is_inside_the_machine():
    art = gs.Artifact("machine", ["x", "y", "z"])
    assert gs.g3_substrate_ceiling(gs.Frame("c", world_capabilities=["x", "y"]), art).fired
    assert not gs.g3_substrate_ceiling(gs.Frame("c", world_capabilities=["x", "beyond"]), art).fired
    assert not gs.g3_substrate_ceiling(gs.Frame("c"), art).fired


def test_g4_fires_only_on_an_exterior_that_cannot_be_located():
    crit = gs.Criterion("crit", registers=["a"])
    assert gs.g4_exterior(gs.Frame("c", exterior="the setter", exterior_required=True), crit, []).fired
    assert not gs.g4_exterior(gs.Frame("c", exterior="a", exterior_required=True), crit, []).fired
    assert not gs.g4_exterior(
        gs.Frame("c", exterior="m", exterior_required=True), crit, [gs.Operand("m", gs.MEASURED)]).fired
    assert not gs.g4_exterior(gs.Frame("c"), crit, []).fired


def test_scan_derives_nothing_it_was_not_given():
    r = gs.scan(gs.Frame("c", requires=["a"]), gs.Artifact("m", ["x"]),
                gs.Criterion("crit", registers=["a"]), [gs.Operand("o", gs.MEASURED)])
    assert r.fired == []


def test_instance_without_an_identifiable_artifact_is_rejected():
    errors = gs.validate_instance({"frame": {"claim": "c"}, "artifact": {}, "criterion": {}})
    assert any("dominant artifact" in e for e in errors)


def test_unknown_provenance_is_rejected():
    errors = gs.validate_instance({
        "frame": {"claim": "c"}, "artifact": {"name": "a"}, "criterion": {},
        "operands": [{"name": "o", "provenance": "GUESSED"}]})
    assert any("provenance" in e for e in errors)


def test_instance_without_provenance_is_rejected():
    errors = gs.validate_instance({"frame": {"claim": "c"}, "artifact": {"name": "a"}, "criterion": {}})
    assert any("provenance" in e for e in errors)


def test_shipped_instances_are_marked_spec_derived():
    for name in ("clockwork", "telegraph_brain"):
        r = gs.scan_instance(name)
        assert r.record_provenance["concept"] == prov.SPEC
        assert r.record_provenance["record"] == prov.MODEL


def test_gap_scan_states_which_axis_it_is_on():
    doc = gs.__doc__
    assert "cross-INSTANCE" in doc
    assert "not Rosetta's" in doc


def test_missing_instance_reports_cleanly():
    assert gs.main(["--example", "no_such_instance"]) == 1


# ── CLI smoke ─────────────────────────────────────────────────────

@pytest.mark.parametrize("argv,module", [
    (["--list"], fam), (["--audit"], fam), (["--term", "gravity"], fam),
    (["--validate"], entry_mod), (["--lint"], entry_mod), (["--list"], entry_mod),
    (["--audit"], sc), (["--all"], sc), (["--shape", "HEXAGON"], sc),
    (["--classify", "HEXAGON"], sc),
    (["--forcing", "flow"], rop), (["--source", "grass"], rop),
    (["--list"], gl), (["--summary"], gl), (["--validate"], gl), (["--check-slugs"], gl),
    (["--list"], gs), (["--example", "clockwork"], gs),
])
def test_cli_paths_exit_zero(argv, module, capsys):
    assert module.main(argv) == 0
    assert capsys.readouterr().out


@pytest.mark.parametrize("argv,module", [
    (["--list"], fam), (["--validate"], entry_mod), (["--all"], sc),
    (["--forcing", "flow"], rop), (["--list"], gl), (["--example", "clockwork"], gs),
])
def test_json_output_parses(argv, module, capsys):
    module.main(argv + ["--json"])
    json.loads(capsys.readouterr().out)


# ── provenance ────────────────────────────────────────────────────

def test_every_shipped_record_is_marked():
    assert prov.audit() == []


def test_provenance_audit_covers_every_artifact_set():
    s = prov.summary()
    assert set(s) == {"entries", "families", "observations", "transfers", "holdings",
                      "shape reads", "gap_scan instances"}
    APPEND_ONLY_AND_EMPTY = {"holdings"}  # a contact is a recorded event; none logged yet
    for name, block in s.items():
        if name in APPEND_ONLY_AND_EMPTY:
            continue
        assert block["count"] > 0, name


def test_provenance_requires_both_halves_from_the_vocabulary():
    assert prov.validate({"concept": prov.AUTHOR, "record": prov.MODEL}) == []
    assert prov.validate(None)
    assert prov.validate({"concept": prov.AUTHOR})
    assert prov.validate({"concept": "MINE", "record": prov.MODEL})
    assert prov.validate({"concept": prov.AUTHOR, "record": prov.MODEL, "vibe": "x"})


def test_make_refuses_to_emit_an_unmarkable_block():
    with pytest.raises(ValueError):
        prov.make("NOPE")
    assert prov.make(prov.SPEC, prov.MODEL, note="n") == {
        "concept": prov.SPEC, "record": prov.MODEL, "note": "n"}


def test_tally_counts_unmarked_records_rather_than_dropping_them():
    t = prov.tally([{"concept": prov.AUTHOR, "record": prov.MODEL}, None])
    assert t["concept"] == {prov.AUTHOR: 1, "(unmarked)": 1}


def test_hand_written_observations_are_marked_public_concept_model_record():
    for o in sc.load_observations(ROOT / "data" / "rosetta" / "observations.jsonl"):
        assert o.provenance["concept"] == prov.PUBLIC
        assert o.provenance["record"] == prov.MODEL


def test_entry_schema_requires_provenance():
    schema = json.loads((ROOT / "schema" / "rosetta_entry.schema.json").read_text(encoding="utf-8"))
    assert "provenance" in schema["required"]
    enum = schema["properties"]["provenance"]["properties"]["concept"]["enum"]
    assert set(enum) == set(prov.ORIGINS)


# ── license ───────────────────────────────────────────────────────

def test_repo_license_is_cc0():
    text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "CC0 1.0 Universal" in text
    assert 'license = {text = "CC0-1.0"}' in (ROOT / "pyproject.toml").read_text(encoding="utf-8")


@pytest.mark.parametrize("module", MODULES, ids=lambda m: m.__name__.rsplit(".", 1)[-1])
def test_modules_carry_the_spdx_line(module):
    first = pathlib.Path(module.__file__).read_text(encoding="utf-8").splitlines()[0]
    assert first == "# SPDX-License-Identifier: CC0-1.0"


# ── docs ──────────────────────────────────────────────────────────

def test_the_three_specs_are_at_root_and_read_in_order():
    """METHOD_SPEC -> SHAPE_SPEC -> READING_PROTOCOL. Section 6 sets the order."""
    method = (ROOT / "METHOD_SPEC.md").read_text(encoding="utf-8")
    shape = (ROOT / "SHAPE_SPEC.md").read_text(encoding="utf-8")
    protocol = (ROOT / "READING_PROTOCOL.md").read_text(encoding="utf-8")
    assert "A METHOD IS NOT FALSIFIABLE" in method
    assert "SHAPE  =  the constraint set a geometry is a solution to" in shape
    for link in ("METHOD_SPEC.md", "SHAPE_SPEC.md"):
        assert link in protocol, link
    assert not (ROOT / "docs" / "reading-protocol.md").exists()
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for link in ("METHOD_SPEC.md", "SHAPE_SPEC.md", "READING_PROTOCOL.md"):
        assert link in readme, link


def test_reading_protocol_carries_marker_status_and_blocked_conflations():
    text = (ROOT / "READING_PROTOCOL.md").read_text(encoding="utf-8")
    for signature in ("context ceiling", "gate / register", "accepted"):
        assert signature in text
    assert "MARKER STATUS" in text
    assert "BLOCKED CONFLATIONS" in text


def test_the_third_blocked_conflation_is_the_shadow_read():
    """METHOD_SPEC section 4 cites it by number."""
    text = (ROOT / "READING_PROTOCOL.md").read_text(encoding="utf-8")
    third = text.split("### 3. ")[1].split("### 4.")[0]
    assert "tangents" in third.lower()
    assert "not competing claims" in third
    assert "METHOD_SPEC.md §4" in third or "METHOD_SPEC.md" in third


# ── transfers: what happened when a move was carried over ─────────

def test_shipped_transfers_validate():
    assert tr.validate_file() == []


def test_transfers_validate_against_the_json_schema():
    schema = json.loads((ROOT / "schema" / "transfer.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    raws = tr.load_raw()
    assert raws
    for d in raws:
        assert list(validator.iter_errors(d)) == [], d.get("id")


def test_a_transfer_that_did_not_hold_must_say_where():
    d = {"from_source": "x", "to_problem": "p", "outcome": tr.BROKE,
         "verdict_on": tr.ENTRY_SCOPE, "provenance": {"concept": "MODEL", "record": "MODEL"}}
    assert any("broke_at" in e for e in tr.validate_transfer(d))


def test_a_transfer_that_did_not_hold_must_indict_something():
    d = {"from_source": "x", "to_problem": "p", "outcome": tr.PARTIAL, "broke_at": "here",
         "verdict_on": tr.NONE, "provenance": {"concept": "MODEL", "record": "MODEL"}}
    assert any("cannot be NONE" in e for e in tr.validate_transfer(d))


def test_a_move_can_hold_while_the_source_reading_is_revised():
    """The two are independent — that is 'port the move, not the ontology' as data."""
    d = {"from_source": "termite mound", "to_problem": "p", "outcome": tr.HELD,
         "verdict_on": tr.SOURCE_READING, "provenance": {"concept": "PUBLIC", "record": "MODEL"}}
    assert tr.validate_transfer(d) == []
    assert any("not one of" in e or "admits" in e
               for e in tr.validate_transfer({**d, "verdict_on": tr.LICENSING}))


def test_a_transfer_must_come_from_somewhere():
    d = {"to_problem": "p", "outcome": tr.HELD, "verdict_on": tr.NONE,
         "provenance": {"concept": "MODEL", "record": "MODEL"}}
    assert any("from_source" in e for e in tr.validate_transfer(d))


def test_stop_references_must_resolve_against_the_entry():
    d = {"from_entry": "ENTRY.HONEYCOMB_PARTITION", "to_problem": "p", "outcome": tr.BROKE,
         "broke_at": "x", "confirms_stop": "not_a_stop", "verdict_on": tr.SCOPE_CONFIRMED,
         "provenance": {"concept": "MODEL", "record": "MODEL"}}
    assert any("is not a stop of" in e for e in tr.validate_transfer(d))


def test_scope_confirmed_requires_the_stop_it_confirms():
    d = {"from_entry": "ENTRY.HONEYCOMB_PARTITION", "to_problem": "p", "outcome": tr.BROKE,
         "broke_at": "x", "verdict_on": tr.SCOPE_CONFIRMED,
         "provenance": {"concept": "MODEL", "record": "MODEL"}}
    assert any("confirms_stop" in e for e in tr.validate_transfer(d))


def test_an_unrecorded_source_is_reported_as_a_missing_entry():
    missing = tr.unrecorded_sources()
    assert missing
    findings = tr.audit()
    assert any("pointer to a missing entry" in f for f in findings)


def test_a_break_the_entry_did_not_state_is_a_finding_against_the_entry():
    e = entry_mod.Entry(source_system="x", configuration="y", id="ENTRY.X",
                        scope={"produces": ["a"], "stops": [{"id": "s", "says": "it stops"}]})
    t = tr.Transfer(to_problem="p", outcome=tr.BROKE, from_entry="ENTRY.X",
                    broke_at="somewhere else", verdict_on=tr.ENTRY_SCOPE)
    assert any("understates its scope" in f for f in tr.audit([t], [e]))


def test_criterion_report_does_not_claim_a_clean_bill_without_evidence():
    r = tr.criterion_report()
    assert r["transfers"] == len(tr.load_transfers())
    assert r["graded_at_the_time"] <= r["transfers"]
    assert r["against_the_criterion"] == r["verdicts"].get(tr.LICENSING, 0)


def test_transfer_grade_vocabulary_matches_the_operator():
    """transfer.py holds GRADES locally to keep the module graph acyclic."""
    assert tr.GRADES == rop.GRADES


# ── the worked example ────────────────────────────────────────────

def test_walkthrough_runs_and_teaches_the_two_steps_people_skip(capsys):
    import importlib.util
    path = ROOT / "examples" / "rosetta_walkthrough.py"
    spec = importlib.util.spec_from_file_location("rosetta_walkthrough", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.main() == 0
    out = capsys.readouterr().out
    assert "SHARED_DOMINANT" in out and "SHARED_PRESENT" in out
    assert "ENTRY.GRASS_RECONFIGURATION" in out
    assert "ASSERTED" in out
    for wrong in ("WRONG READING A", "WRONG READING B", "WRONG READING C"):
        assert wrong in out
    assert "RIGHT READING" in out


def test_walkthrough_is_not_hardcoded():
    """Every claim in it is computed, so it cannot teach a stale entry set."""
    src = (ROOT / "examples" / "rosetta_walkthrough.py").read_text(encoding="utf-8")
    for call in ("load_entries()", "run(", "resolve_family(", "stop_status("):
        assert call in src


# ── field status: a hole is not a guess ───────────────────────────

BASE = {
    "source_system": "x", "configuration": "y", "move_ported": "z",
    "forcing_terms": ["FLOW"], "forcing_dominant": ["FLOW"],
    "scope": {"produces": ["a"], "stops": ["b"]},
    "provenance": {"concept": "MODEL", "record": "MODEL"},
}


def test_a_required_field_may_be_empty_when_it_is_marked():
    d = {k: v for k, v in BASE.items() if k not in ("forcing_terms", "forcing_dominant", "move_ported")}
    d["field_status"] = {"forcing_terms": entry_mod.OPEN, "forcing_dominant": entry_mod.OPEN,
                         "move_ported": entry_mod.OPEN}
    assert entry_mod.validate_entry(d) == []
    d2 = {k: v for k, v in BASE.items() if k != "move_ported"}
    assert any("missing required field: move_ported" in e for e in entry_mod.validate_entry(d2))


def test_marking_is_not_a_way_to_silence_a_check():
    """OPEN on a filled field and PARTIAL on an empty one are both errors."""
    assert any("is filled" in e for e in entry_mod.validate_entry(
        {**BASE, "field_status": {"move_ported": entry_mod.OPEN}}))
    empty = {**BASE, "move_ported": "", "field_status": {"move_ported": entry_mod.PARTIAL}}
    assert any("is empty" in e for e in entry_mod.validate_entry(empty))


def test_due_for_update_requires_something_to_update():
    assert entry_mod.validate_entry(
        {**BASE, "field_status": {"configuration": entry_mod.DUE_FOR_UPDATE}}) == []
    stale = {**BASE, "configuration": "", "field_status": {"configuration": entry_mod.DUE_FOR_UPDATE}}
    assert any("is empty" in e for e in entry_mod.validate_entry(stale))


def test_field_status_only_names_real_fields_and_real_statuses():
    assert any("not a field of an entry" in e for e in entry_mod.validate_entry(
        {**BASE, "field_status": {"vibes": entry_mod.OPEN}}))
    assert any("not one of" in e for e in entry_mod.validate_entry(
        {**BASE, "field_status": {"note": "MAYBE"}}))


def test_an_open_scope_half_is_a_statement_not_a_silence():
    e = entry_mod.Entry.from_dict({**BASE, "scope": {"produces": ["a"], "stops": []},
                                   "field_status": {"scope.stops": entry_mod.OPEN}})
    assert sc.audit_entries([e]) == []
    unmarked = entry_mod.Entry.from_dict({**BASE, "scope": {"produces": ["a"], "stops": []}})
    assert sc.audit_entries([unmarked])


# ── cited vs measured ─────────────────────────────────────────────

def test_a_cited_stop_is_evidence_about_the_source_not_about_a_transfer():
    e = entry_mod.Entry.from_dict({**BASE, "id": "ENTRY.C", "scope": {
        "produces": ["a"],
        "stops": [{"id": "s", "says": "it stops", "cited": "Someone (2000)"}]}})
    rows = sc.stop_status([e], [], [])
    assert rows["ENTRY.C"][0]["status"] == sc.CITED
    assert any("cited:" in ev for ev in rows["ENTRY.C"][0]["evidence"])


def test_carrying_a_move_to_a_cited_stop_promotes_it_to_measured():
    e = entry_mod.Entry.from_dict({**BASE, "id": "ENTRY.C", "scope": {
        "produces": ["a"],
        "stops": [{"id": "s", "says": "it stops", "cited": "Someone (2000)"}]}})
    t = tr.Transfer(to_problem="p", outcome=tr.BROKE, from_entry="ENTRY.C",
                    broke_at="there", confirms_stop="s", verdict_on=tr.SCOPE_CONFIRMED)
    assert sc.stop_status([e], [], [t])["ENTRY.C"][0]["status"] == sc.MEASURED


def test_most_stops_are_cited_and_almost_none_are_measured():
    """The true state of the corpus, and the report must not flatter it."""
    counts = sc.stop_tally()
    assert counts[sc.CITED] > counts[sc.MEASURED] * 10
    assert counts[sc.MEASURED] > 0


def test_a_stated_test_is_not_a_failed_one():
    assert sc.classify([sc.Observation("X", "p", None)]).status == sc.NO_DATA
    assert sc.classify([sc.Observation("X", "p", True), sc.Observation("X", "p", None)]).status == sc.ADEQUATE
    assert len(sc.pending_tests()) >= 225


# ── the LID import ────────────────────────────────────────────────

def test_importer_never_fills_a_field_it_has_no_source_for():
    for e in entry_mod.load_entries(ROOT / "data" / "rosetta" / "entries.lid.jsonl"):
        assert not e.forcing_terms and not e.forcing_dominant and not e.move_ported, e.key
        for f in ("forcing_terms", "forcing_dominant", "move_ported"):
            assert e.status_of(f) == entry_mod.OPEN, e.key


def test_imported_records_are_marked_as_the_authors():
    entries = entry_mod.load_entries(ROOT / "data" / "rosetta" / "entries.lid.jsonl")
    assert len(entries) > 200
    for e in entries:
        assert e.provenance["concept"] == prov.AUTHOR
        assert e.provenance["record"] == prov.AUTHOR
        assert "Living-Intelligence-Database" in e.provenance["note"]


def test_imported_entries_validate_and_carry_citations():
    path = ROOT / "data" / "rosetta" / "entries.lid.jsonl"
    assert entry_mod.validate_file(path) == []
    cited = [e for e in entry_mod.load_entries(path)
             if any(r.get("cited") for r in e.stop_records)]
    assert len(cited) > 200


def test_the_falsifier_arrives_as_an_unrun_test_not_as_evidence():
    obs = sc.load_observations(ROOT / "data" / "rosetta" / "observations.lid.jsonl")
    assert len(obs) > 200
    for o in obs:
        assert o.holds is None, o.entry
        assert o.entry and not o.shape_token


def test_import_is_idempotent_and_keeps_hand_filled_fields(tmp_path, monkeypatch):
    being = {"id": "XX", "name": "Testbeing"}
    attr = {"scope": {"definition": "d", "measurement_limits": "One limit.",
                      "falsifiability": "If X then fail.",
                      "evidence": {"source": "S (1999)"}}}
    rel = pathlib.Path("ontology/animal/testbeing.json")
    first = lid.build_entry(rel, being, "an_attribute", attr)
    second = lid.build_entry(rel, being, "an_attribute", attr)
    assert first == second, "the same input must produce the same record"
    assert first["id"] == "ENTRY.LID_TESTBEING_AN_ATTRIBUTE"


def test_gecko_transfer_now_measures_a_stop_the_database_already_had():
    """The loop: transfer audit named a missing entry, the database had it."""
    rows = {r["id"]: r for r in sc.stop_status()["ENTRY.LID_GECKO_SETAE_ADHESION"]}
    assert rows["limit_2"]["status"] == sc.MEASURED
    assert any("transfer" in ev for ev in rows["limit_2"]["evidence"])
    assert rows["limit_1"]["status"] == sc.CITED


# ── tier separation: domains of the world vs ways of knowing ──────

def test_families_are_f01_to_f20():
    ids = sorted(p.stem.split("-")[0] for p in tier.family_files())
    assert ids == [f"f{i:02d}" for i in range(1, 21)]
    assert not (ROOT / "ontology" / "families" / "f21-narrative-constraint.json").exists()


def test_the_access_tier_has_a01_and_no_implied_closure():
    """No face assignment, no count, no polytope closure on the access tier."""
    names = [p.name for p in tier.access_files()]
    assert "a01-narrative-constraint.json" in names
    schema = json.loads((ROOT / "schema" / "access.schema.json").read_text(encoding="utf-8"))
    for structural in ("face_assignment", "face", "faces", "count", "dual", "incidence",
                       "vertices", "edges"):
        assert structural not in schema["properties"], structural
    description = schema["description"].lower()
    for stated in ("no face_assignment", "no fixed count", "no polytope closure"):
        assert stated in description, stated


def test_a01_validates_against_the_access_schema():
    schema = json.loads((ROOT / "schema" / "access.schema.json").read_text(encoding="utf-8"))
    record = json.loads((ROOT / "ontology" / "access" / "a01-narrative-constraint.json")
                        .read_text(encoding="utf-8"))
    assert list(Draft202012Validator(schema).iter_errors(record)) == []
    assert record["derived_from"] == "FAMILY.F21", "the old slug must still resolve"


def test_breaks_when_is_mandatory_and_may_not_be_null():
    schema = json.loads((ROOT / "schema" / "access.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    record = json.loads((ROOT / "ontology" / "access" / "a01-narrative-constraint.json")
                        .read_text(encoding="utf-8"))
    assert "breaks_when" in schema["required"]
    for bad in (None, "", "   "):
        broken = {**record, "breaks_when": bad}
        assert list(validator.iter_errors(broken)) or tier.check_access_states_a_break


def test_a_way_of_knowing_in_families_fails():
    f21_as_filed = {
        "id": "FAMILY.F21", "name": "Narrative-Constraint",
        "domain": "Constraint consistency, selective application detection, symmetry of rules",
        "tags": ["manipulation-detection", "narrative-physics"],
    }
    assert tier.marks_way_of_knowing(f21_as_filed)


@pytest.mark.parametrize("record", [
    {"id": "FAMILY.F14", "name": "Measurement",
     "domain": "Uncertainty quantification, calibration, error propagation, dimensional analysis"},
    {"id": "FAMILY.F03", "name": "Information",
     "domain": "Shannon entropy, coding theory, information measures, channel capacity"},
    {"id": "FAMILY.F16", "name": "Consciousness",
     "domain": "Integrated information, global workspace, neural oscillations, predictive coding"},
])
def test_domains_of_the_world_do_not_trip_the_detector(record):
    """Measurement and information are domains OF the world, not accounts of it."""
    assert tier.marks_way_of_knowing(record) == []


def test_shipped_families_and_access_entries_pass():
    assert tier.check_families_are_domains() == []
    assert tier.check_access_states_a_break() == []
    assert tier.run()["fail"] == []


def test_the_free_measured_mismatch_is_the_detector():
    warned = tier.check_cost_lands_on_mismatch()
    assert warned and "a01" in warned[0]
    assert "cheap travel to an expensive destination" in warned[0]


def test_candidates_are_not_members_of_the_tier():
    """a02-a06 have no break point, so they are not access entries yet."""
    path = ROOT / "ontology" / "access" / "_candidates.json"
    assert path.exists()
    assert path not in tier.access_files()
    doc = json.loads(path.read_text(encoding="utf-8"))
    ids = [c["id"] for c in doc["candidates"]]
    assert ids == ["a02", "a04", "a05", "a06"], "a03 has a break point now and became a member"
    for c in doc["candidates"]:
        assert c["breaks_when"] is None


def test_f21_is_gone_from_the_family_map_and_the_icosahedron_closes_at_20():
    fm = json.loads((ROOT / "ontology" / "family_map.json").read_text(encoding="utf-8"))
    assert "FAMILY.F21" not in json.dumps(fm)
    assert len(fm["family_affinity_model"]["families"]) == 20
    assert len(fm["shape_profiles"]["SHAPE.ICOSA"]["all_equation_families"]) == 20


def test_the_index_and_the_registry_agree_with_the_files():
    index = json.loads((ROOT / "ontology" / "index.json").read_text(encoding="utf-8"))
    assert index["families"]["count"] == 20
    assert len(index["families"]["registry"]) == 20
    access = index["access"]
    assert access["members_present"] == len(tier.access_files())
    assert "open" in access["closure"].lower()
    registry = json.loads((ROOT / "ontology" / "_id_registry.json").read_text(encoding="utf-8"))
    assert "ACCESS" in registry["registry"]
    assert registry["registry"]["ACCESS"]["path"] == "ontology/access/"


# ── the holding record ────────────────────────────────────────────

def test_absent_acquired_reads_as_unmarked_not_as_missing():
    e = entry_mod.Entry(source_system="x", configuration="y")
    assert e.acquired == ""
    assert e.acquisition == entry_mod.UNMARKED


def test_holding_record_validates_and_rejects_a_domain_that_is_not_one():
    base = dict(BASE)
    assert entry_mod.validate_entry({**base, "domain": "f05", "access": "a01",
                                     "acquired": "residual"}) == []
    assert any("f01..f20" in e for e in entry_mod.validate_entry({**base, "domain": "f21"}))
    assert any("access" in e for e in entry_mod.validate_entry({**base, "access": "a1"}))
    assert any("unmarked" in e for e in entry_mod.validate_entry({**base, "acquired": "probably"}))


def test_nothing_was_backfilled_with_a_guess():
    """unmarked is expected to dominate; no entry claims an acquisition nobody recorded."""
    entries = entry_mod.load_entries()
    assert all(e.acquisition == entry_mod.UNMARKED for e in entries)
    assert not any(e.domain or e.access for e in entries)


def test_claiming_a_domain_without_an_access_is_reported():
    claimed = entry_mod.Entry(source_system="x", configuration="y", id="ENTRY.X", domain="f05")
    assert tier.check_domain_claims_name_an_access([claimed])
    both = entry_mod.Entry(source_system="x", configuration="y", id="ENTRY.X",
                           domain="f05", access="a01")
    assert tier.check_domain_claims_name_an_access([both]) == []


# ── the discriminator: cost cannot tell a01 from a03 ──────────────

ACCESS_SCHEMA = json.loads((ROOT / "schema" / "access.schema.json").read_text(encoding="utf-8"))


def _access(aid):
    for p in tier.access_files():
        d = json.loads(p.read_text(encoding="utf-8"))
        if d["id"] == aid:
            return d
    raise AssertionError(f"no access entry {aid}")


def test_a01_and_a03_are_indistinguishable_on_cost_signature():
    """Both cheap to acquire, both land on measured. Cost cannot separate them."""
    a01, a03 = _access("a01"), _access("a03")
    assert a01["cost"] in ("free", "cheap") and a03["cost"] in ("free", "cheap")
    assert a01["lands_on"] == a03["lands_on"] == "measured"


def test_recoverability_is_what_separates_them():
    assert _access("a01")["receipt_recoverable"] == "none"
    assert _access("a03")["receipt_recoverable"] == "in_principle"
    assert _access("a07")["receipt_recoverable"] == "n/a"
    assert "receipt_recoverable" in ACCESS_SCHEMA["required"]


def test_a_cheap_measured_mode_without_recoverability_fails():
    assert tier.check_recoverability_stated() == []
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        d = pathlib.Path(td) / "a90.json"
        d.write_text(json.dumps({"id": "a90", "name": "x", "tier": "access", "cost": "cheap",
                                 "lands_on": "measured", "breaks_when": "somewhere"}))
        findings = tier.check_recoverability_stated([d])
        assert findings and "collapse" in findings[0]


def test_a03_reclassifies_to_a01_when_receipts_are_gone_in_fact():
    breaks = _access("a03")["breaks_when"]
    assert any("reclassify" in b for b in breaks)
    assert "none" in _access("a03")["uptake_decays_when"]


def test_every_access_mode_states_what_keeps_its_channel_open():
    assert tier.check_uptake_maintenance_stated() == []
    for aid in ("a01", "a03", "a07"):
        rec = _access(aid)
        assert rec["uptake_maintained_by"].strip()
        assert rec["uptake_decays_when"].strip()


def test_a07_never_lands_on_measured():
    """An audit can only refute. Passing means no contradiction found among what is held."""
    a07 = _access("a07")
    assert a07["channel"] == "none"
    assert "measured" not in a07["lands_on"]
    assert set(a07["sub_modes"]) == {"d1_dimensional", "d2_semantic", "d3_lineage"}


@pytest.mark.parametrize("aid", ["a01", "a03", "a07"])
def test_access_entries_validate(aid):
    assert list(Draft202012Validator(ACCESS_SCHEMA).iter_errors(_access(aid))) == []


# ── holdings: recorded contacts, derived trajectories ─────────────

TODAY = datetime.date(2026, 8, 24)


def _h(**kw):
    base = {"holding_id": "h", "provenance": {"concept": "MODEL", "record": "MODEL"}}
    base.update(kw)
    return hold.Holding.from_dict(base)


def test_the_ratio_is_the_reading_not_the_age():
    slow = _h(referent_rate="slow", contact_log=[{"t": "2025-08-24", "kind": "residual"}])
    fast = _h(referent_rate="fast", contact_log=[{"t": "2026-07-01", "kind": "residual"}])
    assert hold.decay_ratio(slow, TODAY) < 1.0, "365 days on a slow referent is fine"
    assert hold.decay_ratio(fast, TODAY) >= 1.0, "54 days on a fast referent is already gone"


def test_unknown_rate_never_becomes_slow():
    assert hold.decay_ratio(_h(referent_rate="unknown"), TODAY) is None
    assert hold.RATE_DAYS["unknown"] is None
    assert cur.priority(_h(referent_rate="unknown"), TODAY) is None


def test_confirmed_stable_and_unrefreshed_are_not_merged():
    """Conflating these is the failure the whole tier exists to catch."""
    s1 = _h(referent_rate="slow", contact_log=[{"t": "2026-08-01", "kind": "residual",
                                                "result": "confirmed"}])
    s2 = _h(referent_rate="slow", contact_log=[])
    assert hold.STALE_CONFIRMED_STABLE in hold.trajectories(s1, {}, TODAY)
    assert hold.STALE_UNREFRESHED in hold.trajectories(s2, {}, TODAY)
    assert hold.STALE_UNREFRESHED not in hold.trajectories(s1, {}, TODAY)
    assert hold.STALE_CONFIRMED_STABLE not in hold.trajectories(s2, {}, TODAY)


def test_discrepancy_is_the_learning_counter():
    learn = _h(referent_rate="slow",
               contact_log=[{"t": "2026-08-01", "kind": "residual", "result": "discrepant"}])
    assert hold.TOWARD_LEARNING in hold.trajectories(learn, {}, TODAY)
    assert "new information" in hold.reading(hold.TOWARD_LEARNING)


def test_circulation_reads_as_confirmation_and_is_not():
    circ = _h(holding_id="c", restatement_count=7, referent_rate="slow", contact_log=[])
    assert hold.TOWARD_CIRCULATION in hold.trajectories(circ, {}, TODAY)
    assert any(f.startswith("CIRCULATION") for f in hold.audit([circ], TODAY))


def test_a_cycle_with_no_residual_anchor_is_circulation_not_false():
    a = _h(holding_id="a", support_ids=["b"], referent_rate="slow")
    b = _h(holding_id="b", support_ids=["a"], referent_rate="slow")
    assert not hold.residual_anchored(a, {"a": a, "b": b})
    findings = hold.audit([a, b], TODAY)
    assert any("CIRCULATION" in f for f in findings)
    assert not any("false" in f.lower() and "not as false" not in f.lower() for f in findings)


def test_zero_discrepancies_over_many_contacts_is_reported_not_resolved():
    amb = _h(holding_id="amb", referent_rate="slow",
             contact_log=[{"t": "2026-08-01", "kind": "residual"} for _ in range(21)])
    findings = [f for f in hold.audit([amb], TODAY) if "AMBIGUOUS" in f]
    assert findings and "Not resolvable" in findings[0]


def test_decay_class_defaults_to_undiagnosed_never_to_d1():
    assert _h().decay_class == hold.UNDIAGNOSED
    assert hold.DECAY_CLASSES[-1] == hold.UNDIAGNOSED
    stale = _h(referent_rate="fast", contact_log=[{"t": "2026-01-01", "kind": "residual"}])
    flagged = [f for f in hold.audit([stale], TODAY) if "PREMATURE_D1" in f]
    assert flagged and "another receiver still resolves it" in flagged[0]


def test_a_cross_observer_check_clears_the_premature_d1_flag():
    checked = _h(referent_rate="fast", cross_observer_checked=True,
                 contact_log=[{"t": "2026-01-01", "kind": "residual"}])
    assert not any("PREMATURE_D1" in f for f in hold.audit([checked], TODAY))


def test_a_trajectory_may_never_be_written_into_the_record():
    d = {"holding_id": "x", "provenance": {"concept": "MODEL", "record": "MODEL"},
         "trajectory": hold.DECAY}
    assert any("computed on read" in e for e in hold.validate_holding(d))


def test_holdings_validate_against_the_json_schema():
    schema = json.loads((ROOT / "schema" / "holding.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    for d in hold.load_raw():
        assert list(validator.iter_errors(d)) == [], d.get("holding_id")
    good = {"holding_id": "h1", "provenance": {"concept": "MODEL", "record": "MODEL"},
            "contact_log": [{"t": "2026-01-01", "kind": "residual", "result": "discrepant"}],
            "referent_rate": "slow"}
    assert list(validator.iter_errors(good)) == []


def test_gap_reach_classes_do_not_collide_with_gap_scan():
    """gap_scan numbers G1-G4 on a different axis. These are spelled out on purpose."""
    assert set(hold.GAP_REACH) == {hold.KNOWN_MISSING, hold.KNOWN_UNRESOLVED, hold.UNMARKED_GAP}
    assert not any(k.startswith("G") and k[1:].isdigit() for k in hold.GAP_REACH)
    assert [g.id for g in gs.scan(gs.Frame("c"), gs.Artifact("m"), gs.Criterion("c"), []).gaps] == \
        ["G1", "G2", "G3", "G4"]


# ── curiosity: the allocator ──────────────────────────────────────

def test_load_bearing_and_decayed_outranks_fresh_and_isolated():
    load = _h(holding_id="load", referent_rate="fast", dependents=["a", "b", "c"],
              contact_log=[{"t": "2026-01-01", "kind": "residual"}])
    leaf = _h(holding_id="leaf", referent_rate="fast", dependents=[],
              contact_log=[{"t": "2026-08-20", "kind": "residual"}])
    assert cur.priority(load, TODAY) > cur.priority(leaf, TODAY)


def test_an_allocation_with_no_offset_is_refused():
    """Zero offset is the self-sealing configuration, not an aggressive one."""
    leaf = _h(holding_id="leaf", referent_rate="fast",
              contact_log=[{"t": "2026-08-20", "kind": "residual"}])
    for bad in (0, -0.5, 1.0, 3):
        with pytest.raises(ValueError):
            cur.allocate(10, [leaf], offset_fraction=bad)
    ok = cur.allocate(10, [leaf], offset_fraction=0.2, as_of=TODAY)
    assert ok.offset == 2
    assert ok.unrankable == hold.UNMARKED_GAP


def test_the_queue_only_ever_reaches_known_missing():
    leaf = _h(holding_id="leaf", referent_rate="fast",
              contact_log=[{"t": "2026-08-20", "kind": "residual"}])
    assert all(r["reach"] == hold.KNOWN_MISSING for r in cur.rank([leaf], TODAY))
    assert "cross-station" in hold.GAP_REACH[hold.UNMARKED_GAP]


def test_unrankable_holdings_are_reported_not_dropped():
    unknown = _h(holding_id="u", referent_rate="unknown")
    leaf = _h(holding_id="leaf", referent_rate="fast",
              contact_log=[{"t": "2026-08-20", "kind": "residual"}])
    rows = cur.rank([unknown, leaf], TODAY)
    assert [r["holding_id"] for r in rows] == ["leaf", "u"]
    assert "why_unrankable" in rows[-1]


def test_audit_triggers_are_recorded_conditions():
    fired = cur.triggered(_h(discrepancy_count=1, scope_misses=2, restatement_count=3))
    assert set(fired) <= set(cur.AUDIT_TRIGGERS)
    assert cur.triggered(_h()) == []


# ── the acquired distribution is a check, not a hope ──────────────

def test_unmarked_must_dominate_or_the_field_is_worthless():
    assert tier.check_acquired_is_recorded_not_guessed() == []
    guessed = [entry_mod.Entry(source_system="x", configuration="y", id=f"E{i}",
                               acquired="transmitted") for i in range(3)]
    findings = tier.check_acquired_is_recorded_not_guessed(guessed)
    assert findings and "guessed at rather than recorded" in findings[0]


# ── SHAPE_SPEC: a shape is the constraint set, not the geometry ───

SHAPE_READ_SCHEMA = json.loads((ROOT / "schema" / "shape_read.schema.json").read_text(encoding="utf-8"))


def test_the_spec_is_shipped_and_pointed_at_not_restated():
    spec = ROOT / "SHAPE_SPEC.md"
    assert spec.exists()
    text = spec.read_text(encoding="utf-8")
    assert "SHAPE  =  the constraint set a geometry is a solution to" in text
    doc = (ROOT / "src" / "rosetta_shape_core" / "shape_read.py").read_text(encoding="utf-8")
    assert "SHAPE_SPEC.md is upstream of this module" in doc


def test_every_file_in_shapes_is_marked_a_geometry_note():
    """faces, edges, vertices and no constraint set. Marking, not criticism."""
    rows = sr.classify_shapes_dir()
    assert len(rows) == 6
    for r in rows:
        assert r["read_class"] == sr.GEOMETRY_NOTE, r["file"]
        assert r["declared"] == sr.GEOMETRY_NOTE, f"{r['file']} is not marked in the file itself"
        assert "removal_test" in r["missing"]


def test_shape_files_still_validate_with_the_marking():
    schema = json.loads((ROOT / "schema" / "shape.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    for f in sorted((ROOT / "shapes").glob("*.json")):
        assert list(validator.iter_errors(json.loads(f.read_text(encoding="utf-8")))) == [], f.name


def test_the_removal_test_is_what_separates_an_entry_from_a_note():
    full = {p: "x" for p in sr.SHAPE_ENTRY_PARTS}
    assert sr.classify(full) == "shape_entry"
    for part in sr.SHAPE_ENTRY_PARTS:
        without = {k: v for k, v in full.items() if k != part}
        assert sr.classify(without) == sr.GEOMETRY_NOTE
        assert sr.missing_parts(without) == [part]


def test_an_unchanged_removal_test_means_the_read_is_wrong():
    """If the form is unchanged the constraint was not load-bearing."""
    base = json.loads((ROOT / "data" / "rosetta" / "shape_reads.jsonl")
                      .read_text(encoding="utf-8").splitlines()[0])
    unchanged = {**base, "removal_test": {**base["removal_test"], "result": "unchanged"}}
    assert any("not load-bearing" in e for e in sr.validate_read(unchanged))
    assert sr.validate_read({**unchanged, "status": "refuted"}) == [], \
        "a failed transfer is a measurement, not an embarrassment"


def test_shipped_reads_validate_against_schema_and_module():
    assert sr.validate_file() == []
    validator = Draft202012Validator(SHAPE_READ_SCHEMA)
    raws = sr.load_raw()
    assert len(raws) == 3
    for d in raws:
        assert list(validator.iter_errors(d)) == [], d.get("id")


def test_cost_framing_is_flagged_and_dissipation_is_not():
    costed = sr.ShapeRead.from_dict({
        "id": "SHAPE_READ.C", "solving_for": "x", "geometry": "g",
        "why_not_the_other_geometry": {"other_geometry": "o", "recovered_term": "t"},
        "removal_test": {"constraint": "c", "absent_in": "a", "result": "unrun"},
        "constraints": [{"name": "the cost of pumping", "sits": sr.INTERNAL_UNIFORM}]})
    assert any("dissipation" in f for f in sr.audit([costed]))
    assert not any("COST_FRAMING" in f for f in sr.audit(sr.load_reads()))


def test_an_external_constraint_geometry_is_not_read_as_an_optimum():
    terrain = sr.ShapeRead.from_dict({
        "id": "SHAPE_READ.T", "geometry": "g", "solving_for": "the optimal routing of sediment",
        "why_not_the_other_geometry": {"other_geometry": "o", "recovered_term": "t"},
        "removal_test": {"constraint": "c", "absent_in": "a", "result": "unrun"},
        "constraints": [{"name": "whatever rock was hit", "sits": sr.EXTERNAL_HETEROGENEOUS}]})
    assert any("transcript of terrain" in f for f in sr.audit([terrain]))


def test_the_delta_read_declares_its_external_constraint():
    delta = next(r for r in sr.load_reads() if "DELTA" in r.id)
    assert delta.external_constraints
    assert delta.status == sr.MARKER
    assert delta.removal_test["result"] == sr.UNRUN, "stated and not run is not tested"


def test_every_constraint_says_where_it_sits():
    for r in sr.load_reads():
        for c in r.constraints:
            assert c["sits"] in sr.SITS, r.id


def test_reads_carry_independent_recurrence_not_just_an_exponent():
    """The fit describes the surviving sample; separate runs converging is the evidence."""
    for r in sr.load_reads():
        assert len(r.independent_recurrence) >= 3, r.id
    assert sr.audit() == []


def test_shared_form_is_named_as_the_blocked_misread():
    doc = rop.__doc__
    assert "GEOMETRIES coincide" in doc
    assert "SHAPE_SPEC.md section 2" in doc
    m = rop.match(rop.Problem(["resonance"], dominant_terms=["resonance"]),
                  entry_mod.load_entries(HAND_WRITTEN)[0])
    assert m.licensing == rop.SHARED_FORM
    assert "picture that matches" in m.reading


def test_the_operator_licenses_on_a_constraint_set():
    """Forcing terms are a constraint set, which is what section 1 calls a shape."""
    assert "constraint set" in rop.__doc__
    assert "SHAPE_SPEC.md section 1" in rop.__doc__
    assert "SHAPE_SPEC.md section 1" in sc.__doc__


# ── METHOD_SPEC: the method is not the falsifiable layer ──────────

def test_the_falsifiable_layer_is_the_read_not_the_method():
    method = (ROOT / "METHOD_SPEC.md").read_text(encoding="utf-8")
    assert "The falsifiable layer is the INDIVIDUAL READ" in method
    assert "removal test" in sr.__doc__ and "per read" in sr.__doc__
    # and it is actually enforced: every shipped read carries one
    for r in sr.load_reads():
        assert r.removal_test.get("constraint"), r.id


def test_confidence_is_never_raised_by_recurrence_alone():
    """NOT upgraded by more instances sharing the geometry without a checked constraint set."""
    base = sr.load_raw()[0]
    bad = {**base, "confidence": {"value": 0.9, "basis": [sr.RECURRENCE_COUNT]}}
    assert any("blocked misread wearing a number" in e for e in sr.validate_read(bad))
    assert sr.RECURRENCE_COUNT not in sr.CONFIDENCE_BASIS
    ok = {**base, "confidence": {"value": 0.8, "basis": [sr.REMOVAL_TEST_PASSED, sr.SCALE_HELD]}}
    assert sr.validate_read(ok) == []


def test_confidence_is_a_separate_readout_not_a_claim_strength():
    base = sr.load_raw()[0]
    low = sr.ShapeRead.from_dict({**base, "confidence": {
        "value": 0.4, "comfort_threshold": 0.7, "basis": [sr.REMOVAL_TEST_PASSED]}})
    findings = sr.audit([low])
    assert any("uncoalesced marker" in f for f in findings)
    assert any("do not resolve it in either direction" in f for f in findings)


def test_a_disappearance_is_the_constraint_set_changing_not_a_falsification():
    base = sr.load_raw()[0]
    wrong = sr.ShapeRead.from_dict({
        **base, "status": "refuted",
        "disappearances": [{"absent_from": "a market after a rule change",
                            "since": "2026-01-01", "bounded_candidates": ["the rule that changed"]}]})
    findings = sr.audit([wrong])
    assert any("WRONG_FINDING" in f for f in findings)
    assert any("not which" in f for f in findings)


def test_a_disappearance_without_a_timestamp_is_fully_underdetermined():
    base = sr.load_raw()[0]
    unbounded = sr.ShapeRead.from_dict({**base, "disappearances": [{"absent_from": "somewhere"}]})
    assert any("UNBOUNDED" in f and "bounds the candidate set" in f
               for f in sr.audit([unbounded]))
    untapped = sr.ShapeRead.from_dict({**base, "disappearances": [
        {"absent_from": "somewhere", "since": "2026-01-01"}]})
    assert any("has not been used" in f for f in sr.audit([untapped]))


def test_an_excluded_domain_is_untested_not_inapplicable():
    """Substrate exclusion returns a null that reads as absence."""
    base = sr.load_raw()[0]
    excluded = sr.ShapeRead.from_dict({**base, "sample_frame": {
        "admitted": ["termite colonies"],
        "excluded": [{"domain": "human settlement", "reason": "treated as a separate category"}]}})
    findings = sr.audit([excluded])
    assert any("UNTESTED, not inapplicable" in f for f in findings)
    assert any("by construction" in f for f in findings)


# ── the shadow read ───────────────────────────────────────────────

SHADOW = {
    "id": "SHAPE_READ.SHADOW", "geometry": "", "solving_for": "a quantity",
    "constraints": [{"name": "c", "sits": sr.INTERNAL_UNIFORM}],
    "why_not_the_other_geometry": {"other_geometry": "o", "recovered_term": "t"},
    "removal_test": {"constraint": "c", "absent_in": "a", "result": "unrun"},
    "read_path": sr.SHADOW, "tangents": ["one gap", "another gap"],
    "outline_state": sr.UNDER_OUTLINED, "status": sr.MARKER,
    "provenance": {"concept": "MODEL", "record": "MODEL"},
}


def test_a_shadow_read_needs_tangents_and_an_outline_state():
    assert sr.validate_read(SHADOW) == []
    assert any("tangents" in e for e in sr.validate_read(
        {k: v for k, v in SHADOW.items() if k != "tangents"}))
    assert any("outline_state" in e for e in sr.validate_read(
        {k: v for k, v in SHADOW.items() if k != "outline_state"}))


def test_a_shadow_read_may_have_no_visible_geometry_but_still_carries_a_removal_test():
    """The geometry is often not visible; the falsifiable layer stays required."""
    schema = Draft202012Validator(SHAPE_READ_SCHEMA)
    assert list(schema.iter_errors(SHADOW)) == []
    direct_empty = {**SHADOW, "read_path": sr.DIRECT}
    for k in ("tangents", "outline_state"):
        direct_empty.pop(k)
    assert list(schema.iter_errors(direct_empty)), "a direct read with no geometry should fail"
    assert SHADOW["removal_test"]["constraint"]


def test_under_outlined_is_a_stated_state_not_a_finished_read():
    assert any("not a failure" in e for e in sr.validate_read({**SHADOW, "status": sr.TESTED}))
    findings = sr.audit([sr.ShapeRead.from_dict(SHADOW)])
    assert any("UNDER_OUTLINED" in f for f in findings)
    assert any("stated state, not a failure" in f for f in findings)


def test_shadow_tangents_are_exempt_from_consistency_checking():
    """A consistency audit over tangents reports conflicts that are not conflicts."""
    assert sr.ShapeRead.from_dict(SHADOW).consistency_exempt
    assert not sr.ShapeRead.from_dict(sr.load_raw()[0]).consistency_exempt
    assert any("not competing claims" in f
               for f in sr.audit([sr.ShapeRead.from_dict(SHADOW)]))


def test_tangents_on_a_direct_read_are_rejected():
    base = sr.load_raw()[0]
    assert any("shadow read" in e for e in sr.validate_read({**base, "tangents": ["g"]}))
