/**
 * Login Component - Premium glassmorphism login form
 */
import { useState } from 'react';
import { useAuth } from '../context/AuthContext';

export default function Login({ onClose }) {
  const { login } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const result = await login(username, password);

    if (result.success) {
      onClose?.();
    } else {
      setError(result.error);
    }
    setLoading(false);
  };

  const demoAccounts = [
    { username: 'admin', password: 'admin123', role: 'COE' },
    { username: 'hod_demo', password: 'hod123', role: 'HOD' },
    { username: 'faculty_demo', password: 'faculty123', role: 'Faculty' },
    { username: 'auditor_demo', password: 'auditor123', role: 'Auditor' },
    { username: 'external_demo', password: 'external123', role: 'External' }
  ];

  const fillDemo = (demo) => {
    setUsername(demo.username);
    setPassword(demo.password);
    setError('');
  };

  return (
    <div className="login-container">
      <div className="login-brand">
        <div className="shape shape-1"></div>
        <div className="shape shape-2"></div>
        <div className="shape shape-3"></div>
        <div className="brand-content">
          <img src="/logo.png" alt="ScruCheck AI" className="brand-logo-image" />
        </div>
        <div className="brand-pattern"></div>
      </div>

      <div className="login-form-section">
        <div className="login-form-wrapper">
          {onClose && <button className="login-close" onClick={onClose}>×</button>}

          <div className="mobile-brand">
            <img src="/logo.png" alt="ScruCheck AI" className="brand-logo-image small" />
          </div>

          <div className="login-header">
            <h2>Welcome Back</h2>
            <p>Please enter your credentials to continue</p>
          </div>

          <form onSubmit={handleSubmit} className="login-form">
            {error && (
              <div className="login-error">
                 {error}
              </div>
            )}

            <div className="form-group">
              <label>Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your username"
                required
              />
            </div>

            <div className="form-group">
              <label>Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                required
              />
            </div>

            <button
              type="submit"
              className="login-btn"
              disabled={loading}
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <div className="login-demo">
            <p>Try it with a demo account</p>
            <div className="demo-accounts">
              {demoAccounts.map((demo) => (
                <button
                  key={demo.username}
                  className="demo-btn"
                  onClick={() => fillDemo(demo)}
                >
                  {demo.role}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      <style>{`
        .login-container {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: #ffffff;
          display: flex;
          z-index: 1000;
          animation: fadeIn 0.4s ease;
          font-family: 'Inter', -apple-system, sans-serif;
          perspective: 1000px;
        }

        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }

        /* Left Brand Section */
        .login-brand {
          flex: 1.2;
          background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
          display: flex;
          align-items: center;
          justify-content: center;
          position: relative;
          overflow: hidden;
          padding: 4rem;
          border-right: 1px solid #e2e8f0;
          transform-style: preserve-3d;
        }

        .brand-pattern {
          position: absolute;
          inset: 0;
          background-image: radial-gradient(#bae6fd 1px, transparent 1px);
          background-size: 40px 40px;
          opacity: 0.4;
          transform: translateZ(-100px);
        }

        /* 3D Floating Shapes */
        .shape {
          position: absolute;
          background: linear-gradient(135deg, rgba(0, 82, 204, 0.1), rgba(14, 165, 233, 0.1));
          border-radius: 20px;
          animation: float3D 15s infinite ease-in-out;
          transform-style: preserve-3d;
        }

        .shape-1 { width: 150px; height: 150px; top: 10%; left: 10%; animation-delay: 0s; }
        .shape-2 { width: 100px; height: 100px; bottom: 15%; right: 15%; animation-delay: -5s; }
        .shape-3 { width: 80px; height: 80px; top: 40%; right: 10%; animation-delay: -10s; }

        @keyframes float3D {
          0%, 100% { transform: translateY(0) rotateX(0) rotateY(0) translateZ(0); }
          33% { transform: translateY(-30px) rotateX(20deg) rotateY(-20deg) translateZ(50px); }
          66% { transform: translateY(30px) rotateX(-20deg) rotateY(20deg) translateZ(-50px); }
        }

        .brand-content {
          position: relative;
          z-index: 10;
          max-width: 440px;
          text-align: center;
          transform: translateZ(50px);
          transition: transform 0.5s ease;
        }

        .brand-logo-image {
          width: 100%;
          max-width: 380px;
          height: auto;
          margin-bottom: 2.5rem;
          display: block;
          margin-left: auto;
          margin-right: auto;
          filter: drop-shadow(0 30px 40px rgba(0, 82, 204, 0.2));
          animation: logoFloat 6s infinite ease-in-out;
        }

        @keyframes logoFloat {
          0%, 100% { transform: translateY(0) rotateZ(0); }
          50% { transform: translateY(-15px) rotateZ(2deg); }
        }

        .brand-logo-image.small {
          max-width: 180px;
          margin-bottom: 0;
        }

        .brand-content p {
          color: #475569;
          font-size: 1.125rem;
          line-height: 1.7;
          font-weight: 500;
          text-shadow: 0 5px 15px rgba(0,0,0,0.05);
        }

        /* Right Form Section */
        .login-form-section {
          flex: 1;
          background: #ffffff;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 3rem;
          position: relative;
          transform-style: preserve-3d;
        }

        .login-form-wrapper {
          width: 100%;
          max-width: 400px;
          position: relative;
          transform: translateZ(20px);
          background: white;
          padding: 2.5rem;
          border-radius: 24px;
          box-shadow: 0 10px 40px rgba(0,0,0,0.04);
          border: 1px solid rgba(0,0,0,0.02);
        }

        .mobile-brand {
          display: none;
          align-items: center;
          justify-content: center;
          margin-bottom: 3rem;
        }

        .login-header {
          margin-bottom: 2.5rem;
          text-align: left;
        }

        .login-header h2 {
          color: #0f172a;
          font-size: 2.25rem;
          font-weight: 800;
          margin-bottom: 0.75rem;
          letter-spacing: -0.025em;
        }

        .login-header p {
          color: #64748b;
          font-size: 1rem;
          font-weight: 500;
        }

        .login-form {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
        }

        .form-group {
          display: flex;
          flex-direction: column;
          gap: 0.625rem;
        }

        .form-group label {
          color: #1e293b;
          font-size: 0.875rem;
          font-weight: 600;
        }

        .form-group input {
          background: #f8fafc;
          border: 1.5px solid #e2e8f0;
          border-radius: 12px;
          padding: 1rem 1.25rem;
          color: #0f172a;
          font-size: 1rem;
          font-weight: 500;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .form-group input:focus {
          outline: none;
          background: #ffffff;
          border-color: #0052cc;
          box-shadow: 0 10px 20px rgba(0, 82, 204, 0.1);
          transform: translateY(-2px) translateZ(10px);
        }

        .login-btn {
          background: #0052cc;
          color: white;
          border: none;
          border-radius: 12px;
          padding: 1.125rem;
          font-size: 1.125rem;
          font-weight: 700;
          cursor: pointer;
          transition: all 0.3s ease;
          margin-top: 0.5rem;
          box-shadow: 0 10px 20px rgba(0, 82, 204, 0.2);
          transform: translateZ(15px);
        }

        .login-btn:hover:not(:disabled) {
          background: #0747a6;
          transform: translateY(-3px) translateZ(25px);
          box-shadow: 0 15px 30px rgba(0, 82, 204, 0.3);
        }

        .login-btn:active:not(:disabled) {
          transform: translateY(0) translateZ(15px);
        }

        .login-btn:disabled {
          background: #94a3b8;
          cursor: not-allowed;
          box-shadow: none;
          transform: none;
        }

        .login-error {
          background: #fff1f2;
          border: 1px solid #fecdd3;
          color: #be123c;
          border-radius: 10px;
          padding: 1rem;
          font-size: 0.9375rem;
          font-weight: 500;
          display: flex;
          align-items: center;
          gap: 0.75rem;
          animation: shake 0.4s ease-in-out;
        }

        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          25% { transform: translateX(-5px); }
          75% { transform: translateX(5px); }
        }

        .login-demo {
          margin-top: 3rem;
          text-align: center;
          transform: translateZ(5px);
        }

        .login-demo p {
          color: #94a3b8;
          font-size: 0.875rem;
          font-weight: 600;
          margin-bottom: 1.5rem;
          display: flex;
          align-items: center;
          gap: 1rem;
        }

        .login-demo p::before,
        .login-demo p::after {
          content: '';
          flex: 1;
          height: 1px;
          background: #e2e8f0;
        }

        .demo-accounts {
          display: flex;
          gap: 0.75rem;
          justify-content: center;
          flex-wrap: wrap;
        }

        .demo-btn {
          background: #ffffff;
          border: 1.5px solid #e2e8f0;
          color: #475569;
          border-radius: 10px;
          padding: 0.625rem 1.25rem;
          font-size: 0.875rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .demo-btn:hover {
          background: #f0f7ff;
          border-color: #0052cc;
          color: #0052cc;
          transform: translateY(-4px) translateZ(10px);
          box-shadow: 0 5px 15px rgba(0,0,0,0.05);
        }

        .login-close {
          position: absolute;
          top: 2rem;
          right: 2rem;
          background: #f8fafc;
          border: 1px solid #e2e8f0;
          color: #64748b;
          width: 40px;
          height: 40px;
          border-radius: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 1.5rem;
          cursor: pointer;
          transition: all 0.2s;
          transform: translateZ(50px);
        }

        .login-close:hover {
          background: #fff1f2;
          color: #be123c;
          border-color: #fecdd3;
          transform: rotate(90deg) translateZ(60px);
        }

        @media (max-width: 1024px) {
          .login-brand {
            display: none;
          }
          .login-form-section {
            padding: 2rem;
          }
          .mobile-brand {
            display: flex;
          }
        }

        @media (max-width: 768px) {
          .login-container {
            flex-direction: column;
          }
          .login-form-section {
            padding: 1.5rem 1rem;
            min-height: 100vh;
          }
          .login-form-wrapper {
            max-width: 100%;
            padding: 1.75rem 1.25rem;
            border-radius: 18px;
          }
          .login-header {
            margin-bottom: 1.75rem;
          }
          .demo-accounts {
            gap: 0.5rem;
          }
          .demo-btn {
            padding: 0.5rem 0.85rem;
            font-size: 0.8rem;
          }
        }

        @media (max-width: 480px) {
          .login-form-section {
            padding: 1rem 0.75rem;
          }
          .login-form-wrapper {
            padding: 1.25rem 1rem;
            border-radius: 14px;
            box-shadow: none;
            border: none;
          }
          .login-header h1 {
            font-size: 1.5rem !important;
          }
          .demo-accounts {
            flex-direction: column;
          }
          .demo-btn {
            width: 100%;
            text-align: center;
          }
        }
      `}</style>
    </div>
  );
}
