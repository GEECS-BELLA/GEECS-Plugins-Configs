# Legacy optimizer configs — not loadable, deliberately out of the listing

These are `BaseOptimizerConfig`-shaped documents (an `evaluator:` block with
`geecs_scanner.optimization.*` module paths, save-set-shaped
`device_requirements`). The native `OptimizerConfig` schema refuses them:

    legacy optimizer config is not loadable; see Planning/native_bluesky/11_optimization.md

They live in this subfolder so the scanner's optimizer listing skips them.
`GeecsBluesky`'s config resolver lists a kind folder with `path.iterdir()`
filtered to `.yaml`/`.yml` — non-recursive — so a subdirectory is invisible
to it. Left in the listing, each one renders as a paragraph of pydantic
validation error in the New scan panel.

Moving them out is not a decision about their future; it only stops them
polluting the operator UI. Nothing here is referenced by any preset.

## What each one is waiting on

`hi_res_mag_cam.yaml`, `hi_res_mag_cam_max_counts.yaml`
: **Keepers.** Regeneration is blocked, not declined: one names a deleted
  evaluator module, and no `UC_HiResMagCam` diagnostic document exists under
  `scan_analysis_configs/analyzers/HTU/`. The owner has to say what the
  measurement should point at before these can be rewritten. This may be
  waiting on PVA coverage for non-scalar device types rather than on a
  missing YAML.

`ebeam_source_opt.yaml`
: **Dropped** per `Planning/native_bluesky/11_optimization.md` §9 — its
  objective comes from a LabVIEW TSV trace rather than a frame, which the
  native measurement vocabulary does not express.

`hexapod_alignment.yaml`, `multi_device_example.yaml`
: **Dropped** per the same brief. `multi_device_example` was an example, not
  an operational config.

The brief calls for the three dropped files to be deleted outright. They are
parked here instead, because hiding them was the immediate need and a move is
reversible where a delete is a separate decision. Delete them whenever that
call is made — nothing depends on them.

## The live configs

The six documents in the parent folder are the v1 native shape and validate
against `OptimizerConfig`: the four `bax_alignment_*` steering alignments,
`TopViewMax`, and `bax_alignment_simulation` (the synthetic, hardware-free
objective intended for acceptance runs).
