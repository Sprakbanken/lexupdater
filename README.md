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
`DATABASE`  | filnavnet til backend-databasen i filstrukturen | `data / input / backend-db03.db`
`OUTPUT_DIR` | filmappen hvor output blir lagret | `data / output`
`RULES_FILE` | regelfil med søk-erstatt-regelsett-lister |  `rules.py`
`EXEMPTIONS_FILE` | unntaksfil med lister over ord som er unntatt regel-oppdateringene | `exemptions.py`
`NEWWORD_FILE` | Fil som definerer en pandas dataramme med nyord som skal legges til  |   `newword.py`
`DIALECTS` | navnet på gyldige dialektområder | `e_spoken, e_written, sw_spoken, sw_written, w_spoken, w_written, t_spoken, t_written, n_spoken, n_written`


## Oppdatér leksikonet
Hovedprogramsnutten er i fila `lexupdater/lexupdater.py`, som kan kjøres med 
`python -m lexupdater` og med kommandolinje-argumenter som beskrevet under. 
Kjører man `lexupdater` uten argumenter, 
genereres leksikonfiler med oppdaterte transkripsjoner for alle 
dialektområdene.

Der det ikke angis "gyldige verdier" er flagget et boolsk argument som slås 
"på" .  
Samme informasjon er tilgjengelig med `python -m lexupdater -h`.


Flagg | Forklaring  | Gyldige verdier/eksempler
---   | --- | ---
`-b, --write-base`  | Skriv ut base-leksikonet, altså original-transkripsjonene fra NST. | 
`-m, --match-words`  | Skriv ut hvilke ord som blir dekket av hvert regel-mønster. | 
`-d, --dialects`  | Generer leksikonfiler bare for spesifikke dialektområder.  | `e_spoken, e_written, sw_spoken, sw_written, w_spoken, w_written, t_spoken, t_written, n_spoken, n_written`
`-r, --rules-file` | Regelfil med søk-erstatt-regelsett-lister. | `rules.py`  
`-e, --exemptions-file` | Unntaksfil med lister over ord som er unntatt regel-oppdateringene. | `exemptions.py`
`-n, --newword-file` | Fil som definerer en pandas dataramme med nyord som skal legges til.  |   `newword.py` 
`--db` | Filnavnet til backend-databasen i filstrukturen. | `data / input / backend-db03.db` 
`-o, --output-dir` | Filmappen hvor output blir lagret. | `data / output`
`-v, --verbose-info `  | Skriv ut logg-beskjeder til terminalen. |
`-vv, --verbose-debug` | Skriv mer detaljerte logg-beskjeder til terminalen. | 
`-c, --config-file` | Filsti til en python konfigurasjonsfil. | `config.py`
`-h, --help` | Print informasjon om alle argumentene og avslutt. | 


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
som en vanlig fil, samt å installere pakken med `pip`. 

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
