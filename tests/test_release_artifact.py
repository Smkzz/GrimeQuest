"""Release-packaging privacy, reproducibility and Git provenance regressions.

The isolated test image intentionally has no .git checkout. Git observations
are controlled fixtures; the actual release CLI requires a real clean Git tree.
"""
import hashlib
import json
from pathlib import Path
import zipfile

import pytest
from scripts import package_release as pkg


@pytest.fixture
def checked_out(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    sha = "f" * 40
    files = sorted([
        *pkg.MANDATORY, "package.json", "pyproject.toml", ".env.example",
        "client/casual.ts"
    ])
    for name in files:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if name == "package.json":
            text = '{"name":"grimequest-client","version":"0.1.0"}\n'
        elif name == "pyproject.toml":
            text = '[project]\nname="grimequest"\nversion="0.1.0"\n'
        else:
            text = f"SAFE TEST CONTENT {name}\n"
        path.write_text(text)
    # A deliberately untracked household photo + credential must NEVER ship.
    (root / "evidence").mkdir()
    (root / "evidence" / "private-actual-home.jpg").write_bytes(b"\xff\xd8PRIVATE")
    (root / ".env").write_text("GQ_PROVIDER_KEY=private-untracked-placeholder\n")
    responses = {
        ("rev-parse", "--show-toplevel"): str(root.resolve()).encode() + b"\n",
        ("status", "--porcelain", "--untracked-files=no"): b"",
        ("rev-parse", "HEAD"): sha.encode() + b"\n",
        ("show", "-s", "--format=%ct", "HEAD"): b"1791504000\n",
        ("ls-files", "--cached", "-z"): b"\0".join(x.encode() for x in files) + b"\0",
    }
    monkeypatch.setattr(pkg, "ROOT", root)
    monkeypatch.setattr(pkg, "git", lambda *a: responses[a])
    return root, responses, files


def test_source_archive_contains_exactly_tracked_files_with_manifest_and_hashes(checked_out, tmp_path):
    _, _, paths = checked_out
    result = pkg.build_release(tmp_path / "dist1")
    with zipfile.ZipFile(result["archive"]) as z:
        names = z.namelist()
        assert len(names) == len(paths) + 1
        assert set(names) == {"grimequest/" + p for p in paths} | {"grimequest/BUILD_MANIFEST.json"}
        assert all("evidence" not in n for n in names)
        assert all(not n.endswith(".env") for n in names)
        manifest = json.loads(z.read("grimequest/BUILD_MANIFEST.json"))
        assert manifest["git_sha"] == "f" * 40
        assert manifest["version"] == "0.1.0"
        assert len(manifest["files"]) == len(paths)
        for r in manifest["files"]:
            assert hashlib.sha256(z.read("grimequest/" + r["path"])).hexdigest() == r["sha256"]
    archive = Path(result["archive"])
    recorded = Path(result["sha256_file"]).read_text().split()[0]
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == recorded
    second = pkg.build_release(tmp_path / "dist2")
    assert Path(result["archive"]).read_bytes() == Path(second["archive"]).read_bytes()


def test_package_refuses_dirty_checkout(checked_out, tmp_path):
    _, responses, _ = checked_out
    responses[("status", "--porcelain", "--untracked-files=no")] = b" M README.md\n"
    with pytest.raises(RuntimeError, match="Tracked files are modified"):
        pkg.build_release(tmp_path / "out")


def test_package_refuses_tracked_secret(checked_out, tmp_path):
    root, _, _ = checked_out
    (root / "client" / "casual.ts").write_text("const leaked = 'sk-proj-" + "a" * 28 + "';\n")
    with pytest.raises(RuntimeError, match="Potential credential"):
        pkg.build_release(tmp_path / "out")


def test_package_refuses_tracked_private_evidence(checked_out, tmp_path):
    _, responses, files = checked_out
    with_evidence = sorted([*files, "evidence/private-actual-home.jpg"])
    responses[("ls-files", "--cached", "-z")] = b"\0".join(x.encode() for x in with_evidence) + b"\0"
    with pytest.raises(RuntimeError, match="Prohibited path"):
        pkg.build_release(tmp_path / "out")


def test_package_refuses_symlink_and_version_mismatch(checked_out, tmp_path):
    root, _, _ = checked_out
    (root / "pyproject.toml").write_text('[project]\nversion="9.9.9"\n')
    with pytest.raises(RuntimeError, match="Python/npm versions differ"):
        pkg.build_release(tmp_path / "out")
    (root / "pyproject.toml").write_text('[project]\nversion="0.1.0"\n')
    target = root / "client" / "casual.ts"
    target.unlink()
    target.symlink_to(root / "README.md")
    with pytest.raises(RuntimeError, match="Missing/linked"):
        pkg.build_release(tmp_path / "out")


def test_readme_local_links_and_required_release_files_exist():
    readme = (pkg.ROOT / "README.md").read_text()
    assert "docs/RELEASING.md" in readme
    for name in sorted(pkg.MANDATORY):
        assert (pkg.ROOT / name).is_file(), f"Missing public release file: {name}"
    assert (pkg.ROOT / ".github" / "workflows" / "ci.yml").is_file()
