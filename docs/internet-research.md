# Badanie źródeł: AK-Rex, schemat i powerfail

Status: research źródeł, **nie test na urządzeniu**. Nie pobierano obrazów OS,
nie wykonywano instalatorów, nie dodawano repozytoriów APT ani nie flashowano MCU.
Strony są zmienne; wersje i deklaracje poniżej dotyczą odczytanej treści.
Nie aktualizujemy na ich podstawie przypiętego kernela projektu.

## 1. AK-Rex — materiały przydatne, ale nie gotowa baza Arch

- [Strona autora](https://ak-rex.com/) kieruje do
  [obrazów](https://images.ak-rex.com/) i konta GitHub `ak-rex`.
- Strona obrazów opisuje Cardputer Zero jako **pre-production hardware**
  i zapowiada osobny retail image. W odczytanej treści podaje Debian 13 Trixie
  oraz kernel 7.1.4. To deklaracja strony, nie wersja sprawdzona w uruchomionym
  obrazie ani dowód zgodności z egzemplarzem użytkownika.
- [README obrazu](https://images.ak-rex.com/CardPuter-Readme.txt) opisuje:
  kreator użytkownika/hasła/kraju Wi-Fi i sieci; usunięcie domyślnego konta pi;
  CLI na ekranie 320×170; APPLaunch uruchamiany komendą lub przytrzymaniem ESC;
  start desktopu po HDMI, jego zatrzymanie po odłączeniu i odtworzenie APPLaunch,
  jeśli był wcześniej aktywny.
- Są to przydatne scenariusze funkcjonalne dla naszych testów. README nie podaje
  pomiarów RAM, pełnego mechanizmu uprawnień, kodu hotplug ani dowodu bezpiecznego
  poweroff. Nie traktujemy opisu jako spełnienia naszych kryteriów.
- [Repo kernela](https://github.com/ak-rex/rpi-linux), odczytany HEAD
  `bb414f4cb32f725f02de09cf5e3a8d29bd40b56b` (domyślna gałąź `rpi-7.3.y`).
  Wersja domyślnej gałęzi nie musi odpowiadać kernelowi obrazu. Rekurencyjne
  drzewo GitHub było **truncated=true**; brak trafień nie dowodzi braku drivera.
  Dodatkowe przeglądanie `drivers/misc` (pełne poddrzewo), `drivers/platform`
  i wyszukiwanie kodu nie ustaliło źródła powerfail dla tego obrazu.
- [Repo APT](https://github.com/ak-rex/akrex-arm-repo) publikuje instrukcję
  dodania klucza/repozytorium Debiana. **Nie stosujemy jej w Arch Linux ARM.**

Decyzja: własny rootfs ALARM, pacman, launcher TOML i integracja usług.
Nie kopiować obrazu Debiana, instalatorów ani binarnych modułów AK-Rexa.
Ewentualny kod wymaga osobnego przeglądu licencji i zgodności API.

## 2. Schemat producenta — odnaleziony

[Dokumentacja M5Stack](https://docs.m5stack.com/en/CardputerZero) i
[schemat C154 V0.6.1](https://m5stack-doc.oss-cn-shenzhen.aliyuncs.com/1243/C154-CardputerZERO_SCH_V0.6.1_20260702.pdf).
Odczytano tekst PDF; ekstrakcja nie zachowuje wszystkich połączeń graficznych.
**Nie przypisujemy V0.6.1 do urządzenia użytkownika bez potwierdzenia.**

- PDF opisuje `G6_SW_DET` jako sygnał CM0 GPIO6 oraz sekcje SWITCH,
  `VSYS_PW_EN`, przetwornicę SY7088 zasilającą CM0 i M5IOE1.
- Dokumentacja pinów nazywa PYG14 `PWR_EN`, PYG5 `PWR_DET`, PYG2 `HW_DET`.
- Nie utożsamiać numeru GPIO CM0, indeksu gpiochip Linuksa, PYG ani fizycznego
  pinu MCU. Są to różne przestrzenie numeracji.
- PDF nie dostarczył w odczytanym tekście gwarantowanego czasu podtrzymania
  po zdarzeniu ani potwierdzenia zakończenia zapisu microSD.

Pełny schemat jest więc dostępny, ale wcześniejszy bloker zmienia się z
„nie odnaleziono schematu” na „potrzebna analiza połączeń, numeracji i firmware
zgodnego z egzemplarzem”. Samo znalezienie PDF nie zatwierdza poweroff.

## 3. ZeroPower — kandydat do porównania, nie przyjęta poprawka

[Repo](https://github.com/stefexec/ZeroPower), przeanalizowany plik:
[`driver/powerfail_suo.c`](https://github.com/stefexec/ZeroPower/blob/f6b5156d5c27d60150299359bbf66f64c45873a8/driver/powerfail_suo.c).
Commit `f6b5156d5c27d60150299359bbf66f64c45873a8`.

Kod rozpoznaje ten sam problem asynchronicznego SysRq U. Wywołuje
`orderly_poweroff(true)` i przenosi operację na `disabled-gpios` do `.shutdown()`
przy `SYSTEM_POWER_OFF`, nie przy reboocie. To wartościowy kierunek analizy,
nie dowód bezpieczeństwa:

- Po 15 s fallback wywołuje SysRq S, czeka 1000 ms, SysRq U, czeka 1500 ms
  i przełącza wyjście. Stały czas nie jest potwierdzeniem zakończenia I/O.
- `.shutdown()` oznacza fazę zamykania urządzeń, nie uniwersalny dowód
  poprawnego zakończenia wszystkich zapisów w każdej ścieżce wejścia do kernela.
- `remove()` nadal anuluje work bez wcześniejszego odłączenia/synchronizacji IRQ.
- Pin `disabled` nadal ma indeks 11. Potrzebne uzgodnienie z opisem PYG14.
- Nie kompilowano tego kodu z naszym kernelem i nie testowano go na urządzeniu.
- Metadane GitHub pokazały datę push późniejszą od daty sesji; zapisujemy commit
  jako treść dostępnego źródła, nie chronologiczny dowód stanu wydania na dziś.

Decyzja: nie uruchamiać install.sh, nie podmieniać modułu, nie przyjmować
marketingowego określenia „safe” jako wyniku naszej walidacji.

## 4. Open-IOE1 — ujawnia zależność od firmware

[Repo](https://github.com/prokrypt/CardputerZero-Open-IOE1), commit
`4369350e13ba29087b98f39169e57d31e9629e33`:
[README](https://github.com/prokrypt/CardputerZero-Open-IOE1/blob/4369350e13ba29087b98f39169e57d31e9629e33/README.md)
i [firmware/main.c](https://github.com/prokrypt/CardputerZero-Open-IOE1/blob/4369350e13ba29087b98f39169e57d31e9629e33/firmware/main.c).
Projekt opisuje reverse engineering aplikacji M5, nie oficjalną specyfikację.

Według README PYG14/PB7 podtrzymuje zasilanie po przełączeniu OFF;
firmware ma `PWR_EN lock` 0xB1, `OFF_TIME` 0xB2/B3 (domyślnie 2000 ms),
HW id 0xB8 i wersję 0xBA. Przeczytany kod implementuje automat wyłączania
z odmierzaniem `off_time`. **Nie jest to pomiar ani odczyt firmware użytkownika.**

Istotna rozbieżność: README mapuje Linux IO14/offset13 na PWR_EN, natomiast
vendor DT używa offset11 jako `disabled`. Przypięty vendor `m5ioe1.c` zapisuje
bity GPIO bez specjalnego mapowania offset11 na PWR_EN. Nie zmieniamy DT
na podstawie samego społecznościowego opisu: możliwe są różnice rewizji,
firmware lub inne znaczenie sygnału `disabled`.

Decyzja: **nie flashować zamiennego firmware**, nie pisać rejestrów 0xB1/0xB2
ani nie resetować MCU. Zmiana MCU może sama przerwać zasilanie i utrudnić recovery.
Następne badanie powinno uzgodnić schemat, kod stock firmware i numerację.

## 5. Wpływ na kolejne etapy

1. Dokończyć uzgodnienie powerfail ↔ M5IOE1 ↔ schemat; żadnego zgadywania pinu.
2. Przygotować bezpieczną diagnostykę istniejących interfejsów na stock systemie.
   Nie polecać `i2cget/i2cdump -f` obok aktywnego sterownika.
3. Dopiero potem własna poprawka, testy mock IRQ/GPIO i pełny build.
4. Fizyczny test na drugiej microSD z kopią danych nadal jest osobną bramką.
5. Hotplug HDMI i kreator z README AK-Rexa wykorzystać jako scenariusze
   porównawcze, nie zastępstwo pomiarów i niezależnej implementacji Arch.

Wyszukiwarki zwróciły też zgłoszenia o błędach I2C M5IOE1 i integracje Kali.
Nie rozszerzamy na tej podstawie twierdzeń o naszym sprzęcie; nieprzeanalizowany
PR ani tabela wsparcia innej dystrybucji nie stanowią dowodu działania.
