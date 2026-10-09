"""Fail-closed, reproducible source release built ONLY from Git-tracked files.

Never archive local evidence, photos, credentials, untracked scratch folders or
evaluation output. GitHub Releases can attach this ZIP and its SHA-256 file.
No provider, network or external CI actions are performed here.
"""
from __future__ import annotations

from pathlib import Path, PurePosixPath
import hashlib
import json
import re
import subprocess
import time
import tomllib
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MAX_SOURCE_BYTES = 10_000_000
MANDATORY = {
    "README.md", "LICENSE", "SECURITY.md", "CONTRIBUTING.md",
    "CHANGELOG.md", "THIRD_PARTY_NOTICES.md", "docs/RELEASING.md",
}
SKIP_PREFIXES = (
    "evidence/", "eval/images/", "eval/results/", "test-results/",
    "playwright-report/", "node_modules/", ".venv/", ".git/",
)
SKIP_COMPONENTS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
SKIP_NAMES = {"BUILD_MANIFEST.json", ".coverage", ".DS_Store"}
SECRET = re.compile(
    r"(?m)^\s*-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----\s*$"
    r"|(?:sk-proj-|sk-or-v1-|github_pat_|ghp_|xox[baprs]-|AIzaSy)[A-Za-z0-9_-]{18,}"
)
TEXT_TYPES = {".md", ".py", ".ts", ".js", ".json", ".toml", ".yml", ".yaml", ".txt", ".css", ".html", ".svg"}
EXTRA_TEXT = {".env.example", ".gitignore", ".dockerignore"}


def git(*args: str) -> bytes:
    """Return a stable Git-index observation or fail closed."""
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, stderr=subprocess.PIPE)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RuntimeError("Git is required for a safe source release; no ZIP created.") from exc


def source_identity() -> tuple[str, int]:
    checkout = Path(git("rev-parse", "--show-toplevel").decode().strip()).resolve()
    if checkout != ROOT.resolve():
        raise RuntimeError("Release must run from the repository root, not a copied directory.")
    if git("status", "--porcelain", "--untracked-files=no").strip():
        raise RuntimeError("Tracked files are modified. Commit and qualify the exact release first.")
    sha = git("rev-parse", "HEAD").decode().strip()
    if not re.fullmatch(r"[a-f0-9]{40}", sha):
        raise RuntimeError("Invalid Git HEAD; refusing an untraceable release.")
    timestamp = int(git("show", "-s", "--format=%ct", "HEAD").decode().strip())
    return sha, timestamp


def tracked_sources() -> list[tuple[str, bytes]]:
    paths = sorted(
        entry.decode("utf-8") for entry in
        git("ls-files", "--cached", "-z").split(b"\0") if entry
    )
    if not MANDATORY.issubset(paths):
        raise RuntimeError("Missing required public project/release documents from the Git index.")
    seen: set[str] = set()
    files: list[tuple[str, bytes]] = []
    for name in paths:
        posix = PurePosixPath(name)
        if name in seen or posix.is_absolute() or ".." in posix.parts or name.startswith("/"):
            raise RuntimeError("Unsafe or repeated tracked file path.")
        seen.add(name)
        if (
            name.startswith(SKIP_PREFIXES) or any(p in SKIP_COMPONENTS for p in posix.parts)
            or posix.name in SKIP_NAMES
            or (posix.name.startswith(".env") and name != ".env.example")
            or posix.suffix.lower() in {".pem", ".key", ".p12", ".pfx", ".p8", ".sqlite", ".db"}
            or posix.name.lower() in {"id_rsa", "id_ed25519", "credentials.json", "secrets.json"}
        ):
            raise RuntimeError(f"Prohibited path is tracked: {name}. Remove it from Git before releasing.")
        file = ROOT.joinpath(*posix.parts)
        if file.is_symlink() or not file.is_file():
            raise RuntimeError(f"Missing/linked tracked release file: {name}")
        if file.stat().st_size > MAX_SOURCE_BYTES:
            raise RuntimeError(f"Oversized release source file: {name}")
        payload = file.read_bytes()
        if posix.suffix.lower() in TEXT_TYPES or name in EXTRA_TEXT:
            try:
                text = payload.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise RuntimeError(f"Invalid UTF-8 in tracked text file: {name}") from exc
            if SECRET.search(text):
                raise RuntimeError(f"Potential credential in tracked file: {name}. Review and rotate it.")
        files.append((name, payload))
    return files


def build_release(output_dir: Path | None = None) -> dict[str, object]:
    sha, timestamp = source_identity()
    package = json.loads((ROOT / "package.json").read_text())
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())
    version = package["version"]
    if version != project["project"]["version"] or not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise RuntimeError("Python/npm versions differ or are not a three-part release version.")
    files = tracked_sources()
    records = [
        {"path": name, "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
        for name, payload in files
    ]
    aggregate = hashlib.sha256(
        "\n".join(r["path"] + " " + r["sha256"] for r in records).encode()
    ).hexdigest()
    manifest = {
        "project": "GrimeQuest", "version": version, "git_sha": sha,
        "source_date_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(timestamp)),
        "scope": "Git-index-only source; no real photos, evidence or private data",
        "qualification": "See docs/MONSTER_RELEASE_AUDIT_20261009.md. Physical iPhone acceptance is separate.",
        "aggregate_sha256": aggregate, "files": records,
    }
    out = (output_dir or ROOT.parent).resolve()
    out.mkdir(parents=True, exist_ok=True)
    stem = f"GrimeQuest-v{version}-{sha[:8]}"
    archive = out / (stem + ".zip")
    temp = out / (stem + ".zip.tmp")
    # ZIP timestamps can only represent even seconds, and not before 1980.
    ziptime = time.gmtime(max(timestamp, 315532800))
    date = (ziptime.tm_year, ziptime.tm_mon, ziptime.tm_mday,
            ziptime.tm_hour, ziptime.tm_min, ziptime.tm_sec // 2 * 2)
    try:
        with zipfile.ZipFile(temp, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for name, payload in [
                *files, ("BUILD_MANIFEST.json", (json.dumps(manifest, indent=2) + "\n").encode())
            ]:
                info = zipfile.ZipInfo("grimequest/" + name, date_time=date)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                info.create_system = 3
                z.writestr(info, payload, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        with zipfile.ZipFile(temp) as z:
            if z.testzip() is not None:
                raise RuntimeError("ZIP integrity failure.")
            actual = set(z.namelist())
            expected = {"grimequest/" + name for name, _ in files} | {"grimequest/BUILD_MANIFEST.json"}
            if actual != expected:
                raise RuntimeError("Unexpected release ZIP members.")
            for record in records:
                if hashlib.sha256(z.read("grimequest/" + record["path"])).hexdigest() != record["sha256"]:
                    raise RuntimeError("Release archive content hash mismatch.")
        temp.replace(archive)
    finally:
        temp.unlink(missing_ok=True)
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    (out / (stem + ".sha256")).write_text(checksum + "  " + archive.name + "\n")
    result = {
        "archive": str(archive), "sha256_file": str(out / (stem + ".sha256")),
        "git_sha": sha, "version": version, "file_count": len(files),
        "bytes": archive.stat().st_size, "archive_sha256": checksum,
        "manifest_aggregate": aggregate,
    }
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    build_release()
