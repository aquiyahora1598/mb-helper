using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;
using UnityEngine;
using BepInEx;
using BepInEx.Configuration;
using BepInEx.Logging;
using BepInEx.Unity.IL2CPP;
using Il2CppInterop.Runtime.Injection;
using Assets.Scripts.Inventory__Items__Pickups.Items;
using Assets.Scripts.Inventory__Items__Pickups.Chests;
using Assets.Scripts.Inventory__Items__Pickups.Interactables;
using Assets.Scripts.Managers;
using Assets.Scripts.Actors.Player;

namespace MegabonkSeedScout
{
    public enum ScoutMode
    {
        DualVendor_SoulHarvester_And_Magnet = 0,
        SingleItem_SoulHarvester = 1,
        AnyGoldenVendor = 2,
        CustomSelectedItems = 3
    }

    [BepInPlugin("com.facu.megabonkseedscout", "Megabonk Seed Scout", "1.1.2")]
    public class Plugin : BasePlugin
    {
        public static Plugin Instance { get; private set; }
        public static ManualLogSource LogSource { get; private set; }

        public static ConfigEntry<ScoutMode> ConfigScoutMode;
        public static ConfigEntry<string> ConfigCustomItems;
        public static ConfigEntry<string> ConfigTargetItem1;
        public static ConfigEntry<string> ConfigTargetItem2;
        public static ConfigEntry<float> ConfigScanDelay;
        public static ConfigEntry<bool> ConfigPlayAlertSound;
        public static ConfigEntry<bool> ConfigShowHud;
        public static ConfigEntry<bool> ConfigShowMapTracker;
        public static ConfigEntry<float> ConfigWindowX;
        public static ConfigEntry<float> ConfigWindowY;
        public static ConfigEntry<float> ConfigMapTrackerX;
        public static ConfigEntry<float> ConfigMapTrackerY;
        public static ConfigEntry<KeyCode> ConfigKeyStart;
        public static ConfigEntry<KeyCode> ConfigKeyPause;
        public static ConfigEntry<KeyCode> ConfigKeyToggleHud;
        public static ConfigEntry<KeyCode> ConfigKeyCycleMode;
        public static ConfigEntry<KeyCode> ConfigKeyToggleMapTracker;

        public override void Load()
        {
            Instance = this;
            LogSource = Log;

            ConfigScoutMode = Config.Bind("1. General", "ModoDeBusqueda", ScoutMode.CustomSelectedItems,
                "Modo: DualVendor_SoulHarvester_And_Magnet, SingleItem_SoulHarvester, AnyGoldenVendor, CustomSelectedItems");

            ConfigCustomItems = Config.Bind("1. General", "ItemsPersonalizados", "SoulHarvester,SuckyMagnet",
                "Lista de items seleccionados por el usuario para el modo personalizado (separados por coma)");

            ConfigTargetItem1 = Config.Bind("1. General", "ItemObjetivo1", "SoulHarvester,Cosechador",
                "Palabras clave para el primer item en modos rapidos");

            ConfigTargetItem2 = Config.Bind("1. General", "ItemObjetivo2", "SuckyHoof,SuckyMagnet,Magnet,Iman",
                "Palabras clave para el segundo item en modo dual");

            ConfigScanDelay = Config.Bind("2. Ajustes", "RetardoEscaneoSegundos", 0.45f,
                "Tiempo en segundos a esperar tras cargar el mapa antes de evaluar vendedores");

            ConfigPlayAlertSound = Config.Bind("2. Ajustes", "SonidoDeAlerta", true,
                "Reproducir alerta sonora de Windows al hallar la semilla récord");

            ConfigShowHud = Config.Bind("2. Ajustes", "MostrarHUD", true,
                "Mostrar panel de control en pantalla");

            ConfigShowMapTracker = Config.Bind("2. Ajustes", "MostrarIndicadorMapa", true,
                "Mostrar el panel indicador de contenido de la partida (cofres, vasijas, etc.)");

            ConfigWindowX = Config.Bind("2. Ajustes", "PosicionX", -1f,
                "Posicion horizontal del panel principal");

            ConfigWindowY = Config.Bind("2. Ajustes", "PosicionY", -1f,
                "Posicion vertical del panel principal");

            ConfigMapTrackerX = Config.Bind("2. Ajustes", "PosicionMapaX", -1f,
                "Posicion horizontal del panel indicador de mapa");

            ConfigMapTrackerY = Config.Bind("2. Ajustes", "PosicionMapaY", -1f,
                "Posicion vertical del panel indicador de mapa");

            ConfigKeyStart = Config.Bind("3. Atajos", "TeclaIniciar", KeyCode.F5,
                "Tecla para iniciar / reanudar busqueda automatica");

            ConfigKeyPause = Config.Bind("3. Atajos", "TeclaPausar", KeyCode.F6,
                "Tecla para pausar / cancelar busqueda automatica");

            ConfigKeyToggleHud = Config.Bind("3. Atajos", "TeclaOcultarHUD", KeyCode.F7,
                "Tecla para mostrar u ocultar la interfaz HUD");

            ConfigKeyCycleMode = Config.Bind("3. Atajos", "TeclaCambiarModo", KeyCode.F8,
                "Tecla para alternar el modo de busqueda");

            ConfigKeyToggleMapTracker = Config.Bind("3. Atajos", "TeclaIndicadorMapa", KeyCode.F9,
                "Tecla para mostrar u ocultar el indicador de contenido de la partida");

            if (!ClassInjector.IsTypeRegisteredInIl2Cpp(typeof(ScoutController)))
                ClassInjector.RegisterTypeInIl2Cpp<ScoutController>();

            GameObject scoutObj = new GameObject("MegabonkSeedScoutController");
            scoutObj.AddComponent<ScoutController>();
            UnityEngine.Object.DontDestroyOnLoad(scoutObj);

            Log.LogInfo("=== Megabonk Seed Scout & Map Tracker v1.1.2 cargado con exito ===");
        }
    }

    public class ItemCatalogEntry
    {
        public EItem eItem;
        public string idName;
        public string spanishName;
        public EItemRarity rarity;
        public Texture icon;
    }

    public class MapContentStats
    {
        public int BossCurses = 0;
        public int BossCursesMax = 0;

        public int ChallengesDone = 0;
        public int ChallengesTotal = 0;

        public int ChargeShrinesDone = 0;
        public int ChargeShrinesTotal = 0;

        public int ChestsOpened = 0;
        public int ChestsTotal = 0;

        public int GreedShrinesDone = 0;
        public int GreedShrinesTotal = 0;

        public int MagnetShrinesDone = 0;
        public int MagnetShrinesTotal = 0;

        public int MicrowavesDone = 0;
        public int MicrowavesTotal = 0;

        public int MoaisDone = 0;
        public int MoaisTotal = 0;

        public int PotsSmashed = 0;
        public int PotsTotal = 0;

        public int ShadyGuysTotal = 0;
        public int ShadyGuysGolden = 0;
    }

    // Clase estatica separada para no registrar en IL2CPP y evitar advertencias de tipos
    public static class VendorMatcher
    {
        public static InteractableShadyGuy[] FindMatch(InteractableShadyGuy[] vendors, List<EItem> targets)
        {
            if (vendors == null || targets == null || targets.Count == 0 || vendors.Length < targets.Count)
                return null;

            if (targets.Count == 1)
            {
                foreach (var v in vendors)
                {
                    if (VendorOffersItem(v, targets[0])) return new InteractableShadyGuy[] { v };
                }
                return null;
            }
            if (targets.Count == 2)
            {
                for (int i = 0; i < vendors.Length; i++)
                {
                    if (!VendorOffersItem(vendors[i], targets[0])) continue;
                    for (int j = 0; j < vendors.Length; j++)
                    {
                        if (i == j) continue;
                        if (VendorOffersItem(vendors[j], targets[1]))
                        {
                            return new InteractableShadyGuy[] { vendors[i], vendors[j] };
                        }
                    }
                }
                return null;
            }
            if (targets.Count == 3)
            {
                for (int i = 0; i < vendors.Length; i++)
                {
                    if (!VendorOffersItem(vendors[i], targets[0])) continue;
                    for (int j = 0; j < vendors.Length; j++)
                    {
                        if (i == j || !VendorOffersItem(vendors[j], targets[1])) continue;
                        for (int k = 0; k < vendors.Length; k++)
                        {
                            if (k == i || k == j) continue;
                            if (VendorOffersItem(vendors[k], targets[2]))
                            {
                                return new InteractableShadyGuy[] { vendors[i], vendors[j], vendors[k] };
                            }
                        }
                    }
                }
                return null;
            }
            return null;
        }

