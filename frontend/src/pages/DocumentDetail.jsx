import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { 
  FileText, ArrowLeft, Calendar, Building, Users, Beaker, 
  CheckCircle, Lightbulb, Clock, RefreshCw, Loader2, 
  FileSearch, AlertTriangle, Target, Hash
} from 'lucide-react'
import { getDocumentById, analyzeDocumentAI } from '../services/api'

function DocumentDetail() {
  const { docId } = useParams()
  const navigate = useNavigate()
  const [document, setDocument] = useState(null)
  const [analysis, setAnalysis] = useState(null)
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadDocument()
  }, [docId])

  const loadDocument = async () => {
    setLoading(true)
    try {
      const doc = await getDocumentById(docId)
      setDocument(doc)
      // Check if we have cached analysis
      if (doc.ai_analysis) {
        setAnalysis(doc.ai_analysis)
      }
    } catch (err) {
      setError('Failed to load document')
    } finally {
      setLoading(false)
    }
  }

  const runAnalysis = async () => {
    setAnalyzing(true)
    try {
      const result = await analyzeDocumentAI(docId)
      setAnalysis(result)
    } catch (err) {
      setError('Analysis failed: ' + err.message)
    } finally {
      setAnalyzing(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-500" />
        <span className="ml-3 text-slate-600">Loading document...</span>
      </div>
    )
  }

  if (error && !document) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
        <AlertTriangle className="h-12 w-12 mx-auto text-red-500 mb-3" />
        <p className="text-red-700">{error}</p>
        <button onClick={() => navigate('/history')} className="mt-4 text-blue-600 hover:underline">
          Back to Documents
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button 
            onClick={() => navigate('/history')}
            className="p-2 hover:bg-slate-100 rounded-lg"
          >
            <ArrowLeft className="h-5 w-5 text-slate-600" />
          </button>
          <div>
            <h1 className="text-xl font-bold text-slate-800 flex items-center space-x-2">
              <FileText className="h-6 w-6 text-blue-500" />
              <span>{document?.filename}</span>
            </h1>
            <p className="text-sm text-slate-500">
              Uploaded: {new Date(document?.upload_date).toLocaleString()}
            </p>
          </div>
        </div>
        
        {!analysis && (
          <button
            onClick={runAnalysis}
            disabled={analyzing}
            className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
          >
            {analyzing ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Analyzing...</span>
              </>
            ) : (
              <>
                <Beaker className="h-4 w-4" />
                <span>Analyze with AI</span>
              </>
            )}
          </button>
        )}
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Left: Original Content */}
        <div className="col-span-1">
          <div className="bg-white rounded-xl shadow-sm border p-4">
            <h3 className="font-semibold text-slate-700 mb-3 flex items-center space-x-2">
              <FileSearch className="h-4 w-4" />
              <span>Extracted Text</span>
            </h3>
            <div className="bg-slate-50 rounded-lg p-4 max-h-[600px] overflow-y-auto">
              <pre className="text-xs text-slate-600 whitespace-pre-wrap font-mono">
                {document?.content}
              </pre>
            </div>
            <div className="mt-3 text-xs text-slate-400">
              {document?.word_count} words • {document?.file_type}
            </div>
          </div>
        </div>

        {/* Right: Structured Analysis */}
        <div className="col-span-2 space-y-4">
          {analyzing && (
            <div className="bg-purple-50 border border-purple-200 rounded-xl p-8 text-center">
              <Loader2 className="h-12 w-12 mx-auto text-purple-500 animate-spin mb-4" />
              <h3 className="text-lg font-semibold text-purple-800">Analyzing Document...</h3>
              <p className="text-purple-600 mt-2">Extracting key information with AI</p>
            </div>
          )}

          {analysis && !analyzing && (
            <>
              {/* Document Overview */}
              <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-200">
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <p className="text-xs text-blue-600 font-medium">Document Type</p>
                    <p className="text-lg font-bold text-slate-800 capitalize">
                      {analysis.document_type?.replace('_', ' ') || 'Unknown'}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-blue-600 font-medium">Date</p>
                    <p className="text-lg font-bold text-slate-800">
                      {analysis.date || 'Not specified'}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-blue-600 font-medium">Organization</p>
                    <p className="text-lg font-bold text-slate-800">
                      {analysis.organization || 'Not specified'}
                    </p>
                  </div>
                </div>
                {analysis.title && (
                  <div className="mt-4 pt-4 border-t border-blue-200">
                    <p className="text-xs text-blue-600 font-medium">Title/Subject</p>
                    <p className="text-slate-800 font-medium">{analysis.title}</p>
                  </div>
                )}
              </div>

              {/* Key People */}
              {analysis.stakeholders?.length > 0 && (
                <div className="bg-white rounded-xl shadow-sm border p-5">
                  <h3 className="font-semibold text-slate-800 mb-3 flex items-center space-x-2">
                    <Users className="h-5 w-5 text-purple-500" />
                    <span>Key People</span>
                  </h3>
                  <div className="grid grid-cols-2 gap-3">
                    {analysis.stakeholders.map((person, idx) => (
                      <div key={idx} className="flex items-center space-x-3 p-3 bg-slate-50 rounded-lg">
                        <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center text-purple-700 font-bold text-sm">
                          {person.name?.charAt(0) || '?'}
                        </div>
                        <div>
                          <p className="font-medium text-slate-800 text-sm">{person.name}</p>
                          <p className="text-xs text-slate-500">{person.role}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Research Activity */}
              {analysis.research_activity?.study_name && (
                <div className="bg-white rounded-xl shadow-sm border p-5">
                  <h3 className="font-semibold text-slate-800 mb-3 flex items-center space-x-2">
                    <Beaker className="h-5 w-5 text-green-500" />
                    <span>Research Activity</span>
                  </h3>
                  <div className="space-y-3">
                    <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                      <p className="font-medium text-green-800">{analysis.research_activity.study_name}</p>
                      {analysis.research_activity.study_type && (
                        <p className="text-sm text-green-600 mt-1">Type: {analysis.research_activity.study_type}</p>
                      )}
                      {analysis.research_activity.compounds_tested?.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {analysis.research_activity.compounds_tested.map((c, i) => (
                            <span key={i} className="px-2 py-0.5 bg-green-200 text-green-800 text-xs rounded">
                              {c}
                            </span>
                          ))}
                        </div>
                      )}
                      {analysis.research_activity.status && (
                        <p className="text-xs text-green-600 mt-2">Status: {analysis.research_activity.status}</p>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Decisions */}
              {analysis.decisions?.length > 0 && (
                <div className="bg-white rounded-xl shadow-sm border p-5">
                  <h3 className="font-semibold text-slate-800 mb-3 flex items-center space-x-2">
                    <Target className="h-5 w-5 text-orange-500" />
                    <span>Decisions & Approvals</span>
                  </h3>
                  <div className="space-y-2">
                    {analysis.decisions.map((dec, idx) => (
                      <div key={idx} className="p-3 bg-orange-50 rounded-lg border border-orange-200">
                        <p className="text-slate-700">{dec.decision}</p>
                        {dec.decision_maker && (
                          <p className="text-xs text-orange-600 mt-1">By: {dec.decision_maker}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Findings */}
              {analysis.findings?.length > 0 && (
                <div className="bg-white rounded-xl shadow-sm border p-5">
                  <h3 className="font-semibold text-slate-800 mb-3 flex items-center space-x-2">
                    <Lightbulb className="h-5 w-5 text-yellow-500" />
                    <span>Key Findings</span>
                  </h3>
                  <div className="space-y-2">
                    {analysis.findings.map((f, idx) => (
                      <div key={idx} className="p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                        <p className="text-slate-700">{f.finding}</p>
                        {f.significance && (
                          <p className="text-xs text-yellow-700 mt-1 italic">{f.significance}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Timeline Events */}
              {analysis.timeline_events?.length > 0 && (
                <div className="bg-white rounded-xl shadow-sm border p-5">
                  <h3 className="font-semibold text-slate-800 mb-3 flex items-center space-x-2">
                    <Clock className="h-5 w-5 text-blue-500" />
                    <span>Timeline Events</span>
                  </h3>
                  <div className="space-y-2">
                    {analysis.timeline_events.map((event, idx) => (
                      <div key={idx} className="flex items-center space-x-3 p-2 bg-slate-50 rounded">
                        <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded">
                          {event.date}
                        </span>
                        <span className="text-sm text-slate-700">{event.event}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Key Facts */}
              {analysis.key_facts?.length > 0 && (
                <div className="bg-white rounded-xl shadow-sm border p-5">
                  <h3 className="font-semibold text-slate-800 mb-3 flex items-center space-x-2">
                    <Hash className="h-5 w-5 text-slate-500" />
                    <span>Key Facts</span>
                  </h3>
                  <ul className="space-y-1">
                    {analysis.key_facts.map((fact, idx) => (
                      <li key={idx} className="flex items-start space-x-2 text-sm text-slate-600">
                        <CheckCircle className="h-4 w-4 text-green-500 flex-shrink-0 mt-0.5" />
                        <span>{fact}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Re-analyze button */}
              <div className="text-center pt-4">
                <button
                  onClick={runAnalysis}
                  disabled={analyzing}
                  className="text-purple-600 hover:text-purple-700 text-sm flex items-center space-x-1 mx-auto"
                >
                  <RefreshCw className="h-4 w-4" />
                  <span>Re-analyze</span>
                </button>
              </div>
            </>
          )}

          {!analysis && !analyzing && (
            <div className="bg-slate-50 rounded-xl p-8 text-center border-2 border-dashed border-slate-300">
              <Beaker className="h-16 w-16 mx-auto text-slate-300 mb-4" />
              <h3 className="text-lg font-semibold text-slate-600">No Analysis Yet</h3>
              <p className="text-slate-500 mt-2 max-w-md mx-auto">
                Click "Analyze with AI" to extract structured information from this document
              </p>
              <button
                onClick={runAnalysis}
                className="mt-4 px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
              >
                Analyze Document
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default DocumentDetail
