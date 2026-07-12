const BLOOM_COLORS = {
    'Remember': '#ef4444',
    'Understand': '#f97316',
    'Apply': '#eab308',
    'Analyze': '#22c55e',
    'Evaluate': '#3b82f6',
    'Create': '#8b5cf6'
}

// Derive unit label from CO string (e.g. CO3 -> Unit 3)
function coToUnit(co) {
    const num = parseInt((co || '').replace(/\D/g, ''))
    return isNaN(num) ? '' : `Unit ${num}`
}

export default function COTable({ data }) {
    if (!data || data.length === 0) {
        return <p className="text-muted">No CO mapping data available</p>
    }

    // Build summary from actual data — sorted by CO number
    const summary = data.reduce((acc, row) => {
        const co = row.co_mapped || 'Unknown'
        acc[co] = (acc[co] || 0) + 1
        return acc
    }, {})

    const sortedSummary = Object.entries(summary).sort((a, b) => {
        const numA = parseInt(a[0].replace(/\D/g, '')) || 999
        const numB = parseInt(b[0].replace(/\D/g, '')) || 999
        return numA - numB
    })

    return (
        <div className="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Question</th>
                        <th>Question Text</th>
                        <th>Bloom's Level</th>
                        <th>Unit</th>
                        <th>CO Mapped</th>
                    </tr>
                </thead>
                <tbody>
                    {data.map((row, index) => (
                        <tr key={index}>
                            <td style={{ fontWeight: 600 }}>{row.question_no}</td>
                            <td>
                                {row.question_text}
                            </td>
                            <td>
                                <span
                                    className="badge"
                                    style={{
                                        background: `${BLOOM_COLORS[row.bloom_level] || '#6b7280'}20`,
                                        color: BLOOM_COLORS[row.bloom_level] || '#6b7280'
                                    }}
                                >
                                    {row.bloom_level || '—'}
                                </span>
                            </td>
                            <td style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
                                {coToUnit(row.co_mapped)}
                            </td>
                            <td>
                                <span className="badge badge-info">{row.co_mapped || '—'}</span>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>

            {/* Summary — driven purely by actual data, sorted by CO number */}
            <div className="mt-3 flex gap-3" style={{ flexWrap: 'wrap' }}>
                {sortedSummary.map(([co, count]) => (
                    <div key={co} className="flex items-center gap-1" style={{ fontSize: '0.875rem' }}>
                        <span className="badge badge-info">{co}</span>
                        <span className="text-muted">{count} question{count !== 1 ? 's' : ''}</span>
                    </div>
                ))}
            </div>
        </div>
    )
}
