export interface Message {
  id?: string
  type: 'human' | 'ai' | 'tool'
  content: string
  tool_calls?: ToolCall[]
  tool_call_id?: string
  name?: string
}

export interface ToolCall {
  id: string
  name: string
  args: Record<string, unknown>
  status?: 'pending' | 'executing' | 'completed' | 'error'
  result?: string
}

export interface SessionSummary {
  thread_id: string
  message_count: number
  preview: string
}

export interface CheckpointEntry {
  checkpoint_id: string
  node: string
  step: number
  message_count: number
  next_nodes: string[]
  preview: string
}

export type SSEEventType =
  | 'node_start'
  | 'message_chunk'
  | 'message_complete'
  | 'tool_call'
  | 'tool_result'
  | 'approval_required'
  | 'approval_resolved'
  | 'complete'
  | 'error'

export interface SSEEvent {
  type: SSEEventType
  data: Record<string, unknown>
}
