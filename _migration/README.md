# Unified-configs migration

One-shot tooling for migrating this repo to the unified diagnostic
config schema introduced in `GEECS-BELLA/GEECS-Plugins` PR for issue
#400.

## What it does

Rewrites the split `scan_analysis_configs/library/analyzers/<id>.yaml`
+ `image_analysis_configs/<config_name>.yaml` pair into a single
unified diagnostic YAML at
`scan_analysis_configs/analyzers/<namespace>/<id>.yaml`. The old
`scan_analysis_configs/library/groups.yaml` becomes per-file group
configs under `scan_analysis_configs/groups/<namespace>/`. Old
`scan_analysis_configs/experiments/*.yaml` wrappers are dropped.

The script does **not** delete the absorbed originals — that's a
separate, reviewable commit. The script only writes new files.

## How to run

```bash
cd <configs-repo-root>
python _migration/migrate_to_unified.py --dry-run    # report only
python _migration/migrate_to_unified.py              # actually write
```

`--dry-run` prints a report to stderr without writing anything.
Always run `--dry-run` first to read the warnings.

## What the report tells you

- **Deleted `_var` analyzers** — `_var` configs are skipped per the
  shot-by-shot refactor's decisions. Listed for visibility.
- **Unknown analyzer classes** — analyzer classes with no registered
  alias in `scan_analysis.config.aliases.ALIAS_REGISTRY`. Migrated
  with the verbose escape-hatch form; the user can later add an
  alias and switch.
- **Missing paired image configs** — the scan-analyzer YAML
  references an `image_analysis_configs/<name>.yaml` that doesn't
  exist. The output unified YAML omits the `image:` section; manual
  fix needed before the diagnostic is usable.
- **Unclassified groups** — group names that don't appear in
  `NAMESPACE_MAP` inside the migration script. Their members default
  to namespace `"UNCLASSIFIED"`. Add the mapping and re-run.
- **Cross-namespace analyzers** — an analyzer ID appears in groups
  spanning multiple namespaces. The script picks the first
  alphabetically; manual review encouraged.
- **Background method rewrites** — old aggregation methods
  (`percentile_dataset`, `median`) found in
  `image.background.method`. Aggregation methods belong on a
  `scan.background_source.from_current_scan` directive; the
  application-side method has been rewritten to `from_file` but the
  user must point `file_path` somewhere real or add the directive.
- **Orphan image configs** — `image_analysis_configs/*.yaml` files
  with no scan-analyzer reference. Kept in place (not absorbed); may
  represent ad-hoc analysis configs and need manual review.

## After running

1. Inspect the diff. The new YAMLs under `analyzers/<ns>/` and
   `groups/<ns>/` are deterministic; re-running produces the same
   bytes.
2. In a separate commit, delete the absorbed originals:
   - `scan_analysis_configs/library/analyzers/*.yaml`
   - `scan_analysis_configs/library/groups.yaml`
   - `scan_analysis_configs/experiments/*.yaml`
   - `image_analysis_configs/<name>.yaml` for every `<name>` that
     was referenced by a migrated scan-analyzer (orphans kept).

## After the migration is merged

Delete this directory. The tool serves one purpose and has no
reason to live in the repo after the schema flip.
