import { useState, useEffect } from "react";
import "./App.css";
import {
  Loader2,
  Map,
  Table,
  Filter,
  X,
  BarChart3,
  MessageCircle,
} from "lucide-react";
import {
  fetchLineRatings,
  type WeatherParams,
  type RatingResponse,
  type OutageSimulationResult,
} from "./services/api";
// import WeatherControls from "./components/WeatherControls-simple";
import AlertDashboard from "./components/AlertDashboard-simple";
import Chatbot from "./components/Chatbot";
import NetworkMap from "./components/NetworkMap";
import OutageAnalysis from "./components/OutageAnalysis";
import WeatherAnalysis from "./components/WeatherAnalysis";
import LoadScalingAnalysis from "./components/LoadScalingAnalysis";

type ViewTab = "map" | "table" | "analysis" | "chat";
type FilterType =
  | "all"
  | "critical"
  | "high"
  | "caution"
  | "normal"
  | "az"
  | "za";

function App() {
  const [activeTab, setActiveTab] = useState<ViewTab>("map");
  const [filter, setFilter] = useState<FilterType>("all");
  const [selectedLine, setSelectedLine] = useState<string | null>(null);
  const [analysisSubTab, setAnalysisSubTab] = useState<'weather' | 'outage' | 'loading'>('weather');
  const [weather, setWeather] = useState<WeatherParams>({
    ambient_temp: 25,
    wind_speed: 2.0,
    wind_angle: 90,
    sun_time: 12,
    date: "12 Jun",
    elevation: 1000,
    latitude: 27,
    emissivity: 0.8,
    absorptivity: 0.8,
    direction: "EastWest",
    atmosphere: "Clear",
  });

  const [ratings, setRatings] = useState<RatingResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [outageResult, setOutageResult] =
    useState<OutageSimulationResult | null>(null);

  useEffect(() => {
    loadRatings();
  }, []);

  const loadRatings = async (weatherParams?: WeatherParams) => {
    const params = weatherParams || weather;
    setLoading(true);
    setError(null);

    try {
      const data = await fetchLineRatings(params);
      setRatings(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load ratings. Make sure backend is running on http://localhost:5001"
      );
    } finally {
      setLoading(false);
    }
  };

  const handleWeatherChange = (newWeather: Partial<WeatherParams>) => {
    console.log("[App] Weather change requested:", newWeather);
    const updated = { ...weather, ...newWeather };
    console.log("[App] Updated weather params:", updated);
    setWeather(updated);
    loadRatings(updated);
  };

  return (
    <div className="app-container">
      {/* Full-screen background map */}
      <div className="map-background">
        <NetworkMap weather={weather} outageResult={outageResult} />
      </div>

      {/* Error notification */}
      {error && (
        <div className="error-notification">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Floating sidebar overlay with tabs */}
      <aside className="sidebar-overlay">
        {/* Tab Navigation */}
        <div className="sidebar-tabs">
          <button
            className={`sidebar-tab ${activeTab === "map" ? "active" : ""}`}
            onClick={() => setActiveTab("map")}
          >
            <Map size={18} />
            Console
          </button>
          <button
            className={`sidebar-tab ${activeTab === "table" ? "active" : ""}`}
            onClick={() => setActiveTab("table")}
          >
            <Table size={18} />
            Data
          </button>
          <button
            className={`sidebar-tab ${
              activeTab === "analysis" ? "active" : ""
            }`}
            onClick={() => setActiveTab("analysis")}
          >
            <BarChart3 size={18} />
            Analysis
          </button>
          <button
            className={`sidebar-tab ${activeTab === "chat" ? "active" : ""}`}
            onClick={() => setActiveTab("chat")}
          >
            <MessageCircle size={18} />
            Chat
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === "map" && (
          <>
            {/* <WeatherControls
              weather={weather}
              onChange={handleWeatherChange}
              loading={loading}
            /> */}
            <AlertDashboard ratings={ratings} loading={loading} />
          </>
        )}

        {activeTab === "table" && (
          <div className="data-table-view">
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "1rem",
              }}
            >
              <h2 style={{ fontSize: "1.25rem", margin: 0 }}>
                Transmission Lines
              </h2>

              {/* Filter Dropdown */}
              <div style={{ position: "relative" }}>
                <Filter
                  size={16}
                  style={{
                    position: "absolute",
                    left: "0.75rem",
                    top: "50%",
                    transform: "translateY(-50%)",
                    pointerEvents: "none",
                    color: "#9ca3af",
                  }}
                />
                <select
                  value={filter}
                  onChange={(e) => setFilter(e.target.value as FilterType)}
                  style={{
                    background: "rgba(255, 255, 255, 0.1)",
                    border: "1px solid rgba(255, 255, 255, 0.2)",
                    borderRadius: "8px",
                    padding: "0.5rem 2rem 0.5rem 2.5rem",
                    color: "#f5f5f7",
                    fontSize: "0.875rem",
                    fontWeight: 500,
                    cursor: "pointer",
                    appearance: "none",
                  }}
                >
                  <option value="all">All</option>
                  <option value="critical">Critical</option>
                  <option value="high">High</option>
                  <option value="caution">Caution</option>
                  <option value="normal">Normal</option>
                  <option value="az">A → Z</option>
                  <option value="za">Z → A</option>
                </select>
                <div
                  style={{
                    position: "absolute",
                    right: "0.75rem",
                    top: "50%",
                    transform: "translateY(-50%)",
                    pointerEvents: "none",
                    color: "#9ca3af",
                  }}
                >
                  ▼
                </div>
              </div>
            </div>

            {loading && (
              <div style={{ textAlign: "center", padding: "2rem" }}>
                <Loader2 size={32} className="spinner" />
                <p style={{ marginTop: "1rem", color: "#9ca3af" }}>
                  Calculating line ratings...
                </p>
              </div>
            )}

            {!loading &&
              ratings &&
              (() => {
                // Filter and sort lines
                let filteredLines = [...ratings.lines];

                switch (filter) {
                  case "critical":
                    filteredLines = filteredLines.filter(
                      (l) => l.loading_pct >= 100
                    );
                    break;
                  case "high":
                    filteredLines = filteredLines.filter(
                      (l) => l.loading_pct >= 90 && l.loading_pct < 100
                    );
                    break;
                  case "caution":
                    filteredLines = filteredLines.filter(
                      (l) => l.loading_pct >= 60 && l.loading_pct < 90
                    );
                    break;
                  case "normal":
                    filteredLines = filteredLines.filter(
                      (l) => l.loading_pct < 60
                    );
                    break;
                  case "az":
                    filteredLines.sort((a, b) => a.name.localeCompare(b.name));
                    break;
                  case "za":
                    filteredLines.sort((a, b) => b.name.localeCompare(a.name));
                    break;
                  default:
                    // Sort by loading (highest first) by default
                    filteredLines.sort((a, b) => b.loading_pct - a.loading_pct);
                }

                return (
                  <div
                    style={{
                      maxHeight: "calc(100vh - 280px)",
                      overflowY: "auto",
                    }}
                  >
                    {filteredLines.length === 0 ? (
                      <div
                        style={{
                          textAlign: "center",
                          padding: "2rem",
                          color: "#9ca3af",
                        }}
                      >
                        No lines match this filter
                      </div>
                    ) : (
                      filteredLines.map((line) => (
                        <div
                          key={line.name}
                          onClick={() => setSelectedLine(line.name)}
                          style={{
                            background: "rgba(255, 255, 255, 0.05)",
                            padding: "1rem",
                            borderRadius: "8px",
                            marginBottom: "0.75rem",
                            border: "1px solid rgba(255, 255, 255, 0.1)",
                            cursor: "pointer",
                            transition: "all 0.2s",
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.background =
                              "rgba(255, 255, 255, 0.08)";
                            e.currentTarget.style.borderColor =
                              "rgba(255, 255, 255, 0.2)";
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.background =
                              "rgba(255, 255, 255, 0.05)";
                            e.currentTarget.style.borderColor =
                              "rgba(255, 255, 255, 0.1)";
                          }}
                        >
                          <div
                            style={{ fontWeight: 600, marginBottom: "0.5rem" }}
                          >
                            {line.name}
                          </div>
                          <div
                            style={{
                              fontSize: "0.875rem",
                              color: "#9ca3af",
                              marginBottom: "0.5rem",
                            }}
                          >
                            {line.branch_name}
                          </div>
                          <div
                            style={{
                              display: "grid",
                              gridTemplateColumns: "1fr 1fr",
                              gap: "0.5rem",
                            }}
                          >
                            <div>
                              <span
                                style={{
                                  color: "#9ca3af",
                                  fontSize: "0.75rem",
                                }}
                              >
                                Loading:
                              </span>{" "}
                              <span
                                style={{
                                  fontWeight: 700,
                                  color:
                                    line.loading_pct >= 100
                                      ? "#ef4444"
                                      : line.loading_pct >= 90
                                      ? "#f97316"
                                      : line.loading_pct >= 60
                                      ? "#eab308"
                                      : "#10b981",
                                }}
                              >
                                {line.loading_pct.toFixed(1)}%
                              </span>
                            </div>
                            <div>
                              <span
                                style={{
                                  color: "#9ca3af",
                                  fontSize: "0.75rem",
                                }}
                              >
                                Flow:
                              </span>{" "}
                              {line.flow_mva.toFixed(1)} MVA
                            </div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                );
              })()}
          </div>
        )}

        {activeTab === "analysis" && (
          <div className="data-table-view" style={{ padding: 0 }}>
            {/* Analysis Sub-tabs */}
            <div
              style={{
                display: "flex",
                gap: "0.5rem",
                padding: "1rem 1rem 0 1rem",
                borderBottom: "1px solid rgba(255, 255, 255, 0.1)",
                marginBottom: "1rem",
              }}
            >
              <button
                onClick={() => setAnalysisSubTab("weather")}
                style={{
                  padding: "0.5rem 1rem",
                  background:
                    analysisSubTab === "weather"
                      ? "rgba(59, 130, 246, 0.2)"
                      : "transparent",
                  border:
                    analysisSubTab === "weather"
                      ? "1px solid rgba(59, 130, 246, 0.4)"
                      : "1px solid rgba(255, 255, 255, 0.1)",
                  borderRadius: "6px",
                  color: analysisSubTab === "weather" ? "#60a5fa" : "#9ca3af",
                  fontSize: "0.875rem",
                  fontWeight: 600,
                  cursor: "pointer",
                  transition: "all 0.2s",
                }}
              >
                Weather Analysis
              </button>
              <button
                onClick={() => setAnalysisSubTab("outage")}
                style={{
                  padding: "0.5rem 1rem",
                  background:
                    analysisSubTab === "outage"
                      ? "rgba(59, 130, 246, 0.2)"
                      : "transparent",
                  border:
                    analysisSubTab === "outage"
                      ? "1px solid rgba(59, 130, 246, 0.4)"
                      : "1px solid rgba(255, 255, 255, 0.1)",
                  borderRadius: "6px",
                  color: analysisSubTab === "outage" ? "#60a5fa" : "#9ca3af",
                  fontSize: "0.875rem",
                  fontWeight: 600,
                  cursor: "pointer",
                  transition: "all 0.2s",
                }}
              >
                Outage Simulation
              </button>
              <button
                onClick={() => setAnalysisSubTab('loading')}
                style={{
                  padding: '0.5rem 1rem',
                  background: analysisSubTab === 'loading' ? 'rgba(59, 130, 246, 0.2)' : 'transparent',
                  border: analysisSubTab === 'loading' ? '1px solid rgba(59, 130, 246, 0.4)' : '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '6px',
                  color: analysisSubTab === 'loading' ? '#60a5fa' : '#9ca3af',
                  fontSize: '0.875rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
              >
                Daily Load Scaling
              </button>
            </div>

            {/* Sub-tab Content */}
            <div
              style={{
                padding: "0 1rem 1rem 1rem",
                height: "calc(100% - 60px)",
                overflowY: "auto",
              }}
            >
              {analysisSubTab === "weather" && (
                <WeatherAnalysis
                  weather={weather}
                  ratings={ratings}
                  onWeatherChange={handleWeatherChange}
                  loading={loading}
                />
              )}
              {analysisSubTab === "outage" && (
                <OutageAnalysis onOutageComplete={setOutageResult} />
              )}
              {analysisSubTab === 'loading' && (
                <LoadScalingAnalysis />
              )}
            </div>
          </div>
        )}

        {activeTab === "chat" && (
          <div className="chat-tab-container">
            <Chatbot weather={weather} inSidebar={true} />
          </div>
        )}
      </aside>

      {/* Line Detail Pane */}
      {selectedLine && ratings && (
        <div
          className="line-detail-overlay"
          onClick={() => setSelectedLine(null)}
        >
          <div
            className="line-detail-pane"
            onClick={(e) => e.stopPropagation()}
          >
            {(() => {
              const lineData = ratings.lines.find(
                (l) => l.name === selectedLine
              );
              if (!lineData) return null;

              return (
                <>
                  <div className="line-detail-header">
                    <div>
                      <h2
                        style={{
                          fontSize: "1.5rem",
                          margin: 0,
                          marginBottom: "0.5rem",
                        }}
                      >
                        {lineData.name}
                      </h2>
                      <p
                        style={{
                          margin: 0,
                          color: "#9ca3af",
                          fontSize: "0.875rem",
                        }}
                      >
                        {lineData.branch_name}
                      </p>
                    </div>
                    <button
                      onClick={() => setSelectedLine(null)}
                      style={{
                        background: "rgba(255, 255, 255, 0.1)",
                        border: "1px solid rgba(255, 255, 255, 0.2)",
                        borderRadius: "8px",
                        width: "36px",
                        height: "36px",
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        color: "#f5f5f7",
                      }}
                    >
                      <X size={20} />
                    </button>
                  </div>

                  <div className="line-detail-content">
                    {/* Status Badge */}
                    <div
                      style={{
                        padding: "1rem",
                        background:
                          lineData.loading_pct >= 100
                            ? "rgba(239, 68, 68, 0.1)"
                            : lineData.loading_pct >= 90
                            ? "rgba(249, 115, 22, 0.1)"
                            : lineData.loading_pct >= 60
                            ? "rgba(234, 179, 8, 0.1)"
                            : "rgba(16, 185, 129, 0.1)",
                        borderRadius: "12px",
                        border: `2px solid ${
                          lineData.loading_pct >= 100
                            ? "#ef4444"
                            : lineData.loading_pct >= 90
                            ? "#f97316"
                            : lineData.loading_pct >= 60
                            ? "#eab308"
                            : "#10b981"
                        }`,
                        marginBottom: "1.5rem",
                      }}
                    >
                      <div
                        style={{
                          fontSize: "0.75rem",
                          textTransform: "uppercase",
                          fontWeight: 600,
                          marginBottom: "0.5rem",
                          color: "#9ca3af",
                        }}
                      >
                        Status
                      </div>
                      <div
                        style={{
                          fontSize: "1.25rem",
                          fontWeight: 700,
                          color:
                            lineData.loading_pct >= 100
                              ? "#ef4444"
                              : lineData.loading_pct >= 90
                              ? "#f97316"
                              : lineData.loading_pct >= 60
                              ? "#eab308"
                              : "#10b981",
                        }}
                      >
                        {lineData.stress_level.toUpperCase()}
                      </div>
                    </div>

                    {/* Key Metrics Grid */}
                    <div
                      style={{
                        display: "grid",
                        gridTemplateColumns: "1fr 1fr",
                        gap: "1rem",
                        marginBottom: "1.5rem",
                      }}
                    >
                      <div
                        style={{
                          background: "rgba(255, 255, 255, 0.05)",
                          padding: "1rem",
                          borderRadius: "10px",
                        }}
                      >
                        <div
                          style={{
                            fontSize: "0.75rem",
                            color: "#9ca3af",
                            marginBottom: "0.5rem",
                          }}
                        >
                          Loading
                        </div>
                        <div style={{ fontSize: "1.75rem", fontWeight: 700 }}>
                          {lineData.loading_pct.toFixed(1)}%
                        </div>
                      </div>
                      <div
                        style={{
                          background: "rgba(255, 255, 255, 0.05)",
                          padding: "1rem",
                          borderRadius: "10px",
                        }}
                      >
                        <div
                          style={{
                            fontSize: "0.75rem",
                            color: "#9ca3af",
                            marginBottom: "0.5rem",
                          }}
                        >
                          Rating
                        </div>
                        <div style={{ fontSize: "1.75rem", fontWeight: 700 }}>
                          {lineData.rating_mva.toFixed(1)}{" "}
                          <span style={{ fontSize: "1rem", color: "#9ca3af" }}>
                            MVA
                          </span>
                        </div>
                      </div>
                      <div
                        style={{
                          background: "rgba(255, 255, 255, 0.05)",
                          padding: "1rem",
                          borderRadius: "10px",
                        }}
                      >
                        <div
                          style={{
                            fontSize: "0.75rem",
                            color: "#9ca3af",
                            marginBottom: "0.5rem",
                          }}
                        >
                          Flow
                        </div>
                        <div style={{ fontSize: "1.75rem", fontWeight: 700 }}>
                          {lineData.flow_mva.toFixed(1)}{" "}
                          <span style={{ fontSize: "1rem", color: "#9ca3af" }}>
                            MVA
                          </span>
                        </div>
                      </div>
                      <div
                        style={{
                          background: "rgba(255, 255, 255, 0.05)",
                          padding: "1rem",
                          borderRadius: "10px",
                        }}
                      >
                        <div
                          style={{
                            fontSize: "0.75rem",
                            color: "#9ca3af",
                            marginBottom: "0.5rem",
                          }}
                        >
                          Margin
                        </div>
                        <div
                          style={{
                            fontSize: "1.75rem",
                            fontWeight: 700,
                            color:
                              lineData.margin_mva < 0 ? "#ef4444" : "#10b981",
                          }}
                        >
                          {lineData.margin_mva >= 0 ? "+" : ""}
                          {lineData.margin_mva.toFixed(1)}{" "}
                          <span style={{ fontSize: "1rem", color: "#9ca3af" }}>
                            MVA
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Additional Details */}
                    <div
                      style={{
                        background: "rgba(255, 255, 255, 0.05)",
                        padding: "1.25rem",
                        borderRadius: "12px",
                      }}
                    >
                      <h3
                        style={{
                          fontSize: "1rem",
                          marginBottom: "1rem",
                          fontWeight: 600,
                        }}
                      >
                        Line Details
                      </h3>
                      <div
                        style={{
                          display: "flex",
                          flexDirection: "column",
                          gap: "0.75rem",
                        }}
                      >
                        <div
                          style={{
                            display: "flex",
                            justifyContent: "space-between",
                          }}
                        >
                          <span style={{ color: "#9ca3af" }}>Conductor:</span>
                          <span style={{ fontWeight: 500 }}>
                            {lineData.conductor || "N/A"}
                          </span>
                        </div>
                        <div
                          style={{
                            display: "flex",
                            justifyContent: "space-between",
                          }}
                        >
                          <span style={{ color: "#9ca3af" }}>
                            MOT:
                          </span>
                          <span style={{ fontWeight: 500 }}>
                            {lineData.MOT?.toFixed(1) || "N/A"}°C
                          </span>
                        </div>
                        <div
                          style={{
                            display: "flex",
                            justifyContent: "space-between",
                          }}
                        >
                          <span style={{ color: "#9ca3af" }}>Voltage:</span>
                          <span style={{ fontWeight: 500 }}>
                            {lineData.voltage_kv?.toFixed(2) || "N/A"} kV
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </>
              );
            })()}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
