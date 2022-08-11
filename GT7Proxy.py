import argparse
import csv
import signal
from datetime import datetime as dt
from datetime import timedelta as td
import socket
import sys
import struct
from salsa20 import Salsa20_xor
import datetime
import pickle
import time
from gt_packet_definition import GTDataPacket
from xsim_packet_definition import TelemetryPacket, PACKET_HEADER, API_VERSION

# ansi prefix
pref = "\033["

# ports for send and receive data
SendPort = 33739
ReceivePort = 33740

# ctrl-c handler
def handler(signum, frame):
	sys.stdout.write(f'{pref}?1049l')	# revert buffer
	sys.stdout.write(f'{pref}?25h')		# restore cursor
	sys.stdout.flush()
	exit(1)

# handle ctrl-c
signal.signal(signal.SIGINT, handler)

sys.stdout.write(f'{pref}?1049h')	# alt buffer
sys.stdout.write(f'{pref}?25l')		# hide cursor
sys.stdout.flush()

# get ip address from command line
#if len(sys.argv) == 2:
#    ip = sys.argv[1]
#else:
#    print('Run like : python3 gt7telemetry.py <playstation-ip>')
#    exit(1)


parser = argparse.ArgumentParser()
parser.add_argument("--ps_ip",
                    required=True,
                    type=str,
                    help="Playstation 4/5 IP address. Accepts IP or FQDN provided it resolves to something.")

parser.add_argument("--xsim_ip",
                    type=str,
                    default='127.0.0.1',
                    help="IP of the computer where XSim is running. Default is 127.0.0.1")

parser.add_argument("--xsim_port",
                    type=int,
                    default=33800,
                    help="Port where the XSim plugin is expecting to receive telemetry. Default is 33800")

parser.add_argument("--logpackets",
                    type=bool,
                    default=False,
                    help="Optionnaly log packets for future playback using https://github.com/vthinsel/Python_UDP_Receiver/UDPSend_timed.py .Default is False")

parser.add_argument("--csvoutput",
                    type=bool,
                    default=False,
                    help="Optionnaly output data to csv for analysis. Default is False")

parser.add_argument("--silent",
                    type=bool,
                    default=False,
                    help="limit console output to most usefull data for dashboard. Default is False")

args = parser.parse_args()


# Create a UDP socket and bind it
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('0.0.0.0', ReceivePort))
s.settimeout(5)

xsim_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
xsim_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
xsim_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
xsim_client_address = (args.xsim_ip, args.xsim_port)
xsim_socket.settimeout(5)

# data stream decoding
def salsa20_dec(dat):
	KEY = b'Simulator Interface Packet GT7 ver 0.0'
	# Seed IV is always located here
	oiv = dat[0x40:0x44]
	iv1 = int.from_bytes(oiv, byteorder='little')
	# Notice DEADBEAF, not DEADBEEF
	iv2 = iv1 ^ 0xDEADBEAF
	IV = bytearray()
	IV.extend(iv2.to_bytes(4, 'little'))
	IV.extend(iv1.to_bytes(4, 'little'))
	ddata = Salsa20_xor(dat, bytes(IV), KEY[0:32])
	magic = int.from_bytes(ddata[0:4], byteorder='little')
	if magic != 0x47375330:
		return bytearray(b'')
	return ddata

# send heartbeat
def send_hb(s):
	send_data = 'A'
	s.sendto(send_data.encode('utf-8'), (args.ps_ip, SendPort))
	#print('send heartbeat')

# generic print function
def printAt(str, row=1, column=1, bold=0, underline=0, reverse=0):
	sys.stdout.write('{}{};{}H'.format(pref, row, column))
	if reverse:
		sys.stdout.write('{}7m'.format(pref))
	if bold:
		sys.stdout.write('{}1m'.format(pref))
	if underline:
		sys.stdout.write('{}4m'.format(pref))
	if not bold and not underline and not reverse:
		sys.stdout.write('{}0m'.format(pref))
	sys.stdout.write(str)

