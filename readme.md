# LAN Screen Video Transfer with Multiprocessing

This repository contains Python scripts for achieving fast LAN screen video transfer with sub-50ms latency. The scripts leverage the power of multiprocessing to efficiently capture and transmit screen frames from a server to a client over a Local Area Network (LAN).

## Key Features

### VideoClient

-   **Efficient Screen Capture:** The `VideoClient` efficiently captures screen frames.
-   **Low Latency:** Achieve sub-50ms latency for real-time video transfer.
-   **Cross-Platform:** Works on both Linux and Windows operating systems.

### VideoServer

-   **Customizable Capture Area:** Specify the capture area and desired resolution.
-   **Latency Monitoring:** Measure and report latency and frames per second (FPS).
-   **Graceful Shutdown:** Stop the server gracefully when needed.

## Network Efficiency Consideration

Efforts were made to optimize network efficiency, and various encoding methods were explored. However, it was observed that encoding added significant processing overhead and introduced more latency than it reduced. Therefore, the decision was made to transmit raw screen data, resulting in faster and more responsive screen sharing, especially suitable for LAN environments.

## Requirements

### VideoClient

To run the `VideoClient` script, you'll need the following Python packages:

```shell
pip install -r client-requirements.txt
```

-   `mss==9.0.1`: Cross-platform screen capturing library.
-   `numpy==1.23.0`: Efficient data handling for image data.
-   `opencv-python==4.8.0.76`: OpenCV library for image processing.

### VideoServer

To run the `VideoServer` script, you'll need the following Python packages:

```
pip install -r server-requirements.txt
```

-   `numpy==1.23.0`: Efficient data handling for image data.
-   `opencv-python==4.8.0.76`: OpenCV library for image processing.

## Usage

### VideoClient

Run the `VideoClient` script with the following command, adjusting the parameters as needed:

```
python client.py --ip SERVER_IP --port SERVER_PORT [--stdout True/False]
```

-   `SERVER_IP`: IP address of the VideoServer.
-   `SERVER_PORT`: Port number to connect to the VideoServer.
-   `--stdout`: Enable or disable stdout prints (optional).

### VideoServer

Start the `VideoServer` script with the following command:

```
python server.py
```

-   The server listens on all available network interfaces on port 12000 by default.
-   You can customize the IP address, port, capture area, and resolution within the script.

## Performance

In LAN tests, the following performance metrics were achieved:

-   Full HD (1920x1080) resolution: 30FPS with 30ms latency.
-   512x512 pixel resolution: 80FPS with 18ms latency.

These scripts are designed for efficient LAN screen video transfer, making them suitable for various applications requiring real-time screen sharing over a local network.
