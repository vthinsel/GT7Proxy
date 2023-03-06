'''
Sim Racing Studio API.
'''
from ctypes import *

# definition of the constants
PACKET_HEADER = str.encode('xsimpkt')  # constant to identify the package
API_VERSION = 100  # constant of the current version of the api

# defition of the Telemetry Class
class TelemetryPacket(Structure):
    _fields_ = [('api_mode', c_char * 8),  # 'api' constant to identify packet
                ('version', c_uint),  # version value = 102
                ('game', c_char * 16),  # Game name for example Project Cars 2
                ('vehicle_name', c_char * 16),  # anything identifying the car (name, ID, ....)
                ('location', c_char * 20),  # track name, location, airport, etc
                ('pkt_type',c_ubyte), # Packet type
                ('speed', c_float),  # float
                ('rpm', c_float),  # float
                ('max_rpm', c_float),  # float
                ('gear', c_short),  # -1=revere 0=Neutral 1 to 9=gears
                ('rx', c_float),  # in degrees -180 to +180 - Roll for XSim plugin
                ('ry', c_float),  # in degrees -180 to +180 Yaw for XSim plugin
                ('rz', c_float),  # in degrees -180 to +180 Pitch for XSim plugin
                ('ax', c_float),  # gforce acceleration  Surge for XSim plugin
                ('ay', c_float),  # gforce acceleration Heave for XSim plugin
                ('az', c_float),  # gforce acceleration Sway for XSim plugin
                ('traction_loss', c_float),  # gforce in float values beteween 0 to 10
                ('oil_temp', c_float),  # oil temp
                ('oil_pressure', c_float),  # oil pressure
                ('water_temp', c_float),  # water temp
                ('pause', c_bool),  # is game paused ?
                ('ontrack', c_bool),  # is car on track?
                ('revlimitactive', c_bool),  # is rev limiter active ?
                ('handbrake', c_bool),  # is handbrake on ?
                ('asmactive', c_bool),  # is ASM on ?
                ('tcsactive', c_bool),  # is TCS on ?
                ('throttle',c_byte),
                ('brake',c_byte),
                ('px', c_float), 
                ('py', c_float),
                ('pz', c_float),
                ('vx', c_float),
                ('vy', c_float),
                ('vz', c_float),
                ('arx', c_float),
                ('ary', c_float),
                ('arz', c_float),
                ('planex', c_float),
                ('planey', c_float),
                ('planez', c_float),
                ('single01', c_float),
                ('single02', c_float),
                ('fuel_level', c_float),
                ('fuel_capacity', c_float),
                ('lap', c_uint16),
                ('lap_total', c_uint16),
                ('lap_best', c_uint32),
                ('lap_last', c_uint32),
                ('position_pre', c_uint16),
                ('participants_num', c_uint16),
                ('boost', c_float),
                ('suspvelocityFL', c_float),
                ('suspvelocityFR', c_float),
                ('suspvelocityRL', c_float),
                ('suspvelocityRR', c_float),
                ('lights',c_bool),
                ('lowbeam', c_bool),
                ('highbeam', c_bool),
                ('load_process', c_bool),

                ]
    def __iter__(self):
        #return iter([self.position_x, self.position_y, self.position_z])
        #return iter(vars(self))
        #attrs = vars(self)
        #print(', '.join("%s: %s" % item for item in attrs.items()))
        return iter(self.__dict__.values())