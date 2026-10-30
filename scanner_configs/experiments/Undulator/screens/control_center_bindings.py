"""Rebind the Control Center's writing widgets from the mapping: a bare PV becomes {device, role}.

The mapping (control_center.mapping.md) is the source: each writing row names
the DB device and the GEECS variable behind the PV it lists. A DB device's
role is its GEECS variable name, so a setpoint, toggle, flipper or button
bound to that PV is rebound to {device: <device>, role: "<variable>"}, which
the module writes through its gated put route. Readouts and a flipper's
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
WRITES = ("setpoint", "toggle", "flipper", "button")
#: Disabled in the experiment (the mapping's "Also to check"): rebind once re-enabled.
KEEP_BARE = {"U_ACaveMagSpecPS"}
ROW = re.compile(r"^\| \d+ \| [^|]* \| (?P<kind>\w+) \| (?P<device>\S+) · `(?P<var>[^`]+)` → `(?P<pv>[^`]+)`")
BIND = re.compile(r"\{kind: (?P<kind>\w+), (?P<head>[^\n]*?)bind: \{(?P<bind>[^}]*)\}")


def mapping() -> dict[tuple[str, str], tuple[str, str]]:
    """(kind, PV) → (device, variable), for every writing row."""
    rows = (ROW.match(line) for line in MAPPING.read_text(encoding="utf-8").splitlines())
    return {(m["kind"], m["pv"]): (m["device"], m["var"]) for m in rows if m and m["kind"] in WRITES}


def regenerate(text: str, rows: dict[tuple[str, str], tuple[str, str]]) -> tuple[str, list[str]]:
    """The screen with every mapped writing widget device-bound, and what is still unmapped."""
    missing: list[str] = []

    def rebind(m: re.Match) -> str:
        kind, bind = m["kind"], m["bind"]
        pv = re.fullmatch(r'pv: "([^"]+)"', bind)
        if kind not in WRITES or pv is None:
            return m[0]
        if (kind, pv[1]) not in rows:
            missing.append(f"{kind} {pv[1]}")
            return m[0]
        device, var = rows[(kind, pv[1])]
        if device in KEEP_BARE:
            return m[0]
        return f'{{kind: {kind}, {m["head"]}bind: {{device: {device}, role: "{var}"}}'

    return BIND.sub(rebind, text), missing


def main() -> int:
    text = SCREEN.read_text(encoding="utf-8")
    new, missing = regenerate(text, mapping())
    kept = {pv for (_, pv), (device, _) in mapping().items() if device in KEEP_BARE}
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
