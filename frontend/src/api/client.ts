const API_BASE = '/api/v1'

export interface Bracket {
  id: number
  name: string
  bracket_type: string
  total_points: number
  correct_picks: number
  total_picks: number
}

export interface Game {
  id: number
  espn_id: string
  home_team: string
  away_team: string
  home_score: number | null
  away_score: number | null
  status: string
  round: string
  region?: string
  home_team_id?: number
  home_team_name?: string
  home_team_seed?: number
  away_team_id?: number
  away_team_name?: string
  away_team_seed?: number
  is_upset?: boolean
}

export interface BracketDetails extends Bracket {
  picks: Pick[]
}

export interface Pick {
  id: number
  game_id: number
  predicted_winner: string
  points_earned: number
  is_correct: boolean | null
}

class ApiClient {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    })

    if (!response.ok) {
      throw new Error(`API request failed: ${response.statusText}`)
    }

    return response.json()
  }

  async getBrackets(): Promise<Bracket[]> {
    return this.request<Bracket[]>('/brackets')
  }

  async getBracket(id: number): Promise<BracketDetails> {
    return this.request<BracketDetails>(`/brackets/${id}`)
  }

  async getGames(): Promise<Game[]> {
    return this.request<Game[]>('/games')
  }

  async syncESPN(): Promise<{ message: string }> {
    return this.request('/sync', { method: 'POST' })
  }

  async sendTestNotification(): Promise<{ message: string }> {
    return this.request('/notify', { method: 'POST' })
  }

  async createBracket(data: {
    name: string
    bracket_type: string
    picks: { game_id: number; predicted_winner_id: number }[]
  }): Promise<Bracket> {
    return this.request('/brackets', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }
}

export const apiClient = new ApiClient()
