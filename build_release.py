"""Build, check and package a versioned Windows portable release."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_VERSION = "1.1.0"


def build_exe(version=DEFAULT_VERSION):
    if not re.fullmatch(r"\d{1,4}\.\d{1,4}\.\d{1,4}", version):
        raise ValueError("Use a version such as 1.1.0")
    dist_root = BASE_DIR / "dist"
    version_dir = dist_root / f"v{version}"
    app_dir = version_dir / "MB_Helper"
    work_dir = BASE_DIR / "build" / f"v{version}"
    # PyInstaller can replace its output folder. Resolve it first and protect
    # persistent data from a previously used copy of this particular version.
    if not app_dir.resolve().is_relative_to(dist_root.resolve()):
        raise ValueError("Build output must stay inside the project dist folder")
    if app_dir.exists() and any(any(app_dir.glob(pattern))
                                for pattern in ("*.db*", "*.csv", "*.log", "overlay_position.json")):
        raise FileExistsError("This version contains user data. Move it aside before rebuilding.")
    work_dir.mkdir(parents=True, exist_ok=True)
    (work_dir / "tmp").mkdir(exist_ok=True)
    env = os.environ.copy()
    env.update(TEMP=str(work_dir / "tmp"), TMP=str(work_dir / "tmp"),
               PYINSTALLER_CONFIG_DIR=str(work_dir / "cache"))

    numeric_version = tuple(int(part) for part in version.split(".")) + (0,)
    version_file = work_dir / "version_info.txt"
    version_file.write_text(f"""VSVersionInfo(
  ffi=FixedFileInfo(filevers={numeric_version!r}, prodvers={numeric_version!r},
    mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[StringFileInfo([StringTable('040904B0', [
    StringStruct('FileDescription', 'MB Helper'),
    StringStruct('FileVersion', '{version}'),
    StringStruct('InternalName', 'MB_Helper'),
    StringStruct('OriginalFilename', 'MB_Helper.exe'),
    StringStruct('ProductName', 'MB Helper'),
    StringStruct('ProductVersion', '{version}')])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])])
""", encoding="utf-8")

    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--onedir", "--windowed",
           "--name", "MB_Helper", "--distpath", str(version_dir), "--workpath", str(work_dir),
           "--specpath", str(work_dir), "--version-file", str(version_file),
           "--add-data", f"{BASE_DIR / 'assets' / 'item_icons'};assets/item_icons",
           "--exclude-module", "keyboard", str(BASE_DIR / "phantom_gui.py")]
    print(f"[1/3] Building MB Helper {version}", flush=True)
    subprocess.run(cmd, cwd=BASE_DIR, env=env, check=True)

    print("[2/3] Checking the compiled executable without game input", flush=True)
    report_path = work_dir / "build-check.json"
    if report_path.exists():
        report_path.unlink()
    subprocess.run([str(app_dir / "MB_Helper.exe"), "--check-build", str(report_path)],
                   cwd=app_dir, env=env, check=True, timeout=60,
                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if not report.get("passed"):
        raise RuntimeError(f"Compiled executable check failed: {report_path}")

    for name in ("README.md", "LICENSE"):
        shutil.copy2(BASE_DIR / name, app_dir / name)
    shutil.copytree(BASE_DIR / "docs", app_dir / "docs", dirs_exist_ok=True)
    print("[3/3] Packaging the checked portable release", flush=True)
    zip_path = dist_root / f"MB_Helper_v{version}_Portable.zip"
    # Only application resources go into the ZIP, never logs, position or DBs.
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for name in ("MB_Helper.exe", "README.md", "LICENSE", "_internal", "docs"):
            path = app_dir / name
            paths = sorted(path.rglob("*")) if path.is_dir() else [path]
            for file in paths:
                if file.is_file():
                    archive.write(file, (Path("MB_Helper") / file.relative_to(app_dir)).as_posix())
    checksum = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    checksum_path = Path(str(zip_path) + ".sha256")
    checksum_path.write_text(f"{checksum}  {zip_path.name}\n", encoding="ascii")
    print(json.dumps({"executable": str(app_dir / "MB_Helper.exe"), "zip": str(zip_path),
                      "size_mb": round(zip_path.stat().st_size / (1024 * 1024), 2),
                      "sha256": checksum, "build_check": report}, indent=2), flush=True)
    return zip_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default=DEFAULT_VERSION)
    build_exe(parser.parse_args().version)
