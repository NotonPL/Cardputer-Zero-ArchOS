# Powerfail — audyt źródeł, nie walidacja sprzętu

Data: 2026-11-20. Status: **BLOCKED / hardware_validated=false**.
Nie zmieniono zachowania sterownika ani nie uruchamiano zaniku zasilania.

## Powtarzalne wejścia

Vendor `m5stack/m5stack-linux-dtoverlays`:
`a3fd3e83c0247e16e194e7e40f7fc1f5be933dd4`.

| Plik | SHA256 |
|---|---|
| `modules/CardputerZero/powerfail_suo.c` | `6fc04c0c6457aa6fc1791d043642e6a00bd332358bd5cf3381cf7c10195e3885` |
| `modules/CardputerZero/cardputerzero-v5-overlay.dts` | `ab46df7faa21d517199889e639d5839209529d628b687bbf9d3f698a6dd3b110` |

Prześledzono również przypięty kernel Raspberry Pi
`b0b7d2006113562307ade2f6a075b03f3a781346`:
`drivers/tty/sysrq.c`, `fs/super.c`, `kernel/reboot.c`.
Wejścia pobiera `tools/fetch_build_sources.py`; nie wykonywać instalatorów vendora.

## Fakty z kodu

1. DT v5: GPIO6, zbocze opadające, odczyt raw active-low,
   `debounce-ms=500`, wyjście `disabled-gpios=<&m5ioe1 11 1>`
   (active-low). Komentarze sterownika wspominające GPIO23 nie opisują tego DT.
2. IRQ ustawia znacznik atomowy, wyłącza własne IRQ i kolejkuje work.
   Work czeka 500 ms i sprawdza aktualny poziom. Błąd odczytu lub stan wysoki
   resetuje znacznik i ponownie włącza IRQ. Potwierdzony niski stan nie uzbraja
   go ponownie.
3. Aktywna ścieżka wywołuje tylko `handle_sysrq('u')`, następnie wygasza
   podświetlenie i ustawia logiczne 1 na `disabled_gpiod` (fizyczne low).
   `handle_sysrq('s')` i `kernel_power_off()` są zakomentowane.
4. **Wywołanie SysRq U nie czeka na zakończenie remount.**
   `sysrq_handle_mountro()` wywołuje `emergency_remount()`, które alokuje
   i kolejkuje osobny work. Dopiero ten work przechodzi po superblokach.
   Sterownik może zatem zmienić wyjście M5IOE1 przed zakończeniem remount.
   Przy nieudanej alokacji work nie zostanie zakolejkowany.
5. Nie ma potwierdzenia zakończenia remount ani obsługi jego wyniku,
   zatrzymania usług systemd czy uzgodnienia czasu podtrzymania zasilania.
   Nie oznacza to, że remount nigdy nie synchronizuje danych; oznacza brak
   gwarancji zakończenia przed kolejną operacją sterownika.
6. `remove()` wywołuje `cancel_work_sync()` przed zarządzanym zwolnieniem IRQ.
   Samo to nie wyklucza nowego IRQ kolejkującego work po anulowaniu.
   Wymaga poprawki porządku wyłączenia/synchronizacji IRQ przed anulowaniem
   i testu wyścigu unload; obecny audyt nie dowodzi wystąpienia UAF na sprzęcie.
7. Aktywny niski poziom już przy probe nie jest sprawdzany. Samo zbocze
   opadające nie stanowi obsługi wszystkich stanów początkowych.

## Dlaczego nie dopisujemy po prostu poweroff

`orderly_poweroff()` również kolejkuje pracę. Nie jest barierą zakończenia
shutdown i nie uzasadnia natychmiastowego przełączenia pinu. Z kolei twarde
`kernel_power_off()` nie zastępuje zamknięcia usług. Bez znajomości funkcji
M5IOE1 GPIO11, stanu wyjścia przy probe, czasu podtrzymania i prawdziwego
mechanizmu wyłączenia CM0 arbitralna zmiana może pogorszyć bezpieczeństwo.
Nie dodajemy zgadywanego opóźnienia ani obietnicy bezpiecznego odcięcia.

