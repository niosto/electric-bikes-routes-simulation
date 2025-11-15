import React from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, Map, TrendingUp, BookOpen, Zap, Battery, Gauge } from 'lucide-react';

export default function HomePage() {
  const navigate = useNavigate();

  return (
    <main style={{ background: "#f8fafb", minHeight: "100vh" }}>
      <style>{`
        * {
          margin: 0;
          padding: 0;
          box-sizing: border-box;
        }
        
        body {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', sans-serif;
          color: #1f2937;
          background: #f8fafb;
        }

        .container {
          max-width: 1280px;
          margin: 0 auto;
          padding: 0 24px;
        }

        /* Hero Section */
        .hero-section {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 60px;
          align-items: center;
          padding: 100px 0;
        }

        @media (max-width: 768px) {
          .hero-section {
            grid-template-columns: 1fr;
            padding: 60px 0;
            gap: 40px;
          }
        }

        .hero-content h1 {
          font-size: 52px;
          font-weight: 800;
          line-height: 1.2;
          margin-bottom: 20px;
          color: #000;
          letter-spacing: -1.5px;
        }

        @media (max-width: 768px) {
          .hero-content h1 {
            font-size: 36px;
          }
        }

        .hero-highlight {
          background: linear-gradient(135deg, #10b981 0%, #0ea5e9 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .hero-content p {
          font-size: 18px;
          color: #6b7280;
          line-height: 1.6;
          margin-bottom: 32px;
          max-width: 500px;
        }

        .badge {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          background: #dbeafe;
          color: #0369a1;
          padding: 8px 14px;
          border-radius: 20px;
          font-size: 14px;
          font-weight: 500;
          margin-bottom: 20px;
        }

        .button-group {
          display: flex;
          gap: 16px;
          flex-wrap: wrap;
          margin-bottom: 40px;
        }

        .btn {
          padding: 14px 28px;
          border: none;
          border-radius: 50px;
          font-size: 16px;
          font-weight: 600;
          cursor: pointer;
          display: inline-flex;
          align-items: center;
          gap: 8px;
          transition: all 0.3s ease;
          text-decoration: none;
        }

        .btn-primary {
          background: linear-gradient(135deg, #10b981 0%, #059669 100%);
          color: white;
          box-shadow: 0 10px 30px rgba(16, 185, 129, 0.3);
        }

        .btn-primary:hover {
          box-shadow: 0 15px 40px rgba(16, 185, 129, 0.4);
          transform: translateY(-2px);
        }

        .btn-secondary {
          background: white;
          color: #1f2937;
          border: 2px solid #e5e7eb;
        }

        .btn-secondary:hover {
          border-color: #10b981;
          background: #f0fdf4;
        }

        .stats {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 32px;
          padding-top: 32px;
          border-top: 1px solid #e5e7eb;
        }

        .stat {
          display: flex;
          flex-direction: column;
        }

        .stat-value {
          font-size: 24px;
          font-weight: 800;
          color: #10b981;
          margin-bottom: 4px;
        }

        .stat-label {
          font-size: 14px;
          color: #9ca3af;
        }

        /* Right Column - Card */
        .hero-card {
          background: white;
          border-radius: 24px;
          padding: 40px;
          box-shadow: 0 4px 30px rgba(0, 0, 0, 0.08);
          border: 1px solid #f0f0f0;
          position: relative;
          overflow: hidden;
        }

        .hero-card::before {
          content: '';
          position: absolute;
          top: -50%;
          right: -50%;
          width: 200px;
          height: 200px;
          background: radial-gradient(circle, rgba(16, 185, 129, 0.1) 0%, transparent 70%);
          border-radius: 50%;
        }

        .hero-card-content {
          position: relative;
          z-index: 1;
        }

        .hero-card h3 {
          font-size: 20px;
          font-weight: 700;
          margin-bottom: 8px;
          color: #000;
        }

        .hero-card-subtitle {
          font-size: 14px;
          color: #9ca3af;
          margin-bottom: 20px;
        }

        .features-list {
          list-style: none;
        }

        .features-list li {
          display: flex;
          gap: 12px;
          margin-bottom: 16px;
          font-size: 14px;
          color: #6b7280;
          line-height: 1.5;
        }

        .features-list li::before {
          content: '';
          width: 6px;
          height: 6px;
          background: #10b981;
          border-radius: 50%;
          flex-shrink: 0;
          margin-top: 6px;
        }

        /* Features Section */
        .features-section {
          padding: 80px 0;
        }

        .section-header {
          margin-bottom: 60px;
        }

        .section-header h2 {
          font-size: 42px;
          font-weight: 800;
          margin-bottom: 16px;
          color: #000;
          letter-spacing: -1px;
        }

        .section-header p {
          font-size: 18px;
          color: #6b7280;
          max-width: 600px;
          line-height: 1.6;
        }

        .features-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
          gap: 28px;
        }

        .feature-card {
          background: white;
          border-radius: 20px;
          padding: 32px;
          border: 1px solid #f0f0f0;
          cursor: pointer;
          transition: all 0.3s ease;
          position: relative;
          overflow: hidden;
        }

        .feature-card::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: linear-gradient(135deg, rgba(16, 185, 129, 0.05) 0%, transparent 100%);
          opacity: 0;
          transition: opacity 0.3s ease;
        }

        .feature-card:hover {
          box-shadow: 0 12px 40px rgba(0, 0, 0, 0.12);
          transform: translateY(-8px);
          border-color: #10b981;
        }

        .feature-card:hover::before {
          opacity: 1;
        }

        .feature-icon {
          width: 48px;
          height: 48px;
          background: linear-gradient(135deg, #10b981 0%, #059669 100%);
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          margin-bottom: 20px;
          font-size: 0;
        }

        .feature-icon svg {
          width: 24px;
          height: 24px;
        }

        .feature-card h3 {
          font-size: 20px;
          font-weight: 700;
          margin-bottom: 12px;
          color: #000;
        }

        .feature-card p {
          font-size: 14px;
          color: #6b7280;
          line-height: 1.6;
          margin-bottom: 16px;
        }

        .feature-link {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          color: #10b981;
          font-weight: 600;
          font-size: 14px;
          text-decoration: none;
          transition: gap 0.3s ease;
        }

        .feature-card:hover .feature-link {
          gap: 12px;
        }

        /* CTA Section */
        .cta-section {
          background: linear-gradient(135deg, #f0fdf4 0%, #dbeafe 100%);
          border-radius: 24px;
          padding: 80px 40px;
          text-align: center;
          margin-top: 80px;
          border: 1px solid #d1fae5;
        }

        @media (max-width: 768px) {
          .cta-section {
            padding: 50px 30px;
          }
        }

        .cta-section h2 {
          font-size: 40px;
          font-weight: 800;
          margin-bottom: 16px;
          color: #000;
          letter-spacing: -0.5px;
        }

        .cta-section p {
          font-size: 18px;
          color: #6b7280;
          margin-bottom: 32px;
          max-width: 600px;
          margin-left: auto;
          margin-right: auto;
          line-height: 1.6;
        }
      `}</style>

      <div className="container">
        {/* Hero Section */}
        <section className="hero-section">
          <div className="hero-content">
            <div className="badge">
              <Zap size={16} style={{ color: "#0369a1" }} />
              Simulación de energía sostenible
            </div>
            
            <h1>
              Plataforma de simulación para <span className="hero-highlight">bicicletas eléctricas</span>
            </h1>
            
            <p>
              Simula rutas, visualiza telemetría en tiempo real y analiza el consumo de energía con precisión. Exporta resultados en JSON y GeoJSON para análisis avanzado.
            </p>

            <div className="button-group">
              <button 
                className="btn btn-primary"
                onClick={() => navigate("/mapa")}
              >
                Probar mapa de rutas
                <ArrowRight size={18} />
              </button>
              <button
                className="btn btn-secondary"
                onClick={() => navigate("/telemetry")}
              >
                Ver telemetría
              </button>
            </div>

            <div className="stats">
              <div className="stat">
                <div className="stat-value">OpenRouteService</div>
                <div className="stat-label">Rutas optimizadas</div>
              </div>
              <div className="stat">
                <div className="stat-value">Real-time</div>
                <div className="stat-label">Telemetría en vivo</div>
              </div>
            </div>
          </div>

          <div className="hero-card">
            <div className="hero-card-content">
              <h3>Resumen rápido</h3>
              <p className="hero-card-subtitle">Capacidades principales</p>
              <ul className="features-list">
                <li>Simulación de rutas con OpenRouteService (ORS)</li>
                <li>Modelo de consumo energético para bicicletas híbridas</li>
                <li>Visualización de potencia, velocidad, altitud y SoC</li>
                <li>Exportación de datos en JSON y GeoJSON</li>
              </ul>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="features-section">
          <div className="section-header">
            <h2>Características principales</h2>
            <p>Todo lo que necesitas para simular y analizar rutas de bicicletas eléctricas</p>
          </div>

          <div className="features-grid">
            <div 
              className="feature-card"
              onClick={() => navigate("/mapa")}
            >
              <div className="feature-icon">
                <Map size={24} />
              </div>
              <h3>Mapa de rutas</h3>
              <p>Interfaz principal para definir vehículos, cargar rutas y calcular recorridos con ORS.</p>
              <a href="#" onClick={(e) => e.preventDefault()} className="feature-link">
                Acceder
                <ArrowRight size={16} />
              </a>
            </div>

            <div 
              className="feature-card"
              onClick={() => navigate("/telemetry")}
            >
              <div className="feature-icon">
                <TrendingUp size={24} />
              </div>
              <h3>Telemetría</h3>
              <p>Carga archivos de telemetría para visualizar curvas de potencia, velocidad y altitud.</p>
              <a href="#" onClick={(e) => e.preventDefault()} className="feature-link">
                Acceder
                <ArrowRight size={16} />
              </a>
            </div>

            <div 
              className="feature-card"
              onClick={() => navigate("/docs")}
            >
              <div className="feature-icon">
                <BookOpen size={24} />
              </div>
              <h3>Documentación</h3>
              <p>Guías de uso, formatos de entrada/salida, arquitectura y ejemplos de peticiones.</p>
              <a href="#" onClick={(e) => e.preventDefault()} className="feature-link">
                Acceder
                <ArrowRight size={16} />
              </a>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="cta-section">
          <h2>¿Listo para comenzar?</h2>
          <p>Comienza a simular rutas y analiza el consumo energético con herramientas avanzadas</p>
          <button 
            className="btn btn-primary"
            onClick={() => navigate("/mapa")}
          >
            Ir al simulador
            <ArrowRight size={18} />
          </button>
        </section>
      </div>
    </main>
  );
}