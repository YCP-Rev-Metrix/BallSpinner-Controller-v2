# BallSpinner Controller v2 - Desktop setup guide
## Notes
The Code is setup to be Operating System independent. So libraries like Metawear using bluetooth and our motor functionality, ensures that we are on the Raspberry Pi to run. This allows us to develop on any platform and still be able to run the project 

## Windows - WSL
It is recommended to use WSL as that is what our team used. 

### Running the project
Clone the repo
```bash
git clone https://github.com/YCP-Rev-Metrix/BallSpinner-Controller-v2/
```

**Build the virtual environment**
```bash
cd BallSpinner-Controller-v2
python3 -m venv venv
source venv/bin/activate
```

### Developing the frontend
See the UI guide in [BSC_Ui_README.md](BSC_Ui_README.md) for Qt Designer setup and the page workflow.

## Mac
Install Python and create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

For UI work, see [BSC_Ui_README.md](BSC_Ui_README.md).




# BallSpinner Controller v2 - Raspberry Pi Setup Guide

This guide will walk you through setting up a Raspberry Pi to run the BallSpinner-Controller-v2 application.

## Prerequisites

- Raspberry Pi with Raspbian Trixie OS flashed
- Access to YCP network credentials
- Working computer for SSH access

## Table of Contents

1. [Quick Install (Recommended)](#quick-install-recommended)
2. [Initial Setup](#initial-setup)
3. [Network Configuration](#network-configuration)
4. [SSH Configuration](#ssh-configuration)
5. [GitHub SSH Key Setup](#github-ssh-key-setup)
6. [System Updates](#system-updates)
7. [Python Installation](#python-installation)
8. [Repository Setup](#repository-setup)
9. [Motor Driver Requirements](#motor-driver-requirements)
10. [GPIO Defaults](#gpio-defaults)
11. [MetaWear SDK Installation](#metawear-sdk-installation)
12. [Testing](#testing)

---

## Quick Install (Recommended)

If you already cloned the repo on the Pi, run the single interactive installer. It installs system dependencies, creates the virtual environment, builds MetaWear/PyWarble, runs unit tests, and then starts the app via `startup.sh`. It can optionally configure autostart and logs to `logs/pi_install.log`.

```bash
cd BallSpinner-Controller-v2
chmod +x pi_install.sh
./pi_install.sh
```

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

## GitHub SSH Key Setup

1. Generate a GitHub SSH key on your Raspberry Pi
```bash
ssh-keygen -o -t rsa -C "githubusername@github.com"
```
3. Add the key to your GitHub SSH settings
4. Use the `cat` command to display your public key:
 ```bash
 cat ~/.ssh/id_rsa.pub
 ```
5. Copy all contents and add them to your GitHub account's SSH settings

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

## Repository Setup

### Clone the Repository

```bash
git clone git@github.com:YCP-Rev-Metrix/BallSpinner-Controller-v2.git
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

## Notes

- Make sure your virtual environment is activated (`source venv/bin/activate`) before running Python commands
- Keep track of your actual file paths and update the environment variables accordingly
- If you encounter issues, refer to the troubleshooting sections for Bluetooth and library path configuration

