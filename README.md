# Susu Group Tracker

A command-line program that manages one rotating savings group (susu) in
Ghanaian Cedi (GHS). Each week every member pays the same fixed amount; when
everyone has paid in full, the whole pot is paid to the next member in join
order, and the group advances to the next week.

Implemented in Python 3.10+ with no third-party runtime dependencies.

## Project layout

    SUSU GROUP TRACKER/
    ├── main.py
    ├── src/
    │   ├── __init__.py
    │   └── susu.py
    ├── tests/
    │   ├── __init__.py
    │   └── test_susu.py
    ├── README.md
    ├── NOTES.md
    ├── requirements.txt
    ├── pytest.ini
    └── .gitignore

## Requirements

- Python 3.10 or newer
- pytest (only for tests)

## How to run

    python -m pip install -r requirements.txt
    python main.py

Commands: `group 50.00`, `add Ama`, `pay Ama 50`, `close`, `report`, `quit`

### Walkthrough (matches the spec example)

    group 50.00
    add Ama
    add Kofi
    add Esi
    pay Ama 50
    pay Kofi 50
    pay Esi 30
    close
    # -> NOT CLOSED: cannot close week; owes: Esi GHS 20.00
    pay Esi 20
    close
    # -> Week 1 closed. Ama received GHS 150.00
    report

## How to run the tests

    python -m pip install -r requirements.txt
    python -m pytest -v

Expected: 10 passed.

## Design

- Money is stored as integer pesewas (1 GHS = 100 pesewas). Parsing uses
  Decimal and rejects more than two decimal places. No float is used.
- Domain logic (`src/susu.py`) performs no I/O. `main.py` is the only place
  that reads input or prints.
- All invalid operations raise subclasses of `SusuError`.

See NOTES.md for assumptions and next steps.
