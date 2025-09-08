import { create } from 'zustand'
import { z } from 'zod'

// Schemas
export const PetSchema = z.object({
  id: z.string(),
  name: z.string(),
  species: z.enum(['dog', 'cat']),
  breed: z.string(),
  ageMonths: z.number(),
  // Step 1 fields
  gender: z.enum(['male', 'female', 'unknown']).optional(),
  householdType: z.enum(['apartment', 'house']).optional(),
  yardAccess: z.enum(['no_yard', 'small_yard', 'large_yard']).optional(),
  zipCode: z.string().optional(),
  // Step 2 fields
  weightLbs: z.number().optional(),
  heightAtShoulderInches: z.number().optional(),
  chewStrength: z.enum(['light', 'average', 'strong']).optional(),
  activityLevel: z.enum(['low', 'medium', 'high']).optional(),
  allergies: z.string().optional(),
  // Step 3 fields
  about: z.string().optional(), // Pet characteristics for recommendations
  appearance: z.string().optional(), // Physical appearance for avatar generation
  budgetBand: z.enum(['budget', 'moderate', 'premium']).optional(),
  brandPreferences: z.string().optional(),
})

export const RecommendationItemSchema = z.object({
  id: z.string(),
  title: z.string(),
  subtitle: z.string().optional(),
  tags: z.array(z.string()),
  price: z.string(),
  cadence: z.string().optional(),
  whyForPet: z.string(),
  isAIGenerated: z.boolean().default(false),
})

export const MonthRecommendationsSchema = z.object({
  summaryWhy: z.string(),
  subscriptions: z.array(RecommendationItemSchema),
  bundles: z.array(RecommendationItemSchema),
  singles: z.array(RecommendationItemSchema),
})

export const JourneyStateSchema = z.object({
  id: z.string(),
  petId: z.string(),
  current: z.number(),
  totalMonths: z.number(),
  decisions: z.record(z.string(), z.record(z.string(), z.record(z.string(), z.boolean()))), // monthIdx -> section -> itemId -> decision
})

export type Pet = z.infer<typeof PetSchema>
export type RecommendationItem = z.infer<typeof RecommendationItemSchema>
export type MonthRecommendations = z.infer<typeof MonthRecommendationsSchema>
export type JourneyState = z.infer<typeof JourneyStateSchema>

interface AppState {
  // Pet data
  pet: Pet | null
  
  // Journey data
  journey: JourneyState | null
  
  // Current month recommendations
  currentMonthRecommendations: MonthRecommendations | null
  
  // UI state
  isLoading: boolean
  error: string | null
  
  // Dog animation state
  dogPosition: number // 0 = start, 1 = CP1, etc.
  isAnimating: boolean
  
  // Actions
  setPet: (pet: Pet) => void
  setJourney: (journey: JourneyState) => void
  setCurrentMonthRecommendations: (recommendations: MonthRecommendations) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  setDogPosition: (position: number) => void
  setIsAnimating: (animating: boolean) => void
  
  // Journey actions
  makeDecision: (monthIdx: number, section: string, itemId: string, decision: boolean) => void
  makeAllDecisions: (monthIdx: number, section: string, decision: boolean) => void
  getItemDecision: (monthIdx: number, section: string, itemId: string) => boolean | undefined
  getSectionDecision: (monthIdx: number, section: string) => boolean | undefined
  completeMonth: (monthIdx: number) => void
  startJourney: () => void
  
  // Reset state
  reset: () => void
}

const initialState = {
  pet: null,
  journey: null,
  currentMonthRecommendations: null,
  isLoading: false,
  error: null,
  dogPosition: 0,
  isAnimating: false,
}

export const useAppStore = create<AppState>((set, get) => ({
  ...initialState,
  
  setPet: (pet) => set({ pet }),
  setJourney: (journey) => set({ journey }),
  setCurrentMonthRecommendations: (recommendations) => set({ currentMonthRecommendations: recommendations }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
  setDogPosition: (dogPosition) => set({ dogPosition }),
  setIsAnimating: (isAnimating) => set({ isAnimating }),
  
  makeDecision: (monthIdx, section, itemId, decision) => {
    const { journey } = get()
    if (!journey) return
    
    const newDecisions = { ...journey.decisions }
    if (!newDecisions[monthIdx.toString()]) {
      newDecisions[monthIdx.toString()] = {}
    }
    if (!newDecisions[monthIdx.toString()][section]) {
      newDecisions[monthIdx.toString()][section] = {}
    }
    newDecisions[monthIdx.toString()][section][itemId] = decision
    
    set({
      journey: {
        ...journey,
        decisions: newDecisions
      }
    })
  },

  makeAllDecisions: (monthIdx, section, decision) => {
    const { journey, currentMonthRecommendations } = get()
    if (!journey || !currentMonthRecommendations) return
    
    // Get all items in the section
    const sectionItems = currentMonthRecommendations[section as keyof typeof currentMonthRecommendations]
    if (!Array.isArray(sectionItems)) return
    
    const newDecisions = { ...journey.decisions }
    if (!newDecisions[monthIdx.toString()]) {
      newDecisions[monthIdx.toString()] = {}
    }
    if (!newDecisions[monthIdx.toString()][section]) {
      newDecisions[monthIdx.toString()][section] = {}
    }
    
    // Set decision for all items in the section
    sectionItems.forEach((item: RecommendationItem) => {
      newDecisions[monthIdx.toString()][section][item.id] = decision
    })
    
    set({
      journey: {
        ...journey,
        decisions: newDecisions
      }
    })
  },

  getItemDecision: (monthIdx, section, itemId) => {
    const { journey } = get()
    if (!journey) return undefined
    return journey.decisions[monthIdx.toString()]?.[section]?.[itemId]
  },

  getSectionDecision: (monthIdx, section) => {
    const { journey, currentMonthRecommendations } = get()
    if (!journey || !currentMonthRecommendations) return undefined
    
    const sectionItems = currentMonthRecommendations[section as keyof typeof currentMonthRecommendations]
    if (!Array.isArray(sectionItems)) return undefined
    
    const sectionDecisions = journey.decisions[monthIdx.toString()]?.[section] || {}
    
    if (Object.keys(sectionDecisions).length === 0) return undefined
    
    // Check if all items have the same decision
    const decisions = sectionItems.map((item: RecommendationItem) => sectionDecisions[item.id])
    const hasDecisions = decisions.filter((d: boolean | undefined) => d !== undefined)
    
    if (hasDecisions.length === 0) return undefined
    if (hasDecisions.length === sectionItems.length) {
      // All items have decisions - check if they're all the same
      if (hasDecisions.every((d: boolean | undefined) => d === true)) return true
      if (hasDecisions.every((d: boolean | undefined) => d === false)) return false
    }
    
    return undefined // Mixed decisions or incomplete
  },
  
  completeMonth: (monthIdx) => {
    const { journey } = get()
    if (!journey) return
    
    // When completing monthIdx, we should be at checkpoint (monthIdx + 2)
    // Month 0 completion -> checkpoint 2, Month 1 completion -> checkpoint 3, etc.
    const newCurrent = monthIdx + 2
    console.log('completeMonth: monthIdx=', monthIdx, 'setting current to', newCurrent)
    set({
      journey: {
        ...journey,
        current: newCurrent
      }
    })
  },
  
  startJourney: () => {
    const { journey } = get()
    if (!journey) return
    
    set({
      journey: {
        ...journey,
        current: 1 // Move to checkpoint 1
      }
      // Let the useEffect in CheckpointStrip handle dogPosition
    })
  },
  
  reset: () => set(initialState),
}))
