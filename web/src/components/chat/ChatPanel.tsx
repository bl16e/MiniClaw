import { useChatStore } from '../../stores/chatStore'
import { useChat } from '../../hooks/useChat'
import MessageList from './MessageList'
import ChatInput from './ChatInput'
import StreamingIndicator from './StreamingIndicator'
import ApprovalBanner from './ApprovalBanner'

export default function ChatPanel() {
  const { messages, isStreaming, currentNode, pendingApproval, streamingContent, activeThreadId } = useChatStore()
  const { sendMessage, approve } = useChat()

  if (!activeThreadId) {
    return (
      <main className="chat-panel">
        <div className="chat-empty">Select or create a session to start chatting</div>
      </main>
    )
  }

  return (
    <main className="chat-panel">
      <div className="chat-header">
        <span className="thread-label">{activeThreadId}</span>
      </div>
      <MessageList messages={messages} streamingContent={streamingContent} />
      <StreamingIndicator node={isStreaming ? currentNode : null} />
      {pendingApproval && (
        <ApprovalBanner
          tools={pendingApproval.tools}
          onApprove={() => approve(true)}
          onReject={() => approve(false)}
        />
      )}
      <ChatInput disabled={isStreaming} onSend={sendMessage} />
    </main>
  )
}
