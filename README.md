# aXet-P1 — loan-calc

A small Python module for retail loan calculations: **EMI**, **amortisation schedules**, **prepayment savings**, **offer comparison** and **eligibility**.

## Setup (run from `aXet-P1/`)

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows (PowerShell): .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Try the CLI (run from `aXet-P1/`)

Because the `loan_calc/` package lives under `loan-calc/`, you should run the CLI with `PYTHONPATH` set so Python can import it:

```bash
PYTHONPATH=loan-calc python loan-calc/cli.py 1000000 9 240
PYTHONPATH=loan-calc python loan-calc/cli.py 1000000 9 240 --schedule
PYTHONPATH=loan-calc python loan-calc/cli.py 1000000 9 240 --prepay-month 24 --prepay-amount 200000
```

## Run tests + coverage (run from `aXet-P1/`)

```bash
cd loan-calc
pytest --cov=loan_calc --cov-report=term-missing
```

(Tests live under `loan-calc/tests/`.)
