# Decyzje architektoniczne — propozycje, nie wdrożone optymalizacje

## Baza i boot

Arch Linux ARM AArch64, pacman i systemd. Dwie ścieżki:
- mainline `linux-aarch64` + U-Boot: oficjalna ścieżka Zero 2, ale dodatkowa
  weryfikacja CM0 i peryferiów;
- `linux-rpi` AArch64: istniejący CM0 DTS, sterowniki ES8389/BMI270 w audytowanym
  źródle; **kandydat początkowy** z racji zgodności sprzętu, nie wyniku RAM.

Nie mieszamy DTB/modułów z inną wersją kernela. Firmware Pi jest wymaganym
elementem startu; nie jest zastępowany bootloaderem x86/UEFI. Przed etapem 2
trzeba zweryfikować zawartość pakietów firmware i licencje dystrybucji.
Plan obrazu: tablica DOS, FAT boot + ext4 root, fstab po PARTUUID/UUID,
manifest wersji/podpisów/SHA256; bez zależności od mmcblk0/mmcblk1.
Nie ma jeszcze ustalonej konfiguracji startowej ani obrazu.

## CLI, sieć, konfiguracja

Wbudowany terminal na fbcon, o ile wybrana ścieżka display go udostępni.
Czcionka 6×10 daje około 53×17 znaków, 8×8 około 40×21; czytelność i dostępne
fonty trzeba sprawdzić na panelu, nie zakładać z wymiarów.

Sieć: porównać istniejący systemd-networkd + wpa_supplicant/iwd z
NetworkManager. Pierwsza opcja ma mniej funkcji/potencjalnie procesów;
druga wygodniejszy offline kreator i profile. Brak pomiarów nie pozwala
wybrać zwycięzcy RAM/CPU. SSH domyślnie zamknięte do zakończenia first boot,
bez wspólnych haseł, bez udostępniania root przez sieć. Host keys generowane
na urządzeniu. Konto administracyjne oddzielne od codziennego; żadnego
NOPASSWD ALL, root aplikacje przez jawne potwierdzenie i autoryzację sudo.

Systemowe ustawienia w /etc/cardputer, użytkownika w ~/cardputer/{apps,
scripts,config,themes,plugins,logs,backups,data}. Launcher: niezależne TOML
z argv, bez `shell=True` i bez eval. SSH to osobna granica parsowania
(remote ssh uruchamia shell!), wymaga jawnego, przetestowanego kodowania
argumentów. Import nie może automatycznie uruchamiać kodu ani podążać za
symlinkami/ścieżkami ../. Dodawanie ulubionych/skrótów tylko w danych
użytkownika; administrator nie interpretuje plików użytkownika jako root.
Język launchera wybieramy po pomiarze prostego C/ncurses kontra Python
stdlib (czas implementacji kontra koszt interpretera). Obecne narzędzia
Pythona są narzędziami audytu, nie decyzją o runtime launchera.

## HDMI — decyzja odroczona do etapu 7

| Wariant | Zgodność / funkcje | Koszt do zmierzenia |
|---|---|---|
| Xorg + Openbox | dojrzały X11, swobodne aplikacje | serwer i WM, buforowanie ekranu |
| labwc + Wayland | integracja DRM/KMS, zwykłe okna | wlroots, GPU, biblioteki, ewentualny Xwayland |
| Cage | prosta sesja jednego programu | ograniczone zarządzanie wieloma aplikacjami |

Bez pomiarów nie deklarujemy „najlżejszego”. Wspólny warunek: tylko HDMI,
bez przejęcia wbudowanego panelu, boot bez monitora nie startuje GUI.
Obsługa DRM hotplug (nie stały polling), debounce i ponowny odczyt wszystkich
HDMI po zdarzeniu. Sesja jako użytkownik przez logind, osobny cgroup,
po odłączeniu zakończenie całej grupy procesów, nie samo okno launchera.
Trzeba przetestować także HDMI już obecne podczas boot, szybki replug,
wiele konektorów i timeout zamykania. Samo DRM „connected” nie daje prawa
uruchomienia procesu root z dowolnym DISPLAY użytkownika.

## RAM, energia i SD

Zram, limity journald/volatile, tmpfs i governor to eksperymenty A/B, nie
pakiet magicznych sysctl. Zram kosztuje RAM i CPU; tmpfs konkuruje o 512 MB;
volatile usuwa logi potrzebne do diagnozy boot. USB autosuspend może zepsuć
Ethernet; nie wyłączamy huba podczas zapisu. Nie blokujemy timerów bezpieczeństwa
ani usług na ślepo. Kamera/audio/GUI opcjonalne. Najpierw działanie, potem
pomiar, na końcu optymalizacja.