def secondsToLaptime(seconds):
	remaining = seconds
	minutes = seconds // 60
	remaining = seconds % 60
	return '{:01.0f}:{:06.3f}'.format(minutes, remaining)


class LapCounter:
    def __init__(self):
        self.lap = -1
        self.paused = -1
        self.tick = 0
        self.pstart_tick = 0
        self.lstart_tick = 0
        self.lstart_ms = 0
        self.paused_ticks = 0
        self.last_lap_ms = 0
        self.special_packet_time = 0
    def update(self,lap,paused,tick,last_lap_ms):
        if lap == 0: # we have not started a lap or have reset
            self.special_packet_time = 0
        if lap != self.lap: # we have entered a new lap
            if self.lap != 0:
                normal_laptime = self.lapticks()*1000.0/60.0
                self.special_packet_time += last_lap_ms - self.lapticks()*1000.0/60.0
            self.lstart_tick = self.tick
            self.paused_ticks = 0
        if paused != self.paused: # paused has changed
            if paused: # we have switched to paused
                self.pstart_tick = self.tick
            else: # we have switched to not paused
                self.paused_ticks += tick - self.pstart_tick
        self.paused = paused
        self.lap = lap
        self.tick = tick
        self.last_lap_ms = last_lap_ms
    def pausedticks(self):
        if not self.paused:
            return self.paused_ticks
        else:
            return self.paused_ticks + (self.tick - self.pstart_tick)
    def lapticks(self):
        if self.lap == 0:
            return 0
        else:
            return self.tick - self.lstart_tick - self.pausedticks()
    def laptime(self):
        laptime = (self.lapticks() * 1./60.) - (self.special_packet_time/1000.)
        return round(laptime,3)

# start by sending heartbeat
send_hb(s)

printAt('GT7 Telemetry Display 0.7 (ctrl-c to quit)', 1, 1, bold=1)
printAt('Packet ID:', 1, 73)

printAt('{:<92}'.format('Current Track Data'), 3, 1, reverse=1, bold=1)
printAt('Time on track:', 3, 41, reverse=1)
printAt('Laps:    /', 5, 1)
printAt('Position:   /', 5, 21)
printAt('Best Lap Time:', 7, 1)
printAt('Current Lap Time: ', 7, 31)
printAt('Last Lap Time:', 8, 1)
printAt('Calc Lap Time: ', 8, 31)
printAt('{:<92}'.format('Current Car Data'), 10, 1, reverse=1, bold=1)
printAt('Car ID:', 10, 41, reverse=1)
printAt('Throttle:    %', 12, 1)
printAt('RPM:        rpm', 12, 21)
printAt('Speed:        kph', 12, 41)
printAt('Brake:       %', 13, 1)
printAt('Gear:   ( )', 13, 21)

