// Инициализация карты
const map = L.map('map').setView([52.289588, 104.280606], 12);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

const routesData = {
  bus: ["3", "80", "90", "480", "105"],
  tram: ["1", "5", "12", "17"],
  trolley: ["3", "6", "1"],
  miniBus: ["4", "10т", "23", "45", "83"]
};

// DOM элементы
const checkboxes = document.querySelectorAll('.transport-type-checkbox');
const routesContainer = document.getElementById("routes-container");

let geoJsonLayer = null;

function getTypeNameInRussian(type) {
    const names = {
      bus: 'автобусов',
      tram: 'трамваев',
      trolley: 'троллейбусов',
      miniBus: 'маршруток'
    };
    return names[type] || type;
  }

// Функция рендера чекбоксов с маршрутами
function renderRouteCheckboxes(type, routes) {
  const containerId = `${type}-routes`;
  let container = document.getElementById(containerId);

  if (!container) {
    container = document.createElement('div');
    container.id = containerId;
    container.className = 'mb-3';
    
    const header = document.createElement('strong');
    header.textContent = `Выберите маршрут(ы): ${getTypeNameInRussian(type)}`;
    header.className = 'form-label mb-2';
    container.appendChild(header);

    routes.forEach(route => {
      const routeId = `${type}-${route}`;
      const html = `
        <div class="form-check form-check-inline mt-1">
          <input class="form-check-input route-checkbox" type="checkbox" value="${route}" data-type="${type}" id="${routeId}">
          <label class="form-check-label" for="${routeId}">${route}</label>
        </div>
      `;
      container.insertAdjacentHTML('beforeend', html);
    });

    routesContainer.appendChild(container);
  }
}

// Обработчик изменения чекбоксов типа транспорта
checkboxes.forEach(cb => {
  cb.addEventListener('change', function () {
    const type = this.value;
    const container = document.getElementById(`${type}-routes`);

    if (this.checked) {
      // Рендерим чекбоксы маршрутов
      if (!container) {
        renderRouteCheckboxes(type, routesData[type]);
      }
    } else {
      if (container) {
        container.remove(); // Удаляем контейнер с чекбоксами маршрутов
      }
    }
  });
});

// Обработчик кнопки "Получить маршрут"
document.getElementById("route_id_button").addEventListener("click", async (e) => {
  e.preventDefault();

  const selectedRoutes = [];

  // Собираем все выбранные маршруты
  const checkedBoxes = document.querySelectorAll('.route-checkbox:checked');
  checkedBoxes.forEach(box => {
    const routeNum = box.value;
    const routeType = box.dataset.type;
    selectedRoutes.push({ routeNum, routeType });
  });

  if (selectedRoutes.length === 0) {
    alert("Выберите хотя бы один маршрут.");
    return;
  }

  try {
    const response = await axios.post("http://127.0.0.1:5000/", {
      RouteIDs: selectedRoutes.map(r => r.routeNum)
    });

    const geojsonData = response.data;

    if (geoJsonLayer) {
      map.removeLayer(geoJsonLayer);
    }

    // Добавляем GeoJSON со стилем по типу
    geoJsonLayer = L.geoJSON(geojsonData, {
      style: function (feature) {
        // Предположим, что feature.properties.type — это тип транспорта от сервера
        const type = feature.properties?.type || 'default';

        return {
          color: routeTypeColors[type] || '#777',
          weight: 4,
          opacity: 1
        };
      },
      onEachFeature: function (feature, layer) {
        const name = feature.properties?.name || 'Без названия';
        layer.bindPopup(name);
      }
    }).addTo(map);

    if (geojsonData.features.length > 0) {
      map.fitBounds(geoJsonLayer.getBounds());
    }

  } catch (error) {
    console.error("Ошибка при получении данных маршрута:", error);
    alert("Не удалось получить данные маршрута.");
  }
});