"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Heart, Calendar, Info } from "lucide-react"
import { Pet, JourneyState } from "@/lib/store"

interface PetProfileCardProps {
  pet: Pet
  journey: JourneyState
}

export function PetProfileCard({ pet, journey }: PetProfileCardProps) {
  const getAgeGroup = (ageMonths: number) => {
    if (ageMonths <= 12) return "Puppy/Kitten"
    if (ageMonths <= 84) return "Adult"
    return "Senior"
  }

  const getLifeStage = (ageMonths: number) => {
    if (ageMonths <= 6) return "Growing rapidly"
    if (ageMonths <= 12) return "Developing"
    if (ageMonths <= 84) return "Maintaining health"
    return "Senior care"
  }

  const currentAgeMonths = pet.ageMonths + journey.current
  const ageYears = Math.floor(currentAgeMonths / 12)
  const remainingMonths = currentAgeMonths % 12

  const formatAge = () => {
    if (ageYears === 0) {
      return `${currentAgeMonths} months`
    } else if (remainingMonths === 0) {
      return `${ageYears} year${ageYears > 1 ? 's' : ''}`
    } else {
      return `${ageYears} year${ageYears > 1 ? 's' : ''}, ${remainingMonths} month${remainingMonths > 1 ? 's' : ''}`
    }
  }

  const journeyProgress = (journey.current / journey.totalMonths) * 100

  return (
    <Card className="w-full shadow-lg bg-white/90 backdrop-blur border-0 max-h-[80vh] overflow-y-auto">
      <CardHeader className="text-center pb-4">
        <div className="flex justify-center mb-3">
          {(() => {
            if (typeof window !== 'undefined') {
              try {
                const stored = localStorage.getItem('generatedPetImage')
                if (stored) {
                  const img = JSON.parse(stored)
                  if (img?.b64) {
                    return (
                      <div className="w-25 h-25 rounded-full overflow-hidden bg-gradient-to-br from-purple-400 to-blue-400 p-0.5">
                        <img
                          src={`data:${img.mime};base64,${img.b64}`}
                          alt={`${pet.name} portrait`}
                          className="w-full h-full object-cover rounded-full"
                        />
                      </div>
                    )
                  }
                  if (img?.loading === true) {
                    return (
                      <div className="w-25 h-25 rounded-full bg-gradient-to-br from-purple-400 to-blue-400 flex items-center justify-center text-xs text-white">
                        Generating...
                      </div>
                    )
                  }
                }
              } catch (e) {}
            }
            return (
              <div className="w-16 h-16 bg-gradient-to-br from-purple-400 to-blue-400 rounded-full flex items-center justify-center text-3xl">
                {pet.species === 'dog' ? '🐕' : '🐱'}
              </div>
            )
          })()}
        </div>
        <CardTitle className="text-2xl font-bold">{pet.name}</CardTitle>
        <div className="flex justify-center space-x-2">
          <Badge variant="secondary">
            {pet.species === 'dog' ? 'Dog' : 'Cat'}
          </Badge>
          <Badge>
            {pet.breed}
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-3">
        
        {/* Age & Life Stage */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Calendar className="h-4 w-4 text-purple-600" />
              <span className="font-medium">Current Age</span>
            </div>
            <span className="text-gray-700">{formatAge()}</span>
          </div>
          
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Heart className="h-4 w-4 text-red-500" />
              <span className="font-medium">Life Stage</span>
            </div>
            <span className="text-gray-700">{getAgeGroup(currentAgeMonths)}</span>
          </div>
        </div>

        {/* Portrait section removed - will be shown as external badge */}

        {/* Journey Progress */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-medium text-sm">Journey Progress</span>
            <span className="text-sm text-gray-600">{journey.current}/{journey.totalMonths} months</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-gradient-to-r from-purple-500 to-blue-500 h-2 rounded-full transition-all duration-500"
              style={{ width: `${journeyProgress}%` }}
            />
          </div>
        </div>

        {/* Focus Area */}
        <div className="bg-blue-50 p-3 rounded-lg">
          <div className="flex items-start space-x-2">
            <Info className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
            <div>
              <p className="font-medium text-blue-900 text-sm">Current Focus</p>
              <p className="text-blue-800 text-sm">{getLifeStage(currentAgeMonths)}</p>
            </div>
          </div>
        </div>

        {/* Detailed Information - 2 Column Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 border-t pt-3">
          {/* Left Column */}
          <div className="space-y-4">
            {/* Pet Details */}
            <div className="space-y-2">
              <h4 className="font-medium text-gray-800 text-sm">Pet Details</h4>
              
              {pet.gender && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Gender</span>
                  <span className="text-sm font-medium text-gray-800 capitalize">{pet.gender}</span>
                </div>
              )}
              
              {pet.weightLbs && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Weight</span>
                  <span className="text-sm font-medium text-gray-800">{pet.weightLbs} lbs</span>
                </div>
              )}
              
              {pet.heightAtShoulderInches && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Height (shoulder)</span>
                  <span className="text-sm font-medium text-gray-800">{pet.heightAtShoulderInches} inches</span>
                </div>
              )}
              
              {pet.activityLevel && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Activity Level</span>
                  <Badge variant={pet.activityLevel === 'high' ? 'default' : 'secondary'}>
                    {pet.activityLevel.charAt(0).toUpperCase() + pet.activityLevel.slice(1)}
                  </Badge>
                </div>
              )}
              
              {pet.chewStrength && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Chew Strength</span>
                  <Badge variant={pet.chewStrength === 'strong' ? 'default' : 'secondary'}>
                    {pet.chewStrength.charAt(0).toUpperCase() + pet.chewStrength.slice(1)}
                  </Badge>
                </div>
              )}
            </div>
          </div>

          {/* Right Column */}
          <div className="space-y-4">
            {/* Living Situation */}
            {(pet.householdType || pet.yardAccess || pet.zipCode) && (
              <div className="space-y-2">
                <h4 className="font-medium text-gray-800 text-sm">Living Situation</h4>
                
                {pet.householdType && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Home Type</span>
                    <Badge variant="secondary">
                      {pet.householdType.charAt(0).toUpperCase() + pet.householdType.slice(1)}
                    </Badge>
                  </div>
                )}
                
                {pet.yardAccess && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Yard Access</span>
                    <span className="text-sm font-medium text-gray-800">
                      {pet.yardAccess.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </span>
                  </div>
                )}
                
                {pet.zipCode && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Location</span>
                    <span className="text-sm font-medium text-gray-800">{pet.zipCode}</span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Parent Preferences - Full Width */}
        {(pet.budgetBand || pet.brandPreferences) && (
          <div className="space-y-2 border-t pt-3">
            <h4 className="font-medium text-gray-800 text-sm">Parent Preferences</h4>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {pet.budgetBand && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Budget Range</span>
                  <Badge variant="default">
                    {pet.budgetBand.charAt(0).toUpperCase() + pet.budgetBand.slice(1)}
                  </Badge>
                </div>
              )}
              
              {pet.brandPreferences && (
                <div>
                  <p className="font-medium text-sm text-gray-700">Brand Preferences</p>
                  <p className="text-sm text-gray-600">{pet.brandPreferences}</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Special Notes - Full Width */}
        {(pet.allergies || pet.about) && (
          <div className="space-y-3 border-t pt-3">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {pet.allergies && (
                <div>
                  <p className="font-medium text-sm text-gray-700">Allergies & Restrictions</p>
                  <p className="text-sm text-gray-600">{pet.allergies}</p>
                </div>
              )}
              
              {pet.about && (
                <div>
                  <p className="font-medium text-sm text-gray-700">About {pet.name}</p>
                  <p className="text-sm text-gray-600">{pet.about}</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Next Milestone */}
        {journey.current < journey.totalMonths && (
          <div className="bg-purple-50 p-3 rounded-lg">
            <p className="font-medium text-purple-900 text-sm">Next Milestone</p>
            <p className="text-purple-800 text-sm">
              Month {journey.current + 1} - Continue the journey with personalized recommendations
            </p>
          </div>
        )}

        {/* Journey Complete */}
        {journey.current >= journey.totalMonths && (
          <div className="bg-green-50 p-3 rounded-lg text-center">
            <p className="font-medium text-green-900">🎉 Journey Complete!</p>
            <p className="text-green-800 text-sm">
              {pet.name} has completed their 15-month journey
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
