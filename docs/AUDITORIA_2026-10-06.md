# Auditoría de MB Helper — 6 de octubre de 2026

Se revisaron el lector, automatización, HUD, registro, interfaz, empaquetado y el modelo guardado. Las correcciones se hicieron sobre el código fuente. No se generó ni publicó un nuevo ejecutable; el contenido de `dist/` sigue siendo la compilación anterior.

## Errores corregidos

| Problema comprobado | Consecuencia | Corrección |
| --- | --- | --- |
| Escape enviaba eventos de scan code y virtual key para la misma pulsación | Riesgo de pausar y despausar al recibir dos eventos de teclado | Un solo key down y key up; liberación en `finally` y comprobación de `SendInput` |
| Reinicio no comprobaba el foco ni `quick_reset.enabled` | Podía enviar R a otra ventana o comunicar un reinicio que el juego no admite | Comprobación del PID en primer plano y del ajuste nativo; resultado verdadero solo si la entrada se envió |
| `focus_game()` devolvía éxito sin verificar el foco obtenido | Escape podía dirigirse a otra aplicación | Verificación posterior del PID activo |
| Firmas Win32 sin tipos explícitos | `ctypes` usa retornos enteros de 32 bits por defecto; los handles y tamaños podían truncarse en x64 | Firmas de proceso, memoria, HWND, GDI, DWM y teclado explícitas; comprobación de `INVALID_HANDLE_VALUE` |
| Cierre/reconexión del lector concurrente con recorridos de punteros | Una lectura podía atravesar dos estados diferentes del proceso | Exclusión mutua alrededor de la conexión y las lecturas completas |
| Enumeración de procesos en cada búsqueda | Trabajo repetido durante las recargas | Comprobación del handle vivo antes de enumerar |
| Resolución exhaustiva de clases al fallar offsets del HUD | Barrido del heap desde el hilo de Tk y bloqueos visibles | Lectura en un hilo propio; barrido limitado al diagnóstico explícito |
| Sustitución de `MyTime.time` por tiempo de etapa/partida | Tiempos restantes erróneos por usar relojes con orígenes distintos | Solo se usa el reloj del efecto; cero es válido y un fallo se informa como lectura inválida |
| Falta de identificación del powerup y efectos simultáneos ocultos | El jugador no sabía a qué efecto pertenecía el contador | Nombre del efecto principal y hasta cuatro tiempos adicionales; nombres ES/EN/PT |
| Advertencia de 3,5 s calculada pero ignorada por el HUD | No aparecía el estado amarillo hasta 2 s | Se aplica `is_warning` |
| Handles GDI/HWND sin tipos y posición negativa con sintaxis Tk | Fallos de recorte o movimiento en monitores a la izquierda | Tipos de 64 bits, HWND cacheado, coordenadas Win32 y límites del escritorio virtual |
| Prioridad del juego restaurada siempre a NORMAL | Cambiaba una configuración previa del usuario | Se conserva y restaura la clase original, incluido el cierre |
| Gracia por lectura inválida basada en el último guardado | Un resumen/exportación cambiaba cuándo terminaba una partida | Temporizador independiente de lecturas inválidas consecutivas de 10 s |
| Victoria inferida por durar 20 minutos | Etiquetas incorrectas en el dataset | Fin por pérdida de lectura = `interrupted`; no se infiere victoria por duración |
| Lectura inválida al morir reemplazaba estadísticas válidas con ceros | Pérdida de duración, nivel, bajas e inventario final | Se conservan los últimos datos válidos; Game Over repetido no inicia otra partida |
| Buffer retirado antes del commit y exportación concurrente con descarte | Riesgo de pérdida o reinserción de datos descartados | Transacción bajo bloqueo; se vacía el buffer después del commit |
| El hilo dormía 5 s y el cierre esperaba solo 2 s | Registro todavía vivo durante el cierre | Espera interrumpible, unión del hilo antes de guardar; cierre cancelado si falla el guardado |
| Archivos persistentes junto a `__file__` en PyInstaller | Posición y telemetría podían quedar en `_internal` | Directorio del ejecutable para datos de la versión portable |
| Nivel inicial 0 convertido a 1 | Primeros checkpoints desplazados | El lector admite nivel 0, visible en la muestra del video |
| Ítem duplicado en un vendedor conservaba el último precio | Se rechazaba una oferta barata válida o se aceptaba un precio desconocido bajo un tope | Se elige el menor precio conocido; los topes exigen precio confirmado y vendedores distintos |
| Diagnóstico de powerups dejaba su lector abierto | Handles acumulados al repetir auditorías | Cierre del lector en `finally` |

Las actualizaciones del HUD conservan los elementos de Canvas y comparan valores antes de modificarlos. Las lecturas de memoria no se ejecutan desde su temporizador gráfico. Las acciones F5/F6 y actualizaciones provenientes de otros hilos se entregan por una cola a Tk.

