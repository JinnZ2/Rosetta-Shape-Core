#!/usr/bin/env bash
# ============================================================================
#  ROSETTA SAFE ENTRY — AI Training Gateway
# ============================================================================
#  Physics is the guardrail. Curiosity is the engine.
#  This script enforces: read before write, validate before commit,
#  physics before opinion.
#
#  Usage:
#    ./ai_training/safe_entry.sh              # Run full pipeline check
#    ./ai_training/safe_entry.sh orient       # Phase 1: Orient only
#    ./ai_training/safe_entry.sh ground       # Phase 2: Ground + validate
#    ./ai_training/safe_entry.sh validate     # Run all validators
#    ./ai_training/safe_entry.sh explore      # Phase 4: Explore entities
#    ./ai_training/safe_entry.sh pre-commit   # Safety gate before committing
#    ./ai_training/safe_entry.sh status       # System health dashboard
# ============================================================================

set -euo pipefail

# --- Locate repo root ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

# --- Colors (degrade gracefully if no tty) ---
if [ -t 1 ]; then
    RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
    CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'
else
    RED=''; GREEN=''; YELLOW=''; CYAN=''; BOLD=''; RESET=''
fi

pass()  { echo -e "  ${GREEN}OK${RESET}  $1"; }
fail()  { echo -e "  ${RED}FAIL${RESET}  $1"; FAILURES=$((FAILURES + 1)); }
warn()  { echo -e "  ${YELLOW}WARN${RESET}  $1"; }
info()  { echo -e "  ${CYAN}>>>${RESET}  $1"; }
header(){ echo -e "\n${BOLD}=== $1 ===${RESET}"; }

FAILURES=0

# ============================================================================
#  SAFETY CHECKS — Run before anything else
# ============================================================================
safety_checks() {
    header "SAFETY CHECKS"

    # 1. Are we in the right repo?
    if [ -f "$REPO_ROOT/CLAUDE.md" ] && [ -d "$REPO_ROOT/ontology" ]; then
        pass "Repository is Rosetta-Shape-Core"
    else
        fail "Not in Rosetta-Shape-Core repo — aborting"
        exit 1
    fi

    # 2. Is Python available?
    if command -v python3 &>/dev/null || command -v python &>/dev/null; then
        PYTHON=$(command -v python3 || command -v python)
        pass "Python found: $($PYTHON --version 2>&1)"
    else
        fail "Python not found — install Python 3.9+"
        exit 1
    fi

    # 3. Is the package installed?
    if $PYTHON -c "import rosetta_shape_core" 2>/dev/null; then
        pass "rosetta_shape_core is installed"
    else
        warn "rosetta_shape_core not installed — attempting install"
        $PYTHON -m pip install -e ".[dev]" --quiet 2>/dev/null && pass "Installed successfully" || fail "Install failed"
    fi

    # 4. Are immutable axioms intact?
    if [ -f "$REPO_ROOT/.fieldlink.json" ]; then
        local axiom_count
        axiom_count=$(grep -c "explicitly_not_for" "$REPO_ROOT/.fieldlink.json" 2>/dev/null || echo "0")
        if [ "$axiom_count" -gt 0 ]; then
            pass "Use constraints present in .fieldlink.json"
        else
            fail "Use constraints missing — system integrity compromised"
        fi
    else
        fail ".fieldlink.json missing"
    fi

    # 5. No secrets in staging area
    local secrets_found=0
    for pattern in ".env" "*.secrets.json" "credentials*" "*.pem" "*.key"; do
        if git diff --cached --name-only 2>/dev/null | grep -qi "$pattern"; then
            fail "Staged file matches secret pattern: $pattern"
            secrets_found=1
        fi
    done
    if [ "$secrets_found" -eq 0 ]; then
        pass "No secrets detected in staging area"
    fi

    # 6. Protected files not modified without review
    local protected_files=("ontology/_vocab.json" "schema/core.schema.json")
    for pf in "${protected_files[@]}"; do
        if git diff --name-only 2>/dev/null | grep -q "$pf"; then
            warn "Protected file modified: $pf — review carefully"
        fi
    done
}

