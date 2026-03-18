import { useEffect, useState } from 'react'
import { apiClient, type BracketDetails } from '../api/client'

export function useBracket(bracketId: number | null) {
  const [bracket, setBracket] = useState<BracketDetails | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!bracketId) {
      setLoading(false)
      return
    }

    const fetchBracket = async () => {
      try {
        setLoading(true)
        const data = await apiClient.getBracket(bracketId)
        setBracket(data)
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch bracket')
        setBracket(null)
      } finally {
        setLoading(false)
      }
    }

    fetchBracket()
  }, [bracketId])

  return { bracket, loading, error }
}
