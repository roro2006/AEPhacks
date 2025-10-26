import { useState, useEffect, useRef } from "react";
import { fetchMapHTML, type WeatherParams } from "../services/api";
import { Loader2, AlertCircle } from "lucide-react";
import "./NetworkMap.css";

interface NetworkMapProps {
  weather: WeatherParams;
}

const NetworkMap: React.FC<NetworkMapProps> = ({ weather }) => {
  const [mapHTML, setMapHTML] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const mapContainerRef = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    loadMap();
  }, [weather]);

  const loadMap = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await fetchMapHTML(weather);
      setMapHTML(data.map_html);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load map");
    } finally {
      setLoading(false);
    }
  };

  // Create blob URL for iframe
  const getMapBlobURL = (): string => {
    if (!mapHTML) return "";
    const blob = new Blob([mapHTML], { type: "text/html" });
    return URL.createObjectURL(blob);
  };

  return (
    <div className="network-map-container">
      {loading && (
        <div className="map-loading-overlay">
          <Loader2 size={48} className="spinner" />
          <p>Generating interactive map...</p>
        </div>
      )}

      {error && (
        <div className="map-error">
          <AlertCircle size={24} />
          <strong>Error:</strong> {error}
        </div>
      )}

      {!loading && !error && mapHTML && (
        <>
          <iframe
            ref={mapContainerRef}
            src={getMapBlobURL()}
            className="map-viewer"
            title="Interactive Grid Map"
            style={{
              position: "fixed",
              top: 0,
              left: 0,
              width: "100%",
              height: "100%",
              border: "none",
              margin: 0,
              padding: 0,
              display: "block",
            }}
          />
        </>
      )}
    </div>
  );
};

export default NetworkMap;
