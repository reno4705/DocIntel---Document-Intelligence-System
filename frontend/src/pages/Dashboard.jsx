import { useState, useEffect } from 'react'
import { FileText, Tag, Network, GitBranch, ArrowRight } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart as RechartPie, Pie, Cell, Legend } from 'recharts'
import { Link } from 'react-router-dom'
import StatsCard from '../components/StatsCard'
import { getStats, getDocuments } from '../services/api'

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']

function Dashboard() {
  const [stats, setStats] = useState(null)
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsData, docsData] = await Promise.all([
          getStats(),
          getDocuments()
        ])
        setStats(statsData)
        setDocuments(docsData)
      } catch (err) {
        setError('Failed to load dashboard data')
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

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

  const entityChartData = Object.entries(stats?.entity_types || {}).map(([name, value]) => ({
    name,
    value
  }))

  const fileTypeData = Object.entries(stats?.file_types || {}).map(([name, value]) => ({
    name,
    count: value
  }))

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Multi-Document Intelligence</h1>
        <p className="text-slate-500">Cross-document reasoning and knowledge graph analytics</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard
          title="Documents"
          value={stats?.total_documents || 0}
          icon={FileText}
          color="blue"
        />
        <StatsCard
          title="Entities"
          value={stats?.total_entities || 0}
          icon={Tag}
          color="green"
        />
        <StatsCard
          title="Relationships"
          value={stats?.total_relationships || 0}
          icon={GitBranch}
          color="purple"
        />
        <StatsCard
          title="Entity Types"
          value={Object.keys(stats?.entity_types || {}).length}
          icon={Network}
          color="orange"
        />
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link to="/upload" className="p-4 bg-blue-50 border border-blue-200 rounded-xl hover:bg-blue-100 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-blue-800">Add Documents</h3>
              <p className="text-sm text-blue-600">Upload documents to build knowledge graph</p>
            </div>
            <ArrowRight className="h-5 w-5 text-blue-500" />
          </div>
        </Link>
        <Link to="/knowledge-graph" className="p-4 bg-green-50 border border-green-200 rounded-xl hover:bg-green-100 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-green-800">View Knowledge Graph</h3>
              <p className="text-sm text-green-600">Explore entities and relationships</p>
            </div>
            <ArrowRight className="h-5 w-5 text-green-500" />
          </div>
        </Link>
        <Link to="/query" className="p-4 bg-purple-50 border border-purple-200 rounded-xl hover:bg-purple-100 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-purple-800">Query Documents</h3>
              <p className="text-sm text-purple-600">Ask questions across your corpus</p>
            </div>
            <ArrowRight className="h-5 w-5 text-purple-500" />
          </div>
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h3 className="font-semibold text-slate-800 mb-4">Entity Distribution</h3>
          {entityChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={entityChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-slate-400">
              No entity data available
            </div>
          )}
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h3 className="font-semibold text-slate-800 mb-4">File Types Processed</h3>
          {fileTypeData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <RechartPie>
                <Pie
                  data={fileTypeData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="count"
                  nameKey="name"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {fileTypeData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </RechartPie>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-slate-400">
              No file type data available
            </div>
          )}
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200">
          <h3 className="font-semibold text-slate-800">Recent Documents</h3>
        </div>
        <div className="overflow-x-auto">
          {documents.length > 0 ? (
            <table className="w-full">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase">Filename</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase">Words</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase">Entities</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase">Keywords</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {documents.slice(0, 5).map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-50">
                    <td className="px-6 py-4 text-sm font-medium text-slate-800">{doc.filename}</td>
                    <td className="px-6 py-4 text-sm text-slate-600">{doc.word_count || 0}</td>
                    <td className="px-6 py-4 text-sm text-slate-600">{doc.entity_count || 0}</td>
                    <td className="px-6 py-4 text-sm text-slate-600">
                      {doc.keywords?.slice(0, 3).join(', ') || '-'}
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-600">
                      {new Date(doc.upload_date).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="p-6 text-center text-slate-400">
              <Network className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>No documents yet. Upload documents to build your knowledge graph.</p>
              <Link to="/upload" className="text-blue-500 hover:text-blue-600 mt-2 inline-block">
                Upload first document →
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Dashboard
