"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { X, AlertTriangle, CheckCircle } from "lucide-react"
import { Pet } from "@/lib/store"
import { api } from "@/lib/api"

interface PetProfileUpdateModalProps {
  isOpen: boolean
  onClose: () => void
  pet: Pet
  monthIndex: number
  onUpdate: (updatedPet: Pet) => void
}

interface UpdateForm {
  weightLbs: number | ""
  heightAtShoulderInches: number | ""
  chewStrength: "light" | "average" | "strong" | ""
  activityLevel: "low" | "medium" | "high" | ""
  healthIssues: string
  productReturns: string
}

interface AIFollowUp {
  field: string
  question: string
  explanation: string
  suggestedValue?: string
}

const CHEW_STRENGTH_OPTIONS = [
  { value: "light", label: "Light", description: "Gentle chewing, prefers soft items" },
  { value: "average", label: "Average", description: "Normal chewing behavior" },
  { value: "strong", label: "Strong", description: "Power chewer, destroys toys quickly" }
]

const ACTIVITY_LEVEL_OPTIONS = [
  { value: "low", label: "Low", description: "Prefers lounging, short walks" },
  { value: "medium", label: "Medium", description: "Balanced activity, daily exercise" },
  { value: "high", label: "High", description: "Very energetic, needs lots of exercise" }
]

