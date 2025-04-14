import sqlite3 as sql


def initial_devices(components: list[dict[str, str, str]]=None):
    connection = sql.connect('devices.db')
    cursor = connection.cursor()

    cursor.execute("DELETE FROM Devices")
    cursor.execute("DELETE FROM Components")

    cursor.execute(f"INSERT INTO Devices (ID, Name, Permission, Connected) VALUES (0, 'InitialDevices', TRUE, TRUE)")

    if not components:
        from monitor import get_connected_devices
        components = get_connected_devices()

    query = "INSERT INTO Components (Device_ID, IID, Class, Name, Status) VALUES "
    for component in components:
        query += f"(0, '{component["InstanceId"]}', '{component["Class"]}', '{component["FriendlyName"]}', 'OK'), \n"
    cursor.execute(query[:-3])

    connection.commit()
    connection.close()


def add_device(components: list[dict[str, str, str]]):
    connection = sql.connect('devices.db')
    cursor = connection.cursor()
    device_id = cursor.execute(f"INSERT INTO Devices (Connected) VALUES (TRUE); SELECT ID FROM Devices WHERE ROWID=last_insert_rowid()").fetchall()[0]
    for component in components:
        cursor.execute(f"INSERT INTO Components (Device_ID, IID, Class, Name, Status) VALUES ({device_id}, '{component["InstanceId"]}', '{component["Class"]}', '{component["FriendlyName"]}', 'OK')")
    connection.commit()
    connection.close()


def get_devices(id: str=None, name: str=None, status: str=None):
    connection = sql.connect('devices.db')
    cursor = connection.cursor()
    query = f"SELECT * FROM Components"
    if id or name or status:
        query += f" WHERE "
        params = 0
        if id:
            params += 1
            query += f"ID={id} "
        if name:
            if params:
                query += f"AND "
            params += 1
            query += f"Name={name} "
        if status:
            if params:
                query += f"AND "
            query += f"Status={status} "
    devices = cursor.execute(query).fetchall()[2:]
    print(devices)
    return devices
