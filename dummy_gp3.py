import errno
import random
import socket
import sys
import time

import pupillography

if __name__ == '__main__':
    HOST = '127.0.0.1'
    PORT = 4242
    ADDRESS = (HOST, PORT)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        print("Waiting for connection...")
        sock.bind(ADDRESS)
        sock.listen()
        conn, addr = sock.accept()
        print("Connected.")

        with conn:
            last_right = 5.00
            last_left = 4.80
            last_time = 0.00
            change_mm = 0.10

            keepRunning = True
            print("Sending data to ", HOST, ":", PORT, "...", sep="")

            while keepRunning:
                outData = '<REC TIME="' + str(last_time) + '" LPOGX="0.5" LPOGY="0.5" LPOGV="1" RPOGX="0.4" RPOGY="0.6" RPOGV="1" LPMM="' + str(last_left) + '" LPMMV="1" RPMM="' + str(last_right) + '" RPMMV="1" />\r\n'

                try:
                    conn.send(str.encode(outData))
                except socket.error as e:
                    if e.errno == errno.WSAECONNRESET:
                        print("Pupillography program has stopped.")
                        keepRunning = False
                    else:
                        raise

                # update data
                last_right += (change_mm if random.getrandbits(1) else -change_mm)
                last_left += (change_mm if random.getrandbits(1) else -change_mm)
                last_time += 1.0 / pupillography.GAZEPOINT_REFRESH

                # keep in bounds
                last_right = max(last_right, pupillography.PUPIL_MIN_SIZE_MM)
                last_right = min(last_right, pupillography.PUPIL_MAX_SIZE_MM)
                last_left = max(last_left, pupillography.PUPIL_MIN_SIZE_MM)
                last_left = min(last_left, pupillography.PUPIL_MAX_SIZE_MM)

                time.sleep(1.0 / pupillography.GAZEPOINT_REFRESH)

    print("Finished! Have a nice day.")

# EOF
