import tkinter as tk
from datetime import datetime, timedelta, timezone
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_FILE = os.path.join(BASE_DIR, "esemenyek_export.json")

events_cache = []
last_reload_time = None
RELOAD_INTERVAL_SECONDS = 60


def parse_datetime(value):
    """
    ISO dátum biztonságos beolvasása.
    Kezeli a timezone nélküli és timezone-os időpontokat is.
    """
    dt = datetime.fromisoformat(value)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc).astimezone()
    else:
        dt = dt.astimezone()

    return dt


def load_events():
    """
    Események betöltése a JSON fájlból.
    """
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        raw_events = json.load(f)

    events = []

    for event in raw_events:
        try:
            start_time = parse_datetime(event["kezdes"])
            end_time = parse_datetime(event["vege"])

            events.append({
                "cim": event.get("cim", "Névtelen"),
                "kezdes": start_time,
                "vege": end_time
            })

        except Exception as e:
            print("Hiba az esemény feldolgozásakor:", e)

    return sorted(events, key=lambda e: e["kezdes"])


def get_events_cached():
    """
    Percenként újratölti a JSON fájlt.
    Közben cache-ből dolgozik.
    """
    global events_cache, last_reload_time

    now = datetime.now(timezone.utc).astimezone()

    if last_reload_time is None:
        events_cache = load_events()
        last_reload_time = now
        print("Események betöltve.")

    elif (now - last_reload_time).total_seconds() >= RELOAD_INTERVAL_SECONDS:
        events_cache = load_events()
        last_reload_time = now
        print("Események újratöltve.")

    return events_cache


def get_current_or_next_event(events):
    """
    Visszaadja:
    - az aktuálisan futó eseményt, ha most eseményben vagyunk
    - különben a következő jövőbeli eseményt
    - ha nincs ilyen, akkor None
    """
    now = datetime.now(timezone.utc).astimezone()

    for event in events:
        start_time = event["kezdes"]
        end_time = event["vege"]

        if start_time <= now < end_time:
            return {
                "event": event,
                "mode": "running",
                "target_time": end_time
            }

        if now < start_time:
            return {
                "event": event,
                "mode": "upcoming",
                "target_time": start_time
            }

    return None


def update_display(remaining):
    """
    Visszaszámláló kijelzésének frissítése.
    """
    total_seconds = int(remaining.total_seconds())

    if total_seconds <= 0:
        timer_label.config(text="🏁")
        return

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    if hours >= 1:
        timer_label.config(text=f"{hours:02}:{minutes:02}:{seconds:02}")
    else:
        timer_label.config(text=f"{minutes:02}:{seconds:02}")


def start_countdown():
    """
    Másodpercenként frissíti a kijelzőt,
    de a JSON fájlt csak percenként tölti újra.
    """
    events = get_events_cached()
    current = get_current_or_next_event(events)

    if current is None:
        timer_label.config(text="✅")
        target_label.config(text="Nincs több esemény.")
        root.after(1000, start_countdown)
        return

    event = current["event"]
    mode = current["mode"]
    target_time = current["target_time"]

    if mode == "running":
        target_label.config(
            text=f"Most: {event['cim']} | vége: {event['vege'].strftime('%Y-%m-%d %H:%M')}"
        )
    else:
        target_label.config(
            text=f"Következő: {event['cim']} | kezdés: {event['kezdes'].strftime('%Y-%m-%d %H:%M')}"
        )

    now = datetime.now(timezone.utc).astimezone()
    remaining = target_time - now

    if remaining.total_seconds() > 0:
        update_display(remaining)
    else:
        update_display(timedelta(seconds=0))

    root.after(1000, start_countdown)


# 🖼️ Tkinter GUI
root = tk.Tk()
root.title("⏳ 🎯")
root.attributes("-topmost", True)

window_width = 350
window_height = 50
screen_width = root.winfo_screenwidth()
x = screen_width - window_width
y = 0
root.geometry(f"{window_width}x{window_height}+{x}+{y}")

timer_label = tk.Label(root, text="", font=("Menlo", 23, "bold"))
timer_label.pack(expand=True)

target_label = tk.Label(root, text="", font=("Menlo", 10))
target_label.pack()

# 🔁 Indítás
start_countdown()
root.mainloop()