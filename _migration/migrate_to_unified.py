"""Migrate the split scan/image configs to the unified diagnostic schema.

This is a one-shot tool. It rewrites the configs repo in place: the old
``scan_analysis_configs/library/analyzers/``,
``scan_analysis_configs/library/groups.yaml``,
``scan_analysis_configs/experiments/``, and absorbed
``image_analysis_configs/*.yaml`` files are NOT touched by this script
(deletion is a separate, reviewable commit). Reading the report this
script emits to stderr is how you decide what to do with the originals.

Workflow
--------

1. Run with ``--dry-run`` first. Read the report. Resolve any
   ``WARNING`` items (unknown analyzer class, missing image config,
   cross-namespace conflicts).
2. Run for real. The generated unified YAMLs land under
   ``scan_analysis_configs/analyzers/<namespace>/`` and
   ``scan_analysis_configs/groups/<namespace>/``.
3. Inspect the diff. The new files are deterministic; re-running with
   the same inputs produces the same outputs.
4. As a separate commit, delete the absorbed originals.

CLI
---

::

    python _migration/migrate_to_unified.py [--dry-run] [--configs-root DIR]

``--configs-root`` defaults to the directory containing this script's
parent (i.e. the configs repo root when the script lives in
``_migration/``).
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import yaml

logger = logging.getLogger("migrate")


# ---------------------------------------------------------------------------
# Static mappings — keep in sync with scan_analysis/config/aliases.py
# ---------------------------------------------------------------------------


ALIAS_MAP: Dict[str, str] = {
    "image_analysis.offline_analyzers.beam_analyzer.BeamAnalyzer": "beam",
    "image_analysis.offline_analyzers.standard_analyzer.StandardAnalyzer": "standard_2d",
    "image_analysis.offline_analyzers.grenouille_analyzer.GrenouilleAnalyzer": "grenouille",
    (
        "image_analysis.offline_analyzers."
        "magspec_manual_calib_analyzer.MagSpecManualCalibAnalyzer"
    ): "magspec_manual",
    "image_analysis.offline_analyzers.standard_1d_analyzer.Standard1DAnalyzer": "standard_1d",
    "image_analysis.offline_analyzers.line_analyzer.LineAnalyzer": "line",
    "image_analysis.offline_analyzers.ict_1d_analyzer.ICT1DAnalyzer": "ict_1d",
    "image_analysis.offline_analyzers.line_stitcher.LineStitcher": "line_stitcher",
    (
        "image_analysis.offline_analyzers."
        "HASO_himg_has_processor.HASOHimgHasProcessor"
    ): "haso",
}

# Aliases whose target classes consume no embedded image config.
# Diagnostics using these omit the ``image:`` section entirely.
NO_IMAGE_KIND_ALIASES: Set[str] = {"haso"}

# Aliases whose target classes are wrapped in Array1DScanAnalyzer.
# The migrated YAML's ``scan.save`` field maps to ``flag_save_data``
# rather than ``flag_save_images`` when the analyzer is built.
ARRAY1D_ALIASES: Set[str] = {"standard_1d", "line", "ict_1d", "line_stitcher"}

# Group-name → namespace inference for organising the new
# analyzers/<ns>/ tree. Groups not listed here are reported as
# warnings and their members default to namespace "UNCLASSIFIED".
NAMESPACE_MAP: Dict[str, str] = {
    "baseline": "HTU",
    "HTU_slow_analysis": "HTU",
    "htu_variational": "HTU",
    "htu_test": "HTU",
    "HTU_haso_only": "HTU",
    "HTU_opt": "HTU",
    "Visa": "HTU",
    "HTT_MagSpec": "HTT",
    "VHEE": "HTT",
    "PW_frog_onl": "PW",
}


# ---------------------------------------------------------------------------
# Per-run state and reporting
# ---------------------------------------------------------------------------


@dataclass
class MigrationReport:
    """Accumulates issues encountered while migrating; printed at the end."""

    deleted_var_analyzers: List[str] = field(default_factory=list)
    unknown_analyzer_classes: List[Tuple[str, str]] = field(default_factory=list)
    missing_image_configs: List[Tuple[str, str]] = field(default_factory=list)
    unclassified_groups: List[str] = field(default_factory=list)
    cross_namespace_analyzers: List[Tuple[str, List[str]]] = field(default_factory=list)
    background_method_rewrites: List[Tuple[str, str]] = field(default_factory=list)
    orphan_image_configs: List[str] = field(default_factory=list)
    written_analyzers: List[Path] = field(default_factory=list)
    written_groups: List[Path] = field(default_factory=list)

    def print_to(self, stream) -> None:
        """Pretty-print the report. Sections with no items are skipped."""

        def _section(title: str, items: Iterable[Any]) -> None:
            items = list(items)
            if not items:
                return
            print(f"\n[{title}] ({len(items)})", file=stream)
            for item in items:
                print(f"  - {item}", file=stream)

        _section("Deleted _var analyzers", self.deleted_var_analyzers)
        _section(
            "Unknown analyzer classes (manual escape-hatch needed)",
            (f"{a}: {c}" for a, c in self.unknown_analyzer_classes),
        )
        _section(
            "Missing paired image configs",
            (f"{a}: missing {c}" for a, c in self.missing_image_configs),
        )
        _section("Unclassified groups (no namespace mapping)", self.unclassified_groups)
        _section(
            "Cross-namespace analyzers (used first namespace alphabetically)",
            (f"{a}: {sorted(ns)}" for a, ns in self.cross_namespace_analyzers),
        )
        _section(
            "Background method rewrites (aggregation → from_file)",
            (f"{a}: was '{m}'" for a, m in self.background_method_rewrites),
        )
        _section(
            "Orphan image configs (no scan-analyzer paired)",
            self.orphan_image_configs,
        )
        print(
            f"\nWrote {len(self.written_analyzers)} analyzer YAMLs and "
            f"{len(self.written_groups)} group YAMLs.",
            file=stream,
        )


# ---------------------------------------------------------------------------
# Group-file parsing — including commented-out entries
# ---------------------------------------------------------------------------


def parse_groups_file(path: Path) -> Dict[str, List[Tuple[str, bool]]]:
    """Return ``{group_name: [(analyzer_id, enabled_bool), ...]}``.

    Preserves commented-out entries as ``enabled=False`` so the new
    group YAMLs can carry them forward via ``{ref: ..., enabled: false}``
    instead of dropping them. Standard YAML parsing discards comments,
    so this walks the raw text with regex.
    """
    text = path.read_text()
    groups: Dict[str, List[Tuple[str, bool]]] = {}

    # Skip lines until we see "groups:"
    in_groups_block = False
    current_group: Optional[str] = None

    # Group header: "  <name>:" at 2-space indent.
    group_re = re.compile(r"^  ([A-Za-z0-9_-]+):\s*$")
    # Active entry: "    - <id>" at 4-space indent.
    active_re = re.compile(r"^    - ([A-Za-z0-9_./-]+)\s*(?:#.*)?$")
    # Commented entry: "#    - <id>" (any spaces around the #).
    comment_re = re.compile(r"^\s*#\s*-\s*([A-Za-z0-9_./-]+)\s*(?:#.*)?$")

    for line in text.splitlines():
        stripped = line.rstrip()
        if stripped == "groups:":
            in_groups_block = True
            continue
        if not in_groups_block or not stripped:
            continue

        m = group_re.match(line)
        if m:
            current_group = m.group(1)
            groups.setdefault(current_group, [])
            continue

        if current_group is None:
            continue

        active = active_re.match(line)
        if active:
            groups[current_group].append((active.group(1), True))
            continue

        commented = comment_re.match(line)
        if commented:
            groups[current_group].append((commented.group(1), False))
            continue

    return groups


# ---------------------------------------------------------------------------
# Analyzer migration
# ---------------------------------------------------------------------------


def _alias_for_class(class_path: str) -> Optional[str]:
    return ALIAS_MAP.get(class_path)


def _is_var_analyzer(stem: str) -> bool:
    return stem.endswith("_var")


def _normalise_embedded_image(
    image_data: Dict[str, Any],
    analyzer_id: str,
    report: MigrationReport,
) -> Tuple[Dict[str, Any], Optional[int]]:
    """Strip image-side fields that belong elsewhere.

    Returns ``(cleaned_image_dict, background_scan_number_or_None)``.
    The caller writes the bg scan number into ``scan.background_source``.
    """
    data = {k: v for k, v in image_data.items() if k != "name"}

    bg_scan_number: Optional[int] = None
    if "background" in data and isinstance(data["background"], dict):
        bg = dict(data["background"])

        bg_scan_number = bg.pop("background_scan_number", None)
        # dynamic_computation was deleted in the shot-by-shot work;
        # any straggler here is dropped silently — the field no longer
        # exists in BackgroundConfig.
        bg.pop("dynamic_computation", None)

        # PERCENTILE_DATASET and MEDIAN are aggregation methods that
        # don't apply at per-shot subtraction time. Surface as warnings
        # and rewrite to from_file — the user must point file_path at a
        # real cache or switch to background_source.from_current_scan.
        if bg.get("method") in ("percentile_dataset", "median"):
            report.background_method_rewrites.append((analyzer_id, bg["method"]))
            bg["method"] = "from_file"

        data["background"] = bg

    return data, bg_scan_number


def migrate_analyzer(
    analyzer_path: Path,
    image_configs_dir: Path,
    namespace: str,
    report: MigrationReport,
) -> Optional[Dict[str, Any]]:
    """Build the unified diagnostic dict for one old analyzer YAML.

    Returns ``None`` when the analyzer can't be migrated automatically
    (the issue is recorded in ``report``). The analyzer's canonical ID
    is the legacy ``id`` field (since groups reference it that way),
    falling back to the old file stem when ``id`` is absent.
    """
    with open(analyzer_path) as f:
        old = yaml.safe_load(f) or {}

    analyzer_id = old.get("id") or analyzer_path.stem
    class_path = old.get("image_analyzer", {}).get("analyzer_class")
    if not class_path:
        report.unknown_analyzer_classes.append((analyzer_id, "<missing>"))
        return None

    alias = _alias_for_class(class_path)
    if alias is None:
        report.unknown_analyzer_classes.append((analyzer_id, class_path))
        # We still emit the verbose form so the YAML is usable; the
        # user can swap to a custom alias later.
        scan_type = old.get("type", "array2d")
        image_kind = "camera" if scan_type == "array2d" else "line"
        image_analyzer_field: Any = {
            "class": class_path,
            "image_kind": image_kind,
            "scan_type": scan_type,
            "kwargs": old.get("image_analyzer", {}).get("kwargs", {}) or {},
        }
    else:
        # Alias form. Carry kwargs only if the analyzer needs them
        # beyond the embedded image config.
        ia_kwargs = dict(old.get("image_analyzer", {}).get("kwargs", {}) or {})
        # camera_config_name / line_config_name are no longer carried
        # in kwargs — the embedded image: section IS the camera/line
        # config. Drop them.
        ia_kwargs.pop("camera_config_name", None)
        ia_kwargs.pop("line_config_name", None)
        if ia_kwargs:
            image_analyzer_field = {"alias": alias, "kwargs": ia_kwargs}
        else:
            image_analyzer_field = alias

    # Look up the paired image config (if the alias has image_kind != none).
    image_section: Optional[Dict[str, Any]] = None
    bg_scan_number: Optional[int] = None
    if alias not in NO_IMAGE_KIND_ALIASES:
        # The legacy schema was inconsistent about where camera_config_name
        # lived: some configs put it at image_analyzer.camera_config_name
        # (sibling of analyzer_class), others nested it inside
        # image_analyzer.kwargs.camera_config_name. Check both — missing
        # the top-level form silently drops the image absorption and
        # produces a unified diagnostic with no ``image:`` section, which
        # is data loss after the cleanup step deletes the original.
        ia_section = old.get("image_analyzer", {}) or {}
        ia_kwargs_orig = ia_section.get("kwargs", {}) or {}
        config_name = (
            ia_section.get("camera_config_name")
            or ia_section.get("line_config_name")
            or ia_kwargs_orig.get("camera_config_name")
            or ia_kwargs_orig.get("line_config_name")
        )
        if config_name:
            image_path = image_configs_dir / f"{config_name}.yaml"
            if image_path.exists():
                with open(image_path) as f:
                    raw_image = yaml.safe_load(f) or {}
                image_section, bg_scan_number = _normalise_embedded_image(
                    raw_image, analyzer_id, report
                )
            else:
                report.missing_image_configs.append((analyzer_id, str(image_path)))

    # Build the scan: section.
    scan_section: Dict[str, Any] = {}
    if "priority" in old:
        scan_section["priority"] = old["priority"]
    if "analysis_mode" in old:
        scan_section["mode"] = old["analysis_mode"]
    if "flag_save_images" in old:
        scan_section["save"] = old["flag_save_images"]
    elif "flag_save_data" in old:
        scan_section["save"] = old["flag_save_data"]
    if "gdoc_slot" in old:
        scan_section["gdoc_slot"] = old["gdoc_slot"]
    if old.get("device_name") and old.get("device_name") != analyzer_id:
        # Top-level name will default to the diagnostic ID (filename
        # stem). When the data folder name differs, set scan.device.
        # Note: many existing configs use device_name as both the
        # data folder AND the metric prefix; we'll set name=device_name
        # at the top level below and skip scan.device unless they differ.
        pass
    # file_tail can live either on the analyzer's image_analyzer.kwargs
    # or on the top-level kwargs. The top-level form wins when both are
    # present (matches the legacy factory's behavior).
    file_tail: Optional[str] = None
    top_kwargs = old.get("kwargs") or {}
    if isinstance(top_kwargs, dict) and "file_tail" in top_kwargs:
        file_tail = top_kwargs["file_tail"]
    if file_tail is None:
        ia_kwargs_orig = old.get("image_analyzer", {}).get("kwargs", {}) or {}
        if "file_tail" in ia_kwargs_orig:
            file_tail = ia_kwargs_orig["file_tail"]
    if file_tail is not None:
        scan_section["file_tail"] = file_tail

    renderer_kwargs = old.get("renderer_kwargs") or {}
    if renderer_kwargs:
        scan_section["renderer_kwargs"] = renderer_kwargs

    if bg_scan_number is not None:
        scan_section["background_source"] = {"scan_number": bg_scan_number}

    # Top-level name = device_name (which serves as both folder and
    # default metric prefix in the current model).
    name = old.get("device_name") or analyzer_id

    unified: Dict[str, Any] = {
        "name": name,
        "image_analyzer": image_analyzer_field,
    }
    if image_section is not None:
        unified["image"] = image_section
    if scan_section:
        unified["scan"] = scan_section

    return unified


# ---------------------------------------------------------------------------
# Group migration
# ---------------------------------------------------------------------------


def migrate_group(
    group_name: str,
    entries: List[Tuple[str, bool]],
    namespace: str,
    deleted_ids: Set[str],
    report: MigrationReport,
) -> Dict[str, Any]:
    """Build the unified analysis-group dict for one old group entry."""
    analyzers: List[Any] = []
    for analyzer_id, enabled in entries:
        if analyzer_id in deleted_ids:
            continue
        if enabled:
            analyzers.append(analyzer_id)
        else:
            analyzers.append({"ref": analyzer_id, "enabled": False})

    return {
        "name": f"{namespace}_{group_name}" if not group_name.startswith(namespace) else group_name,
        "analyzers": analyzers,
    }


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def _write_yaml(path: Path, data: Dict[str, Any], dry_run: bool) -> None:
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.safe_dump(
            data,
            f,
            sort_keys=False,
            default_flow_style=False,
            indent=2,
        )


def migrate(configs_root: Path, *, dry_run: bool = False) -> MigrationReport:
    """Migrate the configs repo at ``configs_root`` to the unified schema."""
    report = MigrationReport()

    scan_root = configs_root / "scan_analysis_configs"
    image_root = configs_root / "image_analysis_configs"
    old_analyzers_dir = scan_root / "library" / "analyzers"
    old_groups_path = scan_root / "library" / "groups.yaml"
    new_analyzers_root = scan_root / "analyzers"
    new_groups_root = scan_root / "groups"

    if not old_analyzers_dir.is_dir():
        raise FileNotFoundError(f"Old analyzer dir missing: {old_analyzers_dir}")
    if not old_groups_path.is_file():
        raise FileNotFoundError(f"Old groups file missing: {old_groups_path}")

    groups = parse_groups_file(old_groups_path)

    # Build inverse index: analyzer_id → set of namespaces it appears in.
    analyzer_namespaces: Dict[str, Set[str]] = defaultdict(set)
    for group_name, entries in groups.items():
        ns = NAMESPACE_MAP.get(group_name)
        if ns is None:
            if group_name not in report.unclassified_groups:
                report.unclassified_groups.append(group_name)
            continue
        for analyzer_id, _enabled in entries:
            analyzer_namespaces[analyzer_id].add(ns)

    deleted_ids: Set[str] = set()
    referenced_image_configs: Set[str] = set()

    for analyzer_path in sorted(old_analyzers_dir.glob("*.yaml")):
        with open(analyzer_path) as f:
            old = yaml.safe_load(f) or {}
        # The new file stem is the legacy ``id`` field, not the old
        # file stem — groups reference analyzers by id, and many old
        # YAMLs had file stems that diverged from id (e.g.
        # ``HTT-MagCam1.yaml`` with ``id: MagCam1``).
        new_id = old.get("id") or analyzer_path.stem

        if _is_var_analyzer(new_id):
            report.deleted_var_analyzers.append(new_id)
            deleted_ids.add(new_id)
            continue

        namespaces = analyzer_namespaces.get(new_id, set())
        if not namespaces:
            namespace = "UNCLASSIFIED"
        elif len(namespaces) == 1:
            namespace = next(iter(namespaces))
        else:
            report.cross_namespace_analyzers.append((new_id, list(namespaces)))
            namespace = sorted(namespaces)[0]

        unified = migrate_analyzer(analyzer_path, image_root, namespace, report)
        if unified is None:
            continue

        # Track which image configs were absorbed. Mirrors the same
        # top-level-or-kwargs lookup that ``migrate_analyzer`` does.
        ia_section = old.get("image_analyzer") or {}
        ia_kwargs = ia_section.get("kwargs") or {}
        cfg_name = (
            ia_section.get("camera_config_name")
            or ia_section.get("line_config_name")
            or ia_kwargs.get("camera_config_name")
            or ia_kwargs.get("line_config_name")
        )
        if cfg_name:
            referenced_image_configs.add(cfg_name)

        out_path = new_analyzers_root / namespace / f"{new_id}.yaml"
        _write_yaml(out_path, unified, dry_run)
        report.written_analyzers.append(out_path)

    # Migrate groups. Determine each group's namespace by majority.
    for group_name, entries in groups.items():
        ns = NAMESPACE_MAP.get(group_name)
        if ns is None:
            continue
        group_data = migrate_group(group_name, entries, ns, deleted_ids, report)
        out_path = new_groups_root / ns / f"{group_name}.yaml"
        _write_yaml(out_path, group_data, dry_run)
        report.written_groups.append(out_path)

    # Report orphan image configs (present but not referenced).
    for image_path in sorted(image_root.glob("*.yaml")):
        if image_path.stem not in referenced_image_configs:
            report.orphan_image_configs.append(image_path.stem)

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the report without writing any new YAMLs.",
    )
    parser.add_argument(
        "--configs-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Path to the configs repo root (default: parent of this script).",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable INFO logging."
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s: %(message)s",
    )

    report = migrate(args.configs_root, dry_run=args.dry_run)
    report.print_to(sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
