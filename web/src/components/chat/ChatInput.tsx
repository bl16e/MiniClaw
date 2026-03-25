import { useState, type KeyboardEvent } from 'react'

interface Props {
  disabled: boolean
  onSend: (msg: string) => void
}

export default function ChatInput({ disabled, onSend }: Props) {
  const [text, setText] = useState('')

  const handleSend = () => {
    const msg = text.trim()
    if (!msg || disabled) return
    onSend(msg)
    setText('')
  }

  const handleKey = (e: KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="chat-input-wrapper">
      <div className="chat-input-inner">
        <textarea
          className="chat-input"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKey}
          placeholder={disabled ? 'Waiting for response...' : 'Ask anything...'}
          disabled={disabled}
          rows={1}
        />
        <button
          className="send-btn"
          onClick={handleSend}
          disabled={disabled || !text.trim()}
          title="Send message"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
      </div>
    </div>
  )
}