## Validación

- 22 pruebas de regresión aprobadas en Windows, con Python 3.14.5.
- Inicio, entrega de actualizaciones y cierre de la interfaz completa con un lector simulado, sin tocar el juego ni la base de datos del usuario.
- Ventana Tk real: estilos sin `WS_EX_LAYERED`, con `WS_EX_NOACTIVATE`, estado de advertencia, filas adicionales y cero modificaciones de Canvas para datos idénticos o reposo repetido.
- Pruebas de teclado con `SendInput` simulado: no se enviaron teclas reales al juego durante las pruebas.
- Video sintético: tiempos de muestreo, persistencia de evidencia y rechazo de salida ocupada.
- Video de Sheney: 35 fotogramas de los primeros 35 s en 1920×1080; inspección visual de fotogramas de los segundos 20 y 34.

Para reproducir:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

La prueba de muestreo requiere las dependencias opcionales de video. Las demás pruebas usan la biblioteca estándar de Python y Tk de Windows.

No se verificaron los offsets contra una partida real ni el impacto del HUD sobre FPS, G-Sync o frame pacing. La captura del HUD mediante GDI no devolvió una imagen utilizable en este entorno; no se entrega una captura como si fuera una validación visual de pantalla. Los tests de Tk sí verifican los widgets y estilos reales.

## Diferencias respecto del informe técnico

1. El modelo guardado tiene 49 variables, incluidas métricas de los minutos **3 y 5**. No corresponde a un predictor de los primeros 60 s y no se carga para inferencia en `phantom_gui.py`.
2. El script de entrenamiento en `scratch/analyze_telemetry.py` usa una etiqueta heurística por bajas, oro y duración. No utiliza `is_record` como objetivo. La base inspeccionada contiene **97 partidas, 23.513 snapshots y ninguna partida marcada como récord**. Esto impide evaluar un clasificador real de récord usando esas etiquetas.
3. El oro leído es **saldo actual**, no oro acumulado: las compras reducen ese valor. Dividirlo por tiempo no mide producción de oro.
4. Los umbrales implementados son Perfect+ ≥30 con condiciones, Perfect ≥25 con condiciones, Good ≥20 y Light ≥14. El informe menciona 24/18/12. Se preservó el algoritmo existente; cambiar sus reglas exige decidir qué criterio se quiere usar.
5. El watchdog actual considera recargas mayores de 4,2 s/promedio de 4,5 s, distinto de los 800 ms del informe. Una recarga lenta por sí sola no demuestra fragmentación de memoria.
6. Las latencias absolutas, “cero impacto en FPS”, persistencia de MPO y certificación de admisión competitiva no quedan demostradas por el código. Evitar ventanas layered es una decisión implementada; su efecto real debe medirse en el equipo objetivo.

Microsoft describe las [condiciones y límites del redondeo de ventanas](https://learn.microsoft.com/en-us/windows/apps/desktop/modernize/ui/apply-rounded-corners); una preferencia DWM no es una garantía sobre la presentación de DirectX.

## Pendientes con impacto en la siguiente etapa

- Versionar offsets y comprobar la versión de `GameAssembly.dll` antes de tratarlos como fiables.
- **Resuelto el 7/oct:** la configuración del buscador se captura como datos de Python al iniciar; las evaluaciones del worker usan esa copia. Ver [auditoría del menú](MENU_Y_RENDIMIENTO_2026-10-07.md).
- Separar “Game Over” de victoria/derrota usando señales verificadas del juego. Se eliminó la victoria por duración, pero la interpretación del flag terminal sigue dependiendo del offset existente.
- Registrar mapa, etapa, modo, versión, compras, oro generado y etiquetas de resultado revisadas para comparar runs equivalentes.
- Detectar reinicios aunque el bot pierda el inicio de la siguiente partida; el criterio actual todavía exige que el reloj nuevo sea ≤10 s.
- Excluir o condensar snapshots repetidos por pausa y estudiar cómo eso afectó al dataset histórico. Los datos anteriores se conservaron.
- Limitar el tamaño del log y evitar escrituras síncronas frecuentes durante búsquedas largas.
- Validar el HUD con 100/150/200 % de escala, varios monitores y una partida real antes de distribuir.

La propuesta de extracción y guía está en `docs/VIDEO_Y_GUIA.md`.

Actualización del 7 de octubre: el análisis de las últimas búsquedas y el nuevo HUD de contadores compactos están en [BUSQUEDAS_Y_HUD_2026-10-07.md](BUSQUEDAS_Y_HUD_2026-10-07.md). Esa actualización reemplaza el diseño de HUD descrito en esta auditoría.
