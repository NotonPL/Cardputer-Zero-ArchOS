# Egzemplarz użytkownika — identyfikacja

## Źródła i poziom pewności

Użytkownik potwierdził „cardputer zero pełny” i przesłał dwa zdjęcia:
`20261124_175729.jpg`, `20261124_175725.jpg` (pudełko i tył urządzenia).
Nazwy plików są identyfikatorami załączników, nie dowodem daty wykonania.
Zdjęć nie dodajemy do repozytorium; poniżej tylko odczyt oznaczeń.

- Wariant docelowy: **Cardputer Zero pełny, nie Lite** — deklaracja użytkownika.
- Pudełko: „CardputerZero Transparent Black”.
- Rewizja PCB: **nieustalona**. Nie utożsamiać z wersją overlay `v5`.
- SKU: nieodczytany z dostarczonych zdjęć.

## Odczytane oznaczenia, nie wyniki diagnostyki

| Element | Oznaczenie |
|---|---|
| Moduł obliczeniowy | Raspberry Pi CM0 |
| Panel | ST7789, 170×320 (pudełko) |
| Klawiatura | TCA8418RTWR, 46 klawiszy (pudełko) |
| Kamera | IMX219, 8 MP |
| Czujniki | BMI270 IMU + BMM150 magnetometr (pudełko) |
| RTC | RX8130CE |
| Audio | ES8389 |
| Bateria | 1750 mAh, BQ27220 |
| Ekspander | M5IOE1, ADDR 0x4F (etykieta urządzenia) |

Powyższe określa oczekiwany zestaw peryferiów pełnego wariantu. Nie potwierdza
obecności/odpowiedzi urządzeń na magistrali, wersji ich firmware ani działania
sterowników. Schemat blokowy nadrukowany na obudowie nie jest schematem
połączeń zasilania; nie rozstrzyga znaczenia GPIO11 ani czasu podtrzymania.

## Wpływ na projekt

- Zachować kamerę, BMI270 i BMM150 w zakresie pełnej walidacji sprzętu.
- Nie traktować braku magnetometru w innych rewizjach jako cechy tego egzemplarza
  bez diagnostyki; pudełko deklaruje jego obecność.
- Overlay v5 pozostaje kandydatem sprawdzonym kompilacyjnie/strukturalnie,
  nie automatycznie zatwierdzoną konfiguracją tego egzemplarza.
- Nie wymagać od użytkownika rozkręcania urządzenia na tym etapie.
- Blokery powerfail opisano w `docs/powerfail-audit.md`; identyfikacja wariantu
  ich nie usuwa.

## Odczyt zgłoszony przez użytkownika

Użytkownik podał wynik diagnostyki fabrycznego systemu:

- kernel: `6.18.39+rpt-rpi-v8`;
- HW id: `0x06`.

Źródło: wiadomość użytkownika, nie zdalne wykonanie poleceń przez agenta.
Identyfikator nie jest numerem firmware MCU ani samodzielnym dowodem rewizji PCB.
Dostarczony na Drive `config.txt` włącza `cardputerzero-v5-overlay`,
`bq27220_v5` i `bmi270_bmm150_overlay`; jest to dowód konfiguracji zapisanej
na karcie, nie odczyt aktywnego DT ani walidacja wszystkich peryferiów.
Szczegóły inspekcji: `docs/drive-reference-review.md`.
