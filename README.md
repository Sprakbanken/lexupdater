# Lexupdater

Lexupdater is a tool to extend and update the 
[NST pronunciation lexicon](https://www.nb.no/sprakbanken/en/resource-catalogue/oai-nb-no-sbr-23/) with new words and dialect variation in the pronunciation transcriptions. 

The dialectal variation is updated through string transformation rules (search-and-replace with rege patterns) developed by trained linguists in the Language Bank at the National Library of Norway.

Since NST was first published before 2000, new words occurring after 2000 have been added from the corpora [Norwegian Newspaper Corpus Bokmål](https://www.nb.no/sprakbanken/en/resource-catalogue/oai-clarino-uib-no-avis-plain/) and [Målfrid 2021 – Freely Available Documents from Norwegian State Institutions](https://www.nb.no/sprakbanken/en/resource-catalogue/oai-nb-no-sbr-69/).


## Usage 

### 1. Install lexupdater

Enure you have [`python`](https://www.python.org/downloads/) version `3.8` or higher. 

Create a virtual environment and activate it, e.g. 
```shell 
python -m venv .venv
source .venv/bin/activate
```

Install lexupdater:

```shell
pip install git+https://github.com/Sprakbanken/lexupdater.git@v0.7.6
```

## 2. Download data

The NST pronunciation lexion is availalbe in an SQLite database [`nst_lexicon_bm.db`](https://www.nb.no/sbfil/uttaleleksikon/nst_lexicon_bm.db). It has a table with `words`, and with pronunciations (`base`). 

Lexupdater uses external python files with dicts of regex patterns to update the database, and a csv-file to add new words. These files are available from the 
[`nb_uttale`-repo](https://github.com/Sprakbanken/nb_uttale). 


### Linux 

```shell
./fetch_data.sh
```

### Other OS (Windows, Mac)

- Download the pronunciation database by clicking this link: <https://www.nb.no/sbfil/uttaleleksikon/nst_lexicon_bm.db>
- Use git commands to fetch the rules and newwords from [`nb_uttale`](https://github.com/Sprakbanken/nb_uttale):

```shell
git remote add nb_uttale git@github.com:Sprakbanken/nb_uttale.git
git fetch nb_uttale
git show nb_uttale/main:data/input/rules_v1.py > rules.py
git show nb_uttale/main:data/input/exemptions_v1.py > exemptions.py
git show nb_uttale/main:data/input/newwords_2022.csv > newwords.csv
git remote remove nb_uttale
```

## 3. Add new words to the lexicon

Run `lexupdater newwords` from your command line.

## 4. Generate dialect variations 

Run `lexupdater update` from the command line. 

The `update` command and the default settings correspond to the following: 

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

### Configure Lexupdater

The parameters `database`, `output_dir`, `newwords_path`, `dialects` and the `update`-parameters `rules_file` and `exemptions_file` can be changed in your local [`config.py`](./config.py).

You can also set the parameters directly from the command line. See the `help` flag for more info: 

```shell
lexupdater -h
```

## Developers

### Build the `lexupdater` python package yourself

We use [`pyproject.toml`](./pyproject.toml) to configure the package. 

```shell
python -m build .
```

The python distribution wheel is located in the `dist`-folder. 
It can be intsalled with `pip`:

```shell
pip install dist/lexupdater-*.whl      # OS-independent
```
