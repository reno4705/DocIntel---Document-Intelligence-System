import { useState } from 'react'
import { Search, MessageSquare, Users, Link2, AlertTriangle, Send, Loader2 } from 'lucide-react'
import { askQuestion, queryEntity, queryConnection, findContradictions } from '../services/api'

function Query() {
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [activeTab, setActiveTab] = useState('ask')
  
  // Entity query state
  const [entityName, setEntityName] = useState('')
  
  // Connection query state
  const [entity1, setEntity1] = useState('')
  const [entity2, setEntity2] = useState('')

  const handleAskQuestion = async (e) => {
    e.preventDefault()
    if (!question.trim()) return
    
    setLoading(true)
    setResult(null)
    try {
      const data = await askQuestion(question)
      setResult({ type: 'question', data })
    } catch (error) {
      setResult({ type: 'error', message: error.response?.data?.detail || 'Query failed' })
    } finally {
      setLoading(false)
    }
  }

  const handleEntityQuery = async (e) => {
    e.preventDefault()
    if (!entityName.trim()) return
    
    setLoading(true)
    setResult(null)
    try {
      const data = await queryEntity(entityName)
      setResult({ type: 'entity', data })
    } catch (error) {
      setResult({ type: 'error', message: error.response?.data?.detail || 'Query failed' })
    } finally {
      setLoading(false)
    }
  }

  const handleConnectionQuery = async (e) => {
    e.preventDefault()
    if (!entity1.trim() || !entity2.trim()) return
    
    setLoading(true)
    setResult(null)
    try {
      const data = await queryConnection(entity1, entity2)
      setResult({ type: 'connection', data })
    } catch (error) {
      setResult({ type: 'error', message: error.response?.data?.detail || 'Query failed' })
    } finally {
      setLoading(false)
    }
  }

  const handleFindContradictions = async () => {
    setLoading(true)
    setResult(null)
    try {
      const data = await findContradictions()
      setResult({ type: 'contradictions', data })
    } catch (error) {
      setResult({ type: 'error', message: error.response?.data?.detail || 'Analysis failed' })
    } finally {
      setLoading(false)
    }
  }

  const tabs = [
    { id: 'ask', label: 'Ask Question', icon: MessageSquare },
    { id: 'entity', label: 'Entity Lookup', icon: Users },
    { id: 'connection', label: 'Find Connection', icon: Link2 },
    { id: 'contradictions', label: 'Contradictions', icon: AlertTriangle },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800 flex items-center space-x-2">
          <Search className="h-7 w-7 text-blue-600" />
          <span>Cross-Document Query</span>
        </h1>
        <p className="text-slate-500 mt-1">Ask questions across your entire document corpus</p>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="flex border-b border-slate-200">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => { setActiveTab(tab.id); setResult(null) }}
              className={`flex items-center space-x-2 px-6 py-3 text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50'
                  : 'text-slate-500 hover:text-slate-700 hover:bg-slate-50'
              }`}
            >
              <tab.icon className="h-4 w-4" />
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        <div className="p-6">
          {/* Ask Question Tab */}
          {activeTab === 'ask' && (
            <form onSubmit={handleAskQuestion}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Ask a question about your documents
                  </label>
                  <div className="flex space-x-2">
                    <input
                      type="text"
                      value={question}
                      onChange={(e) => setQuestion(e.target.value)}
                      placeholder='e.g., "What do we know about John Smith?" or "List all organizations"'
                      className="flex-1 px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                    <button
                      type="submit"
                      disabled={loading || !question.trim()}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                    >
                      {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                      <span>Ask</span>
                    </button>
                  </div>
                </div>
                <div className="text-sm text-slate-500">
                  <p className="font-medium mb-1">Example questions:</p>
                  <ul className="list-disc list-inside space-y-1">
                    <li>"What do we know about [person/company name]?"</li>
                    <li>"How is [entity1] related to [entity2]?"</li>
                    <li>"List all people/organizations/locations"</li>
                    <li>"Which documents mention [topic]?"</li>
                  </ul>
                </div>
              </div>
            </form>
          )}

          {/* Entity Lookup Tab */}
          {activeTab === 'entity' && (
            <form onSubmit={handleEntityQuery}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Entity name to look up
                  </label>
                  <div className="flex space-x-2">
                    <input
                      type="text"
                      value={entityName}
                      onChange={(e) => setEntityName(e.target.value)}
                      placeholder="Enter entity name (person, company, location...)"
                      className="flex-1 px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                    <button
                      type="submit"
                      disabled={loading || !entityName.trim()}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                    >
                      {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
                      <span>Search</span>
                    </button>
                  </div>
                </div>
              </div>
            </form>
          )}

          {/* Connection Tab */}
          {activeTab === 'connection' && (
            <form onSubmit={handleConnectionQuery}>
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      First Entity
                    </label>
                    <input
                      type="text"
                      value={entity1}
                      onChange={(e) => setEntity1(e.target.value)}
                      placeholder="Entity 1"
                      className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      Second Entity
                    </label>
                    <input
                      type="text"
                      value={entity2}
                      onChange={(e) => setEntity2(e.target.value)}
                      placeholder="Entity 2"
                      className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>
                <button
                  type="submit"
                  disabled={loading || !entity1.trim() || !entity2.trim()}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                >
                  {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Link2 className="h-4 w-4" />}
                  <span>Find Connection</span>
                </button>
              </div>
            </form>
          )}

          {/* Contradictions Tab */}
          {activeTab === 'contradictions' && (
            <div className="space-y-4">
              <p className="text-slate-600">
                Analyze your document corpus to find potential contradictions or conflicting information.
              </p>
              <button
                onClick={handleFindContradictions}
                disabled={loading}
                className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <AlertTriangle className="h-4 w-4" />}
                <span>Find Contradictions</span>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Results */}
      {result && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="px-6 py-4 bg-slate-50 border-b border-slate-200">
            <h3 className="font-semibold text-slate-800">Results</h3>
          </div>
          <div className="p-6">
            {result.type === 'error' && (
              <div className="text-red-600 bg-red-50 p-4 rounded-lg">
                {result.message}
              </div>
            )}

            {result.type === 'entity' && result.data.success && (
              <div className="space-y-4">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <Users className="h-6 w-6 text-purple-600" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-lg">{result.data.entity?.name}</h4>
                    <p className="text-sm text-slate-500">
                      {result.data.entity?.type} • {result.data.entity?.mention_count} mentions
                    </p>
                  </div>
                </div>
                
                {result.data.summary && (
                  <p className="text-slate-700 bg-slate-50 p-4 rounded-lg">{result.data.summary}</p>
                )}

                {result.data.documents?.length > 0 && (
                  <div>
                    <h5 className="font-medium text-slate-700 mb-2">Found in documents:</h5>
                    <div className="space-y-2">
                      {result.data.documents.map((doc, idx) => (
                        <div key={idx} className="p-3 bg-slate-50 rounded-lg">
                          <p className="text-sm font-medium">{doc.filename}</p>
                          {doc.context && (
                            <p className="text-sm text-slate-500 mt-1">...{doc.context}...</p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {result.data.related_entities?.length > 0 && (
                  <div>
                    <h5 className="font-medium text-slate-700 mb-2">Related entities:</h5>
                    <div className="flex flex-wrap gap-2">
                      {result.data.related_entities.map((rel, idx) => (
                        <span
                          key={idx}
                          className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
                        >
                          {rel.name} ({rel.type})
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {result.type === 'entity' && !result.data.success && (
              <div className="text-slate-600">
                <p>{result.data.message}</p>
                {result.data.suggestions?.length > 0 && (
                  <div className="mt-2">
                    <p className="text-sm">Did you mean:</p>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {result.data.suggestions.map((s, idx) => (
                        <button
                          key={idx}
                          onClick={() => setEntityName(s)}
                          className="px-2 py-1 bg-slate-100 hover:bg-slate-200 rounded text-sm"
                        >
                          {s}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {result.type === 'connection' && result.data.success && (
              <div className="space-y-4">
                <div className="flex items-center justify-center space-x-4">
                  <div className="text-center">
                    <p className="font-semibold">{result.data.entity1?.name}</p>
                    <p className="text-sm text-slate-500">{result.data.entity1?.type}</p>
                  </div>
                  <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                    result.data.connection_strength === 'strong' ? 'bg-green-100 text-green-800' :
                    result.data.connection_strength === 'moderate' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {result.data.connection_strength} connection
                  </div>
                  <div className="text-center">
                    <p className="font-semibold">{result.data.entity2?.name}</p>
                    <p className="text-sm text-slate-500">{result.data.entity2?.type}</p>
                  </div>
                </div>
                
                {result.data.summary && (
                  <p className="text-slate-700 bg-slate-50 p-4 rounded-lg text-center">{result.data.summary}</p>
                )}

                {result.data.shared_documents?.length > 0 && (
                  <div>
                    <h5 className="font-medium text-slate-700 mb-2">Shared documents:</h5>
                    <p className="text-sm text-slate-600">{result.data.shared_documents.length} documents mention both entities</p>
                  </div>
                )}
              </div>
            )}

            {result.type === 'contradictions' && (
              <div className="space-y-4">
                <p className="text-slate-600">
                  Found {result.data.total_flagged} potential items for review
                </p>
                {result.data.potential_contradictions?.map((item, idx) => (
                  <div key={idx} className="p-4 bg-orange-50 border border-orange-200 rounded-lg">
                    <p className="font-medium text-orange-800">{item.entity} ({item.type})</p>
                    <p className="text-sm text-orange-600 mt-1">{item.potential_issue}</p>
                    <p className="text-sm text-slate-500 mt-1">
                      Found in {item.documents?.length} documents
                    </p>
                  </div>
                ))}
              </div>
            )}

            {result.type === 'question' && (
              <div className="space-y-4">
                {result.data.results && Array.isArray(result.data.results) && (
                  <div className="space-y-2">
                    {result.data.results.map((r, idx) => (
                      <div key={idx} className="p-3 bg-slate-50 rounded-lg">
                        <p className="font-medium">{r.filename || r.document_id}</p>
                        {r.relevance && <p className="text-sm text-slate-500">Relevance: {r.relevance}</p>}
                      </div>
                    ))}
                  </div>
                )}
                {result.data.summary && (
                  <p className="text-slate-700 bg-slate-50 p-4 rounded-lg">{result.data.summary}</p>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default Query
