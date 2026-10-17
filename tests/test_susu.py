import pytest
from src.susu import (
    SusuGroup, Money,
    DuplicateMemberError, UnknownMemberError, InvalidAmountError,
    OverpaymentError, WeekNotReadyError, LateJoinError,
    WeekAlreadyClosedError,
)


def ghs(s): return Money.from_ghs(s)


def make_group():
    g = SusuGroup(ghs("50.00"))
    for n in ("Ama", "Kofi", "Esi"):
        g.add_member(n)
    return g


def pay_all(g):
    for n in ("Ama", "Kofi", "Esi"):
        g.contribute(n, ghs("50"))


def test_create_group():
    g = SusuGroup(ghs("50.00"))
    assert g.weekly_amount == ghs("50.00")
    assert g.week == 1


def test_money_exact_no_rounding():
    assert ghs("0.10") + ghs("0.20") == ghs("0.30")
    assert str(ghs("50")) == "GHS 50.00"


def test_duplicate_member_rejected():
    g = make_group()
    with pytest.raises(DuplicateMemberError):
        g.add_member("ama")


def test_unknown_member_and_bad_amounts():
    g = make_group()
    with pytest.raises(UnknownMemberError):
        g.contribute("Bisi", ghs("10"))
    with pytest.raises(InvalidAmountError):
        g.contribute("Ama", ghs("0"))
    with pytest.raises(InvalidAmountError):
        g.contribute("Ama", ghs("-5"))


def test_partial_payment_blocks_close():
    g = make_group()
    g.contribute("Ama", ghs("50"))
    g.contribute("Kofi", ghs("50"))
    g.contribute("Esi", ghs("30"))
    assert g.owes("Esi") == ghs("20.00")
    with pytest.raises(WeekNotReadyError) as ei:
        g.close_week()
    assert "Esi" in str(ei.value) and "GHS 20.00" in str(ei.value)
    assert g.week == 1
    assert g.payouts == []
    g.contribute("Esi", ghs("20"))
    payout = g.close_week()
    assert payout.member == "Ama"
    assert payout.amount == ghs("150.00")
    assert g.week == 2


def test_payout_rotation_order():
    g = make_group()
    for _ in range(3):
        pay_all(g)
        g.close_week()
    assert [p.member for p in g.payouts] == ["Ama", "Kofi", "Esi"]
    assert all(p.amount == ghs("150.00") for p in g.payouts)


def test_late_join_rejected_after_week_1():
    g = make_group()
    pay_all(g)
    g.close_week()
    with pytest.raises(LateJoinError):
        g.add_member("Yaw")


def test_week_cannot_be_paid_out_twice():
    """Once week 1 is closed, its payout cannot be re-issued.

    We simulate the scenario by rewinding `g.week` back to 1 and asking
    for another close. The guard must reject it instead of paying a
    second time.
    """
    g = make_group()
    pay_all(g)
    first = g.close_week()
    assert first.week == 1

    g.week = 1  # force the group back to the already-closed week
    with pytest.raises(WeekAlreadyClosedError):
        g.close_week()
    # payout history unchanged
    assert len(g.payouts) == 1


def test_overpayment_rejected():
    g = make_group()
    g.contribute("Ama", ghs("40"))
    with pytest.raises(OverpaymentError):
        g.contribute("Ama", ghs("11"))
    g.contribute("Ama", ghs("10"))
    assert g.owes("Ama") == ghs("0.00")
