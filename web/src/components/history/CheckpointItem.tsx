import type { CheckpointEntry } from '../../types'

interface Props {
  entry: CheckpointEntry
  index: number
  onReplay: () => void
  onBranch: () => void
}

export default function CheckpointItem({ entry, index, onReplay, onBranch }: Props) {
  return (
    <div className="checkpoint-item">
      <div className="checkpoint-meta">
        <span className="checkpoint-step">Turn {index}</span>
        <span className="checkpoint-node">{entry.message_count} msgs</span>
      </div>
      <div className="checkpoint-preview">{entry.preview}</div>
      <div className="checkpoint-actions">
        <button className="btn-small" onClick={onReplay} title="Replay from this checkpoint">
          Replay
        </button>
        <button className="btn-small" onClick={onBranch} title="Branch from this checkpoint">
          Branch
        </button>
      </div>
    </div>
  )
}