        public static bool VendorOffersItem(InteractableShadyGuy shady, EItem target)
        {
            if (shady == null || shady.items == null) return false;
            foreach (ItemData it in shady.items)
            {
                if (it != null && it.eItem == target) return true;
            }
            return false;
        }
    }

    public class ScoutController : MonoBehaviour
    {
        [DllImport("user32.dll")]
        private static extern bool MessageBeep(uint uType);

        public ScoutController(IntPtr ptr) : base(ptr) { }

        // Estado del buscador
        public static bool IsAutoResetActive = false;
        public static int AttemptCount = 0;
        public static string StatusText = "Listo. Presiona [F5] para iniciar busqueda.";
        public static bool MatchFound = false;
        public static List<string> MatchDetails = new List<string>();

        private float _timeSincePlayerSpawned = 0f;
        private bool _evaluatedCurrentMap = false;

        // Ventana Principal
        private Rect _windowRect = new Rect(20f, 320f, 480f, 200f);
        private bool _isDraggingMain = false;
        private Vector2 _dragOffsetMain = Vector2.zero;

        // Ventana Indicador de Mapa
        private Rect _mapTrackerRect = new Rect(20f, 530f, 260f, 290f);
        private bool _isDraggingMap = false;
        private Vector2 _dragOffsetMap = Vector2.zero;

        // Ventana Selector de Items
        private bool _showItemPicker = false;
        private Rect _pickerRect = new Rect(100f, 100f, 750f, 520f);
        private bool _isDraggingPicker = false;
        private Vector2 _dragOffsetPicker = Vector2.zero;
        private int _pickerRarityTab = 0; // 0: Todos, 1: Dorados, 2: Epicos, 3: Raros, 4: Comunes
        private int _pickerPage = 0;
        private const int ItemsPerPage = 24;

        // Catalogo de items
        private static List<ItemCatalogEntry> _catalog = new List<ItemCatalogEntry>();
        private static Dictionary<EItem, ItemCatalogEntry> _catalogDict = new Dictionary<EItem, ItemCatalogEntry>();
        private static bool _catalogLoaded = false;
        private List<EItem> _selectedItems = new List<EItem>();

        // Monitoreo del Mapa
        private MapContentStats _mapStats = new MapContentStats();
        private float _lastStatsScanTime = 0f;
        private int _initialPotsCount = 0;
        private bool _mapInitialized = false;

        // Recursos visuales
        private Font _gameFont = null;

        // Estilos GUI
        private GUIStyle _titleStyle;
        private GUIStyle _subTitleStyle;
        private GUIStyle _badgeStyle;
        private GUIStyle _labelWhite;
        private GUIStyle _labelMuted;
        private GUIStyle _labelGreen;
        private GUIStyle _btnStyle;
        private GUIStyle _btnHighlightStyle;
        private GUIStyle _mapRowNameStyle;
        private GUIStyle _mapRowCountStyle;
        private bool _stylesInitialized = false;
        private bool _positionsInitialized = false;

        private void Start()
        {
            _timeSincePlayerSpawned = 0f;
            _evaluatedCurrentMap = false;
            LoadSelectedItemsFromConfig();
            InitItemCatalog();
        }

        private void LoadSelectedItemsFromConfig()
        {
            _selectedItems.Clear();
            string raw = Plugin.ConfigCustomItems.Value;
            if (!string.IsNullOrEmpty(raw))
            {
                string[] parts = raw.Split(new char[] { ',', ';' }, StringSplitOptions.RemoveEmptyEntries);
                foreach (string p in parts)
                {
                    string clean = p.Trim();
                    if (Enum.TryParse<EItem>(clean, true, out EItem parsed))
                    {
                        if (!_selectedItems.Contains(parsed) && _selectedItems.Count < 3)
                            _selectedItems.Add(parsed);
                    }
                }
            }
        }

        private void SaveSelectedItemsToConfig()
        {
            List<string> names = new List<string>();
            foreach (EItem it in _selectedItems)
            {
                names.Add(it.ToString());
            }
            Plugin.ConfigCustomItems.Value = string.Join(",", names);
        }

        private void Update()
        {
            // Atajos de teclado
            if (Input.GetKeyDown(Plugin.ConfigKeyStart.Value))
            {
                StartSearch();
            }
            if (Input.GetKeyDown(Plugin.ConfigKeyPause.Value))
            {
                PauseSearch();
            }
            if (Input.GetKeyDown(Plugin.ConfigKeyToggleHud.Value))
            {
                Plugin.ConfigShowHud.Value = !Plugin.ConfigShowHud.Value;
            }
            if (Input.GetKeyDown(Plugin.ConfigKeyToggleMapTracker.Value))
            {
                Plugin.ConfigShowMapTracker.Value = !Plugin.ConfigShowMapTracker.Value;
            }

            // Cargar catalogo si aun no se cargo (se ejecuta incluso en el menu de Megabonk)
            if (!_catalogLoaded)
            {
                InitItemCatalog();
            }

            // Comprobar estado del jugador en partida
            MyPlayer player = UnityEngine.Object.FindObjectOfType<MyPlayer>();
            bool isInGame = (player != null);

            if (!isInGame)
            {
                _timeSincePlayerSpawned = 0f;
                _evaluatedCurrentMap = false;
                _mapInitialized = false;
                return;
            }

            _timeSincePlayerSpawned += Time.deltaTime;

            // Evaluar mapa en busqueda automatica tras retardo
            if (IsAutoResetActive && !_evaluatedCurrentMap)
            {
                if (_timeSincePlayerSpawned >= Plugin.ConfigScanDelay.Value)
                {
                    EvaluateCurrentMap();
                }
            }

            // Actualizar estadisticas del mapa cada 0.35 segundos
            if (Plugin.ConfigShowMapTracker.Value && (Time.time - _lastStatsScanTime >= 0.35f))
            {
                _lastStatsScanTime = Time.time;
                UpdateMapStats();
            }
        }

