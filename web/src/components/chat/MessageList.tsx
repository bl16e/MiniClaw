import { useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import type { Message } from '../../types'
import MessageBubble from './MessageBubble'
import CodeBlock from './CodeBlock'

interface Props {
  messages: Message[]
  streamingContent: string
}

export default function MessageList({ messages, streamingContent }: Props) {
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingContent])

  return (
    <div className="message-list">
      {messages.map((m, i) => (
        <MessageBubble key={i} message={m} />
      ))}
      {streamingContent && (
        <div className="message-row ai">
          <div className="message-bubble ai-bubble streaming">
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
                    if (match || codeStr.includes('\n')) {
                      return (
                        <CodeBlock
                          language={match ? match[1] : ''}
                          code={codeStr}
                          className={className}
                          {...props}
                        />
                      )
                    }
                    return <code className={className} {...props}>{children}</code>
                  },
                }}
              >
                {streamingContent}
              </ReactMarkdown>
            </div>
            <span className="cursor-blink" />
          </div>
        </div>
      )}
      <div ref={endRef} />
    </div>
  )
}
