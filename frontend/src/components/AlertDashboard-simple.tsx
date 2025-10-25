import type { RatingResponse } from '../services/api'
import { AlertTriangle, Activity, CheckCircle } from 'lucide-react'

interface AlertDashboardProps {
  ratings: RatingResponse | null
  loading: boolean
}

const AlertDashboard: React.FC<AlertDashboardProps> = ({ ratings, loading }) => {
  if (loading) {
    return (
      <div style={{ background: 'white', padding: '1.5rem', borderRadius: '8px', marginTop: '1rem' }}>
        <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
          <AlertTriangle size={20} />
          System Alerts
        </h2>
        <div style={{ textAlign: 'center', color: '#6b7280' }}>Calculating...</div>
      </div>
    )
  }

  if (!ratings) {
    return (
      <div style={{ background: 'white', padding: '1.5rem', borderRadius: '8px', marginTop: '1rem' }}>
        <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
          <AlertTriangle size={20} />
          System Alerts
        </h2>
        <div style={{ textAlign: 'center', color: '#6b7280' }}>No data available</div>
      </div>
    )
  }

  const { summary } = ratings

  const getHealthColor = () => {
    if (summary.overloaded_lines > 0) return '#dc2626'
    if (summary.high_stress_lines > 0) return '#ea580c'
    if (summary.caution_lines > 0) return '#ca8a04'
    return '#16a34a'
  }

  const getHealthStatus = () => {
    if (summary.overloaded_lines > 0) return 'CRITICAL - Immediate Action Required'
    if (summary.high_stress_lines > 0) return 'HIGH STRESS - Monitor Closely'
    if (summary.caution_lines > 0) return 'CAUTION - Watch for Changes'
    return 'NORMAL - All Systems Healthy'
  }

  return (
    <div style={{ background: 'white', padding: '1.5rem', borderRadius: '8px', marginTop: '1rem' }}>
      <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
        <AlertTriangle size={20} />
        System Alerts
      </h2>

      <div style={{
        padding: '1rem',
        borderRadius: '8px',
        background: summary.overloaded_lines > 0 ? '#fef2f2' : '#f0fdf4',
        color: getHealthColor(),
        marginBottom: '1rem',
        display: 'flex',
        alignItems: 'center',
        gap: '1rem'
      }}>
        <Activity size={24} />
        <div>
          <div style={{ fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase' }}>Grid Health Status</div>
          <div style={{ fontWeight: 700 }}>{getHealthStatus()}</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem', marginBottom: '1rem' }}>
        <div style={{ padding: '1rem', background: '#f9fafb', borderRadius: '8px' }}>
          <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>Total Lines</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{summary.total_lines}</div>
        </div>
        <div style={{ padding: '1rem', background: summary.overloaded_lines > 0 ? '#fef2f2' : '#f9fafb', borderRadius: '8px' }}>
          <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>Overloaded</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 700, color: summary.overloaded_lines > 0 ? '#dc2626' : '#111827' }}>
            {summary.overloaded_lines}
          </div>
        </div>
        <div style={{ padding: '1rem', background: summary.high_stress_lines > 0 ? '#fff7ed' : '#f9fafb', borderRadius: '8px' }}>
          <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>High Stress</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 700, color: summary.high_stress_lines > 0 ? '#ea580c' : '#111827' }}>
            {summary.high_stress_lines}
          </div>
        </div>
        <div style={{ padding: '1rem', background: '#f9fafb', borderRadius: '8px' }}>
          <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>Caution</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{summary.caution_lines}</div>
        </div>
      </div>

      <div style={{ padding: '1rem', background: '#f9fafb', borderRadius: '8px', marginBottom: '1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
          <span>Average Loading:</span>
          <strong>{summary.avg_loading.toFixed(1)}%</strong>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span>Maximum Loading:</span>
          <strong style={{ color: summary.max_loading >= 100 ? '#dc2626' : '#111827' }}>
            {summary.max_loading.toFixed(1)}%
          </strong>
        </div>
      </div>

      {summary.critical_lines.length > 0 && (
        <div>
          <h3 style={{ fontSize: '0.875rem', marginBottom: '0.75rem' }}>Top Lines Requiring Attention</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {summary.critical_lines.slice(0, 5).map((line, idx) => (
              <div key={line.name} style={{
                padding: '0.75rem',
                background: '#f9fafb',
                borderRadius: '6px',
                fontSize: '0.8125rem'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontWeight: 600 }}>#{idx + 1} {line.name}</div>
                    <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>{line.branch_name}</div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{
                      fontWeight: 700,
                      color: line.loading_pct >= 100 ? '#dc2626' : line.loading_pct >= 90 ? '#ea580c' : '#ca8a04'
                    }}>
                      {line.loading_pct.toFixed(1)}%
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                      {line.margin_mva >= 0 ? '+' : ''}{line.margin_mva.toFixed(1)} MVA
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {summary.overloaded_lines === 0 && summary.high_stress_lines === 0 && (
        <div style={{ textAlign: 'center', padding: '2rem', color: '#16a34a' }}>
          <CheckCircle size={48} style={{ margin: '0 auto' }} />
          <p style={{ marginTop: '0.75rem', color: '#6b7280' }}>All transmission lines operating within safe limits</p>
        </div>
      )}
    </div>
  )
}

export default AlertDashboard
