import type { SessionSummary } from '../../types'

interface Props {
  session: SessionSummary
  active: boolean
  onSelect: () => void
  onDelete: () => void
}

export default function SessionItem({ session, active, onSelect, onDelete }: Props) {
  return (
    <div
      className={`session-item ${active ? 'active' : ''}`}
      onClick={onSelect}
    >
      <div className="session-item-header">
        <span className="session-id">{session.thread_id}</span>
        <button
          className="session-delete-btn"
          onClick={(e) => { e.stopPropagation(); onDelete() }}
          title="Delete session"
        >
          &times;
        </button>
      </div>
      <div className="session-preview">{session.preview}</div>
      <div className="session-count">{session.message_count} messages</div>
    </div>
  )
}
