# Voltorb Flip Solver

A terminal-based constraint solver for the **Voltorb Flip** mini-game from *Pokémon HeartGold / SoulSilver*.

Given the row and column clues shown on the board (sum of values + number of Voltorbs), it enumerates every valid board configuration and tells you exactly which cell to flip next.

---

## Features

- **Backtracking solver** with incremental row *and* column pruning — fast even in the worst case
- **Probability board** — shows P(safe) for every unrevealed cell across all compatible solutions
- **Value board** — shows the set of possible values (0–3) each cell can still hold
- **Expected-value ranking** — recommends the best move using E[val] = P(1)×1 + P(2)×2 + P(3)×3, which automatically balances reward and Voltorb risk
- **Auto-mark** (`s100`) — instantly locks in all cells that are 100% safe with a known value
- **Full solution list** — prints every compatible board when solutions ≤ 20
- Colour-coded output for quick reading at a glance

---

## How it works

Voltorb Flip is a 5×5 minesweeper-like game. Each cell hides a value of **1**, **2**, **3**, or a **Voltorb** (= 0, which ends the round). The board shows, for every row and column:

| Clue | Meaning |
|------|---------|
| **Sum** | Total of all non-Voltorb values in that line |
| **Voltorbs** | Number of Voltorb cards in that line |

The solver treats these as hard constraints and uses backtracking to enumerate all valid 5×5 grids. For each unrevealed cell it then computes:

```
P(safe)  = fraction of solutions where that cell ≠ Voltorb
E[value] = P(val=1)×1 + P(val=2)×2 + P(val=3)×3
```

The cell with the **highest E[value]** is recommended. This metric is strictly better than just picking the safest cell: a 100%-safe cell worth 1 (E = 1.0) loses to an 80%-safe cell worth 3 (E = 2.4).

---

## Requirements

- Python **3.8+**
- No external dependencies — standard library only
- A terminal with ANSI colour support (Linux, macOS, Windows Terminal)

---

## Usage

```bash
python voltorb_flip_solver.py
```

Enter the clues when prompted (one row/column at a time, `SUM VOLTORBS`):

```
── ROWS ────────────────────────────────
  Row 1  →  6 1
  Row 2  →  3 3
  ...
── COLUMNS ─────────────────────────────
  Col 1  →  7 0
  ...
```

### In-game commands

| Command | Description |
|---------|-------------|
| `R C V` | Mark cell at row R, column C as value V (0 = Voltorb) |
| `del R C` | Remove a previously marked cell |
| `s100` | Auto-mark all cells that are 100% safe with a certain value |
| `solutions` | Print all compatible board configurations (up to 20) |
| `reset` | Re-enter the board clues |
| `help` | Show command reference |
| `quit` | Exit |

---

## Example session

```
  Safety probability P(safe)  — across 4 solutions

  ╔════════╦════════╦════════╦════════╦════════╦════════╗
  ║        ║  Col 1 ║  Col 2 ║  Col 3 ║  Col 4 ║  Col 5 ║
  ╠════════╬════════╬════════╬════════╬════════╬════════╣
  ║ Row 1  ║  100%  ║   50%  ║  100%  ║  100%  ║   50%  ║
  ╟────────╫────────╫────────╫────────╫────────╫────────╢
  ║ Row 2  ║  100%  ║    V   ║  100%  ║    V   ║    V   ║
  ...
  ╚════════╩════════╩════════╩════════╩════════╩════════╝

  ╔══════════════════════════════════════════════════════╗
  ║               RECOMMENDED MOVE                       ║
  ╠══════════════════════════════════════════════════════╣
  ║  Flip cell (5, 2)                                    ║
  ║  E[value]    = 2.000   (higher = better)             ║
  ║  P(safe)     = 100.0%                                ║
  ║  ** 100% safe with a guaranteed multiplier — flip!   ║
  ╚══════════════════════════════════════════════════════╝
```

---

## License

MIT
