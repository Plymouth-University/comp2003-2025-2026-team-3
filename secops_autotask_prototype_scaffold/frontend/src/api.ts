import type { Ticket } from './types'

export async function fetchCategories(): Promise<{ key: string; label: string }[]> {
  const r = await fetch('/api/categories')
  const j = await r.json()
  return j.items
}

export async function fetchTickets(category?: string): Promise<Ticket[]> {
  const url = category ? `/api/tickets?category=${encodeURIComponent(category)}` : '/api/tickets'
  const r = await fetch(url)
  const j = await r.json()
  return j.items
}
