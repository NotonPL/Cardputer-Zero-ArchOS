# Etapy i raport iteracji

## Iteracja 5: pełny kernel, moduły `.ko`, DT i staging (etap integracji)

**Wynik potwierdzony:** [run 45438187490 — success](https://github.com/NotonPL/Cardputer-Zero-ArchOS/actions/runs/45438187490),
commit cfddd992401f414bdd071b45adffc510090a2f70. Metadane kroków i artefaktu:
`kernel/full-build-evidence.json`. Zbudowano Image 6.18.64 oraz wszystkie
moduły wskazane eksperymentalnym fragmentem CM0/v5, pełne Module.symvers,
15 vendor `.ko` (ścisły modpost, kontrola AArch64/vermagic), bazowy DTB CM0
i trzy overlay. Scalenie fdtoverlay i kontrole węzłów/adresów przeszły.

Staging do NOWEGO katalogu zawiera moduły upstream/vendor w /usr/lib/modules,
Image, config, wyniki DT, hashe i licencję. Depmod -e -E z połączonymi symbolami
przeszedł BEZ stderr. Archiwum kernel-test-bundle.tar.gz jest wewnątrz artefaktu
experimental-kernel-build w tym runie. To nie jest rootfs/obraz microSD,
nie zawiera firmware Pi/peryferiów ani initramfs; NIE flashować/instalować.
Nie pobrano go do sandboxa (przekierowania storage GitHub poza allowlistą);
wyniki kroków potwierdzono przez API GitHub, artefakt jest do pobrania w UI.

### Problemy rzeczywiście wykryte i poprawione

- Pierwszy build Image/modułów przeszedł, lecz początkowy allnoconfig odrzucił
  ustawienia platformy bez nadrzędnego ARCH_BCM. Kontrakt wygenerowanego
  config wykrył to; dodano rodziców Broadcoma, USB-net, HID, serdev i zram.
  Sukces kompilacji początkowego Image NIE był dowodem obsługi CM0.
- Run 45434358931 zatrzymał modpost na brakujących matrix_keypad_*;
  jawne INPUT_MATRIXKMAP rozwiązało brak biblioteki dla zewnętrznej klawiatury.
  Uzupełniono też zależności UART/thermal i sterowniki zegara/cpufreq.
- Run 45436266442 zlinkował 15 `.ko` i scalił DT, ale staging zatrzymał się
  na ostrzeżeniach wersji symboli. MODVERSIONS bez BASIC_MODVERSIONS nie
  zapewniało kodowania CRC wymaganego przez obecną kontrolę kmod. Włączono
  BASIC_MODVERSIONS/GENKSYMS, dodano kontrakt i preflight oraz test regresji;
  nie wyłączono modpost ani kontroli CRC. Końcowy run przeszedł depmod.
- DTC nadal generuje ostrzeżenia w źródłach upstream/vendor. Są zachowane;
  powodzenie scalenia nie oznacza walidacji dt-schema/elektryki sprzętu.

Nowe pliki: kernel/{cardputer-v5.config,contract.json,full-build-evidence.json},
.github/workflows/kernel-full.yml, tools/check_kernel_contract.py,
scripts/{check-cm0-dt,stage-kernel-test}.sh,
tests/{test_kernel_contract,test_kernel_staging}.py. Builder/preflight,
README kernela i dokumentacja integracji także zaktualizowane.

Testy lokalne: **51/51 OK**, kontrola składni skryptów i diff OK.
Nadal brak boot/load testu Arch i pomiarów urządzenia. Kernel config jest
kandydatem integracyjnym, nie wynikiem pomiarowej optymalizacji. Kamera/IR,
firmware, initramfs i userspace Arch są niekompletne. BQ27220 ma ścieżkę
programowania parametrów podczas inicjalizacji; vendor powerfail nie jest
zatwierdzonym bezpiecznym shutdown. To blokady przed dopuszczeniem obrazu
na sprzęt. Fabryczna karta użytkownika nie została zmieniona.

## Iteracja 4: powtarzalne budowanie sterowników (integracja etapu 1)

Dodano przypięte archiwa i ich SHA256 (`kernel/build-lock.json`), pobieranie
z kontrolowaną ekstrakcją, własny Kbuild i builder 15 modułów. Nie wykonuje
vendor make install/config_setup ani żadnego ładowania sterowników.
Źródła kernela 6.18.64 wskazane przez audytowany pakiet Arch są kandydatem;
referencyjny config 6.18.39 jest przenoszony przez olddefconfig na potrzeby
API testu, nie jest jeszcze zatwierdzonym config obrazu Arch.

Lokalnie: 41/41 testów narzędzi OK; sprawdzono SHA256/ekstrakcję obu archiwów,
staging 26 plików C/h oraz składnię skryptów. Na GitHub Actions wykonano
rzeczywistą cross-kompilację wszystkich 15 obiektów `.o` i walidację ich
ELF AArch64: [run 45429656971 — success](https://github.com/NotonPL/Cardputer-Zero-ArchOS/actions/runs/45429656971),
commit 163ed5068ad1b4152f1220fdd313338ad0066a02. Testy offline w CI również OK.

Tryb `modules` wymaga pełnej tablicy Module.symvers; nie zbudowano jeszcze
pełnego kernela ani linkowanych modułów `.ko`. Żadnego boot/load testu ani
pomiaru RAM/energii. Pobranie artefaktów CI do tego sandboxa jest blokowane
przez przekierowanie do hosta Azure; status kroków sprawdzono przez GitHub.
Logi/config/raport pozostają dostępne w artefakcie workflow.

Pliki: `tools/{fetch_build_sources,build_vendor_modules}.py`,
`tests/test_build.py`, `kernel/{build-lock.json,README.md}`,
`.github/workflows/kernel-api.yml`, `scripts/check-vendor-overlays.sh`.
Builder dostępny także przez `./build.sh --drivers ...`.
Kontrola cpp/dtc/fixupów v5 zachowuje ostrzeżenia i nie aplikuje overlay do
CM0 DTB. Drugi [run 45430245930 — success](https://github.com/NotonPL/Cardputer-Zero-ArchOS/actions/runs/45430245930)
na commicie 12d548390b3535bd39760658ed7bc8d42e8b3471 ponownie zbudował
15 obiektów oraz skompilował trzy overlay (płyta v5/bateria/IMU).
Nie oznacza to zgodności bindingów ani akceptacji vendor powerfail.

## Iteracja 3: konfiguracja z fizycznego urządzenia (etap 1)

Użytkownik udostępnił kernel config i config.txt z działającego CM0,
Debian 13, kernel 6.18.39+rpt-rpi-v8, overlay v5. Zachowano referencję
w `hardware/reference/stock-cm0-v5/` wraz z analizą i SHA256 wejść.
Nie identyfikuje to automatycznie rewizji PCB ani commita modułów vendor.

Dodano `tools/inspect_stock_config.py` i `tests/test_stock_config.py`.
Raport rozróżnia opcje wyłączone/nieobecne i zachowuje filtry firmware;
nie stosuje ustawień do urządzenia. Istotne: CONFIG_MODVERSIONS=y,
BQ27XXX/ES8389 upstream wyłączone mimo obecnych modułów zewnętrznych,
fbcon włączony, fonty 8×8/8×16, gpu_mem=128 i overlay cma-64.
Nie zmieniono rezerwacji pamięci i nie wyciągnięto wyników RAM z konfiguracji.

Testy offline: 30/30 OK, w tym odtworzenie raportu z załączonych plików.
Nadal brak kompilacji modułów i boot testu Arch. Szczegóły, pochodzenie
obserwacji użytkownika i granice wnioskowania w README referencji.

## Iteracja 2: źródła vendor i mapa klawiatury (etap 1 nadal trwa)

Znaleziono i przypięto źródła producenta dla M5IOE1/BQ27220/LCD/klawiatury.
Potwierdzono upstream RX8130 w rtc-ds1307. Wyodrębniono trzy warstwy po
46 pozycji z v5; nie są to jeszcze testy fizycznej klawiatury.
Szczegóły i konflikty DT/shutdown: [vendor-integration.md](vendor-integration.md).

Nowe pliki: hardware/{vendor-sources.toml,vendor-evidence.json,rtc-sources.toml,
rtc-evidence.json,keymap-v5.json}, tools/inspect_keymap.py,
tests/test_keymap.py, docs/vendor-integration.md. Zmienione: audytor źródeł
(opcjonalny cache i ochrona ścieżek), build.sh (--audit-vendor), README,
dokumentacja kompatybilności i ten raport.

Testy: 23/23 offline OK; audyt 16 plików vendor i 2 plików RTC bez błędów;
validator rzeczywistego v5: 5×10, 46 pozycji w każdej warstwie.
Nie kompilowano modułów/DT, nie uruchomiono instalatora, nie testowano boot.
Obraz nadal zablokowany. Brak źródeł nie jest już główną blokadą M5IOE1;
pozostają zgodność API/bindingów, wybór rewizji PCB i bezpieczne wyłączanie.

## Iteracja 1: stan historyczny (częściowo wykonany)

Wykonano analizę producenta/ALARM, audyt przypiętego źródła kernela,
identyfikację różnic CM0/Zero 2, macierz kandydatów sterowników i blokad.
Dostarczono rzeczywiste narzędzia diagnostyki i audytu, nie atrapę UI.
Nie wykonano portowania, budowy kernela, pierwszego startu ani testów GPIO.

Pliki: README.md, build.sh, .gitignore, hardware/{sources.toml,
source-evidence.json}, tools/{audit_sources.py,diagnose.py},
tests/test_tools.py, .github/workflows/check.yml i docs/{compatibility,
architecture,testing,stages}.md.

Wynik testów lokalnych: 11/11 unittest OK; bash -n OK; audyt 15 plików bez
błędów pobrania (3 identyfikatory nie znalezione); smoke test kolektora na
hoście OK; próba --image zatrzymana kodem 2 zgodnie z projektem.
Nie oznacza to, że sprzęt, initramfs lub obraz działają.

Blokady: brak fizycznego Cardputera w środowisku, brak dostępu powłoki do
mirrorów ALARM, niezweryfikowany protokół M5IOE1, poweroff/bateria/RTC,
mapa klawiatury oraz integracja DT/firmware. Najpilniej potrzebny SKU/revizja
i raport diagnostyki z działającego systemu producenta. Nie wymagamy
przekazywania haseł lub sekretów ani dostępu root przez Internet.

## Kolejne bramki (niezrealizowane)

| Etap | Warunek akceptacji |
|---|---|
| 1 analiza | źródła/bindingi M5IOE1 i zasilania, mapa klawiatury, zgodny zestaw firmware/kernel/DT |
| 2 obraz bazowy | podpisane wejścia ALARM, powtarzalny manifest, partycje/fstab, bezpieczeństwo kont, build host testy |
| 3 boot | rzeczywisty boot na CM0, trwały zapis i bezpieczny shutdown, logi i odzyskiwanie |
| 4 panel/klawiatura | fbcon, 46 klawiszy, FN/SYM, poprawny reset/BL, brak konfliktów pinów |
| 5 optymalizacja | pomiary bazowe i A/B, brak regresji funkcjonalnych |
| 6 launcher | TOML/schema, menu/search/favorites/recent/shortcuts, bezpieczne argv/tmux/SSH/root, CRUD/import/export |
| 7 HDMI | porównanie zasobów, hotplug/unplug, cgroup cleanup, brak GUI bez HDMI |
| 8 sprzęt | każdy moduł z diagnostyką/testem/disable, różne SKU |
| 9 skrypty | niezależny katalog użytkownika i rozszerzenia, walidacja uprawnień |
| 10 utrzymanie | pacman, świadome aktualizacje, backup/restore i integralność, test przerwanej aktualizacji |
| 11 wydajność | powtarzalne raporty CLI/login/menu/HDMI/SSH/energia |
| 12 wydanie | zweryfikowany obraz microSD, SHA256/podpis, instrukcja flash/recovery, pełny test od czystej karty |

Kreator offline będzie częścią obrazu bazowego przed uznaniem go za bezpieczny:
bez domyślnych zdalnych haseł, hostname/user/admin/password, timezone/locale,
klawiatura, Wi-Fi/SSH i moduły. Niedokończony kreator nie może wystawić SSH.

## Flashowanie / odzyskiwanie

**Obecnie brak artefaktu do flashowania.** Nie podajemy destrukcyjnego `dd`
dla nieistniejącego obrazu. Na tym etapie zachować stockową kartę nietkniętą,
a przyszłe testy wykonywać na drugiej karcie. Procedura końcowa musi obejmować
weryfikację podpisu/hash, identyfikację nośnika, potwierdzenie usunięcia danych,
weryfikację zapisu, powrót do stock i odzyskanie konfiguracji z backupu.
