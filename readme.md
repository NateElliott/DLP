Starting in the home dir

	cd /home

Update system repositories

	sudo apt-get update

Install Git

    sudo apt-get install git

Install Python virtualenv

    sudo apt-get install python-virtualenv

Create Python3 virtualenv named "backbone"

    sudo virtualenv -p python3 backbone

Activate the "backbone" virtualenv

    source backbone/bin/activate

This will change the command prompt to:

    (backbone)user@pc:/home$
    
Install Django framework

    sudo pip install Django







