// Инициализация карты с центром в Иркутске
const map = L.map('map').setView([52.289588, 104.280606], 12);

// Добавляем слой OpenStreetMap
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

const route_id_input = document.getElementById('route_id_input');
const route_id_button = document.getElementById('route_id_button');

// Создание стиля для GeoJSON слоя
function style(feature) {
    return {
        fillColor: '#3388ff',
        weight: 3,
        opacity: 1,
        color: feature.properties.color || 'red', // Цвет линии
        fillOpacity: 0.7
    };
}

// Функция для обработки каждого объекта в GeoJSON
function onEachFeature(feature, layer) {
    if (feature.properties && feature.properties.name) {
        layer.bindPopup(feature.properties.name);
    }
}

let geoJsonLayer = null

route_id_button.addEventListener('click', async () => {
    const route_id = route_id_input.value
    const response = await axios.post("http://127.0.0.1:5000/", {
        "RouteID": route_id
    })

    const geojsonData = response.data

    if(geoJsonLayer)
        map.removeLayer(geoJsonLayer)

    geoJsonLayer = L.geoJSON(geojsonData, {
        style: style,
        onEachFeature: onEachFeature
    }).addTo(map)
})