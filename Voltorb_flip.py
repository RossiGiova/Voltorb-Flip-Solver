#!/usr/bin/env python3
"""
╔══════════════════════════════════════════╗
║        VOLTORB FLIP  SOLVER              ║
║   Pokémon HeartGold / SoulSilver         ║
╚══════════════════════════════════════════╝

A constraint-based solver for the Voltorb Flip mini-game.
Given the row/column sums and Voltorb counts, it enumerates
all valid board configurations and recommends the safest move
using expected value: E[val] = P(1)×1 + P(2)×2 + P(3)×3.
"""

import os
import sys
import re


# ── ANSI colour codes ─────────────────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BLUE   = "\033[94m"
ORANGE = "\033[38;5;208m"
PURPLE = "\033[95m"


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def ansi_strip(s: str) -> str:
    """Remove ANSI escape codes from a string."""
    return re.sub(r'\033\[[0-9;]*m', '', s)


def ansi_len(s: str) -> int:
    """Return the visible (printable) length of a string, ignoring ANSI codes."""
    return len(ansi_strip(s))


def ansi_pad(s: str, width: int) -> str:
    """Right-pad a string to `width` visible characters, accounting for ANSI codes."""
    return s + " " * max(0, width - ansi_len(s))


# ═══════════════════════════════════════════════════════════════════════════════
# INPUT
# ═══════════════════════════════════════════════════════════════════════════════

def ask_constraints():
    """
    Prompt the user to enter row and column constraints for the 5×5 board.

    Each row/column requires two integers:
      - sum  : the total of all non-Voltorb values in that line (0–15)
      - volts: the number of Voltorb cards in that line (0–5)

    Returns:
        row_sums  (list[int]): sum  for each of the 5 rows
        row_volts (list[int]): voltorb count for each of the 5 rows
        col_sums  (list[int]): sum  for each of the 5 columns
        col_volts (list[int]): voltorb count for each of the 5 columns
    """
    print(f"\n{BOLD}Enter the 5×5 board data.{RESET}")
    print(f"For each row/column provide: {BOLD}SUM  VOLTORBS{RESET}   e.g. {BOLD}6 1{RESET}\n")

    row_sums, row_volts = [], []
    print(f"{BOLD}── ROWS ────────────────────────────────{RESET}")
    for i in range(5):
        while True:
            try:
                parts = input(f"  Row {i + 1}  →  ").split()
                s, v = int(parts[0]), int(parts[1])
                if 0 <= v <= 5 and 0 <= s <= 15:
                    row_sums.append(s)
                    row_volts.append(v)
                    break
                print("    ⚠  Values out of range (sum 0–15, voltorbs 0–5).")
            except (ValueError, IndexError):
                print("    ⚠  Enter two space-separated numbers, e.g.: 6 1")

    col_sums, col_volts = [], []
    print(f"\n{BOLD}── COLUMNS ─────────────────────────────{RESET}")
    for j in range(5):
        while True:
            try:
                parts = input(f"  Col {j + 1}  →  ").split()
                s, v = int(parts[0]), int(parts[1])
                if 0 <= v <= 5 and 0 <= s <= 15:
                    col_sums.append(s)
                    col_volts.append(v)
                    break
                print("    ⚠  Values out of range (sum 0–15, voltorbs 0–5).")
            except (ValueError, IndexError):
                print("    ⚠  Enter two space-separated numbers, e.g.: 4 2")

    return row_sums, row_volts, col_sums, col_volts


# ═══════════════════════════════════════════════════════════════════════════════
# SOLVER  — backtracking with row AND column accumulators
# ═══════════════════════════════════════════════════════════════════════════════

