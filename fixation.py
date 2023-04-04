# show a series of fixation targets

import ctypes
import cv2
import glob
import os
import sys

class FixationTargets:
    # path to targets
    targets = []
    target_index = -1

    WINDOW_TITLE = "Fixation Targets"

    def __init__(self, targetsdir):
        # get our targets
        self.targets = glob.glob(os.path.join(targetsdir, "*.png"))

        if len(self.targets) < 1:
            raise ValueError("No targets found in directory: " + targetsdir)

        # window setup
        cv2.namedWindow(self.WINDOW_TITLE, cv2.WINDOW_NORMAL)
        ctypes.windll.user32.MessageBoxW(0, "Move the fixation window to the correct monitor and press OK", "Window Position", 0)
        cv2.setWindowProperty(self.WINDOW_TITLE, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        # and start!
        self.showNextTarget()

    def __del__(self):
        cv2.destroyAllWindows()

    def showImage(self):
        print("Showing target:", self.currentImageName())
        img = cv2.imread(self.targets[self.target_index])
        cv2.imshow(self.WINDOW_TITLE, img)
        cv2.waitKey(10)

    def showNextTarget(self):
        if (self.target_index + 1) >= len(self.targets):
            print("All targets shown.")
            return False

        self.target_index += 1
        self.showImage()

    def showPrevTarget(self):
        if (self.target_index - 1) < 0:
            print("First target currently shown.")
            return False

        self.target_index -= 1
        self.showImage()

    def currentImageName(self):
        return os.path.split(self.targets[self.target_index])[1]

if __name__ == '__main__':
    def printUsage():
        print("Usage:", os.path.split(__file__)[1], "<targets_dir>")
        print("      ", "all *.png files in the directory will be shown, in sorted order")

    if len(sys.argv) < 2:
        printUsage()
        sys.exit(1)

    # targets needs to be a directory that exists
    targetsdir = sys.argv[1]
    if not os.path.isdir(targetsdir):
        print("ERROR: targets_dir is not a valid directory", file=sys.stderr)
        sys.exit(1)

    targets = FixationTargets(targetsdir)

    key = 0
    while key not in [0x1B]: # escape
        if key == 0x250000: # left arrow
            targets.showPrevTarget()
        elif key in(0x20, 0x270000): # space or right arrow
            targets.showNextTarget()

        key = cv2.waitKeyEx()
    
# EOF
