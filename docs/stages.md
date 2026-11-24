# Etapy i raport iteracji

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
