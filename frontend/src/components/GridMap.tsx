import { useEffect, useState } from 'react'
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet'
import { fetchGridTopology } from '../services/api'
import type { RatingResponse, LineRating } from '../services/api'
import { Loader2 } from 'lucide-react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import './GridMap.css'

interface GridMapProps {
  ratings: RatingResponse | null
  loading: boolean
}

const GridMap: React.FC<GridMapProps> = ({ ratings, loading }) => {
  const [topology, setTopology] = useState<any>(null)
  const [selectedLine, setSelectedLine] = useState<LineRating | null>(null)

  useEffect(() => {
    loadTopology()
  }, [])

  const loadTopology = async () => {
    try {
      const data = await fetchGridTopology()
      setTopology(data)
    } catch (err) {
      console.error('Failed to load topology:', err)
    }
  }

  const getLineColor = (lineName: string): string => {
    if (!ratings) return '#999'

    const lineRating = ratings.lines.find(l => l.name === lineName)
    if (!lineRating) return '#999'

    switch (lineRating.stress_level) {
      case 'critical':
        return '#dc2626' // red
      case 'high':
        return '#ea580c' // orange
      case 'caution':
        return '#ca8a04' // yellow/gold
      case 'normal':
      default:
        return '#16a34a' // green
    }
  }

  const getLineWeight = (lineName: string): number => {
    if (!ratings) return 3

    const lineRating = ratings.lines.find(l => l.name === lineName)
    if (!lineRating) return 3

    // Thicker lines for higher voltage
    if (lineRating.voltage_kv >= 138) return 4
    return 3
  }

  const getLineRating = (lineName: string): LineRating | null => {
    if (!ratings) return null
    return ratings.lines.find(l => l.name === lineName) || null
  }

  const onEachFeature = (feature: any, layer: L.Layer) => {
    const lineName = feature.properties.Name
    const lineRating = getLineRating(lineName)

    if (lineRating) {
      // Add hover tooltip
      layer.bindTooltip(
        `<strong>${lineRating.branch_name}</strong><br/>
        Loading: ${lineRating.loading_pct.toFixed(1)}%<br/>
        Rating: ${lineRating.rating_mva.toFixed(1)} MVA`,
        { sticky: true }
      )

      // Add click popup
      layer.on('click', () => {
        setSelectedLine(lineRating)
      })

      // Hover effect
      layer.on('mouseover', function(this: L.Path) {
        this.setStyle({ weight: 6, opacity: 1 })
      })

      layer.on('mouseout', function(this: L.Path) {
        this.setStyle({ weight: getLineWeight(lineName), opacity: 0.8 })
      })
    }
  }

  const lineStyle = (feature: any) => {
    const lineName = feature.properties.Name
    return {
      color: getLineColor(lineName),
      weight: getLineWeight(lineName),
      opacity: 0.8,
    }
  }

  if (!topology) {
    return (
      <div className="map-loading">
        <Loader2 className="spin" size={48} />
        <p>Loading grid topology...</p>
      </div>
    )
  }

  // Hawaii coordinates
  const center: [number, number] = [21.4, -157.9]
  const zoom = 10

  return (
    <div className="grid-map-container">
      {loading && (
        <div className="map-overlay">
          <Loader2 className="spin" size={32} />
          <span>Calculating ratings...</span>
        </div>
      )}

      <MapContainer center={center} zoom={zoom} className="map">
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {topology.lines && (
          <GeoJSON
            data={topology.lines}
            style={lineStyle}
            onEachFeature={onEachFeature}
          />
        )}
      </MapContainer>

      {selectedLine && (
        <div className="line-details-panel">
          <button
            className="close-button"
            onClick={() => setSelectedLine(null)}
          >
            ×
          </button>

          <h3>{selectedLine.branch_name}</h3>

          <div className="detail-grid">
            <div className="detail-row">
              <span className="label">Line ID:</span>
              <span className="value">{selectedLine.name}</span>
            </div>

            <div className="detail-row">
              <span className="label">Voltage:</span>
              <span className="value">{selectedLine.voltage_kv} kV</span>
            </div>

            <div className="detail-row">
              <span className="label">Conductor:</span>
              <span className="value">{selectedLine.conductor}</span>
            </div>

            <div className="detail-row">
              <span className="label">Max Temp (MOT):</span>
              <span className="value">{selectedLine.MOT}°C</span>
            </div>

            <div className="divider"></div>

            <div className="detail-row highlight">
              <span className="label">Current Loading:</span>
              <span className={`value stress-${selectedLine.stress_level}`}>
                {selectedLine.loading_pct.toFixed(1)}%
              </span>
            </div>

            <div className="detail-row">
              <span className="label">Current Flow:</span>
              <span className="value">{selectedLine.flow_mva.toFixed(1)} MVA</span>
            </div>

            <div className="detail-row">
              <span className="label">Dynamic Rating:</span>
              <span className="value">{selectedLine.rating_mva.toFixed(1)} MVA</span>
            </div>

            <div className="detail-row">
              <span className="label">Static Rating:</span>
              <span className="value">{selectedLine.static_rating_mva.toFixed(1)} MVA</span>
            </div>

            <div className="detail-row">
              <span className="label">Margin to Limit:</span>
              <span className={`value ${selectedLine.margin_mva < 0 ? 'stress-critical' : ''}`}>
                {selectedLine.margin_mva.toFixed(1)} MVA
              </span>
            </div>

            <div className="divider"></div>

            <div className="detail-row">
              <span className="label">Connection:</span>
              <span className="value text-sm">{selectedLine.bus0} → {selectedLine.bus1}</span>
            </div>
          </div>
        </div>
      )}

      <div className="map-legend">
        <h4>Line Stress Level</h4>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#16a34a' }}></span>
          <span>Normal (&lt;60%)</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#ca8a04' }}></span>
          <span>Caution (60-90%)</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#ea580c' }}></span>
          <span>High (90-100%)</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#dc2626' }}></span>
          <span>Critical (&gt;100%)</span>
        </div>
      </div>
    </div>
  )
}

export default GridMap