def solve(row_sums, row_volts, col_sums, col_volts, known=None):
    """
    Find all valid 5×5 board configurations consistent with the constraints.

    The search is a depth-first backtrack over the 25 cells (row-major order).
    Pruning rules are applied at every cell for both its row and its column:
      • Partial sum already exceeds the target         → prune
      • Partial sum cannot reach the target with 3s    → prune
      • Partial Voltorb count already exceeds target   → prune
      • Remaining cells cannot supply enough Voltorbs  → prune
      • Last cell in a line: exact match required      → prune if off

    Args:
        row_sums  (list[int]): target sum  per row
        row_volts (list[int]): target #Voltorbs per row
        col_sums  (list[int]): target sum  per column
        col_volts (list[int]): target #Voltorbs per column
        known     (dict):      {(r, c): value} for already-revealed cells

    Returns:
        list[list[int]]: every valid board as a flat list of 25 values (0–3)
    """
    if known is None:
        known = {}

    solutions = []

    # Running totals for pruning — updated incrementally (no grid rescans)
    row_sum_acc  = [0] * 5   # accumulated sum  for each row
    row_volt_acc = [0] * 5   # accumulated Voltorbs for each row
    col_sum_acc  = [0] * 5   # accumulated sum  for each column
    col_volt_acc = [0] * 5   # accumulated Voltorbs for each column
    grid = [0] * 25

    def backtrack(pos: int):
        if pos == 25:
            solutions.append(grid[:])
            return

        r, c = divmod(pos, 5)

        # Use the known value if this cell has been revealed; otherwise try 0–3
        candidates = [known[(r, c)]] if (r, c) in known else [0, 1, 2, 3]

        # How many cells remain in this row/column AFTER the current position
        remaining_in_row = 4 - c
        remaining_in_col = 4 - r

        for val in candidates:
            contrib   = val           # contribution to the sum (0 for Voltorb)
            is_voltorb = (val == 0)

            # ── Row pruning ──────────────────────────────────────────────────
            new_row_sum  = row_sum_acc[r]  + contrib
            new_row_volt = row_volt_acc[r] + is_voltorb

            if new_row_volt > row_volts[r]:                                 continue
            if new_row_sum  > row_sums[r]:                                  continue
            if new_row_sum  + remaining_in_row * 3 < row_sums[r]:          continue
            if new_row_volt + remaining_in_row     < row_volts[r]:          continue
            if c == 4 and (new_row_sum != row_sums[r] or
                           new_row_volt != row_volts[r]):                   continue

            # ── Column pruning ───────────────────────────────────────────────
            new_col_sum  = col_sum_acc[c]  + contrib
            new_col_volt = col_volt_acc[c] + is_voltorb

            if new_col_volt > col_volts[c]:                                 continue
            if new_col_sum  > col_sums[c]:                                  continue
            if new_col_sum  + remaining_in_col * 3 < col_sums[c]:          continue
            if new_col_volt + remaining_in_col     < col_volts[c]:          continue
            if r == 4 and (new_col_sum != col_sums[c] or
                           new_col_volt != col_volts[c]):                   continue

            # ── Place the value and recurse ──────────────────────────────────
            grid[pos]         = val
            row_sum_acc[r]   += contrib;    row_volt_acc[r] += is_voltorb
            col_sum_acc[c]   += contrib;    col_volt_acc[c] += is_voltorb

            backtrack(pos + 1)

            row_sum_acc[r]   -= contrib;    row_volt_acc[r] -= is_voltorb
            col_sum_acc[c]   -= contrib;    col_volt_acc[c] -= is_voltorb

    backtrack(0)
    return solutions


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

def analyse(solutions: list) -> list:
    """
    Return the set of possible values for each cell across all solutions.

    Returns:
        list[set[int]]: 25 sets, one per cell, each containing the values
                        (0–3) that appear in at least one valid solution.
    """
    possible = [set() for _ in range(25)]
    for sol in solutions:
        for i, v in enumerate(sol):
            possible[i].add(v)
    return possible