# ============================================================================
#  PHASE 1: ORIENT — Confirm key files exist and are readable
# ============================================================================
phase_orient() {
    header "PHASE 1: ORIENT"
    info "Checking that core system files are present and readable."

    local orient_files=(
        "CLAUDE.md"
        "ai_training/index.json"
        "ai_training/entry_pipeline.json"
        "ontology/_vocab.json"
        "schema/core.schema.json"
        ".fieldlink.json"
    )

    for f in "${orient_files[@]}"; do
        if [ -f "$REPO_ROOT/$f" ]; then
            pass "$f"
        else
            fail "$f — missing"
        fi
    done

    # Count shapes
    local shape_count
    shape_count=$(find "$REPO_ROOT/shapes" -name "*.json" 2>/dev/null | wc -l)
    info "Shapes found: $shape_count (expected 6)"

    # Count bridges
    local bridge_count
    bridge_count=$(find "$REPO_ROOT/bridges" -name "*.json" 2>/dev/null | wc -l)
    info "Bridges found: $bridge_count"

    # Count fieldlink sources
    local source_count
    source_count=$(grep -c '"name":' "$REPO_ROOT/.fieldlink.json" 2>/dev/null || echo "0")
    info "Fieldlink sources: $source_count"
}

# ============================================================================
#  PHASE 2: GROUND — Validate physics constraints
# ============================================================================
phase_ground() {
    header "PHASE 2: GROUND"
    info "Validating ontology schemas and referential integrity."

    if $PYTHON examples/validate_ontology.py 2>&1 | tail -1 | grep -q "Ontology OK"; then
        pass "Ontology validation: OK"
    else
        fail "Ontology validation failed"
        $PYTHON examples/validate_ontology.py 2>&1 | grep -i "error" | head -5
    fi

    info "Running self-audit (8 structural checks + 7 immutable axioms)."
    local audit_output
    audit_output=$($PYTHON -m rosetta_shape_core.self_audit 2>&1)

    if echo "$audit_output" | grep -q "VERDICT: CLEAN"; then
        pass "Self-audit: CLEAN"
    else
        fail "Self-audit: NOT CLEAN"
        echo "$audit_output" | grep -E "(FAIL|✗)" | head -5
    fi
}

# ============================================================================
#  PHASE 3: VALIDATE — Full test suite
# ============================================================================
phase_validate() {
    header "VALIDATION"
    info "Running full test suite."

    local test_output
    test_output=$($PYTHON -m pytest tests/ -q 2>&1)
    local test_exit=$?

    if [ $test_exit -eq 0 ]; then
        local test_summary
        test_summary=$(echo "$test_output" | tail -1)
        pass "Tests: $test_summary"
    else
        fail "Tests failed"
        echo "$test_output" | grep -E "FAILED|ERROR" | head -10
    fi
}

# ============================================================================
#  PHASE 4: EXPLORE — Show what's available
# ============================================================================
phase_explore() {
    header "PHASE 4: EXPLORE"
    info "Listing all known entities."
    $PYTHON -m rosetta_shape_core.bloom --list 2>&1
}

# ============================================================================
#  PRE-COMMIT GATE — Must pass before any commit
# ============================================================================
pre_commit_gate() {
    header "PRE-COMMIT SAFETY GATE"
    info "This gate enforces: validate before commit."

    # 1. No dangling references
    info "Checking ontology integrity..."
    if $PYTHON examples/validate_ontology.py 2>&1 | tail -1 | grep -q "Ontology OK"; then
        pass "No dangling references"
    else
        fail "Dangling references detected — fix before committing"
    fi

    # 2. Self-audit clean
    info "Running self-audit..."
    if $PYTHON -m rosetta_shape_core.self_audit 2>&1 | grep -q "VERDICT: CLEAN"; then
        pass "Self-audit clean"
    else
        fail "Self-audit failed — system constraints violated"
    fi

    # 3. Tests pass
    info "Running tests..."
    if $PYTHON -m pytest tests/ -q 2>&1 | tail -1 | grep -q "passed"; then
        pass "Tests pass"
    else
        fail "Tests failed — fix before committing"
    fi

    # 4. No destructive patterns in diff
    info "Scanning diff for destructive patterns..."
    local diff_content
    diff_content=$(git diff --cached 2>/dev/null || git diff 2>/dev/null || echo "")

    if echo "$diff_content" | grep -qiE "rm -rf|drop table|delete from|force.push|reset --hard"; then
        warn "Destructive pattern detected in diff — review manually"
    else
        pass "No destructive patterns in diff"
    fi

    # 5. Provenance check on atlas files
    local atlas_files
    atlas_files=$(git diff --cached --name-only 2>/dev/null | grep "^atlas/" || true)
    if [ -n "$atlas_files" ]; then
        info "Checking provenance on staged atlas files..."
        local missing_prov=0
        for af in $atlas_files; do
            if [ -f "$af" ] && ! grep -q "extracted_from" "$af" 2>/dev/null; then
                warn "Missing extracted_from provenance: $af"
                missing_prov=1
            fi
        done
        if [ "$missing_prov" -eq 0 ]; then
            pass "All atlas files have provenance"
        fi
    fi

    echo ""
    if [ "$FAILURES" -eq 0 ]; then
        echo -e "${GREEN}${BOLD}  GATE: OPEN — safe to commit.${RESET}"
    else
        echo -e "${RED}${BOLD}  GATE: BLOCKED — $FAILURES issue(s) must be resolved.${RESET}"
        exit 1
    fi
}

