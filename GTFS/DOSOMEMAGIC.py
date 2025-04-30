import sqlite3
import json
from itertools import tee
from tqdm import tqdm
import math
from datetime import datetime, timedelta
from shapely.geometry import Point, Polygon
import csv
import os
import zipfile

Databasename = 'GTFS_Database.db'

# Создаем подключение к базе данных
conn = sqlite3.connect(Databasename)

# Создаем курсор для выполнения SQL-запросов
cursor = conn.cursor()

# Создаем таблицу Agency
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Agency (
        agency_id TEXT,
        agency_name TEXT,
        agency_timezone TEXT,
        agency_url TEXT
    )
''')

# Создаем таблицу Calendar
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Calendar (
        service_id TEXT,
        monday INTEGER,
        tuesday INTEGER,
        wednesday INTEGER,
        thursday INTEGER,
        friday INTEGER,
        saturday INTEGER,
        sunday INTEGER,
        start_date TEXT,
        end_date TEXT
    )
''')

# Создаем таблицу Calendar_dates
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Calendar_dates (
        service_id TEXT,
        date TEXT,
        exception_type INTEGER
    )
''')

# Создаем таблицу Routes
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Routes (
        route_id TEXT,
        agency_id TEXT,
        route_short_name TEXT,
        route_long_name TEXT,
        route_type INTEGER,
        Headway TEXT,
        Сapacity TEXT,
        geometry TEXT,
        fid TEXT
    )
''')

# Создаем таблицу Shapes
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Shapes (
        shape_id TEXT,
        shape_pt_lat REAL,
        shape_pt_lon REAL,
        shape_pt_sequence INTEGER
    )
''')

# Создаем таблицу Stop_times
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Stop_times (
        trip_id TEXT,
        arrival_time TEXT,
        departure_time TEXT,
        stop_id TEXT,
        stop_sequence INTEGER,
        FOREIGN KEY (trip_id) REFERENCES Trips(trip_id),
        FOREIGN KEY (stop_id) REFERENCES Stops(stop_id)
    )
''')

# Создаем таблицу Stops
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Stops (
        stop_id TEXT,
        stop_name TEXT,
        stop_lat REAL,
        stop_lon REAL,
        id_stop INTEGER,
        highway TEXT
    )
''')

# Создаем таблицу Transfers
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Transfers (
        from_stop_id TEXT,
        to_stop_id TEXT,
        transfer_type INTEGER,
        min_transfer_time INTEGER
    )
''')

# Создаем таблицу Trips
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Trips (
        route_id TEXT,
        service_id TEXT,
        trip_id TEXT,
        trip_headsign TEXT,
        direction_id INTEGER,
        block_id INTEGER,
        shape_id TEXT,
        FOREIGN KEY (shape_id) REFERENCES Shapes(shape_id),
        FOREIGN KEY (route_id) REFERENCES Routes(route_id)
    )
''')

# Таблица для совмещения stops и routes
cursor.execute('''
    CREATE TABLE IF NOT EXISTS StopRoutes (
        stop_id TEXT,
        route_id TEXT,
        FOREIGN KEY (stop_id) REFERENCES Stops(stop_id),
        FOREIGN KEY (route_id) REFERENCES Routes(route_id)
    )
