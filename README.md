# MB Helper 🏆

[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white)](#)
[![Status](https://img.shields.io/badge/Steam%20Leaderboards-100%25%20Legal-22C55E?logo=steam&logoColor=white)](#)
[![Languages](https://img.shields.io/badge/Languages-ES%20%7C%20EN%20%7C%20PT--BR-FBBF24)](#)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](#)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](#)

**MB Helper** es una suite externa que incluye un **contador flotante (HUD) de duración de Powerups en tiempo real** y un **buscador de semillas récord de mapa** mediante lectura pasiva de memoria (`ReadProcessMemory`). Diseñada para la comunidad competitiva y speedrunners.

> [!IMPORTANT]
> **100% Legal para Steam Leaderboards:**
> El juego se ejecuta en estado **100% Vanilla (sin mods, sin BepInEx y sin DLLs inyectadas)**.
> La verificación antitrampas nativa (`CheckMods()`) aprueba todas tus partidas con total autenticidad y tus puntuaciones se publican con normalidad en el Ranking Mundial Oficial de Steam.

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
   - **HUD minimalista negro mate y números blancos** con esquinas redondeadas nativas por hardware (Windows 11 DWM).
   - Cronometra en vivo la duración y barra de progreso al recoger **Reloj (Time Freeze), Escudo, Furia, Velocidad (Haste) y Stonks**.
   - **Arquitectura de Cero Impacto en FPS:** Diseñado sin `WS_EX_LAYERED` para preservar el modelo **DirectX Independent Flip / MPO** de Windows; mantiene 144Hz / G-Sync estables sin desenfoque ni vibración de cámara.
   - Arrastrable a cualquier posición de la pantalla con guardado automático.
   - Atajo global **F6** para alternar visibilidad en cualquier momento durante la partida.
3. **🎯 4 Modos de Búsqueda Avanzados:**
   - **Modo 1 (Ítems):** Catálogo de los 88 ítems oficiales clasificados por rareza (Dorados, Épicos, Raros, Comunes) con búsqueda por texto en 3 idiomas. Busca hasta 3 ítems simultáneos garantizando vendedores distintos.
   - **Modo 2 (Vendedores Dorados):** Filtra partidas con 1, 2 o 3 vendedores legendarios (0.1% chance).
   - **Modo 3 (Específico):** Filtros cuantitativos exactos para Moáis, Maldiciones de Jefe, Microondas, Santuarios y Cofres.
   - **Modo 4 (Puntuación & Plantillas):** Algoritmo de scoring competitivo con rangos objetivos (*Perfect+*, *Perfect*, *Good*, *Light*) y presets rápidos (*Record Mundial*, *Lluvia de Moáis*, *2x Microondas*, etc.), combinable con ítems y dorados.
4. **⏸️ Pausa de Seguridad AFK Automática:**
   - Al encontrar la semilla objetivo, el bot envía automáticamente la señal de pausa (`Esc`) para proteger al jugador de enemigos mientras esté ausente.
5. **⚡ Atajos Globales de Baja Latencia (`F5` y `F6`):**
   - Sondeo asíncrono nativo (`GetAsyncKeyState`) que responde en menos de 20ms incluso con el juego en pantalla completa DirectX sin requerir Alt+Tab.
6. **🩺 Watchdog de Salud y Degradación de Memoria:**
   - Detecta si las recargas del motor se ralentizan tras partidas largas y avisa al usuario para reiniciar el juego y recuperar máxima velocidad.

---

## 🚀 Inicio Rápido / Quick Start

### Opción 1: Versión Portable (.exe sin instalación)
1. Descarga el archivo `MB_Helper_v1.0.0_Portable.zip` desde la sección [Releases](https://github.com/) del repositorio.
2. Descomprime la carpeta en cualquier ubicación.
3. Ejecuta `MB_Helper.exe`.

### Opción 2: Desde el Código Fuente (Python)
1. Clona el repositorio:
   ```bash
   git clone https://github.com/tu-usuario/mb-helper.git
   cd mb-helper
   ```
2. Instala dependencias opcionales (si se desea captura global con `keyboard`):
   ```bash
   pip install keyboard
   ```
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
4. **Buscador de Semillas:** Selecciona tu Modo objetivo (1, 2, 3 o 4) y configura tus requisitos.
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
├── build_release.py       # Script de empaquetado automático a PyInstaller y .zip
├── Iniciar_MB_Helper.bat  # Script de inicio rápido de 1 clic
└── README.md              # Documentación oficial
```

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
