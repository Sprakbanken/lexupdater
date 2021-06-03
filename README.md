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
Sett opp et virtuelt kodemiljø ved hjelp av `Makefile`: 

```shell
make setup
```

### 2. Last ned data
Original-leksikonet er blitt lagret som en `sqlite`-database, 
og må lastes ned i forkant. 
Kontakt [Per Erik Solberg](https://github.com/peresolb) for å få tilgang 
til denne fila. 

Lagre databasen lokalt i data-mappen: `./data/input/backend-db02.db`

### 3. Konfigurér oppdateringen av leksikonet

Hovedskriptet til `lexupdater` konfigureres i `config/config.py`, 
hvor man bl.a. spesifiserer følgende variabler:

* `DATABASE`: stien til backend-databasen i filstrukturen
* `OUTPUT_DIR`: filmappen hvor output blir lagret
* `DIALECTS`: navnet på dialektområdene
* `RULES`: liste med søk-erstatt-regelsett 
* `EXEMPTIONS`: lister over ord som er unntatt regel-oppdateringene


## Oppdatér leksikonet
Hovedprogramsnutten er i fila `lexupdater/lexupdater.py`, som kan kjøres med 
`python -m lexupdater` og med kommandolinje-argumenter som beskrevet under. 
Der det ikke angis "gyldige verdier" er flagget et boolsk argument som slås 
"på" .  

Flagg | Forklaring  | Gyldige verdier/eksempler
---   | ---          | ---
`-d`  | Generer leksikonfiler bare for spesifikke dialektområder  | `e_spoken, e_written, sw_spoken, sw_written, w_spoken, w_written, t_spoken, t_written, n_spoken, n_written`
`-b`  | Skriv ut base-leksikonet, altså NST | 
`-m`  | Dersom man bare vil se listene over hvilke ord som blir dekket av hver regel | 
`-v`  | Skriv ut mer detaljerte debug-beskjeder i loggen | 
`-l`  | Angi et filnavn som loggen skrives til. Om ikke -l spesifiseres, skrives alt til terminalen. | `log.txt`

Kjører man `lexupdater` uten argumenter, 
genereres leksikonfiler med oppdaterte transkripsjoner for alle 
dialektområdene.


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

## Installér `lexupdater` som en python-pakke 
Du kan lage en pip-installérbar python-pakke 
(komprimerte filer med `.tar.gz`, `.egg`, `.whl` suffiks) 
via `setup.py`-skriptet: 

```shell
python setup.py install     # Installer direkte fra repoet 
```
Dette lagrer en `.egg`-fil i en ny mappe `dist`. 
Denne fila kan deles med andre python-brukere, 
og de kan installere pakken med pip: 

```shell
pip install ./lexupdater-0.0.1-py3.7.egg
```
