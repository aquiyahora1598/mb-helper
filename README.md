# MB Helper 🏆

[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white)](#)
[![Status](https://img.shields.io/badge/Memoria-Lectura%20externa-22C55E)](#)
[![Languages](https://img.shields.io/badge/Languages-ES%20%7C%20EN%20%7C%20PT--BR-FBBF24)](#)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](#)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](#)

**MB Helper** es una suite externa que incluye un **contador flotante (HUD) de duración de Powerups en tiempo real** y un **buscador de semillas récord de mapa** mediante lectura pasiva de memoria (`ReadProcessMemory`). Diseñada para la comunidad competitiva y speedrunners.

> [!IMPORTANT]
> **Funcionamiento externo:**
> El lector usa `ReadProcessMemory` sin escribir memoria ni inyectar DLLs. El buscador automatiza entradas de teclado. Estas propiedades técnicas no constituyen una certificación de admisión en rankings o categorías competitivas.

---

## 🌐 Idiomas Soportados / Supported Languages / Idiomas Suportados
- 🇪🇸 **Español** (Nativo)
- 🇺🇸 **English** (Native)
- 🇧🇷 **Português (Brasil)** (Nativo)

*Todos los 88 ítems oficiales, interfaz y alertas del sistema están 100% traducidos y localizados.*

---

## 🌟 Características Principales / Key Features

1. **🛡️ 100% Externo y Pasivo (Cero Inyección):**
   - No altera archivos del juego ni inyecta DLLs.
   - Funciona externamente con llamadas estándar de Windows API (`ReadProcessMemory`).
2. **⏱️ Overlay Flotante de Powerups en Tiempo Real (`F6`):**
   - **HUD compacto negro mate, ajustado al tamaño de los números**, con esquinas redondeadas nativas (Windows 11 DWM).
   - Un contador por powerup activo, en una sola fila: **Reloj celeste, Escudo verde, Furia violeta, Velocidad naranja y Stonks dorado**. La caja se ensancha solo al agregar contadores, sin barras ni parpadeos.
   - Ventana sin `WS_EX_LAYERED`, lecturas en segundo plano y renderizado solo de valores modificados. El impacto real sobre FPS y frame pacing requiere medición con el juego.
   - Arrastrable a cualquier posición de la pantalla con guardado automático.
   - Atajo global **F6** para alternar visibilidad en cualquier momento durante la partida.
3. **🎯 3 Modos de Búsqueda:**
   - **Modo 1 (Ítems):** Catálogo de los 88 ítems oficiales clasificados por rareza (Dorados, Épicos, Raros, Comunes) con búsqueda por texto en 3 idiomas. Busca hasta 3 ítems simultáneos garantizando vendedores distintos.
   - **Modo 2 (Vendedores Dorados):** Filtra partidas con 1, 2 o 3 vendedores legendarios (0.1% chance).
   - **Modo 3 (Puntuación & Plantillas):** Algoritmo de scoring competitivo con rangos objetivos (*Perfect+*, *Perfect*, *Good*, *Light*) y presets rápidos (*Record Mundial*, *Lluvia de Moáis*, *2x Microondas*, etc.), combinable con ítems y dorados.
   - Sin límite automático de tiempo ni de intentos. El modo Custom fue retirado.
4. **⏸️ Pausa de Seguridad AFK Automática:**
   - Al encontrar la semilla objetivo, el bot envía automáticamente la señal de pausa (`Esc`) para proteger al jugador de enemigos mientras esté ausente.
5. **⚡ Atajos Globales de Baja Latencia (`F5` y `F6`):**
   - Sondeo asíncrono nativo (`GetAsyncKeyState`) que responde en menos de 20ms incluso con el juego en pantalla completa DirectX sin requerir Alt+Tab.
6. **🩺 Watchdog de Salud y Degradación de Memoria:**
   - Detecta si las recargas del motor se ralentizan tras partidas largas y avisa al usuario para reiniciar el juego y recuperar máxima velocidad.

---

## 🚀 Inicio Rápido / Quick Start

### Opción 1: Versión Portable (.exe sin instalación)
1. Descarga el archivo `MB_Helper_v1.1.0_Portable.zip` desde la [última versión portable](https://github.com/aquiyahora1598/mb-helper/releases/latest).
2. Descomprime la carpeta en cualquier ubicación.
3. Ejecuta `MB_Helper.exe`.

### Opción 2: Desde el Código Fuente (Python)
1. Clona el repositorio:
   ```bash
   git clone https://github.com/aquiyahora1598/mb-helper.git
   cd mb-helper
   ```
2. Los atajos y la entrada de teclado usan Win32 y no necesitan paquetes adicionales. Las dependencias para analizar videos son opcionales y están en `requirements-video.txt`.
3. Ejecuta con el lanzador rápido:
   ```bash
   Iniciar_MB_Helper.bat
   ```
   o directamente:
   ```bash
   python phantom_gui.py
   ```

---

## 🎮 Cómo Usar / How to Use
1. Abre **Steam** e inicia el juego.
2. Abre **MB Helper**. El estado indicará `● En Menu` o `● En Partida`.
3. **Contador de Powerups:** Pulsa **F6** para mostrar u ocultar el HUD flotante en cualquier momento. Arrástralo con el ratón a tu posición preferida.
4. **Buscador de Semillas:** Selecciona Ítems, Dorados o Plantillas y configura tus requisitos.
5. Entra a una partida y pulsa **F5** (o haz clic en `▶ INICIAR BÚSQUEDA`).
6. El bot reiniciará rápidamente hasta encontrar la semilla ganadora y pausará el juego automáticamente.

---

## 🏗️ Estructura del Proyecto / Project Structure

```text
├── assets/
│   └── item_icons/        # 88 Iconos oficiales de ítems
├── powerup_overlay.py     # HUD flotante nativo DirectX/DWM de cuenta regresiva (F6)
├── phantom_reader.py      # Lector de memoria pasivo con catálogo de 88 ítems (ES, EN, PT)
├── phantom_bot.py         # Módulo de reinicio ('R') y pausa AFK ('Esc') nativos
├── telemetry_logger.py    # Recolector de telemetría pasivo para análisis
├── phantom_gui.py         # Interfaz gráfica principal moderna (Dark Cybernetic)
├── menu_ui.py             # Menú, catálogo y tipografía; categorías sin números
├── search_config.py       # Validación y configuración inmutable del buscador
├── runtime_paths.py       # Recursos y datos persistentes de la versión portable
├── release_checks.py      # Comprobación aislada del ejecutable compilado
├── build_release.py       # Script de empaquetado automático a PyInstaller y .zip
├── Iniciar_MB_Helper.bat  # Script de inicio rápido de 1 clic
└── README.md              # Documentación oficial
```

---

## Auditoría y extracción de videos — octubre de 2026

La versión portable **1.1.0** incorpora el menú renovado, categorías sin números y con letra más grande, HUD compacto y correcciones de entrada de teclado, handles de 64 bits, concurrencia y persistencia de telemetría. Se retiraron Custom y los límites automáticos de tiempo e intentos. Ver [notas de la versión y compilación](docs/RELEASE_1.1.0.md).

- [Auditoría, validación y pendientes](docs/AUDITORIA_2026-10-06.md).
- [Últimas búsquedas y HUD compacto — 7/oct](docs/BUSQUEDAS_Y_HUD_2026-10-07.md).
- [Menú renovado, correcciones y mediciones — 7/oct](docs/MENU_Y_RENDIMIENTO_2026-10-07.md).
- [Extractor de video, perfil de Sheney y propuesta de guía](docs/VIDEO_Y_GUIA.md).
- `video_telemetry.py`: muestreo offline y OCR numérico opcional con evidencia por fotograma.
- `video_profiles/sheney_q0GJluxOWRY.json`: ROIs iniciales, pendientes de validación OCR.

Pruebas desde el código fuente en Windows:

```powershell
python -m unittest discover -s tests -v
```

El test de video se omite si OpenCV no está instalado. El OCR necesita un ejecutable Tesseract independiente.

---

## ⚖️ Descargo de Responsabilidad / Legal Disclaimer
- **Uso no oficial / Fan Project:** MB Helper es una herramienta comunitaria independiente y de código abierto sin fines de lucro. No está afiliada, respaldada ni asociada oficialmente con los desarrolladores ni editores de Megabonk.
- **Propiedad Intelectual:** Todos los nombres de ítems, iconos, sprites y marcas registradas de *Megabonk* pertenecen a sus respectivos creadores. Se utilizan exclusivamente bajo propósitos informativos y de referencia comunitaria (Fair Use).
- **Lectura Pasiva y Juego Limpio:** MB Helper no modifica archivos del juego en disco, no inyecta librerías DLL ni elude medidas técnicas de protección (DRM).

---

## 🤝 Créditos y Agradecimientos / Credits
- **ALuiell ([BonkScanner](https://github.com/ALuiell/BonkScanner)):** Agradecimiento especial por la investigación comunitaria de ingeniería inversa y análisis de offsets base de estructuras IL2CPP de Megabonk.
- **Comunidad de Megabonk:** Por las sugerencias de filtros y apoyo en la validación de semillas récord.

---

## 📜 Licencia / License
Este proyecto se distribuye bajo la licencia MIT. Consulta el archivo `LICENSE` para más detalles.