# ============================================================================
#  STATUS DASHBOARD
# ============================================================================
status_dashboard() {
    header "ROSETTA SYSTEM STATUS"

    # Git state
    local branch
    branch=$(git branch --show-current 2>/dev/null || echo "unknown")
    info "Branch: $branch"

    local uncommitted
    uncommitted=$(git status --porcelain 2>/dev/null | wc -l)
    if [ "$uncommitted" -eq 0 ]; then
        pass "Working tree clean"
    else
        warn "$uncommitted uncommitted change(s)"
    fi

    # Counts
    local shapes bridges sources entities tests
    shapes=$(find shapes -name "*.json" 2>/dev/null | wc -l)
    bridges=$(find bridges -name "*.json" 2>/dev/null | wc -l)
    sources=$(grep -c '"name":' .fieldlink.json 2>/dev/null || echo "0")
    tests=$($PYTHON -m pytest tests/ --collect-only -q 2>&1 | tail -1 | grep -oP '\d+' | head -1 || echo "?")

    echo ""
    echo "  Shapes:     $shapes"
    echo "  Bridges:    $bridges"
    echo "  Sources:    $sources"
    echo "  Tests:      $tests"
    echo ""

    # Quick validation
    phase_ground
}

# ============================================================================
#  MAIN DISPATCH
# ============================================================================
main() {
    echo -e "${BOLD}Rosetta Safe Entry — AI Training Gateway${RESET}"
    echo "  Physics is the guardrail. Curiosity is the engine."
    echo ""

    safety_checks

    local cmd="${1:-full}"

    case "$cmd" in
        orient)
            phase_orient
            ;;
        ground)
            phase_orient
            phase_ground
            ;;
        validate)
            phase_ground
            phase_validate
            ;;
        explore)
            phase_explore
            ;;
        pre-commit)
            pre_commit_gate
            ;;
        status)
            status_dashboard
            ;;
        full)
            phase_orient
            phase_ground
            phase_validate
            echo ""
            if [ "$FAILURES" -eq 0 ]; then
                echo -e "${GREEN}${BOLD}  ALL CLEAR — system is safe for exploration.${RESET}"
                echo "  Next: run './ai_training/safe_entry.sh explore' to navigate entities."
            else
                echo -e "${RED}${BOLD}  $FAILURES ISSUE(S) FOUND — resolve before proceeding.${RESET}"
                exit 1
            fi
            ;;
        *)
            echo "Usage: $0 {orient|ground|validate|explore|pre-commit|status|full}"
            echo ""
            echo "  orient      Check core files exist"
            echo "  ground      Validate schemas + self-audit"
            echo "  validate    Run full test suite"
            echo "  explore     List all entities"
            echo "  pre-commit  Safety gate before committing"
            echo "  status      System health dashboard"
            echo "  full        Run orient + ground + validate (default)"
            exit 1
            ;;
    esac

    echo ""
    if [ "$FAILURES" -gt 0 ] && [ "$cmd" != "pre-commit" ]; then
        echo -e "${YELLOW}  $FAILURES issue(s) detected. Review above.${RESET}"
    fi
}

main "$@"
