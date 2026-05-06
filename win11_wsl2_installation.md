---
layout: default
title: Windows 11 WSL2 and Ubuntu Installation
---

This page contains a step-by-step guide through the installation of WSL2 on Windows 11.
<br><br>


## Install WSL2 and an Ubuntu 24.04 LTS Virtual Machine

---

This guide was developed using [Microsoft's official documentation here](https://docs.microsoft.com/en-us/windows/wsl/install-win10). It is recommended that you follow along with THIS guide as it includes some additional steps beyond what the Microsoft guide provides. These additional steps will ensure that you install all the packages required for your YCP CS courses.

* **Step 1:** Open the Windows **Command Prompt** as an Administrator by typing **cmd** into the search box in the Windows taskbar.  You should see the option to **Run as Administrator** on the right-hand side of the search results. Click on **Run as Administrator** to open the Windows **Command Prompt**.  When the **User Account Control** prompt asks "Do you want to allow this app to make changes to your device", click **Yes**.

* **Step 2:** To install WSL2 along with Ubuntu Linux 24.04 LTS run the following command in your newly opened **Command Prompt** window.
    > ```
    > wsl --install -d Ubuntu-24.04
    > ```
    * Do NOT close the terminal window while the installation is running.
    * Do NOT click anywhere in the terminal window as this will put the terminal window
    into a "text-selection mode".  While in "text-selection mode", the terminal will not
    update and will not appear to make any progress.  So, your installation may be complete,
    but you won't know.  If you accidentally clicked in the terminal window, you can exit
    "text-selection mode" by simple pressing your **Enter** key.

* **Step 3:** When the installer finishes, you should see a prompt in your terminal to "Create a default Unix user account". Here, you will need to create a username and password.  This doesn't have to be the same username and password that you use to log into Windows, but it can be if you wish. This account is specifically for the Linux virtual machine that you just created. **Create your Linux username and password to finalize the installation.**

* **Step 4:** After the WSL2 installation is complete, your Windows Command Prompt should change into a Linux terminal. If not, you can run a new instance of your newly installed Linux terminal by using the Windows search bar and searching for "Ubuntu".

* **Step 5:** Exit all instances of the **Linux terminal** and the Windows **Command Prompt** that you may be running.
<br><br>

---

### Congratulations, you’re now running Linux in Windows 11.

Copyright (c) 2011-202x, James Moscola

**Continue to:** [Install Build Tools in the WSL2 Linux Terminal](./win11_wsl2_build_tool_installation.html)

--- 
