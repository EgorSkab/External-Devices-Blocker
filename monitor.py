import threading
import time

from commands import get_connected_devices_by_class


def get_connected_devices(device_type: str=""):
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
                devices.append({"Class": device_type, "FriendlyName": friendly_name, "InstanceId": instance_id})
        return devices
    except Exception as e:
        print(f"Error fetching devices: {e}")
        return []


def monitor_devices(interval: float=5, device_type: str=""):
    initial_devices = get_connected_devices(device_type)

    while True:
        init_time = time.time()
        current_devices = get_connected_devices(device_type)

        new_devices = [device for device in current_devices if device not in initial_devices]
        unplugged_devices = [device for device in initial_devices if device not in current_devices]

        if new_devices or unplugged_devices:
            changed_devices = {"added": [0], "removed": [0]}
            while changed_devices["added"] or changed_devices["removed"]:
                time.sleep(1)
                devices = get_connected_devices(device_type)
                changed_devices["added"] = [device for device in devices if device not in initial_devices and device not in new_devices]
                changed_devices["removed"] = [device for device in initial_devices if device not in devices and device not in unplugged_devices]

                if changed_devices["added"]:
                    current_devices.extend(device for device in changed_devices["added"])
                    new_devices.extend(device for device in changed_devices["added"])

                if changed_devices["removed"]:
                    current_devices.remove(device for device in changed_devices["removed"])
                    unplugged_devices.extend(device for device in changed_devices["removed"])

            # replace with DB filling function
            for device in new_devices:
                print("Added device:")
                if len(device) == 3:
                    print(f"Class: {device["Class"]}\nFriendlyName: {device['FriendlyName']}\nInstanceId: {device['InstanceId']}\n")
                else:
                    print(f"FriendlyName: {device['FriendlyName']}\nInstanceId: {device['InstanceId']}\n")

            for device in unplugged_devices:
                print("Unplugged device:")
                if len(device) == 3:
                    print(f"Class: {device["Class"]}\nFriendlyName: {device['FriendlyName']}\nInstanceId: {device['InstanceId']}\n")
                else:
                    print(f"FriendlyName: {device['FriendlyName']}\nInstanceId: {device['InstanceId']}\n")

        initial_devices = current_devices

        sleep_time = interval - (time.time() - init_time)
        if sleep_time > 0:
            time.sleep(sleep_time)


def start_monitoring_in_background(interval: float=5, device_type: str=""):
    monitor_thread = threading.Thread(target=monitor_devices, args=(interval,device_type,), daemon=True)
    monitor_thread.start()
