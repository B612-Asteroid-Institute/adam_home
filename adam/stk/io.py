import numpy as np

from .config import STKConfig

__all__ = ["createVectorFile", 
           "createSensorFile",
           "createIntervalFile", 
           "convertPointingsToSensorInterval",
           "convertPointingsToVectorInterval"]

def createVectorFile(fileName,
                     observationIds,
                     exposureStart,
                     exposureEnd, 
                     ra,
                     dec,
                     epochStart,
                     verbose=STKConfig.verbose):
    """
    Builds an STK vector file given a series of sensor pointings.
    
    Args:
        fileName (str): Name to save vector file to. Extension should not be included.
                        (e.g., "VectorInput")
        exposureStart (`~numpy.ndarray`): Exposure start times in seconds from epochStart.
                                         (e.g., "np.array([332, 367, ...])")
        exposureEnd (`~numpy.ndarray`): Exposure end times in seconds from epochStart.
                                        (e.g., "np.array([362, 397, ...])")
        ra (`~numpy.ndarray`): Right ascension in degrees. 
                                    (e.g., "np.array([22.3454, 26.7565, ...])")
        dec (`~numpy.ndarray`): Declination in degrees.
                                    (e.g., "np.array([65.8922, 63.2398, ...])")
        epochStart (str): Time of epoch start.
                          (e.g., "'1 Jan 2022 00:00:00'")
        observationIds (`~numpy.ndarray): List of observation ids corresponding to the pointings.
                                          (e.g., "numpy.ndarray([1, 2, 3, 4, ...])")
        verbose (bool): Print progress statements?
        
    Returns:
        None
    """    
    header = ["stk.v.{}\n".format(STKConfig.version),
              "Begin VectorData\n",
              "NumberOfVectorDataPoints {}\n".format(2*len(exposureStart)),
              "ScenarioEpoch {}\n".format(epochStart),
              "InterpolationSamplesM1 0\n",
              "CentralBody Earth\n",
              "CoordinateAxes ICRF\n",
              "DimensionName Distance\n",
              "VectorDataTimeRaDecMag\n"]
    
    vectorFile = open(fileName + ".vd", "w")
    mappingFile = open(fileName + "_mapping.txt", "w")
    
    if verbose is True:
        print("Writing vector pointing file: {}".format(fileName + ".vd"))
        print("Writing observation Id to vector mapping file: {}".format(fileName + "_mapping.txt"))
        
    # Write header
    for line in header:
        vectorFile.write(line)
    
    # Write pointings
    for obsId, ti, tf, az, el in zip(observationIds, exposureStart, exposureEnd, ra, dec):
        # Need to figure out magnitude
        vectorFile.write("{} {} {} 1.0\n".format(ti, az, el))
        vectorFile.write("{} {} {} 1.0\n".format(tf, az, el))
        mappingFile.write("{}\n".format(obsId))
        mappingFile.write("{}\n".format(obsId))

    # Write file footer
    vectorFile.write("End VectorData")
    vectorFile.close()
    if verbose is True:
        print("Done. Wrote {} pointing start and end times.".format(2*len(exposureStart)))
        print("")
        
    return

