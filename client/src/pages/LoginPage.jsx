import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [user, setUser] = useState("");
  const [pass, setPass] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    setTimeout(() => {
      const ok = login(user, pass);

      if (!ok) {
        setError("Usuario o contraseña inválidos");
        setIsLoading(false);
        return;
      }

      navigate("/home", { replace: true });
    }, 300);
  }

  const styles = `
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    }

    .login-container {
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, #f5f5f5 0%, #f0f0f0 100%);
      padding: 20px;
    }

    .login-card {
      background: white;
      border-radius: 16px;
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.08);
      width: 100%;
      max-width: 420px;
      padding: 48px 40px;
      animation: slideUp 0.4s ease-out;
    }

    @keyframes slideUp {
      from {
        opacity: 0;
        transform: translateY(20px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    .login-header {
      margin-bottom: 32px;
      text-align: center;
    }

    .login-header h1 {
      font-size: 28px;
      font-weight: 700;
      color: #1a1a1a;
      margin-bottom: 8px;
      letter-spacing: -0.5px;
    }

    .login-header p {
      font-size: 14px;
      color: #666;
      font-weight: 500;
    }

    .form-group {
      margin-bottom: 20px;
      display: flex;
      flex-direction: column;
    }

    .form-group label {
      font-size: 13px;
      font-weight: 600;
      color: #333;
      margin-bottom: 8px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .form-group input {
      padding: 12px 16px;
      border: 2px solid #e0e0e0;
      border-radius: 10px;
      font-size: 15px;
      transition: all 0.2s ease;
      background: #fafafa;
      color: #1a1a1a;
      font-family: inherit;
    }

    .form-group input::placeholder {
      color: #999;
    }

    .form-group input:focus {
      outline: none;
      border-color: #10b981;
      background: white;
      box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
    }

    .form-group input:hover {
      border-color: #d0d0d0;
    }

    .error-message {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 20px;
      padding: 12px 14px;
      background: #fee;
      border: 1px solid #fcc;
      border-radius: 8px;
      color: #c33;
      font-size: 14px;
      font-weight: 500;
      animation: shake 0.3s ease;
    }

    @keyframes shake {
      0%, 100% { transform: translateX(0); }
      25% { transform: translateX(-5px); }
      75% { transform: translateX(5px); }
    }

    .error-message::before {
      content: '⚠';
      font-weight: bold;
    }

    .submit-button {
      width: 100%;
      padding: 13px 16px;
      background: linear-gradient(135deg, #10b981 0%, #059669 100%);
      color: white;
      border: none;
      border-radius: 10px;
      font-size: 15px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 16px;
      position: relative;
      overflow: hidden;
    }

    .submit-button:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba(16, 185, 129, 0.3);
    }

    .submit-button:active:not(:disabled) {
      transform: translateY(0);
    }

    .submit-button:disabled {
      opacity: 0.7;
      cursor: not-allowed;
    }

    .button-text {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
    }

    .spinner {
      display: inline-block;
      width: 14px;
      height: 14px;
      border: 2px solid rgba(255, 255, 255, 0.3);
      border-top-color: white;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }

    .login-footer {
      text-align: center;
      font-size: 13px;
      color: #666;
    }

    .login-footer a {
      color: #10b981;
      text-decoration: none;
      font-weight: 600;
      transition: color 0.2s;
    }

    .login-footer a:hover {
      color: #059669;
      text-decoration: underline;
    }

    .demo-info {
      background: #f0fdf4;
      border: 1px solid #dcfce7;
      border-radius: 8px;
      padding: 12px;
      margin-top: 20px;
      font-size: 12px;
      color: #166534;
      text-align: center;
      font-weight: 500;
    }
  `;

  return (
    <>
      <style>{styles}</style>
      <div className="login-container">
        <div className="login-card">
          <div className="login-header">
            <h1>Bienvenido</h1>
            <p>Accede a tu simulador de rutas</p>
          </div>

          <form onSubmit={handleSubmit}>
            {error && (
              <div className="error-message">
                {error}
              </div>
            )}

            <div className="form-group">
              <label htmlFor="username">Usuario</label>
              <input
                id="username"
                type="text"
                placeholder="Ingresa tu usuario"
                value={user}
                onChange={(e) => setUser(e.target.value)}
                disabled={isLoading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">Contraseña</label>
              <input
                id="password"
                type="password"
                placeholder="Ingresa tu contraseña"
                value={pass}
                onChange={(e) => setPass(e.target.value)}
                disabled={isLoading}
              />
            </div>

            <button
              type="submit"
              className="submit-button"
              disabled={isLoading || !user || !pass}
            >
              <span className="button-text">
                {isLoading && <span className="spinner"></span>}
                {isLoading ? "Ingresando..." : "Iniciar Sesión"}
              </span>
            </button>
          </form>

          <div className="login-footer">
            <p>¿Usuario de prueba? Usa <strong>admin</strong> / <strong>password</strong></p>
          </div>

          <div className="demo-info">
            Modo demo: Cualquier usuario con contraseña "password" funciona
          </div>
        </div>
      </div>
    </>
  );
}