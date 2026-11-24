import { createRoot } from 'react-dom/client'
import App from './App'
import './index.css'

// Bewust géén StrictMode: dubbele development-effects zouden de live
// zuinigheidsindicator (zero-AI-acties) onterecht opblazen.
createRoot(document.getElementById('root')!).render(<App />)