## Wymagane dane i bramka następnej implementacji

- SKU i rewizja PCB, schemat toru zasilania, wersja firmware M5IOE1.
- Potwierdzenie znaczenia GPIO6 i M5IOE1 GPIO11 oraz stanów startowych.
- Pomiar: źródło zasilania, poziom baterii, obciążenie, moment zbocza,
  rzeczywisty czas do utraty zasilania; nie wymyślać budżetu czasowego.
- Ustalenie wspieranego końcowego poweroff (osobno od zdarzenia powerfail).
- Wybór ścieżki kontrolowanego shutdown z potwierdzonym zakończeniem przed
  ewentualnym wyłączeniem toru oraz jawnej polityki awaryjnej.

## Plan testów — jeszcze niewykonany

Najpierw testy programowe ze sztucznymi GPIO/IRQ i bez fizycznego wyjścia:
nieaktywny/aktywny start, drgania, błąd odczytu, seria IRQ, ponowne uzbrojenie,
unload podczas work i IRQ, błąd inicjalizacji, poprawna kolejność shutdown.
Następnie druga karta microSD z kopią danych i pomiary sprzętowe: zwykły
shutdown, zanik wejścia z baterią/bez niej, niski stan baterii i intensywny zapis.
Po każdym teście kontrola systemu plików z innego systemu i analiza logów.
Nie wykonywano żadnego z tych testów na urządzeniu.

**Decyzja:** vendor `powerfail_suo.ko` pozostaje wyłącznie artefaktem kompilacji.
Nie zatwierdzamy ładowania modułu, instalacji overlay ani obrazu dla użytkownika.
Wyłączenie samego sterownika również nie jest rozwiązaniem ochrony danych.

## Identyfikacja egzemplarza po audycie

Użytkownik potwierdził pełny wariant i dostarczył zdjęcia pudełka oraz obudowy;
odczyt oznaczeń: [hardware/user-device.md](../hardware/user-device.md).
M5IOE1 0x4F oraz BQ27220 są zgodne z oczekiwanymi oznaczeniami. Nie wynika
z tego potwierdzenie rewizji v5, funkcji GPIO11 ani czasu podtrzymania.
Wyszukiwanie kodu GitHub w `m5stack/m5-docs` dla `CardputerZero` nie zwróciło
wyników; to ograniczony wynik wyszukiwania, nie dowód braku dokumentacji.
Schemat zasilania pozostaje do pozyskania i analizy.

## Aktualizacja po badaniu Internetu i materiałów AK-Rexa

**Schemat V0.6.1 został odnaleziony**; wcześniejsze stwierdzenia o braku
pozyskanego schematu opisują stan sprzed tego badania. Źródła, przypięte commity,
ograniczenia i nowe rozbieżności: [internet-research.md](internet-research.md).
Pozostaje dopasowanie schematu/firmware do egzemplarza i uzgodnienie offset11
`disabled` z PYG14 `PWR_EN`. Społecznościowe ZeroPower i Open-IOE1 nie zostały
zainstalowane ani zatwierdzone jako rozwiązanie. Nie ma jeszcze podstaw do
przejścia z blokera do deklaracji bezpiecznego wyłączania.
## Rozstrzygnięcie ścieżki rejestru (nie funkcji elektrycznej)

[power-pin-mapping.md](power-pin-mapping.md) śledzi offset11 do bit3 rejestru
0x06. Open-IOE1 opisuje ten pin jako LCD reset, a PWR_EN jako offset13.
Dlatego **nie jest potwierdzone, że operacja `disabled` odcina zasilanie CM0**.
Asynchroniczny remount pozostaje faktem kodowym, ale jego skutek sprzętowy
wymaga potwierdzenia. Nie zamieniono automatycznie offset11 na offset13:
w społecznościowym firmware pin13 ma dodatkowo własność sterowaną lock.
