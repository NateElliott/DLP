#!/bin/bash
cd /home

WT='\033[1;37m'
GR='\033[0;32m'
NC='\033[0m'

REPO='https://github.com/NateElliott/DLP.git'
BRAN='dev'


if [ "$1" = "remove" ]
then 

printf "\n${WT}Removing DLP${NC}\n"

printf "... ${GR}Removing backbone${NC}\n"
sudo rm -rf backbone/ 

printf "... ${GR}Removing DLP(core)${NC}\n"
sudo rm -rf DLP/

printf "... ${GR}Cleaning up${NC}\n"
sudo rm runserver.sh

printf "\n${WT}Removal complete${NC}\n\n"

else

printf "\n${WT}Installing DLP${NC}\n"
read -p "$(echo -e "Enter branch (default=$GR$BRAN$NC)"):" BRAN



printf "... ${GR}Preparing to install${NC}\n"
sudo apt-get -qq update

printf "... ${GR}Installing Git${NC}\n"
sudo apt-get -qq install git

printf "... ${GR}Installing virtualenv${NC}\n"
sudo apt-get -qq install python-virtualenv

printf "... ${GR}Preparing virtualenv${NC}\n"
sudo virtualenv -q -p python3 backbone

printf "... ${GR}Installing Django${NC}\n"
sudo backbone/bin/pip -q install Django

printf "... ${GR}Cloning branch($BRAN)${NC}\n"
sudo git clone -b $BRAN -q $REPO


sudo touch runserver.sh
cat <<EOT >> runserver.sh
#!/bin/bash
sudo backbone/bin/python DLP/playground/manage.py runserver
EOT

sudo chmod 777 runserver.sh
printf "${WT}Install complete!${NC}\n\n"

printf "Use: ${GR}sudo ./runserver.sh${NC} to start local dev server\n\n"

fi
