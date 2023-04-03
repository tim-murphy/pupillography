# Basic pupillography using the Gazepoint GP3 HD eye tracker

import ctypes
import cv2
from datetime import datetime
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import os
from pynput import keyboard
import sys
import threading
from time import sleep

from eyedata import EyeData
from fixation import FixationTargets
from webcam import PupilWebcam

WINDOW_SIZE_SECONDS = 30
FRAMES_PER_SECOND = 8
FRAMES_PER_WINDOW = WINDOW_SIZE_SECONDS * FRAMES_PER_SECOND
PUPIL_MIN_SIZE_MM = 0
PUPIL_MAX_SIZE_MM = 10
INVALID_READING = 0
GAZEPOINT_REFRESH = 60

FIXATION_TARGETS = os.path.join(os.path.split(__file__)[0], "gaze_targets", "bear")
IMAGE_OUTDIR = PupilWebcam.DEFAULT_OUTDIR

RIGHT = 0
LEFT = 1
DELTA = 2

def pressEnter(msg="Press enter to continue..."):
    input(msg)

class Pupillography:
    def __init__(self, outpath):
        self.keepRunning = False
        self.targets = None
        self.webcam = None
        self.eyedata = EyeData(outpath, GAZEPOINT_REFRESH)

        # each x-coord has right, left, and delta values
        # accessed as plotPupilData[y-set]
        # similar for X and Y coords, but no delta
        self.xData = [x / FRAMES_PER_SECOND for x in range(FRAMES_PER_WINDOW)]
        self.plotPupilData = [[], [], []]
        self.plotXData = [[], []]
        self.plotYData = [[], []]
        defaultYData = [INVALID_READING] * FRAMES_PER_WINDOW
        for j in (RIGHT, LEFT, DELTA):
            self.plotPupilData[j] = defaultYData.copy()

        for j in (RIGHT, LEFT):
            self.plotXData[j] = defaultYData.copy()
            self.plotYData[j] = defaultYData.copy()

    def onClose(self, event):
        self.stop()

    def detectKeys(self, key):
        image_outpath = os.path.join(
            IMAGE_OUTDIR,
            datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + "_" + self.targets.currentImageName())

        if key.name == 'space':
            self.webcam.takePhoto(image_outpath)
        elif key.name == 'left':
            self.webcam.takePhoto(image_outpath)
            self.targets.showPrevTarget()
        elif key.name == 'right':
            self.webcam.takePhoto(image_outpath)
            self.targets.showNextTarget()
        elif key.name == 'esc':
            self.stop()

    def liveGraph(self):
        # wait until some data has been collected
        while not self.eyedata.dataAvailable():
            sleep(0.1)

        # create three plots: pupils, x-pos, and y-pos
        fig, axs = plt.subplots(3)

        # plot config: exit on close window
        fig.canvas.mpl_connect('close_event', self.onClose)
        fig.canvas.manager.set_window_title("Pupil and X/Y Pos (close window to exit)")

        self.keepRunning = True

        # FIXME this is confusing
        # line[0] has three plots: left, right, dela
        # line[1] and line[2] only have left and right
        line = [[[], [], []], [[], []], [[], []]] # this will store the plot line for live updating
        currentLine = [[], [], []] # the vertical line showing the current time
        while self.keepRunning:
            xPos = int(self.eyedata.elapsed * FRAMES_PER_SECOND % FRAMES_PER_WINDOW)

            # pupil data
            for side, colour, label, diam in [(LEFT, "blue", "Left", self.eyedata.lpmm),
                                              (RIGHT, "red", "Right", self.eyedata.rpmm),
                                              (DELTA, "green", "Difference", self.eyedata.delta)]:
                self.plotPupilData[side][xPos] = diam

                if line[0][side] == []:
                    axs[0].set_xlim([0, WINDOW_SIZE_SECONDS])
                    axs[0].set_ylim([PUPIL_MIN_SIZE_MM, PUPIL_MAX_SIZE_MM])
                    axs[0].set_title("Pupil size and X/Y position")
                    axs[0].set(ylabel="Pupil (mm)")
                    line[0][side], = axs[0].plot(self.xData, self.plotPupilData[side], c=colour, label=label)
                else:
                    line[0][side].set_ydata(self.plotPupilData[side])

                # X/Y pos data
                for side, colour, label, x, y in [(LEFT, "blue", "Left", self.eyedata.lpogx, self.eyedata.lpogy),
                                                  (RIGHT, "red", "Right", self.eyedata.rpogx, self.eyedata.rpogy)]:
                    self.plotXData[side][xPos] = x
                    self.plotYData[side][xPos] = y

                    for i, dat in ((1, self.plotXData[side]), (2, self.plotYData[side])):
                        if line[i][side] == []:
                            line[i][side], = axs[i].plot(self.xData, dat, c=colour, label=label)
                        else:
                            line[i][side].set_ydata(dat)

                # add the "current time" line
                current_xdata = [xPos / FRAMES_PER_SECOND, xPos / FRAMES_PER_SECOND]
                current_ydata = [-0.5, PUPIL_MAX_SIZE_MM]
                if currentLine[0] == []:
                    for a in range(3):
                        currentLine[a], = axs[a].plot(current_xdata, current_ydata, c="black", label="Current Time")

                    # we only get here on the first run, so add in the other labels
                    axs[1].set(ylabel="X-Pos")
                    axs[2].set(xlabel="Time (moving window in seconds)", ylabel="Y-Pos")

                    for a in (1, 2):
                        axs[a].sharex(axs[0])
                        axs[a].set_ylim([-0.5, 0.5])

                    for a in range(3):
                        axs[a].legend()

                    fig.show()
                else:
                    for a in range(3):
                        currentLine[a].set_xdata(current_xdata)
                        currentLine[a].set_ydata(current_ydata)

                fig.canvas.draw_idle()
                fig.canvas.flush_events() # FIXME this is very slow

                # self.detectKeys()

            # end if pupilData is not None
        # end while keepRunning

    def run(self):
        # start the webcam preview
        self.webcam = PupilWebcam()
        self.webcam.startPreview()
        ctypes.windll.user32.MessageBoxW(0, "Move the webcam preview window and press OK", "Window Position", 0)

        # show fixation targets
        self.targets = FixationTargets(FIXATION_TARGETS)

        # pull the data
        data_thread = threading.Thread(target=self.eyedata.run)
        data_thread.start()

        # listen for keypresses
        listener = keyboard.Listener(on_press=self.detectKeys)
        listener.start()

        # and show the live graph
        self.liveGraph()

        # all done! cleanup time
        listener.stop()
        listener.join()
        self.eyedata.stop()
        data_thread.join()
        self.webcam.stopPreview()
        pressEnter("Finished! Press enter to close the program")
        print("Goodbye")

    def stop(self):
        self.keepRunning = False
        self.eyedata.stop()

