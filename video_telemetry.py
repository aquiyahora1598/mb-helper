"""Offline, auditable video sampling and numeric OCR. Never reads the game."""

import argparse
import csv
import io
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys


def parse_value(text, kind):
    """Reject ambiguous OCR instead of turning unreadable values into zero."""
    value = text.strip().replace(" ", "").replace(",", ".")
    if kind == "timer":
        if not re.fullmatch(r"\d{1,3}:\d{2}(?:\.\d+)?", value):
            return None
        minutes, seconds = value.split(":")
        return int(minutes) * 60 + float(seconds) if float(seconds) < 60 else None
    if kind == "integer":
        return int(value) if re.fullmatch(r"\d+", value) else None
    if kind in ("float", "percent", "multiplier"):
        suffix = {"float": "", "percent": "%", "multiplier": "x"}[kind]
        if suffix and value.lower().endswith(suffix):
            value = value[:-1]
        if not re.fullmatch(r"[+-]?\d+(?:\.\d+)?", value):
            return None
        result = float(value)
        if not math.isfinite(result):
            return None
        return result / 100 if kind == "percent" else result
    raise ValueError(f"Tipo de campo desconocido: {kind}")


def crop_bounds(roi, width, height):
    if len(roi) != 4 or any(not isinstance(v, (int, float)) or not math.isfinite(v) for v in roi):
        raise ValueError("ROI debe contener cuatro números finitos")
    x, y, w, h = roi
    if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > 1.000001 or y + h > 1.000001:
        raise ValueError("ROI normalizada fuera del fotograma")
    bounds = (round(x * width), round(y * height), round((x + w) * width), round((y + h) * height))
    if bounds[2] <= bounds[0] or bounds[3] <= bounds[1]:
        raise ValueError("ROI demasiado pequeña")
    return bounds


def load_profile(path):
    profile = json.loads(Path(path).read_text(encoding="utf-8"))
    if profile.get("schema_version") != 1:
        raise ValueError("Versión de perfil no compatible")
    if not isinstance(profile.get("fields"), dict) or not profile["fields"]:
        raise ValueError("Calibrá al menos una ROI en fields antes de ejecutar OCR")
    for name, field in profile["fields"].items():
        crop_bounds(field.get("roi", []), 1920, 1080)
        if field.get("kind") not in {"integer", "float", "timer", "percent", "multiplier"}:
            raise ValueError(f"Tipo incorrecto: {name}")
        confidence = field.get("min_confidence", 70)
        if not isinstance(confidence, (int, float)) or not math.isfinite(confidence) or not 0 <= confidence <= 100:
            raise ValueError(f"Confianza incorrecta: {name}")
    return profile


