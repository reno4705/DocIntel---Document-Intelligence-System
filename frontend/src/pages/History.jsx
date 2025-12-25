import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { FileText, Eye, Calendar, Trash2, AlertTriangle, RefreshCw, Beaker, Search } from 'lucide-react'
import { getDocuments, getDocumentById, deleteDocument, resetSystem } from '../services/api'
import ResultsView from '../components/ResultsView'

function History() {
  const navigate = useNavigate()
  const [documents, setDocuments] = useState([])
  const [selectedDocument, setSelectedDocument] = useState(null)
  const [loading, setLoading] = useState(true)
  const [loadingDoc, setLoadingDoc] = useState(false)
  const [error, setError] = useState(null)
  const [showResetConfirm, setShowResetConfirm] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  const fetchDocuments = async () => {
    try {
      const data = await getDocuments()
      setDocuments(data)
    } catch (err) {
      setError('Failed to load document history')
    } finally {
      setLoading(false)
    }
  }

  const selectDocument = async (doc) => {
    setLoadingDoc(true)
    try {
      const fullDoc = await getDocumentById(doc.id)
      // Map to expected format for ResultsView
      setSelectedDocument({
        ...fullDoc,
        extracted_text: fullDoc.content,
        text_length: fullDoc.content?.length || 0,
        processing_time: 0
      })
    } catch (err) {
      console.error('Failed to load document:', err)
    } finally {
      setLoadingDoc(false)
    }
  }

  useEffect(() => {
    fetchDocuments()
  }, [])

  const handleDeleteDocument = async (docId, e) => {
    e.stopPropagation()
    if (!confirm('Delete this document?')) return
    
    setDeleting(true)
    try {
      await deleteDocument(docId)
      setDocuments(docs => docs.filter(d => d.id !== docId))
      if (selectedDocument?.id === docId) {
        setSelectedDocument(null)
      }
    } catch (err) {
      alert('Failed to delete document')
    } finally {
      setDeleting(false)
    }
  }

  const handleResetAll = async () => {
    setDeleting(true)
    try {
      await resetSystem()
      setDocuments([])
      setSelectedDocument(null)
      setShowResetConfirm(false)
    } catch (err) {
      alert('Failed to reset system')
    } finally {
      setDeleting(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-12 text-red-500">
        <p>{error}</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Document History</h1>
          <p className="text-slate-500">View all previously processed documents</p>
        </div>
        {documents.length > 0 && (
          <button
            onClick={() => setShowResetConfirm(true)}
            className="flex items-center space-x-2 px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors"
          >
            <Trash2 className="h-4 w-4" />
            <span>Delete All</span>
          </button>
        )}
      </div>

      {/* Reset Confirmation Modal */}
      {showResetConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md mx-4 shadow-xl">
            <div className="flex items-center space-x-3 text-red-600 mb-4">
              <AlertTriangle className="h-6 w-6" />
              <h3 className="font-semibold text-lg">Delete All Data?</h3>
            </div>
            <p className="text-slate-600 mb-6">
              This will permanently delete all {documents.length} documents, the knowledge graph, and all extracted data. This cannot be undone.
            </p>
            <div className="flex space-x-3 justify-end">
              <button
                onClick={() => setShowResetConfirm(false)}
                className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg"
                disabled={deleting}
              >
                Cancel
              </button>
              <button
                onClick={handleResetAll}
                disabled={deleting}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 flex items-center space-x-2"
              >
                {deleting ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
                <span>{deleting ? 'Deleting...' : 'Delete All'}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {documents.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-12 text-center">
          <FileText className="h-16 w-16 mx-auto text-slate-300 mb-4" />
          <h3 className="text-lg font-medium text-slate-600">No documents yet</h3>
          <p className="text-slate-400 mt-1">Upload your first document to get started</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1 space-y-3">
            {/* Search Bar */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search documents..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              />
            </div>
            <p className="text-sm font-medium text-slate-500 px-1">
              {documents.filter(d => d.filename.toLowerCase().includes(searchQuery.toLowerCase())).length} of {documents.length} document{documents.length !== 1 ? 's' : ''}
            </p>
            {documents.filter(d => d.filename.toLowerCase().includes(searchQuery.toLowerCase())).map((doc) => (
              <div
                key={doc.id}
                onClick={() => navigate(`/document/${doc.id}`)}
                className={`bg-white rounded-xl shadow-sm border p-4 cursor-pointer transition-all ${
                  selectedDocument?.id === doc.id
                    ? 'border-blue-500 ring-2 ring-blue-100'
                    : 'border-slate-200 hover:border-slate-300'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="p-2 bg-slate-100 rounded-lg">
                      <FileText className="h-5 w-5 text-slate-600" />
                    </div>
                    <div>
                      <p className="font-medium text-slate-800 truncate max-w-[150px]">
                        {doc.filename}
                      </p>
                      <p className="text-xs text-slate-500">{doc.entity_count || 0} entities</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-1">
                    <button
                      onClick={(e) => { e.stopPropagation(); navigate(`/document/${doc.id}`) }}
                      className="p-1 text-slate-400 hover:text-purple-500 hover:bg-purple-50 rounded transition-colors"
                      title="Analyze document"
                    >
                      <Beaker className="h-4 w-4" />
                    </button>
                    <button
                      onClick={(e) => handleDeleteDocument(doc.id, e)}
                      className="p-1 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors"
                      title="Delete document"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
                <div className="mt-3 flex items-center space-x-4 text-xs text-slate-500">
                  <span className="flex items-center space-x-1">
                    <Calendar className="h-3 w-3" />
                    <span>{new Date(doc.upload_date).toLocaleDateString()}</span>
                  </span>
                  <span>{doc.word_count || 0} words</span>
                </div>
              </div>
            ))}
          </div>

          <div className="lg:col-span-2">
            {loadingDoc ? (
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-12 text-center h-full flex flex-col items-center justify-center">
                <RefreshCw className="h-12 w-12 text-blue-500 mb-4 animate-spin" />
                <h3 className="text-lg font-medium text-slate-600">Loading document...</h3>
              </div>
            ) : selectedDocument ? (
              <ResultsView document={selectedDocument} />
            ) : (
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-12 text-center h-full flex flex-col items-center justify-center">
                <Eye className="h-16 w-16 text-slate-300 mb-4" />
                <h3 className="text-lg font-medium text-slate-600">Select a document</h3>
                <p className="text-slate-400 mt-1">Click on a document to view its details</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default History
