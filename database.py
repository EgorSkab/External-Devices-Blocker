import sqlite3 as sql


def initial_devices(components: list[dict[str, str, str]]=None):
    connection = sql.connect('devices.db')
    cursor = connection.cursor()

    cursor.execute("DELETE FROM Devices")
    cursor.execute("DELETE FROM Components")

    cursor.execute(f"INSERT INTO Devices (ID, Name, Permission, Connected) VALUES (0, 'InitialDevices', TRUE, TRUE)")

    if not components:
        from commands import get_connected_devices_by_class
        components = get_connected_devices_by_class()

    query = "INSERT INTO Components (Device_ID, IID, Class, Name, Status) VALUES "
    for component in components:
        query += f"(0, '{component["InstanceId"]}', '{component["Class"]}', '{component["FriendlyName"]}', 'OK'), "
    cursor.execute(query[:-2])

    connection.commit()
    connection.close()


def add_device(components: list[dict[str, str]]):
    if not components:
        return "Got no connections"
    connection = sql.connect('devices.db')
    cursor = connection.cursor()
    cursor.execute(f"INSERT INTO Devices (Connected) VALUES (TRUE)")
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
    for component in components:
        cursor.execute(f"UPDATE Components SET Name='{component["FriendlyName"]}', Class='{component["Class"]}', Status='{component["Status"]}' WHERE IID='{component['InstanceId']}'")
    connection.commit()
    connection.close()


def get_devices(id: int=None, iid: str=None, type: str=None, name: str=None, status: str=None):
    connection = sql.connect('devices.db')
    cursor = connection.cursor()
    query = f"SELECT * FROM Components"
    if id or iid or type or name or status:
        query += f" WHERE "
        params = 0
        if id:
            params += 1
            query += f"Device_ID={id} "
        if iid:
            if params:
                query += f"AND "
            params += 1
            query += f"IID='{iid}' "
        if type:
            if params:
                query += f"AND "
            params += 1
            query += f"Class='{type}' "
        if name:
            if params:
                query += f"AND "
            params += 1
            query += f"Name='{name}' "
        if status:
            if params:
                query += f"AND "
            query += f"Status='{status}' "
    devices = cursor.execute(query).fetchall()
    return devices
