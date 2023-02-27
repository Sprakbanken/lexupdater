
# These only need to be run once per user. Comment out afterwards.
#git remote add rules git@github.com:Sprakbanken/rulebook.git
#git remote add conversion git@github.com:Sprakbanken/convert_nofabet.git


git fetch conversion
git checkout conversion/main conversion.py
mv conversion.py lexupdater/conversion.py


git fetch rules
git checkout rules/develop rules.py exemptions.py

