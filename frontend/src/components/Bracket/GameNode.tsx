import type { Game } from './Bracket'

interface GameNodeProps {
  game: Game
}

export default function GameNode({ game }: GameNodeProps) {
  const { homeTeam, awayTeam, status, predictedWinnerId, isCorrect, isUpset } = game

  // Determine winner
  const homeScore = homeTeam.score ?? 0
  const awayScore = awayTeam.score ?? 0
  const winnerId = homeScore > awayScore ? homeTeam.id : homeScore < awayScore ? awayTeam.id : null

  // Color scheme based on pick correctness and status
  const getStatusColor = () => {
    if (status === 'scheduled') {
      return {
        border: 'border-slate-800',
        glow: '',
        bg: 'bg-slate-900/50',
      }
    }

    if (status === 'in_progress') {
      return {
        border: 'border-amber-500/30',
        glow: 'shadow-lg shadow-amber-500/20',
        bg: 'bg-gradient-to-br from-slate-900/80 to-amber-900/20',
      }
    }

    // Completed
    if (isCorrect === true) {
      return {
        border: 'border-emerald-500/40',
        glow: 'shadow-xl shadow-emerald-500/25',
        bg: 'bg-gradient-to-br from-slate-900/80 to-emerald-900/30',
      }
    }

    if (isCorrect === false) {
      return {
        border: 'border-rose-500/40',
        glow: 'shadow-xl shadow-rose-500/25',
        bg: 'bg-gradient-to-br from-slate-900/80 to-rose-900/30',
      }
    }

    // Completed but no pick
    return {
      border: 'border-slate-700',
      glow: '',
      bg: 'bg-slate-900/50',
    }
  }

  const statusColors = getStatusColor()

  return (
    <div
      className={`
        group relative rounded-xl border backdrop-blur-sm
        transition-all duration-300 hover:scale-[1.02]
        ${statusColors.border}
        ${statusColors.glow}
        ${statusColors.bg}
      `}
    >
      {/* Upset Badge */}
      {isUpset && status === 'completed' && (
        <div className="absolute -top-3 -right-3 z-10">
          <div className="relative">
            <div className="absolute inset-0 bg-amber-400 rounded-full blur-md animate-pulse" />
            <div className="relative bg-gradient-to-br from-amber-400 to-orange-500 text-slate-900 text-xs font-black px-3 py-1.5 rounded-full shadow-xl border-2 border-amber-300">
              UPSET
            </div>
          </div>
        </div>
      )}

      {/* Region Tag */}
      <div className="px-4 pt-3 pb-2 border-b border-slate-800/50">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">{game.region}</span>
          {status === 'in_progress' && (
            <div className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
              <span className="text-xs font-bold text-amber-400 uppercase tracking-wider">Live</span>
            </div>
          )}
        </div>
      </div>

      {/* Teams */}
      <div className="p-4 space-y-2">
        {/* Home Team */}
        <TeamRow
          team={homeTeam}
          isWinner={winnerId === homeTeam.id && status === 'completed'}
          isPredicted={predictedWinnerId === homeTeam.id}
          showScore={status !== 'scheduled'}
        />

        {/* Divider */}
        <div className="relative h-px bg-slate-800/50">
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-slate-700/50 to-transparent" />
        </div>

        {/* Away Team */}
        <TeamRow
          team={awayTeam}
          isWinner={winnerId === awayTeam.id && status === 'completed'}
          isPredicted={predictedWinnerId === awayTeam.id}
          showScore={status !== 'scheduled'}
        />
      </div>

      {/* Pick Indicator */}
      {predictedWinnerId && (
        <div className="px-4 pb-3 pt-2 border-t border-slate-800/50">
          <div className="flex items-center gap-2 text-xs">
            <div className="w-1.5 h-1.5 rounded-full bg-slate-600" />
            <span className="text-slate-500 font-medium">
              Your pick:{' '}
              <span className="text-slate-400 font-semibold">
                {predictedWinnerId === homeTeam.id ? homeTeam.name : awayTeam.name}
              </span>
            </span>
          </div>
        </div>
      )}
    </div>
  )
}

interface TeamRowProps {
  team: { name: string; seed: number; score?: number }
  isWinner: boolean
  isPredicted: boolean
  showScore: boolean
}

function TeamRow({ team, isWinner, isPredicted, showScore }: TeamRowProps) {
  return (
    <div
      className={`
        flex items-center justify-between gap-3 px-3 py-2.5 rounded-lg
        transition-all duration-200
        ${isWinner ? 'bg-white/5 ring-1 ring-white/10' : 'hover:bg-white/[0.02]'}
      `}
    >
      <div className="flex items-center gap-3 flex-1 min-w-0">
        {/* Seed Badge */}
        <div
          className={`
            flex-shrink-0 w-7 h-7 rounded-md flex items-center justify-center
            font-black text-sm
            ${
              isWinner
                ? 'bg-gradient-to-br from-amber-400 to-amber-500 text-slate-900 shadow-lg shadow-amber-500/30'
                : 'bg-slate-800/50 text-slate-400'
            }
          `}
          style={{ fontFamily: "'Bebas Neue', sans-serif" }}
        >
          {team.seed}
        </div>

        {/* Team Name */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p
              className={`
                font-semibold truncate
                ${isWinner ? 'text-white text-base' : 'text-slate-300 text-sm'}
              `}
            >
              {team.name}
            </p>
            {isPredicted && (
              <div className="flex-shrink-0 w-1.5 h-1.5 rounded-full bg-blue-400 shadow-sm shadow-blue-400/50" />
            )}
          </div>
        </div>
      </div>

      {/* Score */}
      {showScore && (
        <div
          className={`
            flex-shrink-0 text-right font-black text-2xl tracking-tighter
            ${isWinner ? 'text-white' : 'text-slate-500'}
          `}
          style={{ fontFamily: "'Bebas Neue', sans-serif" }}
        >
          {team.score ?? '-'}
        </div>
      )}
    </div>
  )
}
