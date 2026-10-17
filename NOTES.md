# Notes

## Assumptions and rules

| Situation | Rule |
|---|---|
| Duplicate member | Rejected, case-insensitive, surrounding spaces trimmed. |
| Member added after week 1 starts | Rejected (`LateJoinError`). |
| Partial payment | Allowed; payments accumulate within a week. |
| Overpayment | Rejected without changing the balance (`OverpaymentError`). |
| Incomplete week | No payout, week does not advance (`WeekNotReadyError`). |
| Payout order | Original joining order, one recipient per successful week. |
| Final member receives payout | Rotation completes; next recipient is "(rotation complete)". |
| Money handling | Integer pesewas; parsed via Decimal; >2 dp rejected. |
| Repeated week closure | Rejected (`WeekAlreadyClosedError`). |

**Invariant:** a failed `close_week()` leaves the current week, the next
recipient, and `payouts` untouched. Asserted in `test_partial_payment_blocks_close`.

## Decisions

- Money stored as integer pesewas; Decimal only at the parse boundary.
- Domain logic has no I/O; `main.py` is a thin shell.
- Invalid operations raise subclasses of `SusuError`.

## Improvements with more time

- SQLite persistence and a transaction journal.
- Contributions recorded against an explicit week (domain already supports it).
- JSON report export.
- Property-based tests (Hypothesis) for the money arithmetic.
