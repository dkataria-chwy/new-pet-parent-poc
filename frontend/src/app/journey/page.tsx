"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAppStore } from "@/lib/store"
import { CheckpointStrip } from "@/components/CheckpointStrip"
import { PetProfileCard } from "@/components/PetProfileCard"
import { LoadingSpinner } from "@/components/LoadingSpinner"

export default function JourneyOverview() {
  const router = useRouter()
  const { pet, journey, isLoading } = useAppStore()

  useEffect(() => {
    // Redirect to onboarding if no pet/journey
    if (!isLoading && (!pet || !journey)) {
      router.push('/onboarding')
    }
  }, [pet, journey, isLoading, router])

  if (isLoading) {
    return <LoadingSpinner />
  }

  if (!pet || !journey) {
    return null // Will redirect
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50">
      <div className="container mx-auto px-4 py-8 space-y-8">
        
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold text-gray-900">
            {pet.name}'s Journey
          </h1>
          <p className="text-gray-600">
            A personalized 15-month adventure of growth and discovery
          </p>
        </div>

        {/* Pet Profile Card - Centered and positioned after header */}
        <div className="flex justify-center">
          <div className="w-full max-w-md">
            <PetProfileCard pet={pet} journey={journey} />
          </div>
        </div>

        {/* Checkpoint Strip */}
        <div className="w-full">
          <CheckpointStrip />
        </div>
      </div>
    </div>
  )
}
