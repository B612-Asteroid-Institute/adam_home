import datetime

import numpy as np
import pandas as pd

from adam.astro_utils import icrf_to_jpl_ecliptic

# Could replace these with a config class import
STK_VERSION = "11.1"
VERBOSE = True

__all__ = [
    "createVectorFile",
    "createSensorFile", 
    "createIntervalFile",
    "convertPointingsToSensorInterval", 
    "convertPointingsToVectorInterval",
    "ephemeris_file_data_to_dataframe"
]


def createVectorFile(fileName, exposureStart, exposureEnd,
                     ra, dec, epochStart,
                     verbose=VERBOSE):
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
        verbose (bool): Print progress statements?

    Returns:
        None
    """
    header = ["stk.v.{}\n".format(STK_VERSION),
              "Begin VectorData\n",
              "NumberOfVectorDataPoints {}\n".format(2 * len(exposureStart)),
              "ScenarioEpoch {}\n".format(epochStart),
              "InterpolationSamplesM1 0\n",
              "CentralBody Earth\n",
              "CoordinateAxes ICRF\n",
              "DimensionName Distance\n",
              "VectorDataTimeRaDecMag\n"]

    vectorFile = open(fileName + ".vd", "w")
    if verbose is True:
        print("Writing vector pointing file: {}".format(fileName))

    # Write header
    for line in header:
        vectorFile.write(line)

    # Write pointings
    for ti, tf, az, el in zip(exposureStart, exposureEnd, ra, dec):
        # Need to figure out magnitude
        vectorFile.write("{} {} {} 1.0\n".format(ti, az, el))
        vectorFile.write("{} {} {} 1.0\n".format(tf, az, el))

    # Write file footer
    vectorFile.write("End VectorData")
    vectorFile.close()
    if verbose is True:
        print("Done. Wrote {} pointing start and end times.".format(2 * len(exposureStart)))
        print("")

    return


def createSensorFile(fileName, exposureStart, exposureEnd,
                     azimuth, elevation, epochStart,
                     verbose=VERBOSE):
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
    header = ["stk.v.{}\n".format(STK_VERSION),
              "Begin Attitude\n",
              "NumberofAttitudePoints {}\n".format(2 * len(exposureStart)),
              "Sequence 323\n",
              "ScenarioEpoch {}\n".format(epochStart),
              "AttitudeTimeAzElAngles\n"]

    sensorFile = open(fileName + ".sp", "w")
    if verbose is True:
        print("Writing sensor pointing file: {}".format(fileName))

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
        print("Done. Wrote {} pointing start and end times.".format(2 * len(exposureStart)))
        print("")

    return


def createIntervalFile(fileName, exposureStart,
                       exposureEnd, epochStart,
                       verbose=VERBOSE):
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
    header = ["stk.v.{}\n".format(STK_VERSION),
              "BEGIN IntervalList\n\n",
              "\tScenarioEpoch {}\n\n".format(epochStart),
              "Begin Intervals\n\n"]

    intervalFile = open(fileName + ".int", "w")
    if verbose is True:
        print("Writing interval file: {}".format(fileName))

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


def convertPointingsToSensorInterval(sensorFileName, intervalFileName, exposureStart,
                                     azimuth, elevation, epochStart,
                                     exposureEnd=None,
                                     exposureLength=None,
                                     verbose=VERBOSE):
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
                                        defined, will use static exposureLength to calculate
                                        exposure end times.
                                        (e.g., "np.array([362, 397, ...])")
        exposureLength (float): If exposure end times are None, calculate exposure end times with
                                this static value (exposureEnd = exposureStart + exposureLength).
                                (e.g., 30)
        verbose (bool): Print progress statements?

    Returns:
        None

    Raises:
        ValueError : If exposureLength and exposureEnd are None

    """
    # Check that either exposureEnd or exposureLength are defined
    if exposureEnd is None and exposureLength is None:
        raise ValueError(
            "Either exposureLength or exposureEnd should be defined, "
            "or else pointings will be interpolated.")
    elif exposureLength is not None and exposureEnd is None:
        exposureEnd = exposureStart + np.ones(len(exposureStart), dtype=int) * exposureLength

    # Create the sensor pointing file
    createSensorFile(sensorFileName, exposureStart, exposureEnd,
                     azimuth, elevation, epochStart, verbose=verbose)

    # Create interval file
    createIntervalFile(intervalFileName, exposureStart, exposureEnd, epochStart, verbose=verbose)

    return


