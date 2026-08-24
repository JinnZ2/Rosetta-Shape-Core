"""Tests for the Rosetta operator stack — T1 rosetta, T2 families, T3 entry,
T4 scope, T5 gate log, plus gap_scan."""
import json
import pathlib

import pytest
from jsonschema import Draft202012Validator

from rosetta_shape_core import entry as entry_mod
from rosetta_shape_core import families as fam
from rosetta_shape_core import gap_scan as gs
from rosetta_shape_core import gate_log as gl
from rosetta_shape_core import provenance as prov
from rosetta_shape_core import rosetta as rop
from rosetta_shape_core import scope as sc
from rosetta_shape_core import transfer as tr

ROOT = pathlib.Path(__file__).resolve().parents[1]

MODULES = [rop, fam, entry_mod, sc, gl, tr, prov, gs]


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
                "pathlib", "re", "sys", "typing", "rosetta_shape_core",
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


def test_shipped_entries_are_lint_clean():
    assert entry_mod.lint_file() == []


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
           for e in entry_mod.load_entries()}
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
    assert "Coincidence until a mechanism appears" in leads[0].reading


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


def test_every_shipped_entry_names_what_sets_its_configuration():
    for e in entry_mod.load_entries():
        assert e.dominant, e.key
        assert set(e.dominant) <= set(e.families), e.key


def test_unresolved_problem_terms_are_reported_not_silently_dropped():
    p = rop.Problem(["flow", "astrology"])
    assert p.families == ["FLOW"]
    assert p.unresolved == ["astrology"]


def test_by_source_is_the_what_would_x_do_here_lookup():
    assert [e.key for e in rop.by_source("grass")] == ["ENTRY.GRASS_RECONFIGURATION"]
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
    assert set(s) == {"entries", "families", "observations", "transfers", "gap_scan instances"}
    assert all(block["count"] > 0 for block in s.values())


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


def test_observations_are_marked_public_concept_model_record():
    for o in sc.load_observations():
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

def test_reading_protocol_is_present_and_linked():
    doc = (ROOT / "docs" / "reading-protocol.md")
    assert doc.exists()
    text = doc.read_text(encoding="utf-8")
    for signature in ("context ceiling", "gate / register", "accepted guess"):
        assert signature in text
    assert "reading-protocol.md" in (ROOT / "README.md").read_text(encoding="utf-8")
    assert "reading-protocol.md" in (ROOT / "docs" / "rosetta-operator.md").read_text(encoding="utf-8")


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
