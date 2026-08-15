import React, { useEffect, useMemo, useState } from "react";

const API_BASE = "http://127.0.0.1:8000";
const REFRESH_INTERVAL = 10000;

// ============================================================
// HELPERS
// ============================================================

function normalizeStatus(value) {
  const s = String(value || "").trim().toUpperCase();

  if (s === "ONLINE") return "ONLINE";
  if (s === "OFFLINE") return "OFFLINE";

  return "UNKNOWN";
}

function statusColor(status) {
  if (status === "ONLINE") return "#20e28a";
  if (status === "OFFLINE") return "#ff4d5f";

  return "#f6b84b";
}

function formatTime(date) {
  if (!date) return "--";

  return date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

// ============================================================
// MAIN COMPONENT
// ============================================================

export default function NVR() {
  const [nvrs, setNvrs] = useState([]);
  const [cameras, setCameras] = useState([]);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("ALL");

  const [selectedNvr, setSelectedNvr] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  // ==========================================================
  // LOAD DATA
  // ==========================================================

  const loadData = async (manual = false) => {
    try {
      if (manual) {
        setRefreshing(true);
      }

      const [nvrResponse, cameraResponse] =
        await Promise.all([
          fetch(`${API_BASE}/nvr/status`),
          fetch(`${API_BASE}/cameras`),
        ]);

      if (!nvrResponse.ok) {
        throw new Error(
          `NVR API Error: ${nvrResponse.status}`
        );
      }

      if (!cameraResponse.ok) {
        throw new Error(
          `Camera API Error: ${cameraResponse.status}`
        );
      }

      const nvrData = await nvrResponse.json();
      const cameraData = await cameraResponse.json();

      setNvrs(
        Array.isArray(nvrData)
          ? nvrData
          : []
      );

      setCameras(
        Array.isArray(cameraData)
          ? cameraData
          : []
      );

      setLastUpdated(new Date());

      setError("");
    } catch (err) {
      console.error(
        "NVR Management Error:",
        err
      );

      setError(
        err?.message ||
          "Unable to connect to backend."
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // ==========================================================
  // AUTO REFRESH
  // ==========================================================

  useEffect(() => {
    loadData(true);

    const timer = setInterval(() => {
      loadData(false);
    }, REFRESH_INTERVAL);

    return () => clearInterval(timer);
  }, []);

  // ==========================================================
  // ENRICH NVR DATA
  // ==========================================================

  const enrichedNvrs = useMemo(() => {
    return nvrs.map((nvr, index) => {
      const name =
        String(
          nvr?.name ||
            `NVR-${index + 1}`
        );

      const status =
        normalizeStatus(
          nvr?.status
        );

      const nvrCameras =
        cameras.filter(
          (camera) =>
            String(
              camera?.nvr || ""
            )
              .trim()
              .toLowerCase() ===
            name
              .trim()
              .toLowerCase()
        );

      const total =
        nvrCameras.length;

      const online =
        nvrCameras.filter(
          (camera) =>
            String(
              camera?.status || ""
            )
              .trim()
              .toLowerCase() ===
            "online"
        ).length;

      const offline =
        nvrCameras.filter(
          (camera) =>
            String(
              camera?.status || ""
            )
              .trim()
              .toLowerCase() ===
            "offline"
        ).length;

      const unknown =
        total -
        online -
        offline;

      const health =
        total > 0
          ? Math.round(
              (online / total) *
                100
            )
          : 0;

      return {
        ...nvr,

        name,
        status,

        cameras:
          nvrCameras,

        totalCameras:
          total,

        onlineCameras:
          online,

        offlineCameras:
          offline,

        unknownCameras:
          unknown,

        health,

        score:
          status === "OFFLINE"
            ? 0
            : total === 0
            ? 70
            : health,
      };
    });
  }, [nvrs, cameras]);

  // ==========================================================
  // SUMMARY
  // ==========================================================

  const summary = useMemo(() => {
    const total =
      enrichedNvrs.length;

    const online =
      enrichedNvrs.filter(
        (nvr) =>
          nvr.status === "ONLINE"
      ).length;

    const offline =
      enrichedNvrs.filter(
        (nvr) =>
          nvr.status === "OFFLINE"
      ).length;

    const unknown =
      enrichedNvrs.filter(
        (nvr) =>
          nvr.status === "UNKNOWN"
      ).length;

    const totalCameras =
      enrichedNvrs.reduce(
        (sum, nvr) =>
          sum +
          nvr.totalCameras,
        0
      );

    const onlineCameras =
      enrichedNvrs.reduce(
        (sum, nvr) =>
          sum +
          nvr.onlineCameras,
        0
      );

    const offlineCameras =
      enrichedNvrs.reduce(
        (sum, nvr) =>
          sum +
          nvr.offlineCameras,
        0
      );

    const availability =
      total > 0
        ? Math.round(
            (online / total) *
              100
          )
        : 0;

    return {
      total,
      online,
      offline,
      unknown,
      totalCameras,
      onlineCameras,
      offlineCameras,
      availability,
    };
  }, [enrichedNvrs]);

  // ==========================================================
  // SEARCH + FILTER
  // ==========================================================

  const filteredNvrs =
    useMemo(() => {
      const q =
        search
          .trim()
          .toLowerCase();

      return enrichedNvrs.filter(
        (nvr) => {
          const matchesSearch =
            !q ||
            nvr.name
              .toLowerCase()
              .includes(q) ||
            String(
              nvr.ip || ""
            )
              .toLowerCase()
              .includes(q) ||
            String(
              nvr.port || ""
            )
              .toLowerCase()
              .includes(q);

          const matchesFilter =
            filter === "ALL" ||
            nvr.status ===
              filter;

          return (
            matchesSearch &&
            matchesFilter
          );
        }
      );
    }, [
      enrichedNvrs,
      search,
      filter,
    ]);

  // ==========================================================
  // LOADING
  // ==========================================================

  if (loading) {
    return (
      <div style={styles.loadingPage}>
        <div style={styles.loaderCircle}>
          VG
        </div>

        <div style={styles.loaderTitle}>
          VisionGuard AI
        </div>

        <div style={styles.loaderText}>
          Connecting to NVR infrastructure...
        </div>
      </div>
    );
  }

  // ==========================================================
  // PAGE
  // ==========================================================

  return (
    <div style={styles.page}>

      {/* ================================================== */}
      {/* HEADER */}
      {/* ================================================== */}

      <div style={styles.header}>

        <div style={styles.headerLeft}>

          <div style={styles.logo}>
            ◈
          </div>

          <div>

            <div style={styles.eyebrow}>
              VISIONGUARD AI
              <span style={styles.live}>
                ● LIVE
              </span>
            </div>

            <h1 style={styles.title}>
              NVR Command Center
            </h1>

            <div style={styles.subtitle}>
              Tata 1mg Security Infrastructure
            </div>

          </div>

        </div>

        <div style={styles.headerRight}>

          <div style={styles.sync}>
            <span style={styles.greenDot} />

            <div>
              <div style={styles.syncLabel}>
                LAST SYNCHRONIZED
              </div>

              <div style={styles.syncTime}>
                {formatTime(
                  lastUpdated
                )}
              </div>
            </div>
          </div>

          <button
            style={styles.refresh}
            onClick={() =>
              loadData(true)
            }
            disabled={refreshing}
          >
            {refreshing
              ? "SYNCING..."
              : "↻ SYNC"}
          </button>

        </div>

      </div>

      {/* ================================================== */}
      {/* ERROR */}
      {/* ================================================== */}

      {error && (
        <div style={styles.error}>
          <strong>
            Backend communication issue
          </strong>

          <span>
            {error}
          </span>

          <button
            onClick={() =>
              loadData(true)
            }
            style={styles.retry}
          >
            RETRY
          </button>
        </div>
      )}

      {/* ================================================== */}
      {/* TOP COMMAND BAR */}
      {/* ================================================== */}

      <div style={styles.commandBar}>

        <div>
          <div style={styles.smallBlue}>
            INFRASTRUCTURE STATUS
          </div>

          <div style={styles.commandTitle}>
            Connected NVR Systems
          </div>
        </div>

        <div style={styles.commandStats}>

          <MiniStat
            value={summary.total}
            label="TOTAL NVR"
          />

          <MiniStat
            value={summary.online}
            label="ONLINE"
            green
          />

          <MiniStat
            value={summary.offline}
            label="OFFLINE"
            red
          />

          <MiniStat
            value={summary.totalCameras}
            label="CAMERAS"
            blue
          />

        </div>

      </div>

      {/* ================================================== */}
      {/* CONNECTED NVR STATUS STRIP */}
      {/* ================================================== */}

      <div style={styles.statusStrip}>

        <div style={styles.stripTitle}>
          <span style={styles.greenDot} />
          CONNECTED NVR STATUS
        </div>

        <div style={styles.stripList}>

          {enrichedNvrs.map(
            (nvr) => {

              const color =
                statusColor(
                  nvr.status
                );

              return (
                <button
                  key={
                    nvr.name
                  }
                  style={{
                    ...styles.stripNvr,
                    borderColor:
                      `${color}33`,
                  }}
                  onClick={() =>
                    setSelectedNvr(
                      nvr
                    )
                  }
                >

                  <span
                    style={{
                      ...styles.stripDot,
                      background:
                        color,
                    }}
                  />

                  <strong>
                    {nvr.name}
                  </strong>

                  <span
                    style={
                      styles.stripIp
                    }
                  >
                    {nvr.ip}
                  </span>

                  <span
                    style={{
                      color,
                      fontWeight: 900,
                    }}
                  >
                    {nvr.status}
                  </span>

                </button>
              );
            }
          )}

        </div>
      </div>

      {/* ================================================== */}
      {/* OVERVIEW */}
      {/* ================================================== */}

      <div style={styles.sectionHead}>

        <div>
          <div style={styles.smallBlue}>
            LIVE TELEMETRY
          </div>

          <h2 style={styles.sectionTitle}>
            Infrastructure Overview
          </h2>
        </div>

        <div style={styles.availability}>
          <span style={styles.greenDot} />
          {summary.availability}%
          NVR availability
        </div>

      </div>

      <div style={styles.overviewGrid}>

        <OverviewCard
          label="NVR AVAILABILITY"
          value={`${summary.availability}%`}
          detail={`${summary.online} of ${summary.total} NVRs online`}
          progress={
            summary.availability
          }
          color="#20e28a"
        />

        <OverviewCard
          label="CAMERA FLEET"
          value={
            summary.totalCameras
          }
          detail={`${summary.onlineCameras} cameras online`}
          progress={
            summary.totalCameras
              ? Math.round(
                  (summary.onlineCameras /
                    summary.totalCameras) *
                    100
                )
              : 0
          }
          color="#44d9ff"
        />

        <OverviewCard
          label="ATTENTION REQUIRED"
          value={
            summary.offline +
            summary.offlineCameras
          }
          detail={
            summary.offline +
              summary.offlineCameras ===
            0
              ? "All systems healthy"
              : "Systems need attention"
          }
          progress={0}
          color={
            summary.offline ||
            summary.offlineCameras
              ? "#ff4d5f"
              : "#20e28a"
          }
        />

      </div>

      {/* ================================================== */}
      {/* SEARCH */}
      {/* ================================================== */}

      <div style={styles.control}>

        <div style={styles.searchBox}>

          <span style={styles.searchIcon}>
            ⌕
          </span>

          <input
            value={search}
            onChange={(e) =>
              setSearch(
                e.target.value
              )
            }
            placeholder="Search NVR name, IP address or port..."
            style={styles.input}
          />

        </div>

        <div style={styles.filters}>

          {[
            ["ALL", "ALL"],
            ["ONLINE", "ONLINE"],
            ["OFFLINE", "OFFLINE"],
            ["UNKNOWN", "UNKNOWN"],
          ].map(
            ([value, label]) => (
              <button
                key={value}
                onClick={() =>
                  setFilter(
                    value
                  )
                }
                style={{
                  ...styles.filter,
                  ...(filter ===
                  value
                    ? styles.filterActive
                    : {}),
                }}
              >
                {label}
              </button>
            )
          )}

        </div>

      </div>

      {/* ================================================== */}
      {/* NVR LIST */}
      {/* ================================================== */}

      <div style={styles.sectionHead}>

        <div>
          <div style={styles.smallBlue}>
            NVR FLEET
          </div>

          <h2 style={styles.sectionTitle}>
            Live NVR Infrastructure
          </h2>
        </div>

        <div style={styles.result}>
          {filteredNvrs.length}
          {" "}systems visible
        </div>

      </div>

      <div style={styles.grid}>

        {filteredNvrs.map(
          (nvr, index) => (

            <NvrCard
              key={
                `${nvr.name}-${nvr.ip}`
              }
              nvr={nvr}
              index={index}
              onClick={() =>
                setSelectedNvr(
                  nvr
                )
              }
            />

          )
        )}

      </div>

      {/* ================================================== */}
      {/* EMPTY */}
      {/* ================================================== */}

      {filteredNvrs.length ===
        0 && (
        <div style={styles.empty}>
          <div style={styles.emptyIcon}>
            ⌕
          </div>

          <h3>
            No NVR found
          </h3>

          <p>
            Change search or filter.
          </p>
        </div>
      )}

      {/* ================================================== */}
      {/* FOOTER */}
      {/* ================================================== */}

      <div style={styles.footer}>

        <span>
          <span
            style={
              styles.greenDot
            }
          />{" "}
          VisionGuard AI Monitoring
        </span>

        <span>
          Auto Refresh:{" "}
          <strong>
            10 seconds
          </strong>
        </span>

        <span>
          Last Sync:{" "}
          <strong>
            {formatTime(
              lastUpdated
            )}
          </strong>
        </span>

      </div>

      {/* ================================================== */}
      {/* DETAILS */}
      {/* ================================================== */}

      {selectedNvr && (
        <NvrDetails
          nvr={selectedNvr}
          onClose={() =>
            setSelectedNvr(null)
          }
        />
      )}

    </div>
  );
}

// ============================================================
// MINI STAT
// ============================================================

function MiniStat({
  value,
  label,
  green,
  red,
  blue,
}) {
  let color = "#75b7ff";

  if (green) color = "#20e28a";
  if (red) color = "#ff5c6b";
  if (blue) color = "#44d9ff";

  return (
    <div style={styles.miniStat}>
      <div
        style={{
          ...styles.miniValue,
          color,
        }}
      >
        {value}
      </div>

      <div style={styles.miniLabel}>
        {label}
      </div>
    </div>
  );
}

// ============================================================
// OVERVIEW CARD
// ============================================================

function OverviewCard({
  label,
  value,
  detail,
  progress,
  color,
}) {
  return (
    <div style={styles.overviewCard}>

      <div style={styles.cardLabel}>
        {label}
      </div>

      <div
        style={{
          ...styles.overviewValue,
          color,
        }}
      >
        {value}
      </div>

      <div style={styles.overviewDetail}>
        {detail}
      </div>

      <div style={styles.progress}>
        <div
          style={{
            ...styles.progressFill,
            width: `${progress}%`,
            background: color,
          }}
        />
      </div>

    </div>
  );
}

// ============================================================
// NVR CARD
// ============================================================

function NvrCard({
  nvr,
  index,
  onClick,
}) {
  const color =
    statusColor(
      nvr.status
    );

  return (
    <div
      style={{
        ...styles.nvrCard,
        borderColor:
          `${color}38`,
      }}
    >

      {/* HEADER */}

      <div style={styles.nvrHeader}>

        <div style={styles.nvrIdentity}>

          <div
            style={{
              ...styles.nvrNumber,
              color,
              borderColor:
                `${color}55`,
              background:
                `${color}0d`,
            }}
          >
            {String(
              index + 1
            ).padStart(2, "0")}
          </div>

          <div>

            <div
              style={
                styles.systemText
              }
            >
              NETWORK VIDEO RECORDER
            </div>

            <div
              style={
                styles.nvrName
              }
            >
              {nvr.name}
            </div>

          </div>

        </div>

        <div
          style={{
            ...styles.status,
            color,
            borderColor:
              `${color}44`,
          }}
        >
          <span
            style={{
              ...styles.statusDot,
              background: color,
            }}
          />

          {nvr.status}
        </div>

      </div>

      {/* NETWORK */}

      <div style={styles.network}>

        <div>
          <div
            style={
              styles.networkLabel
            }
          >
            IP ADDRESS
          </div>

          <div
            style={
              styles.ip
            }
          >
            {nvr.ip || "--"}
          </div>
        </div>

        <div style={styles.divider} />

        <div>
          <div
            style={
              styles.networkLabel
            }
          >
            PORT
          </div>

          <div
            style={
              styles.port
            }
          >
            {nvr.port || "--"}
          </div>
        </div>

      </div>

      {/* CAMERA COUNTS */}

      <div style={styles.cameraStats}>

        <Stat
          label="CAMERAS"
          value={
            nvr.totalCameras
          }
        />

        <Stat
          label="ONLINE"
          value={
            nvr.onlineCameras
          }
          color="#20e28a"
        />

        <Stat
          label="OFFLINE"
          value={
            nvr.offlineCameras
          }
          color="#ff5c6b"
        />

      </div>

      {/* HEALTH */}

      <div style={styles.health}>

        <div style={styles.healthHead}>

          <span>
            CAMERA HEALTH
          </span>

          <strong>
            {nvr.status ===
            "OFFLINE"
              ? "N/A"
              : `${nvr.health}%`}
          </strong>

        </div>

        <div
          style={
            styles.healthTrack
          }
        >
          <div
            style={{
              ...styles.healthFill,
              width:
                nvr.status ===
                "OFFLINE"
                  ? "0%"
                  : `${nvr.health}%`,
              background:
                nvr.health >=
                90
                  ? "#20e28a"
                  : nvr.health >=
                    60
                  ? "#f6b84b"
                  : "#ff4d5f",
            }}
          />
        </div>

      </div>

      {/* BOTTOM */}

      <div style={styles.nvrBottom}>

        <div>
          <div
            style={
              styles.scoreLabel
            }
          >
            OPERATIONAL SCORE
          </div>

          <div
            style={
              styles.score
            }
          >
            {nvr.status ===
            "OFFLINE"
              ? "—"
              : `${nvr.score}/100`}
          </div>
        </div>

        <div
          style={
            styles.monitoring
          }
        >
          <span
            style={{
              ...styles.statusDot,
              background:
                color,
            }}
          />

          {nvr.status ===
          "ONLINE"
            ? "Monitoring Active"
            : nvr.status ===
              "OFFLINE"
            ? "Connection Lost"
            : "Awaiting Status"}
        </div>

      </div>

      {/* BUTTON */}

      <button
        style={styles.detailsButton}
        onClick={onClick}
      >
        OPEN NVR INTELLIGENCE
        <span>→</span>
      </button>

    </div>
  );
}

// ============================================================
// STAT
// ============================================================

function Stat({
  label,
  value,
  color,
}) {
  return (
    <div style={styles.stat}>

      <div
        style={{
          ...styles.statValue,
          color:
            color ||
            "#72b5ff",
        }}
      >
        {value}
      </div>

      <div
        style={
          styles.statLabel
        }
      >
        {label}
      </div>

    </div>
  );
}

// ============================================================
// DETAILS DRAWER
// ============================================================

function NvrDetails({
  nvr,
  onClose,
}) {
  const color =
    statusColor(
      nvr.status
    );

  return (
    <div
      style={styles.overlay}
      onClick={onClose}
    >

      <div
        style={styles.drawer}
        onClick={(e) =>
          e.stopPropagation()
        }
      >

        <div
          style={
            styles.drawerHeader
          }
        >

          <div>

            <div
              style={
                styles.drawerEyebrow
              }
            >
              NVR INTELLIGENCE
            </div>

            <h2
              style={
                styles.drawerTitle
              }
            >
              {nvr.name}
            </h2>

          </div>

          <button
            style={
              styles.close
            }
            onClick={onClose}
          >
            ×
          </button>

        </div>

        {/* STATUS */}

        <div
          style={{
            ...styles.drawerStatus,
            borderColor:
              `${color}44`,
          }}
        >

          <div>

            <div
              style={
                styles.drawerLabel
              }
            >
              CURRENT STATUS
            </div>

            <div
              style={{
                ...styles.drawerStatusValue,
                color,
              }}
            >
              ● {nvr.status}
            </div>

          </div>

          <div>

            <div
              style={
                styles.drawerLabel
              }
            >
              SCORE
            </div>

            <div
              style={
                styles.drawerScore
              }
            >
              {nvr.status ===
              "OFFLINE"
                ? "N/A"
                : `${nvr.score}/100`}
            </div>

          </div>

        </div>

        {/* NETWORK */}

        <Panel title="NETWORK IDENTITY">

          <Row
            label="NVR NAME"
            value={
              nvr.name
            }
          />

          <Row
            label="IP ADDRESS"
            value={
              nvr.ip
            }
            mono
          />

          <Row
            label="HTTP PORT"
            value={
              nvr.port
            }
            mono
          />

          <Row
            label="STATUS"
            value={
              nvr.status
            }
          />

        </Panel>

        {/* CAMERAS */}

        <Panel title="CAMERA FLEET">

          <div
            style={
              styles.bigNumber
            }
          >
            {nvr.totalCameras}
          </div>

          <div
            style={
              styles.bigLabel
            }
          >
            DISCOVERED CAMERAS
          </div>

          <div
            style={
              styles.breakdown
            }
          >

            <Breakdown
              value={
                nvr.onlineCameras
              }
              label="ONLINE"
              color="#20e28a"
            />

            <Breakdown
              value={
                nvr.offlineCameras
              }
              label="OFFLINE"
              color="#ff4d5f"
            />

            <Breakdown
              value={
                nvr.unknownCameras
              }
              label="UNKNOWN"
              color="#f6b84b"
            />

          </div>

        </Panel>

        {/* CAMERA LIST */}

        <Panel title="DISCOVERED CHANNELS">

          {nvr.cameras.length ===
          0 ? (
            <div
              style={
                styles.noCamera
              }
            >
              No camera records available.
            </div>
          ) : (
            <div
              style={
                styles.cameraList
              }
            >

              {nvr.cameras.map(
                (camera) => {

                  const online =
                    String(
                      camera?.status ||
                        ""
                    )
                      .trim()
                      .toLowerCase() ===
                    "online";

                  return (
                    <div
                      key={`${nvr.name}-${camera.id}`}
                      style={
                        styles.cameraRow
                      }
                    >

                      <div>

                        <div
                          style={
                            styles.cameraName
                          }
                        >
                          {camera.name ||
                            `Camera ${camera.id}`}
                        </div>

                        <div
                          style={
                            styles.cameraMeta
                          }
                        >
                          CH {camera.id}

                          {camera.ip
                            ? ` • ${camera.ip}`
                            : ""}
                        </div>

                      </div>

                      <div
                        style={{
                          color:
                            online
                              ? "#20e28a"
                              : "#ff5c6b",
                          fontSize:
                            "8px",
                          fontWeight:
                            900,
                        }}
                      >
                        ●{" "}
                        {String(
                          camera.status ||
                            "UNKNOWN"
                        ).toUpperCase()}
                      </div>

                    </div>
                  );
                }
              )}

            </div>
          )}

        </Panel>

      </div>

    </div>
  );
}

// ============================================================
// PANEL
// ============================================================

function Panel({
  title,
  children,
}) {
  return (
    <div style={styles.panel}>

      <div
        style={
          styles.panelTitle
        }
      >
        {title}
      </div>

      {children}

    </div>
  );
}

// ============================================================
// ROW
// ============================================================

function Row({
  label,
  value,
  mono,
}) {
  return (
    <div
      style={
        styles.row
      }
    >

      <span>
        {label}
      </span>

      <strong
        style={
          mono
            ? {
                fontFamily:
                  "Consolas, monospace",
              }
            : {}
        }
      >
        {value || "--"}
      </strong>

    </div>
  );
}

// ============================================================
// BREAKDOWN
// ============================================================

function Breakdown({
  value,
  label,
  color,
}) {
  return (
    <div
      style={
        styles.breakdownItem
      }
    >

      <span
        style={{
          ...styles.breakdownDot,
          background:
            color,
        }}
      />

      <strong>
        {value}
      </strong>

      <span>
        {label}
      </span>

    </div>
  );
}

// ============================================================
// STYLES
// ============================================================

const styles = {

  page: {
    minHeight: "100vh",
    padding: "25px",
    boxSizing: "border-box",
    color: "#edf6ff",
    background:
      "radial-gradient(circle at 80% 0%, rgba(36,112,210,.18), transparent 32%), #030a16",
    fontFamily:
      "Inter, Segoe UI, Arial, sans-serif",
  },

  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "22px 24px",
    borderRadius: "22px",
    background:
      "linear-gradient(135deg,#092442,#04101f)",
    border:
      "1px solid rgba(70,145,235,.25)",
    boxShadow:
      "0 20px 60px rgba(0,0,0,.3)",
  },

  headerLeft: {
    display: "flex",
    alignItems: "center",
    gap: "16px",
  },

  logo: {
    width: "55px",
    height: "55px",
    borderRadius: "15px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "26px",
    background:
      "linear-gradient(135deg,#287ff3,#123e91)",
    boxShadow:
      "0 10px 30px rgba(30,110,240,.3)",
  },

  eyebrow: {
    color: "#5ba7ff",
    fontSize: "9px",
    fontWeight: 900,
    letterSpacing: "2px",
  },

  live: {
    marginLeft: "10px",
    color: "#20e28a",
  },

  title: {
    margin: "6px 0 0",
    fontSize: "28px",
    fontWeight: 900,
  },

  subtitle: {
    marginTop: "5px",
    color: "#7089a6",
    fontSize: "10px",
  },

  headerRight: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
  },

  sync: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    padding: "9px 12px",
    borderRadius: "10px",
    background:
      "rgba(20,48,78,.5)",
  },

  greenDot: {
    width: "7px",
    height: "7px",
    display: "inline-block",
    borderRadius: "50%",
    background: "#20e28a",
    boxShadow:
      "0 0 10px #20e28a",
  },

  syncLabel: {
    color: "#59748f",
    fontSize: "7px",
    fontWeight: 900,
  },

  syncTime: {
    marginTop: "3px",
    color: "#b5d4f5",
    fontSize: "10px",
    fontFamily:
      "Consolas, monospace",
  },

  refresh: {
    padding: "10px 14px",
    borderRadius: "10px",
    border:
      "1px solid rgba(76,146,226,.3)",
    background:
      "rgba(37,105,190,.15)",
    color: "#9ccaff",
    cursor: "pointer",
    fontWeight: 900,
    fontSize: "9px",
  },

  error: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    marginTop: "14px",
    padding: "12px 15px",
    borderRadius: "12px",
    background:
      "rgba(255,77,95,.08)",
    border:
      "1px solid rgba(255,77,95,.25)",
    color: "#ff7180",
    fontSize: "10px",
  },

  retry: {
    marginLeft: "auto",
    border: "none",
    borderRadius: "7px",
    padding: "7px 11px",
    background: "#d94758",
    color: "#fff",
    cursor: "pointer",
    fontSize: "8px",
    fontWeight: 900,
  },

  commandBar: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: "15px",
    padding: "16px 20px",
    borderRadius: "15px",
    background:
      "linear-gradient(90deg,#081e36,#061525)",
    border:
      "1px solid rgba(73,132,194,.16)",
  },

  smallBlue: {
    color: "#4e9ae8",
    fontSize: "8px",
    fontWeight: 900,
    letterSpacing: "1.5px",
  },

  commandTitle: {
    marginTop: "5px",
    fontSize: "17px",
    fontWeight: 900,
  },

  commandStats: {
    display: "flex",
    gap: "30px",
  },

  miniStat: {
    textAlign: "right",
  },

  miniValue: {
    fontSize: "21px",
    fontWeight: 900,
  },

  miniLabel: {
    marginTop: "4px",
    color: "#536e8a",
    fontSize: "7px",
    fontWeight: 900,
    letterSpacing: "1px",
  },

  statusStrip: {
    display: "flex",
    alignItems: "center",
    gap: "14px",
    marginTop: "10px",
    padding: "9px",
    borderRadius: "12px",
    background:
      "rgba(4,16,30,.85)",
    border:
      "1px solid rgba(72,123,174,.13)",
  },

  stripTitle: {
    minWidth: "145px",
    color: "#66809d",
    fontSize: "8px",
    fontWeight: 900,
  },

  stripList: {
    display: "flex",
    gap: "7px",
    overflowX: "auto",
    flex: 1,
  },

  stripNvr: {
    display: "flex",
    alignItems: "center",
    gap: "7px",
    minWidth: "190px",
    padding: "8px 10px",
    borderRadius: "8px",
    background:
      "rgba(10,31,51,.7)",
    color: "#d8eaff",
    cursor: "pointer",
    fontSize: "8px",
  },

  stripDot: {
    width: "6px",
    height: "6px",
    borderRadius: "50%",
  },

  stripIp: {
    marginLeft: "auto",
    color: "#58728e",
    fontFamily:
      "Consolas, monospace",
  },

  sectionHead: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "end",
    marginTop: "23px",
    marginBottom: "11px",
  },

  sectionTitle: {
    margin: "5px 0 0",
    fontSize: "19px",
    fontWeight: 900,
  },

  availability: {
    display: "flex",
    alignItems: "center",
    gap: "7px",
    padding: "8px 10px",
    borderRadius: "8px",
    background:
      "rgba(32,226,138,.06)",
    color: "#6f9c89",
    fontSize: "9px",
  },

  overviewGrid: {
    display: "grid",
    gridTemplateColumns:
      "repeat(3,1fr)",
    gap: "11px",
  },

  overviewCard: {
    padding: "16px",
    borderRadius: "15px",
    background:
      "linear-gradient(145deg,#0a2038,#061425)",
    border:
      "1px solid rgba(74,128,181,.15)",
  },

  cardLabel: {
    color: "#5e7894",
    fontSize: "8px",
    fontWeight: 900,
    letterSpacing: "1px",
  },

  overviewValue: {
    marginTop: "10px",
    fontSize: "27px",
    fontWeight: 900,
  },

  overviewDetail: {
    marginTop: "3px",
    color: "#607994",
    fontSize: "9px",
  },

  progress: {
    height: "4px",
    marginTop: "12px",
    borderRadius: "10px",
    background:
      "rgba(75,110,145,.15)",
    overflow: "hidden",
  },

  progressFill: {
    height: "100%",
    borderRadius: "10px",
  },

  control: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    marginTop: "17px",
    padding: "9px",
    borderRadius: "12px",
    background:
      "rgba(5,19,35,.85)",
    border:
      "1px solid rgba(73,126,181,.14)",
  },

  searchBox: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    flex: 1,
    padding: "0 10px",
  },

  searchIcon: {
    color: "#4e93d8",
    fontSize: "18px",
  },

  input: {
    width: "100%",
    border: "none",
    outline: "none",
    background: "transparent",
    color: "#e9f5ff",
    fontSize: "10px",
  },

  filters: {
    display: "flex",
    gap: "4px",
  },

  filter: {
    padding: "8px 11px",
    borderRadius: "8px",
    border:
      "1px solid transparent",
    background:
      "transparent",
    color: "#607b98",
    cursor: "pointer",
    fontSize: "8px",
    fontWeight: 900,
  },

  filterActive: {
    color: "#91c5ff",
    background:
      "rgba(46,122,229,.15)",
    border:
      "1px solid rgba(46,122,229,.28)",
  },

  result: {
    color: "#55708c",
    fontSize: "9px",
  },

  grid: {
    display: "grid",
    gridTemplateColumns:
      "repeat(3,minmax(0,1fr))",
    gap: "13px",
  },

  nvrCard: {
    padding: "17px",
    borderRadius: "18px",
    background:
      "linear-gradient(150deg,#0a1d34,#04101f)",
    border: "1px solid",
    boxShadow:
      "0 15px 40px rgba(0,0,0,.2)",
  },

  nvrHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: "10px",
  },

  nvrIdentity: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    minWidth: 0,
  },

  nvrNumber: {
    width: "39px",
    height: "39px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0,
    borderRadius: "11px",
    border: "1px solid",
    fontSize: "11px",
    fontWeight: 900,
  },

  systemText: {
    color: "#506b87",
    fontSize: "7px",
    fontWeight: 900,
    letterSpacing: "1px",
  },

  nvrName: {
    marginTop: "4px",
    fontSize: "17px",
    fontWeight: 900,
  },

  status: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    padding: "6px 8px",
    borderRadius: "8px",
    border: "1px solid",
    fontSize: "7px",
    fontWeight: 900,
  },

  statusDot: {
    width: "6px",
    height: "6px",
    borderRadius: "50%",
  },

  network: {
    display: "grid",
    gridTemplateColumns:
      "1fr auto 1fr",
    alignItems: "center",
    gap: "12px",
    marginTop: "14px",
    padding: "11px",
    borderRadius: "10px",
    background:
      "rgba(1,9,19,.55)",
  },

  networkLabel: {
    color: "#506a85",
    fontSize: "7px",
    fontWeight: 900,
    letterSpacing: "1px",
  },

  ip: {
    marginTop: "4px",
    color: "#a9d4ff",
    fontSize: "11px",
    fontFamily:
      "Consolas, monospace",
  },

  port: {
    marginTop: "4px",
    color: "#91abc5",
    fontSize: "11px",
    fontFamily:
      "Consolas, monospace",
  },

  divider: {
    width: "1px",
    height: "27px",
    background:
      "rgba(83,128,171,.15)",
  },

  cameraStats: {
    display: "grid",
    gridTemplateColumns:
      "repeat(3,1fr)",
    gap: "7px",
    marginTop: "9px",
  },

  stat: {
    padding: "9px",
    borderRadius: "9px",
    background:
      "rgba(18,42,68,.45)",
  },

  statValue: {
    fontSize: "17px",
    fontWeight: 900,
  },

  statLabel: {
    marginTop: "3px",
    color: "#536e8a",
    fontSize: "7px",
    fontWeight: 900,
  },

  health: {
    marginTop: "13px",
  },

  healthHead: {
    display: "flex",
    justifyContent: "space-between",
    color: "#607994",
    fontSize: "7px",
    fontWeight: 900,
    letterSpacing: "1px",
  },

  healthTrack: {
    height: "4px",
    marginTop: "6px",
    borderRadius: "10px",
    background:
      "rgba(70,105,140,.15)",
    overflow: "hidden",
  },

  healthFill: {
    height: "100%",
    borderRadius: "10px",
  },

  nvrBottom: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: "13px",
  },

  scoreLabel: {
    color: "#506a87",
    fontSize: "7px",
    fontWeight: 900,
  },

  score: {
    marginTop: "3px",
    color: "#b8d7f7",
    fontSize: "13px",
    fontWeight: 900,
  },

  monitoring: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    color: "#6d87a3",
    fontSize: "8px",
  },

  detailsButton: {
    width: "100%",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginTop: "13px",
    padding: "9px 11px",
    borderRadius: "9px",
    border:
      "1px solid rgba(70,137,214,.2)",
    background:
      "rgba(35,91,155,.08)",
    color: "#83baf1",
    cursor: "pointer",
    fontSize: "8px",
    fontWeight: 900,
    letterSpacing: ".8px",
  },

  empty: {
    padding: "60px",
    textAlign: "center",
    color: "#607994",
  },

  emptyIcon: {
    fontSize: "35px",
    color: "#315b85",
  },

  footer: {
    display: "flex",
    justifyContent: "space-between",
    marginTop: "22px",
    padding:
      "13px 3px 5px",
    borderTop:
      "1px solid rgba(73,116,157,.12)",
    color: "#506a86",
    fontSize: "8px",
  },

  overlay: {
    position: "fixed",
    inset: 0,
    zIndex: 9999,
    display: "flex",
    justifyContent: "flex-end",
    background:
      "rgba(1,6,13,.76)",
    backdropFilter:
      "blur(6px)",
  },

  drawer: {
    width: "480px",
    maxWidth: "94vw",
    height: "100%",
    overflowY: "auto",
    padding: "25px",
    boxSizing: "border-box",
    background:
      "linear-gradient(180deg,#071a30,#030b17)",
    borderLeft:
      "1px solid rgba(70,137,211,.25)",
    boxShadow:
      "-25px 0 80px rgba(0,0,0,.5)",
  },

  drawerHeader: {
    display: "flex",
    justifyContent: "space-between",
  },

  drawerEyebrow: {
    color: "#4f99e8",
    fontSize: "8px",
    fontWeight: 900,
    letterSpacing: "1.5px",
  },

  drawerTitle: {
    margin: "6px 0 0",
    fontSize: "25px",
  },

  close: {
    width: "34px",
    height: "34px",
    borderRadius: "9px",
    border:
      "1px solid rgba(91,135,180,.2)",
    background:
      "rgba(18,43,70,.5)",
    color: "#a0bad5",
    fontSize: "22px",
    cursor: "pointer",
  },

  drawerStatus: {
    display: "flex",
    justifyContent: "space-between",
    marginTop: "20px",
    padding: "15px",
    borderRadius: "13px",
    background:
      "rgba(10,29,50,.72)",
    border: "1px solid",
  },

  drawerLabel: {
    color: "#526e8b",
    fontSize: "7px",
    fontWeight: 900,
  },

  drawerStatusValue: {
    marginTop: "6px",
    fontSize: "16px",
    fontWeight: 900,
  },

  drawerScore: {
    marginTop: "6px",
    color: "#a8d2fa",
    fontSize: "17px",
    fontWeight: 900,
  },

  panel: {
    marginTop: "12px",
    padding: "15px",
    borderRadius: "13px",
    background:
      "rgba(11,30,51,.72)",
    border:
      "1px solid rgba(75,126,175,.13)",
  },

  panelTitle: {
    marginBottom: "11px",
    color: "#4f91d0",
    fontSize: "8px",
    fontWeight: 900,
    letterSpacing: "1.4px",
  },

  row: {
    display: "flex",
    justifyContent: "space-between",
    padding: "8px 0",
    borderBottom:
      "1px solid rgba(76,119,159,.08)",
    color: "#617c99",
    fontSize: "10px",
  },

  bigNumber: {
    color: "#73b8ff",
    fontSize: "38px",
    fontWeight: 900,
  },

  bigLabel: {
    color: "#5b7592",
    fontSize: "8px",
  },

  breakdown: {
    display: "flex",
    gap: "15px",
    marginTop: "15px",
    flexWrap: "wrap",
  },

  breakdownItem: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    color: "#708aa6",
    fontSize: "9px",
  },

  breakdownDot: {
    width: "7px",
    height: "7px",
    borderRadius: "50%",
  },

  cameraList: {
    display: "flex",
    flexDirection: "column",
    gap: "6px",
    maxHeight: "420px",
    overflowY: "auto",
  },

  cameraRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: "10px",
    padding: "9px",
    borderRadius: "8px",
    background:
      "rgba(2,13,27,.62)",
  },

  cameraName: {
    fontSize: "10px",
    fontWeight: 800,
  },

  cameraMeta: {
    marginTop: "3px",
    color: "#506b88",
    fontSize: "8px",
    fontFamily:
      "Consolas, monospace",
  },

  noCamera: {
    padding: "20px",
    textAlign: "center",
    color: "#607994",
    fontSize: "10px",
  },

  loadingPage: {
    minHeight: "80vh",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    background: "#030a16",
    color: "#fff",
  },

  loaderCircle: {
    width: "72px",
    height: "72px",
    borderRadius: "50%",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    color: "#69b2ff",
    border:
      "1px solid rgba(75,160,255,.35)",
    boxShadow:
      "0 0 50px rgba(41,128,255,.2)",
    fontWeight: 900,
  },

  loaderTitle: {
    marginTop: "17px",
    fontSize: "19px",
    fontWeight: 900,
  },

  loaderText: {
    marginTop: "6px",
    color: "#607a97",
    fontSize: "10px",
  },
};