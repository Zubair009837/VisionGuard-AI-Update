import AIInsights from "../components/ai/AIInsights";
import Loader from "../components/Loader";
import { useEffect, useState } from "react";
import api from "../services/api";

import CameraPieChart from "../components/charts/CameraPieChart";
import PerformanceChart from "../components/charts/PerformanceChart";
import StorageChart from "../components/charts/StorageChart";

// ==========================================================
// VISIONGUARD AI
// PREMIUM NVR SECURITY OPERATIONS CENTER
// ==========================================================

function Dashboard() {

  // ========================================================
  // DASHBOARD DATA
  // ========================================================

  const [dashboard, setDashboard] = useState({
    total: 0,
    online: 0,
    offline: 0,
    nvr: 0,
  });

  const [displayStats, setDisplayStats] = useState({
    total: 0,
    online: 0,
    offline: 0,
    nvr: 0,
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [lastUpdated, setLastUpdated] = useState("");
  const [nvrHealth, setNvrHealth] = useState([]);
  const [liveAlerts, setLiveAlerts] = useState([]);

  // ========================================================
  // ROTATING CONTENT
  // ========================================================

  const [tickerIndex, setTickerIndex] = useState(0);
  const [visualIndex, setVisualIndex] = useState(0);
  const [orbitRotation, setOrbitRotation] = useState(0);

  // ========================================================
  // TICKER MESSAGES
  // ========================================================

  const tickerMessages = [
    "VISIONGUARD AI • LIVE SECURITY MONITORING ACTIVE",
    "AI ENGINE • CONTINUOUS CAMERA HEALTH ANALYSIS",
    "NETWORK • REAL-TIME NVR CONNECTIVITY MONITORING",
    "SECURITY CORE • AUTOMATED ALERT DETECTION ACTIVE",
    "CCTV MATRIX • LIVE INFRASTRUCTURE SURVEILLANCE",
    "OPERATIONS • ALL MONITORING SYSTEMS ONLINE",
  ];

  // ========================================================
  // VISUAL MESSAGES
  // ========================================================

  const visualMessages = [
    {
      icon: "🛰️",
      title: "LIVE SURVEILLANCE",
      text: "Real-time CCTV infrastructure monitoring",
    },
    {
      icon: "🤖",
      title: "AI ANALYTICS",
      text: "Intelligent camera health analysis",
    },
    {
      icon: "🛡️",
      title: "SECURITY CORE",
      text: "Automated threat and failure detection",
    },
    {
      icon: "📡",
      title: "NETWORK MATRIX",
      text: "Continuous NVR connectivity analysis",
    },
    {
      icon: "🎥",
      title: "CAMERA GRID",
      text: "Enterprise CCTV monitoring environment",
    },
    {
      icon: "⚡",
      title: "MISSION CONTROL",
      text: "Centralized security operations monitoring",
    },
  ];

  // ========================================================
  // LOAD DASHBOARD
  // ========================================================

  async function loadDashboard() {
    try {
      const response = await api.get("/dashboard");

      const data = response.data || {};

      const newDashboard = {
        total: Number(data.total || 0),
        online: Number(data.online || 0),
        offline: Number(data.offline || 0),
        nvr: Number(data.nvr || 0),
      };

      setDashboard(newDashboard);

      setLastUpdated(
        new Date().toLocaleTimeString()
      );

      setError(false);

    } catch (err) {
      console.error("Dashboard API Error:", err);
      setError(true);

    } finally {
      setLoading(false);
    }
  }

  async function loadHealthAndAlerts() {
    try {
      const [healthResponse, alertsResponse] = await Promise.all([
        api.get("/nvr/health"),
        api.get("/alerts"),
      ]);
      const health = Array.isArray(healthResponse.data?.data) ? healthResponse.data.data : [];
      const alerts = Array.isArray(alertsResponse.data) ? alertsResponse.data : [];
      setNvrHealth(health);
      setLiveAlerts([...alerts].reverse().slice(0, 8));
    } catch (err) {
      console.error("Health/alert telemetry error:", err);
    }
  }

  // ========================================================
  // INITIAL LOAD + AUTO REFRESH
  // ========================================================

  useEffect(() => {
    loadDashboard();
    loadHealthAndAlerts();

    const interval = setInterval(
      loadDashboard,
      30000
    );
    const healthInterval = setInterval(
      loadHealthAndAlerts,
      5000
    );

    return () => {
      clearInterval(interval);
      clearInterval(healthInterval);
    };
  }, []);

  // ========================================================
  // ANIMATED NUMBERS
  // ========================================================

  useEffect(() => {

    const duration = 1000;
    const startTime = Date.now();

    const startValues = {
      total: displayStats.total,
      online: displayStats.online,
      offline: displayStats.offline,
      nvr: displayStats.nvr,
    };

    const targetValues = {
      total: dashboard.total,
      online: dashboard.online,
      offline: dashboard.offline,
      nvr: dashboard.nvr,
    };

    let animationFrame;

    function animate() {

      const elapsed =
        Date.now() - startTime;

      const progress =
        Math.min(
          elapsed / duration,
          1
        );

      const eased =
        1 -
        Math.pow(
          1 - progress,
          3
        );

      setDisplayStats({

        total: Math.round(
          startValues.total +
          (
            targetValues.total -
            startValues.total
          ) *
          eased
        ),

        online: Math.round(
          startValues.online +
          (
            targetValues.online -
            startValues.online
          ) *
          eased
        ),

        offline: Math.round(
          startValues.offline +
          (
            targetValues.offline -
            startValues.offline
          ) *
          eased
        ),

        nvr: Math.round(
          startValues.nvr +
          (
            targetValues.nvr -
            startValues.nvr
          ) *
          eased
        ),

      });

      if (progress < 1) {
        animationFrame =
          requestAnimationFrame(
            animate
          );
      }
    }

    animationFrame =
      requestAnimationFrame(
        animate
      );

    return () => {
      cancelAnimationFrame(
        animationFrame
      );
    };

  }, [dashboard]);

  // ========================================================
  // TICKER ROTATION
  // ========================================================

  useEffect(() => {

    const interval =
      setInterval(() => {

        setTickerIndex(
          previous =>
            (
              previous + 1
            ) %
            tickerMessages.length
        );

      }, 3200);

    return () => {
      clearInterval(interval);
    };

  }, []);

  // ========================================================
  // VISUAL ROTATION
  // ========================================================

  useEffect(() => {

    const interval =
      setInterval(() => {

        setVisualIndex(
          previous =>
            (
              previous + 1
            ) %
            visualMessages.length
        );

      }, 4200);

    return () => {
      clearInterval(interval);
    };

  }, []);

  // ========================================================
  // ORBIT ROTATION
  // ========================================================

  useEffect(() => {

    const interval =
      setInterval(() => {

        setOrbitRotation(
          previous =>
            (previous + 2) % 360
        );

      }, 40);

    return () => {
      clearInterval(interval);
    };

  }, []);

  // ========================================================
  // LOADING
  // ========================================================

  if (loading) {

    return (
      <Loader
        text="Initializing VisionGuard Mission Control..."
      />
    );

  }

  // ========================================================
  // CALCULATIONS
  // ========================================================

  const onlinePercent =
    displayStats.total > 0
      ? Math.round(
          (
            displayStats.online /
            displayStats.total
          ) * 100
        )
      : 0;

  const offlinePercent =
    displayStats.total > 0
      ? Math.round(
          (
            displayStats.offline /
            displayStats.total
          ) * 100
        )
      : 0;

  const healthPercentage =
    displayStats.total > 0
      ? Math.round(
          (
            displayStats.online /
            displayStats.total
          ) * 100
        )
      : 0;

  // ========================================================
  // RENDER
  // ========================================================

  return (

    <div className="vg-dashboard">

      <div className="vg-grid-background" />

      <div className="vg-glow vg-glow-one" />
      <div className="vg-glow vg-glow-two" />
      <div className="vg-glow vg-glow-three" />

      {/* ==================================================
          HEADER
      ================================================== */}

      <div className="vg-header">

        <div>

          <div className="vg-brand-line">

            <span className="vg-live-dot" />

            <span>
              VISIONGUARD AI
            </span>

            <span className="vg-live-badge">
              LIVE
            </span>

          </div>

          <h1 className="vg-title">

            🛡 Tata 1mg

            <span>
              NVR Security Operations Center
            </span>

          </h1>

          <p className="vg-subtitle">
            Enterprise CCTV • NVR • Network • AI Monitoring
          </p>

        </div>

        <div className="vg-header-right">

          <div className="vg-clock">

            <span>
              SYSTEM TIME
            </span>

            <strong>
              {lastUpdated || "--:--:--"}
            </strong>

          </div>

          <button
            className="vg-refresh"
            onClick={loadDashboard}
          >
            ⟳ Refresh
          </button>

        </div>

      </div>

      {/* ==================================================
          MOVING TICKER
      ================================================== */}

      <div className="vg-ticker">

        <div className="vg-ticker-label">
          ● SYSTEM FEED
        </div>

        <div className="vg-ticker-window">

          <div
            key={tickerIndex}
            className="vg-ticker-text"
          >
            {tickerMessages[tickerIndex]}
          </div>

        </div>

        <div className="vg-ticker-status">
          SECURE
        </div>

      </div>

      {/* ==================================================
          ERROR
      ================================================== */}

      {error && (

        <div className="vg-error">

          <span>⚠</span>

          <div>

            <strong>
              Backend Connection Warning
            </strong>

            <small>
              Dashboard could not fetch the latest
              monitoring data.
            </small>

          </div>

        </div>

      )}

      {/* ==================================================
          MAIN DASHBOARD

          IMPORTANT:
          STATS FIRST
          HERO SECOND

          NO AUTOMATIC SWAP
      ================================================== */}

      <div className="vg-main-area">

        {/* ==================================================
            SECTION 1
            BIG CORE STATS
        ================================================== */}

        <section className="vg-main-section vg-stats-section">

          <div className="vg-stats-grid">

            {/* TOTAL */}

            <div className="vg-stat-card vg-blue">

              <div className="vg-stat-top">

                <div className="vg-stat-icon">
                  📹
                </div>

                <span>
                  CAMERA MATRIX
                </span>

              </div>

              <div className="vg-stat-number">
                {displayStats.total}
              </div>

              <div className="vg-stat-name">
                TOTAL CAMERAS
              </div>

              <div className="vg-stat-bottom">

                <span>
                  REGISTERED DEVICES
                </span>

                <div className="vg-mini-bars">

                  <i />
                  <i />
                  <i />
                  <i />
                  <i />

                </div>

              </div>

            </div>

            {/* ONLINE */}

            <div className="vg-stat-card vg-green">

              <div className="vg-stat-top">

                <div className="vg-stat-icon">
                  🟢
                </div>

                <span>
                  ACTIVE FEED
                </span>

              </div>

              <div className="vg-stat-number">
                {displayStats.online}
              </div>

              <div className="vg-stat-name">
                ONLINE CAMERAS
              </div>

              <div className="vg-stat-bottom">

                <span>
                  {onlinePercent}% OPERATIONAL
                </span>

                <div className="vg-pulse-line" />

              </div>

            </div>

            {/* OFFLINE */}

            <div className="vg-stat-card vg-red">

              <div className="vg-stat-top">

                <div className="vg-stat-icon">
                  🔴
                </div>

                <span>
                  ATTENTION
                </span>

              </div>

              <div className="vg-stat-number">
                {displayStats.offline}
              </div>

              <div className="vg-stat-name">
                OFFLINE CAMERAS
              </div>

              <div className="vg-stat-bottom">

                <span>
                  {offlinePercent}% REQUIRE ACTION
                </span>

                <div className="vg-alert-bars">

                  <i />
                  <i />
                  <i />

                </div>

              </div>

            </div>

            {/* NVR */}

            <div className="vg-stat-card vg-orange">

              <div className="vg-stat-top">

                <div className="vg-stat-icon">
                  💾
                </div>

                <span>
                  INFRASTRUCTURE
                </span>

              </div>

              <div className="vg-stat-number">
                {displayStats.nvr}
              </div>

              <div className="vg-stat-name">
                CONNECTED NVR
              </div>

              <div className="vg-stat-bottom">

                <span>
                  RECORDING SYSTEMS
                </span>

                <div className="vg-small-orbit">
                  <i />
                </div>

              </div>

            </div>

          </div>

        </section>

        {/* ==================================================
            SECTION 1B
            LIVE NVR HEALTH + CPU
        ================================================== */}
        <section className="vg-main-section" style={{ marginTop: 18 }}>
          <div className="vg-section-head" style={{ marginBottom: 14 }}>
            <div>
              <h3>LIVE NVR HEALTH</h3>
              <span>CPU • MEMORY • TEMPERATURE • CONNECTIVITY</span>
            </div>
            <span style={{ color: "#59f2a7" }}>● LIVE • 5s</span>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(220px,1fr))", gap: 12 }}>
            {Array.from({ length: 9 }, (_, i) => {
              const item = nvrHealth.find(x => Number(x.id) === i + 1) || { id: i + 1, name: `NVR-${i + 1}`, status: "UNKNOWN" };
              const cpu = item.cpu_percent;
              const mem = item.memory_percent;
              const temp = item.temperature_c;
              const online = item.status === "ONLINE";
              return (
                <div key={item.id} style={{ padding: 16, borderRadius: 14, background: "rgba(8,18,40,.78)", border: `1px solid ${online ? "rgba(59,130,246,.35)" : "rgba(239,68,68,.5)"}`, boxShadow: "inset 0 0 24px rgba(30,64,175,.08)" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                    <strong style={{ color: "#fff" }}>{item.name}</strong>
                    <span style={{ color: online ? "#59f2a7" : "#ff6577", fontSize: 11, fontWeight: 800 }}>{online ? "ONLINE" : item.status || "UNKNOWN"}</span>
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                    <div><small style={{ color: "#7f93b8" }}>CPU</small><div style={{ fontSize: 24, fontWeight: 800, color: cpu >= 90 ? "#ff6577" : cpu >= 75 ? "#ffc857" : "#59f2a7" }}>{cpu == null ? "--" : `${cpu}%`}</div></div>
                    <div><small style={{ color: "#7f93b8" }}>MEMORY</small><div style={{ fontSize: 24, fontWeight: 800, color: mem >= 90 ? "#ff6577" : mem >= 80 ? "#ffc857" : "#75b7ff" }}>{mem == null ? "--" : `${mem}%`}</div></div>
                  </div>
                  <div style={{ marginTop: 8, fontSize: 12, color: "#a9b9d6" }}>Temp: {temp == null ? "--" : `${temp}°C`} &nbsp; • &nbsp; IP: {item.ip || "--"}</div>
                </div>
              );
            })}
          </div>
        </section>

        {/* ==================================================
            SECTION 1C
            LIVE ALERT FEED
        ================================================== */}
        <section className="vg-main-section" style={{ marginTop: 18 }}>
          <div className="vg-section-head" style={{ marginBottom: 14 }}>
            <div><h3>🚨 LIVE ALERT FEED</h3><span>Issues detected by the NVR health and monitoring engines</span></div>
            <span>{liveAlerts.length} recent</span>
          </div>
          <div style={{ display: "grid", gap: 8 }}>
            {liveAlerts.length === 0 ? (
              <div style={{ padding: 18, color: "#59f2a7", background: "rgba(8,40,28,.35)", borderRadius: 12 }}>✓ No active/recent issues detected</div>
            ) : liveAlerts.slice(0, 6).map((alert, index) => (
              <div key={`${alert.time}-${index}`} style={{ display: "flex", gap: 12, alignItems: "center", padding: 12, borderRadius: 12, background: "rgba(12,23,47,.72)", borderLeft: `4px solid ${alert.severity === "CRITICAL" ? "#ff4d5f" : alert.severity === "WARNING" ? "#ffc857" : "#4ea1ff"}` }}>
                <div style={{ flex: 1 }}><strong style={{ color: "#fff" }}>{alert.title || alert.type || "Alert"}</strong><div style={{ color: "#9db0d0", fontSize: 12 }}>{alert.description || alert.change || "Monitoring event detected"}</div></div>
                <small style={{ color: "#7186ab", whiteSpace: "nowrap" }}>{alert.time || "--"}</small>
              </div>
            ))}
          </div>
        </section>

        {/* ==================================================
            SECTION 2
            HERO MISSION CONTROL
        ================================================== */}

        <section className="vg-main-section vg-hero-section">

          <div className="vg-hero">

            <div className="vg-hero-title">

              <small>
                MISSION CONTROL
              </small>

              <h2>
                Security Intelligence
              </h2>

              <p>
                Real-time surveillance infrastructure monitoring
              </p>

            </div>

            {/* FLOATING DATA */}

            <div className="vg-floating float-1">

              <small>
                CAMERAS ONLINE
              </small>

              <strong>
                {displayStats.online}
              </strong>

            </div>

            <div className="vg-floating float-2">

              <small>
                CONNECTED NVR
              </small>

              <strong>
                {displayStats.nvr}
              </strong>

            </div>

            <div className="vg-floating float-3">

              <small>
                NETWORK STATE
              </small>

              <strong className="green-value">
                STABLE
              </strong>

            </div>

            <div className="vg-floating float-4">

              <small>
                AI ENGINE
              </small>

              <strong className="blue-value">
                ACTIVE
              </strong>

            </div>

            {/* ORBIT */}

            <div className="vg-orbit-area">

              <div className="vg-orbit">

                <div className="vg-orbit-dot vg-dot-1" />
                <div className="vg-orbit-dot vg-dot-2" />
                <div className="vg-orbit-dot vg-dot-3" />

              </div>

              <div
                className="vg-orbit vg-orbit-inner"
                style={{
                  transform:
                    `rotate(${orbitRotation}deg)`
                }}
              />

              <div className="vg-core">

                <div className="vg-core-icon">
                  🛡️
                </div>

                <strong>
                  VISIONGUARD
                </strong>

                <span className="vg-monitoring">
                  ● MONITORING
                </span>

              </div>

            </div>

            {/* ROTATING TEXT */}

            <div
              key={tickerIndex}
              className="vg-rotating-text"
            >
              {tickerMessages[tickerIndex]}
            </div>

          </div>

        </section>

      </div>

      {/* ==================================================
          HEALTH / VISUAL / AI
      ================================================== */}

      <div className="row g-4 mt-1">

        {/* HEALTH */}

        <div className="col-xl-4">

          <div className="vg-panel vg-health-panel">

            <div className="vg-panel-header">

              <div>

                <span>
                  SYSTEM HEALTH
                </span>

                <h3>
                  Infrastructure Status
                </h3>

              </div>

              <div className="vg-live-mini">
                ● LIVE
              </div>

            </div>

            <div className="vg-health-body">

              <div
                className="vg-health-ring"
                style={{
                  "--health":
                    `${healthPercentage * 3.6}deg`
                }}
              >

                <div>

                  <strong>
                    {healthPercentage}%
                  </strong>

                  <span>
                    HEALTH
                  </span>

                </div>

              </div>

              <div className="vg-health-list">

                <div>

                  <span>
                    ● Camera Services
                  </span>

                  <strong>
                    {displayStats.online}
                  </strong>

                </div>

                <div>

                  <span>
                    ● Offline Devices
                  </span>

                  <strong className="danger-text">
                    {displayStats.offline}
                  </strong>

                </div>

                <div>

                  <span>
                    ● NVR Infrastructure
                  </span>

                  <strong>
                    {displayStats.nvr}
                  </strong>

                </div>

                <div>

                  <span>
                    ● AI Engine
                  </span>

                  <strong className="success-text">
                    ACTIVE
                  </strong>

                </div>

              </div>

            </div>

          </div>

        </div>

        {/* VISUAL */}

        <div className="col-xl-4">

          <div className="vg-panel vg-visual-panel">

            <div className="vg-scan-line" />
            <div className="vg-visual-grid" />

            <div
              key={visualIndex}
              className="vg-visual-content"
            >

              <div className="vg-big-icon">

                {
                  visualMessages[
                    visualIndex
                  ].icon
                }

              </div>

              <div className="vg-visual-label">
                VISIONGUARD CORE
              </div>

              <h2>

                {
                  visualMessages[
                    visualIndex
                  ].title
                }

              </h2>

              <p>

                {
                  visualMessages[
                    visualIndex
                  ].text
                }

              </p>

              <div className="vg-visual-status">

                <span />

                SYSTEM ACTIVE

              </div>

            </div>

            <div className="vg-corner vg-c1" />
            <div className="vg-corner vg-c2" />
            <div className="vg-corner vg-c3" />
            <div className="vg-corner vg-c4" />

          </div>

        </div>

        {/* AI */}

        <div className="col-xl-4">

          <div className="vg-panel vg-ai-panel">

            <div className="vg-panel-header">

              <div>

                <span>
                  ARTIFICIAL INTELLIGENCE
                </span>

                <h3>
                  AI Command Center
                </h3>

              </div>

              <div className="vg-ai-orb">
                AI
              </div>

            </div>

            <div className="vg-ai-content">

              <div className="vg-ai-status">

                <span className="vg-ai-pulse" />

                <strong>
                  AI MONITORING ACTIVE
                </strong>

              </div>

              <p>
                VisionGuard AI is continuously
                analysing the CCTV infrastructure
                and monitoring device health.
              </p>

              <div className="vg-ai-metrics">

                <div>

                  <span>
                    CAMERA ANALYSIS
                  </span>

                  <strong>
                    24/7
                  </strong>

                </div>

                <div>

                  <span>
                    ALERT ENGINE
                  </span>

                  <strong>
                    ACTIVE
                  </strong>

                </div>

                <div>

                  <span>
                    NETWORK WATCH
                  </span>

                  <strong>
                    ON
                  </strong>

                </div>

              </div>

            </div>

          </div>

        </div>

      </div>

      {/* ==================================================
          LIVE SYSTEM STATUS
      ================================================== */}

      <div className="vg-panel vg-status-panel mt-4">

        <div className="vg-panel-header">

          <div>

            <span>
              OPERATIONS MONITOR
            </span>

            <h3>
              Live System Status
            </h3>

          </div>

          <div className="vg-status-running">
            ● MONITORING
          </div>

        </div>

        <div className="vg-status-grid">

          <StatusItem
            icon="📡"
            title="NETWORK"
            value="STABLE"
          />

          <StatusItem
            icon="💾"
            title="NVR SERVICES"
            value={`${displayStats.nvr} CONNECTED`}
          />

          <StatusItem
            icon="🎥"
            title="CAMERA FEEDS"
            value={`${displayStats.online} ONLINE`}
          />

          <StatusItem
            icon="🧠"
            title="AI ENGINE"
            value="ACTIVE"
          />

          <StatusItem
            icon="🔐"
            title="SECURITY"
            value="PROTECTED"
          />

        </div>

      </div>

      {/* ==================================================
          AI INSIGHTS + OVERVIEW
      ================================================== */}

      <div className="row g-4 mt-1">

        <div className="col-xl-4">

          <div className="vg-component-wrapper">
            <AIInsights />
          </div>

        </div>

        <div className="col-xl-8">

          <div className="vg-panel vg-overview">

            <div className="vg-panel-header">

              <div>

                <span>
                  COMMAND OVERVIEW
                </span>

                <h3>
                  Security Operations
                </h3>

              </div>

              <span className="vg-secure-badge">
                🛡 SECURE
              </span>

            </div>

            <div className="vg-overview-grid">

              <OverviewItem
                icon="🟢"
                title="Critical Services"
                text="All core monitoring services operational"
              />

              <OverviewItem
                icon="📡"
                title="Network"
                text="NVR communication layer stable"
              />

              <OverviewItem
                icon="💽"
                title="Storage"
                text="Recording infrastructure under monitoring"
              />

              <OverviewItem
                icon="🤖"
                title="AI Monitoring"
                text="Automated intelligence engine active"
              />

            </div>

          </div>

        </div>

      </div>

      {/* ==================================================
          CAMERA / PERFORMANCE CHARTS
      ================================================== */}

      <div className="vg-section">

        <div className="vg-section-head">

          <h3>
            ◈ SURVEILLANCE ANALYTICS
          </h3>

          <span>
            AUTOMATED TELEMETRY
          </span>

        </div>

        <div className="row g-4">

          <div className="col-xl-6">

            <div className="vg-chart-wrapper">

              <div className="vg-panel-title">

                <strong>
                  CAMERA DISTRIBUTION
                </strong>

                <span>
                  LIVE DATA
                </span>

              </div>

              <CameraPieChart />

            </div>

          </div>

          <div className="col-xl-6">

            <div className="vg-chart-wrapper">

              <div className="vg-panel-title">

                <strong>
                  SYSTEM PERFORMANCE
                </strong>

                <span>
                  LIVE DATA
                </span>

              </div>

              <PerformanceChart />

            </div>

          </div>

        </div>

      </div>

      {/* ==================================================
          STORAGE
      ================================================== */}

      <div className="vg-section">

        <div className="vg-section-head">

          <h3>
            ◈ STORAGE TELEMETRY
          </h3>

          <span>
            NVR RECORDING INFRASTRUCTURE
          </span>

        </div>

        <div className="vg-chart-wrapper">

          <StorageChart />

        </div>

      </div>

      {/* ==================================================
          FOOTER
      ================================================== */}

      <div className="vg-footer">

        <span>
          VISIONGUARD AI · ENTERPRISE SECURITY PLATFORM
        </span>

        <span className="vg-footer-live">
          ● SYSTEM LIVE
        </span>

        <span>
          LAST UPDATED · {lastUpdated || "--"}
        </span>

      </div>

      {/* ==================================================
          STYLES
      ================================================== */}

      <style>{`

        * {
          box-sizing: border-box;
        }

        .vg-dashboard {
          min-height: calc(100vh - 70px);
          padding: 22px;
          position: relative;
          overflow: hidden;

          color: #e8f1ff;

          background:
            radial-gradient(
              circle at 50% 0%,
              rgba(0,110,255,.20),
              transparent 30%
            ),
            radial-gradient(
              circle at 0% 70%,
              rgba(0,255,180,.08),
              transparent 28%
            ),
            radial-gradient(
              circle at 100% 80%,
              rgba(150,60,255,.10),
              transparent 28%
            ),
            #020712;
        }

        /* ==================================================
           BACKGROUND
        ================================================== */

        .vg-grid-background {
          position: absolute;
          inset: 0;

          pointer-events: none;

          opacity: .18;

          background-image:
            linear-gradient(
              rgba(60,130,220,.08) 1px,
              transparent 1px
            ),
            linear-gradient(
              90deg,
              rgba(60,130,220,.08) 1px,
              transparent 1px
            );

          background-size: 45px 45px;

          mask-image:
            linear-gradient(
              to bottom,
              black,
              transparent
            );
        }

        .vg-glow {
          position: absolute;

          width: 300px;
          height: 300px;

          border-radius: 50%;

          filter: blur(100px);

          pointer-events: none;

          opacity: .12;
        }

        .vg-glow-one {
          background: #1677ff;
          top: 100px;
          left: 30%;
        }

        .vg-glow-two {
          background: #00ff9d;
          top: 800px;
          right: 10%;
        }

        .vg-glow-three {
          background: #8b5cf6;
          bottom: 300px;
          left: 10%;
        }

        /* ==================================================
           HEADER
        ================================================== */

        .vg-header {
          position: relative;
          z-index: 2;

          display: flex;

          justify-content: space-between;
          align-items: center;

          padding: 18px 22px;

          border:
            1px solid
            rgba(80,160,255,.20);

          border-radius: 18px;

          background:
            linear-gradient(
              135deg,
              rgba(10,25,50,.94),
              rgba(4,12,28,.78)
            );

          backdrop-filter: blur(18px);

          box-shadow:
            0 18px 55px rgba(0,0,0,.38),
            inset 0 1px rgba(255,255,255,.04);
        }

        .vg-brand-line {
          display: flex;
          align-items: center;
          gap: 9px;

          color: #62a8ff;

          font-size: 11px;
          font-weight: 900;

          letter-spacing: 3px;
        }

        .vg-live-dot {
          width: 8px;
          height: 8px;

          border-radius: 50%;

          background: #00ff88;

          box-shadow:
            0 0 12px #00ff88;

          animation:
            vgPulse 1.2s infinite;
        }

        .vg-live-badge {
          padding: 4px 7px;

          border:
            1px solid
            rgba(0,255,140,.25);

          border-radius: 5px;

          color: #3eff9c;

          background:
            rgba(0,255,140,.06);

          font-size: 8px;

          letter-spacing: 1px;
        }

        .vg-title {
          margin: 8px 0 4px;

          font-size: 27px;
          font-weight: 900;

          letter-spacing: -.5px;

          color: #f5f9ff;
        }

        .vg-title span {
          margin-left: 9px;

          color: #6ea9e9;

          font-size: 20px;
        }

        .vg-subtitle {
          margin: 0;

          color: #617995;

          font-size: 11px;

          letter-spacing: 1px;
        }

        .vg-header-right {
          display: flex;

          align-items: center;

          gap: 12px;
        }

        .vg-clock {
          min-width: 125px;

          text-align: right;
        }

        .vg-clock span {
          display: block;

          color: #526b89;

          font-size: 8px;

          letter-spacing: 1.5px;
        }

        .vg-clock strong {
          display: block;

          margin-top: 4px;

          color: #a9cfff;

          font-family: Consolas, monospace;

          font-size: 15px;
        }

        .vg-refresh {
          border:
            1px solid
            rgba(70,160,255,.25);

          border-radius: 8px;

          padding: 10px 15px;

          color: #b9d9ff;

          background:
            rgba(20,80,150,.15);

          cursor: pointer;

          transition: .25s;
        }

        .vg-refresh:hover {
          transform: translateY(-2px);

          border-color:
            rgba(70,160,255,.65);

          background:
            rgba(20,100,190,.25);

          box-shadow:
            0 0 25px
            rgba(30,130,255,.15);
        }

        /* ==================================================
           TICKER
        ================================================== */

        .vg-ticker {
          position: relative;
          z-index: 2;

          display: flex;

          align-items: center;

          margin-top: 14px;

          min-height: 42px;

          overflow: hidden;

          border:
            1px solid
            rgba(80,150,255,.13);

          border-radius: 10px;

          background:
            rgba(5,15,30,.78);
        }

        .vg-ticker-label {
          padding: 0 15px;

          color: #35ff9a;

          font-size: 8px;

          font-weight: 900;

          letter-spacing: 1.5px;

          white-space: nowrap;
        }

        .vg-ticker-window {
          flex: 1;

          overflow: hidden;
        }

        .vg-ticker-text {
          animation:
            vgTickerIn .7s ease;

          color: #8fb8e8;

          font-size: 10px;

          font-weight: 700;

          letter-spacing: 1.5px;
        }

        .vg-ticker-status {
          padding: 0 15px;

          color: #3eff9c;

          font-size: 8px;

          font-weight: 900;

          letter-spacing: 1px;
        }

        /* ==================================================
           ERROR
        ================================================== */

        .vg-error {
          position: relative;
          z-index: 2;

          display: flex;

          gap: 12px;

          align-items: center;

          margin-top: 14px;

          padding: 12px 16px;

          border:
            1px solid
            rgba(255,70,70,.25);

          border-radius: 10px;

          color: #ff9a9a;

          background:
            rgba(255,40,40,.06);
        }

        .vg-error span {
          font-size: 22px;
        }

        .vg-error strong,
        .vg-error small {
          display: block;
        }

        .vg-error small {
          margin-top: 3px;

          color: #a76868;

          font-size: 9px;
        }

        /* ==================================================
           MAIN AREA
           
           IMPORTANT:
           NO SWAP
           NO ORDER CHANGE
           STATS ALWAYS FIRST
           HERO ALWAYS SECOND
        ================================================== */

        .vg-main-area {
          position: relative;

          z-index: 2;

          display: flex;

          flex-direction: column;

          gap: 18px;

          margin-top: 18px;
        }

        .vg-main-section {
          position: relative;

          width: 100%;
        }

        /* ==================================================
           HERO
        ================================================== */

        .vg-hero {
          position: relative;

          min-height: 390px;

          overflow: hidden;

          border:
            1px solid
            rgba(80,160,255,.17);

          border-radius: 23px;

          background:
            radial-gradient(
              circle at center,
              rgba(20,100,220,.16),
              transparent 38%
            ),
            rgba(4,12,27,.82);

          box-shadow:
            0 25px 80px
            rgba(0,0,0,.38);
        }

        .vg-hero-title {
          position: absolute;

          top: 22px;
          left: 27px;

          z-index: 5;
        }

        .vg-hero-title small {
          color: #4e9dff;

          font-size: 9px;

          font-weight: 900;

          letter-spacing: 3px;
        }

        .vg-hero-title h2 {
          margin: 6px 0 0;

          font-size: 27px;

          font-weight: 900;
        }

        .vg-hero-title p {
          margin: 5px 0;

          color: #657e9e;

          font-size: 11px;
        }

        /* ==================================================
           ORBIT
        ================================================== */

        .vg-orbit-area {
          position: absolute;

          left: 50%;
          top: 53%;

          width: 350px;
          height: 350px;

          transform:
            translate(-50%, -50%);
        }

        .vg-orbit {
          position: absolute;

          inset: 0;

          border:
            1px solid
            rgba(40,140,255,.25);

          border-radius: 50%;

          animation:
            vgRotate 18s linear infinite;
        }

        .vg-orbit::before {
          content: "";

          position: absolute;

          inset: 35px;

          border:
            1px dashed
            rgba(0,220,255,.18);

          border-radius: 50%;
        }

        .vg-orbit::after {
          content: "";

          position: absolute;

          inset: 80px;

          border:
            1px solid
            rgba(130,80,255,.20);

          border-radius: 50%;
        }

        .vg-orbit-inner {
          border-color:
            rgba(0,255,180,.12);

          animation: none;
        }

        .vg-orbit-dot {
          position: absolute;

          width: 9px;
          height: 9px;

          border-radius: 50%;

          background: #26a7ff;

          box-shadow:
            0 0 20px #26a7ff;
        }

        .vg-dot-1 {
          top: 4px;
          left: 50%;
        }

        .vg-dot-2 {
          right: 14px;
          top: 65%;
        }

        .vg-dot-3 {
          bottom: 25px;
          left: 22%;
        }

        /* ==================================================
           CORE
        ================================================== */

        .vg-core {
          position: absolute;

          left: 50%;
          top: 50%;

          width: 155px;
          height: 155px;

          transform:
            translate(-50%, -50%);

          display: flex;

          flex-direction: column;

          align-items: center;

          justify-content: center;

          text-align: center;

          border:
            1px solid
            rgba(60,170,255,.45);

          border-radius: 50%;

          background:
            radial-gradient(
              circle,
              rgba(20,120,255,.25),
              rgba(4,15,32,.97) 67%
            );

          box-shadow:
            0 0 35px
            rgba(0,120,255,.30),

            inset 0 0 40px
            rgba(0,120,255,.12);

          animation:
            vgCoreFloat 3s ease-in-out infinite;
        }

        .vg-core-icon {
          font-size: 37px;

          filter:
            drop-shadow(
              0 0 12px #2495ff
            );
        }

        .vg-core strong {
          margin-top: 5px;

          color: #72baff;

          font-size: 10px;

          letter-spacing: 2px;
        }

        .vg-monitoring {
          margin-top: 7px;

          color: #35ff9b;

          font-size: 8px;
        }

        .vg-rotating-text {
          position: absolute;

          left: 50%;
          top: 50%;

          width: 420px;

          transform:
            translate(-50%, 125px);

          text-align: center;

          color: #a9cfff;

          font-size: 10px;

          font-weight: 800;

          letter-spacing: 2px;

          animation:
            vgTextIn .6s ease;
        }

        /* ==================================================
           FLOATING CARDS
        ================================================== */

        .vg-floating {
          position: absolute;

          z-index: 4;

          padding: 10px 14px;

          border:
            1px solid
            rgba(80,150,255,.18);

          border-radius: 12px;

          background:
            rgba(7,20,40,.80);

          backdrop-filter:
            blur(10px);

          box-shadow:
            0 10px 30px
            rgba(0,0,0,.3);

          animation:
            vgFloat 4s ease-in-out infinite;
        }

        .vg-floating small {
          display: block;

          color: #6681a5;

          font-size: 8px;

          letter-spacing: 1px;
        }

        .vg-floating strong {
          display: block;

          margin-top: 3px;

          color: #dceaff;

          font-size: 16px;
        }

        .green-value {
          color: #3eff9c !important;
        }

        .blue-value {
          color: #7eb8ff !important;
        }

        .float-1 {
          left: 8%;
          top: 35%;
        }

        .float-2 {
          right: 8%;
          top: 35%;

          animation-delay: 1s;
        }

        .float-3 {
          left: 12%;
          bottom: 18%;

          animation-delay: 2s;
        }

        .float-4 {
          right: 12%;
          bottom: 18%;

          animation-delay: 3s;
        }

        /* ==================================================
           BIG STATS
        ================================================== */

        .vg-stats-grid {
          display: grid;

          grid-template-columns:
            repeat(4, minmax(0, 1fr));

          gap: 15px;
        }

        .vg-stat-card {
          position: relative;

          min-height: 160px;

          padding: 19px;

          overflow: hidden;

          border:
            1px solid
            rgba(80,150,255,.14);

          border-radius: 17px;

          background:
            linear-gradient(
              145deg,
              rgba(12,28,52,.94),
              rgba(5,13,29,.94)
            );

          transition: .3s ease;
        }

        .vg-stat-card:hover {
          transform:
            translateY(-5px);

          box-shadow:
            0 18px 45px
            rgba(0,100,255,.13);
        }

        .vg-stat-card::after {
          content: "";

          position: absolute;

          width: 120px;
          height: 120px;

          right: -45px;
          top: -45px;

          border-radius: 50%;

          background:
            currentColor;

          filter:
            blur(45px);

          opacity: .08;
        }

        .vg-blue {
          color: #2585ff;
        }

        .vg-green {
          color: #00ff8c;
        }

        .vg-red {
          color: #ff3d58;
        }

        .vg-orange {
          color: #f59e0b;
        }

        .vg-stat-top {
          display: flex;

          justify-content: space-between;

          align-items: center;
        }

        .vg-stat-top span {
          color: #617895;

          font-size: 8px;

          font-weight: 800;

          letter-spacing: 1.5px;
        }

        .vg-stat-icon {
          font-size: 20px;
        }

        .vg-stat-number {
          margin-top: 12px;

          color: currentColor;

          font-size: 44px;

          font-weight: 950;

          line-height: 1;
        }

        .vg-stat-name {
          margin-top: 7px;

          color: #d9e5f4;

          font-size: 12px;

          font-weight: 900;

          letter-spacing: 1.2px;
        }

        .vg-stat-bottom {
          display: flex;

          align-items: center;

          justify-content: space-between;

          margin-top: 17px;
        }

        .vg-stat-bottom span {
          color: #526a87;

          font-size: 8px;

          letter-spacing: .8px;
        }

        .vg-mini-bars {
          display: flex;

          align-items: end;

          gap: 3px;

          height: 18px;
        }

        .vg-mini-bars i {
          width: 4px;
          height: 12px;

          border-radius: 2px;

          background: #2585ff;

          animation:
            vgBars .8s infinite alternate;
        }

        .vg-mini-bars i:nth-child(2) {
          height: 17px;
          animation-delay: .1s;
        }

        .vg-mini-bars i:nth-child(3) {
          height: 9px;
          animation-delay: .2s;
        }

        .vg-mini-bars i:nth-child(4) {
          height: 15px;
          animation-delay: .3s;
        }

        .vg-mini-bars i:nth-child(5) {
          height: 12px;
          animation-delay: .4s;
        }

        .vg-pulse-line {
          width: 55px;
          height: 3px;

          border-radius: 5px;

          background: #00ff8c;

          box-shadow:
            0 0 12px #00ff8c;

          animation:
            vgPulseLine 1.5s infinite;
        }

        .vg-alert-bars {
          display: flex;

          gap: 3px;

          align-items: end;

          height: 18px;
        }

        .vg-alert-bars i {
          width: 4px;
          height: 15px;

          border-radius: 2px;

          background: #ff3d58;

          animation:
            vgAlert .7s infinite alternate;
        }

        .vg-alert-bars i:nth-child(2) {
          height: 9px;

          animation-delay: .2s;
        }

        .vg-alert-bars i:nth-child(3) {
          height: 17px;

          animation-delay: .4s;
        }

        .vg-small-orbit {
          width: 19px;
          height: 19px;

          border:
            1px solid
            rgba(245,158,11,.5);

          border-radius: 50%;

          animation:
            vgRotate 2s linear infinite;
        }

        .vg-small-orbit i {
          display: block;

          width: 4px;
          height: 4px;

          margin: -2px auto 0;

          border-radius: 50%;

          background: #f59e0b;

          box-shadow:
            0 0 8px #f59e0b;
        }

        /* ==================================================
           PANELS
        ================================================== */

        .vg-panel {
          position: relative;

          overflow: hidden;

          height: 100%;

          padding: 18px;

          border:
            1px solid
            rgba(80,150,255,.14);

          border-radius: 17px;

          background:
            rgba(5,14,29,.84);

          box-shadow:
            0 15px 45px
            rgba(0,0,0,.24);
        }

        .vg-panel-header {
          display: flex;

          align-items: center;

          justify-content: space-between;

          margin-bottom: 17px;
        }

        .vg-panel-header span {
          color: #526c89;

          font-size: 8px;

          font-weight: 800;

          letter-spacing: 1.5px;
        }

        .vg-panel-header h3 {
          margin: 4px 0 0;

          color: #e3edf9;

          font-size: 16px;

          font-weight: 900;
        }

        .vg-live-mini {
          color: #35ff9a !important;

          font-size: 8px !important;
        }

        /* ==================================================
           HEALTH
        ================================================== */

        .vg-health-body {
          display: flex;

          align-items: center;

          justify-content: space-around;

          gap: 18px;
        }

        .vg-health-ring {
          width: 150px;
          height: 150px;

          flex-shrink: 0;

          display: flex;

          align-items: center;

          justify-content: center;

          border-radius: 50%;

          background:
            conic-gradient(
              #00ff8c
              var(--health),
              #10223a 0
            );

          box-shadow:
            0 0 35px
            rgba(0,255,140,.12);

          position: relative;
        }

        .vg-health-ring::after {
          content: "";

          position: absolute;

          inset: 11px;

          border-radius: 50%;

          background: #071321;

          border:
            1px solid
            rgba(80,150,255,.12);
        }

        .vg-health-ring > div {
          position: relative;

          z-index: 2;

          text-align: center;
        }

        .vg-health-ring strong {
          display: block;

          color: #e9fff4;

          font-size: 28px;
        }

        .vg-health-ring span {
          color: #5d7693;

          font-size: 8px;

          letter-spacing: 2px;
        }

        .vg-health-list {
          flex: 1;
        }

        .vg-health-list > div {
          display: flex;

          justify-content: space-between;

          padding: 10px 0;

          border-bottom:
            1px solid
            rgba(148,163,184,.07);
        }

        .vg-health-list span {
          color: #627995;

          font-size: 9px;
        }

        .vg-health-list strong {
          color: #a8c7e8;

          font-size: 10px;
        }

        .danger-text {
          color: #ff6477 !important;
        }

        .success-text {
          color: #35ff9a !important;
        }

        /* ==================================================
           VISUAL
        ================================================== */

        .vg-visual-panel {
          min-height: 250px;

          display: flex;

          align-items: center;

          justify-content: center;

          text-align: center;

          background:
            radial-gradient(
              circle at center,
              rgba(40,120,255,.12),
              transparent 55%
            ),
            #06101f;
        }

        .vg-visual-grid {
          position: absolute;

          inset: 0;

          opacity: .12;

          background-image:
            linear-gradient(
              rgba(80,160,255,.15) 1px,
              transparent 1px
            ),
            linear-gradient(
              90deg,
              rgba(80,160,255,.15) 1px,
              transparent 1px
            );

          background-size: 28px 28px;
        }

        .vg-scan-line {
          position: absolute;

          left: 0;
          right: 0;

          height: 1px;

          background:
            linear-gradient(
              90deg,
              transparent,
              #27a7ff,
              transparent
            );

          box-shadow:
            0 0 15px #27a7ff;

          animation:
            vgScan 3s linear infinite;
        }

        .vg-visual-content {
          position: relative;

          z-index: 3;

          animation:
            vgVisualIn .7s ease;
        }

        .vg-big-icon {
          font-size: 45px;

          filter:
            drop-shadow(
              0 0 16px
              rgba(40,160,255,.5)
            );
        }

        .vg-visual-label {
          margin-top: 8px;

          color: #4f9fff;

          font-size: 8px;

          font-weight: 900;

          letter-spacing: 3px;
        }

        .vg-visual-content h2 {
          margin: 7px 0 5px;

          color: #e6f2ff;

          font-size: 18px;

          font-weight: 900;
        }

        .vg-visual-content p {
          max-width: 280px;

          margin: auto;

          color: #637c99;

          font-size: 9px;

          line-height: 1.6;
        }

        .vg-visual-status {
          display: inline-flex;

          align-items: center;

          gap: 6px;

          margin-top: 14px;

          padding: 6px 10px;

          border:
            1px solid
            rgba(0,255,140,.16);

          border-radius: 20px;

          color: #3eff9c;

          background:
            rgba(0,255,140,.05);

          font-size: 8px;

          letter-spacing: 1px;
        }

        .vg-visual-status span {
          width: 5px;
          height: 5px;

          border-radius: 50%;

          background: #00ff8c;

          box-shadow:
            0 0 8px #00ff8c;
        }

        .vg-corner {
          position: absolute;

          width: 20px;
          height: 20px;

          border-color: #2a8cff;
        }

        .vg-c1 {
          left: 12px;
          top: 12px;

          border-left: 1px solid;
          border-top: 1px solid;
        }

        .vg-c2 {
          right: 12px;
          top: 12px;

          border-right: 1px solid;
          border-top: 1px solid;
        }

        .vg-c3 {
          left: 12px;
          bottom: 12px;

          border-left: 1px solid;
          border-bottom: 1px solid;
        }

        .vg-c4 {
          right: 12px;
          bottom: 12px;

          border-right: 1px solid;
          border-bottom: 1px solid;
        }

        /* ==================================================
           AI
        ================================================== */

        .vg-ai-panel {
          background:
            radial-gradient(
              circle at 85% 10%,
              rgba(145,80,255,.12),
              transparent 35%
            ),
            #071020;
        }

        .vg-ai-orb {
          width: 43px;
          height: 43px;

          display: flex;

          align-items: center;

          justify-content: center;

          border-radius: 50%;

          color: #d2b5ff;

          border:
            1px solid
            rgba(170,100,255,.35);

          background:
            rgba(130,70,255,.12);

          box-shadow:
            0 0 25px
            rgba(160,80,255,.18);

          animation:
            vgAiOrb 2s infinite;
        }

        .vg-ai-status {
          display: flex;

          align-items: center;

          gap: 8px;

          color: #3eff9c;

          font-size: 10px;
        }

        .vg-ai-pulse {
          width: 7px;
          height: 7px;

          border-radius: 50%;

          background: #00ff8c;

          box-shadow:
            0 0 12px #00ff8c;

          animation:
            vgPulse 1.2s infinite;
        }

        .vg-ai-content p {
          color: #667f9e;

          font-size: 10px;

          line-height: 1.7;
        }

        .vg-ai-metrics {
          display: grid;

          grid-template-columns:
            repeat(3,1fr);

          gap: 8px;

          margin-top: 20px;
        }

        .vg-ai-metrics > div {
          padding: 11px;

          border:
            1px solid
            rgba(160,100,255,.12);

          border-radius: 8px;

          background:
            rgba(100,50,180,.05);
        }

        .vg-ai-metrics span {
          display: block;

          color: #526a88;

          font-size: 7px;
        }

        .vg-ai-metrics strong {
          display: block;

          margin-top: 5px;

          color: #c5a5ff;

          font-size: 11px;
        }

        /* ==================================================
           STATUS
        ================================================== */

        .vg-status-panel {
          min-height: auto;
        }

        .vg-status-running {
          color: #3eff9c;

          font-size: 8px;

          letter-spacing: 1px;
        }

        .vg-status-grid {
          display: grid;

          grid-template-columns:
            repeat(5, minmax(0,1fr));

          gap: 10px;
        }

        .vg-status-item {
          padding: 13px;

          border:
            1px solid
            rgba(148,163,184,.08);

          border-radius: 9px;

          background:
            rgba(7,17,31,.55);

          transition: .25s;
        }

        .vg-status-item:hover {
          transform:
            translateY(-3px);

          border-color:
            rgba(70,160,255,.25);
        }

        .vg-status-item-top {
          display: flex;

          justify-content: space-between;
        }

        .vg-status-item-icon {
          font-size: 18px;
        }

        .vg-status-indicator {
          width: 6px;
          height: 6px;

          border-radius: 50%;

          background: #22c55e;

          box-shadow:
            0 0 8px #22c55e;

          animation:
            vgPulse 1.5s infinite;
        }

        .vg-status-item-title {
          margin-top: 10px;

          color: #52657f;

          font-size: 7px;

          letter-spacing: 1px;
        }

        .vg-status-item-value {
          margin-top: 4px;

          color: #cbd5e1;

          font-family:
            Consolas,
            monospace;

          font-size: 9px;
        }

        /* ==================================================
           OVERVIEW
        ================================================== */

        .vg-component-wrapper {
          height: 100%;

          overflow: hidden;

          border:
            1px solid
            rgba(148,163,184,.12);

          border-radius: 14px;

          background: #081322;
        }

        .vg-secure-badge {
          padding: 5px 8px;

          border:
            1px solid
            rgba(34,197,94,.2);

          border-radius: 5px;

          color: #4ade80;

          background:
            rgba(34,197,94,.06);

          font-size: 7px;

          letter-spacing: 1px;
        }

        .vg-overview-grid {
          display: grid;

          grid-template-columns:
            repeat(2,1fr);

          gap: 10px;
        }

        .vg-overview-item {
          display: flex;

          gap: 10px;

          padding: 13px;

          border:
            1px solid
            rgba(148,163,184,.08);

          border-radius: 9px;

          background:
            rgba(7,17,31,.55);
        }

        .vg-overview-icon {
          font-size: 18px;
        }

        .vg-overview-item strong {
          display: block;

          color: #cbd5e1;

          font-size: 10px;
        }

        .vg-overview-item p {
          margin: 4px 0 0;

          color: #52657f;

          font-size: 8px;

          line-height: 1.5;
        }

        /* ==================================================
           CHARTS
        ================================================== */

        .vg-section {
          position: relative;

          z-index: 2;

          margin-top: 22px;
        }

        .vg-section-head {
          display: flex;

          justify-content: space-between;

          align-items: center;

          margin-bottom: 12px;
        }

        .vg-section-head h3 {
          margin: 0;

          color: #dbe8f7;

          font-size: 14px;

          font-weight: 900;
        }

        .vg-section-head span {
          color: #4d6784;

          font-size: 8px;

          letter-spacing: 1px;
        }

        .vg-chart-wrapper {
          min-height: 280px;

          padding: 15px;

          overflow: hidden;

          border:
            1px solid
            rgba(148,163,184,.10);

          border-radius: 14px;

          background:
            rgba(8,19,34,.92);

          box-shadow:
            0 12px 35px
            rgba(0,0,0,.20);
        }

        .vg-panel-title {
          display: flex;

          justify-content: space-between;

          align-items: center;

          margin-bottom: 12px;
        }

        .vg-panel-title strong {
          color: #cbd8e8;

          font-size: 10px;
        }

        .vg-panel-title span {
          color: #3eff9c;

          font-size: 7px;

          letter-spacing: 1px;
        }

        /* ==================================================
           FOOTER
        ================================================== */

        .vg-footer {
          position: relative;

          z-index: 2;

          display: flex;

          justify-content: space-between;

          gap: 15px;

          margin-top: 25px;

          padding: 15px 5px;

          border-top:
            1px solid
            rgba(148,163,184,.08);

          color: #334155;

          font-family:
            Consolas,
            monospace;

          font-size: 7px;

          letter-spacing: .8px;
        }

        .vg-footer-live {
          color: #4ade80 !important;
        }

        /* ==================================================
           GENERAL ANIMATIONS
        ================================================== */

        @keyframes vgPulse {

          0%,100% {
            transform: scale(1);
            opacity: 1;
          }

          50% {
            transform: scale(1.5);
            opacity: .55;
          }

        }

        @keyframes vgRotate {

          from {
            transform:
              rotate(0deg);
          }

          to {
            transform:
              rotate(360deg);
          }

        }

        @keyframes vgCoreFloat {

          0%,100% {
            transform:
              translate(-50%,-50%)
              scale(1);
          }

          50% {
            transform:
              translate(-50%,-50%)
              scale(1.04);
          }

        }

        @keyframes vgFloat {

          0%,100% {
            transform:
              translateY(0);
          }

          50% {
            transform:
              translateY(-10px);
          }

        }

        @keyframes vgTickerIn {

          from {
            transform:
              translateX(35px);

            opacity: 0;
          }

          to {
            transform:
              translateX(0);

            opacity: 1;
          }

        }

        @keyframes vgTextIn {

          from {
            opacity: 0;

            transform:
              translate(-50%,125px)
              translateY(10px);
          }

          to {
            opacity: 1;

            transform:
              translate(-50%,125px);
          }

        }

        @keyframes vgVisualIn {

          from {
            opacity: 0;

            transform:
              scale(.9)
              translateY(8px);
          }

          to {
            opacity: 1;

            transform:
              scale(1)
              translateY(0);
          }

        }

        @keyframes vgScan {

          from {
            top: 0;
          }

          to {
            top: 100%;
          }

        }

        @keyframes vgBars {

          from {
            opacity: .35;

            transform:
              scaleY(.7);
          }

          to {
            opacity: 1;

            transform:
              scaleY(1.15);
          }

        }

        @keyframes vgPulseLine {

          0%,100% {
            opacity: .4;

            transform:
              scaleX(.7);
          }

          50% {
            opacity: 1;

            transform:
              scaleX(1);
          }

        }

        @keyframes vgAlert {

          from {
            opacity: .35;
          }

          to {
            opacity: 1;
          }

        }

        @keyframes vgAiOrb {

          0%,100% {
            transform:
              scale(1);
          }

          50% {
            transform:
              scale(1.08);

            box-shadow:
              0 0 30px
              rgba(168,85,247,.3);
          }

        }

        /* ==================================================
           RESPONSIVE
        ================================================== */

        @media(max-width:1100px) {

          .vg-stats-grid {
            grid-template-columns:
              repeat(2,1fr);
          }

          .vg-status-grid {
            grid-template-columns:
              repeat(3,1fr);
          }

        }

        @media(max-width:768px) {

          .vg-dashboard {
            padding: 12px;
          }

          .vg-header {
            flex-direction: column;

            align-items: flex-start;
          }

          .vg-header-right {
            width: 100%;

            justify-content:
              space-between;
          }

          .vg-title {
            font-size: 22px;
          }

          .vg-title span {
            display: block;

            margin-left: 0;

            margin-top: 4px;

            font-size: 16px;
          }

          .vg-hero {
            min-height: 350px;
          }

          .vg-floating {
            display: none;
          }

          .vg-orbit-area {
            transform:
              translate(-50%,-50%)
              scale(.75);
          }

          .vg-status-grid {
            grid-template-columns:
              repeat(2,1fr);
          }

          .vg-overview-grid {
            grid-template-columns: 1fr;
          }

          .vg-ai-metrics {
            grid-template-columns:
              repeat(3,1fr);
          }

        }

        @media(max-width:480px) {

          .vg-stats-grid {
            grid-template-columns: 1fr;
          }

          .vg-status-grid {
            grid-template-columns: 1fr;
          }

          .vg-ai-metrics {
            grid-template-columns: 1fr;
          }

          .vg-ticker-status {
            display: none;
          }

          .vg-rotating-text {
            width: 90%;

            font-size: 8px;
          }

        }

        /* ==================================================
           REDUCE MOTION ACCESSIBILITY
        ================================================== */

        @media(prefers-reduced-motion: reduce) {

          .vg-live-dot,
          .vg-orbit,
          .vg-core,
          .vg-floating,
          .vg-ticker-text,
          .vg-rotating-text,
          .vg-visual-content {
            animation: none !important;

            transition: none !important;
          }

        }

      `}</style>

    </div>
  );
}

// ==========================================================
// STATUS ITEM
// ==========================================================

function StatusItem({
  icon,
  title,
  value,
}) {

  return (

    <div className="vg-status-item">

      <div className="vg-status-item-top">

        <span className="vg-status-item-icon">
          {icon}
        </span>

        <span className="vg-status-indicator" />

      </div>

      <div className="vg-status-item-title">
        {title}
      </div>

      <div className="vg-status-item-value">
        {value}
      </div>

    </div>
  );
}

// ==========================================================
// OVERVIEW ITEM
// ==========================================================

function OverviewItem({
  icon,
  title,
  text,
}) {

  return (

    <div className="vg-overview-item">

      <div className="vg-overview-icon">
        {icon}
      </div>

      <div>

        <strong>
          {title}
        </strong>

        <p>
          {text}
        </p>

      </div>

    </div>
  );
}

export default Dashboard;