        private void UpdateMapStats()
        {
            try
            {
                bool usedOfficialTracker = false;

                // 1. Intentar leer del rastreador oficial interno de Megabonk (InteractablesStatus)
                try
                {
                    var dict = InteractablesStatus.interactablesByName;
                    if (dict != null && dict.Count > 0)
                    {
                        foreach (var kvp in dict)
                        {
                            string k = kvp.Key != null ? kvp.Key.ToLower() : "";
                            var c = kvp.Value;
                            if (c == null) continue;

                            if (k.Contains("curse"))
                            {
                                _mapStats.BossCurses = c.numUsed;
                                _mapStats.BossCursesMax = c.numTotal;
                                usedOfficialTracker = true;
                            }
                            else if (k.Contains("challenge"))
                            {
                                _mapStats.ChallengesDone = c.numUsed;
                                _mapStats.ChallengesTotal = c.numTotal;
                                usedOfficialTracker = true;
                            }
                            else if (k.Contains("charge"))
                            {
                                _mapStats.ChargeShrinesDone = c.numUsed;
                                _mapStats.ChargeShrinesTotal = c.numTotal;
                                usedOfficialTracker = true;
                            }
                            else if (k.Contains("chest"))
                            {
                                _mapStats.ChestsOpened = c.numUsed;
                                _mapStats.ChestsTotal = c.numTotal;
                                usedOfficialTracker = true;
                            }
                            else if (k.Contains("greed"))
                            {
                                _mapStats.GreedShrinesDone = c.numUsed;
                                _mapStats.GreedShrinesTotal = c.numTotal;
                                usedOfficialTracker = true;
                            }
                            else if (k.Contains("magnet"))
                            {
                                _mapStats.MagnetShrinesDone = c.numUsed;
                                _mapStats.MagnetShrinesTotal = c.numTotal;
                                usedOfficialTracker = true;
                            }
                            else if (k.Contains("micro"))
                            {
                                _mapStats.MicrowavesDone = c.numUsed;
                                _mapStats.MicrowavesTotal = c.numTotal;
                                usedOfficialTracker = true;
                            }
                            else if (k.Contains("moai"))
                            {
                                _mapStats.MoaisDone = c.numUsed;
                                _mapStats.MoaisTotal = c.numTotal;
                                usedOfficialTracker = true;
                            }
                            else if (k.Contains("pot"))
                            {
                                _mapStats.PotsSmashed = c.numUsed;
                                _mapStats.PotsTotal = c.numTotal;
                                usedOfficialTracker = true;
                            }
                            else if (k.Contains("shady"))
                            {
                                _mapStats.ShadyGuysTotal = c.numTotal;
                                usedOfficialTracker = true;
                            }
                        }
                    }
                }
                catch { }

                // 2. Vendedores dorados en vivo
                InteractableShadyGuy[] shadys = UnityEngine.Object.FindObjectsOfType<InteractableShadyGuy>();
                if (shadys != null)
                {
                    if (!usedOfficialTracker) _mapStats.ShadyGuysTotal = shadys.Length;
                    _mapStats.ShadyGuysGolden = shadys.Count(s => s != null && s.rarity == EItemRarity.Legendary);
                }

                // 3. Respaldo por componentes de escena si el juego aún no ha poblado InteractablesStatus
                if (!usedOfficialTracker)
                {
                    // Santuarios Malditos (Maldiciones de Jefe)
                    InteractableShrineCursed[] cursedShrines = UnityEngine.Object.FindObjectsOfType<InteractableShrineCursed>();
                    if (cursedShrines != null)
                    {
                        _mapStats.BossCursesMax = cursedShrines.Length;
                        _mapStats.BossCurses = cursedShrines.Count(c => c != null && c.done);
                    }

                    // Moais
                    InteractableShrineMoai[] moais = UnityEngine.Object.FindObjectsOfType<InteractableShrineMoai>();
                    if (moais != null && moais.Length > 0)
                    {
                        if (moais.Length > _mapStats.MoaisTotal) _mapStats.MoaisTotal = moais.Length;
                        _mapStats.MoaisDone = moais.Count(m => m != null && m.done);
                    }

                    // Vasijas
                    InteractablePot[] currentPots = UnityEngine.Object.FindObjectsOfType<InteractablePot>();
                    int potsRemaining = (currentPots != null) ? currentPots.Length : 0;
                    if (!_mapInitialized || potsRemaining > _initialPotsCount)
                    {
                        _initialPotsCount = potsRemaining;
                        _mapInitialized = true;
                    }
                    _mapStats.PotsTotal = _initialPotsCount;
                    _mapStats.PotsSmashed = Mathf.Max(0, _initialPotsCount - potsRemaining);

                    // Cofres
                    InteractableChest[] remainingChests = UnityEngine.Object.FindObjectsOfType<InteractableChest>();
                    OpenChest[] openedChests = UnityEngine.Object.FindObjectsOfType<OpenChest>();
                    int remCount = (remainingChests != null) ? remainingChests.Length : 0;
                    int opCount = (openedChests != null) ? openedChests.Length : 0;
                    _mapStats.ChestsOpened = opCount;
                    _mapStats.ChestsTotal = remCount + opCount;

                    // Cargas
                    ChargeShrine[] charges = UnityEngine.Object.FindObjectsOfType<ChargeShrine>();
                    if (charges != null)
                    {
                        _mapStats.ChargeShrinesTotal = charges.Length;
                        _mapStats.ChargeShrinesDone = charges.Count(c => c != null && c.completed);
                    }

                    // Desafios
                    InteractableShrineChallenge[] challenges = UnityEngine.Object.FindObjectsOfType<InteractableShrineChallenge>();
                    if (challenges != null)
                    {
                        _mapStats.ChallengesTotal = challenges.Length;
                        _mapStats.ChallengesDone = challenges.Count(c => c != null && c.done);
                    }

                    // Codicia
                    InteractableShrineGreed[] greeds = UnityEngine.Object.FindObjectsOfType<InteractableShrineGreed>();
                    if (greeds != null)
                    {
                        _mapStats.GreedShrinesTotal = greeds.Length;
                        _mapStats.GreedShrinesDone = greeds.Count(g => g != null && g.done);
                    }

                    // Iman
                    InteractableShrineMagnet[] magnets = UnityEngine.Object.FindObjectsOfType<InteractableShrineMagnet>();
                    if (magnets != null)
                    {
                        _mapStats.MagnetShrinesTotal = magnets.Length;
                        _mapStats.MagnetShrinesDone = magnets.Count(m => m != null && m.done);
                    }

                    // Microondas
                    InteractableMicrowave[] micros = UnityEngine.Object.FindObjectsOfType<InteractableMicrowave>();
                    if (micros != null)
                    {
                        _mapStats.MicrowavesTotal = micros.Length;
                        _mapStats.MicrowavesDone = micros.Count(m => m != null && m.usesLeft <= 0);
                    }
                }
            }
            catch (Exception ex)
            {
                Plugin.LogSource.LogDebug($"Error actualizando estadisticas del mapa: {ex.Message}");
            }
        }

        private static string GetSpanishItemName(EItem item, string fallback)
        {
            switch (item)
            {
                case EItem.SoulHarvester: return "Cosechador de Almas";
                case EItem.SuckyMagnet: return "Iman de Bonk";
                case EItem.GoldenShield: return "Escudo Dorado";
                case EItem.GoldenGlove: return "Guantelete Dorado";
                case EItem.GoldenSneakers: return "Zapatillas Doradas";
                case EItem.ZaWarudo: return "Detener Tiempo (Za Warudo)";
                case EItem.Dragonfire: return "Fuego de Dragon";
                case EItem.DemonicBlood: return "Sangre Demoniaca";
                case EItem.DemonicSoul: return "Alma Demoniaca";
                case EItem.LightningOrb: return "Orbe Relampago";
                case EItem.SluttyCannon: return "Canon Explosivo";
                case EItem.CreditCardRed: return "Tarjeta Roja";
                case EItem.CreditCardGreen: return "Tarjeta Verde";
                case EItem.Anvil: return "Yunque";
                case EItem.Clover: return "Trebol de la Suerte";
                case EItem.Campfire: return "Fogata";
                case EItem.Rollerblades: return "Patines";
                case EItem.Ghost: return "Fantasma";
                case EItem.IceCube: return "Cubo de Hielo";
                case EItem.Medkit: return "Botiquin";
                case EItem.Borgar: return "Hamburguesa";
                case EItem.HolyBook: return "Libro Sagrado";
                case EItem.ToxicBarrel: return "Barril Toxico";
                case EItem.EnergyCore: return "Nucleo de Energia";
                case EItem.ElectricPlug: return "Enchufe Electrico";
                case EItem.BossBuster: return "Cazajefes";
                case EItem.LeechingCrystal: return "Cristal Vampirico";
                case EItem.TacticalGlasses: return "Gafas Tacticas";
                case EItem.Cactus: return "Cactus";
                case EItem.TimeBracelet: return "Brazalete del Tiempo";
                case EItem.GloveLightning: return "Guante Relampago";
                case EItem.GlovePoison: return "Guante Venenoso";
                case EItem.GloveBlood: return "Guante Sangriento";
                case EItem.GloveCurse: return "Guante Maldito";
                case EItem.GlovePower: return "Guante de Poder";
                case EItem.Wrench: return "Llave Inglesa";
                case EItem.Beacon: return "Baliza";
                case EItem.GoldenRing: return "Anillo Dorado";
                case EItem.QuinsMask: return "Mascara de Quin";
                case EItem.OldMask: return "Mascara Vieja";
                case EItem.Snek: return "Serpiente";
                case EItem.Pot: return "Olla de Acero";
                case EItem.BobsLantern: return "Linterna de Bob";
                case EItem.Pumpkin: return "Calabaza";
                case EItem.WizardsHat: return "Sombrero de Mago";
                case EItem.Beer: return "Cerveza";
                case EItem.SpikyShield: return "Escudo de Espinas";
                case EItem.Bonker: return "El Bonker";
                case EItem.SlipperyRing: return "Anillo Resbaladizo";
                case EItem.CowardsCloak: return "Capa del Cobarde";
                case EItem.GymSauce: return "Salsa Fitness";
                case EItem.Battery: return "Bateria";
                case EItem.PhantomShroud: return "Manto Fantasmal";
                case EItem.ForbiddenJuice: return "Jugo Prohibido";
                case EItem.DemonBlade: return "Hoja Demoniaca";
                case EItem.GrandmasSecretTonic: return "Tonico de la Abuela";
                case EItem.GiantFork: return "Tenedor Gigante";
                case EItem.MoldyCheese: return "Queso Mohoso";
                case EItem.SpicyMeatball: return "Albondiga Picante";
                case EItem.Chonkplate: return "Placa Blindada";
                case EItem.BeefyRing: return "Anillo Robusto";
                case EItem.OverpoweredLamp: return "Lampara Rota";
                case EItem.Feathers: return "Plumas";
                case EItem.TurboSocks: return "Calcetines Turbo";
                case EItem.ShatteredWisdom: return "Sabiduria Rota";
                case EItem.EchoShard: return "Fragmento Eco";
                case EItem.Backpack: return "Mochila";
                case EItem.Skuleg: return "Skuleg";
                case EItem.EagleClaw: return "Garra de Aguila";
                case EItem.Scarf: return "Bufanda";
                case EItem.Oats: return "Avena";
                case EItem.CursedDoll: return "Muneco Maldito";
                case EItem.BobDead: return "Bob Muerto";
                case EItem.Mirror: return "Espejo";
                case EItem.JoesDagger: return "Daga de Joe";
                case EItem.WeebHeadset: return "Auriculares Otaku";
                case EItem.SpeedBoi: return "Speed Boi";
                case EItem.Gasmask: return "Mascara de Gas";
                case EItem.BrassKnuckles: return "Manopla";
                case EItem.IdleJuice: return "Jugo AFK";
                case EItem.Kevin: return "Kevin";
                case EItem.GamerGoggles: return "Gafas Gamer";
                case EItem.UnstableTransfusion: return "Transfusion Inestable";
                case EItem.BloodyCleaver: return "Cuchillo Sangriento";
                default:
                    return fallback;
            }
        }

