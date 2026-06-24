import ChatWindow from './components/ChatWindow'

export default function App() {
  return (
    <div className="h-full flex items-center justify-center bg-slate-950 p-4">

      {/* Background glow */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-20%] left-[30%] w-[600px] h-[600px] bg-brand-600/5 rounded-full blur-3xl" />
        <div className="absolute bottom-[-10%] right-[20%] w-[400px] h-[400px] bg-brand-500/5 rounded-full blur-3xl" />
      </div>

      {/* Chat panel */}
      <div className="relative w-full max-w-2xl h-[90vh] max-h-[800px]
                      bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl
                      flex flex-col overflow-hidden">
        <ChatWindow />
      </div>

    </div>
  )
}
