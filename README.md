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
`DATABASE`  | Filsti til backend-databasen i filstrukturen | `data input/backend-db03.db`
`OUTPUT_DIR` | Filmappe hvor output blir lagret | `data/output`
`RULES_FILE` | Python-fil med søk-erstatt-regelsett-lister |  `rules.py`
`EXEMPTIONS_FILE` | Python-fil med lister over ord som er unntatt regel-oppdateringene | `exemptions.py`
`NEWWORD_FILES` | CSV-filer med nyord som skal legges til  |   `nyord.csv, nyord2.csv`
`DIALECTS` | Navn på gyldige dialektområder | `e_spoken, e_written, sw_spoken, sw_written, w_spoken, w_written, t_spoken, t_written, n_spoken, n_written`


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
`-c, --config` | Filsti til en python-konfigurasjonsfil. | `config.py`
`-b, --write-base`  | Skriv ut base-leksikonet, altså original-transkripsjonene fra NST. | 
`-m, --match-words`  | Skriv ut hvilke ord som blir dekket av hvert regel-mønster. | 
`-l, --mfa-lexicon` | Formater leksikon-filer for å brukes med "Montreal Forced Aligner"-algoritmen. |
`-s, --spoken` | Sannsynlighet/vekttall (mellom 0 og 1) for talemålsnære transkripsjoner av ord i MFA-formaterte uttaleleksika. | `1.0`
`-w --written` | Sannsynlighet/vekttall (mellom 0 og 1) for skriftnære transkripsjoner av ord i MFA-formaterte uttaleleksika. | `1.0`
`-d, --dialects`  | Generer leksikonfiler bare for spesifikke dialektområder.  | `e_spoken, e_written, sw_spoken, sw_written, w_spoken, w_written, t_spoken, t_written, n_spoken, n_written`
`-r, --rules-file` | Python-fil med søk-erstatt-regelsett-lister. | `rules.py`  
`-e, --exemptions-file` | Python-fil med lister over ord som er unntatt regel-oppdateringene. | `exemptions.py`
`--no-exemptions`  | Ignorer unntakene til reglene. |
`-n, --newword-files` | CSV-filer med nyord som skal legges til.  |   `nyord.csv, nyord2.csv`
`--no-newwords`  |  Ignorer nyordsfiler i oppdateringen.
`-db, --database` | Filsti til backend-databasen i filstrukturen. | `data/input/backend-db03.db` 
`-o, --output-dir` | Filmappe hvor output blir lagret. | `data/output`
`-v, --verbose`  | Skriv ut logg-beskjeder til terminalen. `-vv` gir mer detaljerte beskjer, for debugging. |
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
pip install dist/lexupdater-0.2.0-py2.py3-none-any.whl      # OS-uavhengig
```
