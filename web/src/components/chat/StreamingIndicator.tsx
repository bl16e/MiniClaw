interface Props {
  node: string | null
}

export default function StreamingIndicator({ node }: Props) {
  if (!node) return null
  return (
    <div className="streaming-indicator">
      <div className="typing-dots">
        <span />
        <span />
        <span />
      </div>
      <span>{node} is running...</span>
    </div>
  )
}
