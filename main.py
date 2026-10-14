
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
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cat Feeder</title>
<style>
    * { box-sizing: border-box; }

    body {
        font-family: system-ui, sans-serif;
        background: #f3f4f6;
        color: #20242c;
        margin: 0;
        padding: 24px 12px;
    }

    .container {
        max-width: 460px;
        margin: auto;
        background: white;
        padding: 24px;
        border-radius: 16px;
    }

    header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #e5e7eb;
        padding-bottom: 18px;
        margin-bottom: 20px;
    }

    h1 { font-size: 24px; margin: 0; }
    .subtitle { color: #777; font-size: 13px; }
    .network { font-size: 12px; color: #555; }

    .meal {
        border: 1px solid #ddd;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 14px;
    }

    .meal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 18px;
    }

    .meal-title { font-weight: 650; font-size: 17px; }

    .toggle {
        width: 42px;
        height: 24px;
        accent-color: #2563eb;
        cursor: pointer;
    }

    label {
        display: block;
        font-size: 13px;
        color: #666;
        margin-bottom: 8px;
    }

    input[type="time"] {
        width: 100%;
        font: inherit;
        padding: 10px;
        border: 1px solid #ccc;
        border-radius: 8px;
        margin-bottom: 20px;
    }

    input[type="range"] {
        width: 100%;
        accent-color: #2563eb;
        cursor: pointer;
    }

    .duration-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .duration-value {
        font-weight: bold;
        font-size: 14px;
    }

    .range-labels {
        display: flex;
        justify-content: space-between;
        color: #888;
        font-size: 12px;
    }

    .meal.disabled .controls {
        opacity: .4;
    }

    button {
        background: #2563eb;
        color: white;
        border: none;
        border-radius: 9px;
        padding: 14px;
        font: inherit;
        font-weight: 600;
        width: 100%;
        cursor: pointer;
    }

    #message {
        text-align: center;
        color: #666;
        font-size: 13px;
        margin-top: 12px;
    }
</style>
</head>

<body>
<div class="container">
    <header>
        <div>
            <h1>Cat Feeder</h1>
            <div class="subtitle">Feeding Schedule</div>
        </div>
        <div class="network">Pico W</div>
    </header>

    <div id="meals"></div>

    <button onclick="saveSchedule()">Save Schedule</button>
    <div id="message"></div>
</div>

<script>
const meals = [
    {id:"breakfast", name:"Breakfast",
     enabled:true, time:"07:00", duration:2},
    {id:"lunch", name:"Lunch",
     enabled:true, time:"12:00", duration:2},
    {id:"dinner", name:"Dinner",
     enabled:true, time:"18:00", duration:3}
];

function render() {
    const container = document.getElementById("meals");
    container.innerHTML = "";

    meals.forEach((meal, index) => {
        const card = document.createElement("div");
        card.className = "meal" +
            (meal.enabled ? "" : " disabled");

        card.innerHTML = `
            <div class="meal-header">
                <span class="meal-title">${meal.name}</span>
                <input type="checkbox" class="toggle"
                    ${meal.enabled ? "checked" : ""}
                    onchange="toggleMeal(${index},this.checked)">
            </div>
            <div class="controls">
                <label>Feeding time (24-hour)</label>
                <input type="time" value="${meal.time}"
                    ${meal.enabled ? "" : "disabled"}
                    onchange="setTime(${index},this.value)">

                <div class="duration-header">
                    <label>Feed duration</label>
                    <span class="duration-value"
                          id="duration-${index}">
                        ${meal.duration} seconds
                    </span>
                </div>
                <input type="range" min="1" max="5" step="1"
                    value="${meal.duration}"
                    ${meal.enabled ? "" : "disabled"}
                    oninput="setDuration(${index},this.value)">
                <div class="range-labels">
                    <span>1s</span><span>2s</span>
                    <span>3s</span><span>4s</span>
                    <span>5s</span>
                </div>
            </div>
        `;
        container.appendChild(card);
    });
}

function toggleMeal(index, enabled) {
    meals[index].enabled = enabled;
    render();
}

function setTime(index, value) {
    meals[index].time = value;
}

function setDuration(index, value) {
    meals[index].duration = Number(value);
    document.getElementById("duration-" + index)
        .textContent = value + " seconds";
}

function saveSchedule() {
    document.getElementById("message").textContent =
        "Schedule saving is not connected yet.";
}

render();
</script>
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
