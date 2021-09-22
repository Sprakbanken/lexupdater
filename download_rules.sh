#!/usr/bin/env bash


GITHUB_TOKEN="${1:-$GITHUB_TOKEN}"

function download_file {
  FILE=$1
  GIT_RESPONSE="tmp.txt"

  curl \
      -H "Authorization: token ${GITHUB_TOKEN}" \
      -o $GIT_RESPONSE \
      -L "https://api.github.com/repos/Ingerid/rulebook/contents/${FILE}"

  URL=$( grep -E 'download_url": ' $GIT_RESPONSE |  sed -E s'/.*"download_url": "(.*)",.*/\1/' )

  echo "download_url of the git blob: "
  echo ${URL}

  wget -O  ${FILE} "${URL}"

  rm -f $GIT_RESPONSE
}

for FILE in 'rules.py' 'exemptions.py'; do download_file $FILE; done
