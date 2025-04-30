import { MapContainer, TileLayer, GeoJSON, Marker, Popup, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css';

import { useRef, useState } from 'react'
import './App.css'
import axios from 'axios'
import './components/MapFilters/MapFilters'

import MapFilters from './components/MapFilters/MapFilters';
import Loader from './components/Loader/Loader';
import SettingsPanel from './components/SettingsPanel/SettingsPanel';
import InfoPanel from './components/InfoPanel/InfoPanel';

export default function App() {
    const mapRef = useRef(null)
    const geoJsonLayerRef = useRef(null)
    const markerRef = useRef(null)

    const [geoJsonData, setGeoJsonData] = useState(null)
    const [stationsData, setStationsData] = useState(null)
    const [hoveredFeature, setHoveredFeature] = useState(null)
    const [hoveredData, setHoveredData] = useState(null)

    const [isLoading, setIsLoading] = useState(false)
    let settings = {}

    const center = [52.289588, 104.280606];
    const zoom = 13;

    // Стиль GeoJSON слоя
    function style(feature) {
        const isHovered = hoveredFeature && hoveredFeature === feature

        return {
            fillColor: '#3388ff',
            weight: isHovered ? 5 : 3,
            opacity: 1,
            color: feature.properties.color || 'gray', // Цвет линии
            fillOpacity: 0.7
        }
    }

    // Обработка каждого объекта GeoJSON
    function onEachFeature(feature, layer) {
        if (feature.properties && feature.properties.name)
            layer.bindPopup(feature.properties.name)

        layer.on({
            mouseover: () => {
                setHoveredFeature(feature)
                layer.bringToFront()
                
                if(feature.properties.color)
                    setHoveredData({ type: 'route', data: feature })
            },

            mouseout: () => {
                setHoveredFeature(null)
                setHoveredData(null)
            }
        })
    }

    async function fetchRouteData(filterParams) {
        setIsLoading(true)

        console.log(settings)

        const requestBody = {
            'filter': filterParams,
            'settings': settings
        }
        const response = await axios.post("http://127.0.0.1:5000/api/Filter", requestBody);
        setGeoJsonData(response.data)

        if (settings.showStations) {
            const stationsResponse = await axios.post("http://127.0.0.1:5000/api/StationFilter", { routes: filterParams.routes })
            setStationsData(stationsResponse.data)
        }
        else{
            setStationsData(null)
        }

        setIsLoading(false)
    }

    function handleSettingsChanged(data) {
        settings = data
    }

    return (
        <div>
            <Loader isLoading={isLoading} />

            <MapFilters onGetRoutesClick={fetchRouteData} />
            <SettingsPanel onSettingsChanged={handleSettingsChanged} />
            <InfoPanel data={hoveredData}/>

            <MapContainer center={center} zoom={zoom} className='map' ref={mapRef}>
                <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' />

                {geoJsonData && (
                    <GeoJSON
                        key={JSON.stringify(geoJsonData)}
                        data={geoJsonData}
                        style={style}
                        onEachFeature={onEachFeature}
                        ref={geoJsonLayerRef}
                    />
                )}

                {stationsData && (
                    stationsData.map(station => 
                        <Marker
                            key={JSON.stringify(station)}
                            position={[station.coordinates[1], station.coordinates[0]]}
                            ref={markerRef}
                            eventHandlers={{
                                mouseover: () => setHoveredData({ type: 'station', data: station.routes_nearby }),
                                mouseout: () => setHoveredData(null)
                            }}
                        />
                    )
                )}
            </MapContainer>
        </div>
    )
}