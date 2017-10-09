# Client APIs for the Cloud
Authors: @HoodedCrow, @samotiwala
## What's been done
We've re-organized and revamped the client-side API scripts to be modular so that it can be easily imported. An example script can be found in this directory (entitled test.py). A simple "from adam import Batch" will allow the user to have access to the batch propagator API scripts. With a given state vector and some defined time parameters (see test.py), a job can be submitted for propagation on the cloud. Shims and unit tests have also been added.
## What to do next
There is a lot more work to be done, including:
* Completing the covariance API wrapper
* Removing some of the hard-coded values for user inputs
* Completing unit tests
* Much more
