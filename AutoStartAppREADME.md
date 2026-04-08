# Autostart the Ball Spinner Application - Setup Guide
## Do not use this if you want to debug; you will not see console logs.

If you ran `pi_install.sh`, you can choose the autostart option at the end and skip this file.

First, note the path to `startup.sh`.
```bash
BallSpinner-Controller-v2/startup.sh
```
This file is responsible for launching the application.

## Configure autostart for startup.sh

We must wait for the Raspberry Pi to load the desktop environment.

navigate to the `/home/username/.config` directory, create or open the autostart folder.
```bash
cd ${HOME}/.config/
mkdir autostart
cd autostart
```
create a new `.desktop` file and fill in with the following format.
```bash
[Desktop Entry]
Type=Application
Name=RevMetrixStartupScript
Exec=lxterminal --command="/home/youruser/BallSpinner-Controller-v2/startup.sh"
Terminal=true
```

Replace `/home/youruser` with the actual path on your Pi.

### Hooray!
You should now have a functioning startup script :)