        private void InitItemCatalog()
        {
            try
            {
                ItemData[] allData = null;
                if (DataManager.Instance != null && DataManager.Instance.unsortedItems != null && DataManager.Instance.unsortedItems.Count > 0)
                {
                    allData = DataManager.Instance.unsortedItems.ToArray();
                }

                if (allData == null || allData.Length == 0)
                {
                    allData = Resources.FindObjectsOfTypeAll<ItemData>();
                }

                if (allData == null || allData.Length == 0)
                {
                    if (DataManager.Instance != null)
                    {
                        List<ItemData> list = new List<ItemData>();
                        foreach (EItem val in Enum.GetValues(typeof(EItem)))
                        {
                            try
                            {
                                ItemData d = DataManager.Instance.GetItem(val);
                                if (d != null) list.Add(d);
                            }
                            catch { }
                        }
                        if (list.Count > 0) allData = list.ToArray();
                    }
                }

                if (allData == null || allData.Length == 0) return;

                _catalog.Clear();
                _catalogDict.Clear();

                foreach (ItemData it in allData)
                {
                    if (it == null) continue;
                    if (_catalogDict.ContainsKey(it.eItem)) continue;

                    string cleanName = it.name != null ? it.name.Replace("Item", "") : it.eItem.ToString();
                    string spanish = GetSpanishItemName(it.eItem, cleanName);

                    ItemCatalogEntry entry = new ItemCatalogEntry
                    {
                        eItem = it.eItem,
                        idName = cleanName,
                        spanishName = spanish,
                        rarity = it.rarity,
                        icon = it.icon
                    };

                    _catalog.Add(entry);
                    _catalogDict[it.eItem] = entry;
                }

                _catalog.Sort((a, b) =>
                {
                    int rComp = ((int)b.rarity).CompareTo((int)a.rarity);
                    if (rComp != 0) return rComp;
                    return string.Compare(a.spanishName, b.spanishName, StringComparison.OrdinalIgnoreCase);
                });

                _catalogLoaded = true;
                Plugin.LogSource.LogInfo($"Catalogo de items cargado: {_catalog.Count} items disponibles.");
            }
            catch (Exception ex)
            {
                Plugin.LogSource.LogError($"Error al cargar catalogo de items: {ex.Message}");
            }
        }

        public void StartSearch()
        {
            if (Plugin.ConfigScoutMode.Value == ScoutMode.CustomSelectedItems && _selectedItems.Count == 0)
            {
                _showItemPicker = true;
                StatusText = "Primero elige al menos 1 item en el selector para buscar.";
                return;
            }

            IsAutoResetActive = true;
            MatchFound = false;
            MatchDetails.Clear();
            StatusText = $"BUSCANDO SEMILLA... (Intento #{AttemptCount})";
            Plugin.LogSource.LogInfo($"Iniciando busqueda en modo: {Plugin.ConfigScoutMode.Value}");

            MyPlayer player = UnityEngine.Object.FindObjectOfType<MyPlayer>();
            if (player != null)
            {
                EvaluateCurrentMap();
            }
            else
            {
                _evaluatedCurrentMap = false;
                _timeSincePlayerSpawned = 0f;
            }
        }

        public void PauseSearch()
        {
            IsAutoResetActive = false;
            StatusText = $"PAUSADO en el intento #{AttemptCount}. Presiona [F5] para reanudar.";
            Plugin.LogSource.LogInfo("Busqueda pausada.");
        }

        private void EvaluateCurrentMap()
        {
            _evaluatedCurrentMap = true;

            InteractableShadyGuy[] allShady = UnityEngine.Object.FindObjectsOfType<InteractableShadyGuy>();
            int totalShadyCount = (allShady != null) ? allShady.Length : 0;

            bool isMatch = false;
            List<string> foundInfo = new List<string>();

            if (_selectedItems.Count > 0 && allShady != null && allShady.Length >= _selectedItems.Count)
            {
                InteractableShadyGuy[] matchedVendors = VendorMatcher.FindMatch(allShady, _selectedItems);
                if (matchedVendors != null && matchedVendors.Length == _selectedItems.Count)
                {
                    isMatch = true;
                    for (int i = 0; i < _selectedItems.Count; i++)
                    {
                        EItem target = _selectedItems[i];
                        InteractableShadyGuy v = matchedVendors[i];
                        string rName = GetRaritySpanish(v.rarity);
                        string itName = GetSpanishItemName(target, target.ToString());
                        foundInfo.Add($"Vendedor #{i + 1} ({rName}): Ofrece {itName} | Todos: [{DescribeVendorItems(v)}]");
                    }
                }
            }

            if (isMatch)
            {
                MatchFound = true;
                IsAutoResetActive = false;
                MatchDetails = foundInfo;
                StatusText = $"¡PARTIDA ENCONTRADA! ({_selectedItems.Count} item(s) en {AttemptCount} intentos)";

                Plugin.LogSource.LogInfo("========================================");
                Plugin.LogSource.LogInfo($"¡PARTIDA RECORD ENCONTRADA EN EL INTENTO #{AttemptCount}!");
                foreach (string d in foundInfo) Plugin.LogSource.LogInfo(" -> " + d);
                Plugin.LogSource.LogInfo("========================================");

                if (Plugin.ConfigPlayAlertSound.Value)
                {
                    try { Console.Beep(1000, 400); Console.Beep(1300, 600); } catch { }
                }
            }
            else
            {
                if (IsAutoResetActive)
                {
                    AttemptCount++;
                    StatusText = $"Reiniciando... (Intento #{AttemptCount})";
                    RestartMap();
                }
            }
        }

        private string DescribeVendorItems(InteractableShadyGuy shady)
        {
            if (shady == null || shady.items == null) return "Sin items";
            List<string> names = new List<string>();
            foreach (ItemData it in shady.items)
            {
                if (it != null)
                {
                    names.Add(GetSpanishItemName(it.eItem, it.eItem.ToString()));
                }
            }
            return string.Join(", ", names);
        }

        private static string GetRaritySpanish(EItemRarity r)
        {
            switch (r)
            {
                case EItemRarity.Legendary: return "Dorado";
                case EItemRarity.Epic: return "Epico";
                case EItemRarity.Rare: return "Raro";
                case EItemRarity.Common: return "Comun";
                case EItemRarity.Corrupted: return "Corrupto";
                default: return r.ToString();
            }
        }

