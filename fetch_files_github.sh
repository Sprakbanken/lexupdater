#!/usr/bin/env bash

GITHUB_TOKEN="${1:-$GITHUB_TOKEN}"


##### EITHER fetch with git itself ###############################

function add_remotes {
git remote add rules git@github.com:Sprakbanken/rulebook.git
git remote add conversion git@github.com:Sprakbanken/convert_nofabet.git
}

function fetch_conversion_module {
git fetch conversion
git checkout conversion/main conversion.py
mv conversion.py lexupdater/conversion.py
}

function fetch_rules_exemptions {
git fetch rules
git checkout rules/develop rules.py exemptions.py
}


############# OR use github API to download raw file #####################

function download_file {
  FILE=$1

  JSON_RESPONSE=$(curl \
    -H "Accept: application/vnd.github+json" \
    -H "Authorization: Bearer ${GITHUB_TOKEN}"\
    -H "X-GitHub-Api-Version: 2022-11-28" \
    https://api.github.com/repos/Sprakbanken/rulebook/contents/${FILE}?ref=develop )

  URL="$(echo $JSON_RESPONSE | jq -r '.download_url' )"


  wget -O ${FILE} ${URL}
}

################### RUN FUNCTIONS ###################
# Toggle comment to run/ignore

#add_remotes # This only needs to be run once per user. Comment out afterwards.
fetch_conversion_module
fetch_rules_exemptions

# for FILE in 'rules.py' 'exemptions.py'; do download_file $FILE; done
