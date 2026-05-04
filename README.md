# BallSpinner Controller v2 - Desktop development guide
## Notes
The codebase is operating-system independent for development. Hardware-bound pieces (MetaWear over Bluetooth, motor drivers) are meant to run on the Raspberry Pi, so you can develop on any platform and run the full stack on the Pi.

## Windows - WSL
It is recommended to use WSL; that is what our team used.

A guide to installing the WSL version can be found at https://ycpcs.github.io/dev-env-setup-guide/ under the Windows 11: WSL2 guide (Personal Computer) section.

Only up to step 3 of that guide is required. You can use whatever IDE you like: VS Code was used for our development, but IDEs such as Cursor and PyCharm work fine.

For day-to-day development, stay in WSL. Packaging with PyInstaller on Windows is documented below under [Build on Windows (Native)](#build-on-windows-native). Building under WSL will result in a Linux application rather than Windows.

### Running the project
Clone the repo:

```bash
git clone https://github.com/YCP-Rev-Metrix/BallSpinner-Controller-v2/
```

**Python version**

This project targets **Python 3.13** (same as the native Windows build scripts). In WSL, check your version:

```bash
python3 --version
```

If you need 3.13 on Ubuntu/WSL, use your distro's packages or [deadsnakes](https://launchpad.net/~deadsnakes/+archive/ubuntu/ppa) (`python3.13`, `python3.13-venv`) before creating the venv.

**Virtual environment and dependencies**

```bash
cd BallSpinner-Controller-v2
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**Run the app**

```bash
python main.py
```

### Setting up VS Code with WSL

1. **Install VS Code on Windows** (if not already installed)
   - Download from https://code.visualstudio.com/

2. **Install the Remote - WSL extension in VS Code**
   - Open VS Code
   - Go to Extensions (Ctrl+Shift+X)
   - Search for "Remote - WSL" (by Microsoft)
   - Click Install

3. **Open the project in WSL from VS Code**
   
   Option A: From the command line in WSL:
   ```bash
   cd /mnt/c/Users/YourUsername/Documents/GitHub/BallSpinner-Controller-v2
   code .
   ```
   
   Option B: From VS Code directly:
   - Click the green "WSL" indicator at the bottom-left corner
   - Select "Connect to WSL"
   - Use File → Open Folder and navigate to `/mnt/c/Users/YourUsername/Documents/GitHub/BallSpinner-Controller-v2`

4. **Run the project from VS Code**
   - Open the integrated terminal (Ctrl+`)
   - Your terminal will automatically be inside WSL
   - Activate the virtual environment: `source venv/bin/activate`
   - Run the app: `python main.py`

5. **Run and debug from VS Code**
   - Install Python extension in VS Code (while connected to WSL)
   - Set breakpoints by clicking line numbers
   - Press F5 or go to Run → Start Debugging
   - Select "Python" as the debug environment

### Developing the frontend
See the UI guide in [BSC_Ui_README.md](BSC_Ui_README.md) for how to set up Qt Designer and the page workflow.

## Mac
Install Python (3.13.7 recommended), create a virtual environment, and install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Run the app**

```bash
python main.py
```

For UI work, see [BSC_Ui_README.md](BSC_Ui_README.md).

## Build the Desktop App

### Build on Windows (Native)
Preferred option (no manual venv activation required):

```powershell
powershell -ExecutionPolicy Bypass -File .\build_windows.ps1
```

Manual option:

```powershell
py -3.13 -m venv venv
venv\Scripts\python.exe -m pip install --upgrade pip
venv\Scripts\python.exe -m pip install -r requirements.txt pyinstaller
venv\Scripts\python.exe -m PyInstaller --clean -y main.spec
```

### Build on macOS
After installing dependencies in the virtual environment, build with PyInstaller:

```bash
source venv/bin/activate
pip install pyinstaller
python -m PyInstaller --clean -y main.spec
```

Build output is created in `dist/`, typically:
- `dist/BallSpinnerController/`
- `dist/BallSpinnerController.app`

If PyInstaller warns about macOS codesigning, the bundle is still generated but may need manual signing for distribution.

# BallSpinner Controller v2 - Raspberry Pi Setup Guide

This guide will walk you through setting up a Raspberry Pi to run the BallSpinner-Controller-v2 application.

## Prerequisites

- Raspberry Pi with Raspbian Trixie OS flashed
- Access to YCP network credentials
- Working computer for SSH access

## Table of Contents

