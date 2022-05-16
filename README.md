# NetworkTables-Logger

This program allows you to log all SmartDashboard values on a NetworkTables server to a local csv file.
This makes it easier to debug robot code and understand what is occurring, without having to go through complicated logging steps or fill up storage space on the roboRIO drive.

## Installing dependencies:
Install [pynetworktables](https://robotpy.readthedocs.io/projects/pynetworktables/en/stable/api.html) and [keyboard](https://pypi.org/project/keyboard/)

### With pip (easiest):

Windows:

`py -3 -m pip install --upgrade pynetworktables keyboard`

Mac:

`python3 -m pip install --upgrade pynetworktables keyboard`

Linux (keyboard can only be used in sudo)

`sudo python3 -m pip install --upgrade pynetworktables keyboard`

## Usage:

Run in python with your networktables server's ip/team number and output directory as arguments.

Must be run in sudo mode on linux.

Example:

`python logger.py 687 ./`

This will connect to the networktables server at `roboRIO-687-frc.local` and output the log to the current directory as `SDlog_TIMESTAMP.csv`

Note: Logs WILL NOT save if the program exits improperly, so do not call Ctrl+c.

See the help message for more info. (`python logger.py --help`)