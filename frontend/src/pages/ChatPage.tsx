import { useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import ReactMarkdown from 'react-markdown'
import { Copy, Send } from 'lucide-react'
import toast from 'react-hot-toast'
import { chatService } from '../services/analysisService'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import type { ChatMessage, CitationSource } from '../types'

function Message({ msg }: { msg: ChatMessage }) {
  const isUser = msg.role === 'user'
  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-bold ${isUser ? 'bg-green-600 text-white' : 'bg-slate-100 text-slate-600'}`}>
        {isUser ? 'U' : 'AI'}
      </div>
      <div className={`max-w-2xl rounded-2xl px-4 py-3 text-sm ${isUser ? 'bg-green-600 text-white rounded-tr-none' : 'bg-white border border-slate-100 text-slate-800 rounded-tl-none shadow-sm'}`}>
        {isUser ? <p>{msg.content}</p> : (
          <div className="prose prose-sm max-w-none prose-slate">
            <ReactMarkdown>{msg.content}</ReactMarkdown>
          </div>
        )}
        {/* Citations */}
        {msg.sources && msg.sources.length > 0 && (
          <div className="mt-3 pt-3 border-t border-slate-100 space-y-1">
            <p className="text-xs text-slate-400 font-medium">Sources</p>
            {msg.sources.map((s, i) => (
              <div key={i} className="text-xs text-slate-500 bg-slate-50 rounded px-2 py-1">
                <span className="font-medium">{s.section}</span>
                {s.page && ` · Page ${s.page}`}
                {' · '}<span className="text-green-600">{(s.score * 100).toFixed(0)}% match</span>
              </div>
            ))}
          </div>
        )}
        {msg.confidence !== undefined && (
          <p className="mt-2 text-xs text-slate-400">Confidence: {(msg.confidence * 100).toFixed(0)}%</p>
        )}
      </div>
      {!isUser && (
        <button
          onClick={() => { navigator.clipboard.writeText(msg.content); toast.success('Copied!') }}
          className="self-start mt-1 text-slate-300 hover:text-slate-500 transition-colors"
          title="Copy"
        ><Copy className="w-4 h-4" /></button>
      )}
    </div>
  )
}

function TypingIndicator() {
  return (
    <div className="flex gap-3">
      <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center flex-shrink-0 text-xs font-bold text-slate-600">AI</div>
      <div className="bg-white border border-slate-100 rounded-2xl rounded-tl-none px-4 py-3 shadow-sm">
        <div className="flex gap-1 items-center h-5">
          {[0, 1, 2].map((i) => (
            <div key={i} className="w-2 h-2 rounded-full bg-slate-300 animate-typing" style={{ animationDelay: `${i * 0.2}s` }} />
          ))}
        </div>
      </div>
    </div>
  )
}

export default function ChatPage() {
  const { id: documentId } = useParams<{ id: string }>()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const { mutate: sendMessage, isPending } = useMutation({
    mutationFn: async (question: string) => {
      return chatService.ragChat(
        question,
        documentId!,
        messages.map((m) => ({ role: m.role, content: m.content })),
      )
    },
    onMutate: (question) => {
      const userMsg: ChatMessage = { id: Date.now().toString(), role: 'user', content: question, created_at: new Date().toISOString() }
      setMessages((prev) => [...prev, userMsg])
      setInput('')
    },
    onSuccess: (data) => {
      const aiMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.answer,
        sources: data.sources,
        confidence: data.confidence,
        created_at: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, aiMsg])
    },
    onError: () => toast.error('Failed to get a response. Please try again.'),
  })

  const handleSend = () => {
    const q = input.trim()
    if (!q || isPending) return
    sendMessage(q)
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Chat with Report</h1>
          <p className="text-slate-500 text-xs mt-0.5">Answers grounded in your uploaded report · Document ID: {documentId?.slice(0, 8)}…</p>
        </div>
        <button onClick={() => setMessages([])} className="btn-secondary text-xs px-3 py-1.5">Clear chat</button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-1">
        {messages.length === 0 && (
          <div className="text-center py-16">
            <p className="text-slate-400 text-sm">Ask anything about your medical report.</p>
            <div className="mt-4 flex flex-wrap justify-center gap-2">
              {[
                'What are the abnormal values?',
                'Summarize this report.',
                'What medicines are mentioned?',
                'Is my blood sugar normal?',
              ].map((q) => (
                <button key={q} onClick={() => { setInput(q); }} className="text-xs px-3 py-1.5 bg-green-50 text-green-700 rounded-full border border-green-100 hover:bg-green-100">
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
        <button onClick={handleSend} disabled={!input.trim() || isPending || !documentId} className="btn-primary p-3 rounded-xl">
          {isPending ? <LoadingSpinner size="sm" color="white" /> : <Send className="w-5 h-5" />}
        </button>
      </div>
      <p className="mt-2 text-xs text-slate-400 text-center">
        Answers are grounded in report data only. Always consult a healthcare professional.
      </p>
    </div>
  )
}
