#!/bin/bash
# vault-health.sh — Token budget health check for the workflow protocol ecosystem
# Estimates token counts (word count x 3) across knowledge artifacts
# Run: bash ~/.claude/scripts/vault-health.sh

set -euo pipefail

MULTIPLIER=3  # words -> tokens (conservative for markdown + code blocks)

# Color codes
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

count_words() {
    local total=0
    for f in "$@"; do
        if [ -f "$f" ]; then
            local wc
            wc=$(wc -w < "$f" 2>/dev/null || echo 0)
            total=$((total + wc))
        fi
    done
    echo $total
}

count_dir_words() {
    local dir="$1"
    local pattern="${2:-*.md}"
    local total=0
    if [ -d "$dir" ]; then
        while IFS= read -r -d '' f; do
            local wc
            wc=$(wc -w < "$f" 2>/dev/null || echo 0)
            total=$((total + wc))
        done < <(find "$dir" -name "$pattern" -print0 2>/dev/null)
    fi
    echo $total
}

report_category() {
    local name="$1"
    local words="$2"
    local budget_tokens="$3"

    local tokens=$((words * MULTIPLIER))
    local pct=0
    if [ "$budget_tokens" -gt 0 ]; then
        pct=$((tokens * 100 / budget_tokens))
    fi

    local status="${GREEN}OK${NC}"
    if [ "$pct" -ge 100 ]; then
        status="${RED}OVERHAUL NEEDED${NC}"
    elif [ "$pct" -ge 80 ]; then
        status="${YELLOW}WARNING${NC}"
    fi

    printf "  %-35s %6d words  %6d tokens  %3d%% of %6d  %b\n" \
        "$name" "$words" "$tokens" "$pct" "$budget_tokens" "$status"
}

HOME_DIR="$HOME"
MEMORY_DIR="$HOME_DIR/.claude/projects/C--Users-Anderfail/memory"
MODULES_DIR="$HOME_DIR/.claude/modules"
GLOBAL_SKILLS_DIR="$HOME_DIR/.claude/skills"
AK_DIR="$HOME_DIR/appendix_k"
QAQC_DIR="$HOME_DIR/QAQC Framework"

echo "=========================================="
echo " Vault Health Check"
echo "=========================================="
echo ""

# Workflow-protocol skill (single file, special budget)
wp_words=$(count_words "$GLOBAL_SKILLS_DIR/workflow-protocol.md")
report_category "Workflow-protocol skill" "$wp_words" 15000

# Knowledge modules
modules_words=$(count_dir_words "$MODULES_DIR" "*.md")
report_category "Knowledge modules (all)" "$modules_words" 9000

# Memory files
memory_words=$(count_dir_words "$MEMORY_DIR" "*.md")
report_category "Memory files (all)" "$memory_words" 15000

# Global skills (excluding workflow-protocol, counted separately)
global_skill_words=0
if [ -d "$GLOBAL_SKILLS_DIR" ]; then
    while IFS= read -r -d '' f; do
        if [ "$(basename "$f")" != "workflow-protocol.md" ]; then
            wc=$(wc -w < "$f" 2>/dev/null || echo 0)
            global_skill_words=$((global_skill_words + wc))
        fi
    done < <(find "$GLOBAL_SKILLS_DIR" -maxdepth 1 -name "*.md" -print0 2>/dev/null)
fi
report_category "Global skills (vault cmds)" "$global_skill_words" 6000

# Appendix K project skills
ak_skill_words=0
if [ -d "$AK_DIR/.claude/skills" ]; then
    while IFS= read -r -d '' f; do
        wc=$(wc -w < "$f" 2>/dev/null || echo 0)
        ak_skill_words=$((ak_skill_words + wc))
    done < <(find "$AK_DIR/.claude/skills" -name "SKILL.md" -print0 2>/dev/null)
fi
report_category "Appendix K skills" "$ak_skill_words" 30000

# QAQC project skills
qaqc_skill_words=0
if [ -d "$QAQC_DIR/.claude/skills" ]; then
    while IFS= read -r -d '' f; do
        wc=$(wc -w < "$f" 2>/dev/null || echo 0)
        qaqc_skill_words=$((qaqc_skill_words + wc))
    done < <(find "$QAQC_DIR/.claude/skills" -name "SKILL.md" -print0 2>/dev/null)
fi
report_category "QAQC skills" "$qaqc_skill_words" 15000

# CLAUDE.md files
global_claude_words=$(count_words "$HOME_DIR/.claude/CLAUDE.md")
report_category "Global CLAUDE.md" "$global_claude_words" 2400

ak_claude_words=$(count_words "$AK_DIR/CLAUDE.md")
report_category "Appendix K CLAUDE.md" "$ak_claude_words" 5000

qaqc_claude_words=$(count_words "$QAQC_DIR/CLAUDE.md")
report_category "QAQC CLAUDE.md" "$qaqc_claude_words" 5000

# Decision journals
ak_decisions_words=$(count_words "$AK_DIR/docs/decisions/DECISIONS.md")
report_category "Appendix K decisions" "$ak_decisions_words" 10000

qaqc_decisions_words=$(count_words "$QAQC_DIR/docs/decisions/DECISIONS.md")
report_category "QAQC decisions" "$qaqc_decisions_words" 10000

# Total
total_words=$((wp_words + modules_words + memory_words + global_skill_words + ak_skill_words + qaqc_skill_words + global_claude_words + ak_claude_words + qaqc_claude_words + ak_decisions_words + qaqc_decisions_words))
total_tokens=$((total_words * MULTIPLIER))
total_budget=57000

echo ""
echo "=========================================="
total_pct=$((total_tokens * 100 / total_budget))
if [ "$total_pct" -ge 100 ]; then
    printf "  TOTAL: %d words, %d tokens (%d%% of %d) ${RED}OVERHAUL NEEDED${NC}\n" \
        "$total_words" "$total_tokens" "$total_pct" "$total_budget"
elif [ "$total_pct" -ge 80 ]; then
    printf "  TOTAL: %d words, %d tokens (%d%% of %d) ${YELLOW}WARNING${NC}\n" \
        "$total_words" "$total_tokens" "$total_pct" "$total_budget"
else
    printf "  TOTAL: %d words, %d tokens (%d%% of %d) ${GREEN}OK${NC}\n" \
        "$total_words" "$total_tokens" "$total_pct" "$total_budget"
fi
echo "=========================================="
