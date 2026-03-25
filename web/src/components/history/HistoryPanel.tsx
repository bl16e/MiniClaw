import { useEffect, useState } from 'react'
import { useChatStore } from '../../stores/chatStore'
import { useChat } from '../../hooks/useChat'
import { useSessions } from '../../hooks/useSessions'
import { branchFromCheckpoint, streamReplay } from '../../api/client'
import CheckpointItem from './CheckpointItem'

export default function HistoryPanel() {
  const { history, activeThreadId } = useChatStore()
  const { loadHistory, loadMessages } = useChat()
  const { loadSessions, switchSession } = useSessions()
  const [collapsed, setCollapsed] = useState(false)

  useEffect(() => {
    if (activeThreadId) loadHistory(activeThreadId)
  }, [activeThreadId, loadHistory])

  const handleReplay = async (checkpointId: string) => {
    if (!activeThreadId) return
    useChatStore.setState({ isStreaming: true })
    try {
      await streamReplay(activeThreadId, checkpointId, (event) => {
        // Reuse the same SSE event handler logic
        const d = event.data as Record<string, unknown>
        if (event.type === 'message_complete' && d.role === 'ai') {
          useChatStore.getState().addMessage({ type: 'ai', content: d.content as string })
        } else if (event.type === 'complete') {
          useChatStore.setState({ isStreaming: false })
        }
      })
    } finally {
      useChatStore.setState({ isStreaming: false })
      await loadMessages(activeThreadId)
      await loadHistory(activeThreadId)
    }
  }

  const handleBranch = async (checkpointId: string) => {
    if (!activeThreadId) return
    const result = await branchFromCheckpoint(activeThreadId, checkpointId)
    await loadSessions()
    await switchSession(result.thread_id)
  }

  if (collapsed) {
    return (
      <aside className="history-panel collapsed">
        <button className="toggle-history" onClick={() => setCollapsed(false)}>History &lsaquo;</button>
      </aside>
    )
  }

  return (
    <aside className="history-panel">
      <div className="history-header">
        <h3>History</h3>
        <button className="toggle-history" onClick={() => setCollapsed(true)}>&rsaquo;</button>
      </div>
      <div className="history-list">
        {history.map((entry, idx) => (
          <CheckpointItem
            key={entry.checkpoint_id}
            entry={entry}
            index={history.length - idx}
            onReplay={() => handleReplay(entry.checkpoint_id)}
            onBranch={() => handleBranch(entry.checkpoint_id)}
          />
        ))}
        {history.length === 0 && (
          <div className="no-history">No checkpoints yet</div>
        )}
      </div>
    </aside>
  )
}
