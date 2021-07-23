#!/bin/bash
# Sends a kill signal to all scripts. Stops streaming new comments,
sudo monit stop comment_grabber
# gives time for other scripts to update info (24 hours when not testing)
sleep 1s

sudo monit stop comment_storer
sudo monit stop author_handler
sudo monit stop modqueue_monitor
sudo monit stop modlog_monitor

sleep 3s

sudo monit stop rabbitmq

sudo monit quit
