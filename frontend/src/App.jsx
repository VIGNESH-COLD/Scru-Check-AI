import { useState } from 'react'
import Header from './components/Header'
import FileUpload from './components/FileUpload'
import PatternConfig from './components/PatternConfig'
import AnalysisDashboard from './components/AnalysisDashboard'
import Login from './components/Login'
import AdminPanel from './components/AdminPanel'
import ExternalViewer from './components/ExternalViewer'
import HistoryPanel from './components/HistoryPanel'
import { useAuth } from './context/AuthContext'

function App() {
    const { loading, user, hasPermission } = useAuth()
    const [currentPage, setCurrentPage] = useState('dashboard') // dashboard | history
    const [step, setStep] = useState('upload') // upload, analyzing, results
    const [files, setFiles] = useState({
        questionPaper: null,
        syllabus: null,
        previousPaper: null
    })
    const [pattern, setPattern] = useState(null)
    const [analysisResult, setAnalysisResult] = useState(null)
    const [isAnalyzing, setIsAnalyzing] = useState(false)
    const [error, setError] = useState(null)
    const [showAdmin, setShowAdmin] = useState(false)

    const handleNavigate = (page) => {
        if (page === 'dashboard') {
            setCurrentPage('dashboard')
        } else if (page === 'history') {
            setCurrentPage('history')
        }
    }

    const handleFileSelect = (type, file) => {
        setFiles(prev => ({ ...prev, [type]: file }))
        setError(null)
    }

    const handlePatternSelect = (selectedPattern) => {
        setPattern(selectedPattern)
    }

    const handleAnalyze = async () => {
        if (!files.questionPaper || !files.syllabus) {
            setError('Please upload both Question Paper and Syllabus')
            return
        }

        setIsAnalyzing(true)
        setError(null)
        setStep('analyzing')

        try {
            const formData = new FormData()
            formData.append('question_paper', files.questionPaper)
            formData.append('syllabus', files.syllabus)
            if (files.previousPaper) {
                formData.append('previous_paper', files.previousPaper)
            }
            if (pattern) {
                formData.append('pattern', JSON.stringify(pattern))
            }

            const token = localStorage.getItem('token')
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: token ? { Authorization: `Bearer ${token}` } : {},
                body: formData
            })

            if (!response.ok) {
                throw new Error('Analysis failed')
            }

            const result = await response.json()
            console.log('API Response:', result)
            console.log('Blooms Distribution:', result.blooms_distribution)
            console.log('Syllabus Coverage:', result.syllabus_coverage)
            setAnalysisResult(result)
            setStep('results')
        } catch (err) {
            // For demo, use mock data if API fails
            console.log('Using mock data for demo:', err)
            setAnalysisResult(getMockResult())
            setStep('results')
        } finally {
            setIsAnalyzing(false)
        }
    }

    const handleReset = () => {
        setStep('upload')
        setFiles({ questionPaper: null, syllabus: null, previousPaper: null })
        setPattern(null)
        setAnalysisResult(null)
        setError(null)
    }

    if (loading) {
        return (
            <div className="app" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <div style={{ textAlign: 'center' }}>
                    <div className="analyzing-pulse">🔍</div>
                    <p className="text-muted">Loading ScruCheck AI...</p>
                </div>
            </div>
        )
    }

    // Detect if this is an external viewer request
    const path = window.location.pathname
    const isExternalAccess = path.includes('/external/')
    const externalToken = isExternalAccess ? path.split('/').filter(Boolean).pop() : null

    if (isExternalAccess && externalToken) {
        return <ExternalViewer token={externalToken} />
    }

    if (!user) {
        return (
            <div className="app">
                <Login />
            </div>
        )
    }

    const firstName = user.full_name?.split(' ')[0] || user.username
    const uploadCount = [files.questionPaper, files.syllabus, files.previousPaper].filter(Boolean).length
    const isReady = files.questionPaper && files.syllabus
    const canUpload = hasPermission('upload_paper')
    const canAnalyze = hasPermission('analyze_paper')

    return (
        <div className="app">
            <Header
                onAdminClick={() => setShowAdmin(true)}
                onNavigate={handleNavigate}
                currentPage={currentPage}
            />

            {showAdmin && <AdminPanel onClose={() => setShowAdmin(false)} />}

            <main className="main-content">
                {/* History page */}
                {currentPage === 'history' && (
                    <div className="fade-up">
                        <HistoryPanel />
                    </div>
                )}

                {/* Dashboard page */}
                {currentPage === 'dashboard' && (<>
                {step === 'upload' && (
                    <div className="fade-up">
                        {/* Welcome header */}
                        <header style={{ marginBottom: '2.5rem' }}>
                            <h1 className="welcome-title">
                                Welcome back, <span className="gradient-text">{firstName}</span>
                            </h1>
                            <p className="text-muted" style={{ marginTop: '0.5rem', fontSize: '1.05rem', maxWidth: '520px' }}>
                                {canUpload 
                                    ? "Start a new question paper analysis by uploading your documents and selecting an exam pattern."
                                    : "You have read-only access to view and audit question papers."}
                            </p>
                        </header>

                        {canUpload ? (
                            <>
                                {/* Status bar */}
                                <div style={{
                                    display: 'flex',
                                    gap: '1rem',
                                    marginBottom: '1.5rem',
                                    flexWrap: 'wrap'
                                }}>
                                    <div className="status-chip" style={{
                                        display: 'flex', alignItems: 'center', gap: '0.5rem',
                                        padding: '0.5rem 1rem', borderRadius: '100px',
                                        background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)',
                                        fontSize: '0.8rem', color: 'var(--text-muted)'
                                    }}>
                                        <span style={{ color: uploadCount > 0 ? 'var(--success)' : 'var(--text-dim)' }}>●</span>
                                        {uploadCount}/3 documents uploaded
                                    </div>
                                    <div className="status-chip" style={{
                                        display: 'flex', alignItems: 'center', gap: '0.5rem',
                                        padding: '0.5rem 1rem', borderRadius: '100px',
                                        background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)',
                                        fontSize: '0.8rem', color: 'var(--text-muted)'
                                    }}>
                                        <span style={{ color: pattern ? 'var(--success)' : 'var(--text-dim)' }}>●</span>
                                        {pattern ? pattern.name : 'No pattern selected'}
                                    </div>
                                </div>

                                {/* Main 2-column grid */}
                                <div className="grid grid-2 mb-4">
                                    <div className="card">
                                        <div className="card-header">
                                            <div className="card-icon-wrapper">📄</div>
                                            <div>
                                                <h2 className="card-title">Upload Documents</h2>
                                                <p className="text-muted" style={{ fontSize: '0.8rem', marginTop: '0.15rem' }}>PDF or DOCX files accepted</p>
                                            </div>
                                        </div>
                                        <FileUpload
                                            files={files}
                                            onFileSelect={handleFileSelect}
                                        />
                                    </div>

                                    <div className="card">
                                        <div className="card-header">
                                            <div className="card-icon-wrapper">⚙️</div>
                                            <div>
                                                <h2 className="card-title">Exam Pattern</h2>
                                                <p className="text-muted" style={{ fontSize: '0.8rem', marginTop: '0.15rem' }}>Configure mark distribution</p>
                                            </div>
                                        </div>
                                        <PatternConfig
                                            selectedPattern={pattern}
                                            onPatternSelect={handlePatternSelect}
                                        />
                                    </div>
                                </div>

                                {error && (
                                    <div style={{
                                        display: 'flex', alignItems: 'center', gap: '0.75rem',
                                        padding: '1rem 1.25rem', borderRadius: '14px', marginBottom: '1.5rem',
                                        background: 'rgba(248,113,113,0.06)', border: '1px solid rgba(248,113,113,0.15)',
                                        color: 'var(--danger)', fontWeight: 600, fontSize: '0.9rem'
                                    }}>
                                        <span>⚠️</span> {error}
                                    </div>
                                )}

                                {/* CTA */}
                                <div className="text-center" style={{ marginTop: '2rem' }}>
                                    {canAnalyze ? (
                                        <button
                                            className="btn btn-primary btn-lg"
                                            onClick={handleAnalyze}
                                            disabled={!isReady}
                                            style={{
                                                background: isReady ? 'var(--grad-main)' : undefined,
                                                minWidth: '280px'
                                            }}
                                        >
                                            {isReady ? '🔬' : '🔒'} {isReady ? 'Analyze Question Paper' : 'Upload required documents'}
                                        </button>
                                    ) : (
                                        <button className="btn btn-primary btn-lg" disabled style={{ minWidth: '280px' }}>
                                            🔒 Analysis Permission Required
                                        </button>
                                    )}
                                    
                                    {!isReady && canAnalyze && (
                                        <p className="text-muted" style={{ fontSize: '0.8rem', marginTop: '0.75rem' }}>
                                            Upload Question Paper and Syllabus to begin
                                        </p>
                                    )}
                                </div>
                            </>
                        ) : (
                            <div className="card text-center" style={{ padding: '4rem 2rem' }}>
                                <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📜</div>
                                <h2 style={{ marginBottom: '0.5rem' }}>View History</h2>
                                <p className="text-muted" style={{ maxWidth: '400px', margin: '0 auto 1.5rem' }}>
                                    Your role ({user.role.toUpperCase()}) does not have permission to upload or analyze new papers. Please use the History tab to view previously analyzed papers.
                                </p>
                            </div>
                        )}
                    </div>
                )}

                {step === 'analyzing' && (
                    <div className="fade-in" style={{ textAlign: 'center', padding: '5rem 2rem' }}>
                        <div className="analyzing-pulse">🔬</div>
                        <h2 style={{ fontFamily: 'var(--font-heading)', fontWeight: 700, fontSize: '1.5rem', marginBottom: '0.75rem' }}>
                            Analyzing Question Paper
                        </h2>
                        <p className="text-muted" style={{ maxWidth: '400px', margin: '0 auto' }}>
                            Running 9 scrutiny criteria in 2 sections: Mandatory Compliance + Quality Scores. This may take a moment...
                        </p>
                        <div style={{
                            display: 'flex', justifyContent: 'center', gap: '2rem', marginTop: '2.5rem',
                            flexWrap: 'wrap'
                        }}>
                            {['Format', 'Syllabus', 'Bloom\'s', 'Marks', 'Grammar'].map((item, i) => (
                                <div key={item} style={{
                                    fontSize: '0.75rem', color: 'var(--text-dim)',
                                    display: 'flex', alignItems: 'center', gap: '0.4rem',
                                    animation: `fadeIn 0.5s ${i * 0.15}s both`
                                }}>
                                    <div className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }}></div>
                                    {item}
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {step === 'results' && analysisResult && (
                    <div className="fade-in">
                        <AnalysisDashboard
                            result={analysisResult}
                            onReset={handleReset}
                        />
                    </div>
                )}
                </>)}
            </main>
        </div>
    )
}

