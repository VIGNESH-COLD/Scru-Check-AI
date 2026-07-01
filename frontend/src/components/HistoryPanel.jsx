/**
 * HistoryPanel — Manage Analysis History
 * Shows all previously analysed papers with status badges,
 * score summaries, download and delete actions.
 */
import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../context/AuthContext'

const STATUS_CONFIG = {
    APPROVED:    { color: '#34d399', bg: 'rgba(52,211,153,0.12)',  border: 'rgba(52,211,153,0.25)',  icon: '✓', label: 'Approved'    },
    CONDITIONAL: { color: '#fbbf24', bg: 'rgba(251,191,36,0.12)',  border: 'rgba(251,191,36,0.25)',  icon: '!', label: 'Conditional' },
    REJECTED:    { color: '#f87171', bg: 'rgba(248,113,113,0.12)', border: 'rgba(248,113,113,0.25)', icon: '✗', label: 'Rejected'    },
    UNKNOWN:     { color: '#94a3b8', bg: 'rgba(148,163,184,0.12)', border: 'rgba(148,163,184,0.25)', icon: '?', label: 'Unknown'     },
}

const CRITERION_LABELS = {
    format_compliance:  'Format',
    regulation_check:   'Regulation',
    mark_distribution:  'Marks',
    permitted_aids:     'Aids',
    syllabus_alignment: 'Syllabus',
    blooms_taxonomy:    "Bloom's",
    grammar_clarity:    'Grammar',
    repetition_check:   'Repetition',
    diagrams_symbols:   'Diagrams',
}

function StatusBadge({ status }) {
    const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.UNKNOWN
    return (
        <span style={{
            display: 'inline-flex', alignItems: 'center', gap: '0.35rem',
            padding: '0.25rem 0.7rem', borderRadius: '100px',
            background: cfg.bg, border: `1px solid ${cfg.border}`,
            color: cfg.color, fontSize: '0.72rem', fontWeight: 700,
            fontFamily: 'var(--font-heading)', letterSpacing: '0.03em',
        }}>
            <span style={{ fontSize: '0.75rem' }}>{cfg.icon}</span>
            {cfg.label}
        </span>
    )
}

function MandatoryDots({ items }) {
    return (
        <div style={{ display: 'flex', gap: '0.3rem', flexWrap: 'wrap' }}>
            {items.map(f => (
                <span
                    key={f.criterion}
                    title={`${CRITERION_LABELS[f.criterion] || f.criterion}: ${f.status}`}
                    style={{
                        width: 10, height: 10, borderRadius: '50%', flexShrink: 0,
                        background: f.status === 'PASS' ? '#34d399' : '#f87171',
                        boxShadow: f.status === 'PASS'
                            ? '0 0 4px rgba(52,211,153,0.5)'
                            : '0 0 4px rgba(248,113,113,0.5)',
                    }}
                />
            ))}
        </div>
    )
}

function QualityBar({ score, criterion }) {
    const color = score >= 80 ? '#34d399' : score >= 60 ? '#fbbf24' : '#f87171'
    return (
        <div title={`${CRITERION_LABELS[criterion] || criterion}: ${score ?? 'N/A'}`}
            style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem', minWidth: 40 }}>
            <div style={{ height: 4, borderRadius: 4, background: 'rgba(255,255,255,0.06)', overflow: 'hidden' }}>
                <div style={{
                    height: '100%', width: `${score ?? 0}%`,
                    background: color, borderRadius: 4,
                    transition: 'width 0.6s cubic-bezier(0.4,0,0.2,1)',
                }} />
            </div>
            <span style={{ fontSize: '0.6rem', color: 'var(--text-dim)', textAlign: 'center' }}>
                {score ?? 'N/A'}
            </span>
        </div>
    )
}

