import { useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import ReactMarkdown from 'react-markdown'
import { Copy, Send } from 'lucide-react'
import toast from 'react-hot-toast'
import { chatService } from '../services/analysisService'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import type { ChatMessage } from '../types'

function Message({ msg }: { msg: ChatMessage }) {
  const isUser = msg.role === 'user'
  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div
        className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-bold"
        style={isUser
          ? { backgroundColor: '#00ed64', color: '#001e2b' }
          : { backgroundColor: '#f4f7f6', color: '#5c6c7a' }}
      >
        {isUser ? 'U' : 'AI'}
      </div>

      {/* Bubble */}
      <div
        className={`max-w-[75%] sm:max-w-2xl rounded-[16px] px-4 py-3 text-sm ${
          isUser ? 'rounded-tr-[4px]' : 'rounded-tl-[4px]'
        }`}
        style={isUser
          ? { backgroundColor: '#001e2b', color: '#ffffff' }
          : { backgroundColor: '#ffffff', color: '#001e2b', border: '1px solid #e1e5e8', boxShadow: '0 1px 3px rgba(0,30,43,0.06)' }}
      >
        {isUser ? (
          <p>{msg.content}</p>
        ) : (
          <div className="prose prose-sm max-w-none" style={{ color: '#001e2b' }}>
            <ReactMarkdown>{msg.content}</ReactMarkdown>
          </div>
        )}

        {/* Citations */}
        {msg.sources && msg.sources.length > 0 && (
          <div className="mt-3 pt-3 border-t border-[#e1e5e8] space-y-1">
            <p className="text-xs text-[#a8b3bc] font-medium">Sources</p>
            {msg.sources.map((s, i) => (
              <div key={i} className="text-xs text-[#5c6c7a] rounded-[6px] px-2 py-1"
                style={{ backgroundColor: '#f9fbfa' }}>
                <span className="font-medium">{s.section}</span>
                {s.page && ` · Page ${s.page}`}
                {' · '}
                <span style={{ color: '#00684a' }}>{(s.score * 100).toFixed(0)}% match</span>
              </div>
            ))}
          </div>
        )}
        {msg.confidence !== undefined && (
          <p className="mt-2 text-xs text-[#a8b3bc]">Confidence: {(msg.confidence * 100).toFixed(0)}%</p>
        )}
      </div>

      {/* Copy button (AI only) */}
      {!isUser && (
        <button
          onClick={() => { navigator.clipboard.writeText(msg.content); toast.success('Copied!') }}
          className="self-start mt-1 text-[#c1ccd6] hover:text-[#5c6c7a] transition-colors"
          title="Copy"
        >
          <Copy className="w-4 h-4" />
        </button>
      )}
    </div>
  )
}

function TypingIndicator() {
  return (
    <div className="flex gap-3">
      <div className="w-8 h-8 rounded-full bg-[#f4f7f6] flex items-center justify-center flex-shrink-0 text-xs font-bold text-[#5c6c7a]">AI</div>
      <div className="bg-white border border-[#e1e5e8] rounded-[16px] rounded-tl-[4px] px-4 py-3 shadow-sm">
        <div className="flex gap-1 items-center h-5">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="w-2 h-2 rounded-full animate-typing"
              style={{ backgroundColor: '#c1ccd6', animationDelay: `${i * 0.2}s` }}
            />
          ))}
        </div>
      </div>
    </div>
  )
}

const SUGGESTIONS = [
  'What are the abnormal values?',
  'Summarize this report.',
  'What medicines are mentioned?',
  'Is my blood sugar normal?',
]

export default function ChatPage() {
  const { id: documentId } = useParams<{ id: string }>()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput]       = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const { mutate: sendMessage, isPending } = useMutation({
    mutationFn: async (question: string) =>
      chatService.ragChat(question, documentId!, messages.map((m) => ({ role: m.role, content: m.content }))),
    onMutate: (question) => {
      setMessages((prev) => [
        ...prev,
        { id: Date.now().toString(), role: 'user', content: question, created_at: new Date().toISOString() },
      ])
      setInput('')
    },
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        { id: (Date.now() + 1).toString(), role: 'assistant', content: data.answer,
          sources: data.sources, confidence: data.confidence, created_at: new Date().toISOString() },
      ])
    },
    onError: () => toast.error('Failed to get a response. Please try again.'),
  })

  const handleSend = () => {
    const q = input.trim()
    if (!q || isPending) return
    sendMessage(q)
  }

  return (
    <div className="flex flex-col animate-fade-in" style={{ height: 'calc(100vh - 9rem)' }}>

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4 gap-3">
        <div>
          <h1 className="text-xl font-semibold text-[#001e2b]">Chat with Report</h1>
          <p className="text-[#a8b3bc] text-xs mt-0.5">
            Answers grounded in your report · Doc: {documentId?.slice(0, 8)}…
          </p>
        </div>
        <button onClick={() => setMessages([])} className="btn-secondary text-xs px-3 py-1.5 self-start sm:self-auto">
          Clear chat
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-1">
        {messages.length === 0 && (
          <div className="text-center py-14">
            <div className="w-14 h-14 rounded-[12px] bg-[#f4f7f6] flex items-center justify-center mx-auto mb-4">
              <span className="text-2xl">🩺</span>
            </div>
            <p className="text-[#5c6c7a] text-sm mb-5">Ask anything about your medical report.</p>
            <div className="flex flex-wrap justify-center gap-2">
              {SUGGESTIONS.map((q) => (
                <button
                  key={q}
                  onClick={() => setInput(q)}
                  className="text-xs px-3 py-1.5 rounded-full border transition-colors"
                  style={{ backgroundColor: '#e3fcef', borderColor: '#a7f3d0', color: '#00684a' }}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}
        {messages.map((m) => <Message key={m.id} msg={m} />)}
        {isPending && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="mt-4 flex gap-3 items-end">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() } }}
          placeholder="Ask about your report… (Enter to send)"
          rows={1}
          className="flex-1 input-field resize-none py-3 max-h-32"
          style={{ overflowY: 'auto' }}
        />
        <button
          onClick={handleSend}
          disabled={!input.trim() || isPending || !documentId}
          className="btn-primary p-3 rounded-[12px]"
        >
          {isPending ? <LoadingSpinner size="sm" color="slate" /> : <Send className="w-5 h-5" />}
        </button>
      </div>
      <p className="mt-2 text-xs text-[#a8b3bc] text-center">
        Answers are grounded in report data only. Always consult a healthcare professional.
      </p>
    </div>
  )
}
