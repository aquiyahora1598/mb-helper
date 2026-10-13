# Últimas búsquedas y HUD compacto — 7 de octubre de 2026

## Resultado de la auditoría del registro

La última sesión registrada es del **7 de octubre, 01:11:05–01:15:00**, en Modo 1, buscando **Yunque a 180 de oro como máximo**. Encontró uno a **131 de oro**, en el intento 126.

| Medida | Resultado |
| --- | --- |
| Duración desde START hasta STOP | 235 s (3 min 55 s) |
| Mapas evaluados | 126 |
| Ritmo global | 32,17 mapas/min |
| Intervalo medio entre evaluaciones consecutivas | 1,864 s |
| Ritmo habitual, excluyendo los cuatro intervalos ≥4 s | 1,636 s por mapa (~36,7/min) |
| Tiempo registrado de objetos de vendedores | 119 lecturas; mediana 63 ms; percentil 95: 65 ms |
| Promedio de ese tiempo, incluidos dos valores atípicos | 104,43 ms |
| Watchdogs de reinicio | 3 advertencias |
| Timeouts de vendedores | 1 |
| Pausas por cambio de foco registradas | 0 |

Los timestamps del registro tienen resolución de **un segundo**: los intervalos individuales de 1 o 2 s están redondeados. Los promedios sobre muchos mapas son más útiles. Los “63 ms” son el intervalo registrado desde la detección del mapa hasta la evaluación de ofertas; **no** representan toda la recarga ni una medición aislada del coste de leer memoria. El código calculaba ese valor antes del escaneo del tick, por lo que tampoco mide por sí solo cuándo terminó ese escaneo.

Los cuatro intervalos largos fueron:

| Intento evaluado | Intervalo desde el anterior | Evidencia |
| --- | --- | --- |
| 62 | 4 s | Sin diagnóstico concluyente en el registro |
| 78 | 7 s | Timeout de vendedores: 2391 ms, 0/2 ofertas listas |
| 80 | 10 s | Un watchdog; ofertas registradas a 2437 ms |
| 103 | 14 s | Dos watchdogs consecutivos |

Los cuatro intervalos suman **35 s**, aproximadamente **28,5 s más** que cuatro ciclos al ritmo habitual. Eso señala dónde buscar mejoras; no demuestra que todo ese tiempo pueda eliminarse, ni identifica una única causa para cada bloqueo.

## Comparación con sesiones anteriores

Sesiones largas recientes anteriores en el registro (21 de septiembre, Yunque ≤200 de oro):

| Inicio | Mapas | Duración | Mapas/min |
| --- | --- | --- | --- |
| 16:51:21 | 133 | 292 s | 27,33 |
| 16:57:08 | 69 | 140 s | 29,57 |
| 17:31:10 | 29 | 60 s | 29,00 |
| 17:48:45 | 292 | 825 s | 21,24 |
| **7/oct 01:11:05** | **126** | **235 s** | **32,17** |

La última búsqueda tiene buen ritmo frente al historial. No es una comparación controlada: variaron sesiones, mapas y el límite de precio. El número de intentos hasta encontrar el objeto también depende del azar y los filtros, no solamente de la velocidad del programa.

## Corrección de la espera de recarga

El código exigía haber observado el estado intermedio de generación/carga, incluso cuando ya había una **semilla nueva**, un mapa cargado e interactuables poblados. Como la pulsación de R bloquea brevemente al worker, es posible perder ese estado intermedio y esperar los 5 s del watchdog innecesariamente.

Ahora se admite el cambio de semilla como evidencia de recarga. Se mantienen la espera mínima existente de **1,10 s**, las comprobaciones de mapa cargado y de generación/carga finalizada. Una semilla igual o desconocida todavía requiere observar la transición. Es un fallo concreto del control de estado; el registro antiguo no basta para afirmar que causó todos los bloqueos listados.

Si el controlador no consigue enviar R, la búsqueda informa el problema y se detiene en lugar de esperar una recarga que no se solicitó. Las futuras recargas registran `PERF` con duración de la entrada R y tiempo total hasta aceptar el mapa en milisegundos. Esto permite medir la mejora sin adivinarla a partir de timestamps enteros.

No se redujeron a ciegas la duración de R, el margen de carga ni el timeout de vendedores. La prioridad es recuperar los bloqueos puntuales; reducir unas decenas de milisegundos tiene mucho menos impacto.

## HUD solicitado

- Una sola fila, sin nombres, iconos, barras, borde coloreado ni parpadeos.
- La caja se calcula con las medidas reales de la fuente: **73×32 px** con la escala de las pruebas, en lugar de 180×64 px. Mantiene tamaño de números; reduce el espacio sobrante.
- Con dos o más efectos se ensancha horizontalmente y muestra un contador por efecto. Se contrae al desaparecer; la altura no cambia.
- Dinero: dorado `#FFD700`; escudo: verde `#76FF03`; daño/furia: violeta `#B56CFF`; tiempo: celeste `#00E5FF`; velocidad: naranja `#FF9F1C`.
- Los colores identifican el tipo y permanecen iguales al acercarse a cero. El orden se mantiene estable: tiempo, escudo, daño, velocidad, dinero.
- Sin efectos muestra un único `00:00` neutro. F6 y arrastre conservan su funcionamiento.
- Elementos persistentes y actualizaciones solo al cambiar números, colores o cantidad de contadores. La ventana sigue sin transparencia layered y sin activación al hacer clic.

Las **29 pruebas automatizadas pasan**. La validación usa ventanas y métricas reales de Tk, pruebas de límites de texto y de estilos nativos, y simulaciones de recarga. Se comprobó una caja de 73×32 px con un contador y de 150×32 px con dos. Falta medir nuevas búsquedas y los powerups durante una partida real para cuantificar el efecto en ese equipo.

Los cambios están en el código fuente. Reiniciar la instancia ejecutada desde `Iniciar_MB_Helper.bat` permite usarlos; el ejecutable portable anterior conserva su versión compilada hasta volver a generarlo.
