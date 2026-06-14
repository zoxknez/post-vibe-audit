"""
Tests for VAF config module.
"""

import tempfile
from pathlib import Path


class TestDefaultConfig:
    def test_default_limits(self):
        from vaf.config import VAFConfig
        config = VAFConfig()
        assert config.limits.max_total_files == 300
        assert config.limits.max_file_size_kb == 200
        assert config.max_file_size_bytes == 200 * 1024

    def test_default_mode(self):
        from vaf.config import VAFConfig
        config = VAFConfig()
        assert config.mode == "deep"

    def test_default_redaction_enabled(self):
        from vaf.config import VAFConfig
        config = VAFConfig()
        assert config.enable_redaction is True

    def test_default_standards(self):
        from vaf.config import VAFConfig
        config = VAFConfig()
        assert "OWASP_TOP_10_2025" in config.standards.web
        assert "OWASP_ASVS_5" in config.standards.web
        assert "OWASP_LLM_TOP_10_2025" in config.standards.ai
        assert "OWASP_AGENTIC_TOP_10_2026" in config.standards.ai

    def test_default_exclude_dirs(self):
        from vaf.config import VAFConfig
        config = VAFConfig()
        assert "node_modules" in config.exclude_dirs
        assert ".git" in config.exclude_dirs
        assert ".vibe_audit" in config.exclude_dirs

    def test_env_files_excluded(self):
        from vaf.config import VAFConfig
        config = VAFConfig()
        assert ".env" in config.exclude_files
        assert ".env.local" in config.exclude_files
        assert ".env.production" in config.exclude_files


class TestConfigFromYAML:
    def test_loads_mode(self):
        from vaf.config import load_config
        yaml_content = "version: 1\nmode: quick\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "vaf.config.yaml"
            config_path.write_text(yaml_content, encoding="utf-8")
            config = load_config(Path(tmpdir))
            assert config.mode == "quick"

    def test_loads_limits(self):
        from vaf.config import load_config
        yaml_content = "version: 1\nlimits:\n  max_total_files: 500\n  max_file_size_kb: 300\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "vaf.config.yaml"
            config_path.write_text(yaml_content, encoding="utf-8")
            config = load_config(Path(tmpdir))
            assert config.limits.max_total_files == 500
            assert config.limits.max_file_size_kb == 300

    def test_loads_exclude_dirs(self):
        from vaf.config import load_config
        yaml_content = "version: 1\nexclude:\n  dirs:\n    - my_custom_dir\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "vaf.config.yaml"
            config_path.write_text(yaml_content, encoding="utf-8")
            config = load_config(Path(tmpdir))
            # Custom dirs merged with defaults
            assert "my_custom_dir" in config.exclude_dirs
            assert "node_modules" in config.exclude_dirs  # defaults preserved

    def test_missing_config_returns_defaults(self):
        from vaf.config import load_config
        with tempfile.TemporaryDirectory() as tmpdir:
            config = load_config(Path(tmpdir))
            assert config.mode == "deep"
            assert config.limits.max_total_files == 300

    def test_invalid_yaml_returns_defaults(self):
        from vaf.config import load_config
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "vaf.config.yaml"
            config_path.write_text("{ invalid yaml: [unclosed", encoding="utf-8")
            import warnings
            with warnings.catch_warnings(record=True):
                config = load_config(Path(tmpdir))
            assert config.mode == "deep"  # fallback to defaults


class TestConfigComputed:
    def test_max_file_size_bytes(self):
        from vaf.config import VAFConfig
        config = VAFConfig()
        config.limits.max_file_size_kb = 100
        assert config.max_file_size_bytes == 100 * 1024

    def test_output_dir_default(self):
        from vaf.config import VAFConfig
        config = VAFConfig()
        assert config.output_dir == ".vibe_audit"
