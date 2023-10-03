import socket
import struct
import multiprocessing as mp
import pickle
import cv2 as cv
import ctypes
import numpy as np
import time
import platform
if platform.system() == 'Linux':
    from mss.linux import MSS
else:
    from mss.windows import MSS


class VideoClient:
    DEFAULT_BUFFER_SIZE = 2

    def __init__(
        self,
        ip: str,
        port: int,
        stdout: bool = True,
        buffer_size: int = DEFAULT_BUFFER_SIZE,
    ):
        self.ip: str = ip
        self.port = port
        self.stdout = stdout
        self.sock: socket.socket = None
        self.running = mp.Value(ctypes.c_bool, False)
        self.recording = mp.Value(ctypes.c_bool, False)
        self.img_q = mp.Queue(buffer_size)
        self.error = None
        self.resolution = mp.Array(ctypes.c_uint32, 2)
        self.capture_area = mp.Array(ctypes.c_uint32, 4)

    def recvall(self, n: int) -> bytearray:
        data = bytearray()
        while len(data) < n:
            packet = self.sock.recv(n - len(data))
            data += packet
        return data

    def recv_bytes(self,) -> bytes:
        raw_msglen = self.recvall(4)
        msglen = struct.unpack('>I', raw_msglen)[0]
        return bytes(self.recvall(msglen))

    def send_bytes(self, msg: bytes) -> bool:
        msg = struct.pack('>I', len(msg)) + msg
        self.sock.sendall(msg)

    def _communication_loop(self):
        self.send_bytes(pickle.dumps(self.monitors))
        capture_area = pickle.loads(self.recv_bytes())
        self.capture_area = np.uint32(capture_area)
        self.resolution[:] = np.uint32(pickle.loads(self.recv_bytes()))

        self.recording.value = True
        p = mp.Process(target=self._recording_loop, daemon=False)
        p.start()

        while self.running.value:
            img_buffer = self.img_q.get()
            time_sent = pickle.loads(self.recv_bytes())
            self.send_bytes(img_buffer)
            self.send_bytes(pickle.dumps(time_sent))

    def _recording_loop(self):
        with MSS() as mss:
            x, y, w, h = self.capture_area[:]
            capture_area = {"left": x, "top": y, "width": w, "height": h}
            resolution = self.resolution[:]
            if self.stdout:
                print(f'[+] Capture area set to x:{x} y:{y} w:{w} h:{h}')
                print(
                    f'[+] Transfer resolution set to w:{resolution[0]} h:{resolution[1]}')
                print(f'[+] Recording started')
            while self.recording.value:
                img = mss.grab(capture_area)
                img = np.uint8(img)[:, :, :3]
                if self.resolution is not None:
                    img = cv.resize(img, resolution)
                img_buffer = img.tobytes()
                self.img_q.put(img_buffer)

    def start(self):
        self.running.value = True
        with MSS() as mss:
            self.monitors = mss.monitors
        while self.running.value:
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((self.ip, self.port))
                if self.stdout:
                    print(f'[+] Connected to {self.ip}:{self.port}')
                self._communication_loop()
            except OSError as e:
                self.recording.value = False
                while not self.img_q.empty:
                    self.img_q.get()
                self.sock = None
                self.error = str(e)
                if self.stdout:
                    print(f'[!] {self.error}')
                    for t in range(3, 0, -1):
                        print(f'[+] Restarting in {t}...', end='\r')
                        time.sleep(1)
                    print(f'[+] Restarting now...')


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="VideoClient Argument Parser")

    parser.add_argument('--ip', type=str, default='localhost',
                        help='IP address for the server')
    parser.add_argument('--port', type=int, default=12000,
                        help='Port number for the server')
    parser.add_argument('--stdout', type=bool, default=True,
                        help='Enables/Disables stdout prints')

    args = parser.parse_args()

    client = VideoClient(args.ip, args.port, args.stdout)
    client.start()
