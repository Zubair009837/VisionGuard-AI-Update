import "./Navbar.css";
import {
  FaBell,
  FaSearch,
  FaUserCircle,
  FaCircle,
  FaShieldAlt,
} from "react-icons/fa";

function Navbar({ time }) {
  return (
    <header className="navbar">

      {/* Left Section */}
      <div className="navbar-left">

        <div className="logo-box">
          <FaShieldAlt className="logo-icon" />
        </div>

        <div className="logo-text">
          <h2>
            VisionGuard <span className="brand-ai">AI</span>
          </h2>

          <p>TATA 1MG Security Operations Center</p>
        </div>

      </div>

      {/* Center Section */}
      <div className="navbar-center">

        <div className="search-box">
          <FaSearch className="search-icon" />

          <input
            type="text"
            placeholder="Search Camera, NVR, IP Address..."
          />
        </div>

      </div>

      {/* Right Section */}
      <div className="navbar-right">

        <div className="live-status">
          <FaCircle className="live-dot" />
          <span>Live Monitoring</span>
        </div>

        <div className="clock">
          🕒 {time}
        </div>

        <div className="notification">
          <FaBell />
          <span className="badge">3</span>
        </div>

        <div className="profile">

          <FaUserCircle className="avatar" />

          <div className="profile-info">
            <strong>Administrator</strong>
            <small>Security Admin</small>
          </div>

        </div>

      </div>

    </header>
  );
}

export default Navbar;