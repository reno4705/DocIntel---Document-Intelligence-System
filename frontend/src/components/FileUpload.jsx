import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, Loader2, CheckCircle, AlertCircle, Network, X } from 'lucide-react'
import { uploadDocument, uploadDocumentsBatch } from '../services/api'

function FileUpload({ onUploadComplete }) {
  const [uploading, setUploading] = useState(false)
  const [uploadStatus, setUploadStatus] = useState(null)
  const [error, setError] = useState(null)
  const [progress, setProgress] = useState({ current: 0, total: 0 })

  const onDrop = useCallback(async (acceptedFiles) => {
    if (acceptedFiles.length === 0) return
    
    setUploading(true)
    setError(null)
    setUploadStatus(null)
    setProgress({ current: 0, total: acceptedFiles.length })
    
    try {
      if (acceptedFiles.length === 1) {
        // Single file upload
        const result = await uploadDocument(acceptedFiles[0])
        setUploadStatus(result)
        if (onUploadComplete) {
          onUploadComplete(result.data)
        }
      } else {
        // Batch upload
        const result = await uploadDocumentsBatch(acceptedFiles)
        setUploadStatus({
          success: true,
          message: result.message,
          batch: true,
          processed: result.processed,
          failed: result.failed,
          results: result.results,
          errors: result.errors
        })
        if (onUploadComplete) {
          onUploadComplete(result)
        }
      }
    } catch (err) {
      const errorMessage = err.response?.data?.detail || 'Upload failed. Please try again.'
      setError(errorMessage)
    } finally {
      setUploading(false)
    }
  }, [onUploadComplete])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/*': ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']
    },
    multiple: true,
    disabled: uploading
  })

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all ${
          isDragActive
            ? 'border-blue-500 bg-blue-50'
            : uploading
            ? 'border-slate-300 bg-slate-50 cursor-not-allowed'
            : 'border-slate-300 hover:border-blue-400 hover:bg-slate-50'
        }`}
      >
        <input {...getInputProps()} />
        
        {uploading ? (
          <div className="flex flex-col items-center space-y-4">
            <Loader2 className="h-16 w-16 text-blue-500 animate-spin" />
            <p className="text-lg font-medium text-slate-700">Processing document...</p>
            <p className="text-sm text-slate-500">Extracting text and analyzing content</p>
          </div>
        ) : isDragActive ? (
          <div className="flex flex-col items-center space-y-4">
            <Upload className="h-16 w-16 text-blue-500" />
            <p className="text-lg font-medium text-blue-600">Drop the file here</p>
          </div>
        ) : (
          <div className="flex flex-col items-center space-y-4">
            <div className="p-4 bg-slate-100 rounded-full">
              <FileText className="h-12 w-12 text-slate-500" />
            </div>
            <div>
              <p className="text-lg font-medium text-slate-700">
                Drag & drop a document here
              </p>
              <p className="text-sm text-slate-500 mt-1">
                or click to browse files
              </p>
            </div>
            <p className="text-xs text-slate-400">
              Supported: PDF, PNG, JPG, JPEG, TIFF, BMP (Max 10MB each)
            </p>
            <p className="text-xs text-blue-500 mt-1 font-medium">
              Select multiple files for batch upload
            </p>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center space-x-3">
          <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0" />
          <p className="text-red-700">{error}</p>
        </div>
      )}

      {uploadStatus?.success && !uploadStatus.batch && (
        <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center space-x-3">
          <CheckCircle className="h-5 w-5 text-green-500 flex-shrink-0" />
          <div>
            <p className="text-green-700 font-medium">Document processed successfully!</p>
            <p className="text-green-600 text-sm">{uploadStatus.message}</p>
          </div>
        </div>
      )}

      {uploadStatus?.success && uploadStatus.batch && (
        <div className="mt-4 space-y-3">
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-center space-x-3">
              <CheckCircle className="h-5 w-5 text-green-500 flex-shrink-0" />
              <div>
                <p className="text-green-700 font-medium">Batch upload complete!</p>
                <p className="text-green-600 text-sm">
                  {uploadStatus.processed} processed, {uploadStatus.failed} failed
                </p>
              </div>
            </div>
          </div>
          
          {uploadStatus.results?.length > 0 && (
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg">
              <p className="text-sm font-medium text-slate-700 mb-2">Processed files:</p>
              <div className="space-y-1 max-h-40 overflow-y-auto">
                {uploadStatus.results.map((r, idx) => (
                  <div key={idx} className="flex items-center justify-between text-sm">
                    <span className="text-slate-600">{r.filename}</span>
                    <span className="text-green-600">{r.entities_added} entities</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {uploadStatus.errors?.length > 0 && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm font-medium text-red-700 mb-2">Failed files:</p>
              <div className="space-y-1">
                {uploadStatus.errors.map((e, idx) => (
                  <div key={idx} className="text-sm text-red-600">
                    {e.filename}: {e.error}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
        <div className="flex items-center space-x-2">
          <Network className="h-5 w-5 text-blue-600" />
          <span className="font-medium text-blue-800">Multi-Document Intelligence</span>
        </div>
        <p className="text-sm text-blue-700 mt-2">
          Documents are automatically processed, entities extracted, and added to the knowledge graph for cross-document reasoning.
        </p>
      </div>
    </div>
  )
}

export default FileUpload
