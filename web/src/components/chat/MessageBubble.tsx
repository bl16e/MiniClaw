import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import type { Message } from '../../types'
import ToolCallCard from './ToolCallCard'
import CodeBlock from './CodeBlock'

interface Props {
  message: Message
}

export default function MessageBubble({ message }: Props) {
  if (message.type === 'human') {
    return (
      <div className="message-row human">
        <div className="message-bubble human-bubble">{message.content}</div>
      </div>
    )
  }

  if (message.type === 'tool') {
    return null
  }

  return (
    <div className="message-row ai">
      <div className="message-bubble ai-bubble">
        {message.content && (
          <div className="markdown-content">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeHighlight]}
              components={{
                pre({ children }) {
                  return <>{children}</>
                },
                code({ className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '')
                  const codeStr = String(children).replace(/\n$/, '')

                  if (match || (codeStr.includes('\n'))) {
                    return (
                      <CodeBlock
                        language={match ? match[1] : ''}
                        code={codeStr}
                        className={className}
                        {...props}
                      />
                    )
                  }
                  // inline code
                  return <code className={className} {...props}>{children}</code>
                },
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>
        )}
        {message.tool_calls && message.tool_calls.length > 0 && (
          <div className="tool-calls-list">
            {message.tool_calls.map((tc) => (
              <ToolCallCard key={tc.id} toolCall={tc} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
