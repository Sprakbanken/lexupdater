# Lexupdater

Lexupdater er et utviklingsverktøy for å oppdatere og utvide
[NST-leksikonet](https://www.nb.no/sprakbanken/ressurskatalog/oai-nb-no-sbr-23/)
med dialektvariasjon i transkripsjonene og nyord.
Dialektvariasjonen kommer fra strengtransformasjoner
(søk-erstatt-regler) som er utviklet av lingvister i Språkbanken. 
Nyordene kommer fra [Norsk Aviskorpus](https://www.nb.no/sprakbanken/ressurskatalog/oai-clarino-uib-no-avis-plain/) og [Målfrid](https://www.nb.no/sprakbanken/ressurskatalog/oai-nb-no-sbr-69/) etter år 2000, 
og er filtrert slik at bare frekvente forekomster over flere år er kommet med.


## 1. Installer lexupdater

Sørg for at du har versjon `3.8` eller høyere av [`python`](https://www.python.org/downloads/), og sett gjerne opp et virtuelt kodemiljø med pyenv, conda, venv eller lignende.

Installer lexupdater:

```shell
pip install git+https://github.com/Sprakbanken/lexupdater.git@v0.7.5
```

## 2. Last ned data

NST uttaleleksikon er tilgjengelig i en SQLite databasefil (`nst_lexicon_bm.db`) med en ordtabell (`words`), en uttaletabell (`prons`) og en uttaletabell (`base`).


### Linux 

```shell
./fetch_data.sh
```

### Andre OS (Windows, Mac)

- Last ned uttaledatabasefilen ved å klikke på lenken:
    <https://www.nb.no/sbfil/uttaleleksikon/nst_lexicon_bm.db>
- Bruk git i terminalen for å hente regelfilene fra [`nb_uttale`](https://github.com/Sprakbanken/nb_uttale):

```shell
git remote add nb_uttale git@github.com:Sprakbanken/nb_uttale.git
git fetch nb_uttale
git show nb_uttale/main:data/input/rules_v1.py > rules.py
git show nb_uttale/main:data/input/exemptions_v1.py > exemptions.py
git show nb_uttale/main:data/input/newwords_2022.csv > newwords.csv
git remote remove nb_uttale
```

## 3. Legg til nyord i uttaleleksikonet

Kjør `lexupdater newwords` fra kommandolinjen.

## 4. Generer dialektvariasjoner i uttaleleksikonet

Kjør `lexupdater update` fra kommandolinjen. 

Default-innstillingene gjør at dette tilsvarer følgende kommando: 

```shell
lexupdater -v \
    --database "nst_lexicon_bm.db" \
    --newwords-path "newwords.csv" \
    --dialects e_spoken \
        -d e_written \
        -d sw_spoken \
        -d sw_written \
        -d w_spoken \
        -d w_written \
        -d t_spoken \
        -d t_written \
        -d n_spoken \
        -d n_written \
    update \
        --rules-file "rules.py" \
        --exemptions-file "exemptions.py" \
        --output-dir "data/output"
```

### Konfigurer Lexupdater
Parameterne `database`, `output_dir`, `newwords_path`, `dialects` pluss `update`-parameterne `rules_file` og `exemptions_file` kan konfigureres i din lokale [`config.py`](./config.py)-fil.


Du kan også endre parameterne direkte fra kommandolinjen. Se tilgjengelige subkommandoer med hjelpeflagget: 

```shell
lexupdater -h
```

## Utviklere

### Bygg `lexupdater` som en python-pakke

Pakkekonfigurasjonen er i [`pyproject.toml`](./pyproject.toml).

```shell
python -m build .
```

Etter at python-pakken er bygget, vil den ligge i `dist`-mappen. Den kan nå
installeres med `pip`:

```shell
pip install dist/lexupdater-*.whl      # OS-uavhengig
```
