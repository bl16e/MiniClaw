import type { SessionSummary, CheckpointEntry, Message, SSEEvent } from '../types'

const BASE = '/api'

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(BASE + url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`${res.status}: ${text}`)
  }
  return res.json()
}

// ── Sessions ────────────────────────────────────────

export async function fetchSessions(): Promise<SessionSummary[]> {
  return request('/sessions')
}

export async function createSession(name?: string): Promise<SessionSummary> {
  return request('/sessions', {
    method: 'POST',
    body: JSON.stringify({ name: name || null }),
  })
}

export async function deleteSession(threadId: string): Promise<void> {
  await request(`/sessions/${threadId}`, { method: 'DELETE' })
}

export async function getMessages(threadId: string): Promise<Message[]> {
  return request(`/sessions/${threadId}/messages`)
}

export async function getHistory(threadId: string, limit = 20): Promise<CheckpointEntry[]> {
  return request(`/sessions/${threadId}/history?limit=${limit}`)
}

export async function branchFromCheckpoint(
  threadId: string,
  checkpointId: string,
  newThreadId?: string
): Promise<{ thread_id: string }> {
  return request(`/sessions/${threadId}/branch`, {
    method: 'POST',
    body: JSON.stringify({ checkpoint_id: checkpointId, new_thread_id: newThreadId || null }),
  })
}

export async function approveTools(threadId: string, approved: boolean): Promise<void> {
  await request(`/chat/${threadId}/approve`, {
    method: 'POST',
    body: JSON.stringify({ approved }),
  })
}

// ── SSE Stream ──────────────────────────────────────

export async function streamChat(
  threadId: string,
  message: string,
  onEvent: (event: SSEEvent) => void,
  signal?: AbortSignal
): Promise<void> {
  const res = await fetch(`${BASE}/chat/${threadId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
    signal,
  })
  if (!res.ok || !res.body) throw new Error('Stream failed')

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    const parts = buffer.split('\n\n')
    buffer = parts.pop() || ''

    for (const part of parts) {
      const lines = part.split('\n')
      let eventType = ''
      let data = ''
      for (const line of lines) {
        if (line.startsWith('event: ')) eventType = line.slice(7)
        else if (line.startsWith('data: ')) data = line.slice(6)
      }
      if (eventType && data) {
        try {
          onEvent({ type: eventType as SSEEvent['type'], data: JSON.parse(data) })
        } catch { /* skip malformed */ }
      }
    }
  }
}

export async function streamReplay(
  threadId: string,
  checkpointId: string,
  onEvent: (event: SSEEvent) => void,
  signal?: AbortSignal
): Promise<void> {
  const res = await fetch(`${BASE}/sessions/${threadId}/replay`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ checkpoint_id: checkpointId }),
    signal,
  })
  if (!res.ok || !res.body) throw new Error('Replay stream failed')

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    const parts = buffer.split('\n\n')
    buffer = parts.pop() || ''

    for (const part of parts) {
      const lines = part.split('\n')
      let eventType = ''
      let data = ''
      for (const line of lines) {
        if (line.startsWith('event: ')) eventType = line.slice(7)
        else if (line.startsWith('data: ')) data = line.slice(6)
      }
      if (eventType && data) {
        try {
          onEvent({ type: eventType as SSEEvent['type'], data: JSON.parse(data) })
        } catch { /* skip malformed */ }
      }
    }
  }
}
