"use client"

import { useEffect, useState, useRef } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { useRouter } from "next/navigation"
import { useAppStore } from "@/lib/store"
import { Button } from "@/components/ui/button"
import { Check, Lock, Heart } from "lucide-react"
import { cn } from "@/lib/utils"
import { api } from "@/lib/api"

interface CheckpointStripProps {
  compact?: boolean
  focusedCheckpoint?: number // For zoomed effect
  onPlayTTS?: () => void // Handler to play TTS audio
  playingTTS?: boolean // Whether TTS is currently playing
  ttsCheckpoint?: number // Which checkpoint should show the speaker button (defaults to current)
}

export function CheckpointStrip({ compact = false, focusedCheckpoint, onPlayTTS, playingTTS = false, ttsCheckpoint }: CheckpointStripProps) {
  const router = useRouter()
  const { 
    journey, 
    dogPosition, 
    isAnimating, 
    setDogPosition, 
    setIsAnimating,
    setError,
    startJourney
  } = useAppStore()

  const [hasStarted, setHasStarted] = useState(false)
  const [dogIsRunning, setDogIsRunning] = useState(false)

  useEffect(() => {
    if (journey) {
      setHasStarted(journey.current > 0)
      // Dog position: 0 = start position, 1 = CP1, 2 = CP2, etc.
      // journey.current: 0 = no checkpoints reached, 1 = CP1 reached, 2 = CP2 reached, etc.
      console.log('CheckpointStrip useEffect - journey.current:', journey.current, 'current dogPosition:', dogPosition, 'compact:', compact)
      
      // Only update if there's actually a mismatch AND we're not in the middle of animations
      const animationInProgress = isAnimating || dogIsRunning
      
      // Only sync when loading existing journeys (not during normal gameplay)
      // This prevents interference with completion animations
      const isInitialLoad = dogPosition === 0 && journey.current > 0
      if (!animationInProgress && isInitialLoad && dogPosition !== journey.current) {
        console.log('🔄 INITIAL LOAD SYNC: dogPosition:', dogPosition, '→', journey.current)
        setDogPosition(journey.current)
      }
    }
  }, [journey?.current, setDogPosition, compact, dogPosition])



  if (!journey) return null

  // Show 10 checkpoints at a time with sliding window
  const CHECKPOINTS_PER_VIEW = 10
  const currentCheckpoint = journey.current
  
  // Calculate which checkpoints to show (sliding window)
  const getVisibleCheckpoints = () => {
    const totalCheckpoints = journey.totalMonths
    // For positions 0-8 (including before start), always show checkpoints 1-10
    if (currentCheckpoint <= 8) {
      // If we have 15 total months, we should definitely show 10 checkpoints
      const count = totalCheckpoints >= 15 ? CHECKPOINTS_PER_VIEW : Math.min(CHECKPOINTS_PER_VIEW, totalCheckpoints)
      return Array.from({ length: count }, (_, i) => i + 1)
    }
    
    // If current checkpoint is near the end, show last 10
    if (currentCheckpoint > totalCheckpoints - 2) {
      const start = Math.max(1, totalCheckpoints - CHECKPOINTS_PER_VIEW + 1)
      const count = totalCheckpoints - start + 1
      console.log('End position - showing checkpoints', start, 'to', totalCheckpoints)
      return Array.from({ length: count }, (_, i) => start + i)
    }
    
    // Otherwise, center around current checkpoint (show current in middle)
    const start = Math.max(1, currentCheckpoint - 4)
    const end = Math.min(totalCheckpoints, start + CHECKPOINTS_PER_VIEW - 1)
    console.log('Middle position - showing checkpoints', start, 'to', end)
    return Array.from({ length: end - start + 1 }, (_, i) => start + i)
  }

  const visibleCheckpoints = getVisibleCheckpoints()
  console.log('Visible checkpoints:', visibleCheckpoints, 'current:', currentCheckpoint)

  const handleStart = async () => {
    if (!journey || hasStarted || isAnimating) return

    try {
      setIsAnimating(true)
      setHasStarted(true) // Set this immediately to enable the road animation
      
      // Track start event (optional - don't fail if this fails)
      try {
        await api.trackEvent("journey_started", journey.id)
      } catch (trackError) {
        console.warn('Failed to track start event:', trackError)
      }
      
      // Animate dog from start position (0) to CP1 (1)
      await animateDogTo(1)
      
      // Update local state immediately
      startJourney()
      
      // Try to update backend (optional)
      try {
        await api.updateJourneyState("completeMonth", {
          journeyId: journey.id,
          monthIdx: -1 // Special case to move from 0 to 1
        })
      } catch (apiError) {
        console.warn('Failed to update journey state:', apiError)
        // Continue anyway - the UI state is already updated
      }
      
      // Open Month 1
      router.push('/journey/month/0')
      
    } catch (error) {
      console.error('Failed to start journey:', error)
      setError('Failed to start journey')
      setHasStarted(false) // Reset on error
    } finally {
      setIsAnimating(false)
    }
  }

  const handleCheckpointClick = async (checkpointIndex: number) => {
    if (!journey || isAnimating) return

    const monthIndex = checkpointIndex - 1
    
    // Only allow clicking if checkpoint is unlocked (current or previous)
    if (checkpointIndex > journey.current) return

    // Log navigation event
    try {
      await fetch('http://localhost:8000/events', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: "checkpoint_navigation",
          journeyId: journey.id,
          meta: {
            fromCheckpoint: journey.current,
            toCheckpoint: checkpointIndex,
            navigationDirection: checkpointIndex > journey.current ? "forward" : "backward",
            isRevisit: checkpointIndex < journey.current
          }
        })
      })
    } catch (error) {
      console.warn('Failed to log navigation event:', error)
    }

    if (checkpointIndex === journey.current && hasStarted) {
      // Open the current month
      router.push(`/journey/month/${monthIndex}`)
    } else if (checkpointIndex < journey.current) {
      // Allow viewing completed months
      router.push(`/journey/month/${monthIndex}`)
    }
  }

  const [currentAnimationPath, setCurrentAnimationPath] = useState("")

  const animateDogTo = async (targetPosition: number): Promise<void> => {
    return new Promise((resolve) => {
      const startPosition = dogPosition
      
      if (startPosition === targetPosition) {
        resolve()
        return
      }
      
      // Generate path segment for this animation
      const pathSegment = getPathSegment(startPosition, targetPosition)
      setCurrentAnimationPath(pathSegment)
      setDogIsRunning(true)
      
      // The PathFollowingDog component will handle the animation
      // and call this callback when complete
      const handleComplete = () => {
        // Immediately update dog position when animation completes
        setDogPosition(targetPosition)
        setDogIsRunning(false)
        setCurrentAnimationPath("")
        console.log('Animation completed, dog position set to:', targetPosition)
        resolve()
      }
      
      // Store the completion handler for the PathFollowingDog component
      if (typeof window !== 'undefined') {
        (window as any).__dogAnimationComplete = handleComplete
      }
    })
  }

  // Expose function for external animation triggers
  useEffect(() => {
    const animateToNextCheckpoint = async (targetPosition: number) => {
      setIsAnimating(true)
      setDogIsRunning(true)
      await animateDogTo(targetPosition)
      setIsAnimating(false)
    }

    // Store the function globally for month completion
    if (typeof window !== 'undefined') {
      (window as any).animateToNextCheckpoint = animateToNextCheckpoint
    }
  }, [])

  const getCheckpointStatus = (checkpointIndex: number) => {
    if (checkpointIndex < journey.current) {
      return 'completed' // Past checkpoints are green
    } else if (checkpointIndex === journey.current) {
      return 'current' // Current checkpoint (where dog is)
    } else {
      return 'locked' // All future checkpoints are locked (gray)
    }
  }

  const getCheckpointPosition = (index: number) => {
    if (focusedCheckpoint) {
      // When focused, center the focused checkpoint and scale others around it
      const offset = (index - focusedCheckpoint) * 80 // pixels between checkpoints when focused
      return `calc(50% + ${offset}px)`
    }
    // Normal distribution across the width
    return `${((index - 1) / (journey.totalMonths - 1)) * 100}%`
  }

  const CheckpointMarker = ({ index, status }: { index: number, status: string }) => {
    const isClickable = status === 'current' || status === 'completed' || status === 'unlocked'
    const isFocused = focusedCheckpoint === index
    
    console.log(`Checkpoint ${index}: status=${status}, journey.current=${journey.current}`)
    
    return (
      <div className="flex flex-col items-center">
        <motion.button
          onClick={() => handleCheckpointClick(index)}
          disabled={!isClickable || isAnimating}
          aria-label={`Checkpoint ${index}`}
          aria-disabled={!isClickable}
          initial={false}
          animate={{
            scale: isFocused ? 1.2 : 1, // Reduced from 1.3 to 1.2 for less jarring effect
          }}
          transition={{
            duration: 0.5, // Slower, smoother transition
            ease: "easeOut" // Gentler easing
          }}
          className={cn(
            "relative w-12 h-12 rounded-full transition-all duration-200 flex items-center justify-center shadow-lg",
            {
              // Completed: Green circle with white check
              'bg-green-500 border-4 border-green-200 text-white cursor-pointer hover:bg-green-600 hover:scale-110': status === 'completed',
              // Current: Orange circle with number (where dog is)
              'bg-orange-500 border-4 border-orange-200 text-white cursor-pointer hover:bg-orange-600 hover:scale-110': status === 'current',
              // Locked: Light gray circle with darker border and lock
              'bg-gray-100 border-4 border-gray-300 text-gray-500 cursor-not-allowed': status === 'locked',
            }
          )}
        >
          {status === 'completed' && (
            <>
              <span className="text-lg font-bold">{index}</span>
              {/* Small green checkmark badge in bottom-right corner */}
              <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-green-600 rounded-full flex items-center justify-center border-2 border-white">
                <Check className="w-3 h-3 text-white" />
              </div>
            </>
          )}
          {status === 'locked' && (
            <>
              <span className="text-lg font-bold text-gray-500">{index}</span>
              {/* Small lock badge in top-right corner */}
              <div className="absolute -top-1 -right-1 w-5 h-5 bg-gray-500 rounded-full flex items-center justify-center border-2 border-white">
                <Lock className="w-3 h-3 text-white" />
              </div>
            </>
          )}
          {status === 'current' && (
            <span className="text-lg font-bold">{index}</span>
          )}
          {/* Speaker icon badge - shows on the checkpoint matching ttsCheckpoint (or current if not specified) */}
          {onPlayTTS && index === (ttsCheckpoint ?? journey.current) + 1 && (
            <div
              onClick={(e) => {
                e.stopPropagation()
                onPlayTTS()
              }}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault()
                  e.stopPropagation()
                  onPlayTTS()
                }
              }}
              className="absolute -bottom-1 -right-1 w-6 h-6 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-full flex items-center justify-center border-2 border-white shadow-md hover:scale-110 transition-transform duration-200 cursor-pointer"
              title={playingTTS ? "Pause audio" : "Listen to monthly summary"}
            >
              {playingTTS ? (
                <svg className="w-3 h-3 text-white animate-pulse" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/>
                </svg>
              ) : (
                <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z"/>
                </svg>
              )}
            </div>
          )}
        </motion.button>
        {!compact && (
          <span className={cn(
            "text-xs mt-2 transition-all duration-200",
            isFocused ? "text-purple-700 font-semibold" : "text-gray-600"
          )}>
            CP{index}
          </span>
        )}
      </div>
    )
  }

  const RunningDog = () => {
    // Create a bouncing, running dog animation
    return (
      <motion.div
        className="w-12 h-12 flex items-center justify-center"
        animate={dogIsRunning ? {
          y: [0, -8, 0, -4, 0], // Bouncing motion for running
          rotate: [0, 3, 0, -3, 0], // Slight rotation for realism
        } : {
          y: [0, -2, 0], // Gentle idle animation
        }}
        transition={dogIsRunning ? {
          duration: 0.5,
          repeat: Infinity,
          ease: "easeInOut"
        } : {
          duration: 2,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      >
        <div className="relative">
          {/* Simple Dog Emoji - flipped to face right */}
          <div className="w-12 h-12 flex items-center justify-center">
            <span className="text-3xl" style={{ transform: 'scaleX(-1)' }}>🐕</span>
          </div>
          
          {/* Running effects when moving */}
          {dogIsRunning && (
            <>
              {/* Speed lines behind the dog */}
              <motion.div
                className="absolute -left-3 top-1/2 transform -translate-y-1/2 z-0"
                animate={{
                  opacity: [0, 1, 0],
                  x: [-8, 2],
                }}
                transition={{
                  duration: 0.2,
                  repeat: Infinity,
                  ease: "linear"
                }}
              >
                <div className="flex space-x-1">
                  <div className="w-1 h-0.5 bg-orange-400 rounded-full"></div>
                  <div className="w-1 h-0.5 bg-orange-400 rounded-full"></div>
                  <div className="w-1 h-0.5 bg-orange-400 rounded-full"></div>
                </div>
              </motion.div>
              
              {/* Dust cloud under the dog */}
              <motion.div
                className="absolute -bottom-2 left-1/2 transform -translate-x-1/2 z-0"
                animate={{
                  scale: [0.5, 1.5, 0.5],
                  opacity: [0.3, 0.7, 0.3],
                }}
                transition={{
                  duration: 0.3,
                  repeat: Infinity,
                  ease: "easeInOut"
                }}
              >
                <div className="w-8 h-3 bg-gray-300 rounded-full blur-sm opacity-50"></div>
              </motion.div>

              {/* Paw prints effect */}
              <motion.div
                className="absolute -left-6 top-3 z-0"
                animate={{
                  opacity: [0, 0.8, 0],
                  scale: [0.5, 1, 0.5],
                }}
                transition={{
                  duration: 0.4,
                  repeat: Infinity,
                  delay: 0.1
                }}
              >
                <span className="text-xs opacity-60">🐾</span>
              </motion.div>

              <motion.div
                className="absolute -left-4 top-6 z-0"
                animate={{
                  opacity: [0, 0.8, 0],
                  scale: [0.5, 1, 0.5],
                }}
                transition={{
                  duration: 0.4,
                  repeat: Infinity,
                  delay: 0.3
                }}
              >
                <span className="text-xs opacity-60">🐾</span>
              </motion.div>
            </>
          )}


        </div>
      </motion.div>
    )
  }

  // Build SVG path for the road - different configs for different contexts
  const buildRoadPath = () => {
    let marginX, roadY, containerWidth, containerHeight
    
    if (focusedCheckpoint) {
      // Focused mode (when a checkpoint is highlighted) - ONLY for popups/modals
      marginX = 60
      roadY = 12
      containerWidth = 800
      containerHeight = 24
    } else {
      // Both main page AND month pages get the same full-width layout
      marginX = 80
      roadY = 16
      containerWidth = 1400 // Full width for 10 checkpoints
      containerHeight = 32
    }
    
    // Build checkpoint positions only for visible checkpoints, evenly spaced across container width
    const visibleCount = visibleCheckpoints.length
    const step = visibleCount > 1 ? containerWidth / (visibleCount - 1) : 0
    
    const points = []
    for (let i = 0; i < visibleCount; i++) {
      points.push({ x: marginX + i * step, y: roadY })
    }
    
    // Add start position before first checkpoint - moved further left to avoid overlap
    const startPoint = { x: marginX - 80, y: roadY }
    
    // Build SVG path that extends the full container width
    const pathStartX = 0
    const pathEndX = containerWidth + marginX * 2
    const pathString = `M ${pathStartX} ${roadY} L ${pathEndX} ${roadY}`
    
    // Reduced logging for performance
    
    // Return both the full path and the checkpoint positions, plus container info
    const allPoints = [startPoint, ...points]
    
    return { pathString, points: allPoints, containerHeight }
  }

  const { pathString, points: roadPoints, containerHeight } = buildRoadPath()

  // Get path segment for animation
  const getPathSegment = (fromIdx: number, toIdx: number) => {
    // Map checkpoint numbers to roadPoints indices
    const getPointIndex = (checkpointNum: number) => {
      if (checkpointNum === 0) return 0 // Start position
      const visibleIndex = visibleCheckpoints.indexOf(checkpointNum)
      return visibleIndex === -1 ? -1 : visibleIndex + 1 // +1 because roadPoints[0] is start
    }
    
    const fromPointIdx = getPointIndex(fromIdx)
    const toPointIdx = getPointIndex(toIdx)
    
    if (fromPointIdx === -1 || toPointIdx === -1 || !roadPoints[fromPointIdx] || !roadPoints[toPointIdx]) {
      console.log('Invalid path segment:', { fromIdx, toIdx, fromPointIdx, toPointIdx, visibleCheckpoints })
      return ""
    }
    
    const from = roadPoints[fromPointIdx]
    const to = roadPoints[toPointIdx]
    return `M ${from.x} ${from.y} L ${to.x} ${to.y}`
  }

  const PathFollowingDog = () => {
    const handleComplete = () => {
      // Call the stored completion handler
      if (typeof window !== 'undefined' && (window as any).__dogAnimationComplete) {
        (window as any).__dogAnimationComplete()
      }
    }

    return (
      <AnimatePresence>
        {dogIsRunning && currentAnimationPath && (
          <motion.div
            initial={{ offsetDistance: "0%" }}
            animate={{ offsetDistance: "100%" }}
            transition={{ duration: 1.2, ease: "easeInOut" }}
            onAnimationComplete={handleComplete}
            className={`absolute z-40 pointer-events-none transform ${compact ? '-translate-y-4' : '-translate-y-8'}`}
            style={{ 
              offsetPath: `path('${currentAnimationPath}')`,
              offsetRotate: "auto"
            } as any}
          >
            <div className="transform -translate-x-1/2 -translate-y-1/2">
              <RunningDog />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    )
  }

  // Static dog position when not animating
  const StaticDog = () => {
    // Only show if we're not in any animation state
    if (isAnimating || dogIsRunning) return null
    
    // dogPosition: 0 = start, 1 = CP1, 2 = CP2, etc.
    // roadPoints: [start, visibleCP1, visibleCP2, ...]
    // We need to map dogPosition to the correct index in roadPoints
    console.log('StaticDog - dogPosition:', dogPosition, 'journey.current:', journey?.current, 'roadPoints length:', roadPoints.length)
    console.log('visibleCheckpoints:', visibleCheckpoints)
    
    let pointIndex = dogPosition
    
    // If dogPosition > 0 (not at start), find its index in visibleCheckpoints
    if (dogPosition > 0) {
      const checkpointIndex = visibleCheckpoints.indexOf(dogPosition)
      if (checkpointIndex === -1) {
        // Dog is at a checkpoint not currently visible, don't show
        console.log('Dog checkpoint', dogPosition, 'not in visible checkpoints')
        return null
      }
      // roadPoints[0] is start, so visible checkpoint index + 1
      pointIndex = checkpointIndex + 1
    }
    
    console.log('Using roadPoints index:', pointIndex, 'for dogPosition:', dogPosition)
    const point = roadPoints[pointIndex]
    
    if (!point) return null
    
    return (
      <div
        className="absolute z-40 pointer-events-none transform -translate-x-1/2 -translate-y-full"
        style={{
          left: `${point.x}px`,
          top: `${point.y - (compact ? 15 : 30)}px`, // Different spacing: 15px for month page, 30px for main page
        }}
      >
        <RunningDog />
      </div>
    )
  }

  return (
    <div className={cn(
      "w-full",
      compact ? "py-6" : "py-12",
      focusedCheckpoint ? "bg-gradient-to-r from-purple-50 to-blue-50 transition-colors duration-500" : ""
    )}>
      <div className={cn(
        "mx-auto px-4",
        focusedCheckpoint ? "max-w-4xl" : "w-full"
      )}
      style={{ 
        minWidth: focusedCheckpoint ? 'auto' : '1600px',
        transition: 'all 0.5s ease-in-out' // Smooth transitions
      }}>
        
        {/* The Road/Track */}
        <div className={cn(
          "relative transition-all duration-500",
          focusedCheckpoint ? "py-8" : "py-8"
        )}>
          
          {/* SVG Road */}
          <div 
            className="relative" 
            style={{ 
              height: `${containerHeight * 2}px`,
              minWidth: focusedCheckpoint ? 'auto' : '1600px',
              transition: 'all 0.5s ease-in-out' // Smooth container transitions
            }}
          >
            <svg 
              className="absolute inset-0 w-full h-full" 
              width="100%" 
              height="100%" 
              viewBox={`0 0 ${focusedCheckpoint ? 800 : 1600} ${containerHeight * 2}`}
              style={{ transition: 'viewBox 0.5s ease-in-out' }} // Smooth viewBox transitions
            >
              {/* Road background */}
              <path
                d={pathString}
                stroke="#e5e7eb"
                strokeWidth="22"
                fill="none"
                strokeLinecap="round"
              />
              {/* Road surface */}
              <path
                d={pathString}
                stroke="#cbd5e1"
                strokeWidth="14"
                fill="none"
                strokeLinecap="round"
              />
              {/* Progress line */}
              {hasStarted && (
                <motion.path
                  d={pathString}
                  stroke="url(#progressGradient)"
                  strokeWidth="14"
                  fill="none"
                  strokeLinecap="round"
                  initial={{ pathLength: 0 }}
                  animate={{ 
                    pathLength: journey.current / journey.totalMonths 
                  }}
                  transition={{ duration: 0.8, ease: "easeOut" }}
                />
              )}
              {/* Gradient definition */}
              <defs>
                <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#a855f7" />
                  <stop offset="50%" stopColor="#3b82f6" />
                  <stop offset="100%" stopColor="#10b981" />
                </linearGradient>
              </defs>
            </svg>

            {/* Checkpoints positioned along the road */}
            {visibleCheckpoints.map((checkpoint, index) => {
              const point = roadPoints[index + 1] // +1 because roadPoints[0] is start position
              if (!point) return null
              
              return (
                <div
                  key={checkpoint}
                  className="absolute transform -translate-x-1/2 -translate-y-1/2"
                  style={{ left: `${point.x}px`, top: `${point.y}px` }}
                >
                  <CheckpointMarker 
                    index={checkpoint} 
                    status={getCheckpointStatus(checkpoint)}
                  />
                </div>
              )
            })}

            {/* Dog Components */}
            <PathFollowingDog />
            <StaticDog />
          </div>
        </div>

        {/* Start Button - positioned well below the track */}
        {!hasStarted && !compact && (
          <div className="flex justify-center mt-6 mb-8">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
            >
              <Button
                onClick={handleStart}
                disabled={isAnimating}
                size="lg"
                className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-lg px-12 py-4 rounded-full shadow-xl hover:shadow-2xl transition-all duration-300 hover:scale-105"
              >
                {isAnimating ? (
                  <span className="flex items-center space-x-2">
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                      className="w-5 h-5 border-2 border-white border-t-transparent rounded-full"
                    />
                    <span>Starting Journey...</span>
                  </span>
                ) : (
                  "Start Journey 🚀"
                )}
              </Button>
            </motion.div>
          </div>
        )}

        {/* Legend/summary card removed per request */}

        {/* Focused checkpoint info */}
        {focusedCheckpoint && (
          <motion.div
            className="text-center mt-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
          >
            <div className="bg-white rounded-lg p-6 shadow-xl inline-block">
              <h3 className="text-xl font-bold text-gray-800 mb-2">
                Progressing to Checkpoint {focusedCheckpoint}! 🎉
              </h3>
              <p className="text-gray-600">
                Great progress! Your pet's journey continues...
              </p>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  )
}