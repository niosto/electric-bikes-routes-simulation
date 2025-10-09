import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";
// Si prefieres importar leaflet.css aquí en lugar del <link>, también funciona:
// import "leaflet/dist/leaflet.css";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <App />
  </StrictMode>
);