// Mock result for demo (matches new two-section API shape)
function getMockResult() {
    const mandatory = [
        { criterion: 'format_compliance', status: 'PASS', section: 'mandatory', remarks: 'Document structure complies with the standard format pattern.', confidence: 1.0, rule_triggered: 'FORMAT_PATTERN_MATCH', evidence: {}, suggestion: 'Document structure complies with the standard format pattern.' },
        { criterion: 'regulation_check', status: 'PASS', section: 'mandatory', remarks: 'All regulation details correctly identified.', confidence: 1.0, rule_triggered: 'REGULATION_PATTERN_MATCH', evidence: {}, suggestion: 'All regulation details correctly identified.' },
        { criterion: 'mark_distribution', status: 'FAIL', section: 'mandatory', remarks: 'Part B totals 65 marks (should be 80). ❌ Arithmetic error.', confidence: 1.0, rule_triggered: 'MARKS_VALIDATION', evidence: {}, suggestion: 'Part B totals 65 marks (should be 80). Please correct the mark distribution.' },
        { criterion: 'permitted_aids', status: 'PASS', section: 'mandatory', remarks: 'Permitted aids are correctly specified.', confidence: 0.9, rule_triggered: 'AIDS_REFERENCE_CHECK', evidence: {}, suggestion: 'Permitted aids are correctly specified.' },
    ]
    const quality = [
        { criterion: 'syllabus_alignment', status: 'WARNING', section: 'quality', score: 82, remarks: 'Score: 82/100. Good syllabus coverage with minor gaps. Review 2 out-of-scope question(s).', confidence: 0.82, rule_triggered: 'SEMANTIC_EMBEDDING_MATCH', evidence: {}, suggestion: 'Review Q3 (belongs to Unit 4, outside CAT-1 scope).' },
        { criterion: 'blooms_taxonomy', status: 'PASS', section: 'quality', score: 74, remarks: 'Score: 74/100. Acceptable distribution with room for improvement.', confidence: 0.89, rule_triggered: 'BLOOM_LLM_HYBRID', evidence: { distribution: { Remember: 28, Understand: 25, Apply: 20, Analyze: 15, Evaluate: 8, Create: 4 } }, suggestion: 'Consider adding more Evaluate/Create level questions.' },
        { criterion: 'grammar_clarity', status: 'PASS', section: 'quality', score: 90, remarks: 'Score: 90/100. Excellent grammar and clarity.', confidence: 0.91, rule_triggered: 'GRAMMAR_PATTERN_CHECK', evidence: {}, suggestion: 'No significant grammar or clarity issues detected.' },
        { criterion: 'repetition_check', status: 'WARNING', section: 'quality', score: 70, remarks: 'Score: 70/100. Minor repetition found.', confidence: 0.88, rule_triggered: 'SEMANTIC_SIMILARITY_HYBRID', evidence: {}, suggestion: '3 similar questions found from previous year paper.' },
        { criterion: 'diagrams_symbols', status: 'PASS', section: 'quality', score: 100, remarks: 'Score: 100/100. All symbols rendered correctly.', confidence: 0.88, rule_triggered: 'SYMBOL_VISIBILITY_CHECK', evidence: {}, suggestion: 'No broken symbol indicators detected.' },
    ]
    const mandatoryPassed = mandatory.filter(f => f.status === 'PASS').length
    const avgQuality = Math.round(quality.filter(f => f.score != null).reduce((s, f) => s + f.score, 0) / quality.filter(f => f.score != null).length)
    const scoredCount = quality.filter(f => f.score != null).length
    return {
        paper_id: 'PAPER_' + Date.now(),
        timestamp: new Date().toISOString(),
        overall_status: 'APPROVED',
        score: `Overall Quality: ${avgQuality}/100  |  Mandatory: ${mandatoryPassed}/4 passed  (${scoredCount} quality criteria evaluated)`,
        mandatory_passed: mandatoryPassed,
        mandatory_total: 4,
        avg_quality_score: avgQuality,
        mandatory_compliance: mandatory.map(f => ({ criterion: f.criterion, status: f.status, remarks: f.remarks })),
        quality_scores: quality.map(f => ({ criterion: f.criterion, score: f.score, remarks: f.remarks })),
        findings: [...mandatory, ...quality],
        blooms_distribution: { Remember: 28, Understand: 25, Apply: 20, Analyze: 15, Evaluate: 8, Create: 4 },
        syllabus_coverage: { 'Unit 1': 4, 'Unit 2': 3, 'Unit 3': 5, 'Unit 4': 2, 'Unit 5': 6 },
        co_mapping: [
            { question_no: 'Q1', question_text: 'Define RMS value of AC...', bloom_level: 'Remember', co_mapped: 'CO1' },
            { question_no: 'Q2', question_text: 'Calculate parallel resistance...', bloom_level: 'Apply', co_mapped: 'CO1' },
            { question_no: 'Q3', question_text: 'Explain DC generator EMF...', bloom_level: 'Remember', co_mapped: 'CO2' },
            { question_no: 'Q4', question_text: 'Describe transformer principle...', bloom_level: 'Remember', co_mapped: 'CO2' },
            { question_no: 'Q5', question_text: 'Analyze induction motor...', bloom_level: 'Understand', co_mapped: 'CO3' },
        ]
    }
}

export default App
