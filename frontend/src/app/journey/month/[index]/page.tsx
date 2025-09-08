"use client"

import { useEffect, useState, useRef } from "react"
import { useRouter, useParams } from "next/navigation"
import { useAppStore } from "@/lib/store"
import { api } from "@/lib/api"
import { CheckpointStrip } from "@/components/CheckpointStrip"
import { ProductSection } from "@/components/ProductSection"
import { AIRecommendationBox } from "@/components/AIRecommendationBox"
import { MonthRecap } from "@/components/MonthRecap"
import { LoadingSpinner } from "@/components/LoadingSpinner"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ChevronLeft } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { cn } from "@/lib/utils"

export default function MonthDetail() {
  const router = useRouter()
  const params = useParams()
  const monthIndex = parseInt(params.index as string)
  
  const { 
    pet, 
    journey, 
    currentMonthRecommendations, 
    setCurrentMonthRecommendations,
    isLoading,
    setLoading,
    setError,
    makeDecision,
    makeAllDecisions,
    getItemDecision,
    getSectionDecision,
    completeMonth,
    setDogPosition
  } = useAppStore()

  const [localRecommendations, setLocalRecommendations] = useState(currentMonthRecommendations)
  const [showCompletionAnimation, setShowCompletionAnimation] = useState(false)
  const [isCompleting, setIsCompleting] = useState(false)
  const [showAllergiesPopup, setShowAllergiesPopup] = useState(false)
  const isDecisionInProgress = useRef(false)

  useEffect(() => {
    // Redirect if no pet/journey or invalid month
    if (!pet || !journey) {
      router.push('/onboarding')
      return
    }

    if (monthIndex < 0 || monthIndex >= journey.totalMonths) {
      router.push('/journey')
      return
    }
  }, [pet, journey, monthIndex, router])

  // Close allergies popup when clicking outside
  useEffect(() => {
    const handleClickOutside = () => {
      if (showAllergiesPopup) {
        setShowAllergiesPopup(false)
      }
    }

    if (showAllergiesPopup) {
      document.addEventListener('click', handleClickOutside)
    }

    return () => {
      document.removeEventListener('click', handleClickOutside)
    }
  }, [showAllergiesPopup])

  useEffect(() => {
    // Load recommendations for this month
    // Skip reloading if we're in the middle of making a decision
    if (!isDecisionInProgress.current) {
      loadRecommendations()
    }
  }, [pet, journey, monthIndex])

  const loadRecommendations = async () => {
    if (!journey) return

    setLoading(true)
    try {
      const recommendations = await api.getRecommendations(journey.id, monthIndex)
      setCurrentMonthRecommendations(recommendations)
      setLocalRecommendations(recommendations)
    } catch (error) {
      console.error('Failed to load recommendations:', error)
      setError('Failed to load recommendations')
    } finally {
      setLoading(false)
    }
  }

  const handleItemDecision = (section: string, itemId: string, decision: boolean) => {
    if (!journey) return
    
    // Mark that we're making a decision to prevent useEffect from triggering
    isDecisionInProgress.current = true
    
    makeDecision(monthIndex, section, itemId, decision)
    
    // Reset the flag after a short delay
    setTimeout(() => {
      isDecisionInProgress.current = false
    }, 100)
    
    // Update backend - we'll need to update the API to handle individual items
    // For now, keeping it simple
    console.log(`Decision for ${section}/${itemId}: ${decision}`)
  }

  const handleSectionDecision = (section: string, decision: boolean) => {
    if (!journey) return
    
    // Mark that we're making a decision to prevent useEffect from triggering
    isDecisionInProgress.current = true
    
    makeAllDecisions(monthIndex, section, decision)
    
    // Reset the flag after a short delay
    setTimeout(() => {
      isDecisionInProgress.current = false
    }, 100)
    
    // Update backend
    console.log(`Section decision for ${section}: ${decision}`)
  }

  const handleCompleteMonth = async () => {
    if (!journey || isCompleting) return

    try {
      setIsCompleting(true)
      
      // Step 1: Update backend
      await api.updateJourneyState("completeMonth", {
        journeyId: journey.id,
        monthIdx: monthIndex
      })
      
      // Step 2: Update local state immediately
      completeMonth(monthIndex)
      
      // Step 3: Show focused checkpoint animation (zoom/center effect)
      setShowCompletionAnimation(true)
      await new Promise(resolve => setTimeout(resolve, 1500))
      
      // Step 4: Trigger dog animation to next checkpoint
      if (typeof window !== 'undefined' && (window as any).animateToNextCheckpoint) {
        // monthIndex is 0-based: Month 1=0, Month 2=1, etc.
        // After completing Month N, dog should be at checkpoint N+1
        // So: completing monthIndex should put dog at checkpoint (monthIndex + 2)
        const targetCheckpoint = monthIndex + 2
        console.log('Completing Month', monthIndex + 1, '(monthIndex=' + monthIndex + ') - dog should go to checkpoint', targetCheckpoint)
        await (window as any).animateToNextCheckpoint(targetCheckpoint)
        
        // CRITICAL: Ensure the dog position is set in the store after animation
        console.log('Animation completed, FORCING dog position in store to:', targetCheckpoint)
        setDogPosition(targetCheckpoint)
      }
      
      // Step 5: Wait a bit more to ensure dog position is fully set
      await new Promise(resolve => setTimeout(resolve, 200))
      
      // Step 6: Hide the zoom effect and wait for smooth transition
      setShowCompletionAnimation(false)
      await new Promise(resolve => setTimeout(resolve, 600)) // Increased to match CSS transition duration
      
      // Step 7: Navigate to next month or journey overview
      if (monthIndex + 1 < journey.totalMonths) {
        router.push(`/journey/month/${monthIndex + 1}`)
      } else {
        router.push('/journey')
      }
      
    } catch (error) {
      console.error('Failed to complete month:', error)
      setError('Failed to complete month')
      setShowCompletionAnimation(false)
    } finally {
      setIsCompleting(false)
    }
  }

  const handleAIRecommendation = (summary: string, items: any[]) => {
    if (!localRecommendations) return

    // Add AI items to local recommendations
    const updatedRecs = { ...localRecommendations }
    
    items.forEach(({ section, item }) => {
      if (section === 'subscriptions') {
        updatedRecs.subscriptions.push(item)
      } else if (section === 'bundles') {
        updatedRecs.bundles.push(item)
      } else if (section === 'singles') {
        updatedRecs.singles.push(item)
      }
    })

    setLocalRecommendations(updatedRecs)
  }

  if (isLoading) {
    return <LoadingSpinner />
  }

  if (!pet || !journey || !localRecommendations) {
    return null
  }

  // Check if all sections have at least one decision made
  const hasAllDecisions = ['subscriptions', 'bundles', 'singles'].every(section => {
    // Check if any item in this section has been decided
    const sectionItems = localRecommendations?.[section as keyof typeof localRecommendations]
    
    // Make sure it's an array before calling .some()
    if (!Array.isArray(sectionItems)) return false
    
    return sectionItems.some((item: any) => {
      const itemDecision = getItemDecision(monthIndex, section, item.id)
      return itemDecision !== undefined
    })
  })

  return (
    <div 
      className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50"
      style={{
        scrollBehavior: 'auto'
      }}
    >
      <div className="container mx-auto px-4 py-8 space-y-6">
        
        {/* Header */}
        <div className="flex items-center space-x-4">
          <Button
            variant="outline"
            size="sm"
            onClick={() => router.push('/journey')}
            className="flex items-center space-x-2"
          >
            <ChevronLeft className="h-4 w-4" />
            <span>Back to Journey</span>
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Month {monthIndex + 1} - {pet.name}'s Selections
            </h1>
            <p className="text-gray-600">{localRecommendations.summaryWhy}</p>
          </div>
        </div>

        {/* Compact Checkpoint Strip with focus effect */}
                  {/* Background overlay with blur effect during completion animation */}
          <AnimatePresence>
            {showCompletionAnimation && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.8, ease: "easeInOut" }}
                className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40"
              />
            )}
          </AnimatePresence>

          {/* Checkpoint Strip with focus animation */}
          <motion.div
            className={cn(
              "w-full relative transition-all duration-700 mt-10",
              showCompletionAnimation ? "z-50" : "z-10"
            )}
            animate={{
              scale: showCompletionAnimation ? 1.2 : 1,
              y: showCompletionAnimation ? -20 : 0,
            }}
            transition={{ 
              duration: 0.8, 
              ease: "easeInOut",
              type: "spring",
              stiffness: 100,
              damping: 15
            }}
          >
            <div className={cn(
              "rounded-2xl transition-all duration-700",
              showCompletionAnimation 
                ? "bg-white/95 backdrop-blur-lg shadow-2xl border border-purple-200 p-6" 
                : "bg-transparent"
            )}>
              <CheckpointStrip
                compact
                focusedCheckpoint={showCompletionAnimation ? monthIndex + 2 : undefined}
              />
              
              {/* Completion message overlay */}
              {showCompletionAnimation && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5, duration: 0.6 }}
                  className="text-center mt-6"
                >
                  <div className="bg-gradient-to-r from-green-500 to-emerald-500 text-white rounded-xl p-4 shadow-lg">
                    <h3 className="text-lg font-bold mb-2">
                      🎉 Month {monthIndex + 1} Complete!
                    </h3>
                    <p className="text-sm opacity-90">
                      Great choices! Moving to the next checkpoint...
                    </p>
                  </div>
                </motion.div>
              )}
            </div>
          </motion.div>

        {/* Main Content Grid */}
        <div className="grid lg:grid-cols-3 gap-6">
          
          {/* Left: Product Sections */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* Subscriptions */}
            {localRecommendations.subscriptions.length > 0 && (
              <ProductSection
                title="Subscriptions"
                subtitle="Regular deliveries for your pet's essentials"
                items={localRecommendations.subscriptions}
                monthIndex={monthIndex}
                section="subscriptions"
                getItemDecision={getItemDecision}
                getSectionDecision={getSectionDecision}
                onItemDecision={(itemId, decision) => handleItemDecision('subscriptions', itemId, decision)}
                onSectionDecision={(decision) => handleSectionDecision('subscriptions', decision)}
              />
            )}

            {/* Bundles */}
            {localRecommendations.bundles.length > 0 && (
              <ProductSection
                title="Bundles"
                subtitle="Curated product combinations with savings"
                items={localRecommendations.bundles}
                monthIndex={monthIndex}
                section="bundles"
                getItemDecision={getItemDecision}
                getSectionDecision={getSectionDecision}
                onItemDecision={(itemId, decision) => handleItemDecision('bundles', itemId, decision)}
                onSectionDecision={(decision) => handleSectionDecision('bundles', decision)}
              />
            )}

            {/* Singles */}
            {localRecommendations.singles.length > 0 && (
              <ProductSection
                title="Singles"
                subtitle="One-time purchases and special items"
                items={localRecommendations.singles}
                monthIndex={monthIndex}
                section="singles"
                getItemDecision={getItemDecision}
                getSectionDecision={getSectionDecision}
                onItemDecision={(itemId, decision) => handleItemDecision('singles', itemId, decision)}
                onSectionDecision={(decision) => handleSectionDecision('singles', decision)}
              />
            )}



            {/* Complete Month Button */}
            {hasAllDecisions && (
              <Card>
                <CardContent className="pt-6">
                  <div className="text-center space-y-4">
                    <div>
                      <h3 className="font-semibold text-lg">Ready for the next month?</h3>
                      <p className="text-gray-600">You've made all your selections for this month.</p>
                    </div>
                    <Button
                      onClick={handleCompleteMonth}
                      disabled={isLoading}
                      size="lg"
                      className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
                    >
                      {isLoading ? "Completing..." : "Complete Month & Continue"}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Right: Current Month + Recap */}
          <div className="space-y-4 relative">
            {/* Generated portrait badge (prototype) - blend with month card header (left) */}
            <div className="absolute -top-18 -right-7 z-20 pointer-events-none">
              {(() => {
                if (typeof window !== 'undefined') {
                  try {
                    const stored = localStorage.getItem('generatedPetImage')
                    if (stored) {
                      const img = JSON.parse(stored)
                      if (img?.b64) {
                        return (
                          <div className="rounded-full p-1 bg-gradient-to-br from-blue-500 to-indigo-500 shadow-2xl">
                            <div className="rounded-full bg-white p-1">
                              <img
                                src={`data:${img.mime};base64,${img.b64}`}
                                alt={`${pet.name} portrait`}
                                className="w-45 h-45 object-cover rounded-full shadow-xl border-4 border-white"
                              />
                            </div>
                          </div>
                        )
                      }
                      if (img?.loading === true) {
                        return (
                          <div className="rounded-full p-1 bg-gradient-to-br from-blue-500 to-indigo-500 shadow-2xl">
                            <div className="w-45 h-45 rounded-full bg-gray-100 flex items-center justify-center text-xs text-gray-500 border-4 border-white">
                              Generating...
                            </div>
                          </div>
                        )
                      }
                    }
                  } catch (e) {}
                }
                return null
              })()}
            </div>
            
            {/* Current Month Info */}
            <Card className="bg-gradient-to-br from-blue-50 to-indigo-100 border-blue-200 shadow-lg mt-0">
              <CardHeader className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-t-lg">
                <CardTitle className="text-xl font-bold flex items-center gap-2">
                  <span className="text-2xl">📅</span>
                  Month {monthIndex + 1}
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4">
                <div className="space-y-3">
                  {/* Pet Info Section */}
                  <div className="p-3 bg-white/80 rounded-lg border-l-4 border-blue-400">
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-blue-700 font-semibold flex items-center gap-2">
                        <span className="text-lg">{pet.species === 'dog' ? '🐕' : '🐱'}</span>
                        {pet.name}
                        {/* Breed pill inline with pet name */}
                        <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full font-medium">
                          {pet.breed && pet.breed.trim() && pet.breed !== pet.name ? pet.breed : 'Mixed Breed'}
                        </span>
                      </span>
                    </div>
                    <div className="text-sm text-blue-600 relative">
                      {pet.ageMonths + monthIndex} months old
                      {pet.allergies && (
                        <div className="relative inline-block ml-2">
                          <button 
                            className="text-xs bg-orange-100 text-orange-700 px-2 py-0.5 rounded-full hover:bg-orange-200 transition-colors cursor-pointer"
                            onClick={() => setShowAllergiesPopup(!showAllergiesPopup)}
                            title={`Click to view allergies: ${pet.allergies}`}
                          >
                            ⚠️ Allergies
                          </button>
                          
                          {/* Allergies Popup Card */}
                          <AnimatePresence>
                            {showAllergiesPopup && (
                              <motion.div
                                initial={{ opacity: 0, y: -10, scale: 0.95 }}
                                animate={{ opacity: 1, y: 0, scale: 1 }}
                                exit={{ opacity: 0, y: -10, scale: 0.95 }}
                                transition={{ duration: 0.2 }}
                                className="absolute top-full left-0 mt-2 z-50 bg-white border border-orange-200 rounded-lg shadow-lg p-3 min-w-48"
                                onClick={(e) => e.stopPropagation()}
                              >
                                <div className="flex items-center gap-2 mb-2">
                                  <span className="text-orange-600">⚠️</span>
                                  <span className="font-semibold text-orange-800 text-sm">Known Allergies</span>
                                </div>
                                <div className="text-sm text-gray-700 bg-orange-50 p-2 rounded border-l-2 border-orange-300">
                                  {pet.allergies}
                                </div>
                                <button 
                                  onClick={() => setShowAllergiesPopup(false)}
                                  className="absolute top-1 right-1 text-gray-400 hover:text-gray-600 text-sm"
                                >
                                  ✕
                                </button>
                              </motion.div>
                            )}
                          </AnimatePresence>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Stats Grid */}
                  <div className="grid grid-cols-2 gap-2">
                    <div className="p-2 bg-white/70 rounded-lg text-center">
                      <div className="text-lg font-bold text-indigo-800">
                        {['subscriptions', 'bundles', 'singles'].filter(section => 
                          getSectionDecision(monthIndex, section) !== undefined
                        ).length}/3
                      </div>
                      <div className="text-xs text-blue-600">Decisions Made</div>
                    </div>
                    <div className="p-2 bg-white/70 rounded-lg text-center">
                      <div className="text-lg font-bold text-indigo-800">
                        {Math.round(((monthIndex + 1) / 15) * 100)}%
                      </div>
                      <div className="text-xs text-blue-600">Complete</div>
                    </div>
                  </div>

                  {/* Life Stage & Focus */}
                  <div className="p-2 bg-white/70 rounded-lg">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm text-blue-700 font-medium">📈 Life Stage:</span>
                      <span className="text-sm font-semibold text-indigo-800">
                        {pet.ageMonths + monthIndex < 6 ? 'Puppy' : 
                         pet.ageMonths + monthIndex < 18 ? 'Young' : 
                         pet.ageMonths + monthIndex < 84 ? 'Adult' : 'Senior'}
                      </span>
                    </div>
                    <div className="text-xs text-blue-600">
                      🎯 Focus: {pet.ageMonths + monthIndex < 6 ? 'Growth & Development' : 
                                pet.ageMonths + monthIndex < 18 ? 'Training & Socialization' : 
                                pet.ageMonths + monthIndex < 84 ? 'Maintenance & Health' : 'Comfort & Care'}
                    </div>
                  </div>

                  {/* Lifetime Journey Stats */}
                  <div className="p-2 bg-white/70 rounded-lg">
                    <div className="text-xs text-blue-700 font-medium mb-2 text-center">📊 Lifetime Journey Stats</div>
                    <div className="grid grid-cols-3 gap-1 mb-2">
                      <div className="p-1 bg-green-50 rounded text-center">
                        <div className="text-xs font-bold text-green-700">
                          {journey?.decisions ? Object.values(journey.decisions)
                            .flatMap(monthDec => Object.values(monthDec))
                            .flatMap(sectionDec => Object.values(sectionDec))
                            .filter(d => d === true).length : 0}
                        </div>
                        <div className="text-xs text-green-600">Accepted</div>
                      </div>
                      <div className="p-1 bg-red-50 rounded text-center">
                        <div className="text-xs font-bold text-red-700">
                          {journey?.decisions ? Object.values(journey.decisions)
                            .flatMap(monthDec => Object.values(monthDec))
                            .flatMap(sectionDec => Object.values(sectionDec))
                            .filter(d => d === false).length : 0}
                        </div>
                        <div className="text-xs text-red-600">Skipped</div>
                      </div>
                      <div className="p-1 bg-purple-50 rounded text-center">
                        <div className="text-xs font-bold text-purple-700">
                          {Object.keys(journey?.decisions || {}).length}
                        </div>
                        <div className="text-xs text-purple-600">Months Done</div>
                      </div>
                    </div>
                    
                    {/* Additional Insights */}
                    <div className="grid grid-cols-2 gap-1">
                      <div className="p-1 bg-orange-50 rounded text-center">
                        <div className="text-xs font-bold text-orange-700">
                          {journey?.decisions ? Math.round(
                            (Object.values(journey.decisions)
                              .flatMap(monthDec => Object.values(monthDec))
                              .flatMap(sectionDec => Object.values(sectionDec))
                              .filter(d => d === true).length / 
                            (Object.values(journey.decisions)
                              .flatMap(monthDec => Object.values(monthDec))
                              .flatMap(sectionDec => Object.values(sectionDec)).length || 1)) * 100
                          ) : 0}%
                        </div>
                        <div className="text-xs text-orange-600">Accept Rate</div>
                      </div>
                      <div className="p-1 bg-teal-50 rounded text-center">
                        <div className="text-xs font-bold text-teal-700">
                          {journey ? journey.totalMonths - Object.keys(journey.decisions || {}).length : 0}
                        </div>
                        <div className="text-xs text-teal-600">Remaining</div>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* AI Recommendation Box */}
            <AIRecommendationBox
              journeyId={journey.id}
              monthIdx={monthIndex}
              petName={pet.name}
              onRecommendation={handleAIRecommendation}
            />

            {/* Previous Month Recap */}
            {monthIndex > 0 && (
              <MonthRecap 
                monthIndex={monthIndex - 1}
                journey={journey}
                recommendations={localRecommendations}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
