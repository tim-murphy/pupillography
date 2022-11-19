# Basic pupillography using the Gazepoint GP3 HD eye tracker

import matplotlib.pyplot as plt
import os
import re
import socket
import sys

HOST = '127.0.0.1'
PORT = 4242
ADDRESS = (HOST, PORT)

WINDOW_SIZE_SECONDS = 60
FRAMES_PER_SECOND = 8
FRAMES_PER_WINDOW = WINDOW_SIZE_SECONDS * FRAMES_PER_SECOND
PUPIL_MIN_SIZE_MM = 0
PUPIL_MAX_SIZE_MM = 10
INVALID_READING = -1
GAZEPOINT_REFRESH = 150

RIGHT = 0
LEFT = 1

# hackety hack hack
global keepRunning
def onClose(event):
    global keepRunning
    keepRunning = False

def printUsage():
    print("Usage:", sys.argv[0], "<outfile=None>")

if __name__ == '__main__':
    outfile = None

    if len(sys.argv) > 1:
        if sys.argv[1] == "--help":
            printUsage()
            sys.exit()
        else:
            if os.path.exists(sys.argv[1]):
                print("Outfile '", sys.argv[1], "' already exists, exiting", sep="", file=sys.stderr)
                sys.exit(1)

            print("Writing to file:", sys.argv[1])
            outfile = open(sys.argv[1], 'w')

    # connect to the Gazepoint
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(ADDRESS)
    sock.send(str.encode('<SET ID="ENABLE_SEND_TIME" STATE="1" />\r\n'))
    sock.send(str.encode('<SET ID="ENABLE_SEND_PUPILMM" STATE="1" />\r\n'))
    sock.send(str.encode('<SET ID="ENABLE_SEND_DATA" STATE="1" />\r\n'))

    # regex to extract data
    pupilRegex = re.compile(r'^<REC TIME="(.*)" LPMM="(.*)" LPMMV="(.*)" RPMM="(.*)" RPMMV="(.*)" />\r\n$')

    # plot setup
    # right and left side, each with X and Y lists
    plotData = [[[], []], [[], []]]

    # exit on close window
    plt.figure().canvas.mpl_connect('close_event', onClose)

    for i in range(FRAMES_PER_WINDOW):
        plotData[RIGHT][0].append(i)
        plotData[RIGHT][1].append(INVALID_READING)
        plotData[LEFT][0].append(i)
        plotData[LEFT][1].append(INVALID_READING)

    print("Time,Right_Diameter,Right_Valid,Left_Diameter,Left_Valid", file=outfile)

    keepRunning = True
    while keepRunning:
        rxstr = bytes.decode(sock.recv(512))

        # pull out the pupil size data
        pupilData = pupilRegex.match(rxstr)

        if pupilData is not None:
            elapsed = float(pupilData.group(1))
            lpmm = float(pupilData.group(2))
            lpmmv = bool(pupilData.group(3) == "1")
            rpmm = float(pupilData.group(4))
            rpmmv = bool(pupilData.group(5) == "1")

            if not lpmmv:
                lpmm = INVALID_READING
            if not rpmmv:
                rpmm = INVALID_READING

            print(elapsed, rpmm, (1 if rpmmv else 0), lpmm, (1 if lpmmv else 0), sep=',', file=outfile)

            # clean up the plot
            plt.cla()
            plt.axis([0, WINDOW_SIZE_SECONDS, PUPIL_MIN_SIZE_MM, PUPIL_MAX_SIZE_MM])
            xPos = int(elapsed * FRAMES_PER_SECOND % FRAMES_PER_WINDOW)

            for side, colour, label, diam in [(LEFT, "blue", "Left", lpmm), (RIGHT, "red", "Right", rpmm)]:
                plotData[side][1][xPos] = diam

                xData = [x / FRAMES_PER_SECOND for x in plotData[side][0]]
                plt.plot(xData, plotData[side][1], c=colour, label=label)

            # add the "current time" line
            plt.plot([xPos / FRAMES_PER_SECOND, xPos / FRAMES_PER_SECOND], [PUPIL_MIN_SIZE_MM, PUPIL_MAX_SIZE_MM], c="black", label="Current Time")

            plt.title("Pupillography Preview")
            plt.xlabel("Time (moving window in seconds)")
            plt.ylabel("Pupil diameter (millimetres)")
            plt.legend()
            plt.pause(1 / GAZEPOINT_REFRESH)

    sock.close()

    if outfile is not None:
        outfile.close()

    print("Goodbye")

# EOF