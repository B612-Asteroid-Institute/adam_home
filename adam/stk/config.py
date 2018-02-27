__all__ = ["STKConfig"]

class STKConfig:
    
    version = "11.1"
    outputColumns = [
        "time_utcg",
        "phase_angle_deg",
        "r_km",
        "delta_km",
        "topo_RA_deg",
        "topo_Dec_deg",
        "topo_x_km",
        "topo_y_km",
        "topo_z_km",
        "topo_vx_km_p_sec",
        "topo_vy_km_p_sec",
        "topo_vz_km_p_sec",
        "j2000_x_km",
        "j2000_y_km",
        "j2000_z_km",
        "j2000_vx_km_p_sec",
        "j2000_vy_km_p_sec",
        "j2000_vz_km_p_sec"
    ]
    visitTableMapping = {
        "visit_ID" : "observationId",
        "field_ID" : "fieldId",
        "fieldRA_deg" : "fieldRA",
        "fieldDec_deg" : "fieldDec",
        "altitude_deg" : "altitude",
        "azimuth_deg" : "azimuth",
        "filter" : "filter",
        "night" : "night",
        "expDate_sec" : "observationStartTime",
        "expMJD_mjd" : "observationStartMJD",
        "visitTime_sec" : "visitTime",
        "visitExpTime_sec" : "visitExposureTime",
        "FWHMgeom_arcsec" : "seeingFwhmGeom",
        "FWHMeff_arcsec" : "seeingFwhmEff",
        "fiveSigmaDepth_mag" : "fiveSigmaDepth",
    }
    verbose = True