1. [Initial Setup](#initial-setup)
2. [Network Configuration](#network-configuration)
3. [SSH Configuration](#ssh-configuration)
4. [VNC Configuration](#vnc-configuration)
5. [GitHub SSH Key Setup](#github-ssh-key-setup)
6. [Repository Setup](#repository-setup)
   - [Quick Install (Recommended)](#quick-install-recommended)
7. [System Updates](#system-updates)
8. [Python Installation](#python-installation)
9. [Motor Driver Requirements](#motor-driver-requirements)
10. [GPIO Defaults](#gpio-defaults)
11. [MetaWear SDK Installation](#metawear-sdk-installation)
12. [Testing](#testing)

---

## Initial Setup

### Flash Raspbian Trixie

Flash Raspbian Trixie to your Raspberry Pi OS -- 64 Bit OS!!

## Network Configuration

### Connect to eduroam or York Connect

**Option 1: York Connect**
- Register the Pi's MAC address at: https://clearpass.ycp.edu/guest/guest_index.php

**Option 2: eduroam**
1. Select eduroam from the network dropdown
2. Choose "No CA certificate is required"
3. Use your YCP credentials to connect

## SSH Configuration

Enable SSH connection on your Raspberry Pi:

```bash
sudo raspi-config
```

Navigate to:
- **Interface settings** → **SSH** → **Enable SSH**

### Finding Your Pi's IP Address

On the Raspberry Pi, run:
```bash
hostname -I
```

### Connecting via SSH

From your personal computer:
```bash
ssh RPIname@IPAddress
```

Replace `RPIname` with your Pi's hostname and `IPAddress` with the IP address from the previous step.

## VNC Configuration

If you run `pi_install.sh`, VNC should already be enabled (the installer prompts to enable it, default is `Y`).

If needed, you can enable it manually:

```bash
sudo raspi-config nonint do_vnc 0
sudo systemctl enable vncserver-x11-serviced.service
sudo systemctl restart vncserver-x11-serviced.service
```

## GitHub SSH Key Setup

1. **Generate a new SSH key on the Pi** (run this in a terminal on the Raspberry Pi). Use your **GitHub email** in the `-C` field so the key is labeled; it does not log you in by itself.

```bash
ssh-keygen -o -t rsa -b 4096 -C "you@example.com"
```

`ssh-keygen` will ask a few questions:

- **File to save the key** — press **Enter** to accept the default (`/home/<you>/.ssh/id_rsa`). That is what the steps below expect.
- **Passphrase** — you can press **Enter** twice for no passphrase (simpler on a headless Pi) or set one (more secure; you will need to enter it when using the key).

Only the **public** key (the `.pub` file) ever leaves the Pi. Never copy or share the private key file (`id_rsa` without `.pub`).

2. **Show the public key** and copy it to the clipboard, or copy from the terminal after running:

```bash
cat ~/.ssh/id_rsa.pub
```

The line should start with `ssh-rsa` and end with the same comment you passed to `-C`. Copy the **entire** single line.

3. **Add the key in GitHub** (in a browser, on your computer is fine):

- Open [GitHub → Settings → SSH and GPG keys](https://github.com/settings/keys)
- **New SSH key**
- **Title** — e.g. `Raspberry Pi` (any name you will recognize)
- **Key** — paste the line you copied
- **Add SSH key**

4. **Test the connection** from the Pi (optional but recommended):

```bash
ssh -T git@github.com
```

The first time, type `yes` if asked to trust the host. You should see a message that GitHub does not provide shell access, which means authentication worked.

## Repository Setup

### Clone the Repository

```bash
git clone git@github.com:YCP-Rev-Metrix/BallSpinner-Controller-v2.git
```

### Quick Install (Recommended)

After cloning the repo on the Pi, run the single interactive installer. It installs system dependencies, can enable VNC for remote desktop access, creates the virtual environment, builds MetaWear/PyWarble, runs unit tests, and then starts the app via `startup.sh`. It can optionally configure autostart and logs to `logs/pi_install.log`.

```bash
cd BallSpinner-Controller-v2
chmod +x pi_install.sh
./pi_install.sh
```

## System Updates

Update your system packages:

```bash
sudo apt update
sudo apt upgrade
```

## Python Installation 

Upgrade to Python 3.13:

First check your version, if you are already running 3.13 then you are all good.

```bash
python3 --version
```

else install python3.13
```bash
sudo apt install software-properties-common
sudo apt install --reinstall python3-launchpadlib
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.13 python3.13-venv
```

### Create Virtual Environment

```bash
cd BallSpinner-Controller-v2
python3 -m venv venv
source venv/bin/activate
```

### Install Python Dependencies

Inside the cloned directory and virtual environment:

```bash
pip install -r requirements-pi.txt
```

## Motor Driver Requirements

Install requirements for motor drivers:

```bash
sudo apt-get install liblgpio-dev
sudo apt install swig
pip install rpi-lgpio
```

## GPIO Defaults

Set BCM pins 5 and 6 to output low at boot by editing `/boot/firmware/config.txt`:

```bash
sudo cp /boot/firmware/config.txt /boot/firmware/config.txt.bak
sudo nano /boot/firmware/config.txt
```

Add this block at the end of the file:

```ini
# >>> BallSpinner GPIO defaults >>>
gpio=5,6=op,dl
# <<< BallSpinner GPIO defaults <<<
```

Reboot the Pi to apply the boot-time defaults.

If you use `pi_install.sh`, it can add this block automatically.

## MetaWear SDK Installation

The MetaWear SDK allows connection to MetaMotionS devices via Bluetooth.

### Step 1: Install Bluetooth Dependencies

```bash
sudo apt-get install bluetooth bluez libbluetooth-dev libudev-dev libboost-all-dev build-essential
```

### Step 2: Enter Virtual Environment

```bash
source venv/bin/activate
```

### Step 3: Clone MetaWear SDK and PyWarble

```bash
git clone --recurse-submodules git@github.com:mbientlab/MetaWear-SDK-Python.git
cd MetaWear-SDK-Python
git clone --recurse-submodules https://github.com/mbientlab/PyWarble.git
cd PyWarble/clibs/warble/deps/libblepp
```

### Step 4: Compile libblepp

```bash
cd PyWarble/clibs/warble/deps/libblepp
./configure
make
```

**Expected output:**
```
-------------- Test Results ---------------
test_scan: OK
-------------------------------------------
```

### Step 5: Test Bluetooth Examples for libblepp

Set environment variables (replace `[YOUR PATH TO]` with your actual path):

```bash
export BLEPP_LIB="[YOUR PATH TO]/PyWarble/clibs/warble/deps/libblepp"
export LD_LIBRARY_PATH="$BLEPP_LIB:$LD_LIBRARY_PATH"
```

**Example:**
```bash
export BLEPP_LIB="/home/ballz/MetaWear-SDK-Python/PyWarble/clibs/warble/deps/libblepp"
export LD_LIBRARY_PATH="$BLEPP_LIB:$LD_LIBRARY_PATH"
```

Test the library (in the libblepp directory):
```bash
sudo LD_LIBRARY_PATH="/home/ballz/MetaWear-SDK-Python/PyWarble/clibs/warble/deps/libblepp" ./lescan
```

#### Troubleshooting Bluetooth

If you encounter Bluetooth issues, try these commands:

```bash
sudo systemctl status bluetooth
sudo systemctl start bluetooth
rfkill list
sudo rfkill unblock bluetooth
hciconfig
sudo hciconfig hci0 up
```

### Step 6: Compile Warble

```bash
cd PyWarble/clibs/warble
nano Makefile
```

Edit the `ARCH=` line in the Makefile, then:
Change it to `ARCH=-march=armv8-a`
```bash
make
```

### Step 7: Update Library Path

Set environment variables (replace `[YOUR PATH TO]` with your actual path):

```bash
export BLEPP_LIB="[YOUR PATH TO]/PyWarble/clibs/warble/deps/libblepp"
export WARBLE_BUILD="[YOUR PATH TO]/PyWarble/clibs/warble/dist/release/lib/arm"
export LD_LIBRARY_PATH="$BLEPP_LIB:$WARBLE_BUILD:$LD_LIBRARY_PATH"
```

### Step 8: Install PyWarble

From the PyWarble directory:

```bash
cd ~/MetaWear-SDK-Python/PyWarble
pip install .
```

### Step 9: Give Python Bluetooth Permissions

**⚠️ IMPORTANT: You must run this command:**

```bash
sudo setcap cap_net_raw+eip $(eval readlink -f $(which python3))
```

### Step 10: Test PyWarble

1. Find the MAC address for your MetaMotion device
2. Test the connect.py script:
   ```bash
   python3 connect.py "MacAddress of device"
   ```

If it fails, restart Bluetooth and initiate a scan:

```bash
sudo systemctl restart bluetooth
bluetoothctl
scan on
scan off
```

### Step 11: Compile MetaWear-SDK-CPP

#### Step 11a: Edit json.hpp

```bash
sudo nano src/metawear/dfu/cpp/json.hpp
```

Add this include at the top:
```cpp
#include <cstdint>
```

#### Step 11b: Compile MetaWear-SDK-CPP

In the MetaWear-SDK-CPP directory:

```bash
cd ~/MetaWear-SDK-Python/MetaWear-SDK-Cpp
make CXX=g++ CXXFLAGS="-Wall -fPIC -std=c++14 -I$(pwd)/src" -j$(nproc)
```

A successful build will show these lines at the end:
```bash
ln -sf libmetawear.so.0.20.7 dist/release/lib/arm/libmetawear.so.0
ln -sf libmetawear.so.0 dist/release/lib/arm/libmetawear.so
```

### Step 12: Set Library Paths and Compiler Flags

Set all library locations and add them to your environment (replace `[YOUR PATH TO]` with your actual paths):

```bash
export METAWEAR_HEADERS="[YOUR PATH TO]/MetaWear-SDK-Python/MetaWear-SDK-Cpp/src/metawear"
export METAWEAR_LIB="[YOUR PATH TO]/MetaWear-SDK-Python/MetaWear-SDK-Cpp/dist/release/lib/arm"
export BLEPP_LIB="[YOUR PATH TO]/PyWarble/clibs/warble/deps/libblepp"
export BLEPP_HEADERS="[YOUR PATH TO]/PyWarble/clibs/warble/deps/libblepp/blepp"
export WARBLE_BUILD="[YOUR PATH TO]/PyWarble/build/lib/mbientlab/warble"

export LD_LIBRARY_PATH="$METAWEAR_LIB:$BLEPP_LIB:$WARBLE_BUILD:$LD_LIBRARY_PATH"
export CFLAGS="-I$METAWEAR_HEADERS -I$BLEPP_HEADERS"
export LDFLAGS="-L$METAWEAR_LIB -L$BLEPP_LIB -L$WARBLE_BUILD"
```

**Example with actual paths:**
```bash
export METAWEAR_HEADERS="/home/ballz/MetaWear-SDK-Python/MetaWear-SDK-Cpp/src/metawear"
export METAWEAR_LIB="/home/ballz/MetaWear-SDK-Python/MetaWear-SDK-Cpp/dist/release/lib/arm"
export BLEPP_LIB="/home/ballz/MetaWear-SDK-Python/PyWarble/clibs/warble/deps/libblepp"
export BLEPP_HEADERS="/home/ballz/MetaWear-SDK-Python/PyWarble/clibs/warble/deps/libblepp/blepp"
export WARBLE_BUILD="/home/ballz/MetaWear-SDK-Python/PyWarble/build/lib/mbientlab/warble"

export LD_LIBRARY_PATH="$METAWEAR_LIB:$BLEPP_LIB:$WARBLE_BUILD:$LD_LIBRARY_PATH"
export CFLAGS="-I$METAWEAR_HEADERS -I$BLEPP_HEADERS"
export LDFLAGS="-L$METAWEAR_LIB -L$BLEPP_LIB -L$WARBLE_BUILD"
```

**Note:** To make these environment variables persistent across sessions, add them to your `~/.bashrc` or `~/.profile` file.

### Step 13: Install MetaWear-SDK-Python

```bash
cd ~/MetaWear-SDK-Python
pip install .
```

## Testing

### Step 14: Test the Application

Run the main application:

```bash
python main.py
```

Optional test runners:
```bash
./run_unit_tests.sh
./run_integration_tests.sh
```

**Expected Result:** The application should open and you should now be using the BallSpinner-Controller-v2.

---

## Basic VNC Connection (Mac to Raspberry Pi)

Use VNC when you want to control the Pi desktop remotely and interact with the app UI.

`pi_install.sh` should already enable VNC during setup (default prompt is `Y`).

1. In the app, open **Cloud Test**.
2. Read the IP shown in the top-right menu bar (`IP: ...`).
3. On your Mac, open Screen Sharing (Finder -> Go -> Connect to Server) and connect to:
   ```
   vnc://PI_IP_ADDRESS
   ```

4. Log in with your Pi username and password.

Manual fallback if VNC was previously disabled:
```bash
sudo raspi-config nonint do_vnc 0
sudo systemctl enable vncserver-x11-serviced.service
sudo systemctl restart vncserver-x11-serviced.service
```

If you are off-campus or off-LAN, use a VPN solution (for example Tailscale) and connect using the VPN IP.

---

## Notes

- Make sure your virtual environment is activated (`source venv/bin/activate`) before running Python commands
- Keep track of your actual file paths and update the environment variables accordingly
- If you encounter issues, refer to the troubleshooting sections for Bluetooth and library path configuration

