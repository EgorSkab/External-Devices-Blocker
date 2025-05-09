import threading
import time

from commands import get_connected_devices_by_class
from database import add_device, edit_device, get_components

monitoring = False
actual_monitoring = False
devices_changed = False

def monitor_devices(interval: float=5, device_type: str=None, print_changes: bool=False):
    global actual_monitoring
    db_devices = get_components(type=device_type)
    prev_devices = []
    first_loop = True
    for device in db_devices:
        prev_devices.append({"Status": device[4], "Class": device[2], "FriendlyName": device[3], "InstanceId": device[1]})

    while monitoring:
        init_time = time.time()
        current_devices = get_connected_devices_by_class(device_type)

        changed_devices = [device for device in current_devices if device not in prev_devices]

        if changed_devices:
            extra_devices = [0]
            dt = 0
            while extra_devices:
                if dt < 1:
                    time.sleep(1 - dt)
                time.sleep(1)
                t0 = time.time()
                extra_devices = [device for device in get_connected_devices_by_class(device_type) if device not in current_devices and device not in changed_devices]
                changed_devices.extend(extra_devices)
                dt = time.time() - t0

            current_devices = get_connected_devices_by_class(device_type)

            if not first_loop and print_changes:
                for device in changed_devices:
                    print("Changed devices:")
                    print(f"Class: {device["Class"]}\nFriendlyName: {device['FriendlyName']}\nInstanceId: {device['InstanceId']}\nStatus: {device['Status']}\n")

            i = 0
            length = len(changed_devices)
            added_devices = []
            while i < length:
                device = changed_devices[i]
                if not get_components(iid=device["InstanceId"]):
                    added_devices.append(device)
                    changed_devices.remove(device)
                    i -= 1
                    length -= 1
                i += 1
            if changed_devices:
                edit_device(changed_devices)
            if added_devices:
                add_device(added_devices)
            global devices_changed
            devices_changed = True

            prev_devices = current_devices

        if first_loop:
            first_loop = False
            actual_monitoring = True

        sleep_time = interval - (time.time() - init_time)
        if sleep_time > 0:
            time.sleep(sleep_time)
    actual_monitoring = False

def start_monitoring_in_background(interval: float=5, device_type: str=""):
    global monitoring
    monitoring = True
    monitor_thread = threading.Thread(target=monitor_devices, args=(interval,device_type,), daemon=True)
    monitor_thread.start()

def stop_monitoring_in_background():
    global monitoring
    monitoring = False


# usage example
# if __name__ == '__main__':
#     initial_devices()
#     start_monitoring_in_background(1)
#     while True:
#         pass
