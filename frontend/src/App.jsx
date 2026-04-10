import { useState, useEffect } from "react"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"

const API_URL = "http://127.0.0.1:8000"
const WS_URL = "ws://127.0.0.1:8000/ws"

function App() {
  const [violations, setViolations] = useState([])
  const [stats, setStats] = useState(null)
  const [connected, setConnected] = useState(false)

  // Rafraîchissement automatique toutes les 3 secondes
  useEffect(() => {
    const fetchData = () => {
      fetch(`${API_URL}/violations`)
        .then(res => res.json())
        .then(data => setViolations(data.violations))

      fetch(`${API_URL}/stats`)
        .then(res => res.json())
        .then(data => setStats(data))
    }

    fetchData()
    const interval = setInterval(fetchData, 3000)
    return () => clearInterval(interval)
  }, [])

  // Connexion WebSocket
  useEffect(() => {
    const ws = new WebSocket(WS_URL)
    ws.onopen = () => {
      setConnected(true)
      console.log("WebSocket connecté ✅")
    }
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === "violation") {
        setViolations(prev => [data.violation, ...prev].slice(0, 50))
        setStats(prev => prev ? {
          ...prev,
          total_violations: prev.total_violations + 1
        } : prev)
      }
    }
    ws.onclose = () => setConnected(false)
    return () => ws.close()
  }, [])

  const resetDatabase = () => {
    fetch(`${API_URL}/reset`, { method: "DELETE" })
      .then(() => {
        setViolations([])
        setStats({ total_objects: 0, total_violations: 0, by_type: [] })
        alert("Base de données réinitialisée ✅")
      })
  }

  const getViolationColor = (type) => {
    switch(type) {
      case "loitering": return "#f59e0b"
      case "fall_detected": return "#ef4444"
      case "parking_violation": return "#f97316"
      default: return "#6b7280"
    }
  }

  const getViolationEmoji = (type) => {
    switch(type) {
      case "loitering": return "🟡"
      case "fall_detected": return "🔴"
      case "parking_violation": return "🟠"
      default: return "⚪"
    }
  }

  return (
    <div style={{ fontFamily: "Arial", padding: "20px", background: "#111", minHeight: "100vh", color: "white" }}>

      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "30px" }}>
        <h1 style={{ margin: 0, fontSize: "24px" }}>🎥 VSI — Vidéo Surveillance Intelligente</h1>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <button onClick={resetDatabase} style={{
            padding: "6px 14px",
            borderRadius: "20px",
            background: "#dc2626",
            color: "white",
            border: "none",
            cursor: "pointer",
            fontSize: "14px"
          }}>
            🗑️ Reset démo
          </button>
          <span style={{
            padding: "6px 14px",
            borderRadius: "20px",
            background: "#16a34a",
            fontSize: "14px"
          }}>
            🟢 En ligne
          </span>
        </div>
      </div>

      {/* Stats */}
      {stats && (
        <div style={{ display: "flex", gap: "20px", marginBottom: "30px" }}>
          <div style={{ background: "#1f2937", padding: "20px", borderRadius: "12px", flex: 1, textAlign: "center" }}>
            <div style={{ fontSize: "36px", fontWeight: "bold", color: "#60a5fa" }}>{stats.total_objects}</div>
            <div style={{ color: "#9ca3af", marginTop: "5px" }}>Personnes détectées</div>
          </div>
          <div style={{ background: "#1f2937", padding: "20px", borderRadius: "12px", flex: 1, textAlign: "center" }}>
            <div style={{ fontSize: "36px", fontWeight: "bold", color: "#f87171" }}>{stats.total_violations}</div>
            <div style={{ color: "#9ca3af", marginTop: "5px" }}>Violations totales</div>
          </div>
          <div style={{ background: "#1f2937", padding: "20px", borderRadius: "12px", flex: 1, textAlign: "center" }}>
            <div style={{ fontSize: "36px", fontWeight: "bold", color: "#fbbf24" }}>
              {stats.by_type?.find(t => t.type === "loitering")?.count || 0}
            </div>
            <div style={{ color: "#9ca3af", marginTop: "5px" }}>Loitering</div>
          </div>
          <div style={{ background: "#1f2937", padding: "20px", borderRadius: "12px", flex: 1, textAlign: "center" }}>
            <div style={{ fontSize: "36px", fontWeight: "bold", color: "#f87171" }}>
              {stats.by_type?.find(t => t.type === "fall_detected")?.count || 0}
            </div>
            <div style={{ color: "#9ca3af", marginTop: "5px" }}>Chutes</div>
          </div>
        </div>
      )}

      {/* Graphique */}
      {stats?.by_type && stats.by_type.length > 0 && (
        <div style={{ background: "#1f2937", padding: "20px", borderRadius: "12px", marginBottom: "30px" }}>
          <h2 style={{ margin: "0 0 20px 0", fontSize: "18px" }}>📊 Violations par type</h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={stats.by_type}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="type" stroke="#9ca3af" />
              <YAxis stroke="#9ca3af" />
              <Tooltip contentStyle={{ background: "#111", border: "none" }} />
              <Bar dataKey="count" fill="#60a5fa" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Liste des violations */}
      <div style={{ background: "#1f2937", padding: "20px", borderRadius: "12px" }}>
        <h2 style={{ margin: "0 0 20px 0", fontSize: "18px" }}>⚠️ Dernières violations</h2>
        {violations.length === 0 ? (
          <p style={{ color: "#9ca3af" }}>Aucune violation détectée pour l'instant...</p>
        ) : (
          violations.map((v, i) => (
            <div key={i} style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              padding: "12px",
              marginBottom: "8px",
              borderRadius: "8px",
              background: "#111",
              borderLeft: `4px solid ${getViolationColor(v.type)}`
            }}>
              <div>
                <span style={{ marginRight: "10px" }}>{getViolationEmoji(v.type)}</span>
                <span style={{ color: getViolationColor(v.type), fontWeight: "bold" }}>
                  {v.type.toUpperCase()}
                </span>
                <span style={{ color: "#9ca3af", marginLeft: "10px" }}>
                  ID:{v.track_id}
                </span>
                {v.zone && (
                  <span style={{ 
                    color: "#60a5fa", 
                    marginLeft: "10px",
                    fontSize: "12px",
                    background: "#1e3a5f",
                    padding: "2px 8px",
                    borderRadius: "10px"
                  }}>
                    📍 {v.zone}
                  </span>
                )}
              </div>
              <span style={{ color: "#6b7280", fontSize: "13px" }}>
                {new Date(v.timestamp).toLocaleTimeString()}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default App