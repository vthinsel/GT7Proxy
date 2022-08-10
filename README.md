# Gran Turismo 7 UDP proxy for XSim and others....


All the credits go to guys at GTPlanet that all contributed to analyze/share/decrypt data:
@Nenkai https://github.com/Nenkai/PDTools/tree/master/PDTools.SimulatorInterface and also @Bornhall and @gt7coder on GTPlanet forum too ! And others...

Keep in mind that this is an undocumented API from Grand Turismo Series, the game developer
might patch the game and close the door in the future.

To run the script via Python, you need to have at least the version 3.9 installed.
Clone this repository and install all dependencies:
pip install -r requirements.txt

Then runn the proxy with at least one argument representing the PlayStation/Whatever IP:
python GT7Proxy.py --ps_ip myps.local 

Detailed usage:
usage: GT7Proxy.py [-h] --ps_ip PS_IP [--xsim_ip XSIM_IP] [--xsim_port XSIM_PORT] [--logpackets LOGPACKETS] [--csvoutput CSVOUTPUT] [--silent SILENT]

options:
  -h, --help            show this help message and exit
  --ps_ip PS_IP         Playstation 4/5 IP address. Accepts IP or FQDN provided it resolves to something.
  --xsim_ip XSIM_IP     IP of the computer where XSim is running. Default is 127.0.0.1
  --xsim_port XSIM_PORT
                        Port where the XSim plugin is expecting to receive telemetry. Default is 33800
  --logpackets LOGPACKETS
                        Optionnaly log packets for future playback using https://github.com/vthinsel/Python_UDP_Receiver/UDPSend_timed.py .Default is False
  --csvoutput CSVOUTPUT
                        Optionnaly output data to csv for analysis. Default is False
  --silent SILENT       limit console output to most usefull data for dashboard. Default is False

-------------------

To build an executables install the dependencies and run:
pyinstaller main.spec   
The exe will be located in the dist folder normally.

Enjoy!


