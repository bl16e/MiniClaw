import { useEffect } from 'react'
import { useChatStore } from '../../stores/chatStore'
import { useSessions } from '../../hooks/useSessions'
import SessionItem from './SessionItem'

export default function SessionSidebar() {
  const { sessions, activeThreadId } = useChatStore()
  const { loadSessions, newSession, switchSession, removeSession } = useSessions()

  useEffect(() => {
    loadSessions()
  }, [loadSessions])

  return (
    <aside className="session-sidebar">
      <div className="sidebar-header">
        <h2>MiniClaw</h2>
        <button className="new-session-btn" onClick={() => newSession()}>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{marginRight: 3}}>
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          New
        </button>
      </div>
      <div className="session-list">
        {sessions.map((s) => (
          <SessionItem
            key={s.thread_id}
            session={s}
            active={s.thread_id === activeThreadId}
            onSelect={() => switchSession(s.thread_id)}
            onDelete={() => removeSession(s.thread_id)}
          />
        ))}
        {sessions.length === 0 && (
          <div className="no-sessions">No sessions yet.<br/>Create one to start chatting!</div>
        )}
      </div>
    </aside>
  )
}