if not args.silent:
	printAt('Clutch:       /', 15, 1)
	printAt('RPM After Clutch:        rpm', 15, 31)
	printAt('Boost:        kPa', 13, 41)
	printAt('Oil Temperature:       °C', 17, 1)
	printAt('Water Temperature:       °C', 17, 31)
	printAt('Oil Pressure:          bar', 18, 1)
	printAt('Body/Ride Height:        mm', 18, 31)
	printAt('Rev Warning       rpm', 12, 71)
	printAt('Rev Limiter       rpm', 13, 71)
	printAt('Max:', 14, 21)
	printAt('Est. Speed        kph', 14, 71)

	printAt('Tyre Data', 20, 1, underline=1)
	printAt('FL:        °C', 21, 1)
	printAt('FR:        °C', 21, 21)
	printAt('ø:      /       cm', 21, 41)
	printAt('           kph', 22, 1)
	printAt('           kph', 22, 21)
	printAt('Δ:      /       ', 22, 41)
	printAt('RL:        °C', 25, 1)
	printAt('RR:        °C', 25, 21)
	printAt('ø:      /       cm', 25, 41)
	printAt('           kph', 26, 1)
	printAt('           kph', 26, 21)
	printAt('Δ:      /       ', 26, 41)

	printAt('Gearing', 29, 1, underline=1)
	printAt('1st:', 30, 1)
	printAt('2nd:', 31, 1)
	printAt('3rd:', 32, 1)
	printAt('4th:', 33, 1)
	printAt('5th:', 34, 1)
	printAt('6th:', 35, 1)
	printAt('7th:', 36, 1)
	printAt('8th:', 37, 1)
	printAt('???:', 39, 1)

	printAt('Positioning (m)', 29, 21, underline=1)
	printAt('X:', 30, 21)
	printAt('Y:', 31, 21)
	printAt('Z:', 32, 21)

	printAt('Velocity (m/s)', 29, 41, underline=1)
	printAt('X:', 30, 41)
	printAt('Y:', 31, 41)
	printAt('Z:', 32, 41)

	printAt('Rotation', 34, 21, underline=1)
	printAt('X/Pitch:', 35, 21)
	printAt('Y/Yaw:', 36, 21)
	printAt('Z/Roll:', 37, 21)

	printAt('Angular (r/s)', 34, 41, underline=1)
	printAt('X:', 35, 41)
	printAt('Y:', 36, 41)
	printAt('Z:', 37, 41)

	printAt('Acceleration (m/s^2)', 34, 58, underline=1)
	printAt('X/Surge:', 35, 58)
	printAt('Y/Sway:', 36, 58)
	printAt('Z/Heave:', 37, 58)

	printAt('N/S:', 39, 21)

sys.stdout.flush()

prevlap = -1
pktid = 0
pknt = 0
previousts = datetime.datetime.now()
if args.logpackets:
	f1 = open("GT7packets.cap", 'wb')
	f2 = open("GT7packets.raw.cap" , 'wb')
	f3 = open("GT7packets.csv", 'wb')
if args.csvoutput:
	csvfile=open("GT7data.csv",'w', newline='')
	csvwriter = csv.writer(csvfile)
