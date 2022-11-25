# Basic pupillography using the Gazepoint GP3 HD eye tracker

from datetime import datetime
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
INVALID_READING = 0
GAZEPOINT_REFRESH = 150

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
    pupilRegex = re.compile(r'^<REC TIME="(.*)" LPMM="(.*)" LPMMV="(.*)" RPMM="(.*)" RPMMV="(.*)" />\r\n$')

    # each x-coord has right, left, and delta values
    # accessed as plotYData[y-set]
    xData = [x / FRAMES_PER_SECOND for x in range(FRAMES_PER_WINDOW)]
    plotYData = [[], [], []]
    defaultYData = [INVALID_READING] * FRAMES_PER_WINDOW
    for j in (RIGHT, LEFT, DELTA):
        plotYData[j] = defaultYData.copy()

    # plot config: exit on close window
    plt.figure().canvas.mpl_connect('close_event', onClose)

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

            sock.send(str.encode('<SET ID="ENABLE_SEND_TIME" STATE="1" />\r\n'))
            sock.send(str.encode('<SET ID="ENABLE_SEND_PUPILMM" STATE="1" />\r\n'))
            sock.send(str.encode('<SET ID="ENABLE_SEND_DATA" STATE="1" />\r\n'))

            print("Time,Right Pupil,Left Pupil,Difference,Right Valid,Left Valid", file=outfile)

            keepRunning = True
            firstDataTime = None
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

                    print(elapsed, rpmm, lpmm, delta, (1 if rpmmv else 0), (1 if lpmmv else 0), sep=',', file=outfile)

                    # clean up the plot
                    plt.cla()
                    plt.axis([0, WINDOW_SIZE_SECONDS, PUPIL_MIN_SIZE_MM, PUPIL_MAX_SIZE_MM])
                    xPos = int(elapsed * FRAMES_PER_SECOND % FRAMES_PER_WINDOW)

                    for side, colour, label, diam in [(LEFT, "blue", "Left", lpmm),
                                                      (RIGHT, "red", "Right", rpmm),
                                                      (DELTA, "green", "Difference", delta)]:
                        plotYData[side][xPos] = diam
                        plt.plot(xData, plotYData[side], c=colour, label=label)

                    # add the "current time" line
                    plt.plot([xPos / FRAMES_PER_SECOND, xPos / FRAMES_PER_SECOND], [PUPIL_MIN_SIZE_MM, PUPIL_MAX_SIZE_MM], c="black", label="Current Time")

                    plt.title("Pupillography Preview")
                    plt.xlabel("Time (moving window in seconds)")
                    plt.ylabel("Pupil diameter (millimetres)")
                    plt.legend()
                    plt.pause(1 / GAZEPOINT_REFRESH)

                # end if pupilData is not None
            # end while keepRunning
        # end with ... as sock
    # end with ... as outfile

    pressEnter("Finished! Press enter to close the program")
    print("Goodbye")

# EOF
