"""
Script de Compilación Automatizada para MB Helper
Genera el ejecutable MB_Helper.exe y empaqueta el release portable en .zip para GitHub.
"""

import os
import sys
import shutil
import subprocess
import zipfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, "dist")
BUILD_DIR = os.path.join(BASE_DIR, "build")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

def build_exe():
    print("=== [1/3] Limpiando compilaciones anteriores ===")
    for folder in [DIST_DIR, BUILD_DIR]:
        if os.path.exists(folder):
            shutil.rmtree(folder, ignore_errors=True)
            print(f"Eliminado: {folder}")

    spec_file = os.path.join(BASE_DIR, "MB_Helper.spec")
    if os.path.exists(spec_file):
        os.remove(spec_file)

    print("\n=== [2/3] Ejecutando PyInstaller para MB_Helper ===")
    
    # Separador de paths para --add-data en Windows es ';'
    add_data_arg = f"{os.path.join('assets', 'item_icons')};{os.path.join('assets', 'item_icons')}"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name", "MB_Helper",
        "--add-data", add_data_arg,
        "--hidden-import", "keyboard",
        "--hidden-import", "telemetry_logger",
        "--hidden-import", "phantom_reader",
        "--hidden-import", "phantom_bot",
        "--hidden-import", "powerup_overlay",
        "--hidden-import", "audit_powerups",
        "phantom_gui.py"
    ]

    print("Comando:", " ".join(cmd))
    res = subprocess.run(cmd, cwd=BASE_DIR)
    if res.returncode != 0:
        print("[ERROR] Error en compilación PyInstaller")
        sys.exit(res.returncode)

    print("\n=== [3/3] Empaquetando Release Portable (.zip) ===")
    output_app_dir = os.path.join(DIST_DIR, "MB_Helper")
    
    # Copiar README si existe
    readme_path = os.path.join(BASE_DIR, "README.md")
    if os.path.exists(readme_path):
        shutil.copy2(readme_path, output_app_dir)

    # Crear archivo zip portable
    zip_path = os.path.join(DIST_DIR, "MB_Helper_v1.0.0_Portable.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(output_app_dir):
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, DIST_DIR)
                zipf.write(abs_path, rel_path)

    print(f"\n[OK] BUILD EXITOSA!")
    print(f"[OK] Carpeta de la App: {output_app_dir}")
    print(f"[OK] Paquete ZIP listo para GitHub Release: {zip_path} ({os.path.getsize(zip_path) / (1024*1024):.2f} MB)")

if __name__ == "__main__":
    build_exe()
