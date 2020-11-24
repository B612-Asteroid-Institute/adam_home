"""
    stkoutput.py
"""

import numpy as np
import pandas as pd


class AstrogatorOutput:
    """Fetches output from an STK/Astrogator MCS.
    
    This class is used to create a list of desired outputs from an 
    STK Astrogator Mission Control Sequence (MCS).
    This is specifically designed to support multiple runs, such as
    in a parametric study.
    
    This class is also used to retrieve the list of outputs.
    When fetching the data (using update(), the values are 
    returned in rows. The calling code also specifies an index number
    which represents the column index. The output is a table, with the
    desired outputs in each row. Each column contains the values for 
    each different run. Conceptually, it returns a table of the form:
    
              run_1   run_2  run_3 run_4 ...
    output_1   ###     ###    ###   ###  ...
    output_2   ###     ###    ###   ###  ...
    output_3   ###     ###    ###   ###  ...
    ...
    
    NOTE: Internally the class stores the runs as rows, and the
    desired output values as columns. But the supported workflow
    needs the runs as columns, the output is transposed whenever
    requested.
    
    This class can save the resulting values to a csv file, and 
    load from it using pandas.
    
    This class can create a pandas dataframe.
    
    TODO:
        * The current design is to add all the events, getting the
          rownames, then the update, and then get the dataout. 
          Need to decide what to do if these are done out of
          order, or iterated between.

    """

    def __init__(self):
        """Initialize attributes
        
        """
        # events is an array of the desired outputs
        self.events = []

        # results contain the data after update is called
        # NOTE: The rows internally are the runs, and the columns
        #       are the data values
        self.results = None

        # rowNames are the labels for each row
        self._rowNames = None

        # _df is the pandas dataframe (semi-private)
        self._df = None

    def add(self, eventName, quantity, unit):
        """Add a new desired output 
        
        This function adds a desired output to the list of 
        outputs that will be generated when this object is updated.
        It uses the MCS segment name, the desired Astroagtor 
        CalcObject with which to calulate the value, and the 
        desired unit.
        
        Args:
            eventName (str): The MCS segment name 
                             (e.g., "Initial_State")
            quantity (str): The desired CalcObject 
                           (e.g., "Altitude")
            unit (str): The desired unit in STK format 
                        (e.g., "km")
        
        Returns:
            None
            
         TODO: 
            * Catch erros
            * Decide what to do if add is called after update()

        """
        self.events.append([eventName, quantity, unit])

    def update(self, gatorDefn, index):
        """Fetch & store the desired data from STK/Astrogator
        
        This method fetches the desired output values from the
        STK/AStrogator Satellite Object.
        
        Args:
            gatorDefn (STK COM object): The Astrogator definition of
                                        the STK Satellite Object.
            index: The run number, designed to be used in a loop that
                   increments each time.
                   
        TODO: 
            * Catch error if index values called out of sequence (Until
              the next TODO is implemented)
            * Add remove need for an index, and so just always append
              the new run
            
        """
        tempArray = np.zeros([1, len(self.events)])
        for i, eventRow in enumerate(self.events):
            seg = gatorDefn.GetSegmentByName(eventRow[0])
            if seg.GetResultValue(eventRow[1]).Class.value == 'DATE':
                # The following generates an error becasue the np.array is of type float.
                if eventRow[2] in ['EpDay', 'EpMin', 'EpSec', 'EpYr', 'JDate', 'JED', 'ModJDate',
                                   'EarthEpTU', 'GPSZ', 'JDateOff', 'SunEpTU']:
                    tempArray[0, i] = float(
                        seg.GetResultValue(eventRow[1]).Format(eventRow[2]).value)
                else:
                    print(
                        'Format "{}" not supported (must be representable as a float). Substituting with "JDate".'.format(
                            eventRow[2]))
                    tempArray[0, i] = float(seg.GetResultValue(eventRow[1]).Format('JDate').value)
            else:
                tempArray[0, i] = seg.GetResultValue(eventRow[1]).Getin(eventRow[2]).value
        # print(tempArray.T)
        print('1st Item: {:25}  Shape: {}'.format(tempArray[0, 0], tempArray.T.shape))
        if self.results is None:
            self.results = tempArray.T
        else:
            self.results = np.concatenate(
                (self.results, tempArray.T), axis=1)

    def saveCSV(self, path):
        """Save the output values to a csv file
        
        This uses the pandas dataframe funcationality to save the data.
        A csv file is used to support the workflow that a user may
        want to import into a spreadsheet.
        
        Note: The data internally is not the same as the csv; Each
        desired output is a row in the csv, and each run is a column.
        Since this is the opposite of internal storage, the transpose
        function is used.
        
        Args:
            path (str): The filepath to the output csv file,
                        including the suffix, ".csv"
                        
        Returns:
            None:
            
         TODO: 
            * Catch erros
            
        """
        self.df.transpose().to_csv(path)

    @classmethod
    def loadCSV(cls, path):
        """ Load the data from a csv file
        
        This method loads data into the object from a csv file.
        It is inteneded to load a csv that was created with this
        same object. 
        
        Args:
            path (str): The filepath to the output csv file,
                        including the suffix, ".csv"
                        
        Returns:
            The class

        TODO: 
            * Catch erros
        
        """
        c = cls()
        c._df = pd.read_csv(path, index_col=0)
        c.results = c._df.as_matrix()
        c._rowNames = c._df.index.values.tolist()

        # Split the event name into its three components, which were 
        # used to add the event in the first place. The three
        # components that make up the event name are:
        #  1) MCS Segment Name
        #  2) Desired CalcObject quantity
        #  3) Units 
        c.events = list(c.df.index.map(lambda x: x.replace(')', '')).map(
            lambda x: x.replace('(', '')).str.split(" ").values)
        return c

    @property
    def rowNames(self):
        """Return the names of the row as a list
        
        This creates the row name from the event name, the desired
        quantity, and the units. Put the untis in parenthesis
        which is common for human-readable tables.
        
        Args:
            None
            
        Returns:
            List of row names
            
        TODO:
            * Make this work even if add() has been called since the
              last time rowNames() was called.
              
        """
        if self._rowNames is None:
            self._rowNames = []
            for row in self.events:
                # Create the row names on the fly
                self._rowNames.append('{} {} ({})'.format(row[0], row[1], row[2]))
        return self._rowNames

    @property
    def df(self):
        """Return a pandas dataframe of the data
        
        Note: The data internally is not the same as the returned
        dataframe; Eachdesired output is a row in the dataframe, and 
        each run is a column. Since this is the opposite of internal 
        storage, the transpose function is used.
                
        Args:
            None
            
        Returns:
            Panda data frame
        """
        if self._df is None:
            self._df = pd.DataFrame(self.results.transpose(), columns=self.rowNames)
        return self._df
