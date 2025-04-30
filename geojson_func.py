import pandas as pd
import matplotlib.cm as cm
import matplotlib.colors as mcolors

from datetime import timedelta
import random

from geopy.distance import geodesic

import geopandas as gpd
import pandas as pd
from shapely.geometry import MultiLineString
from shapely.ops import nearest_points

def generate_geojson(data, mode):
    """
    Генерирует GeoJSON с отрезками маршрутов.
    
    Параметры:
    - df: DataFrame с полями ['signal_time', 'uuid', 'route', 'lat', 'lon', 'speed']
    - mode: 'route' | 'all' | 'uuid' — режим работы
    - route_id: номер маршрута (str/int) для 'route' и 'uuid' режимов
    - uuid: ID ТС для режима 'uuid'
    - output_file: путь к файлу вывода
    - time_limit_min: макс. интервал между точками
    - distance_threshold_km: мин. расстояние между точками (для режима 'all')
    - colormap_name: имя цветовой карты
    """
    
    data = pd.DataFrame(data)

    data['signal_time'] = pd.to_datetime(data['signal_time'])

    geojson_data = {
        "type": "FeatureCollection",
        "features": []
    }

    min_signal_time_delta = 1
    distance_threshold_km = 0.1

    if (mode=='speed'):
        colormap = cm.RdYlGn 
    else:
        colormap = cm.Set1

    if mode == 'speed':
        speed_min = data['speed'].min()
        speed_max = data['speed'].max()
        norm = mcolors.Normalize(vmin=speed_min, vmax=speed_max)

        geojson_data["speed_min"] = float(speed_min)
        geojson_data["speed_max"] = float(speed_max)

        for i in range(len(data) - 1):
            p1, p2 = data.iloc[i], data.iloc[i + 1]

            delta = p2['signal_time'] - p1['signal_time']
            distance = geodesic((p1['lat'], p1['lon']), (p2['lat'], p2['lon'])).kilometers

            if (p1['uuid'] == p2['uuid']) and (delta < timedelta(minutes=min_signal_time_delta)) and (distance > distance_threshold_km):
                speed = p1['speed']
                color = mcolors.to_hex(colormap(norm(speed)))

                geojson_data["features"].append({
                    "type": "Feature",
                    "properties": {
                        "speed_from": float(p1['speed']),
                        "speed_to": float(p2['speed']),
                        "color": color,
                        "signal_time_from": p1['signal_time'].isoformat(),
                        "signal_time_to": p2['signal_time'].isoformat(),
                        "uuid": int(p1['uuid']),
                        "route": str(p1['route']),
                        "vehicle_type": str(p1['vehicle_type'])
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[p1['lon'], p1['lat']], [p2['lon'], p2['lat']]]
                    }
                })

    elif mode == 'routes':
        for route in data['route'].unique():
            for vtype in data[data['route'] == route]['vehicle_type'].unique():
                points = data[(data['route'] == route) & (data['vehicle_type'] == vtype)].sort_values('signal_time')
                color = mcolors.to_hex(colormap(random.random()))

                for i in range(len(points) - 1):
                    p1, p2 = points.iloc[i], points.iloc[i + 1]
                    delta = p2['signal_time'] - p1['signal_time']
                    distance = geodesic((p1['lat'], p1['lon']), (p2['lat'], p2['lon'])).kilometers

                    if (p1['uuid'] == p2['uuid']) and (delta < timedelta(minutes=min_signal_time_delta)) and (distance > distance_threshold_km):
                        geojson_data["features"].append({
                            "type": "Feature",
                            "properties": {
                                "speed_from": float(p1['speed']),
                                "speed_to": float(p2['speed']),
                                "color": color,
                                "signal_time_from": p1['signal_time'].isoformat(),
                                "signal_time_to": p2['signal_time'].isoformat(),
                                "uuid": int(p1["uuid"]),
                                "route": str(p1['route']),
                                "vehicle_type": str(p1['vehicle_type'])
                            },
                            "geometry": {
                                "type": "LineString",
                                "coordinates": [[p1['lon'], p1['lat']], [p2['lon'], p2['lat']]]
                            }
                        })

    elif mode == 'transports':
        for uuid in data['uuid'].unique():
            points = data[data['uuid'] == uuid].sort_values('signal_time')
            color = mcolors.to_hex(colormap(random.random()))

            for i in range(len(points) - 1):
                p1, p2 = points.iloc[i], points.iloc[i + 1]
                delta = p2['signal_time'] - p1['signal_time']

                if (delta < timedelta(minutes=min_signal_time_delta)):
                    geojson_data["features"].append({
                        "type": "Feature",
                        "properties": {
                            "speed_from": float(p1['speed']),
                            "speed_to": float(p2['speed']),
                            "color": color,
                            "signal_time_from": p1['signal_time'].isoformat(),
                            "signal_time_to": p2['signal_time'].isoformat(),
                            "uuid": int(p1["uuid"]),
                            "route": str(p1['route']),
                            "vehicle_type": str(p1['vehicle_type'])
                        },
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [[p1['lon'], p1['lat']], [p2['lon'], p2['lat']]]
                        }
                    })

    return geojson_data




