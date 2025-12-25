import { useState } from 'react'
import FileUpload from '../components/FileUpload'
import ResultsView from '../components/ResultsView'

function Upload() {
  const [processedDocument, setProcessedDocument] = useState(null)

  const handleUploadComplete = (document) => {
    setProcessedDocument(document)
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Upload Document</h1>
        <p className="text-slate-500">Upload a PDF or image to extract and analyze text</p>
      </div>

      <FileUpload onUploadComplete={handleUploadComplete} />

      {processedDocument && (
        <div className="mt-8">
          <h2 className="text-xl font-semibold text-slate-800 mb-4">Analysis Results</h2>
          <ResultsView document={processedDocument} />
        </div>
      )}
    </div>
  )
}

export default Upload
