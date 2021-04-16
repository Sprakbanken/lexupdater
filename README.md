# Lexupdater 

Lexupdater er et utviklingsverktøy for å oppdatere og utvide [NST-leksikonet](https://www.nb.no/sprakbanken/ressurskatalog/oai-nb-no-sbr-23/) med transkripsjoner for
4 dialekter og 30 000 nyord. Dialektutvidelsen skal lages ved hjelp av
strengtransformasjoner (søk-erstatt-regler), mens nyorda legges til som lister med ord og
transkripsjoner.

## Last ned data
Original-leksikonet er blitt lagret som en `sqlite`-database, 
og må lastes ned i forkant. Kontakt [Per Erik Solberg](https://github.com/peresolb) for å få tilgang til denne fila. 

Lagre databasen lokalt i data-mappen: `./data/input/backend-db02.db`

## Konfigurér oppdateringen

Hovedskriptet til `lexupdater` konfigureres i `config/config.py`, 
hvor man bl.a. spesifiserer følgende variabler: 

* `dialects`: navnet på dialektområdene
* `database`: stien til backend-databasen i filstrukturen
* `output_dir`: filmappen hvor output blir lagret
* `rules`: regelfiler 
* `blacklists`: svartelister


## Oppdatér leksikonet
Hovedprogramsnutten er i fila `lexupdater/__main__.py`, med følgende hjelpetekst: 

```commandline
$ python -m lexupdater -h   
usage: __main__.py [-h]
                   [--print_dialects [PRINT_DIALECTS [PRINT_DIALECTS ...]]]
                   [--print_base]

optional arguments:
  -h, --help            show this help message and exit
  --print_dialects [PRINT_DIALECTS [PRINT_DIALECTS ...]], -d [PRINT_DIALECTS [PRINT_DIALECTS ...]]
                        Generate lexicon files for one or more specified
                        dialects.
  --print_base, -b      Generate a base lexicon file, containing the state of
                        the lexicon prior to updates.

```

* Kjører man `lexupdater` uten argumenter, genereres leksikonfiler for alle dialektområdene. 
``` commandline
python -m lexupdater 
```

* Om man kun vil generere leksikonfiler for noen dialektområder, 
bruker man argumentet -d og så liste opp hvilke dialekter man vil ha leksika for. 
  (Dette eksempelet gir samme resultat som eksempelet over, hvor default-verdiene brukes.) 
```commandline
python -m lexupdater -d e_spoken, e_written, sw_spoken, sw_written, w_spoken, w_written, t_spoken, t_written, n_spoken, n_written
```

* Om man også vil skrive ut base-leksikonet (altså NST), bruker man -b.
```commandline
python -m lexupdater -b
```

## Installér `lexupdater` som en python-pakke 
Du kan lage en pip-installérbar python-pakke (komprimerte filer med `.tar.gz`, `.egg`, `.whl` suffiks) 
via `setup.py`-skriptet: 

```commandline
python setup.py install     # Installer direkte fra repoet 
```
Dette lagrer en `.egg`-fil i en ny mappe `dist`. 
Denne fila kan deles med andre python-brukere, 
og de kan installere pakken med pip: 

```commandline
pip install ./lexupdater-0.0.1-py3.7.egg
```
