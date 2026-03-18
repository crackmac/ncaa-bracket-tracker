import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiClient, type Bracket } from '../api/client'

export default function BracketsIndex() {
  const [brackets, setBrackets] = useState<Bracket[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchBrackets = async () => {
      try {
        setLoading(true)
        const data = await apiClient.getBrackets()
        // Sort by points descending
        const sorted = data.sort((a, b) => b.total_points - a.total_points)
        setBrackets(sorted)
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load brackets')
      } finally {
        setLoading(false)
      }
    }

    fetchBrackets()
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0e14] flex items-center justify-center">
        <div className="text-slate-400 text-xl">Loading brackets...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[#0a0e14] flex items-center justify-center">
        <div className="text-rose-400 text-xl">Error: {error}</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#0a0e14] relative overflow-hidden">
      {/* Stadium Lighting Effect */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-amber-500/10 rounded-full blur-[128px]" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-emerald-500/10 rounded-full blur-[128px]" />
      </div>

      <div className="relative z-10 container mx-auto px-4 py-8 lg:py-12">
        {/* Header */}
        <div className="mb-12 text-center">
          <h1
            className="text-5xl lg:text-7xl font-black tracking-tighter mb-3 bg-clip-text text-transparent bg-gradient-to-r from-amber-200 via-amber-400 to-amber-200"
            style={{ fontFamily: "'Bebas Neue', sans-serif" }}
          >
            My Brackets
          </h1>
          <p className="text-slate-400 text-lg">Track your March Madness predictions</p>

          <div className="mt-6">
            <Link
              to="/brackets/create"
              className="inline-flex items-center gap-2 px-6 py-3 bg-amber-500 hover:bg-amber-600 text-white font-bold rounded-lg transition-colors"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Create New Bracket
            </Link>
          </div>
        </div>

        {/* Empty State */}
        {brackets.length === 0 ? (
          <div className="text-center py-20">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-slate-900/50 border border-slate-800 mb-6">
              <svg
                className="w-10 h-10 text-slate-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
            </div>
            <p className="text-xl text-slate-400 font-medium mb-8">No brackets yet</p>
          </div>
        ) : (
          /* Brackets Table */
          <div className="bg-slate-900/50 rounded-2xl border border-slate-800 backdrop-blur-sm overflow-hidden">
            <table className="w-full">
              <thead className="bg-slate-800/50 border-b border-slate-700">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-400 uppercase tracking-wider">
                    Bracket Name
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-bold text-slate-400 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-4 text-center text-xs font-bold text-slate-400 uppercase tracking-wider">
                    Points
                  </th>
                  <th className="px-6 py-4 text-center text-xs font-bold text-slate-400 uppercase tracking-wider">
                    Accuracy
                  </th>
                  <th className="px-6 py-4 text-right text-xs font-bold text-slate-400 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {brackets.map((bracket) => {
                  const accuracy =
                    bracket.total_picks > 0
                      ? Math.round((bracket.correct_picks / bracket.total_picks) * 100)
                      : 0

                  return (
                    <tr key={bracket.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="px-6 py-4">
                        <Link
                          to={`/brackets/${bracket.id}`}
                          className="text-white font-semibold hover:text-amber-400 transition-colors"
                        >
                          {bracket.name}
                        </Link>
                      </td>
                      <td className="px-6 py-4">
                        <span className="inline-flex px-3 py-1 rounded-full text-xs font-medium bg-slate-800 text-slate-300 capitalize">
                          {bracket.bracket_type}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <span
                          className="text-2xl font-black text-amber-400"
                          style={{ fontFamily: "'Bebas Neue', sans-serif" }}
                        >
                          {bracket.total_points}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <div className="flex flex-col items-center gap-1">
                          <span className="text-lg font-bold text-white">{accuracy}%</span>
                          <span className="text-xs text-slate-400">
                            {bracket.correct_picks}/{bracket.total_picks}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <Link
                          to={`/brackets/${bracket.id}`}
                          className="inline-flex items-center gap-2 px-4 py-2 bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 rounded-lg text-amber-400 font-semibold text-sm transition-colors"
                        >
                          View Details
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M9 5l7 7-7 7"
                            />
                          </svg>
                        </Link>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