def calc_probs(solutions: list):
    """
    Compute per-cell probabilities and expected values from all solutions.

    Definitions:
        prob_safe[i]      = P(cell i is NOT a Voltorb)
        prob_val[i][v]    = P(cell i == v)  for v in {0, 1, 2, 3}
        expected_val[i]   = E[value of cell i]
                          = P(1)×1 + P(2)×2 + P(3)×3
                            (unconditional — Voltorb risk is already reflected)

    Returns:
        prob_safe    (list[float])
        prob_val     (list[dict])
        expected_val (list[float])
    """
    n = len(solutions)
    if n == 0:
        return (
            [0.0] * 25,
            [{v: 0.0 for v in range(4)} for _ in range(25)],
            [0.0] * 25,
        )

    counts = [{0: 0, 1: 0, 2: 0, 3: 0} for _ in range(25)]
    for sol in solutions:
        for i, v in enumerate(sol):
            counts[i][v] += 1

    prob_val     = [{v: counts[i][v] / n for v in range(4)} for i in range(25)]
    prob_safe    = [1.0 - prob_val[i][0] for i in range(25)]
    expected_val = [sum(v * prob_val[i][v] for v in (1, 2, 3)) for i in range(25)]
    return prob_safe, prob_val, expected_val


def prob_color(p: float) -> str:
    """Return an ANSI colour code that reflects how safe a probability is."""
    if p >= 1.0:   return GREEN
    if p >= 0.85:  return YELLOW
    if p >= 0.60:  return ORANGE
    if p > 0.0:    return PURPLE
    return RED


# ═══════════════════════════════════════════════════════════════════════════════
# CELL FORMATTING
# ═══════════════════════════════════════════════════════════════════════════════

CELL_W = 8   # visible width of each value cell
PROB_W = 8   # visible width of each probability cell


def fmt_cell_val(possible: set, known_val=None) -> str:
    """Format a single cell for the value board."""
    if known_val is not None:
        if known_val == 0:
            s = f"{RED}{BOLD}  VOLT  {RESET}"
        elif known_val >= 2:
            s = f"{BLUE}{BOLD}  [{known_val}]✓  {RESET}"
        else:
            s = f"{BLUE}  [{known_val}]✓  {RESET}"
        return ansi_pad(s, CELL_W)

    if not possible:
        return ansi_pad(f"{DIM}   ?    {RESET}", CELL_W)
    if possible == {0}:
        return ansi_pad(f"{RED}{BOLD}  !V!   {RESET}", CELL_W)
    if 0 not in possible:
        if len(possible) == 1:
            v   = next(iter(possible))
            col = GREEN if v >= 2 else CYAN
            return ansi_pad(f"{col}{BOLD}  [{v}]   {RESET}", CELL_W)
        vals = "/".join(str(v) for v in sorted(possible))
        return ansi_pad(f"{YELLOW} {vals:<6} {RESET}", CELL_W)

    non_volt = sorted(possible - {0})
    vals = "".join(str(v) for v in non_volt)
    return ansi_pad(f"{DIM} ?{vals:<5} {RESET}", CELL_W)


def fmt_cell_prob(p_safe: float, known_val=None) -> str:
    """Format a single cell for the probability board."""
    if known_val is not None:
        if known_val == 0:
            return ansi_pad(f"{RED}{BOLD}   V    {RESET}", PROB_W)
        return ansi_pad(f"{BLUE}   ✓    {RESET}", PROB_W)
    if p_safe >= 1.0:
        return ansi_pad(f"{GREEN}{BOLD}  100%  {RESET}", PROB_W)
    if p_safe <= 0.0:
        return ansi_pad(f"{RED}{BOLD}   V    {RESET}", PROB_W)
    col = prob_color(p_safe)
    return ansi_pad(f"{col}  {p_safe * 100:3.0f}%   {RESET}", PROB_W)


# ═══════════════════════════════════════════════════════════════════════════════
# BOARD DISPLAY
# ═══════════════════════════════════════════════════════════════════════════════

