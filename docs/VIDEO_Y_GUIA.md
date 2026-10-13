# Extracción de videos y guía de partida

## Referencia inicial

[My BEST Megabonk Run (1.11M), de Sheney](https://www.youtube.com/watch?v=q0GJluxOWRY), duración publicada 2 h 53 min 13 s. Se descargó únicamente una muestra de los primeros 35 s para calibración. No se procesó la partida completa.

El video muestra una webcam a la izquierda, dos monedas en el encabezado, un reloj de partida y otro de etapa, además de contadores de interactuables abajo a la derecha. En el segundo 20 del video, el reloj de partida marca 00:07. En el segundo 34, marca 00:20. No debe alinearse la guía por el tiempo del archivo.

Los valores de **373,172** del encabezado y el oro amarillo de partida son campos diferentes. Las ROIs iniciales en `video_profiles/sheney_q0GJluxOWRY.json` apuntan al oro amarillo. El reloj central es tiempo **restante** de etapa y usa una clave distinta de `stage_time` del lector.

Personaje, versión y categoría quedan desconocidos hasta confirmarlos. El título del video es el título del autor; no constituye una verificación de récord ni de categoría.

## Lo que ya funciona

`video_telemetry.py` muestrea un archivo local a 1 FPS, guarda los fotogramas y produce:

- `observations.jsonl`: tiempo del video, índice del fotograma, ruta a la evidencia, dimensiones, valores reconocidos y estado de revisión.
- `manifest.json`: fuente, intervalo, frecuencia y perfil completo usado.
- `frames/`: evidencia visual conservada incluso cuando falla una lectura.

Con un perfil y Tesseract, el módulo también ejecuta OCR numérico de ROIs. Conserva texto original, confianza, valor candidato y valor aceptado. Un OCR ambiguo produce `null`, no cero. Los porcentajes se convierten a fracciones, como `12,5% → 0.125`, para compararlos con las estadísticas del lector.

La confianza OCR no es una probabilidad calibrada de exactitud: aunque se acepte un candidato, `verified` permanece falso y `needs_review` verdadero. Esta primera versión requiere revisión antes de usar sus resultados como referencia competitiva.

## Ejecutar

El entorno `.venv` del proyecto ya tiene instaladas las dependencias de muestreo y descarga. Para reconstruirlo:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-video.txt
```

Muestreo de la muestra existente:

```powershell
.\.venv\Scripts\python.exe video_telemetry.py video_output/reference_sample.mp4 --output video_output/nueva_muestra --fps 1 --end 35
```

La carpeta de salida debe estar vacía para proteger análisis anteriores. El resultado ya probado se encuentra en `video_output/reference_frames/`.

OCR con el perfil inicial:

```powershell
.\.venv\Scripts\python.exe video_telemetry.py video_output/reference_sample.mp4 --output video_output/primer_ocr --profile video_profiles/sheney_q0GJluxOWRY.json --end 35 --tesseract "C:\Program Files\Tesseract-OCR\tesseract.exe"
```

**Tesseract no está instalado en este equipo**. El reconocimiento real y los umbrales del perfil no se validaron. El comando anterior es el procedimiento para esa validación, no un resultado ya obtenido. No se instaló software de OCR en el sistema ni se integró OCR en el proceso del HUD.

El muestreo asigna tiempos por índice de cuadro/FPS; esta versión está pensada para videos de tasa constante. Archivos de tasa variable deben normalizarse antes o incorporar timestamps de presentación mediante FFmpeg/PyAV. Las ROIs son proporciones `[x, y, ancho, alto]`; cambiar el tamaño conservando el encuadre no exige recalcularlas, pero recortes, overlays nuevos o menús sí.

## Convertir observaciones en una guía útil

1. **Validar la lectura.** Revisar un conjunto de fotogramas de gameplay, pausa, subida de nivel y final de partida. Calibrar cada layout por separado y medir errores por campo. No existe una garantía de 100 % por detectar una pausa.
2. **Construir una referencia revisada.** Extraer checkpoints a los 30/60/180/300 s de partida, transiciones de etapa, compras y elecciones de armas/tomos. Mantener las imágenes y distinguir dato visible, desconocido e inferido.
3. **Comparar partidas equivalentes.** Agrupar por personaje, mapa, modo, categoría y versión. Comparar nivel, bajas y evolución de la build al mismo tiempo de partida. Oro disponible es contexto de compra, no productividad.
4. **Primera guía sin modelo.** Mostrar una diferencia concreta y su procedencia: “A 3:00: nivel 18 frente a 21 en la referencia”; “La referencia compró X antes de 2:30, si aparece y alcanza el oro”. Informar el número de referencias comparables. Evitar recomendar abandono con una sola run.
5. **Aprender con evidencia suficiente.** Incorporar runs normales y fallidas además de récords, etiquetas revisadas y una definición exacta del objetivo. Separar entrenamiento y evaluación por partida y por jugador; usar únicamente datos anteriores al checkpoint para evitar fuga de información.
6. **Integrar sin bloquear el HUD.** La guía consume snapshots en otro worker y entrega mensajes breves por la cola de la interfaz, a 1–2 Hz. Los videos y OCR se procesan offline; los temporizadores siguen leyendo el juego con su frecuencia actual.

Una colección de videos ganadores sirve para describir cómo progresan esas runs. Por sí sola no permite estimar la probabilidad de récord ni demostrar que una elección concreta causó el resultado.

El perfil inicial no incluye los 27 stats ni identificación de ítems. Esos campos necesitan observar un panel completo del video, segmentar sus apariciones y calibrar números/iconos. Los iconos existentes son una base para [template matching de OpenCV](https://docs.opencv.org/4.x/d4/dc6/tutorial_py_template_matching.html), pero deben validarse con el tamaño, escalado y compresión de la fuente.
