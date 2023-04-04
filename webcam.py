import cv2
from datetime import datetime
import os
import sys
import threading
from time import sleep

class PupilWebcam:
    vidcapture = None
    camera_index = 0
    frame = None
    preview = False
    preview_thread = None

    WINDOW_TITLE = "Camera Preview"
    DEFAULT_OUTDIR = os.path.join(os.path.split(__file__)[0], "images")
    IDEAL_CAMERA_RES = (1920, 1080)
    PREVIEW_WINDOW_RES = (960, 540)

    def __init__(self, cameraIndex=1):
        self.camera_index = cameraIndex
        os.makedirs(self.DEFAULT_OUTDIR, exist_ok=True)

    def __del__(self):
        if self.vidcapture is None:
            return

        self.stopPreview() # no-op if preview has stopped
        self.vidcapture.release()
        cv2.destroyAllWindows()

    def mouseClick(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONUP:
            self.takePhoto()

    def showFrame(self):
        rv, self.frame = self.vidcapture.read()

        if rv:
            cv2.imshow(self.WINDOW_TITLE, self.frame)
            cv2.waitKey(10)
        else:
            raise ValueError("Could not get camera frame: " + str(rv))

    def previewLoop(self):
        # window setup
        cv2.namedWindow(self.WINDOW_TITLE, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.WINDOW_TITLE, *self.PREVIEW_WINDOW_RES)

        # click the image to take a picture
        cv2.setMouseCallback(self.WINDOW_TITLE, self.mouseClick)

        # start the stream
        self.vidcapture = cv2.VideoCapture(self.camera_index)
        self.vidcapture.set(cv2.CAP_PROP_FRAME_WIDTH, self.IDEAL_CAMERA_RES[0])
        self.vidcapture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.IDEAL_CAMERA_RES[1])
        self.showFrame()

        while self.preview and cv2.getWindowProperty(self.WINDOW_TITLE, 0) >= 0:
            self.showFrame()

        self.preview = False

    def startPreview(self):
        print("Starting preview window...", end="", flush=True)
        if self.preview:
            return

        self.preview = True
        self.preview_thread = threading.Thread(target=self.previewLoop)
        self.preview_thread.start()
        print("done")

    def stopPreview(self):
        if self.preview_thread is None:
            return

        print("Stopping preview window...", end="", flush=True)
        self.preview = False
        self.preview_thread.join()
        self.preview_thread = None
        print("done")

    def takePhoto(self, outfile=None):
        if outfile is None:
            outfile = os.path.join(self.DEFAULT_OUTDIR,
                                   datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + ".png")

        if self.frame is not None:
            cv2.imwrite(outfile, self.frame)
            print("Image saved to:", outfile)
        else:
            print("ERROR: cannot take photo (no frame loaded)", file=sys.stderr)

if __name__ == '__main__':
    # if running this script directly, use it as a webcam
    webcam = PupilWebcam()

    webcam.startPreview()

    while webcam.preview:
        sleep(0.1)

    webcam.stopPreview()

# EOF