def _frame(cell_width: int):
    """Build the box-drawing strings for a board with the given cell width."""
    EQ  = "═" * cell_width
    LN  = "─" * cell_width
    top = f"╔{'═' * 8}╦{'╦'.join([EQ] * 5)}╗"
    hdr = f"╠{'═' * 8}╬{'╬'.join([EQ] * 5)}╣"
    bot = f"╚{'═' * 8}╩{'╩'.join([EQ] * 5)}╝"
    div = f"╟{'─' * 8}╫{'╫'.join([LN] * 5)}╢"
    return top, hdr, bot, div


def _col_header(cell_width: int) -> str:
    """Build the column-header row of a board."""
    h = f"{BOLD}║{'':8}║{RESET}"
    for j in range(5):
        h += ansi_pad(f"{BOLD}  Col {j + 1} {RESET}", cell_width) + f"{BOLD}║{RESET}"
    return h


def print_value_board(possible, known, row_sums, row_volts,
                      col_sums, col_volts, n_solutions: int):
    """Print the board showing which values are possible in each cell."""
    top, hdr, bot, div = _frame(CELL_W)
    print(f"\n{BOLD}{top}{RESET}")
    print(_col_header(CELL_W))
    print(f"{BOLD}{hdr}{RESET}")

    for r in range(5):
        row = f"{BOLD}║ Row {r + 1}  ║{RESET}"
        for c in range(5):
            row += fmt_cell_val(possible[r * 5 + c], known.get((r, c)))
            row += f"{BOLD}║{RESET}"
        row += f"  {BOLD}{row_sums[r]:2}{RESET}  │ {BOLD}{row_volts[r]}{RESET}"
        print(row)
        if r < 4:
            print(f"{DIM}{div}{RESET}")

    print(f"{BOLD}{hdr}{RESET}")
    sum_row  = f"{BOLD}║   Σ    ║{RESET}"
    volt_row = f"{BOLD}║   V    ║{RESET}"
    for j in range(5):
        sum_row  += ansi_pad(f"   {col_sums[j]:2}   ", CELL_W)  + f"{BOLD}║{RESET}"
        volt_row += ansi_pad(f"    {col_volts[j]}   ", CELL_W)  + f"{BOLD}║{RESET}"
    print(sum_row)
    print(volt_row)
    print(f"{BOLD}{bot}{RESET}")

    if n_solutions == 0:
        col, sym = RED, "✗"
    elif n_solutions == 1:
        col, sym = GREEN, "✓"
    elif n_solutions < 20:
        col, sym = YELLOW, "◎"
    else:
        col, sym = "", "·"
    print(f"  {sym} Compatible solutions: {BOLD}{col}{n_solutions}{RESET}")


def print_prob_board(prob_safe: list, known: dict, n_solutions: int):
    """Print the board showing P(safe) for each cell."""
    if n_solutions == 0:
        return
    top, hdr, bot, div = _frame(PROB_W)
    print(f"\n  {BOLD}Safety probability P(safe){RESET}  — across {n_solutions} solutions")
    print(f"{BOLD}{top}{RESET}")
    print(_col_header(PROB_W))
    print(f"{BOLD}{hdr}{RESET}")

    for r in range(5):
        row = f"{BOLD}║ Row {r + 1}  ║{RESET}"
        for c in range(5):
            row += fmt_cell_prob(prob_safe[r * 5 + c], known.get((r, c)))
            row += f"{BOLD}║{RESET}"
        print(row)
        if r < 4:
            print(f"{DIM}{div}{RESET}")
    print(f"{BOLD}{bot}{RESET}")


# ═══════════════════════════════════════════════════════════════════════════════
# BEST MOVE RECOMMENDATION
# ═══════════════════════════════════════════════════════════════════════════════

