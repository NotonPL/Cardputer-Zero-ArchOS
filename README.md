# Cardputer Zero ArchOS

Dedykowany system terminalowy **Arch Linux ARM / AArch64** dla M5Stack
Cardputer Zero. **Status: etap 1, integracja sprzętu zablokowana.**
Nie ma jeszcze obrazu nadającego się do instalacji. Repozytorium nie jest
Raspberry Pi OS, kopią AK-Rex ani gotową dystrybucją z dopisanym menu.

## Co działa teraz

- pełny eksperymentalny build Image/modułów i 15 vendor `.ko` w CI,
- scalenie trzech overlay v5 z DTB CM0 i staging z kontrolą symboli/CRC,
- [potwierdzony wynik CI](https://github.com/NotonPL/Cardputer-Zero-ArchOS/actions/runs/45438187490)
  (artefakt testowy kernela, **nie obraz do flashowania**),

- audyt źródeł przypiętego kernela przez GitHub API (hash każdego pliku),
- audyt przypiętych źródeł producenta (M5IOE1/BQ27220/LCD/klawiatura),
- walidacja i eksport trzech warstw mapy klawiatury v5 (46 pozycji),
- bezinwazyjna diagnostyka Linux i zbieranie próbek CPU/RAM,
- testy offline na sztucznym sysfs/procfs i CI,
- jawne blokowanie budowania obrazu do czasu rozwiązania integracji.

Wymagania narzędzi: Python **3.11+** (wyłącznie biblioteka standardowa),
Bash; audyt online dodatkowo `gh` z dostępem do publicznego GitHub API.

```sh
./build.sh --check
./build.sh --audit
./build.sh --audit-vendor
python3 tools/diagnose.py --output out/device.json --label inventory
```

Diagnostykę uruchom na Cardputerze z aktualnie działającym Linuksem.
Na komputerze deweloperskim raport dotyczy tego komputera, **nie urządzenia**.
Nie wymaga `sudo`, nie skanuje aktywnie I2C, nie zmienia rejestrów ani usług.
Przed udostępnieniem raportu przejrzyj identyfikatory urządzeń wejściowych.

## Dokumentacja modułów

- [Proces kompilacji sterowników i granice testów API/ABI](kernel/README.md)

- [Konfiguracja z fizycznego CM0/v5 i jej analiza](hardware/reference/stock-cm0-v5/README.md)
- `tools/inspect_stock_config.py`: statyczny raport Kconfig/boot bez zmiany urządzenia

- [Aktualizacja: źródła vendor, DT i mapa klawiatury](docs/vendor-integration.md)
- [Pierwszy audyt kompatybilności](docs/compatibility.md)
- [Plan, bramki i wynik tej iteracji](docs/stages.md)
- [Procedura diagnostyki i pomiarów](docs/testing.md)
- [Decyzje architektoniczne](docs/architecture.md)
- `hardware/sources.toml`: manifest audytu, `hardware/source-evidence.json`: wynik
- `tools/audit_sources.py`: weryfikacja obecności kodu, nie zgodności sprzętu
- `tools/diagnose.py`: odczyt sysfs/procfs na żądanie
- `tests/`: izolowane testy narzędzi; `.github/workflows/`: automatyzacja

`./build.sh --image` kończy się kodem 2 i **nie tworzy obrazu**.
Nie flashuj archiwum źródeł na kartę microSD.
