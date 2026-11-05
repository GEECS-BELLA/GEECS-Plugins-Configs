"""Rebind the Control Center's writing widgets from the mapping: a bare PV becomes {device, role}.

The mapping (control_center.mapping.md) is the source: each writing row names
the DB device and the GEECS variable behind the PV it lists. A DB device's
role is its GEECS variable name, so a setpoint, toggle, flipper, button or
select bound to that PV is rebound to {device: <device>, role: "<variable>"},
which the module writes through its gated put route. The row's kind is the
widget's (a select for a choice the LabVIEW GUI drew as a number box), and a
row's `values: {on: N, off: N}` goes on its toggle (a boolean the VI keeps as
a number); a widget already device-bound is matched by device and variable. Readouts and a flipper's
lamps stay bare PVs (read only), and so does a write on a device the
experiment has disabled (KEEP_BARE): the module does not list it, and a
screen naming a device the module does not list is refused whole.
Idempotent; --check fails when the screen is not what the mapping
regenerates.

    python control_center_bindings.py [--check]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAPPING, SCREEN = HERE / "control_center.mapping.md", HERE / "control_center.yaml"
WRITES = ("setpoint", "toggle", "flipper", "button", "select")
#: Disabled in the experiment (the mapping's "Also to check"): rebind once re-enabled.
KEEP_BARE = {"U_ACaveMagSpecPS"}
ROW = re.compile(r"^\| \d+ \| [^|]* \| (?P<kind>\w+) \| (?P<device>\S+) · `(?P<var>[^`]+)` → `(?P<pv>[^`]+)`")
VALUES = re.compile(r"values: (?P<values>\{on: -?[\d.]+, off: -?[\d.]+\})")
BIND = re.compile(r"\{kind: (?P<kind>\w+), (?P<head>[^\n]*?)bind: \{(?P<bind>[^}]*)\}(?:, values: \{[^}]*\})?")


def mapping() -> dict[str, tuple[str, str, str, str]]:
    """PV → (kind, device, variable, values or ""), for every writing row."""
    out: dict[str, tuple[str, str, str, str]] = {}
    for line in MAPPING.read_text(encoding="utf-8").splitlines():
        if (m := ROW.match(line)) and m["kind"] in WRITES:
            values = (v := VALUES.search(line)) and v["values"] or ""
            if out.setdefault(m["pv"], row := (m["kind"], m["device"], m["var"], values)) != row:
                raise SystemExit(f"two writing rows disagree on {m['pv']}")
    return out


def regenerate(text: str, rows: dict[str, tuple[str, str, str, str]]) -> tuple[str, list[str]]:
    """The screen with every mapped writing widget device-bound, of the row's kind, and what is still unmapped."""
    missing: list[str] = []
    by_role = {(r[1], r[2]): r for r in rows.values()}

    def rebind(m: re.Match) -> str:
        kind, bind = m["kind"], m["bind"]
        pv = re.fullmatch(r'pv: "([^"]+)"', bind)
        named = re.fullmatch(r'device: (\S+), role: "([^"]+)"', bind)
        if kind not in WRITES or not (pv or named):
            return m[0]
        row = rows.get(pv[1]) if pv else by_role.get((named[1], named[2]))
        if row is None:
            missing.append(f"{kind} {bind}")
            return m[0]
        kind, device, var, values = row
        if device in KEEP_BARE:
            return m[0]
        return f'{{kind: {kind}, {m["head"]}bind: {{device: {device}, role: "{var}"}}' + (f", values: {values}" if values else "")

    return BIND.sub(rebind, text), missing


def main() -> int:
    text = SCREEN.read_text(encoding="utf-8")
    new, missing = regenerate(text, mapping())
    kept = {pv for pv, (_, device, _, _) in mapping().items() if device in KEEP_BARE}
    bare = [m[0][:70] for m in BIND.finditer(new) if m["kind"] in WRITES and m["bind"].startswith("pv:") and m["bind"][5:-1] not in kept]
    if "--check" in sys.argv:
        ok = new == text and not missing and not bare
        print("the screen is what the mapping regenerates" if ok else f"differs; unmapped: {missing}, still bare: {bare}")
        return 0 if ok else 1
    SCREEN.write_text(new, encoding="utf-8")
    print(f"rebound; unmapped: {missing or 'none'}; writing widgets still bare: {len(bare)}")
    return 0 if not missing else 1


if __name__ == "__main__":
    sys.exit(main())
