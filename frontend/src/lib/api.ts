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

  getPet: async (petId: string): Promise<Pet> => {
    return apiCall<Pet>(`/pet/${petId}`)
  },

  // Journey management
  getAllJourneys: async (): Promise<{
    journeys: Array<{
      journey_id: string
      pet_id: string
      current_month: number
      total_months: number
      pet_name: string
      species: string
      breed: string
      age_months: number
    }>
  }> => {
    return apiCall('/journeys')
  },

  getJourney: async (journeyId: string): Promise<JourneyState> => {
    return apiCall<JourneyState>(`/journey/${journeyId}`)
  },

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

  // On-demand recommendations (new AI-powered system)
  getOnDemandRecommendations: async (journeyId: string, monthIdx: number, userQuery: string, topK: number = 20): Promise<{
    timestamp: string
    query_used: string
    rationale: string
    total_products: number
    products: Array<{
      rank: number
      sku: string
      parentSKU: string
      name: string
      similarity: number
      product_link: string
    }>
    user_query: string
    journey_id: string
    pet_name: string
    pet_species: string
  }> => {
    return apiCall(`/on-demand-recommendations`, {
      method: 'POST',
      body: JSON.stringify({ 
        journey_id: journeyId, 
        month_idx: monthIdx,
        user_query: userQuery, 
        top_k: topK 
      }),
    })
  },

  // Analytics
  trackEvent: async (type: string, journeyId: string, meta?: any): Promise<void> => {
    return apiCall('/events', {
      method: 'POST',
      body: JSON.stringify({ type, journeyId, meta }),
    })
  },

  // Subscription Plans (Structured Pipeline)
  getSubscriptionPlan: async (journeyId: string, monthIdx: number): Promise<{
    success: boolean
    data: {
      subscription_products: Array<{
        slot_id: number
        sku: string
        product_name: string
        product_link: string
        product_price_current: number
        autoship_eligible: boolean
        top_family: string
        bucket: string
        subscription_rationale: string
        estimated_frequency: string
        personalized_note: string
      }>
      one_time_products: Array<{
        slot_id: number
        sku: string
        product_name: string
        product_link: string
        product_price_current: number
        autoship_eligible: boolean
        top_family: string
        bucket: string
        one_time_rationale: string
        personalized_note: string
      }>
      overall_strategy: string
      metadata: {
        journey_id: string
        month_idx: number
        model: string
        generated_at: string
        tokens: {
          prompt: number
          completion: number
          total: number
        }
        elapsed_seconds: number
      }
    }
    from_cache: boolean
    generated_at: string
  }> => {
    return apiCall(`/subscription-plan/${journeyId}/${monthIdx}`)
  },

  // Generic POST method
  post: async <T = any>(endpoint: string, data: any): Promise<{ data: T }> => {
    const result = await apiCall<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    })
    return { data: result }
  },
}
