from struct import unpack

class GTDataPacket:
    def __init__(self, data):
        ## Format string that allows unpack to process the data bytestream:
         gt_format = '<ifffffffffffffffccccfffffffffffihhiiihhhhhhBBBcffffffffffffffffffffffffffffffffffffi'
         (self.magic,              #int32
         self.position_x,         #single
         self.position_y,         #single
         self.position_z,         #single
         self.world_velocity_x,         #single
         self.world_velocity_y,         #single
         self.world_velocity_z,         #single
         self.rotation_x,         #single
         self.rotation_y,         #single
         self.rotation_z,         #single
         self.northorientation,   #single
         self.angularvelocity_x,     #single
         self.angularvelocity_y,     #single
         self.angularvelocity_z,     #single
         self.body_height,        #single
         self.rpm,                #single
         self.iv1,                #char
         self.iv2,                #char
         self.iv3,                #char
         self.iv4,                #char
         self.fuel_level,         #single
         self.fuel_capacity,      #single
         self.speed,              #single
         self.boost,              #single
         self.oil_pressure_bar,   #single
         self.water_temperature,  #single
         self.oil_temperature,    #single
         self.tire_temp_FL,       #single
         self.tire_temp_FR,       #single
         self.tire_temp_RL,       #single
         self.tire_temp_RR,       #single
         self.pkt_id,             #int32
         self.current_lap,        #int16
         self.total_laps,         #int16
         self.best_lap_time,      #int32
         self.last_lap_time,      #int32
         self.day_progression_ms, #int32
         self.pre_race_start_position,  #int16
         self.pre_race_num_cars,  #int16
         self.min_alert_rpm,  #int16
         self.max_alert_rpm,  #int16
         self.calculated_max_speed,  #int16
         self.flags, #int16
         self.suggestedgear_gear, #byte
         self.throttle,  #byte
         self.brake,  #byte
         self.padding_byte1,  #byte
         self.road_plane_x,    #single
         self.road_plane_y,    #single
         self.road_plane_z,    #single
         self.road_plane_dist,    #single
         self.tire_rps_FL,       #single
         self.tire_rps_FR,       #single
         self.tire_rps_RL,       #single
         self.tire_rps_RR,       #single
         self.tire_radius_FL,       #single
         self.tire_radius_FR,       #single
         self.tire_radius_RL,       #single
         self.tire_radius_RR,       #single
         self.susp_height_FL,    #single
         self.susp_height_FR,    #single
         self.susp_height_RL,    #single
         self.susp_height_RR,    #single
         self.unknown_single1, #byte
         self.unknown_single2, #byte
         self.unknown_single3, #byte
         self.unknown_single4, #byte
         self.unknown_single5, #byte
         self.unknown_single6, #byte
         self.unknown_single7, #byte
         self.unknown_single8, #byte
         self.clutch_pedal, #single
         self.clutch_engagement, #single
         self.rpm_clutch_gearbox,  #single
         self.transmission_top_speed,  #single
         self.gear_ratio1,        #single
         self.gear_ratio2,        #single
         self.gear_ratio3,        #single
         self.gear_ratio4,        #single
         self.gear_ratio5,        #single
         self.gear_ratio6,        #single
         self.gear_ratio7,        #single
         self.gear_ratio8,        #single
         self.car_code, #int32
         ) = unpack(gt_format, data)
    def __iter__(self):
        #return iter([self.position_x, self.position_y, self.position_z])
        #return iter(vars(self))
        #attrs = vars(self)
        #print(', '.join("%s: %s" % item for item in attrs.items()))
        return iter(self.__dict__.values())
        