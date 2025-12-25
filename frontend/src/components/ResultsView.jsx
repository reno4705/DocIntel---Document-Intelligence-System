import { FileText, Clock, Hash, Tag, Network } from 'lucide-react'

function ResultsView({ document }) {
  if (!document) {
    return (
      <div className="text-center py-12 text-slate-500">
        <FileText className="h-16 w-16 mx-auto mb-4 opacity-50" />
        <p>Upload a document to see results</p>
      </div>
    )
  }

  const entityColors = {
    PER: 'bg-purple-100 text-purple-800 border-purple-200',
    ORG: 'bg-blue-100 text-blue-800 border-blue-200',
    LOC: 'bg-green-100 text-green-800 border-green-200',
    MISC: 'bg-orange-100 text-orange-800 border-orange-200',
    DATE: 'bg-pink-100 text-pink-800 border-pink-200',
    MONEY: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  }

  const getEntityColor = (label) => {
    return entityColors[label] || 'bg-slate-100 text-slate-800 border-slate-200'
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="px-6 py-4 bg-slate-50 border-b border-slate-200">
          <h3 className="font-semibold text-slate-800 flex items-center space-x-2">
            <FileText className="h-5 w-5" />
            <span>Extracted Text</span>
          </h3>
        </div>
        <div className="p-6">
          <div className="flex items-center space-x-4 mb-4 text-sm text-slate-500">
            <span className="flex items-center space-x-1">
              <Hash className="h-4 w-4" />
              <span>{document.text_length} characters</span>
            </span>
            <span className="flex items-center space-x-1">
              <Clock className="h-4 w-4" />
              <span>{document.processing_time}s</span>
            </span>
          </div>
          <div className="bg-slate-50 rounded-lg p-4 max-h-96 overflow-y-auto">
            <pre className="text-sm text-slate-700 whitespace-pre-wrap font-mono">
              {document.extracted_text}
            </pre>
          </div>
        </div>
      </div>

      <div className="space-y-6">
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="px-6 py-4 bg-slate-50 border-b border-slate-200">
            <h3 className="font-semibold text-slate-800">AI Summary</h3>
          </div>
          <div className="p-6">
            <p className="text-slate-700 leading-relaxed">
              {document.summary || 'No summary available'}
            </p>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="px-6 py-4 bg-slate-50 border-b border-slate-200">
            <h3 className="font-semibold text-slate-800 flex items-center space-x-2">
              <Tag className="h-5 w-5" />
              <span>Named Entities ({document.entities?.length || 0})</span>
            </h3>
          </div>
          <div className="p-6">
            {document.entities?.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {document.entities.map((entity, index) => (
                  <span
                    key={index}
                    className={`px-3 py-1 rounded-full text-sm font-medium border ${getEntityColor(entity.label)}`}
                    title={`${entity.label} - Confidence: ${(entity.score * 100).toFixed(1)}%`}
                  >
                    {entity.text}
                    <span className="ml-1 opacity-60 text-xs">{entity.label}</span>
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-slate-500 text-sm">No entities detected</p>
            )}
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="px-6 py-4 bg-slate-50 border-b border-slate-200">
            <h3 className="font-semibold text-slate-800">Document Info</h3>
          </div>
          <div className="p-6">
            <dl className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <dt className="text-slate-500">Filename</dt>
                <dd className="font-medium text-slate-800">{document.filename}</dd>
              </div>
              <div>
                <dt className="text-slate-500">File Type</dt>
                <dd className="font-medium text-slate-800">{document.file_type}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Upload Date</dt>
                <dd className="font-medium text-slate-800">
                  {new Date(document.upload_date).toLocaleString()}
                </dd>
              </div>
              <div>
                <dt className="text-slate-500">Processing Time</dt>
                <dd className="font-medium text-slate-800">{document.processing_time}s</dd>
              </div>
              {document.confidence_avg > 0 && (
                <div>
                  <dt className="text-slate-500">Avg Confidence</dt>
                  <dd className="font-medium text-slate-800">
                    {(document.confidence_avg * 100).toFixed(1)}%
                  </dd>
                </div>
              )}
              {document.extraction_method && (
                <div>
                  <dt className="text-slate-500">Method</dt>
                  <dd className="font-medium text-slate-800 capitalize">{document.extraction_method}</dd>
                </div>
              )}
            </dl>
          </div>
        </div>

        {document.keywords && document.keywords.length > 0 && (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="px-6 py-4 bg-slate-50 border-b border-slate-200">
              <h3 className="font-semibold text-slate-800 flex items-center space-x-2">
                <Network className="h-5 w-5" />
                <span>Keywords</span>
              </h3>
            </div>
            <div className="p-6">
              <div className="flex flex-wrap gap-2">
                {document.keywords.map((keyword, index) => (
                  <span
                    key={index}
                    className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm border border-blue-200"
                  >
                    {keyword}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default ResultsView