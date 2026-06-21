import { useState, useRef } from 'react'

export default function FileUpload({ files, onFileSelect }) {
    const [dragOver, setDragOver] = useState({})

    const fileInputRefs = {
        questionPaper: useRef(),
        syllabus: useRef(),
        previousPaper: useRef()
    }

    const handleDragOver = (e, type) => {
        e.preventDefault()
        setDragOver(prev => ({ ...prev, [type]: true }))
    }

    const handleDragLeave = (type) => {
        setDragOver(prev => ({ ...prev, [type]: false }))
    }

    const handleDrop = (e, type) => {
        e.preventDefault()
        setDragOver(prev => ({ ...prev, [type]: false }))

        const file = e.dataTransfer.files[0]
        if (file && isValidFile(file)) {
            onFileSelect(type, file)
        }
    }

    const handleFileChange = (e, type) => {
        const file = e.target.files[0]
        if (file && isValidFile(file)) {
            onFileSelect(type, file)
        }
    }

    const isValidFile = (file) => {
        const validTypes = ['.pdf', '.docx', '.doc']
        const extension = '.' + file.name.split('.').pop().toLowerCase()
        return validTypes.includes(extension)
    }

    const fileTypes = [
        { key: 'questionPaper', label: 'Question Paper', required: true, icon: '📝', color: '#818cf8' },
        { key: 'syllabus', label: 'Syllabus', required: true, icon: '📚', color: '#c084fc' },
        { key: 'previousPaper', label: 'Previous Paper', required: false, icon: '📋', color: '#38bdf8' }
    ]

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
            {fileTypes.map(({ key, label, required, icon, color }) => {
                const hasFile = files[key]
                const isDragging = dragOver[key]

                return (
                    <div
                        key={key}
                        className={`upload-zone ${isDragging ? 'active' : ''} ${hasFile ? 'has-file' : ''}`}
                        onDragOver={(e) => handleDragOver(e, key)}
                        onDragLeave={() => handleDragLeave(key)}
                        onDrop={(e) => handleDrop(e, key)}
                        onClick={() => fileInputRefs[key].current.click()}
                        style={{ padding: '1rem 1.25rem' }}
                    >
                        <input
                            ref={fileInputRefs[key]}
                            type="file"
                            accept=".pdf,.docx,.doc"
                            style={{ display: 'none' }}
                            onChange={(e) => handleFileChange(e, key)}
                        />

                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
                            <div style={{
                                width: '40px', height: '40px', borderRadius: '12px',
                                background: hasFile ? 'rgba(52,211,153,0.1)' : `${color}12`,
                                border: `1px solid ${hasFile ? 'rgba(52,211,153,0.2)' : color + '25'}`,
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                fontSize: '1.15rem', flexShrink: 0,
                                transition: 'all 0.3s'
                            }}>
                                {hasFile ? '✓' : icon}
                            </div>

                            <div style={{ flex: 1, minWidth: 0 }}>
                                <div style={{
                                    fontWeight: 600, fontSize: '0.88rem',
                                    color: hasFile ? 'var(--success)' : '#fff',
                                    display: 'flex', alignItems: 'center', gap: '0.35rem'
                                }}>
                                    {hasFile ? (
                                        <span style={{
                                            overflow: 'hidden', textOverflow: 'ellipsis',
                                            whiteSpace: 'nowrap', display: 'block'
                                        }}>
                                            {files[key].name}
                                        </span>
                                    ) : (
                                        <>
                                            {label}
                                            {required && <span style={{ color: 'var(--danger)', fontSize: '0.75rem' }}>*</span>}
                                        </>
                                    )}
                                </div>
                                <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', marginTop: '0.1rem' }}>
                                    {hasFile
                                        ? `${(files[key].size / 1024).toFixed(1)} KB • Click to change`
                                        : 'Drag & drop or click to upload'
                                    }
                                </div>
                            </div>

                            {!hasFile && (
                                <div style={{
                                    padding: '0.35rem 0.75rem', fontSize: '0.7rem',
                                    borderRadius: '8px', fontWeight: 600,
                                    background: 'rgba(255,255,255,0.05)',
                                    border: '1px solid rgba(255,255,255,0.08)',
                                    color: 'var(--text-muted)', whiteSpace: 'nowrap',
                                    fontFamily: 'var(--font-heading)'
                                }}>
                                    Browse
                                </div>
                            )}
                        </div>
                    </div>
                )
            })}
        </div>
    )
}
