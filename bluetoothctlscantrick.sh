#!/usr/bin/expect -f 

set timeout 4 

spawn /usr/bin/bluetoothctl

sleep 0.5 

send "scan on\r"

sleep 3

# expect {
    # -re {^\[bluetoothctl\][#>]} {}
# }
send "scan off\r"
# 
# 
# # expect {
    # # -re {^\[bluetoothctl\][#>]} {}
# }
sleep 0.5
send "exit\r"



# expect {
    # -re {^\[bluetoothctl\][#>]} {}
# }