        private static Color GetRarityColor(EItemRarity r)
        {
            switch (r)
            {
                case EItemRarity.Legendary: return new Color(1.0f, 0.82f, 0.18f);
                case EItemRarity.Epic: return new Color(0.72f, 0.44f, 1.0f);
                case EItemRarity.Rare: return new Color(0.25f, 0.72f, 1.0f);
                case EItemRarity.Common: return new Color(0.85f, 0.88f, 0.92f);
                case EItemRarity.Corrupted: return new Color(1.0f, 0.28f, 0.35f);
                default: return Color.white;
            }
        }

        private void RestartMap()
        {
            _timeSincePlayerSpawned = 0f;
            _evaluatedCurrentMap = false;
            try
            {
                MapController.RestartRun();
            }
            catch (Exception ex)
            {
                Plugin.LogSource.LogError($"Error al reiniciar partida: {ex.Message}");
            }
        }

        // ==========================================
        // RENDERIZADO SOLIDO CON TEXTURE2D.WHITETEXTURE
        // ==========================================
        private static void DrawSolidRect(Rect rect, Color color)
        {
            Color prev = GUI.color;
            GUI.color = color;
            GUI.DrawTexture(rect, Texture2D.whiteTexture);
            GUI.color = prev;
        }

        private static void DrawPanelBox(Rect rect, Color bg, Color border, float borderWidth = 2f)
        {
            DrawSolidRect(rect, border);
            DrawSolidRect(new Rect(rect.x + borderWidth, rect.y + borderWidth, rect.width - (borderWidth * 2f), rect.height - (borderWidth * 2f)), bg);
        }

        private static void DrawHeaderBar(Rect dragBar, Color bg, Color border)
        {
            DrawSolidRect(dragBar, border);
            DrawSolidRect(new Rect(dragBar.x + 1f, dragBar.y + 1f, dragBar.width - 2f, dragBar.height - 2f), bg);
        }

        private bool DrawCyberButton(Rect rect, string text, bool highlight = false)
        {
            Event evt = Event.current;
            bool isHover = evt != null && rect.Contains(evt.mousePosition);

            Color border = highlight ? new Color(0.0f, 1.0f, 0.50f, 1.0f) : (isHover ? new Color(0.0f, 0.90f, 1.0f, 1.0f) : new Color(0.28f, 0.38f, 0.55f, 1.0f));
            Color bg = highlight ? (isHover ? new Color(0.12f, 0.45f, 0.25f, 1.0f) : new Color(0.08f, 0.32f, 0.18f, 1.0f))
                                 : (isHover ? new Color(0.18f, 0.24f, 0.35f, 1.0f) : new Color(0.12f, 0.15f, 0.22f, 1.0f));

            DrawSolidRect(rect, border);
            DrawSolidRect(new Rect(rect.x + 1f, rect.y + 1f, rect.width - 2f, rect.height - 2f), bg);

            return GUI.Button(rect, text, highlight ? _btnHighlightStyle : _btnStyle);
        }

        private static string ColorToHex(Color c)
        {
            int r = Mathf.Clamp(Mathf.RoundToInt(c.r * 255f), 0, 255);
            int g = Mathf.Clamp(Mathf.RoundToInt(c.g * 255f), 0, 255);
            int b = Mathf.Clamp(Mathf.RoundToInt(c.b * 255f), 0, 255);
            return $"{r:X2}{g:X2}{b:X2}";
        }

        private static string GetModeDisplayName(ScoutMode mode)
        {
            switch (mode)
            {
                case ScoutMode.DualVendor_SoulHarvester_And_Magnet:
                    return "Doble Dorado (Cosechador + Iman)";
                case ScoutMode.SingleItem_SoulHarvester:
                    return "Item Unico Dorado (Cosechador)";
                case ScoutMode.AnyGoldenVendor:
                    return "Cualquier Vendedor Dorado";
                case ScoutMode.CustomSelectedItems:
                    return "Personalizado (Elegir Items)";
                default:
                    return mode.ToString();
            }
        }

        private void InitStyles()
        {
            if (_stylesInitialized) return;

            // Cargar fuente alagard del juego
            try
            {
                Font[] fonts = Resources.FindObjectsOfTypeAll<Font>();
                if (fonts != null)
                {
                    foreach (Font f in fonts)
                    {
                        if (f != null && f.name.Equals("alagard", StringComparison.OrdinalIgnoreCase))
                        {
                            _gameFont = f;
                            break;
                        }
                    }
                }
            }
            catch { }

            _titleStyle = new GUIStyle(GUI.skin.label);
            if (_gameFont != null) _titleStyle.font = _gameFont;
            _titleStyle.fontSize = 15;
            _titleStyle.fontStyle = FontStyle.Bold;
            _titleStyle.normal.textColor = new Color(0.0f, 0.92f, 1.0f);

            _subTitleStyle = new GUIStyle(GUI.skin.label);
            if (_gameFont != null) _subTitleStyle.font = _gameFont;
            _subTitleStyle.fontSize = 13;
            _subTitleStyle.fontStyle = FontStyle.Bold;
            _subTitleStyle.normal.textColor = new Color(1.0f, 0.82f, 0.20f);

            _badgeStyle = new GUIStyle(GUI.skin.label);
            if (_gameFont != null) _badgeStyle.font = _gameFont;
            _badgeStyle.fontSize = 12;
            _badgeStyle.richText = true;
            _badgeStyle.normal.textColor = Color.white;

            _labelWhite = new GUIStyle(GUI.skin.label);
            if (_gameFont != null) _labelWhite.font = _gameFont;
            _labelWhite.fontSize = 12;
            _labelWhite.richText = true;
            _labelWhite.normal.textColor = Color.white;

            _labelMuted = new GUIStyle(GUI.skin.label);
            if (_gameFont != null) _labelMuted.font = _gameFont;
            _labelMuted.fontSize = 10;
            _labelMuted.normal.textColor = new Color(0.70f, 0.75f, 0.82f);

            _labelGreen = new GUIStyle(GUI.skin.label);
            if (_gameFont != null) _labelGreen.font = _gameFont;
            _labelGreen.fontSize = 13;
            _labelGreen.fontStyle = FontStyle.Bold;
            _labelGreen.normal.textColor = new Color(0.20f, 1.0f, 0.45f);

            _btnStyle = new GUIStyle(GUI.skin.button);
            if (_gameFont != null) _btnStyle.font = _gameFont;
            _btnStyle.fontSize = 11;
            _btnStyle.fontStyle = FontStyle.Bold;
            _btnStyle.normal.background = null;
            _btnStyle.hover.background = null;
            _btnStyle.active.background = null;
            _btnStyle.normal.textColor = Color.white;
            _btnStyle.hover.textColor = Color.white;
            _btnStyle.active.textColor = Color.white;
            _btnStyle.alignment = TextAnchor.MiddleCenter;

            _btnHighlightStyle = new GUIStyle(GUI.skin.button);
            if (_gameFont != null) _btnHighlightStyle.font = _gameFont;
            _btnHighlightStyle.fontSize = 11;
            _btnHighlightStyle.fontStyle = FontStyle.Bold;
            _btnHighlightStyle.normal.background = null;
            _btnHighlightStyle.hover.background = null;
            _btnHighlightStyle.active.background = null;
            _btnHighlightStyle.normal.textColor = new Color(0.85f, 1.0f, 0.85f);
            _btnHighlightStyle.hover.textColor = Color.white;
            _btnHighlightStyle.active.textColor = Color.white;
            _btnHighlightStyle.alignment = TextAnchor.MiddleCenter;

            _mapRowNameStyle = new GUIStyle(GUI.skin.label);
            if (_gameFont != null) _mapRowNameStyle.font = _gameFont;
            _mapRowNameStyle.fontSize = 12;
            _mapRowNameStyle.fontStyle = FontStyle.Bold;
            _mapRowNameStyle.normal.textColor = new Color(0.92f, 0.94f, 0.98f);

            _mapRowCountStyle = new GUIStyle(GUI.skin.label);
            if (_gameFont != null) _mapRowCountStyle.font = _gameFont;
            _mapRowCountStyle.fontSize = 12;
            _mapRowCountStyle.fontStyle = FontStyle.Bold;
            _mapRowCountStyle.alignment = TextAnchor.MiddleRight;
            _mapRowCountStyle.richText = true;
            _mapRowCountStyle.normal.textColor = new Color(0.25f, 0.95f, 0.95f);

            _stylesInitialized = true;
        }