if __name__ == '__main__':
    def printUsage():
        print("Usage:", sys.argv[0], "--help | <outfile_csv=results/[timestamp]>")

    ### command line arguments ###

    if not os.path.isdir(FIXATION_TARGETS):
        print("ERROR: fixation targets missing, should be at:", FIXATION_TARGETS, file=sys.stderr)
        sys.exit(1)

    # default output file name
    outpath = os.path.join(os.path.join(os.path.split(sys.argv[0])[0], "results"),
                           datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '.csv')

    if len(sys.argv) > 1:
        if sys.argv[1] == "--help":
            printUsage()
            pressEnter("Press enter to close the program")
            sys.exit(1)
        else:
            if os.path.exists(sys.argv[1]):
                print("Outfile '", sys.argv[1], "' already exists, exiting", sep="", file=sys.stderr)
                pressEnter("Press enter to close the program")
                sys.exit(1)

            outpath = sys.argv[1]

    # make sure the output directory exists
    outdir = os.path.split(outpath)[0]
    if outdir != "":
        try:
            os.makedirs(outdir, exist_ok=True)
        except Exception as e:
            print("ERROR:", e)
            pressEnter("Press enter to close the program")
            sys.exit(1)

    pup = Pupillography(outpath)
    pup.run()

# EOF