def print_best_move(prob_safe: list, prob_val: list,
                    expected_val: list, known: dict, n_solutions: int):
    """
    Recommend the best cell to flip next.

    The ranking metric is the expected value:
        E[val] = P(val=1)×1 + P(val=2)×2 + P(val=3)×3

    This naturally balances reward and Voltorb risk:
        • P(safe)=100%, value=2  →  E = 2.0
        • P(safe)=80%,  value=3  →  E = 0.8 × 3 = 2.4  (better!)
        • P(safe)=50%,  value=1  →  E = 0.5 × 1 = 0.5  (worse)

    Cells are sorted by E[val] descending, then by P(safe) descending.
    """
    if n_solutions == 0:
        return

    candidates = []
    for i in range(25):
        r, c = divmod(i, 5)
        if (r, c) in known:
            continue
        candidates.append((i, r + 1, c + 1,
                            prob_safe[i], expected_val[i], prob_val[i]))

    if not candidates:
        return

    candidates.sort(key=lambda x: (-x[4], -x[3]))

    best = candidates[0]
    _, rb, cb, ps, e, pv = best

    W    = 54
    line = "═" * W

    print(f"\n{BOLD}╔{line}╗{RESET}")
    title = "  RECOMMENDED MOVE"
    print(f"{BOLD}║{title:^{W}}║{RESET}")
    print(f"{BOLD}╠{line}╣{RESET}")

    cell_text = f"  Flip cell ({rb}, {cb})"
    print(f"{BOLD}║{RESET} {GREEN}{BOLD}{cell_text:<{W - 1}}{RESET}{BOLD}║{RESET}")

    ev_text = f"  E[value]    = {e:.3f}   (higher = better)"
    ps_text = f"  P(safe)     = {ps * 100:.1f}%"
    p1_text = f"  P(val=1)    = {pv[1] * 100:.1f}%"
    p2_text = f"  P(val=2)    = {pv[2] * 100:.1f}%"
    p3_text = f"  P(val=3)    = {pv[3] * 100:.1f}%"
    pv_text = f"  P(Voltorb)  = {pv[0] * 100:.1f}%"

    ev_col = GREEN if e >= 1.5 else (YELLOW if e >= 0.8 else ORANGE)
    ps_col = prob_color(ps)

    print(f"{BOLD}║{RESET} {ev_col}{ev_text:<{W - 1}}{RESET}{BOLD}║{RESET}")
    print(f"{BOLD}║{RESET} {ps_col}{ps_text:<{W - 1}}{RESET}{BOLD}║{RESET}")
    print(f"{BOLD}║{RESET} {DIM}{p1_text:<{W - 1}}{RESET}{BOLD}║{RESET}")
    print(f"{BOLD}║{RESET} {DIM}{p2_text:<{W - 1}}{RESET}{BOLD}║{RESET}")
    print(f"{BOLD}║{RESET} {DIM}{p3_text:<{W - 1}}{RESET}{BOLD}║{RESET}")
    print(f"{BOLD}║{RESET} {RED}{pv_text:<{W - 1}}{RESET}{BOLD}║{RESET}")

    # ── Textual advice ───────────────────────────────────────────────────────
    print(f"{BOLD}╠{line}╣{RESET}")
    if ps >= 1.0 and e >= 2.0:
        tip     = "  ** 100% safe with a guaranteed multiplier — flip it now!"
        tip_col = GREEN
    elif ps >= 1.0:
        tip     = "  *  100% safe. No risk at all."
        tip_col = GREEN
    elif ps >= 0.85 and e >= 1.5:
        tip     = "  o  Very likely safe and profitable. Good choice."
        tip_col = YELLOW
    elif ps >= 0.85:
        tip     = "  o  High probability of being safe."
        tip_col = YELLOW
    elif ps >= 0.60:
        tip     = "  !  Acceptable risk — consider quitting if your score is high."
        tip_col = ORANGE
    elif ps > 0.0:
        tip     = "  !  Risky! Seriously consider quitting."
        tip_col = PURPLE
    else:
        tip     = "  X  Certainly a Voltorb. Do NOT flip."
        tip_col = RED

    print(f"{BOLD}║{RESET} {tip_col}{BOLD}{tip:<{W - 1}}{RESET}{BOLD}║{RESET}")

    all_risky = all(x[3] < 0.60 for x in candidates)
    if all_risky and ps < 0.60:
        retire = "  !! All remaining cells are risky — consider QUITTING!"
        print(f"{BOLD}║{RESET} {RED}{BOLD}{retire:<{W - 1}}{RESET}{BOLD}║{RESET}")

    print(f"{BOLD}╚{line}╝{RESET}")

    # ── Top alternatives ─────────────────────────────────────────────────────
    if len(candidates) > 1:
        print(f"\n  {BOLD}Alternatives:{RESET}")
        print(f"  {'Cell':<8} {'E[val]':>8}  {'P(safe)':>8}  {'P(1)':>6}  "
              f"{'P(2)':>6}  {'P(3)':>6}")
        print("  " + "─" * 54)
        for idx, (_, r2, c2, ps2, e2, pv2) in enumerate(candidates[:8]):
            col2 = (GREEN  if ps2 >= 1.0
                    else YELLOW if ps2 >= 0.85
                    else ORANGE if ps2 >= 0.60
                    else PURPLE)
            marker = f"{GREEN}{BOLD}◀ best{RESET}" if idx == 0 else ""
            print(f"  ({r2},{c2}){'':4} "
                  f"{col2}{e2:>7.3f}{RESET}  "
                  f"{col2}{ps2 * 100:>7.1f}%{RESET}  "
                  f"{pv2[1] * 100:>5.0f}%  "
                  f"{pv2[2] * 100:>5.0f}%  "
                  f"{pv2[3] * 100:>5.0f}%  {marker}")