''')


# Сохраняем изменения
conn.commit()

# Закрываем соединение с базой данных
conn.close()




type_map = {
    # 'A' : 1,
    "B": 1,
    "MT": 2,
    "Tr": 3,
    # 'TB' : 3,
    "T": 4,
    "M": 5,
    "RA": 6,
    "E": 7,
    "PAR": 8,
}
direction_map = {"1": 0, "2": 1}
# Открываем файл Routs.geojson и загружаем данные
with open("Data/OT3.geojson", "r", encoding="utf-8") as file:
    routs_data = json.load(file)

# Открываем файл Stations.geojson и загружаем данные
with open("Data/OOT3.geojson", "r", encoding="utf-8") as file:
    stations_data = json.load(file)

# Создаем подключение к базе данных
conn = sqlite3.connect(Databasename)

# Создаем курсор для выполнения SQL-запросов
cursor = conn.cursor()


# Функция для разделения итерируемого объекта на пары
def pairwise(iterable):
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


# Функция для вычисления расстояния между двумя точками (формула Винсенти)
def vincenty_distance(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return 6371000 * c  # Радиус Земли в метрах


# Функция для определения принадлежности остановки к маршруту
def is_on_route(stop_lat, stop_lon, route):
    min_distance_squared = 0.0001**2
    for (lat1, lon1), (lat2, lon2) in pairwise(route):
        d1_squared = vincenty_distance(stop_lat, stop_lon, lat1, lon1) ** 2
        d2_squared = vincenty_distance(stop_lat, stop_lon, lat2, lon2) ** 2

        if d1_squared < min_distance_squared or d2_squared < min_distance_squared:
            return True

        lat_diff = lat2 - lat1
        lon_diff = lon2 - lon1
        len_squared = lat_diff**2 + lon_diff**2

        # Вычисляем скалярное произведение векторов (stop_lat - lat1, stop_lon - lon1) и (lat_diff, lon_diff)
        dot_product = (stop_lat - lat1) * lat_diff + (stop_lon - lon1) * lon_diff

        # Проверяем, находится ли проекция остановки на отрезке
        if 0 < dot_product < len_squared:
            # Вычисляем квадрат расстояния от остановки до линии
            d_squared = d1_squared - (dot_product / len_squared) ** 2
            if d_squared < min_distance_squared:
                return True

    return False


# Функция для вставки данных в таблицу
def insert_data(table_name, data):
    for feature in tqdm(data["features"], desc=table_name):
        properties = feature["properties"]
        geometry = feature["geometry"]
        if table_name == "Routes":
            # Вставляем данные в таблицу Routes
            route_id = properties.get("id")
            agency_id = "0"  # Значение agency_id по умолчанию
            route_short_name = properties.get("LINENAME")
            route_long_name = properties.get("NAME")
            route_type = type_map.get(
                properties["TSYSCODE"], 3
            )  # Значение route_type по умолчанию
            Headway = properties.get("Headway")
            Сapacity = properties.get("Сapacity")
            route_geometry = json.dumps(geometry)
            fid = properties.get("fid")

            cursor.execute(
                """
                INSERT INTO Routes (route_id, agency_id, route_short_name, route_long_name, route_type, Headway, Сapacity, geometry, fid)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    route_id,
                    agency_id,
                    route_short_name,
                    route_long_name,
                    route_type,
                    Headway,
                    Сapacity,
                    route_geometry,
                    fid,
                ),
            )
        elif table_name == "Stops":
            # Вставляем данные в таблицу Stops
            stop_id = properties.get("NO")
            stop_name = properties.get("NAME")
            stop_lon, stop_lat = geometry["coordinates"]
            id_stop = properties.get("id")
            highway = properties.get("HIGHWAY")

            cursor.execute(
                """
                INSERT INTO Stops (stop_id, stop_name, stop_lat, stop_lon, id_stop, highway)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (stop_id, stop_name, stop_lat, stop_lon, id_stop, highway),
            )

            # Проверяем принадлежность остановки к маршруту
            cursor.execute("SELECT fid, geometry FROM Routes")
            routes = cursor.fetchall()
            for route in routes:
                route_id = route[0]
                route_geometry = json.loads(route[1])
                for route_coords in route_geometry["coordinates"]:
                    route_polygon = Polygon(route_coords)
                    stop_point = Point(stop_lon, stop_lat)
                    # Проверяем, лежит ли точка внутри полигона маршрута
                    if stop_point.within(route_polygon):
                        # Остановка принадлежит маршруту
                        cursor.execute(
                            """
                            INSERT INTO StopRoutes (stop_id, route_id)
                            VALUES (?, ?)
                        """,
                            (stop_id, route_id),
                        )

                # for route_coords in route_geometry["coordinates"]:
                #     if is_on_route(stop_lon, stop_lat, route_coords):
                #         # Вставляем данные в таблицу StopRoutes
                #         cursor.execute(
                #             """
                #             INSERT INTO StopRoutes (stop_id, route_id)
                #             VALUES (?, ?)
                #         """,
                #             (stop_id, route_id),
                #         )
        elif table_name == "Shapes":
            u = 0
            shape_id = properties.get("fid")
            for coords in geometry["coordinates"]:
                for coord in coords:
                    shape_pt_lat = coord[1]
                    shape_pt_lon = coord[0]
                    shape_pt_sequence = u
                    cursor.execute(
                        """
                        INSERT INTO Shapes (shape_id, shape_pt_lat, shape_pt_lon, shape_pt_sequence)
                        VALUES (?, ?, ?, ?)
                    """,
                        (shape_id, shape_pt_lat, shape_pt_lon, shape_pt_sequence),
                    )
                    u = u + 1
        elif table_name == "Trips":
            # Вставляем данные в таблицу Trips
            route_id = properties.get("id")
            service_id = 1
            trip_id = properties.get("fid")
            trip_headsign = properties.get("NAME")
            route_direction = properties["direction"]
            direction_id = direction_map.get(route_direction, 0)
            block_id = 0
            shape_id = properties.get("fid")

            cursor.execute(
                """
                INSERT INTO Trips (route_id, service_id, trip_id, trip_headsign, direction_id, block_id, shape_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    route_id,
                    service_id,
                    trip_id,
                    trip_headsign,
                    direction_id,
                    block_id,
                    shape_id,
                ),
            )


def fill_stop_times(cursor, start_time, time_increment):
    # Получаем данные из таблицы trips
    cursor.execute("SELECT trip_id FROM trips")
    trips = cursor.fetchall()

    for trip in trips:
        trip_id = trip[0]

        # Получаем данные из таблицы StopRoutes
        cursor.execute("SELECT stop_id, route_id FROM StopRoutes")
        stop_routes = cursor.fetchall()
        stop_sequence = 0

        # Заполняем таблицу stop_times
        for stop_route in stop_routes:
            if float(trip_id) == float(stop_route[1]):
                stop_id = stop_route[0]

                # Генерируем времена прибытия и отправления
                arrival_time = (
                    datetime.strptime(start_time, "%H:%M:%S")
                    + timedelta(seconds=stop_sequence * time_increment)
                ).strftime("%H:%M:%S")
                departure_time = (
                    datetime.strptime(start_time, "%H:%M:%S")
                    + timedelta(seconds=(stop_sequence + 1) * time_increment)
                ).strftime("%H:%M:%S")

                # Вставляем данные в таблицу stop_times
                cursor.execute(
                    """
                    INSERT INTO Stop_times (trip_id, arrival_time, departure_time, stop_id, stop_sequence)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (trip_id, arrival_time, departure_time, stop_id, stop_sequence),
                )
                stop_sequence += 1


def write_agency_file():
    agency_id = 0
    agency_name = "unknown"
    agency_timezone = "temp"
    agency_url = "http://"
    cursor.execute(
        """
        INSERT INTO Agency (agency_id, agency_name, agency_timezone, agency_url)
        VALUES (?, ?, ?, ?)
    """,
        (agency_id, agency_name, agency_timezone, agency_url),
    )


def write_Transfers_file():
    cursor.execute("SELECT stop_id FROM Stops")
    stop_ids = cursor.fetchall()
    for stop_id in stop_ids:
        from_stop_id = stop_id[0]  # Extract the stop_id from the tuple
        to_stop_id = stop_id[0]  # Use the same stop_id for from_stop_id and to_stop_id
        transfer_type = 2
        min_transfer_time = 0
        cursor.execute(
            """
            INSERT INTO Transfers (from_stop_id, to_stop_id, transfer_type, min_transfer_time)
            VALUES (?, ?, ?, ?)
            """,
            (from_stop_id, to_stop_id, transfer_type, min_transfer_time),
        )


def write_calendar_file():
    service_id = 1
    date = "20250430"
    cursor.execute(
        """
        INSERT INTO Calendar (service_id, monday, tuesday, wednesday, thursday, friday, saturday, sunday, start_date, end_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            service_id,
            service_id,
            service_id,
            service_id,
            service_id,
            service_id,
            service_id,
            service_id,
            date,
            date,
        ),
    )


# Заполняем таблицу Routes
insert_data("Routes", routs_data)

# Заполняем таблицу Stops
insert_data("Stops", stations_data)

# Заполняем таблицу Shapes
insert_data("Shapes", routs_data)

# Заполняем таблицу Trips
insert_data("Trips", routs_data)

# Заполняем таблицу Transfers
write_Transfers_file()

# Заполняем таблицы agency, calendar
write_agency_file()
write_calendar_file()

# Заполняем таблицу stop_times
fill_stop_times(cursor, "08:00:00", 30)

# Сохраняем изменения
conn.commit()

# Закрываем соединение с базой данных
conn.close()


def remove_duplicate_routes():
    # Подключение к базе данных и получение курсора
    connection = sqlite3.connect(Databasename)
    cursor = connection.cursor()

    # Создание временной таблицы без повторяющихся значений route_id
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS temp_routes AS SELECT * FROM routes GROUP BY route_id"
    )

    # Удаление оригинальной таблицы routes
    cursor.execute("DROP TABLE IF EXISTS routes")

    # Переименование временной таблицы в routes
    cursor.execute("ALTER TABLE temp_routes RENAME TO routes")

    # Сохранение изменений и закрытие соединения с базой данных
    connection.commit()
    connection.close()


def remove_duplicate_stops():
    # Подключение к базе данных и получение курсора
    connection = sqlite3.connect(Databasename)
    cursor = connection.cursor()

    # Создание временной таблицы без повторяющихся значений stop_id
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS temp_stops AS SELECT * FROM stops GROUP BY stop_id"
    )

    # Удаление оригинальной таблицы stops
    cursor.execute("DROP TABLE IF EXISTS stops")

    # Переименование временной таблицы в stops
    cursor.execute("ALTER TABLE temp_stops RENAME TO stops")

    # Сохранение изменений и закрытие соединения с базой данных
    connection.commit()
    connection.close()

def remove_geometry_column():
    # Подключение к базе данных и получение курсора
    connection = sqlite3.connect(Databasename)
    cursor = connection.cursor()

    # Создание временной таблицы без столбца geometry
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS temp_routes AS SELECT route_id, agency_id, route_short_name, route_long_name, route_type, Headway, Сapacity FROM routes"
    )

    # Удаление оригинальной таблицы routes
    cursor.execute("DROP TABLE IF EXISTS routes")

    # Переименование временной таблицы в routes
    cursor.execute("ALTER TABLE temp_routes RENAME TO routes")

    # Сохранение изменений и закрытие соединения с базой данных
    connection.commit()
    connection.close()

def reworkparent():
    conn = sqlite3.connect(Databasename)
    cursor = conn.cursor()
    
    # Создание таблицы stopparen, если её нет
    cursor.execute('''CREATE TABLE IF NOT EXISTS stopparen
                    (id_stop INTEGER PRIMARY KEY,
                    parent_station INTEGER)''')

    # Перенос значений из таблицы stops в таблицу stopparen
    cursor.execute('''INSERT OR IGNORE INTO stopparen (id_stop, parent_station)
                    SELECT id_stop, NULL FROM stops''')

    # Получение максимального значения stop_id из таблицы stops
    cursor.execute('''SELECT MAX(CAST(stop_id AS INTEGER)) FROM stops''')
    max_id = cursor.fetchone()[0]

    # Обновление значений в таблице stopparen для столбца parent_station
    if max_id is not None:
        cursor.execute('''UPDATE stopparen
                        SET parent_station = ? + rowid
                        WHERE parent_station IS NULL''', (max_id,))

    # Создание столбца parent_station в таблице stops
    cursor.execute('''ALTER TABLE stops ADD COLUMN parent_station INTEGER''')

    # Обновление значений в столбце parent_station таблицы stops
    cursor.execute('''UPDATE stops
                    SET parent_station = (SELECT parent_station FROM stopparen WHERE stopparen.id_stop = stops.id_stop)''')

    # Сохранение изменений и закрытие соединения
    conn.commit()
    conn.close()
    
def addparenttostop():
    conn = sqlite3.connect(Databasename)
    cursor = conn.cursor()
    # Получение всех уникальных значений parent_station из таблицы stopparen
    cursor.execute('''SELECT DISTINCT parent_station FROM stopparen''')
    parent_stations = cursor.fetchall()

    # Создание новых записей в таблице stops для каждой parent_station
    for parent_station in parent_stations:
        parent_station = parent_station[0]  # Извлекаем значение из кортежа
        # Получение средних значений для stop_lat и stop_lon
        cursor.execute('''SELECT AVG(stop_lat), AVG(stop_lon) FROM stops WHERE parent_station = ?''', (parent_station,))
        avg_lat, avg_lon = cursor.fetchone()
        
        # Получение highway
        cursor.execute('''SELECT DISTINCT highway FROM stops WHERE parent_station = ?''', (parent_station,))
        highway = cursor.fetchone()[0]
        
        # Создание новой записи в таблице stops
        cursor.execute('''INSERT INTO stops (stop_id, stop_name, stop_lat, stop_lon, highway)
                        VALUES (?, ?, ?, ?, ?)''',
                    (parent_station, f'parent_{parent_station}', avg_lat, avg_lon, highway))

    # Сохранение изменений и закрытие соединения
    conn.commit()
    conn.close()
    
def loctype():
    # Подключение к базе данных SQLite
    conn = sqlite3.connect(Databasename)
    cursor = conn.cursor()

    # Добавление столбца location_type в таблицу stops
    cursor.execute('''ALTER TABLE stops ADD COLUMN location_type INTEGER''')

    # Обновление значений в столбце location_type на основе условий
    cursor.execute('''UPDATE stops
                    SET location_type = CASE
                        WHEN parent_station IS NULL THEN 1
                        ELSE 0
                    END''')

    # Сохранение изменений и закрытие соединения
    conn.commit()
    conn.close()
    
def StoptimParen():
    # Подключение к базе данных SQLite
    conn = sqlite3.connect(Databasename)
    cursor = conn.cursor()

    # Обновление значений столбца stop_id в таблице Stop_times на основе значений из таблицы stops
    cursor.execute('''UPDATE Stop_times
                    SET stop_id = (SELECT parent_station FROM stops WHERE stops.stop_id = Stop_times.stop_id)''')

    # Сохранение изменений и закрытие соединения
    conn.commit()
    conn.close()
    
def test():
    # Подключение к базе данных SQLite
    conn = sqlite3.connect(Databasename)
    cursor = conn.cursor()

    # Обновление значений столбцов from_stop_id и to_stop_id в таблице Transfers на основе значений из таблицы stops
    cursor.execute('''UPDATE Transfers
                    SET from_stop_id = (SELECT parent_station FROM stops WHERE stops.stop_id = Transfers.from_stop_id),
                        to_stop_id = (SELECT parent_station FROM stops WHERE stops.stop_id = Transfers.to_stop_id)''')

    # Сохранение изменений и закрытие соединения
    conn.commit()
    conn.close()
    
def test2():
    # Подключение к базе данных SQLite
    conn = sqlite3.connect(Databasename)
    cursor = conn.cursor()

    # Удаление дубликатов из таблицы Transfers
    cursor.execute('''DELETE FROM Transfers
                    WHERE ROWID NOT IN (
                        SELECT MIN(ROWID)
                        FROM Transfers
                        GROUP BY from_stop_id, to_stop_id
                    )''')

    # Сохранение изменений и закрытие соединения
    conn.commit()
    conn.close()

# Вызов функции удаления повторяющихся stop_id
remove_duplicate_stops()
remove_duplicate_routes()

# Вызов функции удаления столбца geometry
remove_geometry_column()
 
reworkparent()
addparenttostop()
loctype()




# # Удаление таблицы stopparen
    # cursor.execute('''DROP TABLE IF EXISTS stopparen''')

def create_folder(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        print(f"Папка '{folder_name}' создана.")
    else:
        print(f"Папка '{folder_name}' уже существует.")


folder_name = 'export'

# Создаем подключение к базе данных
conn = sqlite3.connect(Databasename)

# Создаем курсор для выполнения SQL-запросов
cursor = conn.cursor()

# Получаем список таблиц в базе данных
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

# Использование функции для создания папки с именем 'export'
create_folder(folder_name)


# Экспорт данных из каждой таблицы в текстовый файл
for table in tables:
    table_name = table[0]

    # Выполняем SQL-запрос для получения данных из таблицы
    cursor.execute(f"SELECT * FROM {table_name}")
    data = cursor.fetchall()

    # Открываем текстовый файл для записи данных
    with open(f"{folder_name}/{table_name}.txt", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter=",")

        # Записываем заголовки столбцов в файл
        writer.writerow([description[0] for description in cursor.description])

        # Записываем данные в файл
        writer.writerows(data)

# Закрываем соединение с базой данных
conn.close()


def create_zip_archive(source_folder, output_filename):
    # Создаем объект ZipFile с указанием имени выходного файла и режима записи 'w'
    with zipfile.ZipFile(output_filename, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(source_folder):
            for file in files:
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, source_folder)
                print(f'Архивация {relative_path}')
                zf.write(full_path, arcname=relative_path)
    
    print('Архив успешно создан.')

current_script_path = __file__

directory_path = os.path.dirname(os.path.abspath(current_script_path))

source_dir = directory_path + '/export'   # Путь к вашей исходной папке
output_file = 'export.zip'           # Имя архива

create_zip_archive(source_dir, output_file)