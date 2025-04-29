import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.jsx'

import 'bootstrap/dist/css/bootstrap.css';

import '@bopen/leaflet-area-selection/dist/style.css';

//import 'select2/src/scss/core'
//import 'select2-bootstrap-5-theme'
// import "bootstrap/dist/js/bootstrap"

import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap/dist/js/bootstrap'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
