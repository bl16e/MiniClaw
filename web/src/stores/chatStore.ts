import { create } from 'zustand'
import type { Message, ToolCall, SessionSummary, CheckpointEntry } from '../types'

interface ChatState {
  activeThreadId: string
  messages: Message[]
  sessions: SessionSummary[]
  history: CheckpointEntry[]
  isStreaming: boolean
  currentNode: string | null
  pendingApproval: { tools: ToolCall[] } | null
  streamingContent: string

  // Actions
  setActiveThread: (id: string) => void
  setMessages: (msgs: Message[]) => void
  addMessage: (msg: Message) => void
  setSessions: (s: SessionSummary[]) => void
  setHistory: (h: CheckpointEntry[]) => void
  setIsStreaming: (v: boolean) => void
  setCurrentNode: (node: string | null) => void
  setPendingApproval: (p: { tools: ToolCall[] } | null) => void
  setStreamingContent: (c: string) => void
  appendStreamingContent: (chunk: string) => void
  addToolCall: (tc: ToolCall) => void
  updateToolResult: (id: string, result: string, status: 'completed' | 'error') => void
  finalizeStreamingMessage: () => void
}

export const useChatStore = create<ChatState>((set, get) => ({
  activeThreadId: '',
  messages: [],
  sessions: [],
  history: [],
  isStreaming: false,
  currentNode: null,
  pendingApproval: null,
  streamingContent: '',

  setActiveThread: (id) => set({ activeThreadId: id }),
  setMessages: (msgs) => set({ messages: msgs }),
  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
  setSessions: (sessions) => set({ sessions }),
  setHistory: (history) => set({ history }),
  setIsStreaming: (v) => set({ isStreaming: v }),
  setCurrentNode: (node) => set({ currentNode: node }),
  setPendingApproval: (p) => set({ pendingApproval: p }),
  setStreamingContent: (c) => set({ streamingContent: c }),
  appendStreamingContent: (chunk) => set((s) => ({ streamingContent: s.streamingContent + chunk })),

  addToolCall: (tc) => {
    const last = get().messages[get().messages.length - 1]
    if (last && last.type === 'ai') {
      const existing = last.tool_calls || []
      const updated = { ...last, tool_calls: [...existing, tc] }
      set((s) => ({ messages: [...s.messages.slice(0, -1), updated] }))
    }
  },

  updateToolResult: (id, result, status) => {
    set((s) => ({
      messages: s.messages.map((m) => {
        if (m.type === 'ai' && m.tool_calls) {
          return {
            ...m,
            tool_calls: m.tool_calls.map((tc) =>
              tc.id === id ? { ...tc, result, status } : tc
            ),
          }
        }
        return m
      }),
    }))
  },

  finalizeStreamingMessage: () => {
    const content = get().streamingContent
    if (content) {
      set((s) => ({
        messages: [...s.messages, { type: 'ai', content }],
        streamingContent: '',
      }))
    }
  },
}))
