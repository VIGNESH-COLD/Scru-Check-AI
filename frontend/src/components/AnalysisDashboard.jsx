import { useState } from 'react'
import BloomsChart from './BloomsChart'
import SyllabusHeatmap from './SyllabusHeatmap'
import COTable from './COTable'

const API_BASE = ''

const BLOOM_ORDER = ['Remember', 'Understand', 'Apply', 'Analyze', 'Evaluate', 'Create']

const MANDATORY_LABELS = {
    format_compliance: 'Format Compliance',
    regulation_check: 'Regulation Compliance',
    mark_distribution: 'Mark Distribution',
    permitted_aids: 'Permitted Aids Compliance',
}

const QUALITY_LABELS = {
    syllabus_alignment: 'Syllabus Coverage',
    blooms_taxonomy: "Bloom's Taxonomy Distribution",
    grammar_clarity: 'Grammar & Clarity',
    repetition_check: 'Repetition Risk',
    diagrams_symbols: 'Diagram & Symbol Quality',
}

const ALL_LABELS = { ...MANDATORY_LABELS, ...QUALITY_LABELS }

// ── Quality Score bar (0-100) ──
function ScoreBar({ value }) {
    const score = value ?? 0
    const color =
        score >= 90 ? 'var(--success)' :
        score >= 70 ? '#3b82f6' :
        score >= 50 ? 'var(--warning)' : 'var(--danger)'
    return (
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '0.5rem' }}>
            <div style={{
                flex: 1, height: '6px', background: 'rgba(255,255,255,0.06)',
                borderRadius: '100px', overflow: 'hidden'
            }}>
                <div style={{
                    width: `${score}%`, height: '100%', borderRadius: '100px',
                    background: color, transition: 'width 1s cubic-bezier(0.4, 0, 0.2, 1)'
                }} />
            </div>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color, minWidth: '42px', fontFamily: 'var(--font-heading)' }}>
                {score}/100
            </span>
        </div>
    )
}

