
***
# Gran Turismo 7 UDP proxy for XSim and others....

## Introduction

This reposirtory contains a UDP Proxy for Gran Turismo 7 in order to provide motion to [XSim ](https://www.xsimulator.net/)
This proxy is required as Xsim plugin is not able to decrypt the telemetry packets as they are salsa encoded. Salsa decoding is easy to do in python, so this proxy "subscribes" to Gran Turismo by sending a hearbeat message, receives and decrypts the telemetry data and hten forwards it to the XSim plugin dedicated to Gran Turismo 7.

``
PlayStation 4/5 (port 33749) -> GT7Proxy (port 33740) -> XSim plugin (port 33800)
``

## Running the UDP proxy

To run the script via Python, you need to have at least the version 3.9 installed and a couple of dependencies
Clone this repository and install all dependencies:
``pip install -r requirements.txt``
You will need to install Visual C++ Build Tools using ``Visual Studio Installer`` from [here](https://visualstudio.microsoft.com/fr/downloads/).
Once the requirements are correctly installed, you may need to add the directory with pyinstaller.exe in the PATH

Then run the proxy with at least one argument representing the PlayStation/Whatever IP:

``python GT7Proxy.py --ps_ip 192.168.1.10``

Or

``python GT7Proxy.py --ps_ip mipsipaddress.local``

## Detailed usage

Detailed usage:

GT7Proxy.py [-h] --ps_ip PS_IP [--xsim_ip XSIM_IP] [--xsim_port XSIM_PORT] [--logpackets LOGPACKETS] [--csvoutput CSVOUTPUT] [--silent SILENT]

options:
`
-h, --help            show this help message and exit

--ps_ip PS_IP         Playstation 4/5 IP address. Accepts IP or FQDN provided it resolves to something.

--xsim_ip XSIM_IP     IP of the computer where XSim is running. Default is 127.0.0.1

--xsim_port XSIM_PORT  Port where the XSim plugin is expecting to receive telemetry. Default is 33800

--logpackets LOGPACKETS Optionnaly log packets for future playback using https://github.com/vthinsel/Python_UDP_Receiver/UDPSend_timed.py .Default is False

--csvoutput CSVOUTPUT Optionnaly output data to csv for analysis. Default is False

--silent SILENT limit console output to most usefull data for dashboard. Default is False

--xsimoutput XSIMOUTPUT Do not send outout to Xsim

--sendport SENDPORT target UDP port used to send data to GT7. Do not change unless you know what you are doing

--receiveport RECEIVEPORT source UDP port used to send data to GT7. Do not change unless you know what you are doing
`
The logpackets will generate two files called GT7packets.cap and GT7packets.raw.cap

GT7packets.cap can be used to replay the UDP stream using UDPSend_timed.py from the [Python_UDP_Receiver](https://github.com/vthinsel/Python_UDP_Receiver)

The csvoutput option will generate a CSV file called GT7data.csv which you can open with your favorite spreadsheet to make nice graphs
## Building a standalone executable

To build an executables install the dependencies and run:
``pyinstaller GT7Proxy.spec``
The GT7Proxy.exe will be located in the dist folder.

## Credits

Without all great [GTPlanet](https://www.gtplanet.net/forum/threads/gt7-is-compatible-with-motion-rig.410728/) contributors this wouldn't have been possible. Kudos to all the guys there !

Especially for the quaternion part, as Polyphony Digital provides telemetry data based on quaternion model. Quaternion extends complex numbers as per wikipedia https://en.wikipedia.org/wiki/Quaternion. Extending complexity is far beyond my brain capacity :D
Without assistance from Skinny McLean, tarnheld, nokazito and magicfr my motion rig would be silent.
Without poumpoum starting the thread and Nenkai starting reverse-engineering, there would be no telemetry at all.
Without all other contributors, we would still be wondering how to interpret and use telemetry in a efficient and fun way. Once again, thanks to all of you !

Keep in mind that this is an undocumented API from Grand Turismo Series, the game developer
might patch the game and close the door in the future.

Enjoy!
