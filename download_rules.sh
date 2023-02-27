#!/usr/bin/env bash


GITHUB_TOKEN="${1:-$GITHUB_TOKEN}"

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

for FILE in 'rules.py' 'exemptions.py'; do download_file $FILE; done
