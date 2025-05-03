import sqlite3 as sql


def initial_devices(components: list[dict[str, str, str]]=None):
    connection = sql.connect('devices.db')
    cursor = connection.cursor()

    cursor.execute("DELETE FROM Devices")
    cursor.execute("DELETE FROM Components")

    cursor.execute("INSERT INTO Devices (ID, Name, Permission, Connected) VALUES (0, 'InitialDevices', TRUE, TRUE)")

    if not components:
        from commands import get_connected_devices_by_class
        components = get_connected_devices_by_class()

    query = "INSERT INTO Components (Device_ID, IID, Class, Name, Status) VALUES "
    for component in components:
        query += f"(0, '{component["InstanceId"]}', '{component["Class"]}', '{component["FriendlyName"]}', '{component['Status']}'), "
    cursor.execute(query[:-2])

    connection.commit()
    connection.close()
    print("Initial devices table has been created")


def add_device(components: list[dict[str, str]]):
    if not components:
        return "Got no connections"
    connection = sql.connect('devices.db')
    cursor = connection.cursor()
    cursor.execute(f"INSERT INTO Devices (Connected) VALUES ({'TRUE' if components[0]['Status'] == 'OK' else 'FALSE'})")
    connection.commit()
    device_id = cursor.execute("SELECT ID FROM Devices WHERE ROWID=last_insert_rowid()").fetchone()[0]
    query = "INSERT INTO Components (Device_ID, IID, Class, Name, Status) VALUES "
    for component in components:
        query += f"({device_id}, '{component["InstanceId"]}', '{component["Class"]}', '{component["FriendlyName"]}', '{component["Status"]}'), "
    cursor.execute(query[:-2])
    connection.commit()
    connection.close()


def edit_device(components: list[dict[str, str]]):
    connection = sql.connect('devices.db')
    cursor = connection.cursor()
    device = cursor.execute(f"SELECT Device_ID FROM Components WHERE IID='{components[0]["InstanceId"]}'").fetchone()[0]
    if device == 0:
        remove_components(components)
        add_device(components)
        return
    else:
        if components[0]["Status"] == "OK":
            cursor.execute(f"UPDATE Devices SET Connected=TRUE WHERE ID={device}")
        else:
            cursor.execute(f"UPDATE Devices SET Connected=FALSE WHERE ID={device}")
    for component in components:
        cursor.execute(f"UPDATE Components SET Name='{component["FriendlyName"]}', Class='{component["Class"]}', Status='{component["Status"]}' WHERE IID='{component['InstanceId']}'")
    connection.commit()
    connection.close()


def remove_components(components: list[dict[str, str]]):
    connection = sql.connect('devices.db')
    cursor = connection.cursor()
    for component in components:
        cursor.execute(f"DELETE FROM Components WHERE IID='{component['InstanceId']}'")
    connection.commit()
    connection.close()


def get_components(id: int=None, iid: str=None, type: str=None, name: str=None, status: str=None):
    connection = sql.connect('devices.db')
    cursor = connection.cursor()
    query = f"SELECT * FROM Components"
    if id or iid or type or name or status:
        query += f" WHERE "
        params = False
        if id:
            params = True
            query += f"Device_ID={id} "
        if iid:
            if params:
                query += f"AND "
            else:
                params = True
            query += f"IID='{iid}' "
        if type:
            if params:
                query += f"AND "
            else:
                params = True
            query += f"Class='{type}' "
        if name:
            if params:
                query += f"AND "
            else:
                params = True
            query += f"Name='{name}' "
        if status:
            if params:
                query += f"AND "
            query += f"Status='{status}' "
    components = cursor.execute(query).fetchall()
    return components

def get_devices(id: str=None, name: str=None, permission: str=None, connected: str=None):
    connection = sql.connect('devices.db')
    cursor = connection.cursor()
    query = f"SELECT * FROM Devices"
    params = False
    if id:
        query += f" WHERE "
        params = True
        query += f"ID={id} "
    if name:
        if params:
            query += f"AND "
        else:
            params = True
        query += f"Name='{name}' "
    if permission:
        if params:
            query += f"AND "
        else:
            params = True
        query += f"Permission='{permission}' "
    if connected:
        if params:
            query += f"AND "
        query = f"Connected={connected} "
    devices = cursor.execute(query).fetchall()
    return devices
