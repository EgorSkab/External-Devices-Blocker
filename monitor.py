import threading
import time

from commands import get_connected_devices_by_class


def get_connected_devices(device_type=""):
    try:
        result = get_connected_devices_by_class(device_type)
        devices = []
        lines = result.splitlines()
        for line in lines[3:]:
            columns = line.split()
            if len(columns) >= 2 and device_type == "":
                device_class = columns[0]
                instance_id = columns[-1]
                friendly_name = ''.join(columns[1:-1])
                devices.append({"Class": device_class, "FriendlyName": friendly_name, "InstanceId": instance_id})
            elif len(columns) >= 3 and device_type != "":
                instance_id = columns[-1]
                friendly_name = ''.join(columns[:-1])
                devices.append({"FriendlyName": friendly_name, "InstanceId": instance_id})
        return devices
    except Exception as e:
        print(f"Error fetching devices: {e}")
        return []


def monitor_new_devices(interval=5, device_type=""):
    initial_devices = get_connected_devices(device_type)

    while True:
        init_time = time.time()
        current_devices = get_connected_devices(device_type)

        new_devices = [device for device in current_devices if device not in initial_devices]
        if new_devices:
            additional_devices = [0]
            while additional_devices:
                time.sleep(1)
                additional_devices = [device for device in get_connected_devices(device_type) if device not in initial_devices and device not in new_devices]
                if additional_devices:
                    current_devices.extend(device for device in additional_devices)
                    new_devices.extend(device for device in additional_devices)

            # replace with DB filling function
            for device in new_devices:
                if len(device) == 3:
                    print(f"Class: {device["Class"]}\nFriendlyName: {device['FriendlyName']}\nInstanceId: {device['InstanceId']}\n")
                else:
                    print(f"FriendlyName: {device['FriendlyName']}\nInstanceId: {device['InstanceId']}\n")

        initial_devices = current_devices

        sleep_time = interval - (time.time() - init_time)
        if sleep_time > 0:
            time.sleep(sleep_time)


def start_monitoring_in_background(interval=5, device_type=""):
    monitor_thread = threading.Thread(target=monitor_new_devices, args=(interval,device_type,), daemon=True)
    monitor_thread.start()
