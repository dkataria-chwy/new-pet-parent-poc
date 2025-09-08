import { describe, it, expect, beforeEach } from 'vitest'
import { useAppStore } from '../store'

describe('App Store', () => {
  beforeEach(() => {
    // Reset store before each test
    useAppStore.getState().reset()
  })

  it('initializes with correct default state', () => {
    const state = useAppStore.getState()
    
    expect(state.pet).toBeNull()
    expect(state.journey).toBeNull()
    expect(state.currentMonthRecommendations).toBeNull()
    expect(state.isLoading).toBe(false)
    expect(state.error).toBeNull()
    expect(state.dogPosition).toBe(0)
    expect(state.isAnimating).toBe(false)
  })

  it('updates pet correctly', () => {
    const mockPet = {
      id: 'pet-1',
      name: 'Max',
      species: 'dog' as const,
      breed: 'Golden Retriever',
      ageMonths: 24,
    }

    useAppStore.getState().setPet(mockPet)
    
    expect(useAppStore.getState().pet).toEqual(mockPet)
  })

  it('makes decisions correctly', () => {
    const mockJourney = {
      id: 'journey-1',
      petId: 'pet-1',
      current: 1,
      totalMonths: 15,
      decisions: {},
    }

    useAppStore.getState().setJourney(mockJourney)
    useAppStore.getState().makeDecision(0, 'subscriptions', 'item-1', true)
    
    const updatedJourney = useAppStore.getState().journey
    expect(updatedJourney?.decisions['0']['subscriptions']['item-1']).toBe(true)
  })

  it('completes month correctly', () => {
    const mockJourney = {
      id: 'journey-1',
      petId: 'pet-1',
      current: 1,
      totalMonths: 15,
      decisions: {},
    }

    useAppStore.getState().setJourney(mockJourney)
    useAppStore.getState().completeMonth(0) // Completing month 0 should set current to 2
    
    const updatedJourney = useAppStore.getState().journey
    expect(updatedJourney?.current).toBe(2)
  })

  it('resets state correctly', () => {
    const mockPet = {
      id: 'pet-1',
      name: 'Max',
      species: 'dog' as const,
      breed: 'Golden Retriever',
      ageMonths: 24,
    }

    useAppStore.getState().setPet(mockPet)
    useAppStore.getState().setLoading(true)
    useAppStore.getState().setError('Test error')
    
    useAppStore.getState().reset()
    
    const state = useAppStore.getState()
    expect(state.pet).toBeNull()
    expect(state.isLoading).toBe(false)
    expect(state.error).toBeNull()
  })
})
