import SessionSidebar from './sidebar/SessionSidebar'
import ChatPanel from './chat/ChatPanel'
import HistoryPanel from './history/HistoryPanel'

export default function Layout() {
  return (
    <div className="app-layout">
      <SessionSidebar />
      <ChatPanel />
      <HistoryPanel />
    </div>
  )
}
