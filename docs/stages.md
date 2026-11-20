# Etapy i raport iteracji

## Bieżąca iteracja: etap 1 (częściowo wykonany, bramka otwarta)

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
