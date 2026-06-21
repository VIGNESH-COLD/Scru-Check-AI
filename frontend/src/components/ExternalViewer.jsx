/**
 * ExternalViewer Component - Public, read-only view for external examiners.
 * No login required, authenticated solely via the url access token.
 */
import { useState, useEffect } from 'react';
import AnalysisDashboard from './AnalysisDashboard';

export default function ExternalViewer({ token }) {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [accessData, setAccessData] = useState(null);
    const [selectedPaperId, setSelectedPaperId] = useState(null);

    useEffect(() => {
        const fetchExternalData = async () => {
            try {
                const res = await fetch(`/api/external/view/${token}`);
                if (!res.ok) {
                    if (res.status === 401) {
                        throw new Error('Access link has expired or has been revoked by the system administrator.');
                    }
                    throw new Error('Could not verify access token. Please check the link and try again.');
                }
                const data = await res.json();
                setAccessData(data);
                
                // Set default selected paper
                const keys = Object.keys(data.results || {});
                if (keys.length > 0) {
                    setSelectedPaperId(keys[0]);
                }
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        if (token) {
            fetchExternalData();
        } else {
            setError('No access token provided.');
            setLoading(false);
        }
    }, [token]);

    const handleGoBack = () => {
        window.location.href = '/';
    };

    if (loading) {
        return (
            <div className="external-viewer-wrapper" style={styles.centerContainer}>
                <div style={styles.loaderCard}>
                    <div className="analyzing-pulse" style={styles.pulseIcon}>🔍</div>
                    <h3 style={styles.loaderTitle}>Verifying Secure Token</h3>
                    <p style={styles.loaderText}>Establishing connection and retrieving authorized documents...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="external-viewer-wrapper" style={styles.centerContainer}>
                <div style={styles.errorCard}>
                    <div style={styles.errorIcon}>⚠️</div>
                    <h2 style={styles.errorTitle}>Access Denied</h2>
                    <p style={styles.errorText}>{error}</p>
                    <button style={styles.primaryBtn} onClick={handleGoBack}>
                        Go to Portal Login
                    </button>
                </div>
            </div>
        );
    }

    const results = accessData?.results || {};
    const paperIds = Object.keys(results);

    return (
        <div className="external-viewer-container" style={styles.container}>
            {/* Header */}
            <header style={styles.header}>
                <div style={styles.brand}>
                    <span style={styles.logoIcon}>🛡️</span>
                    <div>
                        <h1 style={styles.title}>ScruCheck AI</h1>
                        <span style={styles.subtitle}>External Reviewer Portal</span>
                    </div>
                </div>
                {accessData?.expires_at && (
                    <div style={styles.expiryBadge}>
                        ⏳ Expires: {new Date(accessData.expires_at).toLocaleString()}
                    </div>
                )}
            </header>

            <main style={styles.mainContent}>
                {paperIds.length === 0 ? (
                    <div style={styles.emptyCard}>
                        <div style={styles.emptyIcon}>📁</div>
                        <h3 style={styles.emptyTitle}>No Scrutiny Results Found</h3>
                        <p style={styles.emptyText}>
                            The backend does not have active analysis results for the paper ID(s) linked to this token. 
                            If the server was recently restarted, the papers will need to be analyzed again.
                        </p>
                        <small style={styles.emptySmall}>
                            Authorized Scope: {accessData?.papers?.join(', ')}
                        </small>
                    </div>
                ) : (
                    <>
                        {/* Selector if multiple papers */}
                        {paperIds.length > 1 && (
                            <div style={styles.selectorCard}>
                                <label style={styles.selectorLabel}>Select Question Paper to Review:</label>
                                <select 
                                    value={selectedPaperId} 
                                    onChange={(e) => setSelectedPaperId(e.target.value)}
                                    style={styles.selectDropdown}
                                >
                                    {paperIds.map(pid => (
                                        <option key={pid} value={pid}>
                                            {pid} ({results[pid].overall_status})
                                        </option>
                                    ))}
                                </select>
                            </div>
                        )}

                        {selectedPaperId && results[selectedPaperId] && (
                            <div className="fade-in">
                                <AnalysisDashboard 
                                    result={results[selectedPaperId]} 
                                    isReadOnly={true} 
                                />
                            </div>
                        )}
                    </>
                )}
            </main>
        </div>
    );
}

const styles = {
    centerContainer: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        background: '#090d16',
        padding: '2rem',
        fontFamily: "'Inter', -apple-system, sans-serif",
    },
    loaderCard: {
        background: 'rgba(255, 255, 255, 0.02)',
        backdropFilter: 'blur(20px)',
        border: '1px solid rgba(255, 255, 255, 0.05)',
        borderRadius: '24px',
        padding: '3rem',
        textAlign: 'center',
        maxWidth: '440px',
        boxShadow: '0 20px 40px rgba(0,0,0,0.3)',
    },
    pulseIcon: {
        fontSize: '3rem',
        marginBottom: '1.5rem',
        display: 'inline-block',
    },
    loaderTitle: {
        color: '#fff',
        fontSize: '1.25rem',
        fontWeight: 700,
        marginBottom: '0.75rem',
        fontFamily: "'Outfit', sans-serif",
    },
    loaderText: {
        color: '#94a3b8',
        fontSize: '0.9rem',
        lineHeight: 1.6,
    },
    errorCard: {
        background: 'rgba(239, 68, 68, 0.02)',
        backdropFilter: 'blur(20px)',
        border: '1px solid rgba(239, 68, 68, 0.15)',
        borderRadius: '24px',
        padding: '3rem',
        textAlign: 'center',
        maxWidth: '460px',
        boxShadow: '0 20px 40px rgba(0,0,0,0.3)',
    },
    errorIcon: {
        fontSize: '3rem',
        marginBottom: '1.5rem',
    },
    errorTitle: {
        color: '#ef4444',
        fontSize: '1.5rem',
        fontWeight: 800,
        marginBottom: '1rem',
        fontFamily: "'Outfit', sans-serif",
    },
    errorText: {
        color: '#cbd5e1',
        fontSize: '0.95rem',
        lineHeight: 1.6,
        marginBottom: '2rem',
    },
    primaryBtn: {
        background: '#0052cc',
        color: 'white',
        border: 'none',
        borderRadius: '12px',
        padding: '0.85rem 1.75rem',
        fontSize: '0.95rem',
        fontWeight: 700,
        cursor: 'pointer',
        boxShadow: '0 8px 16px rgba(0, 82, 204, 0.25)',
        transition: 'transform 0.2s',
    },
    container: {
        minHeight: '100vh',
        background: '#090d16',
        color: '#f8fafc',
        fontFamily: "'Inter', -apple-system, sans-serif",
    },
    header: {
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '1.25rem 2rem',
        background: 'rgba(9, 13, 22, 0.7)',
        backdropFilter: 'blur(20px)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
        position: 'sticky',
        top: 0,
        zIndex: 100,
    },
    brand: {
        display: 'flex',
        alignItems: 'center',
        gap: '0.75rem',
    },
    logoIcon: {
        fontSize: '2rem',
    },
    title: {
        fontSize: '1.25rem',
        fontWeight: 800,
        letterSpacing: '-0.02em',
        fontFamily: "'Outfit', sans-serif",
        lineHeight: '1.2',
    },
    subtitle: {
        fontSize: '0.75rem',
        color: '#94a3b8',
        fontWeight: 600,
        textTransform: 'uppercase',
        letterSpacing: '0.05em',
    },
    expiryBadge: {
        background: 'rgba(245, 158, 11, 0.06)',
        border: '1px solid rgba(245, 158, 11, 0.15)',
        color: '#f59e0b',
        borderRadius: '100px',
        padding: '0.4rem 0.9rem',
        fontSize: '0.78rem',
        fontWeight: 600,
    },
    mainContent: {
        maxWidth: '1200px',
        margin: '0 auto',
        padding: '2.5rem 2rem 5rem 2rem',
    },
    emptyCard: {
        background: 'rgba(255, 255, 255, 0.01)',
        border: '1px solid rgba(255, 255, 255, 0.03)',
        borderRadius: '24px',
        padding: '4rem 2rem',
        textAlign: 'center',
        maxWidth: '600px',
        margin: '3rem auto 0 auto',
    },
    emptyIcon: {
        fontSize: '3.5rem',
        marginBottom: '1.5rem',
        opacity: 0.5,
    },
    emptyTitle: {
        fontSize: '1.35rem',
        fontWeight: 700,
        marginBottom: '0.75rem',
        color: '#fff',
    },
    emptyText: {
        color: '#94a3b8',
        fontSize: '0.95rem',
        lineHeight: 1.6,
        marginBottom: '1.5rem',
    },
    emptySmall: {
        display: 'block',
        color: '#64748b',
        fontFamily: 'monospace',
        fontSize: '0.8rem',
        background: 'rgba(0,0,0,0.15)',
        padding: '0.5rem',
        borderRadius: '8px',
    },
    selectorCard: {
        background: 'rgba(255, 255, 255, 0.02)',
        border: '1px solid rgba(255, 255, 255, 0.04)',
        borderRadius: '16px',
        padding: '1.25rem 1.5rem',
        marginBottom: '2rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1rem',
    },
    selectorLabel: {
        fontSize: '0.9rem',
        fontWeight: 600,
        color: '#cbd5e1',
    },
    selectDropdown: {
        background: '#0f172a',
        border: '1.5px solid rgba(255, 255, 255, 0.08)',
        borderRadius: '10px',
        padding: '0.6rem 2.5rem 0.6rem 1rem',
        color: '#fff',
        fontSize: '0.9rem',
        fontWeight: 600,
        cursor: 'pointer',
        outline: 'none',
    },
};