export function PetProfileUpdateModal({ isOpen, onClose, pet, monthIndex, onUpdate }: PetProfileUpdateModalProps) {
  const [form, setForm] = useState<UpdateForm>({
    weightLbs: pet.weightLbs || "",
    heightAtShoulderInches: pet.heightAtShoulderInches || "",
    chewStrength: pet.chewStrength || "",
    activityLevel: pet.activityLevel || "",
    healthIssues: "",
    productReturns: ""
  })

  // Keep form in sync when parent updates pet (after commit) and reset state
  useEffect(() => {
    setForm({
      weightLbs: pet.weightLbs || "",
      heightAtShoulderInches: pet.heightAtShoulderInches || "",
      chewStrength: (pet as any).chewStrength || "",
      activityLevel: (pet as any).activityLevel || "",
      healthIssues: "",
      productReturns: "",
    })
    // Clear all follow-up state when modal reopens/pet changes
    setAiWarnings([])
    setShowWarnings(false)
    setValidationError(null)
  }, [pet])

  // Remove all per-field validation, follow-up, and warning state/logic
  // Only keep aiWarnings (array of {field, question, explanation}) and a two-step submit process
  const [aiWarnings, setAiWarnings] = useState<AIFollowUp[]>([])
  const [showWarnings, setShowWarnings] = useState(false)
  const [isValidating, setIsValidating] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [validationError, setValidationError] = useState<string | null>(null)

  const handleInputChange = (field: keyof UpdateForm, value: string | number) => {
    setForm(prev => ({ ...prev, [field]: value }))
  }

  // On 'Update Profile', validate all fields once and show warnings
  const handleValidateAndShowWarnings = async () => {
    setIsValidating(true)
    try {
      const response = await api.post('/checkpoint/validate', {
        petId: pet.id,
        monthIndex,
        currentData: form,
        previousData: {
          weightLbs: pet.weightLbs,
          heightAtShoulderInches: pet.heightAtShoulderInches,
          chewStrength: pet.chewStrength,
          activityLevel: pet.activityLevel,
        },
      })
      setValidationError(null)
      if ((response.data as any).hasAnomalies) {
        setAiWarnings((response.data as any).followUps || [])
      } else {
        setAiWarnings([])
      }
      setShowWarnings(true)
    } catch (error) {
      setValidationError('Couldn’t validate right now. Please try again in a moment.')
    } finally {
      setIsValidating(false)
    }
  }

  const submitUpdate = async () => {
    setIsSubmitting(true)
    try {
      const updateData = {
        ...pet,
        weightLbs: form.weightLbs ? Number(form.weightLbs) : undefined,
        heightAtShoulderInches: form.heightAtShoulderInches ? Number(form.heightAtShoulderInches) : undefined,
        chewStrength: form.chewStrength || undefined,
        activityLevel: form.activityLevel || undefined
      }

      // Save checkpoint data
      console.log('[Checkpoint] Committing update', { updateData })
      const commitResp = await api.post('/checkpoint/commit', {
        petId: pet.id,
        monthIndex,
        checkpointData: {
          healthIssues: form.healthIssues,
          productReturns: form.productReturns,
          timestamp: new Date().toISOString(),
          aiWarnings: aiWarnings, // Include AI warnings
          userResponses: null // Could track user responses to warnings
        },
        petUpdates: updateData
      })
      console.log('[Checkpoint] Commit response', commitResp)
      // Prefer server-returned pet if available (persists to DB)
      const serverPet = (commitResp as any)?.data?.pet
      onUpdate(serverPet ? serverPet : updateData)
      onClose()
    } catch (error) {
      console.error('[Checkpoint] Failed to update pet profile:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  // On 'Confirm Profile Updates', just submitUpdate (never re-validate)
  const handleConfirmAndSubmit = async () => {
    setIsSubmitting(true)
    try {
      const updateData = {
        ...pet,
        weightLbs: form.weightLbs ? Number(form.weightLbs) : undefined,
        heightAtShoulderInches: form.heightAtShoulderInches ? Number(form.heightAtShoulderInches) : undefined,
        chewStrength: form.chewStrength || undefined,
        activityLevel: form.activityLevel || undefined
      }
      const commitResp = await api.post('/checkpoint/commit', {
        petId: pet.id,
        monthIndex,
        checkpointData: {
          healthIssues: form.healthIssues,
          productReturns: form.productReturns,
          timestamp: new Date().toISOString()
        },
        petUpdates: updateData
      })
      const serverPet = (commitResp as any)?.data?.pet
      onUpdate(serverPet ? serverPet : updateData)
      onClose()
    } catch (error) {
      setValidationError('Failed to update pet profile. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  // In the JSX, show warnings for all fields after validation, and use two-step submit
  const renderWarning = (field: string) => {
    if (!showWarnings) return null
    const warning = aiWarnings.find(f => f.field === field)
    if (!warning) return null
    return (
      <div className="flex items-start border-l-4 border-yellow-400 bg-white rounded-md p-2 pl-3 gap-2 mt-1">
        <AlertTriangle className="text-yellow-500 w-4 h-4 mt-0.5 flex-shrink-0" />
        <div className="flex-1 text-xs text-gray-800">
          <span className="font-semibold mr-1">Warning</span>
          <span className="text-yellow-600">★</span>
          <span className="ml-1 text-gray-500">(AI generated)</span>
          <div className="font-medium mt-0.5">{warning.question}</div>
          <div className="text-gray-600">{warning.explanation}</div>
        </div>
      </div>
    )
  }

  const skipUpdate = () => {
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
      
      {/* Modal */}
      <div className="relative z-10 w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        <Card className="w-full shadow-2xl bg-white border-0">
          <CardHeader className="text-center pb-4 relative">
            <Button
              variant="ghost"
              size="sm"
              className="absolute right-4 top-4"
              onClick={onClose}
            >
              <X className="h-4 w-4" />
            </Button>
            
            <CardTitle className="text-2xl font-bold text-gray-900">
              Update {pet.name}'s Profile
            </CardTitle>
            <CardDescription className="text-lg">
              Month {monthIndex + 1} Checkpoint - Let's track {pet.name}'s growth and changes
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-6">
              <>
                {validationError && (
                  <div className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-700">
                    {validationError}
                  </div>
                )}
                {/* Current Measurements */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="weight">Current Weight (lbs)</Label>
                    <Input
                      id="weight"
                      type="number"
                      step="0.1"
                      placeholder={pet.weightLbs ? `Previously: ${pet.weightLbs} lbs` : "Enter weight"}
                      value={form.weightLbs}
                      onChange={(e) => handleInputChange('weightLbs', parseFloat(e.target.value) || "")}
                    />
                    {renderWarning('weightLbs')}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="height">Height at Shoulder (inches)</Label>
                    <Input
                      id="height"
                      type="number"
                      step="0.1"
                      placeholder={pet.heightAtShoulderInches ? `Previously: ${pet.heightAtShoulderInches}"` : "Enter height"}
                      value={form.heightAtShoulderInches}
                      onChange={(e) => handleInputChange('heightAtShoulderInches', parseFloat(e.target.value) || "")}
                    />
                    {renderWarning('heightAtShoulderInches')}
                  </div>
                </div>

                {/* Behavioral Changes */}
                <div className="space-y-4">
                  <div className="space-y-3">
                    <Label>Chew Strength</Label>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                      {CHEW_STRENGTH_OPTIONS.map((option) => (
                        <button
                          key={option.value}
                          type="button"
                          onClick={() => {
                            handleInputChange('chewStrength', option.value)
                          }}
                          className={`p-3 rounded-lg border text-left transition-all ${
                            form.chewStrength === option.value
                              ? 'border-blue-500 bg-blue-50'
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          <div className="font-medium">{option.label}</div>
                          <div className="text-sm text-gray-600">{option.description}</div>
                        </button>
                      ))}
                    </div>
                    {renderWarning('chewStrength')}
                  </div>

                  <div className="space-y-3">
                    <Label>Activity Level</Label>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                      {ACTIVITY_LEVEL_OPTIONS.map((option) => (
                        <button
                          key={option.value}
                          type="button"
                          onClick={() => {
                            handleInputChange('activityLevel', option.value)
                          }}
                          className={`p-3 rounded-lg border text-left transition-all ${
                            form.activityLevel === option.value
                              ? 'border-blue-500 bg-blue-50'
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          <div className="font-medium">{option.label}</div>
                          <div className="text-sm text-gray-600">{option.description}</div>
                        </button>
                      ))}
                    </div>
                    {renderWarning('activityLevel')}
                  </div>
                </div>

                {/* Health & Issues */}
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="health">Any health issues this month?</Label>
                    <Input
                      id="health"
                      placeholder="e.g., teething, skin irritation, digestive issues (or leave blank)"
                      value={form.healthIssues}
                      onChange={(e) => handleInputChange('healthIssues', e.target.value)}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="returns">Any product returns or issues?</Label>
                    <Input
                      id="returns"
                      placeholder="e.g., toys too soft, food caused upset stomach (or leave blank)"
                      value={form.productReturns}
                      onChange={(e) => handleInputChange('productReturns', e.target.value)}
                    />
                  </div>
                </div>

                {/* Action Buttons */}
                {!showWarnings ? (
                  <Button
                    onClick={handleValidateAndShowWarnings}
                    disabled={isValidating || isSubmitting}
                    className="flex-1"
                  >
                    {isValidating ? 'Validating...' : 'Update Profile'}
                  </Button>
                ) : (
                  <Button
                    onClick={handleConfirmAndSubmit}
                    disabled={isSubmitting}
                    className="flex-1"
                  >
                    {isSubmitting ? 'Updating...' : 'Confirm Profile Updates'}
                  </Button>
                )}
                <Button
                  variant="outline"
                  onClick={skipUpdate}
                  disabled={isValidating || isSubmitting}
                >
                  Skip for Now
                </Button>
              </>
            
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

