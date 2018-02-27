__all__ = ["STKConfig"]

class STKConfig:
    
    version = "11.1"
    outputColumns = ['time_utcg',
                     'phase_angle_deg',
                     'r_km',
                     'delta_km',
                     'topo_RA_deg',
                     'topo_Dec_deg',
                     'topo_x_km',
                     'topo_y_km',
                     'topo_z_km',
                     'topo_vx_km_p_sec',
                     'topo_vy_km_p_sec',
                     'topo_vz_km_p_sec',
                     'j2000_x_km',
                     'j2000_y_km',
                     'j2000_z_km',
                     'j2000_vx_km_p_sec',
                     'j2000_vy_km_p_sec',
                     'j2000_vz_km_p_sec']
    verbose = True