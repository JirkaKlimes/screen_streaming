import socket
import struct
import multiprocessing as mp
import pickle
import time
import cv2 as cv
import ctypes
import numpy as np
from typing import Optional


class VideoServer:
    # ------------- Communication Scheme --------------
    #
    # [Server] <-    monitor resolutions    <- [Client]
    # [Server] ->   desired capture area    -> [Client]
    # [Server] -> desired stream resolution -> [Client]
    #
    # LOOP:
    #       [Server] ->   time stamp   -> [Client]
    #       [Server] <-  image buffer  <- [Client]
    #       [Server] <-    latency     <- [Client]

    DEFAULT_BUFFER_SIZE = 2

    def __init__(
        self,
        ip: str,
        port: int,
        monitor: int = 0,
        area: Optional[tuple[int, int]] = (640, 640),
        resolution: Optional[tuple[int, int]] = None,
        buffer_size: int = DEFAULT_BUFFER_SIZE,
    ):
        self.ip: str = ip
        self.port = port
        self.sock: socket.socket = None
        self.client: socket.socket = None
        self.monitor_num = monitor
        self.area = area
        self.resolution = area if resolution is None else resolution
        self.latency = mp.Value(ctypes.c_float, 0)
        self.fps = mp.Value(ctypes.c_float, 0)
        self.is_stopped = mp.Value(ctypes.c_bool, False)
        self.img_q = mp.Queue(buffer_size)

    def wait_for_img(self):
        """
        Waits for frame, then returns it as 3D np.ndarray
        """
        while True:
            buffer = self.img_q.get()
            img_flat = np.frombuffer(buffer, dtype=np.uint8)
            if img_flat.size == self.resolution[0] * self.resolution[1] * 3:
                break
        return img_flat.reshape((*self.resolution[::-1], 3))

    def start(self):
        """
        Starts the Video Server as a new process
        """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.bind((self.ip, self.port))
        except OSError as e:
            self.sock = None
            return str(e)

        mp.Process(target=self._main_loop, daemon=True).start()

    def recvall(self, n: int) -> bytearray:
        data = bytearray()
        while len(data) < n:
            packet = self.client.recv(n - len(data))
            data += packet
        return data

    def recv_bytes(self,) -> bytes:
        raw_msglen = self.recvall(4)
        msglen = struct.unpack('>I', raw_msglen)[0]
        return bytes(self.recvall(msglen))

    def send_bytes(self, msg: bytes) -> bool:
        msg = struct.pack('>I', len(msg)) + msg
        self.client.sendall(msg)

    def get_capture_area(self, monitors):
        x, y, w, h = monitors[self.monitor_num].values()
        if self.area is None:
            return (x, y, w, h)

        x = x + (w-self.area[0]) // 2
        y = y + (h-self.area[1]) // 2
        return (x, y, *self.area)

    def _communication_loop(self):
        monitors = pickle.loads(self.recv_bytes())
        self.send_bytes(pickle.dumps(self.get_capture_area(monitors)))
        self.send_bytes(pickle.dumps(self.resolution))
        while not self.is_stopped.value:
            t1 = time.time()
            self.send_bytes(pickle.dumps(time.time()))
            img_data = self.recv_bytes()
            time_sent = pickle.loads(self.recv_bytes())
            if not self.img_q.full():
                self.img_q.put(img_data)

            latency = time.time() - time_sent
            self.latency.value = self.latency.value * 0.9 + latency * 0.1

            fps = 1 / (time.time() - t1)
            self.fps.value = self.fps.value * 0.9 + fps * 0.1

    def _main_loop(self):
        self.sock.listen(1)

        while not self.is_stopped.value:
            try:
                self.client, _ = self.sock.accept()
                self._communication_loop()
            except ConnectionResetError:
                self.client = None

        self.client.close()
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()

    def stop(self):
        self.is_stopped.value = True


if __name__ == "__main__":
    ip = ''
    port = 12000

    server = VideoServer(ip, port, area=(512, 512))
    error = server.start()
    if error is None:
        print("Video Server is running!")
    else:
        print(error)
        quit()
    while True:
        t1 = time.time()

        cv.imshow("IMG", server.wait_for_img())
        if cv.waitKey(1) == ord('q'):
            break

        print(f"Latency: {server.latency.value * 1000:0.2f}ms")
        print(f"FPS: {server.fps.value:.02f}")
        print(f"local FPS: {1/(time.time()-t1):.02f}")

    server.stop()