delta = 0
udppackets = 0
lapcounter = LapCounter()
previous_velocity_x = 0
previous_velocity_y = 0
previous_velocity_z = 0
accel_x = 0
accel_y = 0
accel_z = 0
csvheader = True
while True:
	try:
		data, address = s.recvfrom(4096)
		ts = datetime.datetime.now()
		delta = ts - previousts
		previousts = datetime.datetime.now()
		if args.logpackets:
			previoustime = ('{:%H:%M:%S:%f}'.format(datetime.datetime.now()))
			record = [previoustime, delta, data]
			pickle.dump(record, f1)
			f2.write(data)
		pknt = pknt + 1
		ddata = salsa20_dec(data)
		#ts = datetime.datetime.now()
		telemetry = GTDataPacket(ddata[0:296])
		if args.csvoutput:
			if csvheader:
				csvwriter.writerow(telemetry.__dict__.keys())
				csvheader = False
			csvwriter.writerow(telemetry)
		if len(ddata) > 0 and telemetry.pkt_id > pktid:
			pktid = telemetry.pkt_id
			bstlap = telemetry.best_lap_time
			lstlap = telemetry.last_lap_time
			curlap = telemetry.current_lap
			#rpm_min,rpm_max,v_max,flags = struct.unpack_from('hhhh',ddata,0x88)
			paused = telemetry.flags&2 # second bit in flags is paused
			lapcounter.update(curlap,paused,pktid,telemetry.last_lap_time)
			cgear = telemetry.suggestedgear_gear & 0b00001111
			sgear = telemetry.suggestedgear_gear >> 4
			#print ("lapcounter.laptime:",lapcounter.laptime())
			if curlap > 0:
				dt_now = dt.now()
				if curlap != prevlap:
					prevlap = curlap
					dt_start = dt_now
				curLapTime = dt_now - dt_start
				printAt('{:>9}'.format(secondsToLaptime(curLapTime.total_seconds())), 7, 49)
			else:
				curLapTime = 0
				printAt('{:>9}'.format(''), 7, 49)
			if delta.microseconds != 0:
				accel_x=(telemetry.velocity_x - previous_velocity_x )*1000000 / delta.microseconds
				accel_y=(telemetry.velocity_y - previous_velocity_y )*1000000 / delta.microseconds
				accel_z=(telemetry.velocity_z - previous_velocity_z )*1000000 / delta.microseconds
			previous_velocity_x=telemetry.velocity_x
			previous_velocity_y=telemetry.velocity_y
			previous_velocity_z=telemetry.velocity_z
			xsim_packet = TelemetryPacket(PACKET_HEADER,
								API_VERSION,
								str.encode("PS_GT7"),
								str.encode("{}".format(telemetry.car_code)),
								str.encode('NA'),
								1,
								telemetry.speed*3.6,
								telemetry.rpm,
								telemetry.max_alert_rpm,
								cgear,
								telemetry.rotation_x, # roll
								telemetry.rotation_y, # yaw
								telemetry.rotation_z, # pitch
								accel_x , # surge
								accel_y , # heave
								accel_z , # sway
								0, # Traction Loss
								telemetry.oil_temperature,
								telemetry.oil_pressure_bar,
								telemetry.water_temperature,
								telemetry.flags & 0b0000000000000010, #game paused ?
								telemetry.flags & 0b0000000000000001, # on track ?
								telemetry.flags & 0b0000000000010000, # rev limit active ?
								telemetry.flags & 0b0000000000100000, # Handbrake active ?
								telemetry.flags & 0b0000001000000000, # ASM active ?
								telemetry.flags & 0b0000010000000000, # TCS active ?
								telemetry.throttle,
								telemetry.brake,
								telemetry.position_x,
								telemetry.position_y,
								telemetry.position_z,
								telemetry.velocity_x,
								telemetry.velocity_y,
								telemetry.velocity_z,
								telemetry.angularvelocity_x,
								telemetry.angularvelocity_y,
								telemetry.angularvelocity_z,
								telemetry.road_plane_x,
								telemetry.road_plane_y,
								telemetry.road_plane_z,								
								telemetry.unknown_single1,
								telemetry.unknown_single4,
								telemetry.fuel_level,
								telemetry.fuel_capacity,
								telemetry.current_lap,
								telemetry.total_laps,
								telemetry.best_lap_time,
								telemetry.last_lap_time,
								telemetry.pre_race_start_position,
								telemetry.pre_race_num_cars,
								telemetry.boost,
								telemetry.susp_height_FL,
								telemetry.susp_height_FR,
								telemetry.susp_height_RL,
								telemetry.susp_height_RR,
								)
			try:
				xsim_socket.sendto(xsim_packet, xsim_client_address)
			except Exception as e:
				print('Error sending telemetry to SRS ', str(e))

			if cgear < 1:
				cgear = 'R'
			if sgear > 14:
				sgear = '–'

			boost = telemetry.boost - 1
			hasTurbo = True if boost > -1 else False

			tyreDiamFL = telemetry.tire_radius_FL
			tyreDiamFR = telemetry.tire_radius_FR
			tyreDiamRL = telemetry.tire_radius_RL
			tyreDiamRR = telemetry.tire_radius_RR

			tyreSpeedFL = abs(3.6 * tyreDiamFL * telemetry.tire_rps_FL)
			tyreSpeedFR = abs(3.6 * tyreDiamFR * telemetry.tire_rps_FR)
			tyreSpeedRL = abs(3.6 * tyreDiamRL * telemetry.tire_rps_RL)
			tyreSpeedRR = abs(3.6 * tyreDiamRR * telemetry.tire_rps_RR)

			carSpeed = 3.6 * telemetry.speed

			if carSpeed > 0:
				tyreSlipRatioFL = '{:6.2f}'.format(tyreSpeedFL / carSpeed)
				tyreSlipRatioFR = '{:6.2f}'.format(tyreSpeedFR / carSpeed)
				tyreSlipRatioRL = '{:6.2f}'.format(tyreSpeedRL / carSpeed)
				tyreSlipRatioRR = '{:6.2f}'.format(tyreSpeedRR / carSpeed)
			else:
				tyreSlipRatioFL = '  –  '
				tyreSlipRatioFR = '  –  '
				tyreSlipRatioRL = '  -  '
				tyreSlipRatioRR = '  –  '

			printAt('{:>8}'.format(str(td(seconds=round(telemetry.day_progression_ms / 1000)))), 3, 56, reverse=1)	# time of day on track

			printAt('{:3.0f}'.format(curlap), 5, 7)															# current lap
			printAt('{:3.0f}'.format(telemetry.total_laps), 5, 11)						# total laps

			printAt('{:2.0f}'.format(telemetry.pre_race_start_position), 5, 31)						# current position
			printAt('{:2.0f}'.format(telemetry.pre_race_num_cars), 5, 34)						# total positions

			if bstlap != -1:
				printAt('{:>9}'.format(secondsToLaptime(bstlap / 1000)), 7, 16)		# best lap time
			else:
				printAt('{:>9}'.format(''), 7, 16)
			if lstlap != -1:
				printAt('{:>9}'.format(secondsToLaptime(lstlap / 1000)), 8, 16)		# last lap time
			else:
				printAt('{:>9}'.format(''), 8, 16)
			printAt(str(lapcounter.laptime()), 8, 49)		

			printAt('{:5.0f}'.format(telemetry.car_code), 10, 48, reverse=1)		# car id

			printAt('{:3.0f}'.format(telemetry.throttle / 2.55), 12, 11)				# throttle
			printAt('{:7.0f}'.format(telemetry.rpm), 12, 25)					# rpm
			printAt('{:7.1f}'.format(carSpeed), 12, 47)														# speed kph
			printAt('{:3.0f}'.format(telemetry.brake / 2.55), 13, 11)				# brake
			printAt('{}'.format(cgear), 13, 27)																# actual gear
			printAt('{}'.format(sgear), 13, 30)																# suggested gear
			printAt('{:>10}'.format(pktid), 1, 83)						# packet id

			if not args.silent:
				fuelCapacity = telemetry.fuel_capacity
				isEV = False if fuelCapacity > 0 else True
				if isEV:
					printAt('Charge:', 14, 1)
					printAt('{:3.0f} kWh'.format(telemetry.fuel_level), 14, 11)		# charge remaining
					printAt('??? kWh'.format(telemetry.fuel_capacity), 14, 29)			# max battery capacity
				else:
					printAt('Fuel:  ', 14, 1)
					printAt('{:3.0f} lit'.format(telemetry.fuel_level), 14, 11)		# fuel
					printAt('{:3.0f} lit'.format(telemetry.fuel_capacity), 14, 29)		# max fuel

				if hasTurbo:
					printAt('{:7.2f}'.format(telemetry.boost - 1), 13, 47)			# boost
				else:
					printAt('{:>7}'.format('–'), 13, 47)														# no turbo

				printAt('{:5.0f}'.format(telemetry.max_alert_rpm), 13, 83)					# rpm rev limiter
				printAt('{:5.0f}'.format(telemetry.min_alert_rpm), 12, 83)					# rpm rev warning
				printAt('{:5.0f}'.format(telemetry.calculated_max_speed), 14, 83)					# estimated top speed

				printAt('{:5.3f}'.format(telemetry.clutch_pedal), 15, 9)						# clutch
				printAt('{:5.3f}'.format(telemetry.clutch_engagement), 15, 17)					# clutch engaged
				printAt('{:7.0f}'.format(telemetry.rpm_clutch_gearbox), 15, 48)					# rpm after clutch

				printAt('{:6.1f}'.format(telemetry.oil_temperature), 17, 17)					# oil temp
				printAt('{:6.1f}'.format(telemetry.water_temperature), 17, 49)					# water temp

				printAt('{:6.2f}'.format(telemetry.oil_pressure_bar), 18, 17)					# oil pressure
				printAt('{:6.0f}'.format(1000 * telemetry.body_height), 18, 49)				# ride height

				printAt('{:6.1f}'.format(telemetry.tire_temp_FL), 21, 5)						# tyre temp FL
				printAt('{:6.1f}'.format(telemetry.tire_temp_FR), 21, 25)					# tyre temp FR
				printAt('{:6.1f}'.format(telemetry.tire_temp_RL), 25, 5)						# tyre temp RL
				printAt('{:6.1f}'.format(telemetry.tire_temp_RR), 25, 25)					# tyre temp RR
				
				printAt('{:6.1f}'.format(200 * tyreDiamFL), 21, 43)												# tyre diameter FL
				printAt('{:6.1f}'.format(200 * tyreDiamFR), 21, 50)												# tyre diameter FR
				printAt('{:6.1f}'.format(200 * tyreDiamRL), 25, 43)												# tyre diameter RL
				printAt('{:6.1f}'.format(200 * tyreDiamRR), 25, 50)												# tyre diameter RR

				printAt('{:6.1f}'.format(tyreSpeedFL), 22, 5)													# tyre speed FL
				printAt('{:6.1f}'.format(tyreSpeedFR), 22, 25)													# tyre speed FR
				printAt('{:6.1f}'.format(tyreSpeedRL), 26, 5)													# tyre speed RL
				printAt('{:6.1f}'.format(tyreSpeedRR), 26, 25)													# tyre speed RR
				
				printAt(tyreSlipRatioFL, 22, 43)																# tyre slip ratio FL
				printAt(tyreSlipRatioFR, 22, 50)																# tyre slip ratio FR
				printAt(tyreSlipRatioRL, 26, 43)																# tyre slip ratio RL
				printAt(tyreSlipRatioRR, 26, 50)																# tyre slip ratio RR

				printAt('{:6.3f}'.format(telemetry.susp_height_FL), 23, 5)						# suspension FL
				printAt('{:6.3f}'.format(telemetry.susp_height_FR), 23, 25)					# suspension FR
				printAt('{:6.3f}'.format(telemetry.susp_height_RL), 27, 5)						# suspension RL
				printAt('{:6.3f}'.format(telemetry.susp_height_RR), 27, 25)					# suspension RR
				
				printAt('{:7.3f}'.format(telemetry.gear_ratio1), 30, 5)					# 1st gear
				printAt('{:7.3f}'.format(telemetry.gear_ratio2), 31, 5)					# 2nd gear
				printAt('{:7.3f}'.format(telemetry.gear_ratio3), 32, 5)					# 3rd gear
				printAt('{:7.3f}'.format(telemetry.gear_ratio4), 33, 5)					# 4th gear
				printAt('{:7.3f}'.format(telemetry.gear_ratio5), 34, 5)					# 5th gear
				printAt('{:7.3f}'.format(telemetry.gear_ratio6), 35, 5)					# 6th gear
				printAt('{:7.3f}'.format(telemetry.gear_ratio7), 36, 5)					# 7th gear
				printAt('{:7.3f}'.format(telemetry.gear_ratio8), 37, 5)					# 8th gear

				printAt('{:7.3f}'.format(telemetry.transmission_top_speed), 39, 5)					# ??? gear

				printAt('{:11.4f}'.format(telemetry.position_x), 30, 28)					# pos X
				printAt('{:11.4f}'.format(telemetry.position_y), 31, 28)					# pos Y
				printAt('{:11.4f}'.format(telemetry.position_z), 32, 28)					# pos Z

				printAt('{:11.4f}'.format(telemetry.velocity_x), 30, 43)					# velocity X
				printAt('{:11.4f}'.format(telemetry.velocity_y), 31, 43)					# velocity Y
				printAt('{:11.4f}'.format(telemetry.velocity_z), 32, 43)					# velocity Z

				printAt('{:9.4f}'.format(telemetry.rotation_x), 35, 28)					# rot Pitch
				printAt('{:9.4f}'.format(telemetry.rotation_y), 36, 28)					# rot Yaw
				printAt('{:9.4f}'.format(telemetry.rotation_z), 37, 28)					# rot Roll

				printAt('{:9.4f}'.format(telemetry.angularvelocity_x), 35, 45)
				printAt('{:9.4f}'.format(telemetry.angularvelocity_y), 36, 45)
				printAt('{:9.4f}'.format(telemetry.angularvelocity_z), 37, 45)

				printAt('{:9.4f}'.format(accel_x), 35, 65)					# acceleration X
				printAt('{:9.4f}'.format(accel_y), 36, 65)					# acceleration Y
				printAt('{:9.4f}'.format(accel_z), 37, 65)					# acceleration Z

				printAt('{:7.4f}'.format(telemetry.northorientation), 39, 25)					# rot ???

				printAt('0x8E BITS  =  {:0>8}'.format(bin(struct.unpack('B', ddata[0x8E:0x8E+1])[0])[2:]), 23, 71)	# various flags (see https://github.com/Nenkai/PDTools/blob/master/PDTools.SimulatorInterface/SimulatorPacketG7S0.cs)
				printAt('0x8F BITS  =  {:0>8}'.format(bin(struct.unpack('B', ddata[0x8F:0x8F+1])[0])[2:]), 24, 71)	# various flags (see https://github.com/Nenkai/PDTools/blob/master/PDTools.SimulatorInterface/SimulatorPacketG7S0.cs)
				printAt('0x93 BITS  =  {:0>8}'.format(bin(struct.unpack('B', ddata[0x93:0x93+1])[0])[2:]), 25, 71)	# 0x93 = ???

				printAt('Map X {:11.5f}'.format(telemetry.road_plane_x), 27, 71)			# 0x94 = ???
				printAt('Map Y {:11.5f}'.format(telemetry.road_plane_y), 28, 71)			# 0x98 = ???
				printAt('Map Z {:11.5f}'.format(telemetry.road_plane_z), 29, 71)			# 0x9C = ???
				printAt('Map Dist {:11.5f}'.format(telemetry.road_plane_dist), 30, 71)			# 0xA0 = ???

			#printAt('0xD4 FLOAT {:11.5f}'.format(struct.unpack('f', ddata[0xD4:0xD4+4])[0]), 32, 71)			# 0xD4 = ???
			#printAt('0xD8 FLOAT {:11.5f}'.format(struct.unpack('f', ddata[0xD8:0xD8+4])[0]), 33, 71)			# 0xD8 = ???
			#printAt('0xDC FLOAT {:11.5f}'.format(struct.unpack('f', ddata[0xDC:0xDC+4])[0]), 34, 71)			# 0xDC = ???
			#printAt('0xE0 FLOAT {:11.5f}'.format(struct.unpack('f', ddata[0xE0:0xE0+4])[0]), 35, 71)			# 0xE0 = ???

			#printAt('0xE4 FLOAT {:11.5f}'.format(struct.unpack('f', ddata[0xE4:0xE4+4])[0]), 36, 71)			# 0xE4 = ???
			#printAt('0xE8 FLOAT {:11.5f}'.format(struct.unpack('f', ddata[0xE8:0xE8+4])[0]), 37, 71)			# 0xE8 = ???
			#printAt('0xEC FLOAT {:11.5f}'.format(struct.unpack('f', ddata[0xEC:0xEC+4])[0]), 38, 71)			# 0xEC = ???
			#printAt('0xF0 FLOAT {:11.5f}'.format(struct.unpack('f', ddata[0xF0:0xF0+4])[0]), 39, 71)			# 0xF0 = ???#


		if pknt > 100:
			send_hb(s)
			pknt = 0
	except Exception as e:
		printAt('Exception: {}'.format(e), 41, 1, reverse=1)
		send_hb(s)
		pknt = 0
		pass

	sys.stdout.flush()
