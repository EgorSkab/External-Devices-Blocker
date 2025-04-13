import subprocess

def get_connected_devices_by_class(device_type=""):
    try:
        if device_type == "":
            return subprocess.check_output(f'powershell.exe Get-PnpDevice -Status \"OK\" | Select-Object -Property Class, FriendlyName, InstanceID | Out-String -Width 500', text=True, errors="replace").strip()
        else:
            return subprocess.check_output(f'powershell.exe Get-PnpDevice -Class \"{device_type}\" -Status \"OK\" | Select-Object -Property FriendlyName, InstanceID | Out-String -Width 500', text=True, errors="replace").strip()
    except subprocess.CalledProcessError as e:
        return f"Error retrieving {device_type} devices: {str(e)}"

def block_device_by_id(device_id):
    try:
        result = subprocess.run(f'powershell.exe -Command "Disable-PnpDevice -InstanceId \'{device_id}\' -Confirm:$false"',  shell=True, text=True, capture_output=True)
        if result.returncode == 0:
            return f"Device {device_id} blocked successfully."
        else:
            return f"Failed to block device {device_id}."
    except Exception as e:
        return f"Error blocking device {device_id}: {str(e)}"

def unblock_device_by_id(device_id):
    try:
        result = subprocess.run(f'powershell.exe -Command "Enable-PnpDevice -InstanceId \'{device_id}\' -Confirm:$false"', shell=True, text=True, capture_output=True)
        if result.returncode == 0:
            return f"Device {device_id} unblocked successfully."
        else:
            return f"Failed to unblock device {device_id}."
    except Exception as e:
        return f"Error unblocking device {device_id}: {str(e)}"
