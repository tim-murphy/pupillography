import os
import subprocess
import sys

if __name__ == '__main__':
    print("Installing required packages for pupillometry software")
    print("")

    # the directory containing requirements.txt
    basedir = os.path.split(sys.argv[0])[0]
    reqs = os.path.join(basedir, "requirements.txt")

    # update pip first
    print("Updating pip...")
    subprocess.check_call(["pip", "install", "--upgrade", "pip"])
    print("done")

    # then install the packages
    print("Installing required packages...")
    subprocess.check_call(["pip", "install", "-r", reqs])
    print("done")

    input("All done! Press enter to exit.")

# EOF
