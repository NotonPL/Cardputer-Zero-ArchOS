# Odczyt aktywnej konfiguracji powerfail

Narzędzie: `tools/inspect_power_dt.py`, Python 3, bez dodatkowych bibliotek.
Nie wymaga instalowania projektu ani zmiany fabrycznej karty.

## Co zbiera

- wersję kernela z `/proc/sys/kernel/osrelease`;
- HW id przez istniejący `/proc/cardputerzero_hw_id`;
- węzły `cardputerzero,powerfail-suo` z aktywnego Device Tree;
- phandle kontrolera, offset i flagi `disabled-gpios` oraz `irq-gpios`;
- status węzła i debounce;
- nazwę podpiętego sterownika urządzenia I2C o adresie 0x4f.

Nie odczytuje numeru seryjnego, MAC, profili Wi-Fi, haseł, cmdline, kluczy SSH,
całego debugfs ani surowych rejestrów I2C. Brak uprawnień/pliku nie powoduje
próby eskalacji. Wersja firmware M5IOE1 nie jest ustalana tym narzędziem.

## Opcjonalne wykonanie na fabrycznym systemie

Najpierw przenieść pojedynczy `tools/inspect_power_dt.py` z projektu na urządzenie
(np. przez własne połączenie SSH/SCP). Nie pobierać i nie wykonywać instalatorów.
W katalogu z plikiem:

```sh
python3 inspect_power_dt.py
```

Wynik JSON można skopiować z terminala. Opcjonalnie zapisać go pod **nową nazwą**
w katalogu domowym (to jedyny zapis, wykonywany przez przekierowanie powłoki):

```sh
( set -C; python3 inspect_power_dt.py > "$HOME/cardputer-power-dt.json" )
```

`set -C` zapobiega nadpisaniu istniejącego zwykłego pliku przez przekierowanie.
Nie używać sudo, nie montować debugfs, nie odłączać zasilania, nie zmieniać GPIO
ani I2C. Jeśli brakuje Pythona lub interfejsów, zgłosić to zamiast instalować
pakiety w fabrycznym systemie tylko dla tej diagnostyki.

## Interpretacja i ograniczenia

`resolved=true` oznacza jedynie rozpoznany phandle i dwukomórkową specyfikację
GPIO. Nie oznacza poprawności pinu, fizycznej obecności urządzenia ani sukcesu
probe. `status=okay` może występować nawet przy nieudanym probe.
Brak sterownika przy I2C 0x4f nie rozstrzyga przyczyny problemu.

Offset11 active-low potwierdziłby konfigurację omawianą w audycie, nie rolę
power-hold. Offset13 też wymagałby potwierdzenia własności pinu przez firmware.
Nie ma automatycznej naprawy ani oceny „safe”. Wynik zawsze zawiera
`hardware_validated=false`.

## Dotychczasowa walidacja narzędzia

Testy jednostkowe na sztucznym drzewie plików obejmują parsowanie big-endian,
rozwiązywanie GPIO, brak danych, uszkodzone komórki, nieobsługiwany format,
niejednoznaczny phandle, HW id, status disabled i ograniczenie wielkości odczytu.
To testy parsera na hoście, **nie wykonanie na Cardputerze**.
