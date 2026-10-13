# MB Helper 1.1.0 — 13 de octubre de 2026

## Cambios incluidos

- Menú renovado, texto del catálogo más grande y títulos en Segoe UI Semibold. Las categorías Ítems, Dorados y Plantillas aparecen sin números, con tipografía de 13 puntos.
- Catálogo con controles reutilizados, búsqueda por acentos y rareza, y selección de hasta tres ítems en vendedores distintos. Se conserva un único callback por precio.
- Custom retirado, junto con los límites automáticos de duración e intentos. Las plantillas siguen combinándose con ítems y vendedores dorados.
- Configuración capturada antes de buscar para evitar consultar variables de Tk desde el trabajador.
- HUD negro compacto, con un contador por efecto activo; aumenta su anchura al añadir efectos. Dinero dorado, escudo verde, daño violeta, tiempo celeste y velocidad naranja.
- Correcciones del lector de memoria de 64 bits, concurrencia, foco del juego, envío y liberación de teclas, restauración de prioridad y guardado de telemetría.
- Herramienta inicial de muestreo de videos y perfil de Sheney disponibles en el código fuente. La guía en tiempo real sigue siendo una etapa pendiente; el portable no incorpora OCR ni procesa videos durante una partida.

## Descargar y abrir

Descargar `MB_Helper_v1.1.0_Portable.zip` desde [GitHub Releases](https://github.com/aquiyahora1598/mb-helper/releases/latest), extraer la carpeta completa y abrir `MB_Helper/MB_Helper.exe`. No mover únicamente el EXE: necesita la carpeta `_internal`.

El archivo `.sha256` permite comprobar la integridad del ZIP. La versión anterior se conserva en sus propias descargas.

La nueva copia guarda `telemetry.db`, `megabonk_helper.log` y `overlay_position.json` junto al ejecutable. Para conservar datos de otra instalación, cerrar ambas copias y trasladar esos archivos a la carpeta del nuevo EXE; si existen archivos SQLite `-wal` o `-shm`, conservarlos junto a su base. El paquete publicado no incluye datos de partidas ni ajustes personales.

## Validación

38 pruebas automatizadas cubren menú, plantillas, precios, teclado, lector, HUD, telemetría y muestreo de video. Las pruebas usan entradas y lecturas del juego simuladas.

El proceso de compilación ejecuta además una comprobación sobre el EXE real: apertura y cierre de Tk, 88 iconos empaquetados, 87 ítems seleccionables, tres idiomas, tres modos, nueve plantillas, entrega de callbacks y cinco colores del HUD. Comprueba también que dos efectos produzcan dos contadores en una caja más ancha. Esta comprobación no abre una conexión al juego, no escucha atajos y no inicia telemetría.

No se han verificado los offsets contra una partida real de la versión actual de Megabonk ni el impacto sobre FPS, G-Sync o distintas escalas de pantalla.

## Reproducir la compilación en Windows x64

Compilación de esta versión: Python 3.14.5, PyInstaller 6.22.3 y hooks 2026.8. El código fuente conserva sintaxis compatible con Python 3.10.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe build_release.py --version 1.1.0
```

Resultados:

- `dist/v1.1.0/MB_Helper/MB_Helper.exe`
- `dist/MB_Helper_v1.1.0_Portable.zip`
- `dist/MB_Helper_v1.1.0_Portable.zip.sha256`
- `build/v1.1.0/build-check.json`

La compilación conserva las carpetas de versiones anteriores y rechaza reemplazar una copia que ya contenga registros o ajustes personales. El ZIP contiene exclusivamente el programa, sus recursos, licencia y documentación.

Comprobación aislada del portable:

```powershell
.\dist\v1.1.0\MB_Helper\MB_Helper.exe --check-build "$PWD\build\v1.1.0\manual-check.json"
```
