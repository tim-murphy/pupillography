# Pupillography
Very basic pupillography using the Gazepoint GP3 HD.
To use:

1. Start up Gazepoint Control, ensure the control port is 4242 (default setting).
2. Have participant look at a fixation target and position eye tracker to have clear view of both eyes.
3. Start pupillography.py (with optional outfile if running from the command line).
4. Data collection will continue until the preview window is closed.
5. Data will be written to a CSV file in the "results" directory, to be analysed in Excel or similar.

Installation:
* pip install --upgrade pip
* pip install -r requirements.txt

Alternatively, run setup.py
