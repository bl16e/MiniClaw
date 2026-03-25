import { useState } from 'react'
import type { ToolCall } from '../../types'

interface Props {
  toolCall: ToolCall
}

function StatusDot({ status }: { status: string }) {
  const colors: Record<string, string> = {
    pending: '#facc15',
    executing: '#818cf8',
    completed: '#5eead4',
    error: '#fb7185',
  }
  const bg = colors[status] || colors.pending
  return (
    <span className="tool-status-icon" style={{
      display: 'inline-block',
      width: 8,
      height: 8,
      borderRadius: '50%',
      background: bg,
      boxShadow: `0 0 6px ${bg}80`,
      animation: status === 'executing' ? 'typingPulse 1.2s ease-in-out infinite' : undefined,
    }} />
  )
}

export default function ToolCallCard({ toolCall }: Props) {
  const [argsOpen, setArgsOpen] = useState(false)
  const [resultOpen, setResultOpen] = useState(false)
  const status = toolCall.status || 'pending'

  return (
    <div className={`tool-card status-${status}`}>
      <div className="tool-card-header" onClick={() => setArgsOpen(!argsOpen)}>
        <StatusDot status={status} />
        <span className="tool-name">{toolCall.name}</span>
        <span className="tool-toggle" style={{ transform: argsOpen ? 'rotate(0)' : 'rotate(-90deg)' }}>
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </span>
      </div>
      {argsOpen && (
        <pre className="tool-args">{JSON.stringify(toolCall.args, null, 2)}</pre>
      )}
      {toolCall.result && (
        <>
          <div className="tool-result-header" onClick={() => setResultOpen(!resultOpen)}>
            <span>Result</span>
            <span style={{ marginLeft: 4, display: 'inline-block', transform: resultOpen ? 'rotate(0)' : 'rotate(-90deg)', transition: 'transform .2s' }}>
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="6 9 12 15 18 9" />
              </svg>
            </span>
          </div>
          {resultOpen && <pre className="tool-result">{toolCall.result}</pre>}
        </>
      )}
    </div>
  )
}
