import { BrowserRouter, Routes, Route, useParams } from 'react-router-dom'
import { useState, useEffect } from 'react'
import BracketsIndex from './pages/BracketsIndex'
import Bracket from './components/Bracket/Bracket'
import { apiClient } from './api/client'
import { useGames } from './hooks/useGames'
import ScoreCard from './components/Stats/ScoreCard'

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

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<BracketsIndex />} />
        <Route path="/brackets/:id" element={<BracketDetailPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