# ═══════════════════════════════════════════════════════════════════════════════
# LEGEND
# ═══════════════════════════════════════════════════════════════════════════════

def print_legend():
    print(f"""
{BOLD}VALUE LEGEND{RESET}                                  {BOLD}PROBABILITY LEGEND{RESET}
  {GREEN}{BOLD}  [3]   {RESET}  Guaranteed ≥2 — flip immediately   {GREEN}{BOLD}  100%  {RESET}  Definitely safe
  {CYAN}  [1]   {RESET}  Guaranteed 1                         {YELLOW}   85%  {RESET}  Very likely safe
  {YELLOW} 1/2/3  {RESET}  Safe, value varies                   {ORANGE}   60%  {RESET}  Probably safe
  {DIM} ?123   {RESET}  Uncertain (may be Voltorb)            {PURPLE}   30%  {RESET}  Risky
  {RED}{BOLD}  !V!   {RESET}  Certainly Voltorb                    {RED}{BOLD}    V  {RESET}  Certainly Voltorb
  {BLUE}  [2]✓  {RESET}  Already revealed                     {BLUE}    ✓  {RESET}  Already revealed""")


# ═══════════════════════════════════════════════════════════════════════════════
# FULL CELL LIST
# ═══════════════════════════════════════════════════════════════════════════════

def print_cell_list(prob_safe: list, prob_val: list,
                    expected_val: list, known: dict, n_solutions: int):
    """Print all unrevealed cells sorted by expected value (descending)."""
    if n_solutions == 0:
        return

    rows = []
    for i in range(25):
        r, c = divmod(i, 5)
        if (r, c) in known:
            continue
        rows.append((r + 1, c + 1, prob_safe[i], expected_val[i], prob_val[i]))

    if not rows:
        return

    rows.sort(key=lambda x: (-x[3], -x[2]))

    print(f"\n{BOLD}ALL CELLS{RESET}  (sorted by E[value] descending)")
    print(f"  {'Cell':<8} {'E[val]':>8}  {'P(safe)':>8}  {'P(1)':>6}  "
          f"{'P(2)':>6}  {'P(3)':>6}")
    print("  " + "─" * 54)
    for idx, (r, c, ps, e, pv) in enumerate(rows):
        col = (GREEN  if ps >= 1.0
               else YELLOW if ps >= 0.85
               else ORANGE if ps >= 0.60
               else PURPLE if ps > 0
               else RED)
        marker = f" {GREEN}{BOLD}◀{RESET}" if idx == 0 else ""
        print(f"  ({r},{c}){'':4} "
              f"{col}{e:>7.3f}{RESET}  "
              f"{col}{ps * 100:>7.1f}%{RESET}  "
              f"{pv[1] * 100:>5.0f}%  "
              f"{pv[2] * 100:>5.0f}%  "
              f"{pv[3] * 100:>5.0f}%{marker}")


