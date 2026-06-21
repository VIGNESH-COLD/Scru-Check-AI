/**
 * AdminPanel - User management and external access token generation
 * Only visible to HOD and COE roles
 */
import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';

const API_BASE = '';

export default function AdminPanel({ onClose }) {
    const { user, token, hasPermission } = useAuth();
    const [activeTab, setActiveTab] = useState('users');
    const [users, setUsers] = useState([]);
    const [externalTokens, setExternalTokens] = useState([]);
    const [loading, setLoading] = useState(false);
    const [newLinkPapers, setNewLinkPapers] = useState('');
    const [newLinkHours, setNewLinkHours] = useState(48);
    const [generatedLink, setGeneratedLink] = useState(null);

    useEffect(() => {
        if (activeTab === 'users') fetchUsers();
        if (activeTab === 'external') fetchTokens();
    }, [activeTab]);

    const fetchUsers = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/auth/users`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                setUsers(await res.json());
            }
        } catch (error) {
            console.error('Failed to fetch users:', error);
        }
    };

    const fetchTokens = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/external/tokens`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setExternalTokens(data.tokens || []);
            }
        } catch (error) {
            console.error('Failed to fetch tokens:', error);
        }
    };

    const generateExternalLink = async () => {
        setLoading(true);
        try {
            const paperIds = newLinkPapers.split(',').map(p => p.trim()).filter(Boolean);

            const res = await fetch(`${API_BASE}/api/external/generate`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    paper_ids: paperIds.length > 0 ? paperIds : ['all'],
                    expires_hours: newLinkHours
                })
            });

            if (res.ok) {
                const data = await res.json();
                setGeneratedLink(data);
                fetchTokens();
            }
        } catch (error) {
            console.error('Failed to generate link:', error);
        } finally {
            setLoading(false);
        }
    };

    const revokeToken = async (tokenToRevoke) => {
        try {
            await fetch(`${API_BASE}/api/external/revoke/${tokenToRevoke}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            fetchTokens();
        } catch (error) {
            console.error('Failed to revoke token:', error);
        }
    };

    const roleColors = {
        coe: '#3b82f6',
        hod: '#8b5cf6',
        faculty: '#10b981',
        auditor: '#f59e0b'
    };

    return (
        <div className="admin-overlay">
            <div className="admin-modal">
                <button className="admin-close" onClick={onClose}>×</button>

                <div className="admin-header">
                    <h2>⚙️ Admin Panel</h2>
                    <p>Manage users and external access</p>
                </div>

                <div className="admin-tabs">
                    <button
                        className={`tab ${activeTab === 'users' ? 'active' : ''}`}
                        onClick={() => setActiveTab('users')}
                    >
                        👥 Users
                    </button>
                    <button
                        className={`tab ${activeTab === 'external' ? 'active' : ''}`}
                        onClick={() => setActiveTab('external')}
                    >
                        🔗 External Links
                    </button>
                </div>

                <div className="admin-content">
                    {activeTab === 'users' && (
                        <div className="users-panel">
                            <h3>Registered Users ({users.length})</h3>
                            <div className="users-list">
                                {users.map((u) => (
                                    <div key={u.username} className="user-card">
                                        <div className="user-info">
                                            <span className="user-name">{u.full_name || u.username}</span>
                                            <span className="user-email">{u.email}</span>
                                        </div>
                                        <div className="user-meta">
                                            <span
                                                className="user-role"
                                                style={{ background: roleColors[u.role] || '#64748b' }}
                                            >
                                                {u.role.toUpperCase()}
                                            </span>
                                            <span className="user-dept">{u.department}</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {activeTab === 'external' && (
                        <div className="external-panel">
                            <div className="generate-section">
                                <h3>Generate External Link</h3>
                                <div className="form-row">
                                    <div className="form-group">
                                        <label>Paper IDs (comma-separated)</label>
                                        <input
                                            type="text"
                                            value={newLinkPapers}
                                            onChange={(e) => setNewLinkPapers(e.target.value)}
                                            placeholder="Leave empty for all papers"
                                        />
                                    </div>
                                    <div className="form-group small">
                                        <label>Expires (hours)</label>
                                        <input
                                            type="number"
                                            value={newLinkHours}
                                            onChange={(e) => setNewLinkHours(parseInt(e.target.value))}
                                            min="1"
                                            max="168"
                                        />
                                    </div>
                                    <button
                                        className="generate-btn"
                                        onClick={generateExternalLink}
                                        disabled={loading}
                                    >
                                        {loading ? '...' : '🔗 Generate'}
                                    </button>
                                </div>

                                {generatedLink && (
                                    <div className="generated-link">
                                        <p>✅ Link Generated!</p>
                                        <code>{window.location.origin}/external/{generatedLink.token}</code>
                                        <small>Expires: {new Date(generatedLink.expires_at).toLocaleString()}</small>
                                    </div>
                                )}
                            </div>

                            <div className="tokens-section">
                                <h3>Active Tokens ({externalTokens.length})</h3>
                                <div className="tokens-list">
                                    {externalTokens.map((t, i) => (
                                        <div key={i} className="token-card">
                                            <div className="token-info">
                                                <code>{t.token_display || t.token.substring(0, 16) + '...'}</code>
                                                <small>Created by: {t.created_by} | Access count: {t.access_count}</small>
                                            </div>
                                            <button
                                                className="revoke-btn"
                                                onClick={() => revokeToken(t.token)}
                                            >
                                                Revoke
                                            </button>
                                        </div>
                                    ))}
                                    {externalTokens.length === 0 && (
                                        <p className="no-tokens">No active external tokens</p>
                                    )}
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            <style>{`
        .admin-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.75);
          backdrop-filter: blur(8px);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
          animation: fadeIn 0.3s ease;
        }

        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }

        .admin-modal {
          background: linear-gradient(145deg, rgba(30, 41, 59, 0.98), rgba(15, 23, 42, 0.99));
          border: 1px solid rgba(100, 116, 139, 0.3);
          border-radius: 20px;
          width: 95%;
          max-width: 800px;
          max-height: 85vh;
          overflow: hidden;
          display: flex;
          flex-direction: column;
          animation: slideUp 0.4s ease;
          position: relative;
        }

        @keyframes slideUp {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }

        .admin-close {
          position: absolute;
          top: 1rem;
          right: 1rem;
          background: none;
          border: none;
          color: #94a3b8;
          font-size: 1.5rem;
          cursor: pointer;
          z-index: 10;
        }

        .admin-header {
          padding: 1.5rem 2rem;
          border-bottom: 1px solid rgba(100, 116, 139, 0.2);
        }

        .admin-header h2 {
          color: #f1f5f9;
          font-size: 1.5rem;
          margin-bottom: 0.25rem;
        }

        .admin-header p {
          color: #64748b;
          font-size: 0.875rem;
        }

        .admin-tabs {
          display: flex;
          padding: 0 2rem;
          gap: 0.5rem;
          border-bottom: 1px solid rgba(100, 116, 139, 0.2);
        }

        .tab {
          background: none;
          border: none;
          padding: 1rem 1.5rem;
          color: #94a3b8;
          font-size: 0.875rem;
          cursor: pointer;
          border-bottom: 2px solid transparent;
          transition: all 0.2s;
        }

        .tab:hover {
          color: #e2e8f0;
        }

        .tab.active {
          color: #3b82f6;
          border-bottom-color: #3b82f6;
        }

        .admin-content {
          padding: 1.5rem 2rem;
          overflow-y: auto;
          flex: 1;
        }

        .admin-content h3 {
          color: #e2e8f0;
          font-size: 1rem;
          margin-bottom: 1rem;
        }

        .users-list, .tokens-list {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }

        .user-card, .token-card {
          background: rgba(30, 41, 59, 0.5);
          border: 1px solid rgba(100, 116, 139, 0.2);
          border-radius: 10px;
          padding: 1rem;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .user-info {
          display: flex;
          flex-direction: column;
        }

        .user-name {
          color: #f1f5f9;
          font-weight: 500;
        }

        .user-email {
          color: #64748b;
          font-size: 0.813rem;
        }

        .user-meta {
          display: flex;
          gap: 0.75rem;
          align-items: center;
        }

        .user-role {
          padding: 0.25rem 0.75rem;
          border-radius: 20px;
          font-size: 0.688rem;
          font-weight: 600;
          color: white;
        }

        .user-dept {
          color: #94a3b8;
          font-size: 0.813rem;
        }

        .generate-section {
          margin-bottom: 2rem;
        }

        .form-row {
          display: flex;
          gap: 1rem;
          align-items: flex-end;
        }

        .form-group {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .form-group.small {
          flex: 0 0 120px;
        }

        .form-group label {
          color: #94a3b8;
          font-size: 0.75rem;
        }

        .form-group input {
          background: rgba(30, 41, 59, 0.8);
          border: 1px solid rgba(100, 116, 139, 0.3);
          border-radius: 8px;
          padding: 0.75rem;
          color: #f1f5f9;
          font-size: 0.875rem;
        }

        .generate-btn {
          background: linear-gradient(135deg, #3b82f6, #2563eb);
          border: none;
          border-radius: 8px;
          padding: 0.75rem 1.5rem;
          color: white;
          font-weight: 600;
          cursor: pointer;
          white-space: nowrap;
        }

        .generated-link {
          margin-top: 1rem;
          background: rgba(16, 185, 129, 0.1);
          border: 1px solid rgba(16, 185, 129, 0.3);
          border-radius: 10px;
          padding: 1rem;
        }

        .generated-link p {
          color: #10b981;
          font-weight: 500;
          margin-bottom: 0.5rem;
        }

        .generated-link code {
          display: block;
          background: rgba(30, 41, 59, 0.5);
          padding: 0.75rem;
          border-radius: 6px;
          color: #93c5fd;
          font-size: 0.813rem;
          word-break: break-all;
          margin-bottom: 0.5rem;
        }

        .generated-link small {
          color: #64748b;
        }

        .token-info {
          display: flex;
          flex-direction: column;
          gap: 0.25rem;
        }

        .token-info code {
          color: #93c5fd;
          font-size: 0.875rem;
        }

        .token-info small {
          color: #64748b;
          font-size: 0.75rem;
        }

        .revoke-btn {
          background: rgba(239, 68, 68, 0.2);
          border: 1px solid rgba(239, 68, 68, 0.3);
          border-radius: 6px;
          padding: 0.5rem 1rem;
          color: #fca5a5;
          font-size: 0.75rem;
          cursor: pointer;
        }

        .no-tokens {
          color: #64748b;
          text-align: center;
          padding: 2rem;
        }
      `}</style>
        </div>
    );
}
