import { useEffect, useMemo, useState } from 'react'
import { fetchCategories, fetchTickets } from './api'
import type { Ticket } from './types'

export default function App() {
  const [categories, setCategories] = useState<{key: string; label: string}[]>([])
  const [selected, setSelected] = useState<string>('')
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [loading, setLoading] = useState<boolean>(true)

  useEffect(() => {
    ;(async () => {
      const cats = await fetchCategories()
      setCategories(cats)
      setSelected(cats[0]?.key ?? '')
    })()
  }, [])

  useEffect(() => {
    if (!selected) return
    setLoading(true)
    ;(async () => {
      const items = await fetchTickets(selected)
      setTickets(items)
      setLoading(false)
    })()
  }, [selected])

  const grouped = useMemo(() => {
    const byPriority: Record<string, Ticket[]> = {}
    for (const t of tickets) {
      ;(byPriority[t.priority] ||= []).push(t)
    }
    return byPriority
  }, [tickets])

  return (
    <div style={{ fontFamily: 'system-ui, Arial', padding: 16 }}>
      <h1 style={{ marginBottom: 8 }}>SecOps Ticket Dashboard (Prototype)</h1>
      <p style={{ marginTop: 0, color: '#555' }}>
        Categories are AI-derived (keyword MVP). Backend: FastAPI. Data: 100 fake Datto RMM-style tickets.
      </p>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, margin: '12px 0 18px' }}>
        {categories.map(c => (
          <button
            key={c.key}
            onClick={() => setSelected(c.key)}
            style={{
              padding: '8px 12px',
              borderRadius: 10,
              border: '1px solid #ddd',
              cursor: 'pointer',
              background: selected === c.key ? '#111' : '#fff',
              color: selected === c.key ? '#fff' : '#111',
            }}
          >
            {c.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div>Loading…</div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 10 }}>
          <h2 style={{ margin: '8px 0 0' }}>{selected}</h2>

          {Object.entries(grouped).map(([prio, items]) => (
            <div key={prio} style={{ border: '1px solid #eee', borderRadius: 12, padding: 12 }}>
              <h3 style={{ margin: 0 }}>{prio} ({items.length})</h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 8, marginTop: 8 }}>
                {items.map(t => (
                  <div key={t.autotask_ticket_id} style={{ border: '1px solid #f0f0f0', borderRadius: 10, padding: 10 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10 }}>
                      <strong>{t.ticket_number}</strong>
                      <span style={{ color: '#666' }}>{t.status}</span>
                    </div>
                    <div style={{ marginTop: 4 }}>{t.title}</div>
                    <div style={{ marginTop: 6, color: '#444', fontSize: 13 }}>
                      {t.company} • {t.location} • {t.primary_resource}
                    </div>
                    <div style={{ marginTop: 6, fontSize: 13, color: '#333' }}>
                      AI: <strong>{t.ai.category}</strong> (score {t.ai.score})
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