        private void InitPositions()
        {
            if (_positionsInitialized) return;

            float defaultWidth = 480f;
            float defaultHeight = 200f;

            float savedX = Plugin.ConfigWindowX.Value;
            float savedY = Plugin.ConfigWindowY.Value;

            if (savedX >= 0f && savedY >= 0f && savedX < Screen.width && savedY < Screen.height)
            {
                _windowRect = new Rect(savedX, savedY, defaultWidth, defaultHeight);
            }
            else
            {
                float posY = Mathf.Max(30f, (Screen.height - defaultHeight) / 2f - 60f);
                _windowRect = new Rect(20f, posY, defaultWidth, defaultHeight);
            }

            // Posicion del panel del mapa
            float mapX = Plugin.ConfigMapTrackerX.Value;
            float mapY = Plugin.ConfigMapTrackerY.Value;
            float mapW = 310f;
            float mapH = 320f;
            if (mapX >= 0f && mapY >= 0f && mapX < Screen.width && mapY < Screen.height)
            {
                _mapTrackerRect = new Rect(mapX, mapY, mapW, mapH);
            }
            else
            {
                _mapTrackerRect = new Rect(_windowRect.x, _windowRect.y + _windowRect.height + 10f, mapW, mapH);
            }

            // Posicion centrada del selector de items
            float pickW = 750f;
            float pickH = 520f;
            _pickerRect = new Rect((Screen.width - pickW) / 2f, (Screen.height - pickH) / 2f, pickW, pickH);

            _positionsInitialized = true;
        }

        public void OnGUI()
        {
            GUI.depth = -100;
            InitStyles();
            InitPositions();

            // 1. Panel Principal del Buscador
            if (Plugin.ConfigShowHud.Value)
            {
                DrawMainWindow();
            }

            // 2. Panel Indicador de Objetos del Mapa (en Espanol)
            if (Plugin.ConfigShowMapTracker.Value)
            {
                DrawMapTrackerWindow();
            }

            // 3. Ventana Modal del Selector de Items
            if (_showItemPicker)
            {
                DrawItemPickerWindow();
            }
        }

        private void DrawMainWindow()
        {
            Event evt = Event.current;
            Rect dragBar = new Rect(_windowRect.x, _windowRect.y, _windowRect.width, 32f);

            // Arrastre con raton
            if (evt != null)
            {
                if (evt.type == EventType.MouseDown && dragBar.Contains(evt.mousePosition))
                {
                    _isDraggingMain = true;
                    _dragOffsetMain = evt.mousePosition - new Vector2(_windowRect.x, _windowRect.y);
                }
                else if (evt.type == EventType.MouseUp && _isDraggingMain)
                {
                    _isDraggingMain = false;
                    Plugin.ConfigWindowX.Value = _windowRect.x;
                    Plugin.ConfigWindowY.Value = _windowRect.y;
                }

                if (_isDraggingMain && evt.type == EventType.MouseDrag)
                {
                    _windowRect.x = evt.mousePosition.x - _dragOffsetMain.x;
                    _windowRect.y = evt.mousePosition.y - _dragOffsetMain.y;
                    _windowRect.x = Mathf.Clamp(_windowRect.x, 0f, Screen.width - _windowRect.width);
                    _windowRect.y = Mathf.Clamp(_windowRect.y, 0f, Screen.height - _windowRect.height);
                }
            }

            _windowRect.height = MatchFound ? 220f : 185f;

            // Dibujar fondo solido y cabecera solida
            DrawPanelBox(_windowRect, new Color(0.07f, 0.09f, 0.14f, 0.98f), new Color(0.0f, 0.88f, 1.0f, 1.0f), 2f);
            DrawHeaderBar(dragBar, new Color(0.12f, 0.16f, 0.25f, 1.0f), new Color(0.0f, 0.88f, 1.0f, 1.0f));

            // Titulo
            GUI.Label(new Rect(_windowRect.x + 14f, _windowRect.y + 6f, 320f, 22f), "MEGABONK SEED SCOUT", _titleStyle);
            GUI.Label(new Rect(_windowRect.x + _windowRect.width - 130f, _windowRect.y + 8f, 116f, 18f), "v1.1.3 [F7 Ocultar]", _labelMuted);

            float curY = _windowRect.y + 36f;

            // Items objetivos seleccionados
            string chosenList = "";
            if (_selectedItems.Count == 0)
            {
                chosenList = "<color=#FFAA00>(Ninguno - Pulsa [ELEGIR ITEMS])</color>";
            }
            else
            {
                List<string> itemBadges = new List<string>();
                foreach (EItem it in _selectedItems)
                {
                    string sName = GetSpanishItemName(it, it.ToString());
                    itemBadges.Add($"<b>[{sName}]</b>");
                }
                chosenList = string.Join(" + ", itemBadges);
            }
            GUI.Label(new Rect(_windowRect.x + 14f, curY, _windowRect.width - 28f, 20f), $"Objetivos: <color=#00E5FF>{chosenList}</color>", _labelWhite);
            curY += 24f;

            // Estado y coincidencias
            if (MatchFound)
            {
                GUI.Label(new Rect(_windowRect.x + 14f, curY, _windowRect.width - 28f, 20f), StatusText, _labelGreen);
                curY += 22f;
                foreach (string detail in MatchDetails)
                {
                    GUI.Label(new Rect(_windowRect.x + 14f, curY, _windowRect.width - 28f, 18f), detail, _labelWhite);
                    curY += 18f;
                }
            }
            else
            {
                string stateColor = IsAutoResetActive ? "<color=#00FF66>BUSCANDO AUTOMATICO...</color>" : "<color=#FFAA00>PAUSADO</color>";
                GUI.Label(new Rect(_windowRect.x + 14f, curY, _windowRect.width - 28f, 18f), $"Estado: {stateColor} | Intentos: <b>{AttemptCount}</b>", _labelWhite);
                curY += 24f;
            }

            // Botones de accion: 3 botones comodos y claros
            float btnH = 28f;
            float btnGap = 8f;
            float btnX = _windowRect.x + 14f;

            string startTxt = IsAutoResetActive ? "[F6] PAUSAR" : "[F5] BUSCAR";
            if (DrawCyberButton(new Rect(btnX, curY, 140f, btnH), startTxt, IsAutoResetActive))
            {
                if (IsAutoResetActive) PauseSearch();
                else StartSearch();
            }
            btnX += 140f + btnGap;

            if (DrawCyberButton(new Rect(btnX, curY, 160f, btnH), "[ ELEGIR ITEMS ]", true))
            {
                _showItemPicker = !_showItemPicker;
                if (_showItemPicker && !_catalogLoaded) InitItemCatalog();
            }
            btnX += 160f + btnGap;

            string mapTxt = Plugin.ConfigShowMapTracker.Value ? "[ MAPA: SI ]" : "[ MAPA: NO ]";
            if (DrawCyberButton(new Rect(btnX, curY, 140f, btnH), mapTxt, false))
            {
                Plugin.ConfigShowMapTracker.Value = !Plugin.ConfigShowMapTracker.Value;
            }

            curY += 34f;
            GUI.Label(new Rect(_windowRect.x + 14f, curY, _windowRect.width - 28f, 16f), "Atajos: [F5] Buscar/Reanudar | [F6] Pausar | [F7] Ocultar HUD | [F9] Mapa", _labelMuted);
        }

