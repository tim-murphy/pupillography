# Pupillography
Very basic pupillography using the Gazepoint GP3 HD.
To use:

0. Install required packages (see below)
1. Start up Gazepoint Control, ensure the control port is 4242 (default setting).
2. Have participant look at a fixation target and position eye tracker to have clear view of both eyes.
3. Start pupillography.py (with optional outfile if running from the command line).
4. Data collection will continue until the preview window is closed.
5. Data will be written to a CSV file in the "results" directory, to be analysed in Excel or similar.

Installation:
* pip install --upgrade pip
* pip install -r requirements.txt

Alternatively, run setup.py

Testing:
The `dummy_gp3.py` program can be used to emulate a Gazepoint where none is available.
Simply run this program instead of Gazepoint Control to get random pupil size data.
