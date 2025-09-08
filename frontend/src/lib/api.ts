import { Pet, JourneyState, MonthRecommendations } from './store'

const API_BASE = 'http://localhost:8000'

class APIError extends Error {
  constructor(message: string, public status: number) {
    super(message)
    this.name = 'APIError'
  }
}

async function apiCall<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  })

  if (!response.ok) {
    throw new APIError(`API call failed: ${response.statusText}`, response.status)
  }

  return response.json()
}

export const api = {
  // Pet management
  createPet: async (petData: Omit<Pet, 'id'>): Promise<Pet> => {
    return apiCall<Pet>('/profile', {
      method: 'POST',
      body: JSON.stringify(petData),
    })
  },

  // Journey management
  initializeJourney: async (petId: string, months: number = 15): Promise<JourneyState> => {
    return apiCall<JourneyState>('/journey', {
      method: 'POST',
      body: JSON.stringify({ petId, months }),
    })
  },

  updateJourneyState: async (action: string, payload: any): Promise<JourneyState> => {
    return apiCall<JourneyState>('/journey/state', {
      method: 'PATCH',
      body: JSON.stringify({ action, ...payload }),
    })
  },

  // Recommendations
  getRecommendations: async (journeyId: string, monthIdx: number): Promise<MonthRecommendations> => {
    return apiCall<MonthRecommendations>(`/recommendations?journeyId=${journeyId}&monthIdx=${monthIdx}`)
  },

  getAIRecommendations: async (journeyId: string, monthIdx: number, note: string): Promise<{
    summary: string
    items: Array<{
      section: string
      item: any
    }>
  }> => {
    return apiCall(`/ai/recs`, {
      method: 'POST',
      body: JSON.stringify({ journeyId, monthIdx, note }),
    })
  },

  // Analytics
  trackEvent: async (type: string, journeyId: string, meta?: any): Promise<void> => {
    return apiCall('/events', {
      method: 'POST',
      body: JSON.stringify({ type, journeyId, meta }),
    })
  },
}
