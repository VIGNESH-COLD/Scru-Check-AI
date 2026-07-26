import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'

const BLOOM_COLORS = {
    'Remember': '#ef4444',
    'Understand': '#f97316',
    'Apply': '#eab308',
    'Analyze': '#22c55e',
    'Evaluate': '#3b82f6',
    'Create': '#8b5cf6'
}

// Custom tooltip — uses CSS variables so it looks correct in both dark and light mode
function CustomTooltip({ active, payload, total }) {
    if (!active || !payload || !payload.length) return null
    const item = payload[0].payload
    const pct = total > 0 ? ((item.value / total) * 100).toFixed(1) : '0.0'
    return (
        <div style={{
            background: 'var(--bg-elevated)',
            backdropFilter: 'blur(16px)',
            border: `1px solid ${item.color}`,
            borderRadius: '10px',
            padding: '10px 14px',
            boxShadow: `0 4px 20px rgba(0,0,0,0.2), 0 0 0 1px ${item.color}22`,
            minWidth: '140px'
        }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: item.color, flexShrink: 0 }} />
                <span style={{ color: 'var(--text-main)', fontWeight: 700, fontSize: '0.85rem' }}>{item.name}</span>
            </div>
            <div style={{ color: item.color, fontSize: '1.1rem', fontWeight: 800, lineHeight: 1 }}>
                {item.value} <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)', fontWeight: 500 }}>questions</span>
            </div>
            <div style={{ color: 'var(--text-dim)', fontSize: '0.75rem', marginTop: '3px' }}>{pct}% of total</div>
        </div>
    )
}

export default function BloomsChart({ data }) {
    // Null safety: use default empty object if data is undefined
    const safeData = data || {}

    const chartData = Object.entries(safeData).map(([name, value]) => ({
        name,
        value: value || 0,
        color: BLOOM_COLORS[name] || '#6b7280'
    }))

    const total = chartData.reduce((sum, item) => sum + item.value, 0)

    const renderCustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, name, percent }) => {
        if (percent < 0.05) return null  // skip tiny slices
        const RADIAN = Math.PI / 180
        const radius = innerRadius + (outerRadius - innerRadius) * 0.55
        const x = cx + radius * Math.cos(-midAngle * RADIAN)
        const y = cy + radius * Math.sin(-midAngle * RADIAN)
        return (
            <text x={x} y={y} fill="#ffffff" textAnchor="middle" dominantBaseline="central"
                style={{ fontSize: '0.65rem', fontWeight: 700, pointerEvents: 'none', textShadow: '0 1px 3px rgba(0,0,0,0.8)' }}>
                {`${(percent * 100).toFixed(0)}%`}
            </text>
        )
    }

    return (
        <div>
            <div className="chart-container">
                <ResponsiveContainer width="100%" height={280}>
                    <PieChart>
                        <Pie
                            data={chartData}
                            cx="50%"
                            cy="50%"
                            innerRadius={60}
                            outerRadius={100}
                            paddingAngle={2}
                            dataKey="value"
                            labelLine={false}
                            label={renderCustomLabel}
                        >
                            {chartData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.color} stroke="rgba(0,0,0,0.2)" strokeWidth={1} />
                            ))}
                        </Pie>
                        <Tooltip
                            content={<CustomTooltip total={total} />}
                            cursor={false}
                        />
                    </PieChart>
                </ResponsiveContainer>
            </div>

            {/* Legend */}
            <div className="flex gap-2" style={{ flexWrap: 'wrap', justifyContent: 'center', marginTop: 'var(--space-md)' }}>
                {chartData.map((item) => (
                    <div key={item.name} className="flex items-center gap-1" style={{ fontSize: '0.75rem' }}>
                        <div style={{
                            width: '12px',
                            height: '12px',
                            background: item.color,
                            borderRadius: '2px'
                        }}></div>
                        <span className="text-muted">{item.name}</span>
                        <span className="text-muted">({item.value})</span>
                    </div>
                ))}
            </div>


            {/* Target group breakdown */}
            {total > 0 && (() => {
                const lowerVal = (safeData['Remember'] || 0) + (safeData['Understand'] || 0)
                const applyVal  = safeData['Apply'] || 0
                const higherVal = (safeData['Analyze'] || 0) + (safeData['Evaluate'] || 0) + (safeData['Create'] || 0)
                const lowerPct  = Math.round(lowerVal  / total * 100)
                const applyPct  = Math.round(applyVal  / total * 100)
                const higherPct = Math.round(higherVal / total * 100)

                const groups = [
                    { label: 'Lower-order (R+U)', actual: lowerPct,  target: 30, color: '#f97316' },
                    { label: 'Apply',              actual: applyPct,  target: 30, color: '#eab308' },
                    { label: 'Higher-order (A+E+C)', actual: higherPct, target: 40, color: '#22c55e' },
                ]

                return (
                    <div style={{ marginTop: '1rem', display: 'flex', flexDirection: 'column', gap: '0.55rem' }}>
                        <p style={{ fontSize: '0.65rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.25rem' }}>
                            Target Distribution
                        </p>
                        {groups.map(g => {
                            const diff = g.actual - g.target
                            const barColor = Math.abs(diff) <= 10 ? g.color : Math.abs(diff) <= 20 ? 'var(--warning)' : 'var(--danger)'
                            return (
                                <div key={g.label}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '3px' }}>
                                        <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{g.label}</span>
                                        <span style={{ fontSize: '0.72rem', fontWeight: 700, color: barColor }}>
                                            {g.actual}%
                                            <span style={{ color: 'var(--text-dim)', fontWeight: 400, marginLeft: '4px' }}>
                                                (target {g.target}%)
                                            </span>
                                            <span style={{ marginLeft: '6px', color: barColor }}>
                                                {diff === 0 ? '✓' : diff > 0 ? `+${diff}` : `${diff}`}
                                            </span>
                                        </span>
                                    </div>
                                    <div style={{ height: '5px', background: 'var(--border-light)', borderRadius: '100px', overflow: 'hidden' }}>
                                        <div style={{ width: `${g.actual}%`, height: '100%', background: barColor, borderRadius: '100px', transition: 'width 0.8s ease' }} />
                                    </div>
                                </div>
                            )
                        })}
                        <p style={{ fontSize: '0.65rem', color: 'var(--text-dim)', marginTop: '0.25rem', textAlign: 'center' }}>
                            Total classified: {total} questions
                        </p>
                    </div>
                )
            })()}
        </div>
    )
}
