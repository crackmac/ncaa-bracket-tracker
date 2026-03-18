import { useEffect, useState } from 'react'

export interface ScoreCardProps {
  totalPoints: number
  correctPicks: number
  totalPicks: number
  possiblePoints: number
  bracketName?: string
}

export default function ScoreCard({
  totalPoints,
  correctPicks,
  totalPicks,
  possiblePoints,
  bracketName = 'My Bracket',
}: ScoreCardProps) {
  const [mounted, setMounted] = useState(false)
  const [animatedPoints, setAnimatedPoints] = useState(0)

  const accuracy = totalPicks > 0 ? Math.round((correctPicks / totalPicks) * 100) : 0
  const health = possiblePoints > 0 ? Math.round((possiblePoints / 3200) * 100) : 100 // 3200 = max possible points

  useEffect(() => {
    setMounted(true)

    // Animate points counter
    const duration = 1000
    const steps = 30
    const increment = totalPoints / steps
    let current = 0
    let step = 0

    const interval = setInterval(() => {
      step++
      current = Math.min(current + increment, totalPoints)
      setAnimatedPoints(Math.round(current))

      if (step >= steps || current >= totalPoints) {
        setAnimatedPoints(totalPoints)
        clearInterval(interval)
      }
    }, duration / steps)

    return () => clearInterval(interval)
  }, [totalPoints])

  return (
    <div
      className={`
        relative rounded-2xl border border-slate-800 bg-gradient-to-br from-slate-900/80 to-slate-900/40
        backdrop-blur-sm overflow-hidden
        transition-all duration-700
        ${mounted ? 'opacity-100 scale-100' : 'opacity-0 scale-95'}
      `}
    >
      {/* Atmospheric Glow */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-amber-500/5 rounded-full blur-3xl pointer-events-none" />

      <div className="relative z-10 p-6 lg:p-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-2 h-2 rounded-full bg-amber-400 shadow-lg shadow-amber-400/50 animate-pulse" />
            <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider">Performance</h3>
          </div>
          <h2
            className="text-3xl font-black text-white tracking-tight"
            style={{ fontFamily: "'Bebas Neue', sans-serif" }}
          >
            {bracketName}
          </h2>
        </div>

        {/* Main Score */}
        <div className="mb-8">
          <div className="mb-2">
            <span className="text-sm font-bold text-slate-500 uppercase tracking-wider">Total Points</span>
          </div>
          <div className="flex items-baseline gap-3">
            <span
              className="text-7xl font-black bg-clip-text text-transparent bg-gradient-to-br from-amber-300 via-amber-400 to-amber-500 leading-none"
              style={{ fontFamily: "'Bebas Neue', sans-serif" }}
            >
              {animatedPoints}
            </span>
            <span className="text-2xl font-bold text-slate-600" style={{ fontFamily: "'Bebas Neue', sans-serif" }}>
              / {possiblePoints}
            </span>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          {/* Accuracy */}
          <div className="bg-slate-900/50 rounded-xl p-4 border border-slate-800/50">
            <div className="mb-2">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Accuracy</span>
            </div>
            <div className="flex items-baseline gap-2">
              <span
                className="text-4xl font-black text-white leading-none"
                style={{ fontFamily: "'Bebas Neue', sans-serif" }}
              >
                {accuracy}
              </span>
              <span className="text-lg font-bold text-slate-600">%</span>
            </div>
            <div className="mt-2 text-xs text-slate-400 font-medium">
              {correctPicks} of {totalPicks} picks
            </div>
          </div>

          {/* Bracket Health */}
          <div className="bg-slate-900/50 rounded-xl p-4 border border-slate-800/50">
            <div className="mb-2">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Health</span>
            </div>
            <div className="flex items-baseline gap-2">
              <span
                className={`text-4xl font-black leading-none ${
                  health >= 75
                    ? 'text-emerald-400'
                    : health >= 50
                    ? 'text-amber-400'
                    : health >= 25
                    ? 'text-orange-400'
                    : 'text-rose-400'
                }`}
                style={{ fontFamily: "'Bebas Neue', sans-serif" }}
              >
                {health}
              </span>
              <span className="text-lg font-bold text-slate-600">%</span>
            </div>
            <div className="mt-2">
              <ProgressBar value={health} />
            </div>
          </div>
        </div>

        {/* Progress Breakdown */}
        <div className="space-y-3">
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-400 font-medium">Correct Picks</span>
            <span className="font-bold text-emerald-400">{correctPicks}</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-400 font-medium">Incorrect Picks</span>
            <span className="font-bold text-rose-400">{totalPicks - correctPicks}</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-slate-400 font-medium">Remaining</span>
            <span className="font-bold text-slate-500">{possiblePoints - totalPoints} pts possible</span>
          </div>
        </div>
      </div>

      {/* Court Lines Decoration */}
      <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-amber-500/20 to-transparent" />
    </div>
  )
}

function ProgressBar({ value }: { value: number }) {
  const [width, setWidth] = useState(0)

  useEffect(() => {
    setTimeout(() => setWidth(value), 100)
  }, [value])

  const getColor = () => {
    if (value >= 75) return 'bg-emerald-500'
    if (value >= 50) return 'bg-amber-500'
    if (value >= 25) return 'bg-orange-500'
    return 'bg-rose-500'
  }

  return (
    <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
      <div
        className={`h-full ${getColor()} rounded-full transition-all duration-1000 ease-out shadow-lg`}
        style={{
          width: `${width}%`,
          boxShadow: `0 0 12px ${
            value >= 75
              ? 'rgba(52, 211, 153, 0.5)'
              : value >= 50
              ? 'rgba(251, 191, 36, 0.5)'
              : value >= 25
              ? 'rgba(251, 146, 60, 0.5)'
              : 'rgba(251, 113, 133, 0.5)'
          }`,
        }}
      />
    </div>
  )
}
