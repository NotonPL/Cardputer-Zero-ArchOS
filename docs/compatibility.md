# Etap 1 — kompatybilność (2026-11-20)

## Źródła i granice weryfikacji

1. [Dokumentacja M5Stack](https://docs.m5stack.com/en/CardputerZero),
   odczytano sekcje Specifications, PinMap i Product Comparison.
2. [Arch Linux ARM: Zero 2](https://archlinuxarm.org/platforms/armv8/broadcom/raspberry-pi-zero-2):
   oficjalna ścieżka AArch64, mainline + U-Boot, VC4. To dowód wsparcia
   rodziny RP3A0, **nie certyfikacja Cardputera/CM0**.
3. [PKGBUILD linux-rpi](https://github.com/archlinuxarm/PKGBUILDs/blob/1d580617de584d86734df49377c72a3cdddfbfb2/core/linux-rpi/PKGBUILD):
   `arch=(armv7h aarch64)`, wersja deklarowana 6.18.64, źródło Raspberry Pi
   `b0b7d2006113562307ade2f6a075b03f3a781346`.
4. [PKGBUILD linux-aarch64](https://github.com/archlinuxarm/PKGBUILDs/blob/1d580617de584d86734df49377c72a3cdddfbfb2/core/linux-aarch64/PKGBUILD):
   alternatywny kernel wieloplatformowy (w odczytanym źródle 7.3.5).

Nie pobrano rootfs ani binarnych pakietów z mirrorów ALARM: hosty te są poza
listą dozwoloną dla połączeń powłoki tego środowiska. Istnienie PKGBUILD nie
oznacza pobrania, zweryfikowania podpisu lub uruchomienia pakietu.

Audyt wykonano na **źródle kernela wskazanym przez PKGBUILD**, nie na przypadkowym
`latest`. Wyniki z URL i SHA256 plików są w `hardware/source-evidence.json`.
`found` oznacza wyłącznie obecność pliku/identyfikatora. `identifier-not-found`
nie dowodzi braku obsługi w całym drzewie ani nie wyklucza sterownika zewnętrznego.
Błąd sieci/autoryzacji jest osobnym błędem, nigdy „brakiem sterownika”.
Nie używamy niepełnego, rekurencyjnego indeksu GitHub do dowodzenia nieobecności.

## CM0 a Zero 2 W

Procesor i 512 MB RAM są wspólne, ale nośnikiem Cardputera jest **CM0**.
W przypiętym źródle istnieje `bcm2710-rpi-cm0.dts` dla arm64. Należy sprawdzić
identyfikację płyty przez firmware, wybór DTB, bootloader i wyprowadzenia;
nie podmieniamy bez dowodu DT na Zero 2 W.

M5IOE1 pod I2C `0x4f` kontroluje reset LCD PYG12, podświetlenie PYG10,
wspólny reset klawiatury/huba PYG3, zasilanie i multipleksery.
Jego NRST jest na GPIO16. GPIO6 to detekcja przełącznika zasilania.
Brak uzgodnionego sterownika/integracji M5IOE1 jest **blokadą podstawowego UI
oraz bezpiecznego wyłączania**. Nie zapisujemy eksperymentalnych wartości do I2C.

USB ma fizyczny przełącznik Host/Slave. W Slave hub, Ethernet i część portów
są odłączone. Nie należy diagnozować ich wtedy jako awarii sterownika.
CAP nie obsługuje hotplug — rozszerzenia wkładać przy wyłączonym urządzeniu.
Wariant Lite nie ma kamery/IMU/BMM150; C154-V1 nie ma BMM150.

## Macierz (żaden element nie jest jeszcze sprawdzony na urządzeniu)

| Komponent | Kod/kandydat | Integracja, której nadal brakuje |
|---|---|---|
| CM0/RP3A0 | arm64 DTS CM0; `linux-rpi` AArch64 | firmware, boot, karta, UART, właściwy DT |
| ST7789v3 | DRM panel ST7789V; staging fbtft ST7789V | nie są automatycznie zamienne; SPI MOSI10/SCLK11/CS8/DC25, TE5; geometria/offsety 320×170, rotacja, M5IOE1 reset/BL, fbcon |
| TCA8418 | `tca8418_keypad.c` | I2C1 0x34, IRQ GPIO27, reset przez ekspander; rzeczywista macierz, FN/SYM, debounce/repeat |
| Wi-Fi | brcmfmac | firmware/NVRAM/CLM zgodne z modułem, regulatory domain, reconnect |
| Bluetooth | hci_bcm | transport UART, firmware i rfkill/overlay do potwierdzenia |
| Ethernet SR9900A | sr9700/sr9800 tylko kandydaci | nazwa handlowa nie dowodzi zgodności; odczytać USB VID:PID i alias modułu; sprawdzone tabele zawierają 0fe6:9700/9702 i 0fe6:9800, nie dowodzą SR9900A |
| USB GL852G | sterowniki hosta + hub USB | reset PYG3, tryb fizycznego przełącznika, topologia; nie przełączać przy aktywnym nośniku |
| BQ27220 | rodzina bq27xxx istnieje | audyt pliku I2C nie znalazł bq27220; nie podstawiać innego compatible bez datasheet i walidacji |
| RX8130CE | rtc-rx8581 tylko kandydat | brak rx8130 w zbadanym pliku; nie utożsamiać RX8130 z RX8010/RX8581; I2C 0x32 |
| ES8389 | `sound/soc/codecs/es8389.c` istnieje | ASoC machine/DT, zegary, routing; I2C 0x10, I2S18–21, AMP GPIO24, HP GPIO17 |
| IMX219 | sterownik V4L2 i overlay | port/linie CSI oraz zegary/zasilanie; marketingowe „4-Lane” nie dowodzi konfiguracji portu CM0 |
| BMI270 | `bmi270_core.c` istnieje | I2C 0x68, firmware inicjalizacyjne, orientacja osi |
| BMM150 | rodzina bmc150_magn | audyt pliku nie znalazł bmm150; AUX za BMI270, nie mylić 0x10 z kodekiem na głównej magistrali |
| IR | gpio-ir-recv / gpio-ir-tx | GPIO13 RX i GPIO12 TX, polaryzacje, overlay, test odbioru/nadawania |
| GPIO/SPI/I2C/UART | natywne interfejsy Linux | pinctrl i konflikty z LCD/I2S; GROVE wybór GPIO4, zasilanie PYG4; nie wystawiać /dev/mem użytkownikom |

## Warunek zamknięcia analizy

Potrzebne: rewizja/SKU urządzenia, działający stock DT i konfiguracja boot
(z legalnie dostępnych źródeł lub od użytkownika), protokół/źródła obsługi
M5IOE1, matryca klawiatury, dane USB, ścieżka baterii/RTC i shutdown.
Następnie osobny audyt Kconfig, bindingów i licencji — sam plik `.c` nie
potwierdza aktywacji w pakiecie. Nie tworzymy pozornie gotowego overlay z
wymyślonym `compatible` lub numerami klawiszy.
