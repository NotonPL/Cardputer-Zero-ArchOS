# Materiały użytkownika na Google Drive — pierwsza inspekcja

## Zakres odczytu

Odnaleziono folder `cardputerzeroinfo`: 51 pozycji bezpośrednich,
w tym podfolder overlays. Zestaw na tym poziomie odpowiada plikom partycji
startowej, nie pełnemu rootfs. Nie należy nazywać go kompletną kopią systemu.
Przeczytano tylko `config.txt` i `cmdline.txt`; nie pobrano całego zestawu.

Odnaleziono też obraz `Cardputer-Zero-Debian-13-Trixie-7.1.4.img`,
**6 878 658 560 bajtów** (około 6,41 GiB). Limit pobierania pojedynczego pliku
przez dostępny konektor wynosi 100 MiB. Obrazu nie pobierano, nie montowano,
nie uruchamiano i nie analizowano jego partycji. Obecność pliku nie oznacza
potwierdzenia jego zawartości lub pochodzenia.

## Odczyt fabrycznej konfiguracji

`config.txt`:
- `arm_64bit=1`, `auto_initramfs=1`;
- I2C, I2S, SPI włączone;
- `gpu_mem=128`, `vc4-kms-v3d,cma-64`, `max_framebuffers=2`;
- jawny `imx219`, `camera_auto_detect=0`;
- w sekcji `[all]`: UART, dwc2, cardputerzero-v5-overlay,
  bq27220_v5, bmi270_bmm150_overlay, IR RX GPIO13 i TX GPIO12.

To potwierdza zapisany wybór overlay v5, nie rewizję PCB ani aktywne drzewo.
Ustawienia pamięci GPU/CMA nie są naszym wynikiem optymalizacji; nie przenosić
ich bez pomiarów i analizy modelu pamięci KMS/firmware.

`cmdline.txt` wskazuje ext4, rootwait, `console=tty1`, quiet,
`fbcon=map:off`, `fsck.repair=yes` i region Wi-Fi `AE`.
Nie kopiujemy identyfikatora partycji źródłowej do docelowego obrazu.
Region `AE` nie jest właściwym domyślnym wyborem dla każdego użytkownika:
przyszły kreator ma zapytać o rzeczywisty kraj użytkowania (np. PL w Polsce),
bez automatycznej zmiany aktualnej karty. Wartość fbcon to obserwacja wejścia,
nie potwierdzenie jej semantyki/działania z naszym kernelem.

## Prywatność i dalsze porównanie

Nie odczytywano `user-data`, `network-config`, `meta-data`: mogą zawierać
ustawienia kont, sieci i identyfikatory. Nie publikować zawartości rootfs,
kluczy SSH, haseł, profili Wi-Fi lub historii terminala w GitHub.

Następne przydatne materiały z obrazu AK-Rexa to wybrane pliki konfiguracyjne:
boot config, lista plików modułów i ich vermagic, źródła/skrypty hotplug HDMI,
usługi launchera i kreatora oraz reguły udev. Najpierw lista ścieżek i przegląd
pod kątem sekretów, potem wybrane małe pliki — nie cały prywatny rootfs.
Nie uruchamiać dostarczonych skryptów w celu ich zbadania.

Zgłoszone przez użytkownika `uname -r`: 6.18.39+rpt-rpi-v8, HW id 0x06.
Ten odczyt nadal nie podaje wersji firmware M5IOE1 ani mapowania power-hold.
