import os
import sys

# creates the monit config file if it doesn't exist and registers script to be monitored
# argv[1]: path to monit config file
# argv[2]: absolute path of data collection directory
# argv[3]  data collection script to be added to monit config
# argv[4]  absolute path to python
if not os.path.isfile(sys.argv[1]):
    with open(sys.argv[1], "w+") as f:
        f.write("set daemon 600\n") # checks every 10 minutes whether the scripts are alive
        f.write("    with start delay 10\n") # starts checking a minute after start
        f.write("set log /var/log/monit.log\n") # set log file for monit
        f.write("set httpd port 2812 and\n") # sets port to access monit interface
        f.write("    use address localhost\n")
        f.write("    allow localhost\n")
        f.write("    allow admin:monit\n")
        f.write("check process rabbitmq matching rabbitmq\n") # checks whether rabbitmq is alive
        f.write("    start program = \"/bin/rabbitmq-server -detached\"\n") #command to start rabbitmq
        f.write("    stop program = \"/bin/rabbitmqctl stop\"\n") # command to stop rabbitmq
if not os.path.exists("runners/"):
    os.makedirs("runners") 
with open("runners/" + sys.argv[3] +".sh", "w+") as f:
    f.write("#!/bin/bash\n")
    # creates bash script to run data collection script and store its output in logs/[scriptname].log
    f.write("/bin/nohup " + sys.argv[4]+ " " + sys.argv[2]+sys.argv[3]+".py "
            + sys.argv[2] + " &>> " + sys.argv[2]+ "logs/" + sys.argv[3] + ".log &")
with open(sys.argv[1], "a") as f:
    # registers script to be monitored
    f.write("check process " + sys.argv[3] + " matching " + sys.argv[3]+".py\n")
    f.write("    start program = \"/bin/bash -c \'" + sys.argv[2] + "runners/" + sys.argv[3] + ".sh" + "\'\"\n")
    f.write("    stop program = \"/bin/pkill -15 -f \'" + sys.argv[3] + ".py\'\"\n")

