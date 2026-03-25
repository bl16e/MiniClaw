import { useCallback, useRef } from 'react'
import { useChatStore } from '../stores/chatStore'
import { streamChat, approveTools, getMessages, getHistory } from '../api/client'
import type { SSEEvent, ToolCall } from '../types'

export function useChat() {
  const store = useChatStore()
  const abortRef = useRef<AbortController | null>(null)

  const handleSSEEvent = useCallback((event: SSEEvent) => {
    const s = useChatStore.getState()
    const d = event.data as Record<string, unknown>

    switch (event.type) {
      case 'node_start':
        useChatStore.setState({ currentNode: d.node as string })
        break

      case 'message_chunk':
        useChatStore.getState().appendStreamingContent(d.content as string)
        break

      case 'message_complete':
        if (d.role === 'ai') {
          // If there's streaming content, finalize it; otherwise add as new message
          if (s.streamingContent) {
            useChatStore.getState().finalizeStreamingMessage()
          } else {
            useChatStore.getState().addMessage({ type: 'ai', content: d.content as string })
          }
        }
        break

      case 'tool_call': {
        const tc: ToolCall = {
          id: d.id as string,
          name: d.name as string,
          args: d.args as Record<string, unknown>,
          status: 'executing',
        }
        // Add tool_call to the last AI message
        const msgs = useChatStore.getState().messages
        const lastAi = msgs[msgs.length - 1]
        if (lastAi && lastAi.type === 'ai') {
          useChatStore.getState().addToolCall(tc)
        } else {
          // Create a placeholder AI message with tool calls
          useChatStore.getState().addMessage({ type: 'ai', content: '', tool_calls: [tc] })
        }
        break
      }

      case 'tool_result':
        useChatStore.getState().updateToolResult(
          d.id as string,
          d.result as string,
          d.status as 'completed' | 'error'
        )
        break

      case 'approval_required':
        useChatStore.setState({
          pendingApproval: { tools: d.tools as ToolCall[] },
        })
        break

      case 'approval_resolved':
        useChatStore.setState({ pendingApproval: null })
        break

      case 'complete':
        useChatStore.setState({ isStreaming: false, currentNode: null })
        break

      case 'error':
        useChatStore.setState({ isStreaming: false, currentNode: null })
        console.error('Stream error:', d.message)
        break
    }
  }, [])

  const sendMessage = useCallback(async (message: string) => {
    const threadId = useChatStore.getState().activeThreadId
    if (!threadId || !message.trim()) return

    useChatStore.getState().addMessage({ type: 'human', content: message })
    useChatStore.setState({ isStreaming: true, streamingContent: '' })

    abortRef.current = new AbortController()
    try {
      await streamChat(threadId, message, handleSSEEvent, abortRef.current.signal)
    } catch (e) {
      if ((e as Error).name !== 'AbortError') {
        console.error('Chat error:', e)
      }
    } finally {
      useChatStore.setState({ isStreaming: false, currentNode: null })
    }
  }, [handleSSEEvent])

  const approve = useCallback(async (approved: boolean) => {
    const threadId = useChatStore.getState().activeThreadId
    useChatStore.setState({ pendingApproval: null })
    await approveTools(threadId, approved)
  }, [])

  const loadMessages = useCallback(async (threadId: string) => {
    const msgs = await getMessages(threadId)
    useChatStore.setState({ messages: msgs })
  }, [])

  const loadHistory = useCallback(async (threadId: string) => {
    const h = await getHistory(threadId)
    useChatStore.setState({ history: h })
  }, [])

  return { sendMessage, approve, loadMessages, loadHistory }
}
