import { useEffect, useState } from 'react'
import { apiClient, type Game } from '../api/client'

export function useGames() {
  const [games, setGames] = useState<Game[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchGames = async () => {
      try {
        setLoading(true)
        const data = await apiClient.getGames()
        setGames(data)
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch games')
        setGames([])
      } finally {
        setLoading(false)
      }
    }

    fetchGames()

    // Poll for updates every 30 seconds
    const interval = setInterval(fetchGames, 30000)
    return () => clearInterval(interval)
  }, [])

  return { games, loading, error }
}
