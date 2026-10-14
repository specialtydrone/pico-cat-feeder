
import network
import socket
import time
import json
import os

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


SCHEDULE_FILE = "schedule.json"
MAX_BODY = 2048
MAX_HEADERS = 2048
DEFAULT_MEALS = [
    {"id": "breakfast", "name": "Breakfast", "enabled": True,
     "time": "07:00", "duration": 2},
    {"id": "lunch", "name": "Lunch", "enabled": True,
     "time": "12:00", "duration": 2},
    {"id": "dinner", "name": "Dinner", "enabled": True,
     "time": "18:00", "duration": 3},
]


def validate_schedule(data):
    if not isinstance(data, list) or len(data) != 3:
        raise ValueError("Exactly three meals are required")
    validated = []
    for default in DEFAULT_MEALS:
        matches = [meal for meal in data
                   if isinstance(meal, dict) and meal.get("id") == default["id"]]
        if len(matches) != 1:
            raise ValueError("Breakfast, Lunch and Dinner are required once each")
        meal = matches[0]
        if meal.get("name") != default["name"]:
            raise ValueError("Invalid meal name")
        if type(meal.get("enabled")) is not bool:
            raise ValueError("Enabled must be a boolean")
        value = meal.get("time")
        if (not isinstance(value, str) or len(value) != 5 or value[2] != ":"
                or any(c not in "0123456789" for c in value[:2] + value[3:])
                or int(value[:2]) > 23 or int(value[3:]) > 59):
            raise ValueError("Time must be valid HH:MM")
        duration = meal.get("duration")
        if type(duration) is not int or not 1 <= duration <= 5:
            raise ValueError("Duration must be an integer from 1 to 5")
        validated.append({"id": default["id"], "name": default["name"],
                          "enabled": meal["enabled"], "time": value,
                          "duration": duration})
    return validated


def load_schedule():
    try:
        with open(SCHEDULE_FILE, "r") as file:
            # Bound file reads too, so a damaged file cannot exhaust memory.
            content = file.read(MAX_BODY + 1)
        if len(content) > MAX_BODY:
            raise ValueError("Schedule file is too large")
        return validate_schedule(json.loads(content))
    except (OSError, ValueError):
        print("Schedule unavailable or invalid; using defaults")
        return validate_schedule(DEFAULT_MEALS)


def save_schedule(data):
    temporary = SCHEDULE_FILE + ".tmp"
    try:
        with open(temporary, "w") as file:
            json.dump(data, file)
        # Do not remove the existing file first: rename replaces it on Pico's FS.
        os.rename(temporary, SCHEDULE_FILE)
    except OSError:
        try:
            os.remove(temporary)
        except OSError:
            pass
        raise


schedule = load_schedule()


def read_request(client):
    data = b""
    while b"\r\n\r\n" not in data:
        chunk = client.recv(256)
        if not chunk:
            raise ValueError("Incomplete request headers")
        data += chunk
        if len(data.split(b"\r\n\r\n", 1)[0]) > MAX_HEADERS:
            raise ValueError("Request headers are too large")
    header, body = data.split(b"\r\n\r\n", 1)
    lines = header.decode("utf-8").split("\r\n")
    parts = lines[0].split()
    if len(parts) != 3 or parts[2] not in ("HTTP/1.0", "HTTP/1.1"):
        raise ValueError("Invalid request line")
    method, path = parts[:2]
    headers = {}
    for line in lines[1:]:
        if ":" not in line:
            raise ValueError("Invalid request header")
        key, value = line.split(":", 1)
        key = key.strip().lower()
        if key in headers:
            raise ValueError("Duplicate request header")
        headers[key] = value.strip()
    if "transfer-encoding" in headers:
        raise ValueError("Transfer-Encoding is not supported")
    length = headers.get("content-length")
    if method == "POST" and length is None:
        raise ValueError("Content-Length is required")
    if length is None:
        length = 0
    elif not length or any(c not in "0123456789" for c in length):
        raise ValueError("Invalid Content-Length")
    else:
        length = int(length)
    if length > MAX_BODY:
        raise ValueError("Request body is too large")
    body = body[:length]
    while len(body) < length:
        chunk = client.recv(min(256, length - len(body)))
        if not chunk:
            raise ValueError("Incomplete request body")
        body += chunk
    return method, path, body


def send_response(client, status, content_type, body):
    if isinstance(body, str):
        body = body.encode("utf-8")
    header = (
        "HTTP/1.1 {}\r\n"
        "Content-Type: {}\r\n"
        "Content-Length: {}\r\n"
        "Cache-Control: no-store\r\n"
        "Connection: close\r\n\r\n"
    ).format(status, content_type, len(body))
    client.sendall(header.encode())
    client.sendall(body)


def send_json(client, status, data):
    send_response(client, status, "application/json", json.dumps(data))


def handle_request(client):
    global schedule
    try:
        method, path, body = read_request(client)
    except ValueError as error:
        send_json(client, "400 Bad Request", {"error": str(error)})
        return
    if path == "/" and method == "GET":
        send_response(client, "200 OK", "text/html; charset=utf-8", html)
    elif path == "/schedule" and method == "GET":
        send_json(client, "200 OK", schedule)
    elif path == "/schedule" and method == "POST":
        try:
            updated = validate_schedule(json.loads(body.decode("utf-8")))
        except ValueError as error:
            send_json(client, "400 Bad Request", {"error": str(error)})
            return
        try:
            save_schedule(updated)
        except OSError:
            send_json(client, "500 Internal Server Error",
                      {"error": "Could not save schedule"})
            return
        schedule = updated
        send_json(client, "200 OK", {"saved": True})
    elif path in ("/", "/schedule"):
        send_json(client, "405 Method Not Allowed", {"error": "Method not allowed"})
    else:
        send_json(client, "404 Not Found", {"error": "Not found"})


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

    <button id="save" onclick="saveSchedule()" disabled>Save Schedule</button>
    <div id="message"></div>
</div>

<script>
let meals = [];
let saving = false;

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

async function loadSchedule() {
    const message = document.getElementById("message");
    message.textContent = "Loading schedule...";
    try {
        const response = await fetch("/schedule", {cache: "no-store"});
        if (!response.ok) throw new Error("Could not load schedule");
        meals = await response.json();
        render();
        document.getElementById("save").disabled = false;
        message.textContent = "";
    } catch (error) {
        message.textContent = "Could not load schedule. Refresh to retry.";
    }
}

async function saveSchedule() {
    if (saving || meals.length !== 3) return;
    saving = true;
    const button = document.getElementById("save");
    const message = document.getElementById("message");
    button.disabled = true;
    message.textContent = "Saving schedule...";
    try {
        const response = await fetch("/schedule", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(meals)
        });
        const result = await response.json();
        if (!response.ok || result.saved !== true) {
            throw new Error(result.error || "Could not save schedule");
        }
        message.textContent = "Schedule saved.";
    } catch (error) {
        message.textContent = "Save failed: " + error.message;
    } finally {
        saving = false;
        button.disabled = false;
    }
}

loadSchedule();
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
        print("Request from:", address)
        handle_request(client)

    except OSError as error:
        print("Client error:", error)

    finally:
        client.close()
