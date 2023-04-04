# class for getting eye tracking data from a Gazepoint GP3 HD

from datetime import datetime
import re
import socket
from time import sleep

class EyeData:
    systime = None
    elapsed = None
    lpogx = None
    lpogy = None
    lpogv = None
    rpogx = None
    rpogy = None
    rpogv = None
    lpmm = None
    lpmmv = None
    rpmm = None
    rpmmv = None
    delta = None

    HOST = '127.0.0.1'
    PORT = 4242
    ADDRESS = (HOST, PORT)

    def __init__(self, outpath, refresh):
        self.keepRunning = False
        self.haveData = False
        self.outpath = outpath
        self.refresh = refresh # Gazepoint refresh rate

    def dataAvailable(self):
        return self.haveData

    def run(self):
        self.keepRunning = True

        # regex to extract data
        dataRegex = re.compile(r'^<REC TIME="(.*)" LPOGX="(.*)" LPOGY="(.*)" LPOGV="(.*)" RPOGX="(.*)" RPOGY="(.*)" RPOGV="(.*)" LPMM="(.*)" LPMMV="(.*)" RPMM="(.*)" RPMMV="(.*)" />\r\n$')

        with open(self.outpath, 'w') as outfile:
            print("Writing to file:", self.outpath)

            # connect to the Gazepoint
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                try:
                    sock.connect(self.ADDRESS)
                except:
                    print("ERROR: could not connect to Gazepoint (addr: ", self.HOST, ":", self.PORT, ") - is Gazepoint Control running?", sep="")
                    pressEnter("Press enter to close the program")
                    sys.exit(1)

                sock.send(str.encode('<SET ID="ENABLE_SEND_TIME" STATE="1" />\r\n'))
                sock.send(str.encode('<SET ID="ENABLE_SEND_PUPILMM" STATE="1" />\r\n'))
                sock.send(str.encode('<SET ID="ENABLE_SEND_POG_LEFT" STATE="1" />\r\n'))
                sock.send(str.encode('<SET ID="ENABLE_SEND_POG_RIGHT" STATE="1" />\r\n'))
                sock.send(str.encode('<SET ID="ENABLE_SEND_DATA" STATE="1" />\r\n'))

                print("SystemTime,ElapsedTime,Right Pupil,Left Pupil,Difference,Right Pupil Valid,Left Pupil Valid,Right X,Left X,Right Y,Left Y,Right Pos Valid,Left Pos Valid", file=outfile)

                firstDataTime = None
                while self.keepRunning:
                    rxstr = bytes.decode(sock.recv(512))

                    # pull out the pupil size data
                    pupilData = dataRegex.match(rxstr)

                    if pupilData is None:
                        continue

                    # we subtract 0.5 from position data to set 0,0 as the middle of the screen
                    self.systime = datetime.now().strftime('%Y-%m-%d_%H:%M:%S.%f')
                    self.elapsed = float(pupilData.group(1))
                    self.lpogx = float(pupilData.group(2)) - 0.5
                    self.lpogy = (float(pupilData.group(3)) - 0.5) * -1
                    self.lpogv = bool(pupilData.group(4) == "1")
                    self.rpogx = float(pupilData.group(5)) - 0.5
                    self.rpogy = (float(pupilData.group(6)) - 0.5) * -1
                    self.rpogv = bool(pupilData.group(7) == "1")
                    self.lpmm = float(pupilData.group(8))
                    self.lpmmv = bool(pupilData.group(9) == "1")
                    self.rpmm = float(pupilData.group(10))
                    self.rpmmv = bool(pupilData.group(11) == "1")
                    self.delta = (0 if not (self.lpmmv and self.rpmmv) else abs(self.lpmm - self.rpmm))

                    if not self.lpmmv:
                        self.lpmm = INVALID_READING
                    if not self.rpmmv:
                        self.rpmm = INVALID_READING

                    # elapsed timestamp start at zero when Gazepoint Control is started, which is before we start collecting
                    # data. Adjust it so the graph starts at time zero.
                    if firstDataTime is None:
                        firstDataTime = self.elapsed
                    self.elapsed -= firstDataTime

                    # flag that we have data so others can read it
                    self.haveData = True

                    print(self.systime, self.elapsed, self.rpmm, self.lpmm, self.delta, (1 if self.rpmmv else 0), (1 if self.lpmmv else 0),
                          self.rpogx, self.lpogx, self.rpogy, self.lpogy, (1 if self.rpogv else 0), (1 if self.lpogv else 0),
                          sep=',', file=outfile)

                    sleep(1.0 / self.refresh)
                # end while keepRunning
            # end with socket
        # end open

    def stop(self):
        self.keepRunning = False

# EOF
