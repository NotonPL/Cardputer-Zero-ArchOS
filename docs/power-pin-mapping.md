# Rozbieżność numeracji zasilania — wynik analizy kodu

Status: **BLOCKED**, bez testu urządzenia. Dokładne źródła i SHA256:
[`hardware/power-mapping-evidence.json`](../hardware/power-mapping-evidence.json).
Nie zmieniono DT, firmware ani sekwencji wyłączania.

## Prześledzona ścieżka vendora

Przypięty DT v5 definiuje `disabled-gpios = <&m5ioe1 11 1>`.
Sterownik powerfail ustawia na nim logiczne 1, więc active-low oznacza fizyczne 0.
W `m5ioe1_gpio_set()` offset >= 8 wybiera rejestr `GPIO_O_H` (0x06),
a indeks bitu jest `offset % 8`. Dla offset11 daje to **bit3 rejestru 0x06**.
Kod nie ma specjalnego przekierowania tego offsetu do innego pinu lub rejestru
sterowania zasilaniem. Kierunek ustawiany jest analogicznie w GPIO_M_H.

## Co opisuje projekt Open-IOE1

Przypięty README społecznościowy identyfikuje:

| Linux offset | IO | MCU | Opisywana rola |
|---|---|---|---|
| 11 | IO12 | PB6 | LCD reset / SWDIO przy resecie |
| 13 | IO14 | PB7 | PWR_EN, podtrzymanie zasilania |

Kod `firmware/main.c` zawiera `IO_SWDIO = 11`, `IO_PWR = 13`.
Automat zasilania steruje `IO_PWR`, a `owned()` oddaje ten pin hostowi dopiero
po wyłączeniu firmware lock. Zatem **nawet zmiana DT z 11 na 13 nie stanowi
kompletnej, zweryfikowanej poprawki**. Wymaga znajomości własności pinu i wersji
firmware; zmiana lock w złym momencie może przerwać zasilanie.

## Korekta interpretacji wcześniejszego audytu

Wyścig z asynchronicznym remount jest rzeczywisty na poziomie kodu: po SysRq U
sterownik nie czeka na jego zakończenie. Natomiast stwierdzenie, że kolejna
operacja `disabled` na pewno odcina zasilanie CM0, **nie jest potwierdzone**.
Jeśli mapowanie społecznościowe odpowiada temu egzemplarzowi, może to być
reset LCD, nie bezpośrednie zwolnienie power-hold. Nie przyjmujemy komentarzy
sterownika ani opisu ZeroPower jako dowodu elektrycznej funkcji tego wyjścia.

## Bezpieczne następne dowody

Na działającym systemie producenta można później odczytać:

```sh
uname -r
cat /proc/cardputerzero_hw_id
```

To propozycja diagnostyki, **niewykonana na urządzeniu użytkownika**.
Drugi plik występuje w przypiętym driverze po rozpoznaniu REV 0x5A i czyta przez
regmap rejestr HW_VERSION 0xB8. Brak pliku również jest informacją, nie powodem
do wymuszania dostępu I2C. Nie wymaga instalacji naszego kernela ani uprawnień root
przy uprawnieniach 0444 ustawianych przez ten driver. HW id jest identyfikatorem
klasy sprzętu, nie wersją firmware 0xBA; sam nie rozstrzyga wszystkich różnic.

Następnie potrzebne są: analiza graficznych połączeń schematu V0.6.1,
potwierdzenie mapowania na stock firmware oraz zgodności z rewizją egzemplarza.
Nie wykonywać surowych zapisów I2C, GPIO, zmiany lock, resetu MCU ani flashowania
w celu „sprawdzenia, co się stanie”. Nie odłączać zasilania podczas zapisu.
