import random
import socket
import sys
import time

import pupillography

if __name__ == '__main__':
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    print("Waiting for connection...")
    sock.bind(pupillography.ADDRESS)
    sock.listen()
    conn, addr = sock.accept()
    print("Connected.")

    with conn:
        last_right = 5.00
        last_left = 4.80
        last_time = 0.00
        change_mm = 0.10

        while True:
            outData = '<REC TIME="' + str(last_time) + '" LPMM="' + str(last_left) + '" LPMMV="1" RPMM="' + str(last_right) + '" RPMMV="1" />\r\n'
            print(outData, end="")
            conn.send(str.encode(outData))

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

    sock.close()

# EOF