        private void DrawMapTrackerWindow()
        {
            Event evt = Event.current;
            Rect dragBar = new Rect(_mapTrackerRect.x, _mapTrackerRect.y, _mapTrackerRect.width, 28f);

            // Arrastre con raton
            if (evt != null)
            {
                if (evt.type == EventType.MouseDown && dragBar.Contains(evt.mousePosition))
                {
                    _isDraggingMap = true;
                    _dragOffsetMap = evt.mousePosition - new Vector2(_mapTrackerRect.x, _mapTrackerRect.y);
                }
                else if (evt.type == EventType.MouseUp && _isDraggingMap)
                {
                    _isDraggingMap = false;
                    Plugin.ConfigMapTrackerX.Value = _mapTrackerRect.x;
                    Plugin.ConfigMapTrackerY.Value = _mapTrackerRect.y;
                }

                if (_isDraggingMap && evt.type == EventType.MouseDrag)
                {
                    _mapTrackerRect.x = evt.mousePosition.x - _dragOffsetMap.x;
                    _mapTrackerRect.y = evt.mousePosition.y - _dragOffsetMap.y;
                    _mapTrackerRect.x = Mathf.Clamp(_mapTrackerRect.x, 0f, Screen.width - _mapTrackerRect.width);
                    _mapTrackerRect.y = Mathf.Clamp(_mapTrackerRect.y, 0f, Screen.height - _mapTrackerRect.height);
                }
            }

            _mapTrackerRect.width = 310f;
            _mapTrackerRect.height = 320f;

            // Fondo y Cabecera del Indicador de Mapa solidos
            DrawPanelBox(_mapTrackerRect, new Color(0.07f, 0.09f, 0.14f, 0.98f), new Color(0.25f, 0.95f, 0.95f, 1.0f), 2f);
            DrawHeaderBar(dragBar, new Color(0.10f, 0.18f, 0.28f, 1.0f), new Color(0.25f, 0.95f, 0.95f, 1.0f));

            GUI.Label(new Rect(_mapTrackerRect.x + 10f, _mapTrackerRect.y + 5f, _mapTrackerRect.width - 20f, 20f), "OBJETOS DE LA PARTIDA", _titleStyle);

            float rowY = _mapTrackerRect.y + 34f;
            float rowH = 24f;
            float leftW = 145f;
            float rightW = 135f;
            float padX = _mapTrackerRect.x + 14f;

            DrawMapRow(padX, rowY, leftW, rightW, "Maldiciones de Jefe", $"{_mapStats.BossCurses} / {_mapStats.BossCursesMax}");
            rowY += rowH;

            DrawMapRow(padX, rowY, leftW, rightW, "Desafios", $"{_mapStats.ChallengesDone} / {_mapStats.ChallengesTotal}");
            rowY += rowH;

            DrawMapRow(padX, rowY, leftW, rightW, "Santuarios de Carga", $"{_mapStats.ChargeShrinesDone} / {_mapStats.ChargeShrinesTotal}");
            rowY += rowH;

            DrawMapRow(padX, rowY, leftW, rightW, "Cofres", $"{_mapStats.ChestsOpened} / {_mapStats.ChestsTotal}");
            rowY += rowH;

            DrawMapRow(padX, rowY, leftW, rightW, "Santuarios de Codicia", $"{_mapStats.GreedShrinesDone} / {_mapStats.GreedShrinesTotal}");
            rowY += rowH;

            DrawMapRow(padX, rowY, leftW, rightW, "Santuarios de Iman", $"{_mapStats.MagnetShrinesDone} / {_mapStats.MagnetShrinesTotal}");
            rowY += rowH;

            DrawMapRow(padX, rowY, leftW, rightW, "Microondas", $"{_mapStats.MicrowavesDone} / {_mapStats.MicrowavesTotal}");
            rowY += rowH;

            DrawMapRow(padX, rowY, leftW, rightW, "Moais", $"{_mapStats.MoaisDone} / {_mapStats.MoaisTotal}");
            rowY += rowH;

            DrawMapRow(padX, rowY, leftW, rightW, "Vasijas", $"{_mapStats.PotsSmashed} / {_mapStats.PotsTotal}");
            rowY += rowH;

            string shadyCountText = $"{_mapStats.ShadyGuysTotal}";
            if (_mapStats.ShadyGuysGolden > 0)
                shadyCountText += $" (<color=#FFD700><b>{_mapStats.ShadyGuysGolden} Dorado</b></color>)";
            DrawMapRow(padX, rowY, leftW, rightW, "Vendedores", shadyCountText);
        }

        private void DrawMapRow(float x, float y, float leftW, float rightW, string label, string count)
        {
            GUI.Label(new Rect(x, y, leftW, 20f), label, _mapRowNameStyle);
            GUI.Label(new Rect(x + leftW, y, rightW, 20f), count, _mapRowCountStyle);
        }

