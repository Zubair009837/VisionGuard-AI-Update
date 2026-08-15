import { useEffect, useState } from "react";
import api from "../services/api";

function CameraTable() {
  const [cameras, setCameras] = useState([]);
  const [search, setSearch] = useState("");

  async function loadCameras() {
    try {
      const response = await api.get("/cameras");
      setCameras(response.data);
    } catch (error) {
      console.error(error);
      setCameras([]);
    }
  }

  useEffect(() => {
    loadCameras();

    const interval = setInterval(loadCameras, 30000);

    return () => clearInterval(interval);
  }, []);

  const filteredCameras = cameras.filter((camera) =>
    camera.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="card shadow-lg border-0 mt-4">

      <div className="card-header bg-dark text-white d-flex justify-content-between align-items-center">

        <h5 className="mb-0">
          📹 Camera Monitoring
        </h5>

        <span className="badge bg-primary">
          Total : {filteredCameras.length}
        </span>

      </div>

      <div className="card-body">

        <div className="row mb-3">

          <div className="col-md-4">

            <input
              type="text"
              className="form-control"
              placeholder="🔍 Search Camera..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />

          </div>

        </div>

        <div className="table-responsive">

          <table className="table table-hover align-middle">

            <thead className="table-dark">

              <tr>
                <th>#</th>
                <th>Camera Name</th>
                <th>Status</th>
                <th>NVR</th>
                <th>IP Address</th>
              </tr>

            </thead>

            <tbody>

              {filteredCameras.length > 0 ? (

                filteredCameras.map((camera, index) => (

                  <tr key={camera.id}>

                    <td>{index + 1}</td>

                    <td>
                      <strong>{camera.name}</strong>
                    </td>

                    <td>

                      {camera.status === "Online" ? (

                        <span className="badge bg-success px-3 py-2">
                          🟢 Online
                        </span>

                      ) : (

                        <span className="badge bg-danger px-3 py-2">
                          🔴 Offline
                        </span>

                      )}

                    </td>

                    <td>{camera.nvr}</td>

                    <td>
                      <code>{camera.ip}</code>
                    </td>

                  </tr>

                ))

              ) : (

                <tr>

                  <td
                    colSpan="5"
                    className="text-center text-muted py-5"
                  >
                    📷 No Cameras Found
                  </td>

                </tr>

              )}

            </tbody>

          </table>

        </div>

      </div>

    </div>
  );
}

export default CameraTable;