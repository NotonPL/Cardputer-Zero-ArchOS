# Referencja z fizycznego urządzenia użytkownika

Pliki dostarczone przez użytkownika, zachowane bez zmian:
- `config.txt`: fabryczny `/boot/firmware/config.txt` (może zawierać lokalne zmiany),
- `kernel.config`: załącznik `config-6.18.39+rpt-rpi-v8.txt`, odczyt
  `/boot/config-6.18.39+rpt-rpi-v8`.

To materiał porównawczy, NIE konfiguracja docelowa Arch ani pliki do instalacji.
Brak potwierdzonego numeru rewizji całej płytki; nazwa katalogu opisuje CM0
oraz aktywowany wariant overlay v5, nie identyfikację SKU.

Użytkownik podał: CM0 Rev 1.0, Debian 13 Trixie, `uname -r`
`6.18.39+rpt-rpi-v8`. W wynikach lsmod/modinfo widoczne są vendor moduły
M5IOE1, klawiatury, LCD/backlight, baterii, audio i powerfail w `extra/`.
Ich vermagic zgłasza SMP/preempt/mod_unload/modversions/aarch64.
Klawiatura zarejestrowana jako tca8418c pod I2C 1-0034; sysfs baterii
raportował Charging/42%. To obserwacja użytkownika, nie nasz pełny test
sprzętu ani pomiar wydajności. `srcversion` nie identyfikuje commita Git.

## Powtarzalna analiza

Z katalogu głównego projektu:

```sh
python3 tools/inspect_stock_config.py \
  --kernel hardware/reference/stock-cm0-v5/kernel.config \
  --boot hardware/reference/stock-cm0-v5/config.txt \
  --output out/stock-analysis.json
```

`analysis.json` zawiera SHA256 wejść, istotne symbole Kconfig i wpisy boot
z numerami linii i sekcjami. Narzędzie niczego nie instaluje, nie wykonuje
include ani nie interpretuje filtrów firmware jako efektywnych ustawień.
Test automatyczny sprawdza zgodność dołączonego raportu z wejściami.

## Ustalenia dla portu Arch

- `CONFIG_ARM64=y`, moduły i `CONFIG_MODVERSIONS=y`. Budowanie modułów wymaga
  dokładnego źródła/config, nagłówków i właściwego `Module.symvers` z pełnego
  buildu; samo `modules_prepare` nie wystarcza dla modversions. Nie przenosić
  `.ko` pomiędzy wersjami kernela ani wymuszać ładowania przez force-vermagic.
- `CONFIG_BATTERY_BQ27XXX` i `CONFIG_SND_SOC_ES8389` są wyłączone, mimo że
  zgłoszone moduły vendor są załadowane. To nie sprzeczność: zewnętrzne moduły
  zbudowano oddzielnie. Sam config kernela nie opisuje ich pełnego zestawu.
- Upstream `CONFIG_KEYBOARD_TCA8418=m` nie zastępuje vendor tca8418c/FSM.
  Trzeba unikać konfliktu aliasów i podwójnego wiązania urządzeń.
- RTC `CONFIG_RTC_DRV_DS1307=m`, zgodne ze zgłoszonym rtc_ds1307.
- fbcon i emulacja fbdev są dostępne; fonty 8×8 i 8×16 włączone.
  Przy 320×170 daje to teoretycznie 40×21 lub 40×10 pełnych komórek.
  Nie jest to potwierdzenie przypisania VT do LCD, czytelności ani braku GUI.
- DRM/VC4/DBI oraz I2C/SPI to częściowo moduły. Muszą znaleźć się w rootfs
  i być dostępne przy inicjalizacji; wczesny terminal może wymagać initramfs.
- `gpu_mem=128` i `vc4-kms-v3d,cma-64` są w boot config. To dwa różne
  mechanizmy, nie wynik pomiaru RAM. CMA jest pamięcią zarządzaną przez Linux
  z możliwością użycia dla stron migrowalnych; nie wolno po prostu odjąć
  128+64 od 512 MB i uznać reszty za RAM użytkownika. Domyślne Kconfig
  `CMA_SIZE_MBYTES=5` nie dowodzi rozmiaru runtime po DT/parametrach boot.
  `gpu_mem` nie zmniejszamy w ciemno przed sprawdzeniem kamery i firmware.
- `CONFIG_ZRAM=m`, kompresor domyślny zstd; `CONFIG_ZSWAP=y`, ale
  `CONFIG_ZSWAP_DEFAULT_ON` wyłączony. Nie dowodzi to aktywności swap/zram
  w uruchomionym systemie. Profil wybierzemy po pomiarach A/B.
- `[cm5] dtoverlay=dwc2,dr_mode=host` nie jest ustawieniem dla CM0.
  `[all] dtoverlay=dwc2` nie dowodzi wymuszonego host mode.
- Splash wskazuje niestandardowy plik, którego nie otrzymano. Nie będzie
  zależnością obrazu Arch. `auto_initramfs=1` nie potwierdza obecności
  poprawnego initramfs. Ustawienia arm_boost nie są pomiarem zegara CPU.

## Nadal niewiadome

Zgodność znalezionego commita vendor z faktycznymi modułami, pełna zawartość
nagłówków i Module.symvers (otrzymano tylko informację o dowiązaniu), bieżący
DT po zastosowaniu overlay, cmdline/initramfs/boot firmware oraz procedura
bezpiecznego wyłączania. Nie wykonano kompilacji, bootowania Arch ani testów
wszystkich funkcji. Fabryczny system pozostaje nienaruszony.