        private void DrawItemPickerWindow()
        {
            Event evt = Event.current;
            Rect dragBar = new Rect(_pickerRect.x, _pickerRect.y, _pickerRect.width, 32f);

            if (evt != null)
            {
                if (evt.type == EventType.MouseDown && dragBar.Contains(evt.mousePosition))
                {
                    _isDraggingPicker = true;
                    _dragOffsetPicker = evt.mousePosition - new Vector2(_pickerRect.x, _pickerRect.y);
                }
                else if (evt.type == EventType.MouseUp && _isDraggingPicker)
                {
                    _isDraggingPicker = false;
                }

                if (_isDraggingPicker && evt.type == EventType.MouseDrag)
                {
                    _pickerRect.x = evt.mousePosition.x - _dragOffsetPicker.x;
                    _pickerRect.y = evt.mousePosition.y - _dragOffsetPicker.y;
                    _pickerRect.x = Mathf.Clamp(_pickerRect.x, 0f, Screen.width - _pickerRect.width);
                    _pickerRect.y = Mathf.Clamp(_pickerRect.y, 0f, Screen.height - _pickerRect.height);
                }

                if (evt.type == EventType.ScrollWheel && _pickerRect.Contains(evt.mousePosition))
                {
                    if (evt.delta.y > 0) _pickerPage++;
                    else if (evt.delta.y < 0 && _pickerPage > 0) _pickerPage--;
                    evt.Use();
                }
            }

            // Dibujar fondo solido y cabecera solida
            DrawPanelBox(_pickerRect, new Color(0.07f, 0.08f, 0.13f, 0.98f), new Color(1.0f, 0.80f, 0.20f, 1.0f), 2f);
            DrawHeaderBar(dragBar, new Color(0.18f, 0.15f, 0.08f, 1.0f), new Color(1.0f, 0.80f, 0.20f, 1.0f));

            GUI.Label(new Rect(_pickerRect.x + 14f, _pickerRect.y + 6f, 500f, 22f), "SELECTOR DE ITEMS OBJETIVO PARA LA PARTIDA", _titleStyle);

            // Boton cerrar [X]
            if (DrawCyberButton(new Rect(_pickerRect.x + _pickerRect.width - 36f, _pickerRect.y + 4f, 28f, 24f), "[X]", false))
            {
                _showItemPicker = false;
                SaveSelectedItemsToConfig();
            }

            float curY = _pickerRect.y + 38f;

            // Barra de estado de seleccion
            string selInfo = $"Seleccionados: <b><color=#00FF66>{_selectedItems.Count} / 3</color></b> (Haz clic en cualquier item para elegirlo o quitarlo)";
            GUI.Label(new Rect(_pickerRect.x + 16f, curY, _pickerRect.width - 32f, 20f), selInfo, _labelWhite);
            curY += 24f;

            // Mini ranuras de items seleccionados
            float slotW = 226f;
            float slotH = 46f;
            for (int i = 0; i < 3; i++)
            {
                Rect sRect = new Rect(_pickerRect.x + 16f + (i * (slotW + 10f)), curY, slotW, slotH);
                if (i < _selectedItems.Count)
                {
                    EItem it = _selectedItems[i];
                    ItemCatalogEntry entry = _catalogDict.ContainsKey(it) ? _catalogDict[it] : null;

                    // Fondo slot seleccionado
                    DrawSolidRect(sRect, new Color(0.0f, 1.0f, 0.45f, 1.0f));
                    DrawSolidRect(new Rect(sRect.x + 1f, sRect.y + 1f, sRect.width - 2f, sRect.height - 2f), new Color(0.10f, 0.22f, 0.15f, 1.0f));

                    if (entry != null && entry.icon != null)
                    {
                        GUI.DrawTexture(new Rect(sRect.x + 6f, sRect.y + 5f, 36f, 36f), entry.icon, ScaleMode.ScaleToFit);
                    }

                    string itTitle = entry != null ? entry.spanishName : it.ToString();
                    if (itTitle.Length > 18) itTitle = itTitle.Substring(0, 16) + "..";
                    GUI.Label(new Rect(sRect.x + 48f, sRect.y + 6f, sRect.width - 76f, 18f), $"#{i + 1} {itTitle}", _labelWhite);
                    GUI.Label(new Rect(sRect.x + 48f, sRect.y + 24f, sRect.width - 76f, 16f), entry != null ? GetRaritySpanish(entry.rarity) : "", _labelMuted);

                    if (DrawCyberButton(new Rect(sRect.x + sRect.width - 26f, sRect.y + 11f, 22f, 22f), "X", false))
                    {
                        _selectedItems.RemoveAt(i);
                        SaveSelectedItemsToConfig();
                        break;
                    }
                }
                else
                {
                    // Fondo slot vacio
                    DrawSolidRect(sRect, new Color(0.20f, 0.25f, 0.35f, 1.0f));
                    DrawSolidRect(new Rect(sRect.x + 1f, sRect.y + 1f, sRect.width - 2f, sRect.height - 2f), new Color(0.09f, 0.11f, 0.16f, 1.0f));
                    GUI.Label(new Rect(sRect.x + 10f, sRect.y + 14f, sRect.width - 20f, 20f), $"<color=#667788>[ Ranura #{i + 1} vacia ]</color>", _labelWhite);
                }
            }
            curY += slotH + 12f;

            // Pestanas de Rareza
            float tabW = 138f;
            float tabH = 28f;
            string[] tabs = new string[] {
                $"TODOS ({_catalog.Count})",
                $"DORADOS ({_catalog.Count(c => c.rarity == EItemRarity.Legendary)})",
                $"EPICOS ({_catalog.Count(c => c.rarity == EItemRarity.Epic)})",
                $"RAROS ({_catalog.Count(c => c.rarity == EItemRarity.Rare)})",
                $"COMUNES ({_catalog.Count(c => c.rarity == EItemRarity.Common)})"
            };

            for (int t = 0; t < tabs.Length; t++)
            {
                Rect tRect = new Rect(_pickerRect.x + 16f + (t * (tabW + 6f)), curY, tabW, tabH);
                bool isActive = (_pickerRarityTab == t);
                if (DrawCyberButton(tRect, tabs[t], isActive))
                {
                    _pickerRarityTab = t;
                    _pickerPage = 0;
                }
            }

            curY += tabH + 12f;

            // Filtrar lista del catalogo segun pestana seleccionada
            List<ItemCatalogEntry> filtered = new List<ItemCatalogEntry>();
            foreach (ItemCatalogEntry it in _catalog)
            {
                if (_pickerRarityTab == 1 && it.rarity != EItemRarity.Legendary) continue;
                if (_pickerRarityTab == 2 && it.rarity != EItemRarity.Epic) continue;
                if (_pickerRarityTab == 3 && it.rarity != EItemRarity.Rare) continue;
                if (_pickerRarityTab == 4 && it.rarity != EItemRarity.Common) continue;
                filtered.Add(it);
            }

            int totalPages = Mathf.Max(1, Mathf.CeilToInt((float)filtered.Count / ItemsPerPage));
            _pickerPage = Mathf.Clamp(_pickerPage, 0, totalPages - 1);

            int startIndex = _pickerPage * ItemsPerPage;
            int countToShow = Mathf.Min(ItemsPerPage, filtered.Count - startIndex);

            // Cuadricula de Items (6 columnas x 4 filas)
            int cols = 6;
            float cardW = 114f;
            float cardH = 68f;
            float gridGapX = 6f;
            float gridGapY = 6f;

            for (int i = 0; i < countToShow; i++)
            {
                int itemIdx = startIndex + i;
                ItemCatalogEntry item = filtered[itemIdx];

                int col = i % cols;
                int row = i / cols;

                float cx = _pickerRect.x + 16f + col * (cardW + gridGapX);
                float cy = curY + row * (cardH + gridGapY);
                Rect cardRect = new Rect(cx, cy, cardW, cardH);

                bool isSelected = _selectedItems.Contains(item.eItem);
                int selOrder = isSelected ? (_selectedItems.IndexOf(item.eItem) + 1) : 0;

                // Dibujar fondo solido de la tarjeta con borde
                Color cardBorder = isSelected ? new Color(0.0f, 1.0f, 0.45f, 1.0f) : new Color(0.25f, 0.35f, 0.50f, 1.0f);
                Color cardBg = isSelected ? new Color(0.10f, 0.26f, 0.16f, 1.0f) : new Color(0.11f, 0.14f, 0.20f, 1.0f);
                if (evt != null && cardRect.Contains(evt.mousePosition))
                {
                    cardBg = isSelected ? new Color(0.14f, 0.34f, 0.22f, 1.0f) : new Color(0.16f, 0.21f, 0.30f, 1.0f);
                }

                DrawSolidRect(cardRect, cardBorder);
                float bw = isSelected ? 2f : 1f;
                DrawSolidRect(new Rect(cardRect.x + bw, cardRect.y + bw, cardRect.width - bw * 2f, cardRect.height - bw * 2f), cardBg);

                // Dibujar icono oficial del item
                if (item.icon != null)
                {
                    GUI.DrawTexture(new Rect(cx + 6f, cy + 8f, 38f, 38f), item.icon, ScaleMode.ScaleToFit);
                }

                // Nombre en espanol
                string shortName = item.spanishName;
                if (shortName.Length > 12) shortName = shortName.Substring(0, 10) + "..";

                GUI.Label(new Rect(cx + 48f, cy + 6f, cardW - 52f, 18f), shortName, _labelWhite);

                // Rareza con color hexadecimal seguro
                Color rColor = GetRarityColor(item.rarity);
                string hexColor = ColorToHex(rColor);
                GUI.Label(new Rect(cx + 48f, cy + 24f, cardW - 52f, 16f), $"<color=#{hexColor}>{GetRaritySpanish(item.rarity)}</color>", _labelWhite);

                // Indicador de Seleccion
                if (isSelected)
                {
                    GUI.Label(new Rect(cx + cardW - 24f, cy + 44f, 20f, 20f), $"<color=#00FF66><b>#{selOrder}</b></color>", _labelWhite);
                }

                // Clic directo sobre la tarjeta
                if (evt != null && evt.type == EventType.MouseDown && evt.button == 0 && cardRect.Contains(evt.mousePosition))
                {
                    if (isSelected)
                    {
                        _selectedItems.Remove(item.eItem);
                    }
                    else
                    {
                        if (_selectedItems.Count < 3)
                        {
                            _selectedItems.Add(item.eItem);
                        }
                    }
                    SaveSelectedItemsToConfig();
                    evt.Use();
                }
            }

            // Barra inferior: Paginacion y Botones de accion
            float bottomY = _pickerRect.y + _pickerRect.height - 40f;

            // Paginacion
            if (DrawCyberButton(new Rect(_pickerRect.x + 16f, bottomY, 110f, 28f), "< ANTERIOR", false))
            {
                if (_pickerPage > 0) _pickerPage--;
            }

            string pageStr = $"Pagina {_pickerPage + 1} de {totalPages} ({filtered.Count} objetos)";
            GUI.Label(new Rect(_pickerRect.x + 136f, bottomY + 4f, 240f, 22f), pageStr, _labelWhite);

            if (DrawCyberButton(new Rect(_pickerRect.x + 380f, bottomY, 110f, 28f), "SIGUIENTE >", false))
            {
                if (_pickerPage < totalPages - 1) _pickerPage++;
            }

            // Boton Limpiar
            if (DrawCyberButton(new Rect(_pickerRect.x + _pickerRect.width - 250f, bottomY, 90f, 28f), "VACIAR", false))
            {
                _selectedItems.Clear();
                SaveSelectedItemsToConfig();
            }

            // Boton Guardar y Activar
            if (DrawCyberButton(new Rect(_pickerRect.x + _pickerRect.width - 150f, bottomY, 134f, 28f), "APLICAR", true))
            {
                _showItemPicker = false;
                Plugin.ConfigScoutMode.Value = ScoutMode.CustomSelectedItems;
                SaveSelectedItemsToConfig();
                StartSearch();
            }

            // Bloquear clics dentro del modal para que no pasen a los botones del juego
            if (evt != null && _pickerRect.Contains(evt.mousePosition))
            {
                if (evt.type == EventType.MouseDown || evt.type == EventType.MouseUp)
                {
                    evt.Use();
                }
            }
        }
    }
}
