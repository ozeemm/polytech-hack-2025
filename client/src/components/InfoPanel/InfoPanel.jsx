import './InfoPanel.css'

export default function InfoPanel({ data }) {
    if (!data)
        return

    const translations = {
        "tramway": "Трамвай",
        "bus": "Автобус",
        "minibus": "Маршрутка",
        "trolleybus": "Троллейбус",
    }

    function routeData(data) {
        return (
            <div className='infoPanel'>
                <div className="card">
                    <div className="card-header text-center fw-bold bg-secondary text-white">
                        Маршрут
                    </div>

                    <div className="card-body">
                        Тип транспорта: {translations[data.vehicle_type]}<br/>
                        Маршрут: {data.route}<br/>
                        uuid: {data.uuid}<br/>
                        <hr className='m-1'/>
                        Начальный сигнал: {data.signal_time_from.replace('T', ' ')}<br/>
                        Конечный сигнал: {data.signal_time_to.replace('T', ' ')}<br/>
                        <hr className='m-1'/>
                        Начальная скорость: {Math.round(data.speed_from)} км/ч<br/>
                        Конечная скорость: {Math.round(data.speed_to)} км/ч<br/>
                    </div>
                </div>
            </div>
        )
    }

    function stationData(data) {
        return (
            <div className='infoPanel'>
                <div className="card">
                    <div className="card-header text-center fw-bold bg-secondary text-white">
                        Остановка
                    </div>

                    <div className="card-body">
                        {data.map(r => 
                            <span key={JSON.stringify(r)}>
                                {translations[r[1]]}: {r[0]} <br/>
                            </span>
                        )}
                    </div>
                </div>
            </div>
        )
    }

    if (data.type == 'route') 
        return routeData(data.data.properties)
    
    if (data.type == 'station') 
        return stationData(data.data)
}