def createSensorFile(fileName,
                     exposureStart,
                     exposureEnd, 
                     azimuth,
                     elevation,
                     epochStart,
                     verbose=STKConfig.verbose):
    """
    Builds an STK sensor file given a series of sensor pointings.
    
    WARNING
    TODO: Need azimuth and elevation for both start and end of exposure. 
    
    Args:
        fileName (str): Name to save sensor file to. Extension should not be included.
                        (e.g., "SensorPointing")
        exposureStart (`~numpy.ndarray`): Exposure start times in seconds from epochStart.
                                         (e.g., "np.array([332, 367, ...])")
        exposureEnd (`~numpy.ndarray`): Exposure end times in seconds from epochStart.
                                        (e.g., "np.array([362, 397, ...])")
        azimuth (`~numpy.ndarray`): Azimuth angles in degrees. 
                                    (e.g., "np.array([22.3454, 26.7565, ...])")
        elevation (`~numpy.ndarray`): Elevation angles in degrees.
                                    (e.g., "np.array([65.8922, 63.2398, ...])")
        epochStart (str): Time of epoch start.
                          (e.g., "'1 Jan 2022 00:00:00'")
        verbose (bool): Print progress statements?
        
    Returns:
        None
    """    
    header = ["stk.v.{}\n".format(STKConfig.version),
              "Begin Attitude\n",
              "NumberofAttitudePoints {}\n".format(2*len(exposureStart)),
              "Sequence 323\n",
              "ScenarioEpoch {}\n".format(epochStart),
              "AttitudeTimeAzElAngles\n"]
    
    sensorFile = open(fileName + ".sp", "w")
    if verbose is True:
        print("Writing sensor pointing file: {}".format(fileName + ".sp"))
    
    # Write header
    for line in header:
        sensorFile.write(line)
    
    # Write pointings
    for ti, tf, az, el in zip(exposureStart, exposureEnd, azimuth, elevation):
        sensorFile.write("{} {} {}\n".format(ti, az, el))
        sensorFile.write("{} {} {}\n".format(tf, az, el))

    # Write file footer
    sensorFile.write("End Attitude")
    sensorFile.close()
    if verbose is True:
        print("Done. Wrote {} pointing start and end times.".format(2*len(exposureStart)))
        print("")

    return
                         
def createIntervalFile(fileName,
                       exposureStart,
                       exposureEnd,
                       epochStart,
                       verbose=STKConfig.verbose):
    """
    Builds an STK interval file given a series of sensor pointing times.
    
    Args:
        fileName (str): Name to save interval file to. Extension should not be included.
                        (e.g., "IntervalList")
        exposureStart (`~numpy.ndarray`): Exposure start times in seconds from epochStart.
                                         (e.g., "np.array([332, 367, ...])")
        exposureEnd (`~numpy.ndarray`): Exposure end times in seconds from epochStart.
                                        (e.g., "np.array([362, 397, ...])")
        epochStart (str): Time of epoch start.
                          (e.g., "'1 Jan 2022 00:00:00'")
        verbose (bool): Print progress statements?
        
    Returns:
        None
    """                     
    header = ["stk.v.{}\n".format(STKConfig.version),
              "BEGIN IntervalList\n\n",
              "\tScenarioEpoch {}\n\n".format(epochStart),
              "Begin Intervals\n\n"]
                                                  
    intervalFile = open(fileName + ".int", "w")
    if verbose is True:
        print("Writing interval file: {}".format(fileName + ".int"))
    
    # Write header
    for line in header:
        intervalFile.write(line)
    
    # Write intervals
    for ti, tf in zip(exposureStart, exposureEnd):
        # Interval line should have start time and end time 
        # delimited with a space
        intervalFile.write("{} {}\n".format(ti, tf))
    
    # Write file footer
    intervalFile.write("\n")
    intervalFile.write("END Intervals\n")
    intervalFile.write("\n")
    intervalFile.write("END IntervalList")
    if verbose is True:
        print("Done. Wrote {} intervals.".format(len(exposureStart)))
        print("")
    return
                         
