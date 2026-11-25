# Uzupełnienie etapu 1: źródła sprzętowe producenta

> Raport analizy źródeł z iteracji 2. W iteracji 4 wykonano już kompilację
> 15 obiektów AArch64 oraz trzech overlay w CI; [wyniki](stages.md)
> i [procedura](../kernel/README.md). Poniższe konflikty sprzętowe nadal
> pozostają otwarte; nie zbudowano pełnego obrazu ani nie wykonano boot testu.

## Wynik

Znaleziono istniejące źródła, nie ma potrzeby pisać M5IOE1 od zera.
Punktem odniesienia jest [m5stack/m5stack-linux-dtoverlays, commit a3fd3e8](https://github.com/m5stack/m5stack-linux-dtoverlays/tree/a3fd3e83c0247e16e194e7e40f7fc1f5be933dd4).
To źródła modułów/overlay sprzętowych, nie baza systemu. Nie przenosimy
Debiana, Kali, launchera producenta ani instalatorów AK-Rex.

Manifest `hardware/vendor-sources.toml` wskazuje 16 plików; wynik audytu
`hardware/vendor-evidence.json` zawiera SHA256 i pełne URL. Nie wykonano
instalacji ani kompilacji modułów. Plik COPYING i nagłówki poszczególnych
sterowników trzeba zachować przy późniejszym pakowaniu; firmware/binary LCD
wymagają osobnej weryfikacji praw redystrybucji.

## Co zostało ustalone

- **M5IOE1**: `modules/m5ioe1-1.0/m5ioe1.c` implementuje gpiochip,
  pinctrl, PWM i IIO, compatible `m5stack,m5ioe1`. Rejestry UID 0x00–01,
  rewizja 0x02, kierunek GPIO 0x03–04, wyjścia 0x05–06, wejścia 0x07–08,
  PWM 0x1b–22 i częstotliwość 0x25–26. Jest 14 linii, indeksy 0–13.
  Dodatkowy [interfejs Arduino/ESP-IDF M5Stack](https://github.com/m5stack/M5IOE1/blob/8401119bf171cb8f906fbe22e7490989077bbee8/src/M5IOE1.h)
  potwierdza tę numerację i przypisanie PWM4 do fizycznego IO10 (BL).
  Nie jest to dowód zgodności każdej rewizji firmware ekspandera.
- **Klawiatura**: vendor używa `m5stack,tca8418c`, nie standardowego bindingu
  upstream. W v5 są trzy mapy po **46 pozycji**, macierz 5×10. Własności
  `linux,keymap1/2` i FN/SYM wymagają vendor FSM; zwykły tca8418 nie musi ich
  interpretować. `sym/fn/shift-button-code` to scan codes, nie Linux KEY_Fn.
  Wyodrębnione wartości w `hardware/keymap-v5.json`; etykiety v3/v5 nie są
  automatycznie mapowaniem na SKU C154/C155 — potrzebny dowód rewizji PCB.
- **BQ27220**: dostępny dedykowany wariant bq27xxx, compatible `ti,bq27220`,
  overlay v5 ma adres 0x55 i pojemność 1750 mAh. Nie uruchamiamy skryptów
  profilowania baterii: mogą zapisywać konfigurację fuel gauge.
- **RTC — korekta poprzedniej analizy**: `rtc-ds1307.c` w przypiętym kernelu
  zawiera `epson,rx8130`; opcją jest `CONFIG_RTC_DRV_DS1307`. Brak rx8130
  w wcześniej zbadanym rtc-rx8581 nie oznaczał braku sterownika. Dowód:
  `hardware/rtc-evidence.json`. Nie potrzeba nowego sterownika RTC.
- **LCD**: źródła mają własny `panel-mipi-dbi-m.c` i `pwm_bl_m5stack.c`.
  Overlay oczekuje własnych compatible, nie dowolnego upstream ST7789.
  Vendor dostarcza także binarną sekwencję inicjalizacji; przed pakietem
  ustalić format/licencję i zależność ładowania firmware.

## Konkretne problemy przed integracją

1. Samodzielny `modules/rx8130/rx8130-overlay.dts` ma **0x68**, podczas gdy
   skonsolidowany v5 i dokumentacja urządzenia mają **0x32**. 0x68 jest też
   adresem BMI270. Nie instalować obu i nie kopiować samodzielnego overlay
   bez sprawdzenia fizycznej magistrali.
2. V5 deklaruje `everest,es8390`; audytowany upstream `es8389.c` dopasowuje
   `everest,es8389`, a vendor codec obsługuje obie nazwy. Samo występowanie
   upstream ES8389 nie zapewnia powiązania z tym DT ani machine driverem.
3. `ngpios=<16>` w v5 nie odpowiada 14 liniom gpiochip. Nie przyjmujemy,
   że wszystkie właściwości vendor są poprawnym bindingiem upstream.
4. `powerfail_suo.c` w sprawdzonym commicie wykonuje `handle_sysrq('u')`,
   zmniejsza jasność i ustawia disabled GPIO. Wywołania sync/kernel_power_off
   są zakomentowane. Nie jest to standardowy uporządkowany shutdown systemd;
   wymaga przeglądu czasów podtrzymania zasilania i testów utraty danych.
5. Makefile ma instalację do `/boot/firmware`, modyfikację aktywnego config
   oraz pobieranie skryptu z zewnątrz. Nie wywołujemy `make install` ani
   `config_setup`. Arch musi mieć własny pakiet z DESTDIR, wyraźnym wariantem
   płyty i modułami zbudowanymi dokładnie do użytego kernela.
6. **BQ27220 nie jest wyłącznie odczytowy**: w przypiętym
   `modules/bq27220-1.0/bq27xxx_battery.c`, funkcja
   `bq27xxx_battery_setup` wywołuje `bq27xxx_battery_settings`, która dla
   BQ27220 przechodzi do programowania parametrów z DT. Kod obejmuje
   FCC/design capacity, napięcia, profil i konfigurację NTC. Nie należy
   utożsamiać wyłączonego CONFIG_BATTERY_BQ27XXX_DT_UPDATES_NVM z blokadą
   tej osobnej ścieżki BQ27220. Wymagany osobny audyt/default bez zmiany
   profilu przed dopuszczeniem do bootowania. Kompilacja i depmod nie
   uruchamiają tej logiki i nie dotykają baterii użytkownika.

## Powtarzanie analizy

```sh
./build.sh --audit-vendor
./build.sh --check
```

Pierwsze polecenie zapisuje pobrane źródła w ignorowanym `.cache/vendor/`,
raporty w `out/`; nie wykonuje pobranego kodu. `inspect_keymap.py` sprawdza
numeryczne komórki map, zakres 5×10, unikalne pozycje i zgodność warstw.
Nie jest kompilatorem DT: odrzuca makra/preprocessor, nie sprawdza phandle,
nie potwierdza działania klawiszy. Hash wejścia pozwala powiązać raport
z konkretnym audytem. Dla innych rewizji analizować osobno ich overlay.

## Następny krok i ograniczenia

Nadal etap 1: audyt Kconfig/API modułów względem dokładnego `linux-rpi`,
wybór minimalnego zestawu vendor zamiast zastępowania wszystkiego, test
kompilacji oraz własne overlay bez powyższych konfliktów. W tym środowisku
nie ma `dtc`, nagłówków docelowego kernela ani urządzenia; nie zadeklarowano
kompilacji lub bootowania. Bramka obrazu pozostaje zamknięta.
