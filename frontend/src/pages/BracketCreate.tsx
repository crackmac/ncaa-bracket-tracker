import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiClient } from '../api/client'
import { useGames } from '../hooks/useGames'
import BracketPicker from '../components/BracketPicker/BracketPicker'

export default function BracketCreate() {
  const navigate = useNavigate()
  const { games } = useGames()
  const [activeTab, setActiveTab] = useState<'picker' | 'upload'>('picker')
  const [name, setName] = useState('')
  const [bracketType, setBracketType] = useState('balanced')
  const [picks, setPicks] = useState<{ game_id: number; predicted_winner_id: number }[]>([])
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const bracket = await apiClient.createBracket({ name, bracket_type: bracketType, picks })
      navigate(`/brackets/${bracket.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create bracket')
    } finally {
      setLoading(false)
    }
  }

  const handleFileSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) return

    setLoading(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch('/api/v1/brackets/import', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to import bracket')
      }

      const bracket = await response.json()
      navigate(`/brackets/${bracket.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to import bracket')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#0a0e14] relative overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-amber-500/10 rounded-full blur-[128px]" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-emerald-500/10 rounded-full blur-[128px]" />
      </div>

      <div className="relative z-10 container mx-auto px-4 py-8 lg:py-12 max-w-4xl">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1
            className="text-5xl lg:text-7xl font-black tracking-tighter mb-3 bg-clip-text text-transparent bg-gradient-to-r from-amber-200 via-amber-400 to-amber-200"
            style={{ fontFamily: "'Bebas Neue', sans-serif" }}
          >
            Create Bracket
          </h1>
          <p className="text-slate-400 text-lg">Pick your winners or upload a bracket file</p>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6 border-b border-slate-800">
          <button
            onClick={() => setActiveTab('picker')}
            className={`px-6 py-3 font-semibold transition-colors ${
              activeTab === 'picker'
                ? 'text-amber-400 border-b-2 border-amber-400'
                : 'text-slate-400 hover:text-slate-300'
            }`}
          >
            Manual Picker
          </button>
          <button
            onClick={() => setActiveTab('upload')}
            className={`px-6 py-3 font-semibold transition-colors ${
              activeTab === 'upload'
                ? 'text-amber-400 border-b-2 border-amber-400'
                : 'text-slate-400 hover:text-slate-300'
            }`}
          >
            Upload File
          </button>
        </div>

        {/* Error message */}
        {error && (
          <div className="mb-6 p-4 bg-rose-500/10 border border-rose-500/30 rounded-lg text-rose-400">
            {error}
          </div>
        )}

        {/* Tab Content */}
        {activeTab === 'picker' ? (
          <form onSubmit={handleManualSubmit} className="space-y-6">
            {/* Bracket details */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Bracket Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-amber-400"
                  placeholder="My Championship Bracket"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Bracket Type</label>
                <select
                  value={bracketType}
                  onChange={(e) => setBracketType(e.target.value)}
                  className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-amber-400"
                >
                  <option value="chalk">Chalk (Favorites Win)</option>
                  <option value="balanced">Balanced</option>
                  <option value="chaos">Chaos (Upsets)</option>
                  <option value="custom">Custom</option>
                </select>
              </div>
            </div>

            {/* Bracket picker */}
            <BracketPicker games={games} onPicksChange={setPicks} />

            {/* Submit */}
            <div className="space-y-2">
              {picks.length < games.length && (
                <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg text-amber-400 text-sm">
                  ⚠️ You must pick a winner for all {games.length} games before creating your bracket.
                  Currently selected: {picks.length}/{games.length}
                </div>
              )}
              <button
                type="submit"
                disabled={loading || picks.length !== games.length}
                className="w-full px-6 py-3 bg-amber-500 hover:bg-amber-600 disabled:bg-slate-700 disabled:text-slate-500 text-white font-bold rounded-lg transition-colors"
              >
                {loading ? 'Creating...' : `Create Bracket (${picks.length}/${games.length} picked)`}
              </button>
            </div>
          </form>
        ) : (
          <form onSubmit={handleFileSubmit} className="space-y-6">
            <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Upload Bracket File</label>
                <input
                  type="file"
                  accept=".yaml,.yml,.json"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  required
                  className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-amber-500 file:text-white hover:file:bg-amber-600"
                />
                <p className="mt-2 text-sm text-slate-400">Accepts .yaml, .yml, or .json files</p>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || !file}
              className="w-full px-6 py-3 bg-amber-500 hover:bg-amber-600 disabled:bg-slate-700 disabled:text-slate-500 text-white font-bold rounded-lg transition-colors"
            >
              {loading ? 'Importing...' : 'Import Bracket'}
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
