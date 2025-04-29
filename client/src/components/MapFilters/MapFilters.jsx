import { useEffect, useState } from 'react'
import axios from 'axios'
import './MapFilters.css'

export default function MapFilters({ onGetRoutesClick }) {
    const [transports, setTransports] = useState([])
    const [monthPeriods, setMonthPeriods] = useState([])

    const colorModes = [
        {
            key: "speed",
            title: "Скорость"
        },
        {
            key: "routes",
            title: "Маршруты"
        },
        {
            key: "transports",
            title: "Транспортные средства"
        }
    ]

    const [checkedTransports, setCheckedTransports] = useState([])
    const [checkedRoutes, setCheckedRoutes] = useState([])
    const [checkedMonths, setCheckedMonths] = useState([])
    const [timeFrom, setTimeFrom] = useState("00:00")
    const [timeTo, setTimeTo] = useState("23:59")
    const [colorMode, setColorMode] = useState("speed")

    const [isDataFetched, setIsDataFetched] = useState(false)

    function transportCheckbox(transport) {
        return (
            <div className="form-check" key={transport.key}>
                <input
                    className="form-check-input transport-type-checkbox"
                    type="checkbox"
                    value={transport.key}
                    id={transport.key}
                    checked={checkedTransports.includes(transport.key)}
                    onChange={() => handleTransportChange(transport.key)}
                />
                <label className="form-check-label" htmlFor={transport.key}>{transport.title}</label>

                {/* Чекбоксы маршрутов */}
                {checkedTransports.includes(transport.key) &&
                    <div className='d-flex flex-column'>
                        {transport.routes.map(r => routeCheckbox(transport, r))}
                    </div>
                }
            </div>
        )
    }

    function routeCheckbox(transport, r) {
        const id = transport.key + "-" + r

        return (
            <div className='form-check' key={id}>
                <input
                    className="form-check-input transport-type-checkbox"
                    type="checkbox"
                    value={r}
                    id={id}
                    checked={ checkedRoutes.includes(transport.key + "_" + r) }
                    onChange={(e) => handleRoutesChange(transport.key, r)}
                />
                <label className='form-check-label' htmlFor={id}>{r}</label>
            </div>
        )
    }

    function handleMonthChange(date){
        setCheckedMonths(prev => {
            if(prev.includes(date))
                return prev.filter(d => d != date)
            else
                return [...prev, date]
        })
    }

    function handleTransportChange(transport){
        setCheckedTransports(prev => {
            if(prev.includes(transport)){
                setCheckedRoutes(_prev => _prev.filter(r => !r.startsWith(transport)))

                return prev.filter(t => t != transport)
            }
            else
                return [...prev, transport]
        })
    }

    function handleRoutesChange(transport, route){
        setCheckedRoutes(prev => {
            const routeStr = transport + "_" + route

            if(prev.includes(routeStr))
                return prev.filter(r => r != routeStr)
            else
                return [...prev, routeStr]
        })
    }

    function monthPeriodTitle(period) {
        const formatter = new Intl.DateTimeFormat('ru', { month: 'short' })
        const monthName = formatter.format(new Date(2000, period.month-1, 1))
        const monthNameCapitalized = monthName[0].toUpperCase() + monthName.slice(1)

        return `${monthNameCapitalized} ${period.year} г.`
    }

    async function fetchData() {
        if(isDataFetched)
            return
        
        await fetchDates()
        await fetchTransports()
        setIsDataFetched(true)
    }

    async function fetchDates(){
        const response = await axios.get('http://127.0.0.1:5000/api/getDatesFilters')
        setMonthPeriods(response.data)
        console.log("Got dates!")
    }

    async function fetchTransports(){
        const response = await axios.get('http://127.0.0.1:5000/api/getTransportFilters')
        setTransports(response.data)
        console.log("Got transports!")
    }

    async function getFilteredGeoJson(e){
        e.preventDefault()

        const requestBody = {
            'routes': {},
            'dates': checkedMonths,
            'timeStart': timeFrom,
            'timeEnd': timeTo,
            'colorMode': colorMode
        }

        transports.forEach(t => {
            requestBody.routes[t.key] = []
        })

        checkedRoutes.forEach(r => {
            const splitted = r.split('_')
            const transport = splitted[0]
            const route = splitted[1]

            requestBody.routes[transport].push(route)
        });

        onGetRoutesClick(requestBody)
    }

    fetchData()

    return (
        <div className='sidebar p-3'>
            <form onSubmit={getFilteredGeoJson}>
                {/* Чекбоксы для типов транспорта */}
                <div className='card'>
                    <div className="card-header text-center fw-bold bg-primary text-white">
                        Выбор транспорта и маршрутов
                    </div>
                    <div className="card-body">
                        <div id="transport-types-container" className="mb-3">
                            <div className="d-flex flex-column gap-2" id="transport-checkboxes">
                                {transports.map(transport => transportCheckbox(transport))}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Месяцы */}
                <div className="card mb-3">
                    <div className="card-header text-center fw-bold bg-secondary text-white">
                        Месяцы
                    </div>
                    <div className="card-body">
                        {monthPeriods.map((period, index) =>
                            <div className="form-check mb-2" key={index}>
                                <input 
                                    className="form-check-input" 
                                    type="checkbox" 
                                    id={index} 
                                    checked={ checkedMonths.includes(`${period.year}-${period.month}`) }
                                    onChange={(e) => handleMonthChange(`${period.year}-${period.month}`)}
                                />
                                <label className="form-check-label" htmlFor={index}>{monthPeriodTitle(period)}</label>
                            </div>
                        )}
                    </div>
                </div>

                {/* Время */}
                <div className="card mb-3">
                    <div className="card-header text-center fw-bold bg-secondary text-white">
                        Время
                    </div>
                    <div className="card-body">
                        <div className="mb-2">
                            <label htmlFor="time-from" className="form-label">От:</label>
                            <input
                                type="time"
                                className="form-control"
                                id="time-from"
                                value={timeFrom}
                                onChange={(e) => setTimeFrom(e.target.value)}
                            />
                        </div>
                        <div>
                            <label htmlFor="time-to" className="form-label">До:</label>
                            <input
                                type="time"
                                className="form-control"
                                id="time-to"
                                value={timeTo}
                                onChange={(e) => setTimeTo(e.target.value)}
                            />
                        </div>
                    </div>
                </div>

                {/* Цвета */}
                <div className="card mb-3">
                    <div className="card-header text-center fw-bold bg-secondary text-white">
                        Выделение цветом
                    </div>
                    <div className="card-body">
                        {colorModes.map(mode =>
                            <div className="form-check mb-2" key={mode.key}>
                                <input
                                    className="form-check-input"
                                    type="radio"
                                    name="color-mode"
                                    id={"color-" + mode.key}
                                    value={mode.key}
                                    checked={colorMode == mode.key}
                                    onChange={(e) => setColorMode(e.target.value)}
                                />
                                <label className="form-check-label" htmlFor={"color-" + mode.key}>{mode.title}</label>
                            </div>
                        )}
                    </div>
                </div>

                {/* Кнопка */}
                <button id="route_id_button" type="submit" className="btn btn-success w-100 mt-3">
                    Получить маршрут
                </button>
            </form>
        </div>
    )
}