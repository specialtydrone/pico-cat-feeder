
import network
import socket
import time

from secrets import WIFI_SSID, WIFI_PASSWORD

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(WIFI_SSID, WIFI_PASSWORD)

print("Connecting to Wi-Fi...")

timeout = time.ticks_add(time.ticks_ms(), 15000)

while not wlan.isconnected():
    if time.ticks_diff(timeout, time.ticks_ms()) <= 0:
        raise RuntimeError("Wi-Fi connection timed out")
    time.sleep(0.2)

ip = wlan.ifconfig()[0]
print("Connected!")
print("Open http://{}".format(ip))

html = """<!DOCTYPE html>
<html>
<head>
    <meta name="viewport"
          content="width=device-width, initial-scale=1">
    <title>Pico Cat Feeder</title>
    <style>
        body {
            font-family: sans-serif;
            background: #f3f4f6;
            text-align: center;
            padding: 40px 16px;
        }
        .card {
            background: white;
            padding: 24px;
            border-radius: 12px;
            max-width: 400px;
            margin: auto;
        }
    </style>
</head>
<body>
    <div class="card">
        <h1>Cat Feeder</h1>
        <p>Pico W web server is running!</p>
        <p>Connected to Wi-Fi.</p>
    </div>
</body>
</html>
"""

addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
server = socket.socket()
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(addr)
server.listen(1)

print("Web server listening on port 80")

while True:
    client, address = server.accept()

    try:
        client.settimeout(3)
        request = client.recv(1024)
        print("Request from:", address)

        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/html; charset=utf-8\r\n"
            "Connection: close\r\n"
            "\r\n"
        )

        client.sendall(response.encode())
        client.sendall(html.encode())

    except OSError as error:
        print("Client error:", error)

    finally:
        client.close()