# ═══════════════════════════════════════════════════════════════════════════════
# FULL SOLUTION LIST
# ═══════════════════════════════════════════════════════════════════════════════

def print_solutions(solutions: list):
    """Print every valid board configuration (capped at 20)."""
    if len(solutions) > 20:
        print(f"  {YELLOW}Too many solutions ({len(solutions)}): "
              f"reveal more cells to narrow it down.{RESET}")
        return
    print(f"\n{BOLD}── All solutions ({len(solutions)}) ──{RESET}")
    for idx, sol in enumerate(solutions, 1):
        print(f"\n  {BOLD}#{idx}{RESET}")
        for r in range(5):
            line = "  "
            for v in sol[r * 5:(r + 1) * 5]:
                if v == 0:
                    line += f"{RED}{BOLD}V{RESET} "
                elif v == 1:
                    line += f"{CYAN}1{RESET} "
                else:
                    line += f"{GREEN}{BOLD}{v}{RESET} "
            print(line)


# ═══════════════════════════════════════════════════════════════════════════════
# FULL REDRAW
# ═══════════════════════════════════════════════════════════════════════════════

def redraw(solutions, possible, prob_safe, prob_val, expected_val,
           known, row_sums, row_volts, col_sums, col_volts):
    """Clear the terminal and redraw every board and analysis panel."""
    clear_screen()
    print(__doc__)
    n = len(solutions)

    print_prob_board(prob_safe, known, n)
    print_value_board(possible, known, row_sums, row_volts, col_sums, col_volts, n)
    print_legend()
    print_best_move(prob_safe, prob_val, expected_val, known, n)
    print_cell_list(prob_safe, prob_val, expected_val, known, n)

    if n == 1:
        print(f"\n{GREEN}{BOLD}  ✓ Unique solution! All remaining cells are safe.{RESET}")
        print_solutions(solutions)
    elif n == 0:
        print(f"\n{RED}{BOLD}  ✗ No solution: inconsistent data or a cell was marked incorrectly.{RESET}")

    print(f"\n{DIM}Commands: R C V  |  del R C  |  s100  |  solutions  |  reset  |  help  |  quit{RESET}")


# ═══════════════════════════════════════════════════════════════════════════════
# HELP TEXT
# ═══════════════════════════════════════════════════════════════════════════════

HELP_MSG = f"""
{BOLD}Commands:{RESET}
  {BOLD}R C V{RESET}         Mark a cell: row R, column C, value V (0 = Voltorb)
                 Example: {BOLD}2 4 3{RESET}  → row 2, column 4, value 3
  {BOLD}del R C{RESET}       Remove a marked cell  (e.g. del 2 4)
  {BOLD}s100{RESET}          Auto-mark all cells where P(safe) = 100% and the value
                 is certain. Useful to lock in certainties and shrink the
                 solution space quickly.
  {BOLD}solutions{RESET}     Print all compatible board configurations (up to 20)
  {BOLD}reset{RESET}         Re-enter the board constraints
  {BOLD}help{RESET}          Show this message
  {BOLD}quit{RESET}          Exit

{BOLD}How E[value] works:{RESET}
  E[value] = P(val=1)×1 + P(val=2)×2 + P(val=3)×3

  This metric automatically accounts for the Voltorb risk.
  Example: a cell with 50% Voltorb chance and value 3 has E = 0.5 × 3 = 1.5,
  which is worse than a 100%-safe cell with value 2 (E = 2.0).
  Always flip the cell with the highest E[value].
"""


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN LOOP
# ═══════════════════════════════════════════════════════════════════════════════