// ── Improvement panel ──
function ImprovementPanel({ finding, isReadOnly }) {
    const [open, setOpen] = useState(false)
    const [loading, setLoading] = useState(false)
    const [result, setResult] = useState(null)
    const [error, setError] = useState(null)

    if (isReadOnly || finding.status === 'PASS' || finding.status === 'NOT_EVALUATED') return null

    const issueTypeMap = {
        blooms_taxonomy: 'bloom_level',
        grammar_clarity: 'grammar',
        syllabus_alignment: 'syllabus',
    }
    const issueType = issueTypeMap[finding.criterion]
    if (!issueType) return null

    const questionText =
        finding.evidence?.question_text ||
        finding.evidence?.sample_question ||
        'Question text extraction unavailable.'

    const currentBloom = finding.evidence?.bloom_level || null
    const targetBloom = currentBloom
        ? BLOOM_ORDER[Math.min(BLOOM_ORDER.indexOf(currentBloom) + 1, 5)]
        : null

    const handleFetch = async () => {
        if (result) { setOpen(o => !o); return }
        setLoading(true)
        setError(null)
        try {
            const body = {
                question: questionText,
                issue_type: issueType,
                current_finding: finding.suggestion || finding.rule_triggered,
                current_bloom_level: currentBloom,
                target_bloom_level: targetBloom,
            }
            const token = localStorage.getItem('token')
            const res = await fetch(`${API_BASE}/api/improve`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { Authorization: `Bearer ${token}` } : {})
                },
                body: JSON.stringify(body),
            })
            if (!res.ok) throw new Error(`HTTP ${res.status}`)
            setResult(await res.json())
            setOpen(true)
        } catch (e) {
            setError(e.message)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div style={{ marginTop: '0.75rem', borderTop: '1px solid rgba(255,255,255,0.04)', paddingTop: '0.65rem' }}>
            <button
                className="btn btn-glass"
                style={{ fontSize: '0.7rem', padding: '0.3rem 0.65rem' }}
                onClick={handleFetch}
                disabled={loading}
            >
                {loading ? 'Asking AI...' : '✨ Suggest Fix'}
            </button>

            {error && <p style={{ color: 'var(--warning)', fontSize: '0.75rem', marginTop: '0.5rem' }}>⚠️ {error}</p>}

            {open && result && (
                <div style={{
                    marginTop: '0.75rem', background: 'rgba(129,140,248,0.04)',
                    border: '1px solid rgba(129,140,248,0.15)', borderRadius: '12px', padding: '1.1rem'
                }}>
                    <div style={{ marginBottom: '0.75rem' }}>
                        <span style={{ display: 'block', fontSize: '0.65rem', fontWeight: 800, color: 'var(--primary)', textTransform: 'uppercase', marginBottom: '0.2rem' }}>Current</span>
                        <p style={{ fontSize: '0.82rem', color: 'var(--text-dim)' }}>{result.original_question}</p>
                    </div>
                    <div style={{ marginBottom: '0.75rem' }}>
                        <span style={{ display: 'block', fontSize: '0.65rem', fontWeight: 800, color: 'var(--success)', textTransform: 'uppercase', marginBottom: '0.2rem' }}>Recommended Fix</span>
                        <p style={{ fontSize: '0.9rem', color: '#fff', fontWeight: 600, lineHeight: 1.5 }}>{result.improved_question}</p>
                    </div>
                    {result.reasoning && (
                        <div style={{ marginBottom: '0.75rem' }}>
                            <span style={{ display: 'block', fontSize: '0.65rem', fontWeight: 800, color: 'var(--text-dim)', textTransform: 'uppercase', marginBottom: '0.2rem' }}>Reasoning</span>
                            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{result.reasoning}</p>
                        </div>
                    )}
                    <button className="btn btn-glass" style={{ fontSize: '0.65rem', padding: '0.25rem 0.5rem' }} onClick={() => setOpen(false)}>
                        Dismiss
                    </button>
                </div>
            )}
        </div>
    )
}

