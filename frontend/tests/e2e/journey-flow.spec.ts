import { test, expect } from '@playwright/test'

test.describe('Chewy Journey E2E Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Mock API calls since we won't have backend running in CI
    await page.route('/api/**', async route => {
      const url = route.request().url()
      
      if (url.includes('/profile') && route.request().method() === 'POST') {
        await route.fulfill({
          json: {
            id: 'pet-123',
            name: 'Max',
            species: 'dog',
            breed: 'Golden Retriever',
            ageMonths: 24,
            allergies: 'None',
            about: 'Very energetic'
          }
        })
      } else if (url.includes('/journey') && route.request().method() === 'POST') {
        await route.fulfill({
          json: {
            id: 'journey-123',
            petId: 'pet-123',
            current: 0,
            totalMonths: 15,
            decisions: {}
          }
        })
      } else if (url.includes('/recommendations')) {
        await route.fulfill({
          json: {
            summaryWhy: 'For Max, a adult dog, we have curated essentials focused on maintaining health.',
            subscriptions: [{
              id: 'sub-1',
              title: 'Premium Adult Dog Food',
              subtitle: 'Tailored nutrition for daily energy',
              tags: ['Premium', 'Balanced'],
              price: '$24.99',
              cadence: 'Every 4 weeks',
              whyForPet: 'Perfect protein balance supports Max\'s daily activity level.',
              isAIGenerated: false
            }],
            bundles: [{
              id: 'bundle-1',
              title: 'Dental Care Bundle',
              subtitle: 'Complete oral health kit',
              tags: ['Dental', 'Bundle'],
              price: '$31.99',
              whyForPet: 'Dental health is crucial for Max\'s overall wellness.',
              isAIGenerated: false
            }],
            singles: [{
              id: 'single-1',
              title: 'Enrichment Puzzle Toy',
              subtitle: 'Mental stimulation and fun',
              tags: ['Toy', 'Mental Health'],
              price: '$12.99',
              whyForPet: 'Mental stimulation keeps Max engaged.',
              isAIGenerated: false
            }]
          }
        })
      } else {
        await route.fulfill({
          json: { success: true }
        })
      }
    })
  })

  test('complete onboarding and start journey', async ({ page }) => {
    // Start at welcome page
    await page.goto('/')
    
    // Check welcome page elements
    await expect(page.getByText('Chewy Journey')).toBeVisible()
    await expect(page.getByText('Create Your Pet\'s Profile')).toBeVisible()
    
    // Click create profile
    await page.getByText('Create Your Pet\'s Profile').click()
    await expect(page).toHaveURL('/onboarding')
    
    // Fill out onboarding form - Step 1
    await expect(page.getByText('Let\'s meet your pet')).toBeVisible()
    await page.fill('input[placeholder*="Max, Luna, Buddy"]', 'Max')
    await page.click('button:has-text("Dog")')
    await page.fill('input[placeholder*="Golden Retriever"]', 'Golden Retriever')
    
    // Go to step 2
    await page.getByText('Next').click()
    await expect(page.getByText('A few more details')).toBeVisible()
    
    // Fill age
    await page.fill('input[type="number"]', '24')
    await page.fill('input[placeholder*="Chicken, grain-free"]', 'None')
    
    // Go to step 3
    await page.getByText('Next').click()
    await expect(page.getByText('Final touches')).toBeVisible()
    
    // Fill about section
    await page.fill('textarea', 'Very energetic and loves to play fetch')
    
    // Submit and start journey
    await page.getByText('Start Journey').click()
    
    // Should redirect to journey overview
    await expect(page).toHaveURL('/journey')
    await expect(page.getByText('Max\'s Journey')).toBeVisible()
    
    // Check checkpoint strip exists
    await expect(page.locator('[aria-label="Checkpoint 1"]')).toBeVisible()
    await expect(page.getByText('Start Journey')).toBeVisible()
  })

  test('locked checkpoints are not clickable', async ({ page }) => {
    // Navigate to journey overview
    await page.goto('/journey')
    
    // Checkpoint 1 should be unlocked (or current)
    const checkpoint1 = page.locator('[aria-label="Checkpoint 1"]')
    await expect(checkpoint1).not.toHaveAttribute('aria-disabled', 'true')
    
    // Checkpoint 2 and beyond should be locked
    const checkpoint2 = page.locator('[aria-label="Checkpoint 2"]')
    await expect(checkpoint2).toHaveAttribute('aria-disabled', 'true')
    
    const checkpoint3 = page.locator('[aria-label="Checkpoint 3"]')
    await expect(checkpoint3).toHaveAttribute('aria-disabled', 'true')
  })
})