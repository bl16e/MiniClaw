import { useCallback } from 'react'
import { useChatStore } from '../stores/chatStore'
import { fetchSessions, createSession, deleteSession, getMessages } from '../api/client'

export function useSessions() {
  const store = useChatStore()

  const loadSessions = useCallback(async () => {
    const sessions = await fetchSessions()
    useChatStore.setState({ sessions })
    return sessions
  }, [])

  const newSession = useCallback(async (name?: string) => {
    const session = await createSession(name)
    await loadSessions()
    useChatStore.setState({
      activeThreadId: session.thread_id,
      messages: [],
      history: [],
    })
    return session.thread_id
  }, [loadSessions])

  const switchSession = useCallback(async (threadId: string) => {
    useChatStore.setState({ activeThreadId: threadId })
    const msgs = await getMessages(threadId)
    useChatStore.setState({ messages: msgs })
  }, [])

  const removeSession = useCallback(async (threadId: string) => {
    await deleteSession(threadId)
    const sessions = await fetchSessions()
    useChatStore.setState({ sessions })
    if (useChatStore.getState().activeThreadId === threadId) {
      if (sessions.length > 0) {
        const next = sessions[0].thread_id
        useChatStore.setState({ activeThreadId: next })
        const msgs = await getMessages(next)
        useChatStore.setState({ messages: msgs })
      } else {
        useChatStore.setState({ activeThreadId: '', messages: [] })
      }
    }
  }, [])

  return { loadSessions, newSession, switchSession, removeSession }
}
