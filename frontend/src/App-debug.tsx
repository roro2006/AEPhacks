import './App.css'

// Import components one at a time to find the issue
// Uncomment each one to test

// import GridMap from './components/GridMap'
// import WeatherControls from './components/WeatherControls'
// import AlertDashboard from './components/AlertDashboard'
// import ThresholdAnalysis from './components/ThresholdAnalysis'
// import { fetchLineRatings } from './services/api'
// import { Activity } from 'lucide-react'

function App() {
  return (
    <div className="app-container">
      <header className="app-header">
        <div className="header-content">
          <div className="header-title">
            {/* <Activity size={32} className="header-icon" /> */}
            <div>
              <h1>Grid Real-Time Rating Monitor</h1>
              <p className="header-subtitle">AEP Transmission Planning System</p>
            </div>
          </div>
        </div>
      </header>

      <main className="main-content">
        <div style={{ padding: '2rem', background: 'white', borderRadius: '8px' }}>
          <h2>Debug Mode ✅</h2>
          <p>Basic React and CSS are working!</p>
          <p>Now uncomment imports one by one in App-debug.tsx to find the issue.</p>
        </div>
      </main>
    </div>
  )
}

export default App
