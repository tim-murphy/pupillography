# Pupillography
A very basic pupillography using the Gazepoint GP3 HD running on Python 3.
The software works best with two monitors: one for the participant and one for the examiner.
This has been tested on Windows 10 but should work on any Windows, Mac, or Linux setup.

**This tool is for research purposes only and is not intended to be used as a medical device.
The software is provided as-is without warranty and makes no guarantee regarding the accuracy of the data collected.**

This software can do two things without having to change any settings:
1. Measure pupil sizes in different light levels to detect pupil defects.
2. Record pupil sizes and gaze positions during ocular motilities, taking photos in each gaze to help detect oculomotor defects.

## Quick start
0. Install required packages (see **Installation** below).
1. Start up Gazepoint Control and ensure the control port is 4242 (default setting). Alternatively, use fake data (see **Testing** below).
2. Have the participant look at the monitor and position the eye tracker at approximately 65cm with clear view of both eyes.
3. Run the calibration routine in Gazepoint Control. Use a 9-point calibration for motilities or a 1-point calibration for pupil size testing.
4. Start pupillography.py (with optional outfile if running from the command line). Move the camera preview window to the examiner screen, and the target window to the participant screen, and press **Enter**.
5. Binocular gaze position and pupil size data will be collected until the preview window is closed.
6. Data will be written to a CSV file in the "results" directory, to be analysed in Excel or similar.

## How to use the software
When the program starts, a camera preview window (for the examiner) and target display window (for the participant) will be created.
Move the windows to the appropriate screens and click OK on the popup prompts to start data collection. Note: sometimes the first popup is hidden by the camera window so you might need to move this around.
A target will be shown in the middle of the screen.
By default this is will use the images in the `gaze_targets/bear` directory - change the `FIXATION_TARGETS` variable in `pupillography.py` if you want other targets.
Data will be saved to a file in the **results** directory, named with the timestamp of when the program started, in CSV format.
This can then be analysed in Excel or other software as required.
Once finished, press **Escape** or close the graphing window to stop the program.
The target will stay on the screen until you press **Enter** in the command prompt window.

### Pupil size testing
Have the participant look at the target as you change the lighting conditions.
Using a pen torch can cause the eye tracker camera wash out so this works best if you change the room lighting.
All pupil size recordings will automatically be saved to the output file.

### Ocular motilities testing
Use the left and right arrows to move to the next and previous target locations.
A photo will be taken immediately before the target moves to capture the eye positions in that gaze.
Click on the camera preview window to take additional photos as necessary.
Captured images will be stored in the **images** directory, named with the timestamp of when the image was taken.

## Installation
* pip install --upgrade pip
* pip install -r requirements.txt

Alternatively, run setup.py

## Testing
The `dummy_gp3.py` program can be used to emulate a Gazepoint where none is available.
Simply run this program instead of Gazepoint Control to get random pupil size data.

## Future work
1. Allow the directory of fixation targets to be changed in the UI.
