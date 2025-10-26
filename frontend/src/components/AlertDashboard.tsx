import type { RatingResponse } from "../services/api";
import { AlertTriangle, TrendingUp, Activity, CheckCircle } from "lucide-react";
import "./AlertDashboard.css";

interface AlertDashboardProps {
  ratings: RatingResponse | null;
  loading: boolean;
}

const AlertDashboard: React.FC<AlertDashboardProps> = ({
  ratings,
  loading,
}) => {
  if (loading) {
    return (
      <div className="alert-dashboard">
        <div className="dashboard-header">
          <AlertTriangle size={20} />
          <h2>System Alerts</h2>
        </div>
        <div className="loading-state">Calculating...</div>
      </div>
    );
  }

  if (!ratings) {
    return (
      <div className="alert-dashboard">
        <div className="dashboard-header">
          <AlertTriangle size={20} />
          <h2>System Alerts</h2>
        </div>
        <div className="empty-state">No data available</div>
      </div>
    );
  }

  const { summary } = ratings;

  const getHealthStatus = () => {
    if (summary.overloaded_lines > 0) return "critical";
    if (summary.high_stress_lines > 0) return "high";
    if (summary.caution_lines > 0) return "caution";
    return "normal";
  };

  const healthStatus = getHealthStatus();

  return (
    <div className="alert-dashboard">
      <div className="dashboard-header">
        <AlertTriangle size={20} />
        <h2>System Alerts</h2>
      </div>

      <div className={`health-status status-${healthStatus}`}>
        <Activity size={24} />
        <div>
          <div className="status-label">Grid Health Status</div>
          <div className="status-value">
            {healthStatus === "critical" &&
              "CRITICAL - Immediate Action Required"}
            {healthStatus === "high" && "HIGH STRESS - Monitor Closely"}
            {healthStatus === "caution" && "CAUTION - Watch for Changes"}
            {healthStatus === "normal" && "NORMAL - All Systems Healthy"}
          </div>
        </div>
      </div>

      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-label">Total Lines</div>
          <div className="metric-value">{summary.total_lines}</div>
        </div>

        <div className="metric-card critical">
          <div className="metric-label">Overloaded</div>
          <div className="metric-value">{summary.overloaded_lines}</div>
        </div>

        <div className="metric-card high">
          <div className="metric-label">High Stress</div>
          <div className="metric-value">{summary.high_stress_lines}</div>
        </div>

        <div className="metric-card caution">
          <div className="metric-label">Caution</div>
          <div className="metric-value">{summary.caution_lines}</div>
        </div>
      </div>

      <div className="summary-stats">
        <div className="stat-row">
          <span>Average Loading:</span>
          <strong>{summary.avg_loading.toFixed(1)}%</strong>
        </div>
        <div className="stat-row">
          <span>Maximum Loading:</span>
          <strong className={summary.max_loading >= 100 ? "text-critical" : ""}>
            {summary.max_loading.toFixed(1)}%
          </strong>
        </div>
      </div>

      {summary.critical_lines.length > 0 && (
        <div className="critical-lines-section">
          <h3>
            <TrendingUp size={16} />
            Top Lines Requiring Attention
          </h3>

          <div className="critical-lines-list">
            {summary.critical_lines.map((line, idx) => (
              <div key={line.name} className="critical-line-item">
                <div className="line-rank">#{idx + 1}</div>
                <div className="line-info">
                  <div className="line-name">{line.branch_name}</div>
                  <div className="line-id">{line.name}</div>
                </div>
                <div className="line-stats">
                  <div
                    className={`loading-badge ${
                      line.loading_pct >= 100
                        ? "critical"
                        : line.loading_pct >= 90
                        ? "high"
                        : "caution"
                    }`}
                  >
                    {line.loading_pct.toFixed(1)}%
                  </div>
                  <div className="margin-value">
                    {line.margin_mva >= 0 ? "+" : ""}
                    {line.margin_mva.toFixed(1)} MVA
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {summary.overloaded_lines === 0 && summary.high_stress_lines === 0 && (
        <div className="all-clear">
          <CheckCircle size={48} />
          <p>All transmission lines operating within safe limits</p>
        </div>
      )}

      {summary.overloaded_lines > 0 && (
        <div className="recommendations">
          <h3>Recommended Actions</h3>
          <ul>
            <li>
              Immediately review overloaded lines for emergency interventions
            </li>
            <li>Consider load shedding or generation redispatch options</li>
            <li>Prepare contingency plans for potential line outages</li>
            <li>Monitor weather forecasts for condition changes</li>
          </ul>
        </div>
      )}
    </div>
  );
};

export default AlertDashboard;
