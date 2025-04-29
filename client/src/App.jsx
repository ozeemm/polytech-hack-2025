import { MapContainer, TileLayer, GeoJSON, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css';

import { useRef, useState } from 'react'
import './App.css'
import axios from 'axios'
import './components/MapFilters/MapFilters'
import MapFilters from './components/MapFilters/MapFilters';
import Loader from './components/Loader/Loader';

export default function App() {
    const mapRef = useRef(null)
    const geoJsonLayerRef = useRef(null)

    const [routeId, setRouteId] = useState('')
    const [geoJsonData, setGeoJsonData] = useState(null)
    const [hoveredFeature, setHoveredFeature] = useState(null)
    const [isLoading, setIsLoading] = useState(false)

    const center = [52.289588, 104.280606];
    const zoom = 13;

    // Стиль GeoJSON слоя
    function style(feature) {
        const isHovered = hoveredFeature && hoveredFeature === feature

        return {
            fillColor: '#3388ff',
            weight: isHovered ? 5 : 3,
            opacity: 1,
            color: feature.properties.color || 'red', // Цвет линии
            fillOpacity: 0.7
        }
    }

    // Обработка каждого объекта GeoJSON
    function onEachFeature(feature, layer) {
        if (feature.properties && feature.properties.name)
            layer.bindPopup(feature.properties.name)

        if(feature.properties){
            const tooltipText = Object.entries(feature.properties)
                                    .map(([key, value]) => `${key}: ${value}`)
                                    .join('<br>')
            // const tooltipText = `
            //     color: ${feature.properties.color}<br>
            //     speed: ${Math.floor(feature.properties.speed * 100) / 100}`

            layer.bindTooltip(tooltipText, { sticky: true })
        }

        layer.on({
            mouseover: () => {
                setHoveredFeature(feature)
                layer.bringToFront()
                layer.openTooltip()
            },

            mouseout: () => {
                setHoveredFeature(null)
                layer.closeTooltip()
            }
        })
    }

    async function fetchRouteData(requestBody){
        setIsLoading(true)
        
        const response = await axios.post("http://127.0.0.1:5000/api/Filter", requestBody);
        setGeoJsonData(response.data)
        
        setIsLoading(false)
    }

    return (
        <div>
            <Loader isLoading={isLoading}/>

            <MapFilters onGetRoutesClick={fetchRouteData}/>

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
            </MapContainer>
        </div>
    )
}