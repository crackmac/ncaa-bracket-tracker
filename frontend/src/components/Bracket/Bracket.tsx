import { useEffect, useState } from 'react'
import GameNode from './GameNode'

export interface Team {
  id: number
  name: string
  seed: number
  score?: number
}

export interface Game {
  id: number
  round: string
  region: string
  homeTeam: Team
  awayTeam: Team
  status: 'scheduled' | 'in_progress' | 'completed'
  predictedWinnerId?: number
  isCorrect?: boolean | null
  isUpset?: boolean
}

export interface BracketProps {
  games: Game[]
  title?: string
}

export default function Bracket({ games, title = 'Tournament Bracket' }: BracketProps) {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  // Group games by round
  const gamesByRound = games.reduce((acc, game) => {
    if (!acc[game.round]) {
      acc[game.round] = []
    }
    acc[game.round].push(game)
    return acc
  }, {} as Record<string, Game[]>)

  const rounds = Object.keys(gamesByRound).sort((a, b) => {
    const order = ['Round 64', 'Round 32', 'Sweet 16', 'Elite 8', 'Final Four', 'Championship']
    return order.indexOf(a) - order.indexOf(b)
  })

  return (
    <div className="min-h-screen bg-[#0a0e14] relative overflow-hidden">
      {/* Stadium Lighting Effect */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-amber-500/10 rounded-full blur-[128px]" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-emerald-500/10 rounded-full blur-[128px]" />
      </div>

      {/* Court Texture Overlay */}
      <div
        className="absolute inset-0 opacity-[0.02] pointer-events-none"
        style={{
          backgroundImage: `repeating-linear-gradient(
            0deg,
            transparent,
            transparent 2px,
            rgba(255, 255, 255, 0.03) 2px,
            rgba(255, 255, 255, 0.03) 4px
          )`,
        }}
      />

      <div className="relative z-10 container mx-auto px-4 py-8 lg:py-12">
        {/* Header */}
        <div
          className={`mb-12 text-center transition-all duration-1000 ${
            mounted ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-8'
          }`}
        >
          <h1
            className="text-5xl lg:text-7xl font-black tracking-tighter mb-3 bg-clip-text text-transparent bg-gradient-to-r from-amber-200 via-amber-400 to-amber-200"
            style={{ fontFamily: "'Bebas Neue', sans-serif" }}
          >
            {title}
          </h1>
          <div className="flex items-center justify-center gap-6 text-sm font-medium">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-emerald-400 shadow-lg shadow-emerald-400/50" />
              <span className="text-slate-400">Correct Pick</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-rose-400 shadow-lg shadow-rose-400/50" />
              <span className="text-slate-400">Incorrect Pick</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-amber-400 shadow-lg shadow-amber-400/50" />
              <span className="text-slate-400">In Progress</span>
            </div>
          </div>
        </div>

        {/* Bracket Grid */}
        <div className="space-y-16">
          {rounds.map((round, roundIndex) => (
            <div
              key={round}
              className={`transition-all duration-700 ${
                mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
              }`}
              style={{ transitionDelay: `${roundIndex * 150}ms` }}
            >
              {/* Round Header */}
              <div className="mb-6 flex items-center gap-4">
                <div className="flex-shrink-0 w-12 h-12 rounded-lg bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700 flex items-center justify-center">
                  <span
                    className="text-2xl font-black text-amber-400"
                    style={{ fontFamily: "'Bebas Neue', sans-serif" }}
                  >
                    {roundIndex + 1}
                  </span>
                </div>
                <div>
                  <h2
                    className="text-3xl font-black text-white tracking-tight"
                    style={{ fontFamily: "'Bebas Neue', sans-serif" }}
                  >
                    {round}
                  </h2>
                  <p className="text-slate-500 text-sm font-medium">
                    {gamesByRound[round].length} {gamesByRound[round].length === 1 ? 'game' : 'games'}
                  </p>
                </div>
              </div>

              {/* Games Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {gamesByRound[round].map((game, gameIndex) => (
                  <div
                    key={game.id}
                    className="transition-all duration-500"
                    style={{
                      transitionDelay: `${roundIndex * 150 + gameIndex * 100}ms`,
                      opacity: mounted ? 1 : 0,
                      transform: mounted ? 'translateY(0)' : 'translateY(16px)',
                    }}
                  >
                    <GameNode game={game} />
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Empty State */}
        {games.length === 0 && (
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
            <p className="text-xl text-slate-400 font-medium">No games to display</p>
          </div>
        )}
      </div>
    </div>
  )
}
