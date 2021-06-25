# Lexupdater 

Lexupdater er et utviklingsverktøy for å oppdatere og utvide 
[NST-leksikonet](https://www.nb.no/sprakbanken/ressurskatalog/oai-nb-no-sbr-23/) 
med transkripsjoner for 4 dialekter og 30 000 nyord. 
Dialektutvidelsen skal lages ved hjelp av strengtransformasjoner 
(søk-erstatt-regler), mens nyorda legges til som lister med ord og
transkripsjoner.

## Kom i gang
### 1. Sett opp kode-miljøet
Sørg for at du har versjon `3.7` eller høyere av `python`.
Sett opp et virtuelt kodemiljø og installer python-pakkene som er listet i 
`requirements.txt`. 

### 2. Last ned data
Original-leksikonet er blitt lagret som en `sqlite`-database, 
og må lastes ned i forkant. 
Kontakt [Per Erik Solberg](https://github.com/peresolb) for å få tilgang 
til denne fila. 

Lagre databasefilen lokalt i inndata-mappen `data/input/`.

### 3. Konfigurér oppdateringen av leksikonet

Hovedskriptet til `lexupdater` konfigureres i `config.py`, 
hvor man bl.a. spesifiserer følgende variabler:

Variabelnavn | Forklaring | Default-verdi
---|---|---
`WORD_TABLE` | navnet på den midlertidige tabellen med ord fra leksikon-databasen | `"words_tmp"` 
`DATABASE`  | filnavnet til backend-databasen i filstrukturen | `data / input / backend-db03.db`
`OUTPUT_DIR` | filmappen hvor output blir lagret | `data / output`
`DIALECTS` | navnet på gyldige dialektområder | `e_spoken, e_written, sw_spoken, sw_written, w_spoken, w_written, t_spoken, t_written, n_spoken, n_written`
`RULES_FILE` | regelfil med søk-erstatt-regelsett-lister |  `rules.py`
`EXEMPTIONS_FILE` | unntaksfil med lister over ord som er unntatt regel-oppdateringene | `exemptions.py`


## Oppdatér leksikonet
Hovedprogramsnutten er i fila `lexupdater/lexupdater.py`, som kan kjøres med 
`python -m lexupdater` og med kommandolinje-argumenter som beskrevet under. 
Der det ikke angis "gyldige verdier" er flagget et boolsk argument som slås 
"på" .  

Flagg | Forklaring  | Gyldige verdier/eksempler
---   | ---          | ---
`-d`  | Generer leksikonfiler bare for spesifikke dialektområder  | `e_spoken, e_written, sw_spoken, sw_written, w_spoken, w_written, t_spoken, t_written, n_spoken, n_written`
`-b`  | Skriv ut base-leksikonet, altså original-transkripsjonene fra NST | 
`-m`  | Skriv ut hvilke ord som blir dekket av hvert regel-mønster | 
`-v`  | Skriv ut mer detaljerte debug-beskjeder i loggen | 
`-l`  | Angi et filnavn som loggen skrives til. Om ikke -l spesifiseres, skrives alt til terminalen. | `log.txt`

Kjører man `lexupdater` uten argumenter, 
genereres leksikonfiler med oppdaterte transkripsjoner for alle 
dialektområdene.


# For utviklere

I filen  `Makefile` er det flere automatiserte steg som kan kjøres med 
`make <prossessnavn>`-kommandoer:   

## Sett opp kodemiljøet

```shell
make setup
```

## Test koden
Kjør automatiske enhets- og integrasjonstester: 
```shell
make test
```
Oppsett for kvalitativ testing av leksikonoppdateringene 
vil komme på plass senere. 

## Sjekk kodekvalitet
Kjør en linter på koden for å se hvordan den forholder seg til 
pep8-konvensjonene: 
```shell
make lint
```

## Bygg `lexupdater` som en python-pakke
Ferdig-bygde Python-pakker er installérbare, og tillater å dele verktøyet 
som en vanlig fil, samt installere pakken med `pip`. 

### Windows 
```shell
python setup.py bdist --formats=wininst
```

### OS-uavhengig (ikke ferdig testet)
```shell
python setup.py bdist_wheel
```

## Installér `lexupdater` som en python-pakke 
Etter at python-pakken er bygget, vil den ligge i `dist`-mappen. Den kan nå 
installeres med `pip`: 

```shell

pip install dist/lexupdater-0.1.0-py2.py3-none-any.whl      # OS-uavhengig
```
