import { BrowserRouter, Routes, Route, useParams } from 'react-router-dom'
import { useState, useEffect } from 'react'
import BracketsIndex from './pages/BracketsIndex'
import BracketCreate from './pages/BracketCreate'
import Bracket from './components/Bracket/Bracket'
import { apiClient } from './api/client'
import { useGames } from './hooks/useGames'
import ScoreCard from './components/Stats/ScoreCard'

function isValidStatus(status: string): status is 'scheduled' | 'in_progress' | 'completed' {
  return ['scheduled', 'in_progress', 'completed'].includes(status)
}

function BracketDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [bracketName, setBracketName] = useState('Bracket Details')
  const [stats, setStats] = useState({ totalPoints: 0, correctPicks: 0, totalPicks: 0, possiblePoints: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { games } = useGames()

  // Validate ID early
  const numericId = Number(id)
  if (!id || isNaN(numericId)) {
    return (
      <div className="min-h-screen bg-[#0a0e14] flex items-center justify-center">
        <div className="text-rose-400 text-xl">Invalid bracket ID</div>
      </div>
    )
  }

  useEffect(() => {
    const fetchBracketDetails = async () => {
      try {
        setLoading(true)
        const bracket = await apiClient.getBracket(numericId)
        setBracketName(bracket.name)
        setStats({
          totalPoints: bracket.total_points,
          correctPicks: bracket.correct_picks,
          totalPicks: bracket.total_picks,
          possiblePoints: 0, // Calculate from picks if needed
        })
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load bracket')
      } finally {
        setLoading(false)
      }
    }

    fetchBracketDetails()
  }, [numericId])

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0e14] flex items-center justify-center">
        <div className="text-slate-400 text-xl">Loading bracket...</div>
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

  // Convert games to Bracket component format
  const bracketGames = games.map((g) => ({
    id: g.id,
    round: g.round,
    region: g.region || 'Unknown',
    homeTeam: {
      id: g.home_team_id || 0,
      name: g.home_team_name || g.home_team,
      seed: g.home_team_seed || 0,
      score: g.home_score ?? undefined,
    },
    awayTeam: {
      id: g.away_team_id || 0,
      name: g.away_team_name || g.away_team,
      seed: g.away_team_seed || 0,
      score: g.away_score ?? undefined,
    },
    status: isValidStatus(g.status) ? g.status : 'scheduled',
    isUpset: g.is_upset,
  }))

  return (
    <>
      <Bracket games={bracketGames} title={bracketName} />
      <div className="container mx-auto px-4 pb-12">
        <div className="max-w-2xl mx-auto">
          <ScoreCard
            totalPoints={stats.totalPoints}
            correctPicks={stats.correctPicks}
            totalPicks={stats.totalPicks}
            possiblePoints={stats.possiblePoints}
            bracketName={bracketName}
          />
        </div>
      </div>
    </>
  )
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<BracketsIndex />} />
        <Route path="/brackets/create" element={<BracketCreate />} />
        <Route path="/brackets/:id" element={<BracketDetailPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
