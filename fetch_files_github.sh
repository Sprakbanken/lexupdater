#!/usr/bin/env bash

#GITHUB_TOKEN="${1:-$GITHUB_TOKEN}"

##### Define functions to fetch files with git ###############################

function fetch_conversion_module {
  git remote add conversion git@github.com:Sprakbanken/convert_nofabet.git
  git fetch conversion
  git show conversion/main:conversion.py > lexupdater/conversion.py
  git remote remove conversion
}

function fetch_rules_exemptions {
  git remote add nb_uttale git@github.com:Sprakbanken/nb_uttale.git
  git fetch nb_uttale
  git show nb_uttale/main:data/input/rules_v1.py > rules.py
  git show nb_uttale/main:data/input/exemptions_v1.py > exemptions.py
  git show nb_uttale/main:data/input/newwords_2022.csv > newwords.csv
  git remote remove nb_uttale
}

################### RUN FUNCTIONS ###################

#fetch_conversion_module
fetch_rules_exemptions
