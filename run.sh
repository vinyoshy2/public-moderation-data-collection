#!/bin/bash

# starts data collection scripts through monit
# monit will restart data collection scripts on failure
MONIT="/etc/monitrc"

#Writing monit config file
echo "Creating monit file at" $MONIT 
[ -e monitrc ] && rm monitrc #remove any existing local monit file
python write_monit_config.py monitrc $PWD/ comment_grabber $(which python)
python write_monit_config.py monitrc $PWD/ comment_storer $(which python)
python write_monit_config.py monitrc $PWD/ author_handler $(which python)
python write_monit_config.py monitrc $PWD/ modlog_monitor $(which python)
python write_monit_config.py monitrc $PWD/ modqueue_monitor $(which python)

chmod +x runners/*.sh

#copy over monitrc
sudo cp monitrc /etc/monitrc 
#set permissions for monitrc
sudo chmod 700 /etc/monitrc
#start monitoring
echo "Starting data collection..."
sudo monit
echo "Starting rabbitmq..."
sudo monit start rabbitmq
echo "Starting python scripts..."
sleep 10s
sudo monit start all
echo "Starting monitoring..."
sleep 10s
sudo monit monitor all
echo "Validating.."
sleep 10s
sudo monit validate
