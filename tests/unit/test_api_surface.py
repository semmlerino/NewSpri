"""Static checks for the supported public API boundary."""

from __future__ import annotations

import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
API_ROOTS = (
    PROJECT_ROOT / "config.py",
    PROJECT_ROOT / "sprite_viewer.py",
    PROJECT_ROOT / "coordinators",
    PROJECT_ROOT / "core",
    PROJECT_ROOT / "export",
    PROJECT_ROOT / "managers",
    PROJECT_ROOT / "sprite_model",
    PROJECT_ROOT / "ui",
    PROJECT_ROOT / "utils",
)


def _source_files() -> list[Path]:
    files: list[Path] = []
    for root in API_ROOTS:
        if root.is_file():
            files.append(root)
        else:
            files.extend(sorted(root.rglob("*.py")))
    return files


def _literal_all(tree: ast.Module) -> list[str] | None:
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        else:
            continue

        if any(isinstance(target, ast.Name) and target.id == "__all__" for target in targets):
            if node.value is None:
                continue
            value = ast.literal_eval(node.value)
            assert isinstance(value, list)
            assert all(isinstance(name, str) for name in value)
            return value
    return None


def _public_top_level_defs(tree: ast.Module) -> list[str]:
    names: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                names.append(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            names.extend(
                target.id
                for target in targets
                if (
                    isinstance(target, ast.Name)
                    and target.id.isupper()
                    and not target.id.startswith("_")
                    and target.id != "__all__"
                )
            )
    return names


def test_source_modules_define_explicit_all() -> None:
    missing = []
    for path in _source_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        if _literal_all(tree) is None:
            missing.append(path.relative_to(PROJECT_ROOT).as_posix())

    assert missing == []


def test_public_top_level_defs_are_listed_in_all() -> None:
    violations: dict[str, list[str]] = {}
    for path in _source_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        all_names = _literal_all(tree)
        assert all_names is not None

        missing = [name for name in _public_top_level_defs(tree) if name not in all_names]
        if missing:
            violations[path.relative_to(PROJECT_ROOT).as_posix()] = missing

    assert violations == {}
