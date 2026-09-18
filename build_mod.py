import os
import subprocess
import shutil

def build_seed_scout():
    csc = r"C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\Roslyn\csc.exe"
    game_dir = r"C:\Program Files (x86)\Steam\steamapps\common\Megabonk"
    dotnet_dir = os.path.join(game_dir, "dotnet")
    core_dir = os.path.join(game_dir, r"BepInEx\core")
    interop_dir = os.path.join(game_dir, r"BepInEx\interop")
    plugins_dir = os.path.join(game_dir, r"BepInEx\plugins")

    os.makedirs(plugins_dir, exist_ok=True)

    refs = [
        os.path.join(dotnet_dir, "System.Private.CoreLib.dll"),
        os.path.join(dotnet_dir, "System.Runtime.dll"),
        os.path.join(dotnet_dir, "System.Collections.dll"),
        os.path.join(dotnet_dir, "System.Console.dll"),
        os.path.join(dotnet_dir, "System.Linq.dll"),
        os.path.join(dotnet_dir, "netstandard.dll"),

        os.path.join(core_dir, "BepInEx.Core.dll"),
        os.path.join(core_dir, "BepInEx.Unity.Common.dll"),
        os.path.join(core_dir, "BepInEx.Unity.IL2CPP.dll"),
        os.path.join(core_dir, "Il2CppInterop.Runtime.dll"),
        os.path.join(core_dir, "0Harmony.dll"),
        os.path.join(interop_dir, "Assembly-CSharp.dll"),
        os.path.join(interop_dir, "Il2Cppmscorlib.dll"),
        os.path.join(interop_dir, "Il2CppSystem.dll"),
        os.path.join(interop_dir, "UnityEngine.CoreModule.dll"),
        os.path.join(interop_dir, "UnityEngine.IMGUIModule.dll"),
        os.path.join(interop_dir, "UnityEngine.TextRenderingModule.dll"),
        os.path.join(interop_dir, "UnityEngine.InputLegacyModule.dll"),
    ]

    out_dll = "MegabonkSeedScout.dll"

    cmd = [
        csc,
        "/target:library",
        f"/out:{out_dll}",
        "/noconfig",
        "/nostdlib+",
        "/langversion:latest",
    ]
    for r in refs:
        cmd.append(f"/r:{r}")
    cmd.append("MegabonkSeedScout.cs")

    print("Compilando MegabonkSeedScout.cs con Roslyn...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    print("Codigo de salida:", res.returncode)
    if res.stdout:
        print("STDOUT:", res.stdout)
    if res.stderr:
        print("STDERR:", res.stderr)

    if os.path.exists(out_dll) and res.returncode == 0:
        target_path = os.path.join(plugins_dir, out_dll)
        shutil.copy2(out_dll, target_path)
        print(f"EXITO! Mod compilado e instalado en: {target_path}")
        print(f"Tamano del DLL: {os.path.getsize(out_dll)} bytes")
    else:
        print("ERROR: La compilacion fallo.")

if __name__ == "__main__":
    build_seed_scout()
