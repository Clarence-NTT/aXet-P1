## Phase 0 — Branch setup & repo hygiene

### What I did
- Fetched remote refs and ensured work is on branch `first-build` (confirmed with `git branch --show-current`).
- Updated repo-root `.gitignore` to include the required Graphify + Python/tooling ignore patterns.
- Created `PROMPT_LOG.md` with the required columns.
- Consolidated dependencies by moving `loan-calc/requirements.txt` to repo root as `requirements.txt` (so there is exactly one), and updated `loan-calc/README.md` setup command to point to `../requirements.txt`.
- Ensured Graphify-generated files were not staged/committed (reverted `.graphify/*` changes).

### Files changed
- `.gitignore` (expanded ignore rules)
- `PROMPT_LOG.md` (new)
- `requirements.txt` (moved from `loan-calc/requirements.txt`)
- `loan-calc/README.md` (updated install command)

### Test results
- Not run in this phase.

### Uncertainties / items for review
- The initial combined `git fetch/checkout` command hit a 30s timeout in the tool runner, but branch state is confirmed as `first-build` afterwards and `git status` is clean.
- `requirements.txt` currently contains only `pytest` and `pytest-cov` (as it did before the move).

### Commits
- `07b759d chore: add gitignore (incl. graphify), test dependencies and prompt log`
- `ca5b918 docs: add phase 0 summary`
- Confirmed on `first-build`.