export default function HistoryPanel({ onViewResult }) {
    const { user, hasPermission } = useAuth()
    const [papers, setPapers] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [deletingId, setDeletingId] = useState(null)
    const [search, setSearch] = useState('')
    const [filterStatus, setFilterStatus] = useState('ALL')
    const [sortBy, setSortBy] = useState('newest')
    const [confirmDelete, setConfirmDelete] = useState(null) // paper_id to confirm

    const canDelete = hasPermission('manage_users') // COE only

    const fetchHistory = useCallback(async () => {
        setLoading(true)
        setError(null)
        try {
            const token = localStorage.getItem('auth_token')
            const res = await fetch('/api/history', {
                headers: token ? { Authorization: `Bearer ${token}` } : {}
            })
            if (!res.ok) throw new Error(`HTTP ${res.status}`)
            const data = await res.json()
            setPapers(data.papers || [])
        } catch (e) {
            setError('Failed to load history. ' + e.message)
        } finally {
            setLoading(false)
        }
    }, [])

    useEffect(() => { fetchHistory() }, [fetchHistory])

    const handleDelete = async (paper_id) => {
        setDeletingId(paper_id)
        try {
            const token = localStorage.getItem('auth_token')
            const res = await fetch(`/api/history/${paper_id}`, {
                method: 'DELETE',
                headers: token ? { Authorization: `Bearer ${token}` } : {}
            })
            if (!res.ok) throw new Error(`HTTP ${res.status}`)
            setPapers(prev => prev.filter(p => p.paper_id !== paper_id))
        } catch (e) {
            setError('Delete failed: ' + e.message)
        } finally {
            setDeletingId(null)
            setConfirmDelete(null)
        }
    }

    const handleDownload = (paper_id) => {
        const token = localStorage.getItem('auth_token')
        const url = `/api/report/${paper_id}`
        const a = document.createElement('a')
        a.href = url
        a.download = `ScruCheck_Report_${paper_id}.docx`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
    }

    // Filter + sort
    let visible = papers.filter(p => {
        const matchSearch = !search ||
            p.paper_id.toLowerCase().includes(search.toLowerCase()) ||
            (p.department || '').toLowerCase().includes(search.toLowerCase()) ||
            (p.created_by || '').toLowerCase().includes(search.toLowerCase())
        const matchStatus = filterStatus === 'ALL' || p.overall_status === filterStatus
        return matchSearch && matchStatus
    })

    if (sortBy === 'newest')   visible = [...visible].sort((a, b) => b.timestamp.localeCompare(a.timestamp))
    if (sortBy === 'oldest')   visible = [...visible].sort((a, b) => a.timestamp.localeCompare(b.timestamp))
    if (sortBy === 'score')    visible = [...visible].sort((a, b) => (b.avg_quality_score || 0) - (a.avg_quality_score || 0))
    if (sortBy === 'status')   visible = [...visible].sort((a, b) => a.overall_status.localeCompare(b.overall_status))

    const statusCounts = { ALL: papers.length }
    papers.forEach(p => { statusCounts[p.overall_status] = (statusCounts[p.overall_status] || 0) + 1 })

    return (
        <div className="fade-up" style={{ maxWidth: 1100, margin: '0 auto' }}>
            {/* Header */}
            <div style={{ marginBottom: '2rem' }}>
                <h1 className="welcome-title">Analysis <span className="gradient-text">History</span></h1>
                <p className="text-muted" style={{ marginTop: '0.4rem', fontSize: '1rem' }}>
                    {papers.length} paper{papers.length !== 1 ? 's' : ''} analysed · Manage and review past scrutiny results
                </p>
            </div>

            {/* Controls row */}
            <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.25rem', flexWrap: 'wrap', alignItems: 'center' }}>
                {/* Search */}
                <div style={{ position: 'relative', flex: '1 1 220px' }}>
                    <span style={{ position: 'absolute', left: '0.85rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)', fontSize: '0.85rem' }}>🔍</span>
                    <input
                        type="text"
                        placeholder="Search by ID, department, author…"
                        value={search}
                        onChange={e => setSearch(e.target.value)}
                        style={{
                            width: '100%', padding: '0.6rem 0.85rem 0.6rem 2.2rem',
                            background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)',
                            borderRadius: 10, color: 'var(--text-main)', fontSize: '0.82rem',
                            outline: 'none', fontFamily: 'var(--font-body)', boxSizing: 'border-box',
                        }}
                    />
                </div>

                {/* Status filter pills */}
                <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap' }}>
                    {['ALL', 'APPROVED', 'CONDITIONAL', 'REJECTED'].map(s => {
                        const cfg = STATUS_CONFIG[s] || { color: 'var(--text-muted)', bg: 'rgba(255,255,255,0.04)', border: 'rgba(255,255,255,0.08)' }
                        const active = filterStatus === s
                        return (
                            <button key={s} onClick={() => setFilterStatus(s)} style={{
                                padding: '0.4rem 0.8rem', borderRadius: 8, fontSize: '0.75rem', fontWeight: 600,
                                border: `1px solid ${active ? cfg.border : 'rgba(255,255,255,0.06)'}`,
                                background: active ? cfg.bg : 'transparent',
                                color: active ? cfg.color : 'var(--text-dim)',
                                cursor: 'pointer', transition: 'all 0.15s', fontFamily: 'var(--font-heading)',
                            }}>
                                {s === 'ALL' ? `All (${statusCounts.ALL})` : `${s[0] + s.slice(1).toLowerCase()} (${statusCounts[s] || 0})`}
                            </button>
                        )
                    })}
                </div>

                {/* Sort */}
                <select value={sortBy} onChange={e => setSortBy(e.target.value)} style={{
                    padding: '0.55rem 0.85rem', background: 'rgba(255,255,255,0.04)',
                    border: '1px solid rgba(255,255,255,0.08)', borderRadius: 10,
                    color: 'var(--text-muted)', fontSize: '0.8rem', cursor: 'pointer',
                    fontFamily: 'var(--font-body)', outline: 'none',
                }}>
                    <option value="newest">Newest first</option>
                    <option value="oldest">Oldest first</option>
                    <option value="score">Highest score</option>
                    <option value="status">By status</option>
                </select>

                <button onClick={fetchHistory} style={{
                    padding: '0.55rem 1rem', borderRadius: 10, fontSize: '0.8rem', fontWeight: 600,
                    background: 'rgba(129,140,248,0.1)', border: '1px solid rgba(129,140,248,0.2)',
                    color: 'var(--primary)', cursor: 'pointer', transition: 'all 0.15s',
                    fontFamily: 'var(--font-heading)',
                }}>↻ Refresh</button>
            </div>

            {/* Error */}
            {error && (
                <div style={{
                    padding: '0.85rem 1.1rem', borderRadius: 12, marginBottom: '1rem',
                    background: 'rgba(248,113,113,0.08)', border: '1px solid rgba(248,113,113,0.18)',
                    color: 'var(--danger)', fontSize: '0.85rem', display: 'flex', gap: '0.5rem',
                }}>⚠ {error}</div>
            )}

            {/* Loading */}
            {loading && (
                <div style={{ textAlign: 'center', padding: '4rem 2rem', color: 'var(--text-dim)' }}>
                    <div className="analyzing-pulse" style={{ fontSize: '2rem' }}>📜</div>
                    <p style={{ marginTop: '1rem' }}>Loading history…</p>
                </div>
            )}

            {/* Empty */}
            {!loading && visible.length === 0 && (
                <div className="card" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
                    <div style={{ fontSize: '3rem', marginBottom: '0.75rem' }}>🗂️</div>
                    <h3 style={{ marginBottom: '0.4rem', color: 'var(--text-main)' }}>No papers found</h3>
                    <p className="text-muted" style={{ fontSize: '0.85rem' }}>
                        {search || filterStatus !== 'ALL' ? 'Try adjusting your filters.' : 'Analyze a question paper to see it here.'}
                    </p>
                </div>
            )}

            {/* Table */}
            {!loading && visible.length > 0 && (
                <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                    <div style={{ overflowX: 'auto' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                            <thead>
                                <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                                    {['Paper ID', 'Date', 'Status', 'Mandatory Checks', 'Quality Scores', 'Avg Score', 'Actions'].map(h => (
                                        <th key={h} style={{
                                            padding: '0.9rem 1.1rem', textAlign: 'left',
                                            fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-dim)',
                                            textTransform: 'uppercase', letterSpacing: '0.06em',
                                            fontFamily: 'var(--font-heading)', whiteSpace: 'nowrap',
                                        }}>{h}</th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {visible.map((paper, idx) => {
                                    const date = paper.timestamp
                                        ? new Date(paper.timestamp).toLocaleString('en-IN', {
                                            day: '2-digit', month: 'short', year: 'numeric',
                                            hour: '2-digit', minute: '2-digit'
                                          })
                                        : '—'
                                    const isDeleting = deletingId === paper.paper_id
                                    return (
                                        <tr key={paper.paper_id} style={{
                                            borderBottom: idx < visible.length - 1 ? '1px solid rgba(255,255,255,0.04)' : 'none',
                                            transition: 'background 0.15s',
                                        }}
                                        onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.025)'}
                                        onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                                        >
                                            {/* Paper ID */}
                                            <td style={{ padding: '0.85rem 1.1rem' }}>
                                                <div style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-main)', fontFamily: 'var(--font-heading)' }}>
                                                    {paper.paper_id.replace('PAPER_', '')}
                                                </div>
                                                <div style={{ fontSize: '0.68rem', color: 'var(--text-dim)', marginTop: '0.15rem' }}>
                                                    {paper.department} · {paper.created_by}
                                                </div>
                                            </td>

                                            {/* Date */}
                                            <td style={{ padding: '0.85rem 1.1rem', fontSize: '0.75rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                                                {date}
                                            </td>

                                            {/* Status */}
                                            <td style={{ padding: '0.85rem 1.1rem' }}>
                                                <StatusBadge status={paper.overall_status} />
                                            </td>

                                            {/* Mandatory checks */}
                                            <td style={{ padding: '0.85rem 1.1rem' }}>
                                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                                                    <MandatoryDots items={paper.mandatory_compliance || []} />
                                                    <span style={{ fontSize: '0.65rem', color: 'var(--text-dim)' }}>
                                                        {paper.mandatory_passed}/{paper.mandatory_total} passed
                                                    </span>
                                                </div>
                                            </td>

                                            {/* Quality mini-bars */}
                                            <td style={{ padding: '0.85rem 1.1rem' }}>
                                                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-end' }}>
                                                    {(paper.quality_scores || []).map(q => (
                                                        <QualityBar key={q.criterion} criterion={q.criterion} score={q.score} />
                                                    ))}
                                                </div>
                                            </td>

                                            {/* Avg Score */}
                                            <td style={{ padding: '0.85rem 1.1rem' }}>
                                                <div style={{
                                                    fontSize: '1.1rem', fontWeight: 800,
                                                    fontFamily: 'var(--font-heading)',
                                                    color: paper.avg_quality_score >= 80 ? '#34d399'
                                                         : paper.avg_quality_score >= 60 ? '#fbbf24'
                                                         : '#f87171',
                                                }}>
                                                    {paper.avg_quality_score}
                                                    <span style={{ fontSize: '0.65rem', color: 'var(--text-dim)', fontWeight: 400 }}>/100</span>
                                                </div>
                                            </td>

                                            {/* Actions */}
                                            <td style={{ padding: '0.85rem 1.1rem' }}>
                                                <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
                                                    {/* Download */}
                                                    <button
                                                        onClick={() => handleDownload(paper.paper_id)}
                                                        title="Download DOCX report"
                                                        style={{
                                                            padding: '0.4rem 0.75rem', borderRadius: 8, fontSize: '0.72rem',
                                                            fontWeight: 600, border: '1px solid rgba(129,140,248,0.25)',
                                                            background: 'rgba(129,140,248,0.08)', color: 'var(--primary)',
                                                            cursor: 'pointer', transition: 'all 0.15s',
                                                            fontFamily: 'var(--font-heading)',
                                                        }}
                                                    >⬇ Report</button>

                                                    {/* Delete — COE only */}
                                                    {canDelete && (
                                                        confirmDelete === paper.paper_id ? (
                                                            <div style={{ display: 'flex', gap: '0.3rem' }}>
                                                                <button
                                                                    onClick={() => handleDelete(paper.paper_id)}
                                                                    disabled={isDeleting}
                                                                    style={{
                                                                        padding: '0.4rem 0.6rem', borderRadius: 8, fontSize: '0.72rem',
                                                                        fontWeight: 700, border: '1px solid rgba(248,113,113,0.4)',
                                                                        background: 'rgba(248,113,113,0.15)', color: '#f87171',
                                                                        cursor: 'pointer', fontFamily: 'var(--font-heading)',
                                                                    }}
                                                                >{isDeleting ? '…' : 'Confirm'}</button>
                                                                <button
                                                                    onClick={() => setConfirmDelete(null)}
                                                                    style={{
                                                                        padding: '0.4rem 0.6rem', borderRadius: 8, fontSize: '0.72rem',
                                                                        border: '1px solid rgba(255,255,255,0.08)',
                                                                        background: 'transparent', color: 'var(--text-dim)',
                                                                        cursor: 'pointer', fontFamily: 'var(--font-heading)',
                                                                    }}
                                                                >Cancel</button>
                                                            </div>
                                                        ) : (
                                                            <button
                                                                onClick={() => setConfirmDelete(paper.paper_id)}
                                                                title="Delete this record"
                                                                style={{
                                                                    padding: '0.4rem 0.6rem', borderRadius: 8, fontSize: '0.72rem',
                                                                    fontWeight: 600, border: '1px solid rgba(248,113,113,0.15)',
                                                                    background: 'rgba(248,113,113,0.06)', color: 'var(--danger)',
                                                                    cursor: 'pointer', transition: 'all 0.15s',
                                                                    fontFamily: 'var(--font-heading)',
                                                                }}
                                                            >✕</button>
                                                        )
                                                    )}
                                                </div>
                                            </td>
                                        </tr>
                                    )
                                })}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* Summary footer */}
            {!loading && papers.length > 0 && (
                <div style={{
                    display: 'flex', gap: '1rem', marginTop: '1.5rem', flexWrap: 'wrap',
                }}>
                    {[
                        { label: 'Total Analysed', value: papers.length, color: 'var(--primary)' },
                        { label: 'Approved', value: statusCounts.APPROVED || 0, color: '#34d399' },
                        { label: 'Conditional', value: statusCounts.CONDITIONAL || 0, color: '#fbbf24' },
                        { label: 'Rejected', value: statusCounts.REJECTED || 0, color: '#f87171' },
                        {
                            label: 'Avg Quality',
                            value: papers.length
                                ? Math.round(papers.reduce((s, p) => s + (p.avg_quality_score || 0), 0) / papers.length) + '/100'
                                : '—',
                            color: 'var(--text-main)',
                        },
                    ].map(stat => (
                        <div key={stat.label} style={{
                            flex: '1 1 120px', padding: '0.85rem 1.1rem', borderRadius: 12,
                            background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)',
                            textAlign: 'center',
                        }}>
                            <div style={{ fontSize: '1.4rem', fontWeight: 800, color: stat.color, fontFamily: 'var(--font-heading)' }}>
                                {stat.value}
                            </div>
                            <div style={{ fontSize: '0.68rem', color: 'var(--text-dim)', marginTop: '0.2rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                                {stat.label}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}
