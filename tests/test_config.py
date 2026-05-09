from __future__ import annotations

from pathlib import Path

import pytest

from src.config import VALID_MODELS, Config, ConfigError, load_config


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def write_toml(tmp_path: Path, content: str) -> Path:
    cfg = tmp_path / "config.toml"
    cfg.write_text(content, encoding="utf-8")
    return cfg


# ---------------------------------------------------------------------------
# Defaults — no config file
# ---------------------------------------------------------------------------


def test_defaults_when_file_absent(tmp_path: Path) -> None:
    cfg = load_config(path=tmp_path / "nonexistent.toml")
    assert cfg.model == "base"
    assert cfg.hotkey == "ctrl+space"
    assert cfg.output_dir == Path("~/VoiceNotes").expanduser()
    assert cfg.language == "en"


def test_returns_config_dataclass(tmp_path: Path) -> None:
    cfg = load_config(path=tmp_path / "nonexistent.toml")
    assert isinstance(cfg, Config)


# ---------------------------------------------------------------------------
# Valid config file
# ---------------------------------------------------------------------------


def test_valid_file_loads_all_fields(tmp_path: Path) -> None:
    path = write_toml(
        tmp_path,
        'model = "small"\nhotkey = "cmd+shift+space"\noutput_dir = "/tmp/notes"\nlanguage = "fr"\n',
    )
    cfg = load_config(path=path)
    assert cfg.model == "small"
    assert cfg.hotkey == "cmd+shift+space"
    assert cfg.output_dir == Path("/tmp/notes")
    assert cfg.language == "fr"


def test_partial_file_uses_defaults_for_missing_keys(tmp_path: Path) -> None:
    path = write_toml(tmp_path, 'model = "tiny"\n')
    cfg = load_config(path=path)
    assert cfg.model == "tiny"
    assert cfg.hotkey == "ctrl+space"
    assert cfg.language == "en"


def test_output_dir_is_expanded(tmp_path: Path) -> None:
    path = write_toml(tmp_path, 'output_dir = "~/MyNotes"\n')
    cfg = load_config(path=path)
    assert not str(cfg.output_dir).startswith("~")
    assert cfg.output_dir == Path("~/MyNotes").expanduser()


# ---------------------------------------------------------------------------
# Unknown keys
# ---------------------------------------------------------------------------


def test_unknown_key_raises_config_error(tmp_path: Path) -> None:
    path = write_toml(tmp_path, 'model = "base"\nunknown_field = true\n')
    with pytest.raises(ConfigError, match="Unexpected config key"):
        load_config(path=path)


def test_unknown_key_error_names_the_key(tmp_path: Path) -> None:
    path = write_toml(tmp_path, 'foo = "bar"\n')
    with pytest.raises(ConfigError, match="'foo'"):
        load_config(path=path)


def test_multiple_unknown_keys_all_named(tmp_path: Path) -> None:
    path = write_toml(tmp_path, 'foo = 1\nbar = 2\n')
    with pytest.raises(ConfigError) as exc_info:
        load_config(path=path)
    msg = str(exc_info.value)
    assert "'bar'" in msg and "'foo'" in msg


# ---------------------------------------------------------------------------
# Invalid model value
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("model", VALID_MODELS)
def test_all_valid_model_sizes_accepted(tmp_path: Path, model: str) -> None:
    path = write_toml(tmp_path, f'model = "{model}"\n')
    cfg = load_config(path=path)
    assert cfg.model == model


def test_invalid_model_raises_config_error(tmp_path: Path) -> None:
    path = write_toml(tmp_path, 'model = "huge"\n')
    with pytest.raises(ConfigError, match="Invalid model 'huge'"):
        load_config(path=path)


def test_invalid_model_error_lists_valid_options(tmp_path: Path) -> None:
    path = write_toml(tmp_path, 'model = "xl"\n')
    with pytest.raises(ConfigError) as exc_info:
        load_config(path=path)
    msg = str(exc_info.value)
    for valid in VALID_MODELS:
        assert valid in msg


# ---------------------------------------------------------------------------
# Invalid hotkey / language
# ---------------------------------------------------------------------------


def test_empty_hotkey_raises_config_error(tmp_path: Path) -> None:
    path = write_toml(tmp_path, 'hotkey = ""\n')
    with pytest.raises(ConfigError, match="Invalid hotkey"):
        load_config(path=path)


def test_empty_language_raises_config_error(tmp_path: Path) -> None:
    path = write_toml(tmp_path, 'language = ""\n')
    with pytest.raises(ConfigError, match="Invalid language"):
        load_config(path=path)


# ---------------------------------------------------------------------------
# Immutability
# ---------------------------------------------------------------------------


def test_config_is_frozen(tmp_path: Path) -> None:
    cfg = load_config(path=tmp_path / "nonexistent.toml")
    with pytest.raises((AttributeError, TypeError)):
        cfg.model = "tiny"  # type: ignore[misc]