// ── Main dashboard ──
export default function AnalysisDashboard({ result, onReset, isReadOnly = false }) {
    const statusConfig = {
        APPROVED: { color: 'var(--success)', bg: 'rgba(52,211,153,0.08)', border: 'rgba(52,211,153,0.2)', icon: '✅', label: 'Approved' },
        CONDITIONAL: { color: 'var(--warning)', bg: 'rgba(251,191,36,0.08)', border: 'rgba(251,191,36,0.2)', icon: '⚠️', label: 'Conditional' },
        REJECTED: { color: 'var(--danger)', bg: 'rgba(248,113,113,0.08)', border: 'rgba(248,113,113,0.2)', icon: '❌', label: 'Rejected' },
    }

    const status = statusConfig[result.overall_status] || statusConfig.CONDITIONAL

    // Split findings into mandatory and quality
    const mandatoryKeys = new Set(['format_compliance', 'regulation_check', 'mark_distribution', 'permitted_aids'])
    const qualityKeys = new Set(['syllabus_alignment', 'blooms_taxonomy', 'grammar_clarity', 'repetition_check', 'diagrams_symbols'])

    const mandatoryFindings = result.findings.filter(f => mandatoryKeys.has(f.criterion))
    const qualityFindings = result.findings.filter(f => qualityKeys.has(f.criterion))

    const mandatoryPassed = result.mandatory_passed ?? mandatoryFindings.filter(f => f.status === 'PASS').length
    const mandatoryTotal = result.mandatory_total ?? mandatoryFindings.length
    // Weights from backend (or fallback defaults matching scrutiny_engine.py)
    const WEIGHTS = result.quality_weights || {
        syllabus_alignment: 0.35,
        blooms_taxonomy:    0.25,
        grammar_clarity:    0.15,
        repetition_check:   0.15,
        diagrams_symbols:   0.10,
    }

    // Exclude null (N/A) scores; re-normalise weights so they still sum to 1
    const scoredFindings = qualityFindings.filter(f => f.score != null)
    const totalWeight = scoredFindings.reduce((s, f) => s + (WEIGHTS[f.criterion] || 0), 0)
    const avgQuality = result.avg_quality_score ?? (
        scoredFindings.length > 0 && totalWeight > 0
            ? Math.round(
                scoredFindings.reduce((s, f) => s + f.score * (WEIGHTS[f.criterion] || 0), 0) / totalWeight
              )
            : 0
    )

    const downloadReport = async () => {
        try {
            const token = localStorage.getItem('token')
            const response = await fetch(`/api/report/${result.paper_id}`, {
                headers: token ? { Authorization: `Bearer ${token}` } : {}
            })
            if (response.ok) {
                const blob = await response.blob()
                const url = window.URL.createObjectURL(blob)
                const a = document.createElement('a')
                a.href = url
                a.download = `ScruCheck_Report_${result.paper_id}.docx`
                a.click()
                window.URL.revokeObjectURL(url)
            }
        } catch {
            alert('Report download available when backend is running')
        }
    }

    const mandatoryColor = mandatoryPassed === mandatoryTotal ? 'var(--success)' : 'var(--danger)'
    const qualityColor = avgQuality >= 70 ? 'var(--success)' : avgQuality >= 50 ? 'var(--warning)' : 'var(--danger)'

    // Compute the human-readable reason for the decision (mirrors backend rules)
    const syllabusScore = qualityFindings.find(f => f.criterion === 'syllabus_alignment')?.score ?? null
    const failedMandatory = mandatoryFindings.filter(f => f.status !== 'PASS')
    const statusReason = (() => {
        if (result.overall_status === 'APPROVED') return 'All compliance checks passed and quality is satisfactory.'
        if (failedMandatory.length > 0)
            return `Mandatory failure: ${failedMandatory.map(f => f.criterion.replace(/_/g, ' ')).join(', ')}`
        if (syllabusScore !== null && syllabusScore < 40)
            return `Syllabus coverage critically low (${syllabusScore}/100 — below 40 threshold)`
        if (syllabusScore !== null && syllabusScore < 50)
            return `Syllabus coverage insufficient (${syllabusScore}/100 — below 50 threshold)`
        if (avgQuality < 60)
            return `Overall quality score too low (${avgQuality}/100 — below 60 threshold)`
        return ''
    })()

    return (
        <div className="fade-up">
            {/* Header row */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
                <div>
                    <h2 className="welcome-title" style={{ fontSize: '2rem' }}>
                        Analysis <span className="gradient-text">Results</span>
                    </h2>
                    <p className="text-muted" style={{ marginTop: '0.25rem', fontSize: '0.85rem' }}>
                        ID: {result.paper_id} • {new Date().toLocaleDateString()}
                    </p>
                </div>
                <div style={{ display: 'flex', gap: '0.6rem' }}>
                    {!isReadOnly && <button className="btn btn-glass" onClick={onReset}>🔄 New Analysis</button>}
                    <button className="btn btn-primary" onClick={downloadReport}>📥 Download</button>
                </div>
            </div>

            {/* Score overview */}
            <div className="card mb-4" style={{ borderLeft: `4px solid ${status.color}` }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1.5rem' }}>
                    {/* Overall decision */}
                    <div>
                        <p className="text-muted" style={{ fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 700, marginBottom: '0.35rem' }}>
                            Overall Decision
                        </p>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                            <span style={{ fontSize: '2rem' }}>{status.icon}</span>
                            <div>
                                <div style={{ fontSize: '1.5rem', fontWeight: 800, fontFamily: 'var(--font-heading)', color: status.color }}>
                                    {status.label}
                                </div>
                                {statusReason && (
                                    <div style={{
                                        fontSize: '0.75rem',
                                        color: result.overall_status === 'APPROVED' ? 'var(--success)' : status.color,
                                        marginTop: '0.2rem',
                                        maxWidth: '320px',
                                        opacity: 0.85
                                    }}>
                                        {statusReason}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* KPI trio */}
                    <div style={{ display: 'flex', gap: '2.5rem', alignItems: 'center' }}>
                        {/* Overall Quality Score — primary KPI */}
                        <div style={{ textAlign: 'center' }}>
                            <div style={{
                                fontSize: '2.5rem', fontWeight: 900,
                                fontFamily: 'var(--font-heading)',
                                color: qualityColor,
                                lineHeight: 1,
                            }}>
                                {avgQuality}
                            </div>
                            <div style={{ fontSize: '0.65rem', color: 'var(--text-dim)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', marginTop: '0.25rem' }}>
                                Overall Quality
                            </div>
                            <div style={{ fontSize: '0.6rem', color: 'var(--text-muted)', marginTop: '0.1rem' }}>
                                out of 100
                            </div>
                        </div>

                        <div style={{ width: '1px', height: '48px', background: 'rgba(255,255,255,0.08)' }} />

                        {/* Mandatory */}
                        <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '1.75rem', fontWeight: 800, fontFamily: 'var(--font-heading)', color: mandatoryColor }}>
                                {mandatoryPassed}/{mandatoryTotal}
                            </div>
                            <div style={{ fontSize: '0.65rem', color: 'var(--text-dim)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', marginTop: '0.25rem' }}>
                                Mandatory
                            </div>
                        </div>

                        {/* Quality criteria count */}
                        <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '1.75rem', fontWeight: 800, fontFamily: 'var(--font-heading)', color: 'var(--text-dim)' }}>
                                {scoredFindings.length}
                            </div>
                            <div style={{ fontSize: '0.65rem', color: 'var(--text-dim)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', marginTop: '0.25rem' }}>
                                Evaluated
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* ═══ Section 1: Mandatory Compliance ═══ */}
            <div className="card mb-4">
                <div className="card-header">
                    <div className="card-icon-wrapper">📋</div>
                    <div>
                        <h3 className="card-title">Section 1: Mandatory Compliance</h3>
                        <p className="text-muted" style={{ fontSize: '0.78rem' }}>
                            {mandatoryPassed}/{mandatoryTotal} passed — {mandatoryPassed === mandatoryTotal ? 'All mandatory checks cleared' : 'Issues require resolution'}
                        </p>
                    </div>
                </div>
                <div className="criteria-list">
                    {mandatoryFindings.map((finding, index) => (
                        <div
                            key={index}
                            className="criteria-item"
                            style={{
                                background: finding.status === 'PASS' ? 'rgba(52,211,153,0.04)' : 'rgba(248,113,113,0.04)',
                                border: `1px solid ${finding.status === 'PASS' ? 'rgba(52,211,153,0.15)' : 'rgba(248,113,113,0.15)'}`,
                                borderRadius: '12px',
                                padding: '1rem 1.15rem'
                            }}
                        >
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                                    <span style={{ fontSize: '1.2rem' }}>{finding.status === 'PASS' ? '✅' : '❌'}</span>
                                    <span style={{ fontWeight: 600, color: '#fff', fontSize: '0.9rem' }}>
                                        {MANDATORY_LABELS[finding.criterion] || finding.criterion}
                                    </span>
                                </div>
                                <div className={`badge ${finding.status === 'PASS' ? 'badge-success' : 'badge-danger'}`}
                                     style={{
                                         background: finding.status === 'PASS' ? 'rgba(52,211,153,0.15)' : 'rgba(248,113,113,0.15)',
                                         color: finding.status === 'PASS' ? 'var(--success)' : 'var(--danger)',
                                         fontWeight: 700,
                                         fontSize: '0.7rem',
                                         padding: '0.25rem 0.75rem',
                                         borderRadius: '6px',
                                         textTransform: 'uppercase',
                                         letterSpacing: '0.05em'
                                     }}>
                                    {finding.status}
                                </div>
                            </div>

                            {/* Show remarks */}
                            {finding.remarks && (
                                <p style={{
                                    fontSize: '0.82rem',
                                    color: finding.status === 'PASS' ? 'var(--text-dim)' : 'var(--text-secondary)',
                                    marginTop: '0.5rem',
                                    paddingLeft: '1.8rem'
                                }}>
                                    {finding.remarks}
                                </p>
                            )}

                            {/* Show suggestion panel for failures */}
                            {finding.status === 'FAIL' && finding.suggestion && (
                                <div style={{
                                    marginTop: '0.75rem',
                                    padding: '0.75rem',
                                    background: 'rgba(248,113,113,0.1)',
                                    borderLeft: '3px solid var(--danger)',
                                    borderRadius: '4px'
                                }}>
                                    <h4 style={{ fontSize: '0.75rem', color: 'var(--danger)', margin: '0 0 0.35rem 0', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                                        Issues Detected
                                    </h4>
                                    <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0 }}>
                                        {finding.suggestion}
                                    </p>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </div>

            {/* ═══ Section 2: Quality Scores ═══ */}
            <div className="card mb-4">
                <div className="card-header">
                    <div className="card-icon-wrapper">📊</div>
                    <div>
                        <h3 className="card-title">Section 2: Quality Scores</h3>
                        <p className="text-muted" style={{ fontSize: '0.78rem' }}>
                            Weighted average: {avgQuality}/100 — {qualityFindings.length} criteria
                        </p>
                    </div>
                </div>
                <div className="criteria-list">
                    {qualityFindings.map((finding, index) => {
                        const isNA = finding.score == null
                        const score = isNA ? null : finding.score
                        const scoreColor = isNA ? 'var(--text-dim)' :
                            score >= 90 ? 'var(--success)' :
                            score >= 70 ? '#3b82f6' :
                            score >= 50 ? 'var(--warning)' : 'var(--danger)'
                        const scoreLabel = isNA ? 'N/A' :
                            score >= 90 ? 'Excellent' :
                            score >= 70 ? 'Good' :
                            score >= 50 ? 'Needs Improvement' : 'Poor'

                        return (
                            <div
                                key={index}
                                className="criteria-item"
                                style={{
                                    background: 'rgba(255,255,255,0.02)',
                                    border: '1px solid var(--border-light)',
                                    borderRadius: '12px',
                                    padding: '1rem 1.15rem'
                                }}
                            >
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                                        <span style={{ fontSize: '1.2rem' }}>
                                            {isNA ? '⚪' : score >= 90 ? '🟢' : score >= 70 ? '🔵' : score >= 50 ? '🟡' : '🔴'}
                                        </span>
                                        <div>
                                            <span style={{ fontWeight: 600, color: '#fff', fontSize: '0.9rem' }}>
                                                {QUALITY_LABELS[finding.criterion] || finding.criterion}
                                            </span>
                                            {/* Weight pill */}
                                            {WEIGHTS[finding.criterion] && (
                                                <span style={{
                                                    marginLeft: '0.5rem',
                                                    fontSize: '0.62rem',
                                                    fontWeight: 700,
                                                    color: 'var(--text-dim)',
                                                    background: 'rgba(255,255,255,0.06)',
                                                    border: '1px solid rgba(255,255,255,0.1)',
                                                    borderRadius: '100px',
                                                    padding: '1px 6px',
                                                    letterSpacing: '0.04em'
                                                }}>
                                                    {Math.round(WEIGHTS[finding.criterion] * 100)}% weight
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                        {/* Confidence badge */}
                                        {(() => {
                                            const conf = finding.confidence ?? 1
                                            const confLabel = conf >= 0.80 ? 'High' : conf >= 0.60 ? 'Medium' : 'Low'
                                            const confColor = conf >= 0.80 ? 'var(--success)' : conf >= 0.60 ? 'var(--warning)' : 'var(--danger)'
                                            return (
                                                <span style={{
                                                    fontSize: '0.6rem', fontWeight: 700,
                                                    color: confColor,
                                                    background: `${confColor}18`,
                                                    border: `1px solid ${confColor}44`,
                                                    borderRadius: '100px',
                                                    padding: '2px 7px',
                                                    letterSpacing: '0.05em',
                                                    textTransform: 'uppercase'
                                                }}>
                                                    {confLabel} confidence
                                                </span>
                                            )
                                        })()}
                                        <span style={{
                                            fontSize: '0.65rem', fontWeight: 600, color: scoreColor,
                                            textTransform: 'uppercase', letterSpacing: '0.03em'
                                        }}>
                                            {scoreLabel}
                                        </span>
                                        <span style={{
                                            fontSize: '1.1rem', fontWeight: 800, color: scoreColor,
                                            fontFamily: 'var(--font-heading)', minWidth: '42px', textAlign: 'right'
                                        }}>
                                            {isNA ? '—' : score}
                                        </span>
                                    </div>
                                </div>

                                {isNA ? (
                                    <div style={{ marginTop: '0.4rem' }}>
                                        <div style={{
                                            height: '6px', background: 'rgba(255,255,255,0.04)',
                                            borderRadius: '100px'
                                        }} />
                                        <p style={{ fontSize: '0.78rem', color: 'var(--text-dim)', marginTop: '0.4rem', fontStyle: 'italic' }}>
                                            {finding.remarks}
                                        </p>
                                    </div>
                                ) : (
                                    <ScoreBar value={score} />
                                )}

                                {/* Show suggestion for scores below 70 (skip N/A) */}
                                {!isNA && score < 70 && finding.suggestion && (
                                    <div style={{
                                        marginTop: '0.75rem',
                                        padding: '0.75rem',
                                        background: score < 50 ? 'rgba(248,113,113,0.1)' : 'rgba(251,191,36,0.1)',
                                        borderLeft: `3px solid ${score < 50 ? 'var(--danger)' : 'var(--warning)'}`,
                                        borderRadius: '4px'
                                    }}>
                                        <h4 style={{
                                            fontSize: '0.75rem',
                                            color: score < 50 ? 'var(--danger)' : 'var(--warning)',
                                            margin: '0 0 0.35rem 0',
                                            textTransform: 'uppercase',
                                            letterSpacing: '0.05em'
                                        }}>
                                            {score < 50 ? 'Critical Issues' : 'Recommendations'}
                                        </h4>
                                        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0 }}>
                                            {finding.suggestion}
                                        </p>
                                    </div>
                                )}
                                {!isNA && score >= 70 && finding.suggestion && (
                                    <p className="text-muted" style={{ fontSize: '0.82rem', marginTop: '0.5rem' }}>
                                        <span style={{ color: 'var(--primary)', fontWeight: 600 }}>💡</span> {finding.suggestion}
                                    </p>
                                )}

                                <ImprovementPanel finding={finding} isReadOnly={isReadOnly} />
                            </div>
                        )
                    })}
                </div>
            </div>

            {/* Charts */}
            <div className="grid grid-2 mb-4">
                <div className="card">
                    <div className="card-header">
                        <div className="card-icon-wrapper">🧠</div>
                        <h3 className="card-title">Taxonomy Distribution</h3>
                    </div>
                    <BloomsChart data={result.blooms_distribution} />
                </div>

                <div className="card">
                    <div className="card-header">
                        <div className="card-icon-wrapper">📊</div>
                        <h3 className="card-title">Syllabus Coverage</h3>
                    </div>
                    <SyllabusHeatmap data={result.syllabus_coverage} />
                </div>
            </div>

            {/* CO Table */}
            <div className="card">
                <div className="card-header">
                    <div className="card-icon-wrapper">🎯</div>
                    <h3 className="card-title">Question Mapping</h3>
                </div>
                <COTable data={result.co_mapping} />
            </div>
        </div>
    )
}
