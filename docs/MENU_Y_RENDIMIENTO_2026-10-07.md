# Menú y auditoría de rendimiento — 7 de octubre de 2026

## Cambios visibles

- Navegación por Ítems, Dorados y Plantillas, con una paleta oscura uniforme y textos más claros.
- Catálogo adaptable a la anchura disponible, iconos compactos y filtros por rareza.
- Buscar por nombres en cualquiera de los tres idiomas o por nombre interno, sin distinguir acentos. `Ctrl+F` abre la búsqueda; `Escape` limpia el texto.
- Panel lateral permanente para los tres objetivos y sus precios. Su desplazamiento es independiente del catálogo.
- Rangos y nueve plantillas con selección destacada y requisitos generados desde las mismas definiciones que usa el evaluador.
- Botón de inicio/detención siempre accesible, herramientas en otra fila y estado con ajuste de línea. Se comprueban ventanas de 760×540 y 1160×820.
- Al buscar se bloquea la edición del objetivo; detener permite volver a editar. La búsqueda usa una copia de la configuración tomada al iniciar.

## Fallos encontrados y corregidos

1. **Validadores de precio acumulados.** Cada reconstrucción agregaba un callback y destruía la etiqueta anterior. En la reproducción, 16 reconstrucciones dejaron 16 callbacks y escribir un precio produjo 15 errores `invalid command name`. Ahora cada precio tiene un callback, se conserva la tarjeta y se elimina el callback al quitar el ítem.
2. **Reconstrucción completa del catálogo.** Escribir, seleccionar o cambiar de idioma destruía y creaba todos los botones. Ahora se conservan 87 botones (el catálogo tiene 88 entradas, pero la llave de ID 0 ya estaba excluida de selección). Solo se actualizan nombres/estados modificados; filtrar cambia su distribución. La escritura agrupa cambios durante 90 ms antes de filtrar.
3. **Lecturas de Tk en el trabajador de búsqueda.** Modo, precios, plantillas y combinaciones se consultaban desde el hilo del bot. Se capturan como valores de Python y mapas inmutables antes de arrancar; el trabajador ya no consulta esas variables de Tk.
4. **Precios inválidos ignorados.** Texto, negativos o decimales podían terminar interpretados como ausencia de límite. Ahora bloquean el inicio si se requieren esos ítems. Vacío o cero conservan el significado de sin límite. Se limita la entrada a nueve dígitos para evitar conversiones desmesuradas.
5. **Modo Custom retirado.** Se eliminaron su panel de filtros, sus variables y su evaluación. También se retiraron los límites automáticos de tiempo e intentos. Un identificador de modo retirado no puede iniciar una búsqueda.
6. **Probar reinicio.** El clic dejaba Helper en primer plano, pero el controlador rechazaba enviar R sin foco del juego. Ahora el ensayo enfoca el PID comprobado y ejecuta la pulsación en segundo plano. La interfaz sigue disponible y no permite iniciar una búsqueda mientras está pendiente el ensayo. Se comprobó con un controlador simulado; no se enviaron entradas al juego durante los tests.
7. **Trabajo bloqueante al iniciar.** Se quitaron pitidos síncronos duplicados y el calentamiento del heap desde el manejador del botón. El monitor conserva el calentamiento en segundo plano.
8. **Detalles duplicados de plantillas.** Los textos anteriores incluían probabilidades y tiempos sin medición, y no mostraban todos los requisitos del evaluador. Los nuevos detalles reflejan rango, puntuación y mínimos configurados, sin esas estimaciones.

## Mediciones

Python 3.14, Tk real en este equipo; juego, telemetría, HUD y trabajadores de entrada desactivados para aislar el menú. Se incluye `update_idletasks()` en cada medición.

| Operación | Antes | Después |
| --- | ---: | ---: |
| Actualizar catálogo completo sin cambiar datos, mediana de 12 repeticiones | 52,82 ms | 0,61 ms |
| Máximo observado de esa operación | 109,58 ms | 2,68 ms |
| Callbacks de un precio después de 16 renderizados | 16 | 1 |
| Errores al modificar ese precio | 15 | 0 |

Al alternar seis consultas de texto cinco veces, aplicar un filtro y distribuir sus resultados tuvo **4,75 ms de mediana**, con un máximo observado de **68,06 ms**. Esa medición fuerza el filtrado inmediatamente y **no incluye** la espera de agrupación de 90 ms al teclear. No hay una muestra previa equivalente de esta secuencia para atribuirle una mejora porcentual.

La construcción inicial observada fue de 1744,02 ms antes y 1973,43 ms después en una ejecución por versión. No demuestra una mejora de arranque; la reutilización adelanta la creación de controles para abaratar las interacciones posteriores. Son mediciones locales, con variación de sistema y fuentes, no una garantía de latencia ni de FPS durante el juego.

La ejecución final del script reproducible confirmó 0,31 ms de mediana para actualizar sin cambios y 2,12 ms para aplicar filtros; máximos de 0,86 y 29,73 ms, respectivamente. La construcción inicial en esa ejecución fue de 1338,80 ms. Los 87 controles se reutilizaron y modificar el precio dejó un callback activo y cero errores. La variación entre ejecuciones refuerza que no debe atribuirse un tiempo de arranque fijo a una única muestra.

Reproducir la medición actual:

```powershell
.\.venv\Scripts\python.exe tests/benchmark_menu.py
```

## Validación y límites

La suite tiene **38 pruebas automatizadas**: incluye las nueve plantillas con requisitos presentes y ausentes, rangos, los tres modos al iniciar/detener, precios, rechazo del modo retirado, selección máxima, búsqueda por acentos, conservación de controles, idiomas, tamaños, configuración inmutable evaluada desde otro hilo, ensayo de reinicio, HUD, memoria, teclado, telemetría y extracción de video. Se comprueba también sintaxis compatible con Python 3.10. Se retiraron las diez pruebas dedicadas al modo Custom eliminado.

Los tests utilizan controles nativos de Tk y datos simulados. No verifican offsets con una partida real, contenido de vendedores reales, FPS, G-Sync, varios monitores ni escalas de pantalla distintas. Tampoco se dispone de una captura visual utilizable del escritorio; se validan dimensiones y estados de controles, sin presentar una reconstrucción como captura real.

Los cambios están en `menu_ui.py`, `search_config.py` y `phantom_gui.py`. Abrir de nuevo `Iniciar_MB_Helper.bat` carga el nuevo menú desde fuente; los ejecutables portables existentes necesitan otra compilación. Se conservaron los cambios anteriores de auditoría y HUD.

## Búsquedas sin límite de duración

Por solicitud del usuario, se eliminaron el modo Custom y los límites de tiempo e intentos. Las tres pestañas disponibles son Ítems, Dorados y Plantillas. Se conservan las combinaciones de plantillas con ítems y vendedores dorados, y las validaciones de precios.

El buscador sigue reiniciando mientras no encuentre el objetivo y no se lo detenga con F5. Conserva las comprobaciones existentes de foco, fallos de entrada y degradación del juego. La pausa al encontrar una coincidencia también se conserva.

Los identificadores internos 1, 2 y 4 se mantienen para no alterar las rutas de búsqueda y los registros; Plantillas aparece como tercera pestaña en pantalla. Los detalles de las plantillas tienen sus propias traducciones y ya no dependen de los filtros de Custom.
