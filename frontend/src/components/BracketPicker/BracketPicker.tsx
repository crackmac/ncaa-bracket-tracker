import { useState } from 'react'
import { Game } from '../../api/client'

interface BracketPickerProps {
  games: Game[]
  onPicksChange: (picks: { game_id: number; predicted_winner_id: number }[]) => void
}

export default function BracketPicker({ games, onPicksChange }: BracketPickerProps) {
  const [picks, setPicks] = useState<Map<number, number>>(new Map())

  const handleTeamClick = (gameId: number, teamId: number) => {
    const newPicks = new Map(picks)
    newPicks.set(gameId, teamId)
    setPicks(newPicks)

    // Convert to array format for parent
    const picksArray = Array.from(newPicks.entries()).map(([game_id, predicted_winner_id]) => ({
      game_id,
      predicted_winner_id
    }))
    onPicksChange(picksArray)
  }

  // Group games by region
  const gamesByRegion = games.reduce((acc, game) => {
    const region = game.region || 'Unknown'
    if (!acc[region]) acc[region] = []
    acc[region].push(game)
    return acc
  }, {} as Record<string, Game[]>)

  const regions = ['East', 'West', 'South', 'Midwest']
  const selectedTeam = (gameId: number) => picks.get(gameId)

  return (
    <div className="space-y-8">
      <div className="text-center">
        <h2 className="text-3xl font-bold text-white mb-2">Pick Your Winners</h2>
        <p className="text-slate-400">
          Select the winner for each game ({picks.size}/{games.length} picked)
        </p>
      </div>

      {regions.map(region => {
        const regionGames = gamesByRegion[region] || []
        if (regionGames.length === 0) return null

        return (
          <div key={region} className="space-y-4">
            <h3 className="text-xl font-bold text-amber-400">{region} Region</h3>

            <div className="space-y-3">
              {regionGames.map(game => {
                const selected = selectedTeam(game.id)

                return (
                  <div
                    key={game.id}
                    className="bg-slate-900/50 border border-slate-800 rounded-lg p-4"
                  >
                    <div className="flex items-center justify-between gap-4">
                      {/* Home team button */}
                      <button
                        onClick={() => handleTeamClick(game.id, game.home_team_id || 0)}
                        className={`flex-1 p-3 rounded-lg transition-all ${
                          selected === game.home_team_id
                            ? 'bg-emerald-600 text-white font-bold'
                            : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-slate-400">#{game.home_team_seed}</span>
                          <span>{game.home_team_name}</span>
                        </div>
                      </button>

                      <span className="text-slate-500 font-bold">VS</span>

                      {/* Away team button */}
                      <button
                        onClick={() => handleTeamClick(game.id, game.away_team_id || 0)}
                        className={`flex-1 p-3 rounded-lg transition-all ${
                          selected === game.away_team_id
                            ? 'bg-emerald-600 text-white font-bold'
                            : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span>{game.away_team_name}</span>
                          <span className="text-xs text-slate-400">#{game.away_team_seed}</span>
                        </div>
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )
      })}
    </div>
  )
}
