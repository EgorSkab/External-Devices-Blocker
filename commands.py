import subprocess
import database


def get_connected_devices_by_class(device_type: str=None, status: str=None):
    try:
        command = f'powershell.exe chcp 1251; Get-PnpDevice'
        if device_type:
            command += f' -Class "{device_type}"'
        if status:
            command += f' -Status "{status}"'
        command += f' | Select-Object -Property Status, Class, FriendlyName, InstanceID | Out-String -Width 500'
        result = subprocess.check_output(command, text=True, errors="replace").strip().splitlines()
        connections = []
        for line in result[4:]:
            columns = line.split()
            device_status = columns[0]
            device_class = columns[1]
            friendly_name = ''.join(columns[2:-1])
            instance_id = columns[-1]
            connections.append({"Status": device_status, "Class": device_class, "FriendlyName": friendly_name, "InstanceId": instance_id})
        return connections
    except subprocess.CalledProcessError as e:
        return f"Error retrieving {device_type} devices: {str(e)}"


def block_component_by_iid(device_iid: str):
    try:
        result = subprocess.run(f'powershell.exe -Command "Disable-PnpDevice -InstanceId \'{device_iid}\' -Confirm:$false"', shell=True, text=True, capture_output=True)
        if result.returncode == 0:
            return f"Device {device_iid} blocked successfully."
        else:
            return f"Failed to block device {device_iid}."
    except Exception as e:
        return f"Error blocking device {device_iid}: {str(e)}"


def unblock_component_by_iid(device_iid: str):
    try:
        result = subprocess.run(f'powershell.exe -Command "Enable-PnpDevice -InstanceId \'{device_iid}\' -Confirm:$false"', shell=True, text=True, capture_output=True)
        if result.returncode == 0:
            return f"Device {device_iid} unblocked successfully."
        else:
            return f"Failed to unblock device {device_iid}."
    except Exception as e:
        return f"Error unblocking device {device_iid}: {str(e)}"


def block_device_by_id(id: int):
    components = database.get_components(id=id)
    for component in components:
        block_component_by_iid(component[1])

def unblock_device_by_id(id: int):
    components = database.get_components(id=id)
    for component in components:
        unblock_component_by_iid(component[1])