def run():
    """Entry point: outer loop handles board resets; inner loop handles moves."""
    clear_screen()
    print(__doc__)

    while True:
        row_sums, row_volts, col_sums, col_volts = ask_constraints()
        known = {}

        while True:
            solutions                        = solve(row_sums, row_volts,
                                                     col_sums, col_volts, known)
            possible                         = analyse(solutions)
            prob_safe, prob_val, expected_val = calc_probs(solutions)

            # Overwrite known cells with exact probabilities
            for (r, c), v in known.items():
                idx = r * 5 + c
                possible[idx]       = {v}
                prob_safe[idx]      = 0.0 if v == 0 else 1.0
                expected_val[idx]   = 0.0
                for vv in range(4):
                    prob_val[idx][vv] = 1.0 if vv == v else 0.0

            redraw(solutions, possible, prob_safe, prob_val, expected_val,
                   known, row_sums, row_volts, col_sums, col_volts)

            try:
                cmd = input("\n→  ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                sys.exit(0)

            cl = cmd.lower()

            # ── Quit ─────────────────────────────────────────────────────────
            if cl in ("quit", "exit", "q"):
                print("Goodbye! Good luck!")
                sys.exit(0)

            # ── Help ─────────────────────────────────────────────────────────
            elif cl in ("help", "h", "?"):
                print(HELP_MSG)
                input("  Press Enter to continue…")

            # ── Reset ────────────────────────────────────────────────────────
            elif cl == "reset":
                break

            # ── Print all solutions ──────────────────────────────────────────
            elif cl in ("solutions", "sol"):
                print_solutions(solutions)
                input("\n  Press Enter to continue…")

            # ── Auto-mark all 100%-safe certain cells ────────────────────────
            elif cl == "s100":
                added = []
                for i in range(25):
                    r2, c2 = divmod(i, 5)
                    if (r2, c2) in known:
                        continue
                    if prob_safe[i] < 1.0:
                        continue
                    p = possible[i]
                    if len(p) == 1 and 0 not in p:
                        v2 = next(iter(p))
                        known[(r2, c2)] = v2
                        added.append((r2 + 1, c2 + 1, v2))
                if added:
                    print(f"\n  {GREEN}Marked {len(added)} cell(s) at 100%:{RESET}")
                    for ra, ca, va in added:
                        print(f"    ({ra},{ca}) = {va}")
                    input("  Press Enter to continue…")
                else:
                    print(f"  {YELLOW}No certain 100%-safe cells to mark.{RESET}")
                    input("  Press Enter…")

            # ── Delete a marked cell ─────────────────────────────────────────
            elif cl.startswith("del "):
                parts = cl.split()
                try:
                    dr, dc = int(parts[1]) - 1, int(parts[2]) - 1
                    if 0 <= dr < 5 and 0 <= dc < 5:
                        if known.pop((dr, dc), None) is None:
                            print(f"  {YELLOW}Cell ({dr + 1},{dc + 1}) was not marked.{RESET}")
                            input("  Press Enter…")
                    else:
                        print(f"  {RED}Coordinates out of range (1–5).{RESET}")
                        input("  Press Enter…")
                except (ValueError, IndexError):
                    print(f"  {RED}Usage: del R C  (e.g. del 2 3){RESET}")
                    input("  Press Enter…")

            # ── Mark a cell ──────────────────────────────────────────────────
            else:
                parts = cmd.split()
                try:
                    r, c, v = int(parts[0]) - 1, int(parts[1]) - 1, int(parts[2])
                    if 0 <= r < 5 and 0 <= c < 5 and 0 <= v <= 3:
                        known[(r, c)] = v
                    else:
                        print(f"  {RED}Range: rows/columns 1–5, values 0–3{RESET}")
                        input("  Press Enter…")
                except (ValueError, IndexError):
                    print(f"  {RED}Unknown command. Type 'help'.{RESET}")
                    input("  Press Enter…")


if __name__ == "__main__":
    run()
