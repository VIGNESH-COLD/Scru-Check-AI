import { useState, useEffect } from 'react'

export default function PatternConfig({ selectedPattern, onPatternSelect }) {
    const [showCustom, setShowCustom] = useState(false)
    const [activeCategory, setActiveCategory] = useState('CAT1')
    const [patterns, setPatterns] = useState({
        CAT1: [
            { name: 'CAT-1 (Unit I & II) - Standard', exam_type: 'CAT1', sections: [{ questions: 10, marks_per_question: 2 }, { questions: 2, marks_per_question: 15 }], total_marks: 50 },
            { name: 'CAT-1 (Unit I & II) - Alternate', exam_type: 'CAT1', sections: [{ questions: 12, marks_per_question: 2 }, { questions: 2, marks_per_question: 13 }], total_marks: 50 }
        ],
        CAT2: [
            { name: 'CAT-2 (Unit III) - Standard', exam_type: 'CAT2', sections: [{ questions: 5, marks_per_question: 2 }, { questions: 1, marks_per_question: 15 }], total_marks: 25 }
        ],
        CAT3: [
            { name: 'CAT-3 (Unit IV & V) - Standard', exam_type: 'CAT3', sections: [{ questions: 10, marks_per_question: 2 }, { questions: 2, marks_per_question: 15 }], total_marks: 50 }
        ],
        University: [
            { name: 'University End Sem - Standard', exam_type: 'University', sections: [{ questions: 10, marks_per_question: 2 }, { questions: 5, marks_per_question: 16 }], total_marks: 100 }
        ]
    })
    const [loading, setLoading] = useState(false)
    const [customSections, setCustomSections] = useState([
        { name: 'Part A', questions: 10, marks_per_question: 2 }
    ])

    // Load patterns from backend - Using local fallbacks for demo
    useEffect(() => {
        fetchPatterns()
    }, [])

    const fetchPatterns = async () => {
        try {
            const response = await fetch('/api/patterns')
            if (response.ok) {
                const data = await response.json()
                if (data.categories) {
                    setPatterns(data.categories)
                }
            }
        } catch (error) {
            console.error('Error loading patterns:', error)
        } finally {
            setLoading(false)
        }
    }

    const handlePresetSelect = (pattern) => {
        onPatternSelect(pattern)
        setShowCustom(false)
    }

    const addSection = () => {
        const nextLetter = String.fromCharCode(65 + customSections.length)
        setCustomSections([...customSections, {
            name: `Part ${nextLetter}`,
            questions: 5,
            marks_per_question: 10
        }])
    }

    const removeSection = (index) => {
        if (customSections.length > 1) {
            setCustomSections(customSections.filter((_, i) => i !== index))
        }
    }

    const updateSection = (index, field, value) => {
        const updated = [...customSections]
        updated[index][field] = field === 'name' ? value : parseInt(value) || 0
        setCustomSections(updated)
    }

    const applyCustomPattern = () => {
        const totalMarks = customSections.reduce(
            (sum, s) => sum + (s.questions * s.marks_per_question), 0
        )
        onPatternSelect({
            name: 'Custom',
            sections: customSections,
            total_marks: totalMarks,
            time_minutes: 180
        })
    }

    const categories = [
        { id: 'CAT1', label: 'CAT-1' },
        { id: 'CAT2', label: 'CAT-2' },
        { id: 'CAT3', label: 'CAT-3' },
        { id: 'University', label: 'University' }
    ]

    return (
        <div className="flex flex-col h-full">
            <p className="text-muted mb-4" style={{ fontSize: '0.9rem' }}>Select the exam pattern for format and mark validation.</p>

            {/* Category Tabs */}
            <div className="tabs-container">
                {categories.map((cat) => (
                    <div
                        key={cat.id}
                        className={`tab-item ${activeCategory === cat.id ? 'active' : ''}`}
                        onClick={() => setActiveCategory(cat.id)}
                    >
                        {cat.label}
                    </div>
                ))}
            </div>

            {/* Patterns for Selected Category */}
            <div className="flex flex-col gap-2 mb-4" style={{ flex: 1 }}>
                {loading ? (
                    <div className="premium-loader"></div>
                ) : (
                    <>
                        {patterns[activeCategory]?.map((pattern, index) => (
                            <div
                                key={`${pattern.name}-${index}`}
                                className={`option-card ${selectedPattern?.name === pattern.name ? 'selected' : ''}`}
                                onClick={() => handlePresetSelect(pattern)}
                            >
                                <div className="flex flex-col">
                                    <span className="option-name">{pattern.name}</span>
                                    <span className="option-meta">
                                        {pattern.sections.map(s => `${s.questions}×${s.marks_per_question}`).join(', ')}
                                    </span>
                                </div>
                                <div className="badge badge-info" style={{ textTransform: 'none' }}>
                                    {pattern.total_marks} Marks
                                </div>
                            </div>
                        ))}

                        {patterns[activeCategory]?.length === 0 && (
                            <div className="text-muted text-center p-4">
                                No preset patterns found for this category.
                            </div>
                        )}
                    </>
                )}
            </div>

            {/* Custom Pattern Button */}
            <button
                className={`btn ${showCustom ? 'btn-primary' : 'btn-glass'} mb-2`}
                style={{ width: '100%', gap: '0.5rem' }}
                onClick={() => setShowCustom(!showCustom)}
            >
                <span>⚙️</span> {showCustom ? 'Close Builder' : 'Build Custom Pattern'}
            </button>

            {/* Custom Pattern Builder */}
            {showCustom && (
                <div className="card fade-up" style={{ background: 'rgba(0,0,0,0.3)', padding: '1rem', marginTop: '0.5rem', border: '1px solid var(--primary-glow)' }}>
                    <div className="flex justify-between items-center mb-3">
                        <h4 style={{ fontSize: '0.9rem', color: '#fff' }}>Custom Pattern Configuration</h4>
                        <button className="btn btn-glass" style={{ padding: '0.2rem 0.5rem', fontSize: '0.7rem' }} onClick={addSection}>+ Add</button>
                    </div>

                    <div className="flex flex-col gap-2 max-h-40 overflow-y-auto pr-2">
                        {customSections.map((section, index) => (
                            <div key={index} className="flex gap-2 items-center">
                                <input
                                    type="text"
                                    value={section.name}
                                    onChange={(e) => updateSection(index, 'name', e.target.value)}
                                    className="btn-glass"
                                    style={{ flex: 1, padding: '0.4rem', borderRadius: '6px', fontSize: '0.8rem', border: '1px solid rgba(255,255,255,0.1)' }}
                                />
                                <input
                                    type="number"
                                    value={section.questions}
                                    onChange={(e) => updateSection(index, 'questions', e.target.value)}
                                    className="btn-glass"
                                    style={{ width: '45px', padding: '0.4rem', borderRadius: '6px', fontSize: '0.8rem', border: '1px solid rgba(255,255,255,0.1)' }}
                                />
                                <span style={{ color: 'var(--text-dim)' }}>×</span>
                                <input
                                    type="number"
                                    value={section.marks_per_question}
                                    onChange={(e) => updateSection(index, 'marks_per_question', e.target.value)}
                                    className="btn-glass"
                                    style={{ width: '45px', padding: '0.4rem', borderRadius: '6px', fontSize: '0.8rem', border: '1px solid rgba(255,255,255,0.1)' }}
                                />
                                {customSections.length > 1 && (
                                    <button onClick={() => removeSection(index)} style={{ background: 'transparent', border: 'none', color: 'var(--danger)', cursor: 'pointer' }}>×</button>
                                )}
                            </div>
                        ))}
                    </div>

                    <div className="mt-4 flex items-center justify-between">
                        <div className="text-muted" style={{ fontSize: '0.8rem' }}>
                            Total: <span style={{ color: '#fff', fontWeight: 600 }}>{customSections.reduce((sum, s) => sum + s.questions * s.marks_per_question, 0)} marks</span>
                        </div>
                        <button className="btn btn-primary" style={{ padding: '0.4rem 1rem', fontSize: '0.8rem' }} onClick={applyCustomPattern}>
                            Apply Custom
                        </button>
                    </div>
                </div>
            )}
        </div>
    )
}
