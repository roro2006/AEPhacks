import type { RatingResponse } from "../services/api";
import { AlertTriangle, Activity, CheckCircle } from "lucide-react";

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
      <div
        style={{
          background: "rgba(20, 20, 22, 0.85)",
          backdropFilter: "blur(10px)",
          WebkitBackdropFilter: "blur(10px)",
          padding: "1.5rem",
          borderRadius: "14px",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          boxShadow: "0 8px 32px rgba(0, 0, 0, 0.4)",
        }}
      >
        <h2
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.5rem",
            marginBottom: "1rem",
          }}
        >
          <AlertTriangle size={20} />
          System Alerts
        </h2>
        <div style={{ textAlign: "center", color: "#6b7280" }}>
          Calculating...
        </div>
      </div>
    );
  }

  if (!ratings) {
    return (
      <div
        style={{
          background: "rgba(20, 20, 22, 0.85)",
          backdropFilter: "blur(10px)",
          WebkitBackdropFilter: "blur(10px)",
          padding: "1.5rem",
          borderRadius: "14px",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          boxShadow: "0 8px 32px rgba(0, 0, 0, 0.4)",
        }}
      >
        <h2
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.5rem",
            marginBottom: "1rem",
          }}
        >
          <AlertTriangle size={20} />
          System Alerts
        </h2>
        <div style={{ textAlign: "center", color: "#6b7280" }}>
          No data available
        </div>
      </div>
    );
  }

  const { summary } = ratings;

  const getHealthColor = () => {
    if (summary.overloaded_lines > 0) return "#dc2626";
    if (summary.high_stress_lines > 0) return "#ea580c";
    if (summary.caution_lines > 0) return "#ca8a04";
    return "#16a34a";
  };

  const getHealthBackground = () => {
    if (summary.overloaded_lines > 0) return "rgba(220, 38, 38, 0.15)";
    if (summary.high_stress_lines > 0) return "rgba(234, 88, 12, 0.15)";
    if (summary.caution_lines > 0) return "rgba(202, 138, 4, 0.15)";
    return "rgba(22, 163, 74, 0.15)";
  };

  const getHealthBorder = () => {
    if (summary.overloaded_lines > 0) return "2px solid rgba(220, 38, 38, 0.5)";
    if (summary.high_stress_lines > 0) return "2px solid rgba(234, 88, 12, 0.5)";
    if (summary.caution_lines > 0) return "2px solid rgba(202, 138, 4, 0.5)";
    return "2px solid rgba(22, 163, 74, 0.5)";
  };

  const getHealthStatus = () => {
    if (summary.overloaded_lines > 0)
      return "CRITICAL - Immediate Action Required";
    if (summary.high_stress_lines > 0) return "HIGH STRESS - Monitor Closely";
    if (summary.caution_lines > 0) return "CAUTION - Watch for Changes";
    return "NORMAL - All Systems Healthy";
  };

  const getAnalysis = () => {
    if (summary.overloaded_lines > 0) {
      return `${summary.overloaded_lines} line${summary.overloaded_lines > 1 ? 's are' : ' is'} operating beyond capacity. Immediate load reduction or switching recommended to prevent equipment damage.`;
    }
    if (summary.high_stress_lines > 0) {
      return `${summary.high_stress_lines} line${summary.high_stress_lines > 1 ? 's are' : ' is'} experiencing high stress levels. Monitor closely and prepare contingency plans.`;
    }
    if (summary.caution_lines > 0) {
      return `${summary.caution_lines} line${summary.caution_lines > 1 ? 's are' : ' is'} approaching thermal limits. Weather changes or load increases could escalate stress levels.`;
    }
    return `All transmission lines operating within normal parameters. System capacity is adequate for current conditions.`;
  };

  return (
    <div
      style={{
        background: "rgba(20, 20, 22, 0.85)",
        backdropFilter: "blur(10px)",
        WebkitBackdropFilter: "blur(10px)",
        padding: "1.5rem",
        borderRadius: "14px",
        border: "1px solid rgba(255, 255, 255, 0.08)",
        boxShadow: "0 8px 32px rgba(0, 0, 0, 0.4)",
      }}
    >
      <h2
        style={{
          display: "flex",
          alignItems: "center",
          gap: "0.5rem",
          marginBottom: "1rem",
        }}
      >
        <AlertTriangle size={20} />
        System Alerts
      </h2>

      <div
        style={{
          padding: "1.25rem",
          borderRadius: "12px",
          background: getHealthBackground(),
          border: getHealthBorder(),
          marginBottom: "1rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "1rem" }}>
          <Activity size={24} color={getHealthColor()} />
          <div>
            <div
              style={{
                fontSize: "0.75rem",
                fontWeight: 600,
                textTransform: "uppercase",
                color: "#9ca3af",
                marginBottom: "0.25rem",
              }}
            >
              Grid Health Status
            </div>
            <div style={{ fontWeight: 700, fontSize: "1.1rem", color: getHealthColor() }}>
              {getHealthStatus()}
            </div>
          </div>
        </div>

        {/* Analysis Section */}
        <div
          style={{
            background: "rgba(0, 0, 0, 0.2)",
            padding: "0.875rem",
            borderRadius: "8px",
            fontSize: "0.875rem",
            lineHeight: "1.5",
            color: "#e5e5e7",
          }}
        >
          <div style={{ fontWeight: 600, marginBottom: "0.5rem", color: "#f5f5f7" }}>
            📊 Analysis
          </div>
          {getAnalysis()}
        </div>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(2, 1fr)",
          gap: "1rem",
          marginBottom: "1rem",
        }}
      >
        <div
          style={{
            padding: "1rem",
            background: "rgba(25, 25, 27, 0.9)",
            borderRadius: "8px",
          }}
        >
          <div style={{ fontSize: "0.75rem", color: "#6b7280" }}>
            Total Lines
          </div>
          <div style={{ fontSize: "1.5rem", fontWeight: 700 }}>
            {summary.total_lines}
          </div>
        </div>
        <div
          style={{
            padding: "1rem",
            background:
              summary.overloaded_lines > 0
                ? "#fef2f2"
                : "rgba(25, 25, 27, 0.9)",
            borderRadius: "8px",
          }}
        >
          <div style={{ fontSize: "0.75rem", color: "#6b7280" }}>
            Overloaded
          </div>
          <div
            style={{
              fontSize: "1.5rem",
              fontWeight: 700,
              color: summary.overloaded_lines > 0 ? "#d55653" : "#f5f5f7",
            }}
          >
            {summary.overloaded_lines}
          </div>
        </div>
        <div
          style={{
            padding: "1rem",
            background:
              summary.high_stress_lines > 0
                ? "#fff7ed"
                : "rgba(25, 25, 27, 0.9)",
            borderRadius: "8px",
          }}
        >
          <div style={{ fontSize: "0.75rem", color: "#f5f5f7" }}>
            High Stress
          </div>
          <div
            style={{
              fontSize: "1.5rem",
              fontWeight: 700,
              color: summary.high_stress_lines > 0 ? "#d55653" : "#f5f5f7",
            }}
          >
            {summary.high_stress_lines}
          </div>
        </div>
        <div
          style={{
            padding: "1rem",
            background: "rgba(25, 25, 27, 0.9)",
            borderRadius: "8px",
          }}
        >
          <div style={{ fontSize: "0.75rem", color: "#6b7280" }}>Caution</div>
          <div style={{ fontSize: "1.5rem", fontWeight: 700 }}>
            {summary.caution_lines}
          </div>
        </div>
      </div>

      <div
        style={{
          padding: "1rem",
          background: "rgba(25, 25, 27, 0.9)",
          borderRadius: "8px",
          marginBottom: "1rem",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            marginBottom: "0.5rem",
          }}
        >
          <span>Average Loading:</span>
          <strong>{summary.avg_loading.toFixed(1)}%</strong>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <span>Maximum Loading:</span>
          <strong
            style={{
              color: summary.max_loading >= 100 ? "#dc2626" : "#111827",
            }}
          >
            {summary.max_loading.toFixed(1)}%
          </strong>
        </div>
      </div>

      {summary.critical_lines.length > 0 && (
        <div>
          <h3 style={{ fontSize: "0.875rem", marginBottom: "0.75rem" }}>
            Top Lines Requiring Attention
          </h3>
          <div
            style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}
          >
            {summary.critical_lines.slice(0, 5).map((line, idx) => (
              <div
                key={line.name}
                style={{
                  padding: "0.75rem",
                  background: "rgba(25, 25, 27, 0.9)",
                  borderRadius: "6px",
                  fontSize: "0.8125rem",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 600 }}>
                      #{idx + 1} {line.name}
                    </div>
                    <div style={{ fontSize: "0.75rem", color: "#6b7280" }}>
                      {line.branch_name}
                    </div>
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <div
                      style={{
                        fontWeight: 700,
                        color:
                          line.loading_pct >= 100
                            ? "#dc2626"
                            : line.loading_pct >= 90
                            ? "#ea580c"
                            : "#ca8a04",
                      }}
                    >
                      {line.loading_pct.toFixed(1)}%
                    </div>
                    <div style={{ fontSize: "0.75rem", color: "#6b7280" }}>
                      {line.margin_mva >= 0 ? "+" : ""}
                      {line.margin_mva.toFixed(1)} MVA
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {summary.overloaded_lines === 0 && summary.high_stress_lines === 0 && (
        <div style={{ textAlign: "center", padding: "2rem", color: "#16a34a" }}>
          <CheckCircle size={48} style={{ margin: "0 auto" }} />
          <p style={{ marginTop: "0.75rem", color: "#6b7280" }}>
            All transmission lines operating within safe limits
          </p>
        </div>
      )}
    </div>
  );
};

export default AlertDashboard;
