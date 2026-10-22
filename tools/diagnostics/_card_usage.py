"""Per-card usage statistics across recorded Defect runs.

The question is not "which card has the fewest plays" (a card drafted once
naturally shows up little) but "which card keeps sitting in hand, castable,
and never gets played". So for every card we compare:

  available -- decision points where the card was in hand AND the player had
               enough energy to pay its printed cost
  played    -- decision points where it was the card that got played

A card_play record is a snapshot taken just before the card is played: its
hand still contains that card and its energy is pre-payment. So the hand on
the record is exactly the set of choices that were open at that decision.

Costs come from the wiki export under data/ (see _paths for why it is not
sts_cards.json in the repo root), with the upgraded cost used for names ending
in "+". No cost is ever guessed: a card missing from the export is reported, not
assumed free.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import DATA, LOG_DIR, ROOT, behaviour_logs  # noqa: E402

# Game ids used by CommunicationMod that differ from the wiki's English names.
ALIASES = {
    "Strike_B": "Strike", "Defend_B": "Defend", "Redo": "Undo",
    "Gash": "Claw", "Conserve Battery": "Charge Battery",
    "Lockon": "Bullseye", "Equilibrium": "Undo",
    "Steam": "Steam Barrier", "Steam Power": "Overclock",
    "Strike_R": "Strike", "Defend_R": "Defend",
}

# Card ids that are not in the player's card pool export (curses/statuses).
EXTRA_COSTS = {
    # The game reuses the red Strike/Defend ids for Colourless cards that end up
    # in the Defect pool via events (they showed up as playable with a printed
    # cost of 1 in the recorded runs, so they are not unplayable statuses).
    "Strike_R": 1, "Defend_R": 1,
    "Slimed": 1, "Burn": -2, "Dazed": -2, "Void": -2, "Wound": -2,
    "Writhe": -2, "Doubt": -2, "Shame": -2, "Regret": -2, "Decay": -2,
    "Clumsy": -2, "Injury": -2, "Pain": -2, "Parasite": -2,
    "Normality": -2, "Ascender's Bane": -2, "CurseOfTheBell": -2,
    "Necronomicurse": -2, "Pride": -2,
}


def load_costs():
    data = json.loads((DATA / "sts_cards.json").read_text(encoding="utf-8"))
    costs = {}
    for card in data["cards"]:
        name = card["name_en"]
        base, up = card.get("cost"), card.get("upgradedCost")
        if base is None:
            continue
        costs[name] = base
        costs[name + "+"] = up if up is not None else base
    costs.update(EXTRA_COSTS)
    return costs


COSTS = load_costs()

# Logged id -> engine enum name when the two differ in the card table too.
ENUM_NAMES = {
    "Steam": "STEAM_BARRIER", "Steam Power": "OVERCLOCK",
    "Conserve Battery": "CHARGE_BATTERY", "Redo": "RECURSION",
    "Undo": "EQUILIBRIUM", "Gash": "CLAW", "Lockon": "BULLSEYE",
}


def resolve(name):
    """Map a logged card id to the key used in the cost table."""
    upgraded = name.endswith("+") and len(name) > 1
    bare = name[:-1] if upgraded else name
    bare = ALIASES.get(bare, bare)
    key = bare + "+" if upgraded else bare
    return key if key in COSTS else None


# Statuses that shut the end-turn button: you cannot pass while holding one.
UNPLAYABLE_BUT_BLOCKING = {"Slimed", "Dazed", "Wound", "Burn", "Void"}

def scan(paths):
    stats = defaultdict(lambda: {"available": 0, "played": 0, "end_turn_available": 0,
                                 "offered": 0})
    unknown = set()
    for path in paths:
        prev = None
        for line in path.open(encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            kind = rec.get("kind")
            if kind == "card_play":
                card = rec.get("card")
                if card:
                    stats[card]["played"] += 1
                # The hand and energy on a card_play record are the snapshot
                # taken *before* the card was paid for (1099 of 1121 plays still
                # list the card in hand), so they describe the choice exactly.
                energy_before = rec.get("energy", 0)
                hand_before = set(rec.get("hand") or [])
                if card:
                    hand_before.add(card)
                for c in hand_before:
                    key = resolve(c)
                    if key is None:
                        unknown.add(c)
                        continue
                    cost = COSTS[key]
                    # X-cost cards (cost -1) are always castable with any energy.
                    need = 0 if cost < 0 else cost
                    if energy_before >= need:
                        stats[c]["available"] += 1
            elif kind == "end_turn":
                energy = rec.get("energy", 0)
                hand = set(rec.get("hand") or [])
                # Game rules: while holding a non-curse status such as Slimed or
                # Dazed the end-turn button is disabled, so the turn only ended
                # because a card resolved it. Ending here says nothing about the
                # other cards that happened to be in hand.
                blocked = any(c in UNPLAYABLE_BUT_BLOCKING for c in hand)
                for c in hand:
                    key = resolve(c)
                    if key is None:
                        unknown.add(c)
                        continue
                    cost = COSTS[key]
                    need = 0 if cost < 0 else cost
                    if energy >= need:
                        stats[c]["available"] += 1
                        if not blocked:
                            stats[c]["end_turn_available"] += 1
            prev = rec
    # A GRID prompt is where Recycle and friends ask you to pick a card that is
    # about to be spent, so its hand is one more set of live choices. HAND_SELECT
    # is excluded: it carries the live hand but has no card cost attached, and
    # mixing the two would inflate every card's availability.
    for path in paths:
        for line in path.open(encoding="utf-8"):
            line = line.strip()
            if not line or '"selection"' not in line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("kind") != "selection" or rec.get("screen") != "GRID":
                continue
            for c in set(rec.get("hand") or []):
                if resolve(c) is not None:
                    stats[c]["offered"] += 1
    return stats, unknown


def main():
    if "-h" in sys.argv[1:] or "--help" in sys.argv[1:]:
        print(__doc__)
        print("usage: _card_usage.py [log.jsonl ...]\n"
              "  No arguments reads every log in the STS_TEST_LOGS directory.")
        return
    paths = behaviour_logs()
    if len(sys.argv) > 1:
        paths = [Path(p) for p in sys.argv[1:]]
    stats, unknown = scan(paths)
    rows = [(c, s) for c, s in stats.items() if s["available"] or s["played"]]
    # Unplayed-but-available cards first: those are the suspicious ones.
    rows.sort(key=lambda kv: (kv[1]["played"] - kv[1]["available"], -kv[1]["available"]))
    print(f"{'played':>7} {'avail':>7} {'rate':>6} {'endTurn':>8} {'grid':>5}  card")
    print("-" * 46)
    for card, s in rows:
        rate = s["played"] / s["available"] if s["available"] else float("inf")
        print(f"{s['played']:7d} {s['available']:7d} {rate:6.2f} {s['end_turn_available']:8d}"
              f" {s['offered']:5d}  {card}")
    print("\nCards offered but never played (excluding unplayable curses/statuses):")
    never = [(c, s) for c, s in stats.items()
             if not s["played"] and s["available"] and c not in UNPLAYABLE_BUT_BLOCKING and resolve(c)]
    never.sort(key=lambda kv: -kv[1]["available"])
    if not never:
        print("  none")
    for card, s in never:
        print(f"  {s['available']:4d} offers, {s['end_turn_available']:3d} end-turn skips  {card}")
    if unknown:
        print("\nNo cost entry for: " + ", ".join(sorted(unknown)))
    print(f"\n{len(paths)} logs, {sum(s['played'] for s in stats.values())} plays total")


if __name__ == "__main__":
    main()
