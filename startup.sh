#!/bin/bash 
echo "this is our startup script!"


echo "performing bluetooth magic commands so we can connect to the pi"

echo "ensure python has permission to use the bluetooth hardware"
sudo setcap cap_net_raw+eip $(eval readlink -f $(which python3))  

#echo "restart the bluetooth service"
#sudo systemctl restart bluetooth
#echo "waiting 3 seconds"
#sleep 3


cd /home/ballz/BallSpinner-Controller-v2/

echo "Current directory $(pwd)"

source venv/bin/activate

while true; do
    if python3 main.py; then
        echo "main.py finished successfully."
        break                 # exit the loop
    else
        echo "main.py failed (exit $?)."
        echo "Please Ensure the E-Stop is not pressed."
        echo "Press ENTER to retry or Ctrl‑C to quit."
        read -r              # wait for the user to hit Enter
    fi
done