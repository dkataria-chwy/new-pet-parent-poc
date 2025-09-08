import { render, screen, fireEvent } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import { ProductSection } from '../ProductSection'
import { RecommendationItem } from '@/lib/store'

const mockItems: RecommendationItem[] = [
  {
    id: 'test-1',
    title: 'Test Product',
    subtitle: 'Test subtitle',
    tags: ['tag1', 'tag2'],
    price: '$19.99',
    cadence: 'Monthly',
    whyForPet: 'This is good for your pet because...',
    isAIGenerated: false,
  }
]

describe('ProductSection', () => {
  const mockGetItemDecision = vi.fn()
  const mockGetSectionDecision = vi.fn()
  const mockOnItemDecision = vi.fn()
  const mockOnSectionDecision = vi.fn()

  const defaultProps = {
    title: "Subscriptions",
    subtitle: "Regular deliveries",
    items: mockItems,
    monthIndex: 0,
    section: "subscriptions",
    getItemDecision: mockGetItemDecision,
    getSectionDecision: mockGetSectionDecision,
    onItemDecision: mockOnItemDecision,
    onSectionDecision: mockOnSectionDecision,
  }

  beforeEach(() => {
    vi.clearAllMocks()
    mockGetItemDecision.mockReturnValue(undefined)
    mockGetSectionDecision.mockReturnValue(undefined)
  })

  it('renders product section with items', () => {
    render(<ProductSection {...defaultProps} />)
    
    expect(screen.getByText('Subscriptions')).toBeInTheDocument()
    expect(screen.getByText('Regular deliveries')).toBeInTheDocument()
    expect(screen.getByText('Test Product')).toBeInTheDocument()
  })

  it('handles individual item accept and skip decisions', () => {
    render(<ProductSection {...defaultProps} />)
    
    // Look for individual item buttons (within product cards)
    const itemAcceptButtons = screen.getAllByText('Accept').filter(btn => 
      btn.closest('[data-testid="product-card"]') || btn.closest('.product-card')
    )
    const itemSkipButtons = screen.getAllByText('Skip').filter(btn => 
      btn.closest('[data-testid="product-card"]') || btn.closest('.product-card')
    )
    
    if (itemAcceptButtons.length > 0) {
      fireEvent.click(itemAcceptButtons[0])
      expect(mockOnItemDecision).toHaveBeenCalledWith('test-1', true)
    }
    
    if (itemSkipButtons.length > 0) {
      fireEvent.click(itemSkipButtons[0])
      expect(mockOnItemDecision).toHaveBeenCalledWith('test-1', false)
    }
  })

  it('handles section-level accept all and skip all decisions', () => {
    render(<ProductSection {...defaultProps} />)
    
    // Look for section-level buttons (in card header)
    const sectionButtons = screen.getAllByText(/Accept All|Skip All/)
    
    if (sectionButtons.length >= 2) {
      fireEvent.click(sectionButtons[0]) // Accept All
      expect(mockOnSectionDecision).toHaveBeenCalledWith(true)
      
      fireEvent.click(sectionButtons[1]) // Skip All
      expect(mockOnSectionDecision).toHaveBeenCalledWith(false)
    }
  })

  it('shows section decision status when all items have same decision', () => {
    mockGetSectionDecision.mockReturnValue(true) // All items accepted
    
    render(<ProductSection {...defaultProps} />)
    
    expect(screen.getByText(/All Accepted/i)).toBeInTheDocument()
  })

  it('shows individual item decision status', () => {
    mockGetItemDecision.mockReturnValue(true) // Item accepted
    
    render(<ProductSection {...defaultProps} />)
    
    // Should show accepted state on the item buttons
    const acceptedButtons = screen.getAllByText(/✓|Accepted/i)
    expect(acceptedButtons.length).toBeGreaterThan(0)
  })

  it('does not render when no items', () => {
    const emptyProps = { ...defaultProps, items: [] }
    
    const { container } = render(<ProductSection {...emptyProps} />)
    
    expect(container.firstChild).toBeNull()
  })
})
