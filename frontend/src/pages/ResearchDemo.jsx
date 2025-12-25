import { useState, useEffect } from 'react'
import { 
  Brain, Users, Calendar, FileSearch, MessageSquare, RefreshCw, 
  ChevronRight, AlertTriangle, CheckCircle, Clock, Building,
  Beaker, FileText, User, Target, Lightbulb, Send, Loader2,
  Quote, Link, Shield, TrendingUp, Eye, Flag
} from 'lucide-react'
import { getGroqStatus, getAccountabilityTrail, askQuestionAI } from '../services/api'

function ResearchDemo() {
  const [aiStatus, setAiStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [trailLoading, setTrailLoading] = useState(false)
  const [trail, setTrail] = useState(null)
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState(null)
  const [askingQuestion, setAskingQuestion] = useState(false)
  const [activeTab, setActiveTab] = useState('accountability')

  useEffect(() => {
    checkStatus()
  }, [])

  const checkStatus = async () => {
    try {
      const status = await getGroqStatus()
      setAiStatus(status)
    } catch (error) {
      console.error('Failed to check AI status:', error)
      setAiStatus({ available: false })
    } finally {
      setLoading(false)
    }
  }

  const loadAccountabilityTrail = async () => {
    setTrailLoading(true)
    try {
      const result = await getAccountabilityTrail(15)
      setTrail(result)
    } catch (error) {
      console.error('Failed to load trail:', error)
      setTrail({ error: error.message })
    } finally {
      setTrailLoading(false)
    }
  }

  const handleAskQuestion = async () => {
    if (!question.trim()) return
    
    setAskingQuestion(true)
    setAnswer(null)
    try {
      const result = await askQuestionAI(question)
      setAnswer(result)
    } catch (error) {
      console.error('Failed to ask question:', error)
      setAnswer({ error: error.message })
    } finally {
      setAskingQuestion(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-purple-500" />
        <span className="ml-3 text-slate-600">Checking AI status...</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-indigo-600 rounded-2xl p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold flex items-center space-x-3">
              <Brain className="h-8 w-8" />
              <span>Corporate Document Forensics</span>
            </h1>
            <p className="mt-2 text-purple-100">
              AI-powered analysis of corporate research archives
            </p>
          </div>
          <div className="flex items-center space-x-2">
            {aiStatus?.available ? (
              <span className="flex items-center px-3 py-1 bg-green-500/20 rounded-full text-green-100">
                <CheckCircle className="h-4 w-4 mr-2" />
                Groq AI Active
              </span>
            ) : (
              <span className="flex items-center px-3 py-1 bg-red-500/20 rounded-full text-red-100">
                <AlertTriangle className="h-4 w-4 mr-2" />
                AI Unavailable
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Problem Statement */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <h2 className="font-bold text-lg text-slate-800 mb-3">Research Problem Statement</h2>
        <p className="text-slate-600 leading-relaxed">
          <strong className="text-purple-700">Automated Forensic Analysis of Corporate Research Archives:</strong> When 
          organizations face investigations, auditors must manually review thousands of documents to answer critical 
          questions like <em>"Who knew what, and when did they know it?"</em> This system uses AI to automatically 
          extract research activities, stakeholder roles, decisions, and build accountability timelines from 
          unstructured document archives.
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200">
        <nav className="flex space-x-8">
          <button
            onClick={() => setActiveTab('accountability')}
            className={`flex items-center space-x-2 py-3 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'accountability'
                ? 'border-purple-600 text-purple-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <Users className="h-4 w-4" />
            <span>Accountability Trail</span>
          </button>
          <button
            onClick={() => setActiveTab('qa')}
            className={`flex items-center space-x-2 py-3 border-b-2 font-medium text-sm transition-colors ${
              activeTab === 'qa'
                ? 'border-purple-600 text-purple-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <MessageSquare className="h-4 w-4" />
            <span>Document Q&A</span>
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'accountability' && (
        <AccountabilityTab 
          trail={trail} 
          loading={trailLoading} 
          onLoad={loadAccountabilityTrail}
          aiAvailable={aiStatus?.available}
        />
      )}
      {activeTab === 'qa' && (
        <QATab 
          question={question}
          setQuestion={setQuestion}
          answer={answer}
          loading={askingQuestion}
          onAsk={handleAskQuestion}
          aiAvailable={aiStatus?.available}
        />
      )}
    </div>
  )
}

function AccountabilityTab({ trail, loading, onLoad, aiAvailable }) {
  if (!aiAvailable) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6 text-center">
        <AlertTriangle className="h-12 w-12 mx-auto text-yellow-500 mb-3" />
        <h3 className="font-semibold text-yellow-800">AI Service Not Available</h3>
        <p className="text-yellow-700 mt-1">Add GROQ_API_KEY to backend/.env to enable AI analysis</p>
      </div>
    )
  }

  if (!trail && !loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border p-8 text-center">
        <Users className="h-16 w-16 mx-auto text-purple-300 mb-4" />
        <h3 className="text-xl font-semibold text-slate-700 mb-2">Build Accountability Trail</h3>
        <p className="text-slate-500 mb-6 max-w-md mx-auto">
          Analyze documents to extract key actors, timeline of events, and answer 
          "Who knew what, and when did they know it?"
        </p>
        <button
          onClick={onLoad}
          className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 font-medium flex items-center space-x-2 mx-auto"
        >
          <Brain className="h-5 w-5" />
          <span>Analyze Documents</span>
        </button>
        <p className="text-xs text-slate-400 mt-3">This may take 30-60 seconds</p>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border p-8 text-center">
        <Loader2 className="h-12 w-12 mx-auto text-purple-500 animate-spin mb-4" />
        <h3 className="text-lg font-semibold text-slate-700">Analyzing Documents...</h3>
        <p className="text-slate-500 mt-2">Building accountability trail with AI</p>
        <p className="text-xs text-slate-400 mt-4">Analyzing research activities, stakeholders, and timelines</p>
      </div>
    )
  }

  if (trail?.error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-6">
        <AlertTriangle className="h-8 w-8 text-red-500 mb-2" />
        <h3 className="font-semibold text-red-800">Analysis Failed</h3>
        <p className="text-red-600">{trail.error}</p>
        <button onClick={onLoad} className="mt-4 px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200">
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Executive Summary */}
      {(trail?.executive_summary || trail?.summary) && (
        <div className="bg-gradient-to-r from-purple-600 to-indigo-600 rounded-xl p-6 text-white">
          <h3 className="font-semibold text-lg mb-2 flex items-center space-x-2">
            <Brain className="h-5 w-5" />
            <span>Executive Summary</span>
          </h3>
          <p className="text-purple-100 leading-relaxed">{trail.executive_summary || trail.summary}</p>
        </div>
      )}

      {/* Red Flags - Show prominently if any */}
      {trail?.red_flags?.length > 0 && (
        <div className="bg-red-50 rounded-xl border-2 border-red-200 p-6">
          <h3 className="font-semibold text-red-800 mb-4 flex items-center space-x-2">
            <Flag className="h-5 w-5 text-red-500" />
            <span>Red Flags Detected ({trail.red_flags.length})</span>
          </h3>
          <div className="space-y-3">
            {trail.red_flags.map((flag, idx) => (
              <div key={idx} className={`p-4 rounded-lg border ${
                flag.severity === 'critical' ? 'bg-red-100 border-red-300' :
                flag.severity === 'high' ? 'bg-orange-50 border-orange-200' :
                'bg-yellow-50 border-yellow-200'
              }`}>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="font-medium text-slate-800">{flag.issue}</p>
                    {flag.evidence && (
                      <p className="text-sm text-slate-600 mt-2 italic border-l-2 border-slate-300 pl-3">
                        "{flag.evidence}"
                      </p>
                    )}
                    {flag.actors_implicated?.length > 0 && (
                      <p className="text-xs text-slate-500 mt-2">
                        Implicated: {flag.actors_implicated.join(', ')}
                      </p>
                    )}
                  </div>
                  <span className={`px-2 py-1 text-xs font-bold rounded ${
                    flag.severity === 'critical' ? 'bg-red-600 text-white' :
                    flag.severity === 'high' ? 'bg-orange-500 text-white' :
                    'bg-yellow-500 text-white'
                  }`}>
                    {flag.severity?.toUpperCase()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Key Actors - Enhanced */}
      {trail?.key_actors?.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="font-semibold text-slate-800 mb-4 flex items-center space-x-2">
            <Users className="h-5 w-5 text-purple-500" />
            <span>Key Actors ({trail.key_actors.length})</span>
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {trail.key_actors.map((actor, idx) => (
              <div key={idx} className="border border-slate-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex items-start space-x-3">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-bold flex-shrink-0 ${
                    actor.accountability_level === 'high' ? 'bg-red-500' :
                    actor.accountability_level === 'medium' ? 'bg-orange-500' :
                    'bg-purple-500'
                  }`}>
                    {actor.name?.charAt(0) || '?'}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <h4 className="font-semibold text-slate-800">{actor.name}</h4>
                      {actor.accountability_level && (
                        <span className={`px-2 py-0.5 text-xs rounded ${
                          actor.accountability_level === 'high' ? 'bg-red-100 text-red-700' :
                          actor.accountability_level === 'medium' ? 'bg-orange-100 text-orange-700' :
                          'bg-slate-100 text-slate-600'
                        }`}>
                          {actor.accountability_level} accountability
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-purple-600">{actor.role}</p>
                    {actor.involvement_summary && (
                      <p className="mt-2 text-sm text-slate-600">{actor.involvement_summary}</p>
                    )}
                    {actor.key_actions?.length > 0 && (
                      <div className="mt-2">
                        <p className="text-xs text-slate-500">Key Actions:</p>
                        <ul className="text-xs text-slate-600 mt-1 space-y-1">
                          {actor.key_actions.slice(0, 3).map((action, i) => (
                            <li key={i} className="flex items-start space-x-1">
                              <ChevronRight className="h-3 w-3 mt-0.5 text-purple-400" />
                              <span>{action}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {actor.evidence_strength && (
                      <p className="mt-2 text-xs text-slate-500">
                        Evidence: <span className="font-medium">{actor.evidence_strength}</span>
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Actor Relationships */}
      {trail?.actor_relationships?.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="font-semibold text-slate-800 mb-4 flex items-center space-x-2">
            <Link className="h-5 w-5 text-indigo-500" />
            <span>Relationship Map</span>
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {trail.actor_relationships.map((rel, idx) => (
              <div key={idx} className="flex items-center space-x-2 p-3 bg-indigo-50 rounded-lg border border-indigo-200">
                <span className="font-medium text-indigo-800">{rel.from}</span>
                <span className="px-2 py-0.5 bg-indigo-200 text-indigo-700 text-xs rounded">
                  {rel.relationship?.replace('_', ' ')}
                </span>
                <span className="font-medium text-indigo-800">{rel.to}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Evidence Summary */}
      {trail?.evidence_summary?.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="font-semibold text-slate-800 mb-4 flex items-center space-x-2">
            <Quote className="h-5 w-5 text-green-500" />
            <span>Key Evidence ({trail.evidence_summary.length})</span>
          </h3>
          <div className="space-y-4">
            {trail.evidence_summary.map((ev, idx) => (
              <div key={idx} className="border-l-4 border-green-400 pl-4 py-2">
                <p className="font-medium text-slate-800">{ev.claim}</p>
                {ev.key_quote && (
                  <p className="text-sm text-slate-600 mt-2 italic bg-green-50 p-2 rounded">
                    "{ev.key_quote}"
                  </p>
                )}
                <div className="flex items-center justify-between mt-2">
                  <p className="text-xs text-slate-500">
                    Sources: {ev.supporting_documents?.join(', ')}
                  </p>
                  {ev.confidence && (
                    <span className={`px-2 py-0.5 text-xs rounded ${
                      ev.confidence === 'high' ? 'bg-green-100 text-green-700' :
                      ev.confidence === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-slate-100 text-slate-600'
                    }`}>
                      {ev.confidence} confidence
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Timeline - Enhanced */}
      {trail?.timeline?.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="font-semibold text-slate-800 mb-4 flex items-center space-x-2">
            <Calendar className="h-5 w-5 text-blue-500" />
            <span>Timeline ({trail.timeline.length} events)</span>
          </h3>
          <div className="relative">
            <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-blue-200"></div>
            <div className="space-y-4">
              {trail.timeline.map((event, idx) => (
                <div key={idx} className="relative pl-10">
                  <div className="absolute left-2 w-4 h-4 bg-blue-500 rounded-full border-2 border-white shadow"></div>
                  <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                    <div className="flex items-center justify-between mb-2">
                      <span className="px-2 py-1 bg-blue-600 text-white text-xs font-medium rounded">
                        {event.date}
                      </span>
                      {event.source_document && (
                        <span className="text-xs text-slate-500">{event.source_document}</span>
                      )}
                    </div>
                    <p className="text-slate-800 font-medium">{event.event}</p>
                    {event.significance && (
                      <p className="text-sm text-blue-700 mt-1">{event.significance}</p>
                    )}
                    {event.evidence_quote && (
                      <p className="text-xs text-slate-600 mt-2 italic border-l-2 border-blue-300 pl-2">
                        "{event.evidence_quote}"
                      </p>
                    )}
                    {event.actors_involved?.length > 0 && (
                      <p className="text-xs text-slate-500 mt-2">
                        Involved: {event.actors_involved.join(', ')}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Causal Chain */}
      {trail?.causal_chain?.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="font-semibold text-slate-800 mb-4 flex items-center space-x-2">
            <TrendingUp className="h-5 w-5 text-purple-500" />
            <span>Causal Connections</span>
          </h3>
          <div className="space-y-3">
            {trail.causal_chain.map((chain, idx) => (
              <div key={idx} className="flex items-center space-x-3 p-3 bg-purple-50 rounded-lg border border-purple-200">
                <div className="flex-1">
                  <p className="text-sm text-slate-700">{chain.cause}</p>
                </div>
                <div className={`px-2 py-1 text-xs rounded ${
                  chain.connection_strength === 'direct' ? 'bg-purple-600 text-white' :
                  chain.connection_strength === 'indirect' ? 'bg-purple-400 text-white' :
                  'bg-purple-200 text-purple-700'
                }`}>
                  {chain.connection_strength}
                </div>
                <ChevronRight className="h-5 w-5 text-purple-400" />
                <div className="flex-1">
                  <p className="text-sm text-slate-700">{chain.effect}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Knowledge Timeline */}
      {trail?.knowledge_timeline?.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="font-semibold text-slate-800 mb-4 flex items-center space-x-2">
            <Eye className="h-5 w-5 text-amber-500" />
            <span>Who Knew What & When</span>
          </h3>
          <div className="space-y-3">
            {trail.knowledge_timeline.map((item, idx) => (
              <div key={idx} className="p-4 bg-amber-50 rounded-lg border border-amber-200">
                <div className="flex items-center space-x-2 mb-2">
                  <span className="px-2 py-1 bg-amber-500 text-white text-xs font-medium rounded">
                    {item.date}
                  </span>
                  <span className="text-sm font-medium text-amber-800">
                    {item.who_knew?.join(', ')}
                  </span>
                </div>
                <p className="text-slate-700">{item.what_they_knew}</p>
                <p className="text-xs text-slate-500 mt-1">Source: {item.source}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Patterns Detected */}
      {trail?.patterns_detected?.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="font-semibold text-slate-800 mb-4 flex items-center space-x-2">
            <Target className="h-5 w-5 text-orange-500" />
            <span>Patterns Detected</span>
          </h3>
          <div className="space-y-4">
            {trail.patterns_detected.map((pattern, idx) => (
              <div key={idx} className="p-4 bg-orange-50 rounded-lg border border-orange-200">
                <p className="font-medium text-orange-800">{pattern.pattern}</p>
                {pattern.instances?.length > 0 && (
                  <ul className="mt-2 space-y-1">
                    {pattern.instances.map((inst, i) => (
                      <li key={i} className="text-sm text-slate-600 flex items-start space-x-2">
                        <ChevronRight className="h-4 w-4 text-orange-400 mt-0.5" />
                        <span>{inst}</span>
                      </li>
                    ))}
                  </ul>
                )}
                {pattern.significance && (
                  <p className="text-sm text-orange-700 mt-2 italic">{pattern.significance}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Legacy patterns support */}
      {trail?.patterns?.length > 0 && !trail?.patterns_detected && (
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="font-semibold text-slate-800 mb-4 flex items-center space-x-2">
            <Target className="h-5 w-5 text-orange-500" />
            <span>Patterns Identified</span>
          </h3>
          <ul className="space-y-2">
            {trail.patterns.map((pattern, idx) => (
              <li key={idx} className="flex items-start space-x-2 p-3 bg-orange-50 rounded-lg border border-orange-200">
                <AlertTriangle className="h-5 w-5 text-orange-500 flex-shrink-0 mt-0.5" />
                <span className="text-slate-700">{pattern}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Recommendations */}
      {trail?.recommendations?.length > 0 && (
        <div className="bg-slate-800 rounded-xl p-6 text-white">
          <h3 className="font-semibold mb-4 flex items-center space-x-2">
            <Shield className="h-5 w-5 text-green-400" />
            <span>Recommended Follow-up Actions</span>
          </h3>
          <ul className="space-y-2">
            {trail.recommendations.map((rec, idx) => (
              <li key={idx} className="flex items-start space-x-2">
                <CheckCircle className="h-5 w-5 text-green-400 flex-shrink-0 mt-0.5" />
                <span className="text-slate-200">{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Reload button */}
      <div className="text-center">
        <button
          onClick={onLoad}
          className="px-4 py-2 text-purple-600 hover:bg-purple-50 rounded-lg font-medium flex items-center space-x-2 mx-auto"
        >
          <RefreshCw className="h-4 w-4" />
          <span>Re-analyze</span>
        </button>
      </div>
    </div>
  )
}

function QATab({ question, setQuestion, answer, loading, onAsk, aiAvailable }) {
  if (!aiAvailable) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6 text-center">
        <AlertTriangle className="h-12 w-12 mx-auto text-yellow-500 mb-3" />
        <h3 className="font-semibold text-yellow-800">AI Service Not Available</h3>
        <p className="text-yellow-700 mt-1">Add GROQ_API_KEY to backend/.env to enable Q&A</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Question Input */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <h3 className="font-semibold text-slate-800 mb-4 flex items-center space-x-2">
          <MessageSquare className="h-5 w-5 text-purple-500" />
          <span>Ask About Your Documents</span>
        </h3>
        <div className="flex space-x-3">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && onAsk()}
            placeholder="e.g., What toxicity tests were conducted? Who approved the studies?"
            className="flex-1 px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
          />
          <button
            onClick={onAsk}
            disabled={loading || !question.trim()}
            className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            {loading ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <Send className="h-5 w-5" />
            )}
            <span>Ask</span>
          </button>
        </div>
        <p className="text-xs text-slate-400 mt-2">
          The AI will search through all documents to find relevant answers with citations
        </p>
      </div>

      {/* Sample Questions */}
      <div className="bg-slate-50 rounded-xl p-4">
        <p className="text-sm font-medium text-slate-600 mb-2">Try these questions:</p>
        <div className="flex flex-wrap gap-2">
          {[
            "What compounds were tested?",
            "Who conducted the toxicity studies?",
            "When were the safety tests performed?",
            "What were the results of the research?",
          ].map((q, idx) => (
            <button
              key={idx}
              onClick={() => setQuestion(q)}
              className="px-3 py-1 bg-white border border-slate-200 rounded-full text-sm text-slate-600 hover:bg-purple-50 hover:border-purple-200 hover:text-purple-700"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      {/* Answer */}
      {answer && (
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="font-semibold text-slate-800 mb-4 flex items-center space-x-2">
            <Lightbulb className="h-5 w-5 text-green-500" />
            <span>Answer</span>
          </h3>
          
          {answer.error ? (
            <div className="bg-red-50 text-red-700 p-4 rounded-lg">
              {answer.error}
            </div>
          ) : (
            <>
              <p className="text-slate-700 leading-relaxed">{answer.answer}</p>
              
              {answer.confidence && (
                <p className="mt-3 text-sm">
                  <span className="text-slate-500">Confidence: </span>
                  <span className={`font-medium ${
                    answer.confidence === 'high' ? 'text-green-600' :
                    answer.confidence === 'medium' ? 'text-yellow-600' : 'text-red-600'
                  }`}>
                    {answer.confidence}
                  </span>
                </p>
              )}

              {answer.citations?.length > 0 && (
                <div className="mt-4 pt-4 border-t border-slate-200">
                  <h4 className="text-sm font-medium text-slate-600 mb-2">Sources:</h4>
                  <div className="space-y-2">
                    {answer.citations.map((cite, idx) => (
                      <div key={idx} className="p-3 bg-slate-50 rounded-lg text-sm">
                        <p className="font-medium text-slate-700">{cite.document}</p>
                        {cite.relevant_text && (
                          <p className="text-slate-500 mt-1 italic">"{cite.relevant_text}"</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}

export default ResearchDemo
