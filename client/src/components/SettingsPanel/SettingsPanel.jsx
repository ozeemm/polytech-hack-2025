import { useEffect, useState } from 'react'
import axios from 'axios'
import './SettingsPanel.css'

export default function SettingsPanel({ onSettingsChanged }) {
    const [connectToGraph, setConnectToGraph] = useState(false)
    const [showGraph, setShowGraph] = useState(false)
    const [showStations, setShowStations] = useState(true)

    const [isOpen, setIsOpen] = useState(false)

    useEffect(() => {
        const settings = {
            'connectToGraph': connectToGraph,
            'showGraph': showGraph,
            'showStations': showStations
        }

        onSettingsChanged(settings)
    }, [connectToGraph, showGraph, showStations, onSettingsChanged])

    async function onExportClick(){
        const response = await axios.get("http://127.0.0.1:5000/api/gtfs_download", {
            responseType: 'blob'
        })

        const blob = new Blob([response.data], { type: response.headers['content-type'] })
        const url = window.URL.createObjectURL(blob)
        
        const a = document.createElement('a');
        a.href = url;
        a.download = 'GTFS.zip'; // задай имя файла
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
    }

    return (
        <div>
            <div>
                <button
                    className={`openButtonSettings ${isOpen ? 'open' : ''}`}
                    onClick={() => setIsOpen(!isOpen)}
                >
                    <i className={`bi bi-gear-fill openButtonIcon ${isOpen ? 'open' : ''}`}></i>
                </button>
            </div>

            <div className={`sidebar p-3 ${isOpen ? 'open' : ''}`}>
                <div className="card mb-3">
                    <div className="card-header text-center fw-bold bg-secondary text-white">
                        Граф УДС
                    </div>
                    <div className="card-body">
                        <div className='form-check mb-2'>
                            <input
                                className='form-check-input'
                                type="checkbox"
                                id="connect-to-graph-checkbox"
                                checked={connectToGraph}
                                onChange={(e) => setConnectToGraph(!connectToGraph)} />
                            <label className='form-check-label' htmlFor='connect-to-graph-checkbox'>Связать маршруты с графом</label>
                        </div>
                        <div className='form-check mb-2'>
                            <input
                                className='form-check-input'
                                type="checkbox"
                                id="show-graph-checkbox"
                                checked={showGraph}
                                onChange={(e) => setShowGraph(!showGraph)} />
                            <label className='form-check-label' htmlFor='show-graph-checkbox'>Отобразить граф</label>
                        </div>
                    </div>
                </div>

                <div className="card mb-3">
                    <div className="card-header text-center fw-bold bg-secondary text-white">
                        Остановки
                    </div>
                    <div className="card-body">
                        <div className='form-check mb-2'>
                            <input
                                className='form-check-input'
                                type="checkbox"
                                id="show-stations-checkbox"
                                checked={showStations}
                                onChange={(e) => setShowStations(!showStations)} />
                            <label className='form-check-label' htmlFor='show-stations-checkbox'>Показывать остановки</label>
                        </div>

                        <button className="btn btn-success w-100 mt-3" onClick={onExportClick}>
                            Экспорт в GTFS
                        </button>
                    </div>
                </div>
            </div>
        </div>
    )
}