def transfer_nearest_properties(geojson_lines, settings):
    def to_multiline(geom):
        if geom.geom_type == 'LineString':
            return MultiLineString([geom])
        elif geom.geom_type == 'MultiLineString':
            return geom
        else:
            return None

    # Загрузка GeoJSON
    gdf_base = gpd.read_file('Граф Иркутск_link_geojson.geojson')     # Граф УДС
    gdf_target =  gpd.GeoDataFrame.from_features(geojson_lines['features'])

# 3. Назначаешь геометрию явно (если вдруг не подхватилось)
    gdf_target.set_geometry('geometry', inplace=True)


# 3. Устанавливаем CRS (например, EPSG:4326)
    gdf_target.set_crs('EPSG:4326', inplace=True)
    # Приведение геометрий к MultiLineString
    gdf_target['geometry'] = gdf_target['geometry'].apply(to_multiline)

    # Установка CRS
    gdf_base = gdf_base.to_crs(epsg=4326)
    gdf_target = gdf_target.to_crs(epsg=4326)

    # Пространственный индекс
    gdf_target_sindex = gdf_target.sindex

    # Поиск ближайших свойств
    def get_nearest_properties(geom):
        bounds = geom.bounds
        possible_matches_index = list(gdf_target_sindex.intersection(bounds))
        possible_matches = gdf_target.iloc[possible_matches_index]

        nearest_geom = None
        min_distance = float('inf')

        for _, row in possible_matches.iterrows():
            dist = geom.distance(row['geometry'])
            if dist < min_distance:
                min_distance = dist
                nearest_geom = row

        if nearest_geom is not None:
            return {
                "speed_from": float(nearest_geom['speed_from']),
                "speed_to": float(nearest_geom['speed_to']),
                "color": nearest_geom['color'],
                "signal_time_from": nearest_geom['signal_time_from'],
                "signal_time_to": nearest_geom['signal_time_to'],
                "uuid": int(nearest_geom['uuid']),
            }
        return {}

    # Применяем
    properties = gdf_base['geometry'].apply(get_nearest_properties)
    properties_df = pd.json_normalize(properties)

    gdf_result = gdf_base.join(properties_df)
    gdf_result = gpd.GeoDataFrame(gdf_result, geometry='geometry')

    if(not settings["showGraph"]):
        gdf_result = gdf_result[gdf_result['color'].notna()]
    
    geojson = gdf_result.to_json()

    return geojson


def routes_near_each_point(data, radius_m = 50):
    """
    Для каждой координаты (lat_av, lon_av) возвращает список маршрутов с типом транспорта,
    проходящих в радиусе radius_m (в метрах), включая свой маршрут.
    
    Параметры:
    - data: DataFrame с колонками ['lat_av', 'lon_av', 'route', 'vehicle_type']
    - radius_m: радиус в метрах для поиска маршрутов поблизости
    
    Возвращает:
    - Список словарей с полями lat, lon, routes_nearby (список (route, vehicle_type))
    """

    data = pd.DataFrame(data)

    geojson_data = []

    for i, row in data.iterrows():
        lat_i, lon_i = row['lat_av'], row['lon_av']
        nearby_routes = set()

        for j, other in data.iterrows():
            lat_j, lon_j = other['lat_av'], other['lon_av']
            route_j = str(other['route'])
            vtype_j = str(other['vehicle_type'])

            dist = geodesic((lat_i, lon_i), (lat_j, lon_j)).meters
            if dist <= radius_m:
                nearby_routes.add((route_j, vtype_j))

        feature = {
                "routes_nearby": sorted(list(nearby_routes)),  # список (маршрут, тип)
                "coordinates": [lon_i, lat_i]  # Сначала lon, потом lat!
        }

        geojson_data.append(feature)

    return geojson_data

def get_graph():
    # Загрузка GeoJSON
    gdf_base = gpd.read_file('Граф Иркутск_link_geojson.geojson')     # Граф УДС
    gdf_base = gdf_base.to_crs(epsg=4326) 
    geojson = gdf_base.to_json()

    return geojson
