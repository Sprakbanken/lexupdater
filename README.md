# Lexupdater

Lexupdater er et utviklingsverktøy for å oppdatere og utvide
[NST-leksikonet](https://www.nb.no/sprakbanken/ressurskatalog/oai-nb-no-sbr-23/)
med dialektvariasjon i transkripsjonene og nyord.
Dialektvariasjonen kommer fra strengtransformasjoner
(søk-erstatt-regler) som er utviklet av lingvister i Språkbanken. Nyordene kommer fra Norsk Aviskorpus og Målfrid, og er filtrert på frekvente forekomster over flere år, etter år 2000.

## 1. Installer lexupdater

Sørg for at du har versjon `3.8` eller høyere av `python`, og sett gjerne opp et virtuelt kodemiljø med pyenv, conda eller lignende.

Installer lexupdater:

```shell
pip install -e .
```

## 2. Last ned data

### Leksikondatabase

NST uttaleleksikon er lastet inn i en SQLite databasefil (`nst_lexicon_bm.db`) med en ordtabell (`words`) og en uttaletabell (`base`).

- Last ned filen ved å klikke på lenken:
    <https://www.nb.no/sbfil/uttaleleksikon/nst_lexicon_bm.db>

- Evt. kan du også laste ned filen fra kommandolinjen:

    ```shell
    wget https://www.nb.no/sbfil/uttaleleksikon/nst_lexicon_bm.db
    ```

### Regelfiler

Du kan hente de mest oppdaterte regelfilene fra [`rulebook`](https://github.com/Sprakbanken/rulebook) via git:

1. Legg til rulebook som en remote URL i dette repoet (obs! Dette gjøres bare én gang):

    ```shell
    git remote add rules git@github.com:Sprakbanken/rulebook.git
    ```

2. Hent filene:

    ```shell
    git fetch rules
    git checkout rules/develop rules.py exemptions.py
    ```

## 3. Konfigurér oppdateringen av leksikonet

``` shell
lexupdater -h

Usage: lexupdater [OPTIONS] COMMAND [ARGS]...

  Apply the dialect update rules on the base lexicon.

  Default file paths to the lexicon database, the replacement rules, and their
  exemptions, as well as the output directory, are specified in the config.py
  file.

  If provided, CLI arguments override the default values from the config.

  Note that all modifications in the backend db target temp tables, so the db
  isn't modified. The modifications to the lexicon are written to new, temp-
  table-specific files.

Options:
  -db, --database FILE      The path to the lexicon database.
  -d, --dialects TEXT       Apply replacement rules on one or more specified
                            dialects. Args must be separated by a simple comma
                            (,) and no white-space.
  -n, --newwords-path PATH  Path to folder with csv files or to a single file
                            with new words to add to the lexicon.
  -v, --verbose             Print logging messages to the console in addition
                            to the log file. -v is informative, -vv is
                            detailed (for debugging).
  -h, --help                Show this message and exit.

Commands:
  convert-old       (Deprecated) Convert lexicon formats to comply with MFA.
  insert            (Deprecated) Insert new word entries to the lexicon.
  match             (Deprecated) Fetch database entries that match the
                    replacement rules.
  newwords          Write the new word entries from the lexicon db to disk.
  original-lexicon  Write the original lexicon database entries to file.
  track-changes     (Deprecated) Extract transcriptions before and after
                    updates by...
  update            Update dialect transcriptions with rules.
  update-old        (Deprecated) Update dialect transcriptions with rules.
````

Parameterne `database`(filsti: str), `output_dir`(filsti: str), `newwords_path`(filsti), `dialects`(liste av str) pluss `update`-parameterne `rules_file`(filsti: str) og `exemptions_file`(filsti:str) kan konfigureres i en lokal `config.py`-fil.

## 4. Oppdatér leksikonet

Kjør `lexupdater update` med default-parametere:

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

## Utviklere: Bygg `lexupdater` som en python-pakke

Pakkekonfigurasjonen er i [`pyproject.toml`](./pyproject.toml).

```shell
python -m build .
```

Etter at python-pakken er bygget, vil den ligge i `dist`-mappen. Den kan nå
installeres med `pip`:

```shell
pip install dist/lexupdater-*.whl      # OS-uavhengig
```
