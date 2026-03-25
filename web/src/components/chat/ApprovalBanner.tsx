import type { ToolCall } from '../../types'

interface Props {
  tools: ToolCall[]
  onApprove: () => void
  onReject: () => void
}

export default function ApprovalBanner({ tools, onApprove, onReject }: Props) {
  return (
    <div className="approval-banner">
      <div className="approval-title">Approval Required</div>
      <div className="approval-tools">
        {tools.map((tc) => (
          <div key={tc.id} className="approval-tool-item">
            <strong>{tc.name}</strong>
            <pre>{JSON.stringify(tc.args, null, 2)}</pre>
          </div>
        ))}
      </div>
      <div className="approval-actions">
        <button className="btn-approve" onClick={onApprove}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{marginRight: 4}}>
            <polyline points="20 6 9 17 4 12" />
          </svg>
          Approve
        </button>
        <button className="btn-reject" onClick={onReject}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{marginRight: 4}}>
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
          Reject
        </button>
      </div>
    </div>
  )
}
