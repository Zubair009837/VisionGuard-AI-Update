import { NavLink } from "react-router-dom";
import {
  FaHome,
  FaVideo,
  FaServer,
  FaBell,
  FaCog,
  FaChartBar,
  FaMapMarkedAlt,
  FaDatabase,
  FaUsers,
  FaFileAlt,
  FaBroadcastTower,
  FaCheckCircle,
  FaCrown,
} from "react-icons/fa";
import profile from "../../assets/profile.jpg";
import "./Sidebar.css";

function Sidebar() {

  const menuItems = [
    { name: "Dashboard", icon: <FaHome />, path: "/" },
    { name: "Live View", icon: <FaBroadcastTower />, path: "/live" },
    { name: "Cameras", icon: <FaVideo />, path: "/cameras" },
    { name: "NVR", icon: <FaServer />, path: "/nvr" },
    { name: "Alerts", icon: <FaBell />, path: "/alerts" },
    { name: "Camera Movement", icon: <FaBroadcastTower />, path: "/camera-movements" },
    { name: "Analytics", icon: <FaChartBar />, path: "/analytics" },
    { name: "Floor Map", icon: <FaMapMarkedAlt />, path: "/floor-map" },
    { name: "Storage", icon: <FaDatabase />, path: "/storage" },
    { name: "Users", icon: <FaUsers />, path: "/users" },
    { name: "Reports", icon: <FaFileAlt />, path: "/reports" },
    { name: "Settings", icon: <FaCog />, path: "/settings" },
  ];

  return (

    <aside className="sidebar">

            {/* Owner Profile */}

      <div className="owner-card">

        <img
          src={profile}
          alt="Mohd Zubair Khan"
          className="owner-photo"
        />

        <h3 className="owner-name">
          Zubair Khan
        </h3>
<div className="owner-tagline">
    Owned & Developed By
</div>

        <div className="verified-badge">

          <FaCheckCircle />

          <span>Verified Developer</span>

        </div>

        <p className="owner-role">

          Owner & Lead Developer

        </p>

        <div className="owner-status">

          <span className="status-green"></span>

          System Online

        </div>

      </div>

      {/* Navigation */}

      <nav className="menu">
        {menuItems.map((item) => (

          <NavLink
            key={item.name}
            to={item.path}
            className={({ isActive }) =>
              isActive ? "menu-item active" : "menu-item"
            }
          >

            <span className="icon">
              {item.icon}
            </span>

            <span className="menu-text">
              {item.name}
            </span>

          </NavLink>

        ))}

      </nav>

      {/* Owner Information */}

      <div className="developer-box">

        <div className="developer-title">

          <strong>Owned By</strong>

        </div>

        <div className="developer-name">

          👑 Zubair Khan

        </div>

        <div className="developer-desc">
    Enterprise Security Platform Creator
</div>

      </div>

      {/* Footer */}

      <div className="sidebar-footer">

        <div className="status-dot"></div>

        <span>

          Enterprise Monitoring Active

        </span>

      </div>
    </aside>

  );

}

export default Sidebar;