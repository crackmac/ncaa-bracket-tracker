import { BrowserRouter, Routes, Route, useParams } from 'react-router-dom'
import { useState, useEffect } from 'react'
import BracketsIndex from './pages/BracketsIndex'
import Bracket, { type Game } from './components/Bracket/Bracket'
import ScoreCard from './components/Stats/ScoreCard'
import { apiClient } from './api/client'
import { useGames } from './hooks/useGames'

// Sample data for demonstration
const sampleGames: Game[] = [
  {
    id: 1,
    round: 'Round 64',
    region: 'East',
    homeTeam: { id: 1, name: 'Duke', seed: 1, score: 78 },
    awayTeam: { id: 16, name: 'Hampton', seed: 16, score: 62 },
    status: 'completed',
    predictedWinnerId: 1,
    isCorrect: true,
    isUpset: false,
  },
  {
    id: 2,
    round: 'Round 64',
    region: 'East',
    homeTeam: { id: 8, name: 'Memphis', seed: 8, score: 71 },
    awayTeam: { id: 9, name: 'Missouri', seed: 9, score: 75 },
    status: 'completed',
    predictedWinnerId: 8,
    isCorrect: false,
    isUpset: true,
  },
  {
    id: 3,
    round: 'Round 64',
    region: 'West',
    homeTeam: { id: 4, name: 'Kansas', seed: 4, score: 82 },
    awayTeam: { id: 13, name: 'Iona', seed: 13 },
    status: 'in_progress',
    predictedWinnerId: 4,
    isCorrect: null,
    isUpset: false,
  },
  {
    id: 4,
    round: 'Round 64',
    region: 'West',
    homeTeam: { id: 2, name: 'Gonzaga', seed: 2 },
    awayTeam: { id: 15, name: 'Norfolk State', seed: 15 },
    status: 'scheduled',
    predictedWinnerId: 2,
    isCorrect: null,
    isUpset: false,
  },
]

function BracketDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [bracketName, setBracketName] = useState('Bracket Details')
  const [stats, setStats] = useState({ totalPoints: 0, correctPicks: 0, totalPicks: 0, possiblePoints: 0 })
  const { games } = useGames()

  useEffect(() => {
    if (id) {
      const fetchBracketDetails = async () => {
        try {
          const bracket = await apiClient.getBracket(Number(id))
          setBracketName(bracket.name)
          setStats({
            totalPoints: bracket.total_points,
            correctPicks: bracket.correct_picks,
            totalPicks: bracket.total_picks,
            possiblePoints: 0, // Calculate from picks if needed
          })
        } catch (err) {
          console.error('Failed to fetch bracket details:', err)
        }
      }
      fetchBracketDetails()
    }
  }, [id])

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
    status: g.status as 'scheduled' | 'in_progress' | 'completed',
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

function DemoPage() {
  const [view, setView] = useState<'bracket' | 'demo'>('demo')

  return (
    <div className="min-h-screen bg-[#0a0e14]">
      {view === 'demo' ? (
        <>
          <Bracket games={sampleGames} title="March Madness 2026" />

          {/* Stats Section */}
          <div className="container mx-auto px-4 pb-12">
            <div className="max-w-2xl mx-auto">
              <ScoreCard
                totalPoints={180}
                correctPicks={8}
                totalPicks={12}
                possiblePoints={520}
                bracketName="Championship Run"
              />
            </div>
          </div>

          {/* Demo Controls */}
          <div className="fixed bottom-6 right-6">
            <button
              onClick={() => setView('bracket')}
              className="px-6 py-3 bg-slate-800 hover:bg-slate-700 text-white rounded-lg font-semibold shadow-xl border border-slate-700 transition-all duration-200"
            >
              Switch to Live Data
            </button>
          </div>
        </>
      ) : (
        <>
          <Bracket games={[]} title="Live Bracket" />
          <div className="fixed bottom-6 right-6">
            <button
              onClick={() => setView('demo')}
              className="px-6 py-3 bg-slate-800 hover:bg-slate-700 text-white rounded-lg font-semibold shadow-xl border border-slate-700 transition-all duration-200"
            >
              Back to Demo
            </button>
          </div>
        </>
      )}
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<BracketsIndex />} />
        <Route path="/brackets/:id" element={<BracketDetailPage />} />
        <Route path="/demo" element={<DemoPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
