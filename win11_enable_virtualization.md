---
layout: default
title: Windows PC Virtualization Settings
---

This page contains a step-by-step guide to enable virtualization on a Windows-based PC.
<br><br>


## Enable Virtualization in your PC BIOS/UEFI

---

Before you can install and run virtual machines on your computer, you must enable a feature in your computer's BIOS/UEFI.  Many computers are shipped from the manufacturer with this feature disabled.
<br><br>

### Section 1: Access your computer's BIOS/UEFI

---

There are multiple ways to get into your computer's BIOS/UEFI.  Select the method that you prefer below:

#### <u>Method #1: Enter BIOS/UEFI during boot process</u>

* **Step 1:** Reboot your computer (read **Step 2** before executing **Step 1**).

* **Step 2:** As your computer is booting and coming up from the black screen you may see a manufacturer's logo and/or some text describing the memory capacity and other specifications of your computer.  During this phase of the boot process, rapidly continue to press **Delete**, **Esc**, **F1**, **F2**, or **F4** to enter the **Setup Menu** (i.e. BIOS/UEFI). Each computer manufacturer uses a different key but your computer may show a brief message at boot indicating which key you need to press. You'll only have one or two seconds to find and press the right key so be ready!  If you see the Windows boot logo, you've already missed it.  You can reboot and try again or move on to Method #2/3.

 * **Step 3:** Once in your BIOS/UEFI, continue following the instructions in Section 2.


#### <u>Method #2: Enter BIOS/UEFI from Windows 11 Settings panel</u>

* **Step 1:** Find and click on the Windows logo in your taskbar then select Settings to open up the Settings app.

* **Step 2:** In Settings, click on "Windows Update" in the left sidebar.

* **Step 3:** In the "Windows Update" settings, select "Advanced options".

* **Step 4:** In "Advanced options", select "Recovery" under "Additional options".

* **Step 5:** In the "Recovery" menu, click on "Restart now" in the under "Advanced startup" section. This will allow you to reboot your computer for restoration and some configurations. You may see a prompt stating, "We’ll Restart Your Device So Save Your Work". In this prompt, click "Restart Now" to restart your computer.

* **Step 6:** When your computer reboots, you'll see a blue background menu containing options like "Continue", "Troubleshoot", and "Turn off your PC". Click on "Troubleshoot".

* **Step 7:** Click on "Advanced options".

* **Step 8:** Select "UEFI Firmware Settings" and then "Restart" to enter your computer BIOS/UEFI.

* **Step 9:** Once in your BIOS/UEFI, continue following the instructions in Section 2.

<br><br>

### Section 2: Find and enable virtualization settings

---

* **Step 1:** In the BIOS/UEFI settings, find the configuration settings related to the **CPU**. These can be found under the headings **Processor**, **Chipset**, or **Northbridge**.

* **Step 2:** Enable virtualization.  The setting may be called **VT-x**, **AMD-V**, **SVM**, or **Vanderpool**.  Enable **Intel VT-d** or **AMD IOMMU** if the options are available.

* **Step 3:** Save your changes and reboot. 
<br><br>

---

Copyright (c) 2011-202x, James Moscola

**Continue to:** [Install WSL2 with Ubuntu Linux](./win11_wsl2_installation.html)

--- 
