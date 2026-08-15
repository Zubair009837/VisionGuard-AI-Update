import { BrowserRouter, Routes, Route } from "react-router-dom";

import Layout from "./layout/Layout";

import Dashboard from "./pages/Dashboard";
import Cameras from "./pages/Cameras";
import NVR from "./pages/NVR";
import Alerts from "./pages/Alerts";
import Analytics from "./pages/Analytics";
import Settings from "./pages/Settings";
import Storage from "./pages/Storage";
import Users from "./pages/Users";
import FloorMap from "./pages/FloorMap";
import CameraMovements from "./pages/CameraMovements";
import LiveView from "./pages/LiveView";
import Reports from "./pages/Reports";

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/cameras" element={<Cameras />} />
          <Route path="/nvr" element={<NVR />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/storage" element={<Storage />} />
          <Route path="/users" element={<Users />} />
          <Route path="/floor-map" element={<FloorMap />} />
          <Route path="/camera-movements" element={<CameraMovements />} />
          <Route path="/live" element={<LiveView />} />
          <Route path="/reports" element={<Reports />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;