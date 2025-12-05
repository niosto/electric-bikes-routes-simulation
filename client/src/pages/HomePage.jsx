"use client"

import { useState } from "react"
import { useNavigate } from "react-router-dom"
import BidEafitLogo from "../images/bid-eafit-logo.png"; // ajusta ruta si es necesario

export default function HomePage() {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState("simulation")

  const simulationOptions = [
    {
      title: "¿Qué puedes hacer aquí?",
      items: [
        "Configurar tus simulaciones",
        "Seleccionar recorridos reales",
        "Analizar rendimiento",
        "Evaluar impacto ambiental",
      ],
    },
    {
      title: "Resultados que obtendrás",
      items: [
        "Velocidad promedio e instantánea",
        "Consumo energético total",
        "Emisiones estimadas de CO₂",
        "Tiempo total de recorrido",
        "Número de recargas",
        "Energía demandada por estación de carga",
      ],
    },
    {
      title: "Comienza tu simulación ahora",
      items: null,
      cta: true,
    },
  ]

  const telemetryOptions = [
    {
      title: "¿Qué puedes hacer aquí?",
      items: [
        "Supervisar en tiempo real",
        "Ver el recorrido actual en el mapa",
        "Analizar desempeño instantáneo",
      ],
    },
    {
      title: "Datos y visualizaciones",
      items: [
        "Estado de carga",
        "Velocidad actual",
        "Potencia (W) y voltaje (V)",
        "Tiempo total de recorrido",
        "Mapa con geolocalización dinámica",
      ],
    },
    {
      title: "Conecta un vehículo y comienza el monitoreo en vivo",
      items: null,
      cta: true,
    },
  ]

  const options = activeTab === "simulation" ? simulationOptions : telemetryOptions

  return (
    <main className="home-page">
      <style>{`
        .home-page {
          background: #f5f5f5;
          min-height: calc(100vh - 56px);
          padding: 40px 20px;
        }

        .home-container {
          max-width: 1280px;
          margin: 0 auto;
        }

        .hero-search {
          background: #ddd;
          border-radius: 20px;
          padding: 20px;
          margin-bottom: 30px;
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .hero-search input {
          flex: 1;
          border: none;
          background: transparent;
          font-size: 16px;
          outline: none;
          color: #666;
        }

        .hero-search input::placeholder {
          color: #999;
        }

        .logo-img {
          width: 60px;
          height: 60px;
          background: white;
          border-radius: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: bold;
          color: #333;
        }

        .hero-question {
          font-size: 16px;
          color: #333;
        }

        .hero-divider {
          width: 1px;
          height: 100px;
          background: #aaa;
        }

        .hero-bid-logo {
          height: 150px;
          object-fit: contain;
        }

        .tabs-container {
          display: flex;
          gap: 12px;
          margin: 30px 0;
          justify-content: center;
        }

        .tab-btn {
          padding: 10px 24px;
          border: none;
          border-radius: 20px;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.3s ease;
          background: #999;
          color: white;
        }

        .tab-btn.active {
          background: #000;
        }

        .section-header {
          text-align: center;
          margin: 40px 0;
        }

        .section-header h2 {
          font-size: 24px;
          font-weight: 800;
          margin-bottom: 8px;
          color: #000;
        }

        .section-header p {
          color: #666;
          font-size: 14px;
          line-height: 1.6;
          max-width: 800px;
          margin: 0 auto;
        }

        .options-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 24px;
          margin-bottom: 40px;
        }

        @media (max-width: 1024px) {
          .options-grid {
            grid-template-columns: repeat(2, 1fr);
          }
        }

        @media (max-width: 640px) {
          .options-grid {
            grid-template-columns: 1fr;
          }
        }

        .option-card {
          background: #000;
          border-radius: 20px;
          padding: 24px;
          color: white;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        /*  ESTA ES LA MODIFICACIÓN PARA CENTRAR EL TÍTULO */
        .option-title {
          text-align: center;
          width: 100%;
        }

        .option-card h3 {
          font-size: 18px;
          font-weight: 700;
          margin: 0;
        }

        .option-card ul {
          list-style: none;
          margin: 0;
          padding: 0;
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .option-card li {
          font-size: 14px;
          color: #eee;
          padding: 8px 12px;
          background: #1a1a1a;
          border-radius: 10px;
          text-align: center;
        }

        .option-card.cta {
          justify-content: center;
          align-items: center;
          text-align: center;
          gap: 20px;
        }

        .option-card.cta h3 {
          font-size: 16px;
        }

        .option-card.cta p {
          font-size: 13px;
          color: #bbb;
          margin: 0;
          line-height: 1.5;
        }

        .cta-button {
          background: #2563eb;
          color: white;
          border: none;
          padding: 12px 32px;
          border-radius: 50px;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.3s ease;
          align-self: center;
        }

        .cta-button:hover {
          background: #1d4ed8;
          transform: translateY(-2px);
        }

        .bottom-section {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 24px;
          margin-bottom: 40px;
        }

        @media (max-width: 640px) {
          .bottom-section {
            grid-template-columns: 1fr;
          }
        }

        .bottom-card {
          background: #ddd;
          border-radius: 20px;
          padding: 32px;
          text-align: center;
          min-height: 200px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #666;
          font-size: 16px;
        }

        .contact-card {
          grid-column: 1 / -1;
          background: #ddd;
          border-radius: 20px;
          padding: 32px;
          text-align: center;
          color: #666;
        }
      `}</style>

      <div className="home-container">

        {/* Hero Search */}
        <div className="hero-search">
          <span className="hero-question">¿Qué hace esta plataforma?</span>
          <div className="hero-divider" />
          <div className="hero-logo-wrap">
            <img
              src={BidEafitLogo}
              alt="Proyecto BID - EAFIT"
              className="hero-bid-logo"
            />
          </div>
        </div>

        {/* Tabs */}
        <div className="tabs-container">
          <button
            className={`tab-btn ${activeTab === "simulation" ? "active" : ""}`}
            onClick={() => setActiveTab("simulation")}
          >
            Simulación
          </button>
          <button
            className={`tab-btn ${activeTab === "telemetry" ? "active" : ""}`}
            onClick={() => setActiveTab("telemetry")}
          >
            Telemetría
          </button>
        </div>

        {/* Section Header */}
        <div className="section-header">
          <h2>
            {activeTab === "simulation"
              ? "Simula el comportamiento real de motocicletas en entornos urbanos"
              : "Monitorea el rendimiento y estado de tu motocicleta en tiempo real"}
          </h2>
          <p>
            {activeTab === "simulation"
              ? "Explora cómo diferentes tipos de motocicletas afectan la contaminación de aire en contextos urbanos y geográficos. Ayuda parámetros, especula simulaciones y analiza resultados técnicos y ambientales."
              : "Visualiza los datos operacionales de cada vehículo conectado. Ubicación, energía, velocidad y desempeño. La telemetría te permite entender cómo se comportan tus motocicletas en condiciones reales de operación."}
          </p>
        </div>

        {/* Options Grid */}
        <div className="options-grid">
          {options.map((option, idx) => (
            <div key={idx} className={`option-card ${option.cta ? "cta" : ""}`}>
              
              {/* TITULO CENTRADO */}
              <h3 className="option-title">{option.title}</h3>

              {option.items ? (
                <ul>
                  {option.items.map((item, i) => (
                    <li key={i}>{item}</li>
                  ))}
                </ul>
              ) : (
                <>
                  <p>
                    {activeTab === "simulation"
                      ? "Ajusta tus parámetros, visualiza la ruta en el mapa y observa cómo impacta el consumo y las emisiones."
                      : "Observa cada sensor en tiempo real. Toma decisiones impactantes en la conducción y gasto en emisiones."}
                  </p>
                  <button
                    className="cta-button"
                    onClick={() =>
                      navigate(activeTab === "simulation" ? "/mapa" : "/telemetry")
                    }
                  >
                    {activeTab === "simulation" ? "Iniciar simulación" : "Iniciar Telemetría"}
                  </button>
                </>
              )}
            </div>
          ))}
        </div>

        {/* Bottom Cards */}
        <div className="bottom-section">
          <div className="bottom-card">Acerca del proyecto</div>
          <div className="bottom-card">Otros proyectos</div>
          <div className="contact-card">Contáctanos</div>
        </div>
      </div>
    </main>
  )
}
