# Autostart the Ball Spinner Application - Setup Guide
## Don't use this if you want to debug, you wont see your console log. 

First, note the path to the file startup.sh
```bash
BallSpinner-Controller-v2/startup.sh
```
This file is responsible for launching our application.

## Configure autostart for startup.sh

We must wait for the Raspberry Pi to load the desktop environment.

navigate to the /home/hostname/.config directory, create or open the autostart folder. 
```bash
cd ${HOME}/.config/
mkdir autostart
cd autostart
```
create a new .desktop file and fill in with the following format.
```bash
[Desktop Entry]
Type=Application
Name=RevMetrixStartupScript
Exec=lxterminal --command="[!---YOURPATHTO---!]/BallSpinner-Controller-v2/startup.sh"
Terminal=true
```

### Hooray!
You should now have a functioning startup script :)
