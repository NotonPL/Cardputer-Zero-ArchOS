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

Docelowe pakiety firmware, keymap, udev, DTBO i initramfs NIE są jeszcze
przygotowane. Osobny bundle poniżej jest wyłącznie artefaktem testowym.
Nie instalować tych kompilatów na fabrycznym systemie ani nie
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

## Pełny eksperymentalny build CM0/v5

`cardputer-v5.config` jest nowym fragmentem do allnoconfig dla przypiętego
źródła Raspberry Pi 6.18.64. To NIE zminimalizowany na podstawie pomiarów
config produkcyjny ani pełny port pakietu Arch. Ogranicza zakres kompilacji
do jawnych funkcji planowanego urządzenia zamiast budować tysiące obcych
sterowników. Kamera/V4L2 i pełny stos IR nie są jeszcze włączone w tym
wariancie testowym; test koncentruje się na podstawowym kernelu i 15 modułach.
Wartości governor/CMA/zram są ustawieniami kandydata do późniejszych testów,
nie dowodem oszczędności RAM/energii ani osiągniętych wyników.

Workflow `kernel-full.yml`:
1. Pobiera te same archiwa kontrolowane przez SHA256.
2. Uruchamia allnoconfig i zapisuje RZECZYWISTY wygenerowany config.
3. `check_kernel_contract.py` sprawdza wymagane funkcje i brak konkurujących
   sterowników upstream, zapisując również różnice względem fragmentu.
4. Buduje Image i wszystkie skonfigurowane moduły, bez obejścia modpost.
5. Buduje vendor `.ko` z pełnym Module.symvers i sprawdza vermagic.
6. Buduje CM0 DTB z symbolami i nakłada trzy overlay przez fdtoverlay.
   `check-cm0-dt.sh` sprawdza obecność M5IOE1/klawiatury i adresy RTC 0x32,
   baterii 0x55, IMU 0x68 w połączonym drzewie.

To strukturalny test DT, nie dt-schema ani emulacja sekwencji firmware:
nie nakładamy jeszcze wszystkich overlay/parametrów stock (VC4/dwc2/IR/
kamera). Nie instalować połączonego DTB na urządzeniu. Sterowniki, firmware,
polaryzacje i shutdown nadal wymagają testów sprzętowych. Status faktycznie
wykonanych przebiegów znajduje się w docs/stages.md; samo istnienie tego
workflow nie jest dowodem udanego builda.

## Staging i kontrola zależności modułów

`scripts/stage-kernel-test.sh KERNEL_BUILD VENDOR_BUILD DT_RESULTS NEW_OUTPUT`
przyjmuje wyłącznie udany raport buildera w trybie modules. Tworzy świeży
katalog z układem `/usr/lib/modules` i lokalnym symlinkiem `lib -> usr/lib`.
Wywołanie kernelowego modules_install dostaje jawne INSTALL_MOD_PATH tego
katalogu; nie jest to instalacja na runnerze/urządzeniu. Następnie dołącza
vendor `.ko`, usuwa wyłącznie symlinki build/source ze stagingu i uruchamia
depmod z połączoną tablicą symboli kernela i vendor. Dowolny komunikat stderr
z tej kontroli jest błędem, a nie ignorowanym ostrzeżeniem.

Bundle zachowuje Image, config, wyniki DT, moduły, hashe, źródłowy lock,
raport i tekst GPL. Workflow archiwizuje go jako kernel-test-bundle.tar.gz.
Nazwa NIE oznacza obrazu microSD ani kompletnego rootfs. Brak boot firmware
Pi, firmware LCD/Wi-Fi/BMI270, initramfs i userspace Arch. Nie flashować.
Sterownik baterii może programować kontroler podczas inicjalizacji; sukces
modpost/depmod tego nie testuje ani nie akceptuje. Powerfail także pozostaje
blokadą bootowania. Archiwum jest przeznaczone do dalszej analizy/pakowania,
nie do samodzielnego instalowania na fabrycznej karcie.

W CI cache jest indeksowany źródłowym lockiem, platformą i wersją GCC;
zmieniony fragment konfiguracji może korzystać z inkrementalnego buildu
tylko przy zgodnym źródle/toolchain. Kconfig i kontrola kontraktu są zawsze
uruchamiane ponownie. Nie twierdzimy jeszcze, że binaria są bitowo
powtarzalne między runnerami (czas/build-host i cały toolchain wymagają
osobnego przypięcia).

### BQ27220: telemetry-only safety patch

`patches/series.json` locks the patch and both input/output source hashes.
The builder always applies it before either object compilation or module linking;
there is no bypass flag. `report.json` preserves upstream source hashes plus
separate patch and modified-source hashes. A mismatch stops the build.

For BQ27220 both transport write callbacks return `-EPERM` before any transfer.
Automatic profile programming is skipped; forced reset is denied. This blocks
MAC/sysfs command writes as well as profile/unseal operations. Normal register
reads retain the I2C register-selector write phase: this is not an electrically
write-free bus. Extended MAC/data-memory reads requiring command writes may fail.
No claim is made that all exposed telemetry is functional on hardware.

`tools/test_battery_transport.py --drivers <staged-drivers>` compiles the exact
hash-verified patched read/write/settings functions with fake I2C callbacks.
It checks 768 blocked writes, settings skip/reset denial, successful reads,
read-error propagation and unchanged other-chip transport. It does not load a
module, contact a device, or prove real gauge/charger/power-loss safety.
