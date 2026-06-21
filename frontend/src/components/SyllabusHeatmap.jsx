import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell, Tooltip } from 'recharts'

export default function SyllabusHeatmap({ data }) {
    // Debug: Log the data received
    console.log('SyllabusHeatmap received data:', data)

    // Null safety: use default empty object if data is undefined
    const safeData = data || {}

    // Sort units numerically (Unit 1, Unit 2, ... Unit 5)
    const sortedEntries = Object.entries(safeData).sort((a, b) => {
        const numA = parseInt(a[0].replace(/\D/g, '')) || 0
        const numB = parseInt(b[0].replace(/\D/g, '')) || 0
        return numA - numB
    })

    const chartData = sortedEntries.map(([name, value]) => ({
        name,
        value: value || 0,
        // Color based on coverage
        color: value === 0 ? '#ef4444' : value <= 2 ? '#f97316' : '#22c55e'
    }))

    const total = chartData.reduce((sum, item) => sum + item.value, 0)
    const maxValue = chartData.length > 0 ? Math.max(...chartData.map(d => d.value), 1) : 1

    return (
        <div>
            <div className="chart-container">
                <ResponsiveContainer width="100%" height={250}>
                    <BarChart data={chartData} layout="vertical" margin={{ left: 10, right: 30 }}>
                        <XAxis type="number" domain={[0, maxValue + 2]} />
                        <YAxis
                            type="category"
                            dataKey="name"
                            tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
                        />
                        <Tooltip
                            contentStyle={{
                                background: 'var(--bg-card)',
                                border: '1px solid var(--border)',
                                borderRadius: 'var(--radius-md)'
                            }}
                            formatter={(value) => [`${value} questions`, 'Count']}
                        />
                        <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                            {chartData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>

            {/* Coverage Stats */}
            <div className="mt-3">
                <div className="flex justify-between mb-2">
                    <span className="text-secondary" style={{ fontSize: '0.875rem' }}>Coverage Distribution</span>
                    <span className="text-muted" style={{ fontSize: '0.875rem' }}>Total: {total} questions</span>
                </div>

                {chartData.map((item) => (
                    <div key={item.name} className="flex items-center gap-2 mb-1">
                        <span className="text-secondary" style={{ width: '60px', fontSize: '0.875rem' }}>{item.name}</span>
                        <div className="progress-bar" style={{ flex: 1 }}>
                            <div
                                className="progress-fill"
                                style={{
                                    width: `${(item.value / maxValue) * 100}%`,
                                    background: item.color
                                }}
                            ></div>
                        </div>
                        <span className={`${item.value === 0 ? 'text-danger' : item.value <= 2 ? 'text-warning' : 'text-success'}`} style={{ width: '80px', fontSize: '0.875rem', textAlign: 'right' }}>
                            {item.value} ({total > 0 ? ((item.value / total) * 100).toFixed(0) : 0}%)
                        </span>
                    </div>
                ))}
            </div>

            {/* Alerts */}
            {chartData.some(d => d.value === 0) && (
                <div className="mt-2" style={{ padding: 'var(--space-sm)', background: 'rgba(239, 68, 68, 0.1)', borderRadius: 'var(--radius-md)', fontSize: '0.875rem' }}>
                    ⚠️ <span className="text-danger">Warning:</span> Some units have no questions!
                </div>
            )}
            {chartData.length === 0 && (
                <div className="mt-2" style={{ padding: 'var(--space-sm)', background: 'rgba(129,140,248,0.05)', borderRadius: 'var(--radius-md)', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
                    No coverage data available yet.
                </div>
            )}
        </div>
    )
}
