# Testy i pomiary

## Na hoście (bez sprzętu)

`./build.sh --check`: 11 testów manifestu, identyfikatorów źródeł, brakujących
interfejsów, sztucznego sysfs/procfs i delty CPU. `bash -n build.sh`:
walidacja składni. `--image`: oczekiwany kod 2. To nie jest test bootowania.
`./build.sh --audit`: sieciowy odczyt konkretnych plików, SHA256 i URL.
Błąd API powoduje niezerowy wynik, raport zachowuje `fetch-error`.

## Na urządzeniu z działającym Linuksem

Skopiować `tools/diagnose.py`, uruchomić Pythonem 3.11+, np.:

```sh
python3 tools/diagnose.py --label inventory --output device.json
python3 tools/diagnose.py --label login --sample-seconds 30 --output login.json
```

Odczyt nie ładuje sterowników ani nie odpytuje rejestrów. Brak wpisu w sysfs
nie dowodzi braku komponentu. `capacity=null` oznacza brak odczytu, nie 0%.
`cpu_busy_percent=null` oznacza brak prawidłowej próbki. Raport nie odczytuje
kluczy SSH, haseł Wi-Fi, seriali USB ani całego dmesg, ale sekcja input może
zawierać identyfikatory sprzętu — przejrzeć przed publikacją.

Dodatkowo zebrać ręcznie: `uname -a`, wersje pakietów kernela/firmware,
`systemd-analyze time`, `systemd-analyze blame`, `lsusb`, `cat /proc/bus/input/devices`,
`cat /proc/asound/cards`, `ls -l /dev/dri /dev/fb*`. Nie wszystkie narzędzia
muszą być zainstalowane. Kopię boot config/DT przeglądać pod kątem sekretów;
nie udostępniać całej partycji systemowej z hasłami.

## Protokół docelowy — jeszcze niewykonany

- Podawać SKU, rewizję, kernel, commit OS, usługi i wersje pakietów.
- Minimum 5 zimnych startów dla każdego profilu, ten sam zasilacz/microSD.
- Po 60 s stabilizacji mierzyć 30 s CPU, RAM (MemTotal/MemAvailable), usługi.
- Osobne etykiety: boot przed logowaniem (docelowy unit pomiarowy jeszcze
  nie istnieje), login, launcher, HDMI 720p/1080p, jedna sesja SSH.
- CPU liczone z przyrostu /proc/stat, nie z chwilowego load average.
  iowait w narzędziu zaliczone do idle; raportować tę konwencję.
- Boot mierzyć systemd-analyze oraz zewnętrznie od włączenia do użytecznego
  terminala. Nie mylić uptime z czasem startu.
- Dla każdej opcjonalnej usługi A/B: CPU/RAM, gotowość sieci i poprawność UI.
- Energię mierzyć zewnętrznym miernikiem (jasność, radio, warunki stałe).
  Same procenty baterii nie są pomiarem mocy.
- Przed/po HDMI sprawdzić pozostałe procesy/cgroup, pamięć, brak restartu CLI.
- Funkcjonalnie: klawiatura wszystkie 46 klawiszy i kombinacje; LCD offsety,
  usypianie i powrót; SSH/SFTP; Wi-Fi reconnect; USB host/slave; zapis i
  bezpieczne wyłączenie; RTC po odłączeniu zasilania; dźwięk, kamera, IMU i IR
  dopiero na dostępnych wariantach sprzętu.

Brak wyników wydajności Cardputera w tej iteracji. Raport z kontenera x86_64
służył jedynie do smoke-testu kolektora i nie jest dołączony jako benchmark.