def recognize(crop, kind, executable, cv2):
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    if binary.mean() < 127:
        binary = cv2.bitwise_not(binary)
    ok, encoded = cv2.imencode(".png", binary)
    if not ok:
        raise RuntimeError("No se pudo codificar la región OCR")
    result = subprocess.run(
        [executable, "stdin", "stdout", "--psm", "7", "-c",
         "tessedit_char_whitelist=0123456789:.,%xX+-", "tsv"],
        input=encoded.tobytes(), capture_output=True, timeout=20,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if result.returncode:
        raise RuntimeError(result.stderr.decode("utf-8", errors="replace").strip())
    words, confidences = [], []
    for token in csv.DictReader(io.StringIO(result.stdout.decode("utf-8")), delimiter="\t"):
        if token.get("text", "").strip():
            words.append(token["text"])
            confidences.append(float(token["conf"]))
    text = " ".join(words)
    confidence = min(confidences) if confidences else 0.0
    return {"raw_text": text, "confidence": round(confidence, 2), "candidate": parse_value(text, kind)}


def sample_video(video, output, sample_fps=1, start=0, end=None, profile=None, tesseract="tesseract"):
    import cv2  # Optional; importing the main app never loads video libraries.

    if not math.isfinite(sample_fps) or not 0 < sample_fps <= 10:
        raise ValueError("fps debe estar entre 0 y 10")
    if not math.isfinite(start) or start < 0 or (end is not None and (not math.isfinite(end) or end <= start)):
        raise ValueError("Intervalo de video inválido")
    video = Path(video).resolve(strict=True)
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError("Usá una carpeta de salida vacía para conservar la evidencia anterior")
    executable = None
    if profile:
        executable = shutil.which(tesseract)
        if executable is None:
            raise RuntimeError("No se encontró Tesseract. Usá --tesseract con la ruta del ejecutable")
    capture = cv2.VideoCapture(str(video))
    if not capture.isOpened():
        raise ValueError("No se pudo abrir el video")
    try:
        source_fps = capture.get(cv2.CAP_PROP_FPS)
        if not math.isfinite(source_fps) or source_fps <= 0:
            raise ValueError("El video no informa una tasa de cuadros válida")
        output.mkdir(parents=True, exist_ok=True)
        frames = output / "frames"
        frames.mkdir(exist_ok=True)
        count = 0
        previous_index = -1
        with (output / "observations.jsonl").open("w", encoding="utf-8") as stream:
            while True:
                target_time = start + count / sample_fps
                if end is not None and target_time >= end:
                    break
                target_index = round(target_time * source_fps)
                if target_index <= previous_index:
                    raise ValueError("El muestreo supera la tasa de cuadros del video")
                if not capture.set(cv2.CAP_PROP_POS_FRAMES, target_index):
                    raise RuntimeError("El decodificador no admite posicionamiento por fotogramas")
                ok, frame = capture.read()
                if not ok:
                    break
                actual_index = round(capture.get(cv2.CAP_PROP_POS_FRAMES)) - 1
                if actual_index < 0 or actual_index <= previous_index:
                    raise RuntimeError("El decodificador devolvió una posición de fotograma inválida")
                previous_index = actual_index
                frame_file = frames / f"{count:06d}.jpg"
                if not cv2.imwrite(str(frame_file), frame, [cv2.IMWRITE_JPEG_QUALITY, 95]):
                    raise OSError("No se pudo guardar el fotograma")
                observation = {
                    "schema_version": 1, "source": "video", "source_file": str(video),
                    "source_url": profile.get("source_url") if profile else None,
                    "character_id": profile.get("character_id") if profile else None,
                    "game_version": profile.get("game_version") if profile else None,
                    "category": profile.get("category") if profile else None,
                    "video_time": round(actual_index / source_fps, 4),
                    "frame_index": actual_index, "frame_path": f"frames/{frame_file.name}",
                    "frame_size": [frame.shape[1], frame.shape[0]], "run_time": None,
                    "values": {}, "fields": {}, "needs_review": True,
                }
                for name, field in (profile or {}).get("fields", {}).items():
                    x1, y1, x2, y2 = crop_bounds(field["roi"], frame.shape[1], frame.shape[0])
                    found = recognize(frame[y1:y2, x1:x2], field["kind"], executable, cv2)
                    accepted = found["candidate"] is not None and found["confidence"] >= field.get("min_confidence", 70)
                    found.update({"roi": field["roi"], "accepted": accepted, "verified": False})
                    observation["fields"][name] = found
                    observation["values"][name] = found["candidate"] if accepted else None
                observation["run_time"] = observation["values"].get("run_time")
                # OCR acceptance is never human verification, even at confidence 100.
                stream.write(json.dumps(observation, ensure_ascii=False, allow_nan=False) + "\n")
                count += 1
        manifest = {
            "schema_version": 1, "source_file": str(video), "source_fps": source_fps,
            "sampling_fps": sample_fps, "start": start, "end": end, "frames": count,
            "profile": profile, "timestamp_method": "decoded frame index / source FPS (constant frame rate)",
        }
        (output / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        if not count:
            raise ValueError("No se extrajeron fotogramas del intervalo solicitado")
        return count
    finally:
        capture.release()


def main():
    parser = argparse.ArgumentParser(description="Muestrea videos y extrae números con evidencia revisable")
    parser.add_argument("video", help="Archivo de video local")
    parser.add_argument("--output", required=True)
    parser.add_argument("--fps", type=float, default=1)
    parser.add_argument("--start", type=float, default=0)
    parser.add_argument("--end", type=float)
    parser.add_argument("--profile", help="Perfil JSON con ROIs normalizadas")
    parser.add_argument("--tesseract", default="tesseract")
    args = parser.parse_args()
    try:
        profile = load_profile(args.profile) if args.profile else None
        count = sample_video(args.video, args.output, args.fps, args.start, args.end, profile, args.tesseract)
    except (ImportError, ValueError, RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
        parser.exit(1, f"Error: {exc}\n")
    print(f"{count} fotogramas guardados en {args.output}")


if __name__ == "__main__":
    main()
