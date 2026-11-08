# interlock_configs

YAML configs consumed by `geecs_python_api.controls.interlocks.load_interlock_server`.

Layout mirrors the other `*_configs/` folders in this repo:

```
interlock_configs/
  experiments/        # per-deployment interlock-server configs
```

`GeecsPathsConfig.interlock_configs_path` resolves to this directory.
Add the following line under `[Paths]` in `~/.config/geecs_python_api/config.ini`:

```ini
interlock_configs_path = /absolute/path/to/GEECS-Plugins-Configs/interlock_configs
```

A relative path passed to `load_interlock_server(...)` is resolved
against `interlock_configs_path`. For example:

```python
load_interlock_server("experiments/bella_camera_example.yaml")
```

resolves to `<interlock_configs_path>/experiments/bella_camera_example.yaml`.
Absolute paths are honored as-is.
