import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Document endpoints
export const uploadDocument = async (file) => {
  const formData = new FormData()
  formData.append('file', file)
  
  const response = await apiClient.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

export const uploadDocumentsBatch = async (files) => {
  const formData = new FormData()
  files.forEach(file => {
    formData.append('files', file)
  })
  
  const response = await apiClient.post('/upload/batch', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

export const getDocuments = async () => {
  const response = await apiClient.get('/documents')
  return response.data
}

export const getDocumentById = async (docId) => {
  const response = await apiClient.get(`/documents/${docId}`)
  return response.data
}

export const getDocumentInsights = async (id) => {
  const response = await apiClient.get(`/documents/${id}/insights`)
  return response.data
}

export const deleteDocument = async (id) => {
  const response = await apiClient.delete(`/documents/${id}`)
  return response.data
}

// Knowledge Graph endpoints
export const getKnowledgeGraph = async () => {
  const response = await apiClient.get('/knowledge-graph')
  return response.data
}

export const getGraphStats = async () => {
  const response = await apiClient.get('/knowledge-graph/stats')
  return response.data
}

// Query/Reasoning endpoints
export const queryEntity = async (entityName) => {
  const response = await apiClient.get(`/query/entity/${encodeURIComponent(entityName)}`)
  return response.data
}

export const queryConnection = async (entity1, entity2) => {
  const response = await apiClient.get(`/query/connection?entity1=${encodeURIComponent(entity1)}&entity2=${encodeURIComponent(entity2)}`)
  return response.data
}

export const queryEntitiesByType = async (entityType) => {
  const response = await apiClient.get(`/query/entities/${entityType}`)
  return response.data
}

export const askQuestion = async (question) => {
  const response = await apiClient.post('/query/ask', { question })
  return response.data
}

export const findContradictions = async () => {
  const response = await apiClient.get('/query/contradictions')
  return response.data
}

// Search endpoints
export const searchDocuments = async (query, maxResults = 10) => {
  const response = await apiClient.get(`/search?q=${encodeURIComponent(query)}&max_results=${maxResults}`)
  return response.data
}

// Overview endpoints
export const getCorpusOverview = async () => {
  const response = await apiClient.get('/overview')
  return response.data
}

export const getStats = async () => {
  const response = await apiClient.get('/stats')
  return response.data
}

export const healthCheck = async () => {
  const response = await apiClient.get('/health')
  return response.data
}

export const resetSystem = async () => {
  const response = await apiClient.delete('/reset')
  return response.data
}

// AI Chat endpoints (using Groq)
export const chatWithDocuments = async (message, sessionId = 'default') => {
  const response = await apiClient.post('/ai/chat', { message, session_id: sessionId })
  return response.data
}

export const extractInformation = async (documentId = null, text = null, customFields = null) => {
  const response = await apiClient.post('/ai/extract-document', { 
    document_id: documentId
  })
  return response.data
}

export const analyzeDocuments = async (documentIds = null, analysisType = 'summary') => {
  const response = await apiClient.post('/analyze', { 
    document_ids: documentIds, 
    analysis_type: analysisType 
  })
  return response.data
}

export const getChatHistory = async (sessionId = 'default') => {
  const response = await apiClient.get(`/chat/history/${sessionId}`)
  return response.data
}

export const clearChatHistory = async (sessionId = 'default') => {
  const response = await apiClient.delete(`/chat/history/${sessionId}`)
  return response.data
}

export const getAIStatus = async () => {
  const response = await apiClient.get('/ai/groq/status')
  return response.data
}

// Intelligence endpoints
export const getCorpusIntelligence = async () => {
  const response = await apiClient.get('/intelligence/corpus')
  return response.data
}

export const getDocumentIntelligence = async (docId) => {
  const response = await apiClient.get(`/intelligence/document/${docId}`)
  return response.data
}

export const getStakeholderNetwork = async () => {
  const response = await apiClient.get('/intelligence/stakeholders')
  return response.data
}

export const getTimeline = async () => {
  const response = await apiClient.get('/intelligence/timeline')
  return response.data
}

export const getDecisions = async () => {
  const response = await apiClient.get('/intelligence/decisions')
  return response.data
}

// Groq AI endpoints
export const getGroqStatus = async () => {
  const response = await apiClient.get('/ai/groq/status')
  return response.data
}

export const analyzeDocumentAI = async (docId) => {
  const response = await apiClient.post(`/ai/analyze-document/${docId}`)
  return response.data
}

export const getAccountabilityTrail = async (limit = 15) => {
  const response = await apiClient.get(`/ai/accountability-trail?limit=${limit}`)
  return response.data
}

export const askQuestionAI = async (question, docIds = null) => {
  const response = await apiClient.post('/ai/ask', { question, doc_ids: docIds })
  return response.data
}

export default apiClient