def convertPointingsToSensorInterval(sensorFileName,
                                     intervalFileName,
                                     exposureStart, 
                                     azimuth,
                                     elevation,
                                     epochStart,
                                     exposureEnd=None,
                                     exposureLength=None,
                                     verbose=STKConfig.verbose):
    """
    Builds a sensor pointing file and interval file for a series of sensor pointings. 
    
    WARNING
    TODO: Need azimuth and elevation for both start and end of exposure. See createSensorFile.
    
    Args:
        sensorFileName (str): Name to save sensor file to. Extension should not be included.
                              (e.g., "SensorPointing")
        intervalFileName (str): Name to save interval file to. Extension should not be included.
                              (e.g., "IntervalList")
        exposureStart (`~numpy.ndarray`): Exposure start times in seconds from epochStart.
                                         (e.g., "np.array([332, 367, ...])")
        azimuth (`~numpy.ndarray`): Azimuth angles in degrees. 
                                    (e.g., "np.array([22.3454, 26.7565, ...])")
        elevation (`~numpy.ndarray`): Elevation angles in degrees.
                                    (e.g., "np.array([65.8922, 63.2398, ...])")
        epochStart (str): Time of epoch start.
                          (e.g., "'1 Jan 2022 00:00:00'")
        exposureEnd (`~numpy.ndarray`): Exposure end times in seconds from epochStart. If not
                                        defined, will use static exposureLength to calculate exposure
                                        end times. 
                                        (e.g., "np.array([362, 397, ...])")
        exposureLength (float): If exposure end times are None, calculate exposure end times with this 
                                static value (exposureEnd = exposureStart + exposureLength).
                                (e.g., 30)
        verbose (bool): Print progress statements?
        
    Returns:
        None 

    Raises:
        ValueError : If exposureLength and exposureEnd are None

    """                
    # Check that either exposureEnd or exposureLength are defined 
    if exposureEnd is None and exposureLength is None:
        raise ValueError("Either exposureLength or exposureEnd should be defined, or else pointings will be interpolated.")
    elif exposureLength is not None and exposureEnd is None:
        exposureEnd = exposureStart + np.ones(len(exposureStart), dtype=int) * exposureLength
         
    # Create the sensor pointing file                  
    createSensorFile(sensorFileName, exposureStart, exposureEnd,
                     azimuth, elevation, epochStart, verbose=verbose)
    
    # Create interval file
    createIntervalFile(intervalFileName, exposureStart, exposureEnd, epochStart, verbose=verbose)
                         
    return

def convertPointingsToVectorInterval(vectorFileName,
                                     intervalFileName,
                                     observationIds,
                                     exposureStart, 
                                     ra,
                                     dec,
                                     epochStart,
                                     exposureEnd=None,
                                     exposureLength=None,
                                     verbose=STKConfig.verbose):
    """
    Builds a sensor pointing file and interval file for a series of sensor pointings. 
    
    TODO: Automatically calculate epochStart using the provided arrays.
    
    Args:
        vectorFileName (str): Name to save vector file to. Extension should not be included.
                              (e.g., "VectorInput")
        intervalFileName (str): Name to save interval file to. Extension should not be included.
                              (e.g., "IntervalList")
        observationIds (`~numpy.ndarray): List of observation ids corresponding to the pointings.
                                          (e.g., "numpy.ndarray([1, 2, 3, 4, ...])")
        exposureStart (`~numpy.ndarray`): Exposure start times in seconds from epochStart.
                                         (e.g., "np.array([332, 367, ...])")
        ra (`~numpy.ndarray`): Right ascension in degrees. 
                                    (e.g., "np.array([22.3454, 26.7565, ...])")
        dec (`~numpy.ndarray`): Declination in degrees.
                                    (e.g., "np.array([65.8922, 63.2398, ...])")
        epochStart (str): Time of epoch start.
                          (e.g., "'1 Jan 2022 00:00:00'")
        exposureEnd (`~numpy.ndarray`): Exposure end times in seconds from epochStart. If not
                                        defined, will use static exposureLength to calculate exposure
                                        end times. 
                                        (e.g., "np.array([362, 397, ...])")
        exposureLength (float): If exposure end times are None, calculate exposure end times with this 
                                static value (exposureEnd = exposureStart + exposureLength).
                                (e.g., 30)
        verbose (bool): Print progress statements?
        
    Returns:
        None 

    Raises:
        ValueError : If exposureLength and exposureEnd are None

    """                
    # Check that either exposureEnd or exposureLength are defined 
    if exposureEnd is None and exposureLength is None:
        raise ValueError("Either exposureLength or exposureEnd should be defined, or else pointings will be interpolated.")
    elif exposureLength is not None and exposureEnd is None:
        exposureEnd = exposureStart + np.ones(len(exposureStart), dtype=int) * exposureLength
         
    # Create the vector input file                  
    createVectorFile(vectorFileName, observationIds, exposureStart, exposureEnd,
                     ra, dec, epochStart, verbose=verbose)
    
    # Create interval file
    createIntervalFile(intervalFileName, exposureStart, exposureEnd, epochStart, verbose=verbose)
                         
    return

        