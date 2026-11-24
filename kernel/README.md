# Budowanie sterowników Cardputera — etap integracji, nie wydanie OS

## Wejścia

`build-lock.json` przypina commit i SHA256 archiwów kernela oraz vendor.
Kernel 6.18.64 to źródło wskazane przez audytowany PKGBUILD Arch ARM linux-rpi
(`1d580617de584d86734df49377c72a3cdddfbfb2`). Hash archiwum kernela pochodzi
z tego PKGBUILD; hash vendor policzono po pobraniu przypiętego commita.
Samo źródło Raspberry Pi nie obejmuje jeszcze poprawek/config pakietu Arch.
To kandydat do testów API, NIE binarnie zgodny zamiennik fabrycznego 6.18.39.

```sh
python3 tools/fetch_build_sources.py kernel --destination .cache/build-kernel
python3 tools/fetch_build_sources.py vendor --destination .cache/build-vendor
```

Python 3.11+, internet do codeload.github.com. Pobranie jest buforowane,
SHA256 sprawdzany również dla cache. Docelowy katalog musi być nowy.
Ekstrakcja nie zachowuje właścicieli ani specjalnych plików; kontroluje
ścieżki i symlinki. Pobieranie/ekstrakcja nie wykonuje kodu źródeł.
Źródła i kompilaty pozostają poza Git. Kernel wymaga kilku GB miejsca.

## Test zgodności C API (objects)

Na hoście developerskim, NIE na fabrycznej karcie urządzenia:
- GNU make, gcc-aarch64-linux-gnu, flex, bison, bc, libssl-dev, libelf-dev;
- dla dalszych overlay także cpp/dtc.
CI instaluje je na jednorazowym runnerze Ubuntu, nie na Cardputerze.

```sh
cp hardware/reference/stock-cm0-v5/kernel.config .cache/build-kernel/.config
make -C .cache/build-kernel ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- olddefconfig
make -C .cache/build-kernel ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- -j2 modules_prepare
python3 tools/build_vendor_modules.py \
  --kernel-build .cache/build-kernel --vendor-source .cache/build-vendor \
  --mode objects --output out/vendor-api
```

Uwaga: olddefconfig przenosi referencyjne opcje do nowego kernela; nie jest
to zatwierdzony config Arch. Tryb objects kompiluje 15 jednostek `.o` i
sprawdza ELF64/AArch64. Nie wykonuje modpost/linkowania `.ko`. Nie wymaga
ani nie generuje kompletnego Module.symvers. Przejście testu nie dowodzi
zgodności ABI, eksportów, bindingów, firmware, bootowania czy shutdown.
Raport i log są zachowane także przy błędzie Kbuild. CI udostępnia log,
przygotowany config i kernelrelease, nie ogłasza sukcesu przed zakończeniem.

## Pełne moduły (modules) — kolejna bramka

Po pełnym zbudowaniu WŁAŚCIWEGO kernela wraz z zależnościami i tablicą
symboli można użyć identycznego polecenia z `--mode modules` i nowym output.
Tryb ten odmawia działania bez niepustego Module.symvers; nie ustawia
KBUILD_MODPOST_WARN ani opcji wymuszających pominięcie kontroli symboli.
Obecność pliku nie dowodzi sama, że jest poprawny: użytkownik procesu
budowania musi zapewnić jego pochodzenie z dokładnie tego kernela/config.
Dla CONFIG_MODVERSIONS samo modules_prepare nie wystarcza.
Po budowie nadal konieczne: sprawdzenie modinfo/vermagic/zależności,
konfliktów sterowników, staging pakietu pacman i test na drugiej karcie.

## Własne Kbuild zamiast vendor install

`build_vendor_modules.py` kopiuje źródła C/nagłówki do NOWEGO output,
zapisuje SHA256 i generuje własny Kbuild dla zestawu obserwowanego w v5:
M5IOE1, tca8418c, DRM LCD/backlight, BQ27220, audio, gpio-forwarder,
powerfail oraz BMI270/magnetometr. Uwzględnia simple-amplifier wymagany
przez vendor audio. Źródła FSM są include klawiatury, nie osobny moduł.
Legacy st7789v_m5stack/fbtft nie jest budowany obok wybranego DRM panelu.
Zestaw zawiera powerfail WYŁĄCZNIE do kontroli kompilacji: nie oznacza to
akceptacji jego sekwencji wyłączania. Nie ma insmod/modprobe/depmod,
make install, config_setup ani zapisu do /boot czy /lib/modules hosta.
Zewnętrzny kod wykonywany przez Kbuild pochodzi z przypiętych źródeł;
kompilować bez roota na izolowanym hoście.

Pliki firmware, konfiguracja keymap, udev, DTBO i initramfs NIE są jeszcze
pakowane. Nie instalować tych kompilatów na fabrycznym systemie ani nie
flashować katalogu output jako obrazu. Instrukcje są procedurą budowania;
aktualny faktyczny wynik testów dokumentujemy w docs/stages.md.

## Kontrola składni overlay v5

```sh
bash scripts/check-vendor-overlays.sh .cache/build-vendor out/vendor-overlays
```

Jawna lista obejmuje skonsolidowany v5, bq27220_v5 i bmi270_bmm150_overlay.
Skrypt nie wybiera sprzecznego samodzielnego overlay RTC. Używa cpp, dtc
oraz fdtget, zachowuje wszystkie ostrzeżenia i listę fixupów oraz hashe.
Nie wykonuje fdtoverlay na CM0 DTB: sukces kompilacji nie oznacza zgodności
phandle, bindingów lub sprzętu. Nie instaluje wyników. Obecne konflikty
opisane w docs/vendor-integration.md nadal wymagają rozwiązania.
