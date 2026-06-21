/**
 * Header Component with Authentication
 */
import { useState } from 'react'
import { useAuth } from '../context/AuthContext'

export default function Header({ onNavigate, currentPage, onLoginClick, onAdminClick }) {
    const { user, isAuthenticated, isAdmin, logout } = useAuth()

    const handleNavClick = (page) => {
        if (onNavigate) {
            onNavigate(page)
        } else {
            alert(`${page} feature coming soon!`)
        }
    }

    const roleConfig = {
        coe: { color: '#818cf8', bg: 'rgba(129,140,248,0.15)', label: 'COE' },
        hod: { color: '#c084fc', bg: 'rgba(192,132,252,0.15)', label: 'HOD' },
        faculty: { color: '#34d399', bg: 'rgba(52,211,153,0.15)', label: 'Faculty' },
        auditor: { color: '#fbbf24', bg: 'rgba(251,191,36,0.15)', label: 'Auditor' }
    }

    const role = roleConfig[user.role] || { color: '#94a3b8', bg: 'rgba(148,163,184,0.15)', label: user.role }

    return (
        <header className="header">
            <div className="header-content">
                <div className="logo" onClick={() => handleNavClick('dashboard')} style={{ cursor: 'pointer' }}>
                    <div className="logo-icon">SC</div>
                    <div>
                        <div className="logo-text">ScruCheck AI</div>
                        <div className="logo-subtitle">AI-Powered Question Paper Scrutiny</div>
                    </div>
                </div>

                <nav style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <div className="hdr-nav-group">
                        <button
                            className={`hdr-nav-btn ${currentPage === 'dashboard' ? 'active' : ''}`}
                            onClick={() => handleNavClick('dashboard')}
                        >
                            <span className="nav-icon">📊</span>
                            Dashboard
                        </button>
                        <button
                            className={`hdr-nav-btn ${currentPage === 'history' ? 'active' : ''}`}
                            onClick={() => handleNavClick('history')}
                        >
                            <span className="nav-icon">📜</span>
                            History
                        </button>

                        {isAdmin && (
                            <button
                                className="hdr-nav-btn"
                                onClick={onAdminClick}
                            >
                                <span className="nav-icon">⚙️</span>
                                Admin
                            </button>
                        )}
                    </div>

                    <div className="hdr-user-section">
                        <div className="hdr-user-pill">
                            <div className="hdr-avatar" style={{ background: role.bg, color: role.color }}>
                                {(user.full_name || user.username || '?').charAt(0).toUpperCase()}
                            </div>
                            <div className="hdr-user-info">
                                <span className="hdr-user-name">{user.full_name || user.username}</span>
                                <span className="hdr-user-role" style={{ color: role.color }}>{role.label}</span>
                            </div>
                            <button className="hdr-logout" onClick={logout}>
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                                    <polyline points="16 17 21 12 16 7"/>
                                    <line x1="21" y1="12" x2="9" y2="12"/>
                                </svg>
                            </button>
                        </div>
                    </div>
                </nav>
            </div>

            <style>{`
                .hdr-nav-group {
                    display: flex;
                    gap: 0.25rem;
                    background: rgba(255, 255, 255, 0.04);
                    padding: 0.3rem;
                    border-radius: 14px;
                    border: 1px solid rgba(255, 255, 255, 0.06);
                }

                .hdr-nav-btn {
                    padding: 0.55rem 1rem;
                    border-radius: 10px;
                    font-size: 0.8rem;
                    font-weight: 600;
                    color: var(--text-dim);
                    background: transparent;
                    border: none;
                    cursor: pointer;
                    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
                    display: flex;
                    align-items: center;
                    gap: 0.45rem;
                    font-family: var(--font-heading);
                    white-space: nowrap;
                }

                .hdr-nav-btn:hover {
                    color: var(--text-muted);
                    background: rgba(255, 255, 255, 0.04);
                }

                .hdr-nav-btn.active {
                    color: var(--primary);
                    background: rgba(129, 140, 248, 0.1);
                }

                .nav-icon {
                    font-size: 0.9rem;
                    line-height: 1;
                }

                .hdr-user-section {
                    margin-left: 0.5rem;
                }

                .hdr-user-pill {
                    display: flex;
                    align-items: center;
                    gap: 0.65rem;
                    background: rgba(255, 255, 255, 0.04);
                    padding: 0.35rem;
                    padding-right: 0.5rem;
                    border-radius: 100px;
                    border: 1px solid rgba(255, 255, 255, 0.06);
                    transition: all 0.2s;
                }

                .hdr-user-pill:hover {
                    border-color: rgba(255, 255, 255, 0.1);
                }

                .hdr-avatar {
                    width: 34px;
                    height: 34px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: 700;
                    font-size: 0.85rem;
                    font-family: var(--font-heading);
                    flex-shrink: 0;
                }

                .hdr-user-info {
                    display: flex;
                    flex-direction: column;
                    line-height: 1.2;
                }

                .hdr-user-name {
                    font-size: 0.8rem;
                    font-weight: 600;
                    color: var(--text-main);
                }

                .hdr-user-role {
                    font-size: 0.6rem;
                    font-weight: 700;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                }

                .hdr-logout {
                    width: 30px;
                    height: 30px;
                    border-radius: 8px;
                    border: none;
                    background: rgba(248, 113, 113, 0.08);
                    color: var(--danger);
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.2s;
                    margin-left: 0.25rem;
                    flex-shrink: 0;
                }

                .hdr-logout:hover {
                    background: rgba(248, 113, 113, 0.2);
                }
            `}</style>
        </header>
    )
}
