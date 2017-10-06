Mike, Joachim, and John worked on this.
We converted a workflow used on Windows with STK being controlled by MS-Excel.
This now controls STK from a Juptyer notebook.
The STK Scenario is in the Test.zip file
This controls STK in a loop, incrementing the delta-V, and getting altitude and orbit period out.
It's stroed in a STKResults object.
We output the results to a csv file, and we can read the csv file back in, so we don't have to re-run the STK loop.
We can also read in the csv, which has the desired outputs, and re-run the run.
