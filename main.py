"""Command-line entry point for the Susu Group Tracker."""
import sys
from src.susu import SusuGroup, Money, SusuError

HELP = """Commands:
  group <weekly_ghs>            create group (e.g. group 50.00)
  add <name>                    add member
  pay <name> <amount_ghs>       record contribution this week
  close                         close current week
  report                        show report
  quit"""


def run(stdin=sys.stdin, stdout=sys.stdout):
    group = None
    print(HELP, file=stdout)
    for raw in stdin:
        parts = raw.strip().split()
        if not parts:
            continue
        cmd, *args = parts
        try:
            if cmd == "group" and len(args) == 1:
                group = SusuGroup(Money.from_ghs(args[0]))
                print(f"Created group, weekly {group.weekly_amount}", file=stdout)
            elif cmd == "add" and len(args) == 1 and group:
                group.add_member(args[0])
                print(f"Added {args[0]}", file=stdout)
            elif cmd == "pay" and len(args) == 2 and group:
                group.contribute(args[0], Money.from_ghs(args[1]))
                print(f"{args[0]} paid {args[1]}", file=stdout)
            elif cmd == "close" and group:
                try:
                    p = group.close_week()
                    print(f"Week {p.week} closed. {p.member} received {p.amount}", file=stdout)
                except SusuError as e:
                    print(f"NOT CLOSED: {e}", file=stdout)
            elif cmd == "report" and group:
                print(group.report(), file=stdout)
            elif cmd == "quit":
                return
            else:
                print("bad command or group not created", file=stdout)
        except SusuError as e:
            print(f"ERROR: {e}", file=stdout)


if __name__ == "__main__":
    run()
