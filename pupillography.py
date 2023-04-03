# Basic pupillography using the Gazepoint GP3 HD eye tracker

import ctypes
from datetime import datetime
import matplotlib.pyplot as plt
import os
import re
import socket
import sys

from webcam import PupilWebcam

HOST = '127.0.0.1'
PORT = 4242
ADDRESS = (HOST, PORT)

WINDOW_SIZE_SECONDS = 30
FRAMES_PER_SECOND = 8
FRAMES_PER_WINDOW = WINDOW_SIZE_SECONDS * FRAMES_PER_SECOND
PUPIL_MIN_SIZE_MM = 0
PUPIL_MAX_SIZE_MM = 10
INVALID_READING = 0
GAZEPOINT_REFRESH = 60

RIGHT = 0
LEFT = 1
DELTA = 2

# hackety hack hack
global keepRunning
def onClose(event):
    global keepRunning
    keepRunning = False

def pressEnter(msg="Press enter to continue..."):
    input(msg)

def printUsage():
    print("Usage:", sys.argv[0], "--help | <outfile_csv=results/[timestamp]>")

if __name__ == '__main__':
    ### command line arguments ###

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

    ### set up bits we will use in the data processing ###

    # regex to extract data
    dataRegex = re.compile(r'^<REC TIME="(.*)" LPOGX="(.*)" LPOGY="(.*)" LPOGV="(.*)" RPOGX="(.*)" RPOGY="(.*)" RPOGV="(.*)" LPMM="(.*)" LPMMV="(.*)" RPMM="(.*)" RPMMV="(.*)" />\r\n$')

    # each x-coord has right, left, and delta values
    # accessed as plotPupilData[y-set]
    # similar for X and Y coords, but no delta
    xData = [x / FRAMES_PER_SECOND for x in range(FRAMES_PER_WINDOW)]
    plotPupilData = [[], [], []]
    plotXData = [[], []]
    plotYData = [[], []]
    defaultYData = [INVALID_READING] * FRAMES_PER_WINDOW
    for j in (RIGHT, LEFT, DELTA):
        plotPupilData[j] = defaultYData.copy()

    for j in (RIGHT, LEFT):
        plotXData[j] = defaultYData.copy()
        plotYData[j] = defaultYData.copy()

    # create three plots: pupils, x-pos, and y-pos
    fig, axs = plt.subplots(3)

    # plot config: exit on close window
    fig.canvas.mpl_connect('close_event', onClose)
    fig.canvas.manager.set_window_title("Pupil and X/Y Pos (close window to exit)")

    with open(outpath, 'w') as outfile:
        print("Writing to file:", outpath)

        # connect to the Gazepoint
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.connect(ADDRESS)
            except:
                print("ERROR: could not connect to Gazepoint (addr: ", HOST, ":", PORT, ") - is Gazepoint Control running?", sep="")
                pressEnter("Press enter to close the program")
                sys.exit(1)

            # start the webcam preview
            webcam = PupilWebcam()
            webcam.startPreview()

            ctypes.windll.user32.MessageBoxW(0, "Move the webcam preview window and press OK", "Window Position", 0)

            sock.send(str.encode('<SET ID="ENABLE_SEND_TIME" STATE="1" />\r\n'))
            sock.send(str.encode('<SET ID="ENABLE_SEND_PUPILMM" STATE="1" />\r\n'))
            sock.send(str.encode('<SET ID="ENABLE_SEND_POG_LEFT" STATE="1" />\r\n'))
            sock.send(str.encode('<SET ID="ENABLE_SEND_POG_RIGHT" STATE="1" />\r\n'))
            sock.send(str.encode('<SET ID="ENABLE_SEND_DATA" STATE="1" />\r\n'))

            print("SystemTime,ElapsedTime,Right Pupil,Left Pupil,Difference,Right Pupil Valid,Left Pupil Valid,Right X,Left X,Right Y,Left Y,Left Y,Right Pos Valid,Left Pos Valid", file=outfile)

            keepRunning = True
            firstDataTime = None

            # FIXME this is confusing
            # line[0] has three plots: left, right, dela
            # line[1] and line[2] only have left and right
            line = [[[], [], []], [[], []], [[], []]] # this will store the plot line for live updating
            currentLine = [[], [], []] # the vertical line showing the current time
            while keepRunning:
                rxstr = bytes.decode(sock.recv(512))

                # pull out the pupil size data
                pupilData = dataRegex.match(rxstr)

                if pupilData is not None:
                    # we subtract 0.5 from position data to set 0,0 as the middle of the screen
                    systime = datetime.now().strftime('%Y-%m-%d_%H:%M:%S.%f')
                    elapsed = float(pupilData.group(1))
                    lpogx = float(pupilData.group(2)) - 0.5
                    lpogy = (float(pupilData.group(3)) - 0.5) * -1
                    lpogv = bool(pupilData.group(4) == "1")
                    rpogx = float(pupilData.group(5)) - 0.5
                    rpogy = (float(pupilData.group(6)) - 0.5) * -1
                    rpogv = bool(pupilData.group(7) == "1")
                    lpmm = float(pupilData.group(8))
                    lpmmv = bool(pupilData.group(9) == "1")
                    rpmm = float(pupilData.group(10))
                    rpmmv = bool(pupilData.group(11) == "1")
                    delta = (0 if not (lpmmv and rpmmv) else abs(lpmm - rpmm))

                    if not lpmmv:
                        lpmm = INVALID_READING
                    if not rpmmv:
                        rpmm = INVALID_READING

                    # elapsed timestamp start at zero when Gazepoint Control is started, which is before we start collecting
                    # data. Adjust it so the graph starts at time zero.
                    if firstDataTime is None:
                        firstDataTime = elapsed
                    elapsed -= firstDataTime

                    print(systime, elapsed, rpmm, lpmm, delta, (1 if rpmmv else 0), (1 if lpmmv else 0),
                          rpogx, lpogx, rpogy, lpogy, (1 if rpogv else 0), (1 if lpogv else 0),
                          sep=',', file=outfile)

                    xPos = int(elapsed * FRAMES_PER_SECOND % FRAMES_PER_WINDOW)

                    # pupil data
                    for side, colour, label, diam in [(LEFT, "blue", "Left", lpmm),
                                                      (RIGHT, "red", "Right", rpmm),
                                                      (DELTA, "green", "Difference", delta)]:
                        plotPupilData[side][xPos] = diam

                        if line[0][side] == []:
                            axs[0].set_xlim([0, WINDOW_SIZE_SECONDS])
                            axs[0].set_ylim([PUPIL_MIN_SIZE_MM, PUPIL_MAX_SIZE_MM])
                            axs[0].set_title("Pupil size and X/Y position")
                            axs[0].set(ylabel="Pupil (mm)")
                            line[0][side], = axs[0].plot(xData, plotPupilData[side], c=colour, label=label)
                        else:
                            line[0][side].set_ydata(plotPupilData[side])


                    # X/Y pos data
                    for side, colour, label, x, y in [(LEFT, "blue", "Left", lpogx, lpogy),
                                                      (RIGHT, "red", "Right", rpogx, rpogy)]:
                        plotXData[side][xPos] = x
                        plotYData[side][xPos] = y

                        for i, dat in ((1, plotXData[side]), (2, plotYData[side])):
                            if line[i][side] == []:
                                line[i][side], = axs[i].plot(xData, dat, c=colour, label=label)
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
                    else:
                        for a in range(3):
                            currentLine[a].set_xdata(current_xdata)
                            currentLine[a].set_ydata(current_ydata)

                    plt.pause(1 / GAZEPOINT_REFRESH)

                # end if pupilData is not None
            # end while keepRunning

            webcam.stopPreview()
        # end with ... as sock
    # end with ... as outfile

    pressEnter("Finished! Press enter to close the program")
    print("Goodbye")

# EOF