def convertPointingsToVectorInterval(vectorFileName, intervalFileName, exposureStart,
                                     ra, dec, epochStart,
                                     exposureEnd=None,
                                     exposureLength=None,
                                     verbose=VERBOSE):
    """
    Builds a sensor pointing file and interval file for a series of sensor pointings.

    Args:
        vectorFileName (str): Name to save vector file to. Extension should not be included.
                              (e.g., "VectorInput")
        intervalFileName (str): Name to save interval file to. Extension should not be included.
                              (e.g., "IntervalList")
        exposureStart (`~numpy.ndarray`): Exposure start times in seconds from epochStart.
                                         (e.g., "np.array([332, 367, ...])")
        ra (`~numpy.ndarray`): Right ascension in degrees.
                                    (e.g., "np.array([22.3454, 26.7565, ...])")
        dec (`~numpy.ndarray`): Declination in degrees.
                                    (e.g., "np.array([65.8922, 63.2398, ...])")
        epochStart (str): Time of epoch start.
                          (e.g., "'1 Jan 2022 00:00:00'")
        exposureEnd (`~numpy.ndarray`): Exposure end times in seconds from epochStart. If not
                                        defined, will use static exposureLength to calculate
                                        exposure end times.
                                        (e.g., "np.array([362, 397, ...])")
        exposureLength (float): If exposure end times are None, calculate exposure end times with
                                this static value (exposureEnd = exposureStart + exposureLength).
                                (e.g., 30)
        verbose (bool): Print progress statements?

    Returns:
        None

    Raises:
        ValueError : If exposureLength and exposureEnd are None

    """
    # Check that either exposureEnd or exposureLength are defined
    if exposureEnd is None and exposureLength is None:
        raise ValueError(
            "Either exposureLength or exposureEnd should be defined, "
            "or else pointings will be interpolated.")
    elif exposureLength is not None and exposureEnd is None:
        exposureEnd = exposureStart + np.ones(len(exposureStart), dtype=int) * exposureLength

    # Create the vector input file
    createVectorFile(vectorFileName, exposureStart, exposureEnd,
                     ra, dec, epochStart, verbose=verbose)

    # Create interval file
    createIntervalFile(intervalFileName, exposureStart, exposureEnd, epochStart, verbose=verbose)

    return


def ephemeris_file_data_to_dataframe(stk_file_text) -> pd.DataFrame:
    """Given the text of an STK Ephemeris file, read it into a Pandas DataFrame.

    Assumes the Ephemeris file has data in a sun centered ICRF frame with units of meters, seconds.

    Args:
        stk_file_text (list[str]): Contents of an STK Ephemeris file as an array of strings, one for
                                   each line

    Returns:
        dataFrame (pd.DataFrame): Data frame containing the cartesian position and velocity in the
                                  JPL Ecliptic frame in units of kilometers, seconds, and the same
                                  time scale as the Ephemeris File

     TODO:
        * Perform time frame transformations
        * Handle cases where units or frames could be different (but won't handle all cases)

    """
    ref_epoch = None
    ephem_started = False
    ephem_data = []
    current_line = 0
    for raw_line in stk_file_text:
        line = raw_line.strip().lower()
        if not ephem_started and line.startswith('ephemeristimeposvel'):
            ephem_started = True
            continue

        if line.startswith('scenarioepoch'):
            epoch_str = line[13:].strip()
            epoch_datetime = datetime.datetime.strptime(epoch_str, '%d %b %Y %H:%M:%S.%f')
            ref_epoch = np.datetime64(epoch_datetime)

        # if line.startswith('numberofephemerispoints'):
        #     point_count = int(line[23:])
        #     ephem_data = np.empty(point_count, dtype=object)

        if line.startswith('centralbody'):
            body = line[11:].strip()
            if not body == 'sun':
                raise ValueError('Central body must be the Sun')

        if line.startswith('CoordinateSystem'):
            frame = line[16:].strip()
            if not frame == 'icrf':
                raise ValueError('Coordinate frame must be ICRF')

        if not ephem_started:
            continue

        if len(line) == 0:
            continue

        if line.startswith('end'):
            break

        state_str = raw_line.split()
        epoch_sec = float(state_str[0])
        epoch_dt = np.timedelta64(int(epoch_sec * 1000), 'ms')
        epoch = ref_epoch + epoch_dt
        x = float(state_str[1]) / 1000.0
        y = float(state_str[2]) / 1000.0
        z = float(state_str[3]) / 1000.0
        vx = float(state_str[4]) / 1000.0
        vy = float(state_str[5]) / 1000.0
        vz = float(state_str[6]) / 1000.0
        ecliptic_state = icrf_to_jpl_ecliptic(x, y, z, vx, vy, vz)
        state = [epoch] + ecliptic_state
        ephem_data.append(np.array(state))
        current_line += 1

    return pd.DataFrame(data=ephem_data, columns=['Epoch', 'X', 'Y', 'Z', 'Vx', 'Vy', 'Vz'])
