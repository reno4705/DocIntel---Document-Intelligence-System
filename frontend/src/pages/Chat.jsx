import { useState, useEffect, useRef } from 'react'
import { MessageSquare, Send, Loader2, Bot, User, Trash2, FileText, Sparkles, AlertCircle, Search } from 'lucide-react'
import { chatWithDocuments, getChatHistory, clearChatHistory, getAIStatus, extractInformation, getDocuments } from '../services/api'

function Chat() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [aiAvailable, setAiAvailable] = useState(false)
  const [documents, setDocuments] = useState([])
  const [selectedDoc, setSelectedDoc] = useState(null)
  const [extractionResult, setExtractionResult] = useState(null)
  const [extracting, setExtracting] = useState(false)
  const [docSearch, setDocSearch] = useState('')
  const messagesEndRef = useRef(null)

  useEffect(() => {
    checkAIStatus()
    loadDocuments()
    loadHistory()
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const checkAIStatus = async () => {
    try {
      const status = await getAIStatus()
      setAiAvailable(status.available)
    } catch (err) {
      setAiAvailable(false)
    }
  }

  const loadDocuments = async () => {
    try {
      const docs = await getDocuments()
      setDocuments(docs)
    } catch (err) {
      console.error('Failed to load documents:', err)
    }
  }

  const loadHistory = async () => {
    try {
      const data = await getChatHistory()
      if (data.history && data.history.length > 0) {
        setMessages(data.history.map(msg => ({
          role: msg.role,
          content: msg.content,
          timestamp: msg.timestamp
        })))
      }
    } catch (err) {
      console.error('Failed to load chat history:', err)
    }
  }

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMessage = { role: 'user', content: input, timestamp: new Date().toISOString() }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await chatWithDocuments(input)
      
      const assistantMessage = {
        role: 'assistant',
        content: response.answer,
        citations: response.citations,
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, assistantMessage])
    } catch (err) {
      const errorMessage = {
        role: 'assistant',
        content: err.response?.data?.detail || 'Sorry, I encountered an error. Please try again.',
        isError: true,
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const handleClearHistory = async () => {
    if (!confirm('Clear all chat history?')) return
    
    try {
      await clearChatHistory()
      setMessages([])
    } catch (err) {
      console.error('Failed to clear history:', err)
    }
  }

  const handleExtract = async (docId) => {
    setExtracting(true)
    setExtractionResult(null)
    setSelectedDoc(docId)
    
    try {
      const result = await extractInformation(docId)
      setExtractionResult(result)
    } catch (err) {
      setExtractionResult({ error: err.response?.data?.detail || 'Extraction failed' })
    } finally {
      setExtracting(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="h-[calc(100vh-12rem)] flex gap-6">
      {/* Chat Panel */}
      <div className="flex-1 flex flex-col bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Bot className="h-6 w-6" />
            <div>
              <h2 className="font-semibold">Document AI Assistant</h2>
              <p className="text-sm text-blue-100">Ask anything about your documents</p>
            </div>
          </div>
          <button
            onClick={handleClearHistory}
            className="p-2 hover:bg-white/20 rounded-lg transition-colors"
            title="Clear chat history"
          >
            <Trash2 className="h-5 w-5" />
          </button>
        </div>

        {/* AI Status Warning */}
        {!aiAvailable && (
          <div className="px-4 py-3 bg-amber-50 border-b border-amber-200 flex items-center space-x-2 text-amber-700">
            <AlertCircle className="h-5 w-5" />
            <span className="text-sm">AI service not available. Please configure GROQ_API_KEY.</span>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-slate-400">
              <MessageSquare className="h-16 w-16 mb-4 opacity-50" />
              <p className="text-lg font-medium">Start a conversation</p>
              <p className="text-sm mt-1">Ask questions about your uploaded documents</p>
              <div className="mt-6 space-y-2 text-sm text-left">
                <p className="font-medium text-slate-500">Try asking:</p>
                <p className="text-slate-400">"What are the key points in my documents?"</p>
                <p className="text-slate-400">"Summarize the main findings"</p>
                <p className="text-slate-400">"What dates are mentioned?"</p>
                <p className="text-slate-400">"Who are the people involved?"</p>
              </div>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : msg.isError
                    ? 'bg-red-50 text-red-700 border border-red-200'
                    : 'bg-slate-100 text-slate-800'
                }`}
              >
                <div className="flex items-start space-x-2">
                  {msg.role === 'assistant' && (
                    <Bot className="h-5 w-5 mt-0.5 flex-shrink-0" />
                  )}
                  <div>
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                    
                    {/* Citations */}
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-slate-200">
                        <p className="text-xs font-medium text-slate-500 mb-1">Sources:</p>
                        <div className="flex flex-wrap gap-1">
                          {msg.citations.map((cite, i) => (
                            <span
                              key={i}
                              className="inline-flex items-center px-2 py-0.5 bg-white rounded text-xs text-slate-600"
                            >
                              <FileText className="h-3 w-3 mr-1" />
                              {cite.filename}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                  {msg.role === 'user' && (
                    <User className="h-5 w-5 mt-0.5 flex-shrink-0" />
                  )}
                </div>
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-slate-100 rounded-2xl px-4 py-3 flex items-center space-x-2">
                <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
                <span className="text-slate-600">Thinking...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="p-4 border-t border-slate-200">
          <div className="flex space-x-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask a question about your documents..."
              className="flex-1 px-4 py-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              rows={1}
              disabled={loading || !aiAvailable}
            />
            <button
              onClick={handleSend}
              disabled={loading || !input.trim() || !aiAvailable}
              className="px-4 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <Send className="h-5 w-5" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Smart Extraction Panel */}
      <div className="w-80 flex flex-col bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="px-4 py-3 bg-slate-50 border-b border-slate-200">
          <div className="flex items-center space-x-2">
            <Sparkles className="h-5 w-5 text-purple-600" />
            <h3 className="font-semibold text-slate-800">Smart Extraction</h3>
          </div>
          <p className="text-xs text-slate-500 mt-1">Extract structured data from documents</p>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          {documents.length === 0 ? (
            <div className="text-center text-slate-400 py-8">
              <FileText className="h-10 w-10 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No documents uploaded yet</p>
            </div>
          ) : (
            <div className="space-y-2">
              {/* Search Bar */}
              <div className="relative mb-3">
                <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 h-3 w-3 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search documents..."
                  value={docSearch}
                  onChange={(e) => setDocSearch(e.target.value)}
                  className="w-full pl-7 pr-2 py-1.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-xs"
                />
              </div>
              <p className="text-xs font-medium text-slate-500 mb-2">
                {documents.filter(d => d.filename.toLowerCase().includes(docSearch.toLowerCase())).length} documents
              </p>
              {documents.filter(d => d.filename.toLowerCase().includes(docSearch.toLowerCase())).slice(0, 15).map((doc) => (
                <button
                  key={doc.id}
                  onClick={() => handleExtract(doc.id)}
                  disabled={extracting}
                  className={`w-full text-left p-3 rounded-lg border transition-all ${
                    selectedDoc === doc.id
                      ? 'border-purple-500 bg-purple-50'
                      : 'border-slate-200 hover:border-purple-300 hover:bg-slate-50'
                  }`}
                >
                  <p className="text-sm font-medium text-slate-700 truncate">{doc.filename}</p>
                  <p className="text-xs text-slate-500">{doc.entity_count || 0} entities</p>
                </button>
              ))}
            </div>
          )}

          {/* Extraction Result */}
          {extracting && (
            <div className="mt-4 p-4 bg-slate-50 rounded-lg flex items-center justify-center">
              <Loader2 className="h-5 w-5 animate-spin text-purple-600 mr-2" />
              <span className="text-sm text-slate-600">Extracting...</span>
            </div>
          )}

          {extractionResult && !extracting && (
            <div className="mt-4 space-y-3">
              {extractionResult.error ? (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                  {extractionResult.error}
                </div>
              ) : (
                <>
                  <div className="p-3 bg-purple-50 border border-purple-200 rounded-lg">
                    <p className="text-xs font-medium text-purple-700">Document Type</p>
                    <p className="text-sm text-purple-900">{extractionResult.document_type || 'Unknown'}</p>
                  </div>

                  {extractionResult.extracted_fields && Object.keys(extractionResult.extracted_fields).length > 0 && (
                    <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                      <p className="text-xs font-medium text-slate-600 mb-2">Extracted Fields</p>
                      <div className="space-y-1 max-h-40 overflow-y-auto">
                        {Object.entries(extractionResult.extracted_fields).map(([key, value]) => (
                          <div key={key} className="text-xs">
                            <span className="font-medium text-slate-700">{key}:</span>{' '}
                            <span className="text-slate-600">{String(value)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {extractionResult.key_points && extractionResult.key_points.length > 0 && (
                    <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                      <p className="text-xs font-medium text-blue-700 mb-1">Key Points</p>
                      <ul className="text-xs text-blue-800 space-y-1">
                        {extractionResult.key_points.map((point, i) => (
                          <li key={i}>• {point}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {extractionResult.entities && (
                    <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                      <p className="text-xs font-medium text-green-700 mb-1">Entities Found</p>
                      <div className="text-xs text-green-800 space-y-1">
                        {extractionResult.entities.people?.length > 0 && (
                          <p>👤 People: {extractionResult.entities.people.join(', ')}</p>
                        )}
                        {extractionResult.entities.organizations?.length > 0 && (
                          <p>🏢 Orgs: {extractionResult.entities.organizations.join(', ')}</p>
                        )}
                        {extractionResult.entities.locations?.length > 0 && (
                          <p>📍 Places: {extractionResult.entities.locations.join(', ')}</p>
                        )}
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Chat
