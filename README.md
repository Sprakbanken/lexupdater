# Lexicon updater 

Hovedprogramsnutten er lexupdater.py. 

Skriptet konfigureres i config.py, hvor man bl.a. spesifiserer navnet på dialektområdene, stien til backend-databasen, regelfiler og svartelister. 

Kjører man lexupdater uten argumenter, genereres leksikonfiler for alle dialektområdene. 

Om man kun vil generere leksikonfiler for noen dialektområder, 
bruker man argumentet -d og så liste opp hvilke dialekter man vil ha leksika for. 

Om man også vil skrive ut base-leksikonet (altså NST), bruker man -b.