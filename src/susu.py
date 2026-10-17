"""Susu Group Tracker — domain logic.

Money is handled as integer pesewas (1 GHS = 100 pesewas) to guarantee
exact arithmetic. No float is used anywhere.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP


class SusuError(Exception):
    """Base error for all domain violations."""

class DuplicateMemberError(SusuError): ...
class UnknownMemberError(SusuError): ...
class InvalidAmountError(SusuError): ...
class OverpaymentError(SusuError): ...
class WeekNotReadyError(SusuError): ...
class LateJoinError(SusuError): ...
class WeekAlreadyClosedError(SusuError): ...


class Money:
    """Immutable integer-pesewa money. Exactly 2 decimal places."""
    __slots__ = ("_p",)

    def __init__(self, pesewas: int):
        if not isinstance(pesewas, int):
            raise TypeError("pesewas must be int")
        self._p = pesewas

    @classmethod
    def from_ghs(cls, value) -> "Money":
        d = Decimal(str(value))
        if d.as_tuple().exponent < -2:
            raise InvalidAmountError("more than 2 decimal places")
        return cls(int((d * 100).to_integral_value(ROUND_HALF_UP)))

    @property
    def pesewas(self) -> int:
        return self._p

    def __add__(self, other): return Money(self._p + other._p)
    def __sub__(self, other): return Money(self._p - other._p)
    def __eq__(self, other): return isinstance(other, Money) and self._p == other._p
    def __hash__(self): return hash(self._p)
    def __lt__(self, other): return self._p < other._p
    def __le__(self, other): return self._p <= other._p
    def __gt__(self, other): return self._p > other._p
    def __ge__(self, other): return self._p >= other._p

    def __str__(self):
        sign = "-" if self._p < 0 else ""
        p = abs(self._p)
        return f"{sign}GHS {p // 100}.{p % 100:02d}"

    def __repr__(self): return f"Money({self._p})"

    @classmethod
    def zero(cls): return cls(0)


@dataclass
class Member:
    name: str
    contributions: dict = field(default_factory=dict)


@dataclass
class Payout:
    week: int
    member: str
    amount: Money


class SusuGroup:
    def __init__(self, weekly_amount: Money):
        if weekly_amount.pesewas <= 0:
            raise InvalidAmountError("weekly amount must be > 0")
        self.weekly_amount = weekly_amount
        self._members: list = []
        self._by_name: dict = {}
        self.week: int = 1
        self._closed: set = set()
        self.payouts: list = []

    def add_member(self, name: str) -> None:
        if self.week != 1 or self._closed:
            raise LateJoinError("cannot add members after week 1 has begun")
        key = name.strip().lower()
        if not key:
            raise InvalidAmountError("empty name")
        if key in self._by_name:
            raise DuplicateMemberError(f"duplicate member: {name}")
        m = Member(name=name.strip())
        self._members.append(m)
        self._by_name[key] = m

    def _require(self, name: str) -> Member:
        m = self._by_name.get(name.strip().lower())
        if not m:
            raise UnknownMemberError(f"unknown member: {name}")
        return m

    def contribute(self, name: str, amount: Money, week: int | None = None) -> Money:
        if amount.pesewas <= 0:
            raise InvalidAmountError("amount must be > 0")
        m = self._require(name)
        w = self.week if week is None else week
        if w in self._closed:
            raise WeekAlreadyClosedError(f"week {w} already closed")
        paid = m.contributions.get(w, Money.zero())
        owed = self.weekly_amount - paid
        if amount > owed:
            raise OverpaymentError(f"{m.name} owes {owed}; cannot pay {amount}")
        m.contributions[w] = paid + amount
        return m.contributions[w]

    def owes(self, name: str, week: int | None = None) -> Money:
        m = self._require(name)
        w = self.week if week is None else week
        return self.weekly_amount - m.contributions.get(w, Money.zero())

    def paid_in_full(self):
        return [m.name for m in self._members
                if m.contributions.get(self.week, Money.zero()) == self.weekly_amount]

    def outstanding(self):
        out = []
        for m in self._members:
            o = self.owes(m.name)
            if o.pesewas > 0:
                out.append((m.name, o))
        return out

    def next_recipient(self) -> str | None:
        if not self._members or len(self._closed) >= len(self._members):
            return None
        return self._members[(self.week - 1) % len(self._members)].name

    def close_week(self) -> Payout:
        if not self._members:
            raise SusuError("no members")
        if self.week in self._closed:
            raise WeekAlreadyClosedError(f"week {self.week} already closed")
        owing = self.outstanding()
        if owing:
            raise WeekNotReadyError(
                "cannot close week; owes: "
                + ", ".join(f"{n} {o}" for n, o in owing)
            )
        pot = Money(self.weekly_amount.pesewas * len(self._members))
        receiver = self._members[(self.week - 1) % len(self._members)]
        payout = Payout(week=self.week, member=receiver.name, amount=pot)
        self.payouts.append(payout)
        self._closed.add(self.week)
        self.week += 1
        return payout

    def report(self) -> str:
        lines = [f"Current week: {self.week}",
                 f"Weekly amount: {self.weekly_amount}",
                 f"Next recipient: {self.next_recipient() or '(rotation complete)'}",
                 f"Members ({len(self._members)}):"]
        for m in self._members:
            if m.contributions.get(self.week, Money.zero()) == self.weekly_amount:
                lines.append(f"  {m.name}: paid in full")
            else:
                lines.append(f"  {m.name}: owes {self.owes(m.name)}")
        lines.append("Payout history:")
        if not self.payouts:
            lines.append("  (none)")
        else:
            for p in self.payouts:
                lines.append(f"  Week {p.week}: {p.member} received {p.amount}")
        return "\n".join(lines)
