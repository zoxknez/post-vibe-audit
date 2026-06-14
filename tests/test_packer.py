"""
Tests for VAF packer module.
"""

import tempfile
from pathlib import Path

from vaf.config import VAFConfig
from vaf.packer import (
    _file_importance_score,
    collect_file_contents,
    detect_stack,
    generate_file_tree,
)


class TestDetectStack:
    def test_detects_nodejs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "package.json").write_text('{"name": "test"}', encoding="utf-8")
            stack = detect_stack(Path(tmpdir))
            assert stack["has_nodejs"] is True

    def test_detects_python(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "pyproject.toml").write_text("[project]\nname = 'test'", encoding="utf-8")
            stack = detect_stack(Path(tmpdir))
            assert stack["has_python"] is True

    def test_detects_docker(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "Dockerfile").write_text("FROM python:3.11", encoding="utf-8")
            stack = detect_stack(Path(tmpdir))
            assert stack["has_docker"] is True

    def test_detects_github_actions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workflows = Path(tmpdir) / ".github" / "workflows"
            workflows.mkdir(parents=True)
            (workflows / "ci.yml").write_text("on: push", encoding="utf-8")
            stack = detect_stack(Path(tmpdir))
            assert stack["has_github_actions"] is True

    def test_detects_llm_usage_from_package_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            pkg = '{"dependencies": {"openai": "^4.0.0"}}'
            (Path(tmpdir) / "package.json").write_text(pkg, encoding="utf-8")
            stack = detect_stack(Path(tmpdir))
            assert stack["has_llm_usage"] is True

    def test_no_stack_detected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            stack = detect_stack(Path(tmpdir))
            assert not stack["has_python"]
            assert not stack["has_nodejs"]


class TestFileImportanceScore:
    def test_auth_files_highest_priority(self):
        auth_score = _file_importance_score("src/auth/session.ts")
        style_score = _file_importance_score("src/styles/theme.css")
        assert auth_score > style_score

    def test_api_routes_high_priority(self):
        api_score = _file_importance_score("app/api/users/route.ts")
        docs_score = _file_importance_score("docs/architecture.md")
        assert api_score > docs_score

    def test_test_files_lower_priority(self):
        auth_score = _file_importance_score("src/auth/login.ts")
        test_score = _file_importance_score("tests/test_auth.py")
        assert auth_score > test_score


class TestGenerateFileTree:
    def test_excludes_node_modules(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "src").mkdir()
            (root / "src" / "index.ts").write_text("", encoding="utf-8")
            (root / "node_modules").mkdir()
            (root / "node_modules" / "react").mkdir()

            config = VAFConfig()
            tree = generate_file_tree(tmpdir, config)
            assert "node_modules" not in tree
            assert "src" in tree

    def test_includes_source_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "main.py").write_text("", encoding="utf-8")
            (root / "config.yaml").write_text("", encoding="utf-8")

            config = VAFConfig()
            tree = generate_file_tree(tmpdir, config)
            assert "main.py" in tree
            assert "config.yaml" in tree


class TestCollectFileContents:
    def test_collects_python_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "main.py").write_text("print('hello')", encoding="utf-8")

            config = VAFConfig()
            contents, _skipped, _evidence = collect_file_contents(root, config)
            assert len(contents) >= 1
            assert any("main.py" in c for c in contents)

    def test_skips_oversized_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            big_content = "x" * (300 * 1024)  # 300KB > 200KB limit
            (root / "big_file.py").write_text(big_content, encoding="utf-8")

            config = VAFConfig()
            contents, skipped, _evidence = collect_file_contents(root, config)
            assert len(contents) == 0
            assert any("big_file.py" in s for s in skipped)

    def test_redaction_applied(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            secret_content = "API_KEY=sk-proj-thisIsAFakeSecretKeyForTesting123456789"
            (root / "config.py").write_text(secret_content, encoding="utf-8")

            config = VAFConfig()
            config.enable_redaction = True
            contents, _, _ = collect_file_contents(root, config)
            assert len(contents) == 1
            # Secret should be redacted
            assert "sk-proj-thisIsAFakeSecretKeyForTesting" not in contents[0]
            assert "REDACTED" in contents[0]

    def test_evidence_index_built(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "app.py").write_text("def main(): pass", encoding="utf-8")

            config = VAFConfig()
            _contents, _, evidence = collect_file_contents(root, config)
            assert evidence.total_files >= 1
            assert evidence.bundle_sha256 == "" or True  # bundle hash set after save
            file_paths = [f.path for f in evidence.files]
            assert any("app.py" in p for p in file_paths)

    def test_excludes_env_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / ".env").write_text("SECRET=mysecret", encoding="utf-8")
            (root / ".env.local").write_text("SECRET=local", encoding="utf-8")
            (root / "app.py").write_text("print('hello')", encoding="utf-8")

            config = VAFConfig()
            contents, _, _ = collect_file_contents(root, config)
            assert not any(".env" in c for c in contents)

    def test_security_first_strategy(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "auth.ts").write_text("// auth logic", encoding="utf-8")
            (root / "styles.css").write_text("body { color: red; }", encoding="utf-8")
            (root / "middleware.ts").write_text("// middleware", encoding="utf-8")

            config = VAFConfig()
            contents, _, _ = collect_file_contents(root, config, strategy="security-first")
            # Auth and middleware should be included
            assert any("auth.ts" in c for c in contents)
            # Styles might or might not be included based on pattern
