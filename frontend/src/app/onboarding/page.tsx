"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ChevronLeft, ChevronRight, Heart } from "lucide-react"
import { useAppStore } from "@/lib/store"
import { api } from "@/lib/api"
import { motion } from "framer-motion"

const SPECIES_OPTIONS = [
  { value: "dog", label: "Dog", icon: "🐕" },
  { value: "cat", label: "Cat", icon: "🐱" }
]

const GENDER_OPTIONS = [
  { value: "male", label: "Male" },
  { value: "female", label: "Female" },
  { value: "unknown", label: "Unknown" }
]

const HOUSEHOLD_OPTIONS = [
  { value: "apartment", label: "Apartment", icon: "🏢" },
  { value: "house", label: "House", icon: "🏠" }
]

const YARD_OPTIONS = [
  { value: "no_yard", label: "No Yard" },
  { value: "small_yard", label: "Small Yard" },
  { value: "large_yard", label: "Large Yard" }
]

const CHEW_STRENGTH_OPTIONS = [
  { value: "light", label: "Light" },
  { value: "average", label: "Average" },
  { value: "strong", label: "Strong" }
]

const ACTIVITY_LEVEL_OPTIONS = [
  { value: "low", label: "Low" },
  { value: "medium", label: "Medium" },
  { value: "high", label: "High" }
]

const BUDGET_OPTIONS = [
  { value: "budget", label: "Budget ($20-40/month)" },
  { value: "moderate", label: "Moderate ($40-80/month)" },
  { value: "premium", label: "Premium ($80+/month)" }
]

interface OnboardingForm {
  name: string
  species: "dog" | "cat" | ""
  breed: string
  ageMonths: number | ""
  // Step 1 fields
  gender: "male" | "female" | "unknown" | ""
  householdType: "apartment" | "house" | ""
  yardAccess: "no_yard" | "small_yard" | "large_yard" | ""
  zipCode: string
  // Step 2 fields
  weightLbs: number | ""
  heightAtShoulderInches: number | ""
  chewStrength: "light" | "average" | "strong" | ""
  activityLevel: "low" | "medium" | "high" | ""
  allergies: string
  // Step 3 fields
  about: string  // Pet characteristics for recommendations
  appearance: string  // Physical appearance for avatar generation
  budgetBand: "budget" | "moderate" | "premium" | ""
  brandPreferences: string
}

export default function Onboarding() {
  const [currentStep, setCurrentStep] = useState(1)
  const [maxStepReached, setMaxStepReached] = useState(1)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [animationSource, setAnimationSource] = useState<'next' | 'staging'>('next')
  const router = useRouter()
  const { setPet, setJourney, setLoading, setError } = useAppStore()

  const [form, setForm] = useState<OnboardingForm>({
    name: "",
    species: "",
    breed: "",
    ageMonths: "",
    // Step 1 fields
    gender: "",
    householdType: "",
    yardAccess: "",
    zipCode: "",
    // Step 2 fields
    weightLbs: "",
    heightAtShoulderInches: "",
    chewStrength: "",
    activityLevel: "",
    allergies: "",
    // Step 3 fields
    about: "",
    appearance: "",
    budgetBand: "",
    brandPreferences: ""
  })

  const totalSteps = 3

  const handleInputChange = (field: keyof OnboardingForm, value: string | number) => {
    setForm(prev => ({ ...prev, [field]: value }))
  }

  const isStep1Valid = form.name.trim() && form.species && form.breed.trim()
  const isStep2Valid = form.ageMonths !== ""
  const isStep3Valid = true // Optional fields

  const canProceed = () => {
    switch (currentStep) {
      case 1: return isStep1Valid
      case 2: return isStep2Valid
      case 3: return isStep3Valid
      default: return false
    }
  }

  const handleNext = () => {
    if (currentStep < totalSteps) {
      const nextStep = currentStep + 1
      setAnimationSource('next')
      setCurrentStep(nextStep)
      setMaxStepReached(Math.max(maxStepReached, nextStep))
    }
  }

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleCardClick = (step: number) => {
    // Allow navigation to any step up to the highest we've reached
    if (step <= maxStepReached) {
      setAnimationSource('staging')
      setCurrentStep(step)
    }
  }

  const handleSubmit = async () => {
    if (!canProceed()) return

    setIsSubmitting(true)
    setLoading(true)
    setError(null)

    try {
      // Create pet profile
      const petData = {
        name: form.name,
        species: form.species as "dog" | "cat",
        breed: form.breed,
        ageMonths: Number(form.ageMonths),
        // Step 1 fields
        gender: form.gender || undefined,
        householdType: form.householdType || undefined,
        yardAccess: form.yardAccess || undefined,
        zipCode: form.zipCode || undefined,
        // Step 2 fields
        weightLbs: form.weightLbs ? Number(form.weightLbs) : undefined,
        heightAtShoulderInches: form.heightAtShoulderInches ? Number(form.heightAtShoulderInches) : undefined,
        chewStrength: form.chewStrength || undefined,
        activityLevel: form.activityLevel || undefined,
        allergies: form.allergies || undefined,
        // Step 3 fields
        about: form.about || undefined,
        appearance: form.appearance || undefined,
        budgetBand: form.budgetBand || undefined,
        brandPreferences: form.brandPreferences || undefined
      }

      const pet = await api.createPet(petData)
      setPet(pet)

      // Initialize journey
      const journey = await api.initializeJourney(pet.id, 15)
      setJourney(journey)

      // Trigger image generation (prototype) - fire-and-forget
      try { localStorage.setItem('generatedPetImage', JSON.stringify({ loading: true })) } catch(e) {}
      fetch('http://localhost:8000/generate-image', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: petData.name, species: petData.species, breed: petData.breed, ageMonths: petData.ageMonths, appearance: petData.appearance })
      })
        .then(async (r) => {
          if (!r.ok) throw new Error('image endpoint ' + r.status)
          const j = await r.json()
          try { localStorage.setItem('generatedPetImage', JSON.stringify(j)) } catch(e) {}
        })
        .catch((e) => {
          console.warn('Image generation failed (non-blocking):', e)
          try { localStorage.removeItem('generatedPetImage') } catch(_) {}
        })

      // Redirect to journey overview immediately
      router.push('/journey')
    } catch (error) {
      console.error('Onboarding error:', error)
      setError(error instanceof Error ? error.message : 'Failed to create profile')
    } finally {
      setIsSubmitting(false)
      setLoading(false)
    }
  }


  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center p-4 overflow-x-auto">
      <div className="w-full max-w-6xl flex flex-col items-center">
        
        {/* Header */}
        <div className="text-center mb-4">
          <div className="flex justify-center items-center space-x-2 mb-4">
            <Heart className="h-6 w-6 text-purple-600" />
            <h1 className="text-2xl font-bold text-gray-900">Chewy Journey</h1>
          </div>
          <div className="flex justify-center space-x-2">
            {[1, 2, 3].map((step) => (
              <div
                key={step}
                className={`h-2 w-8 rounded-full transition-colors ${
                  step <= currentStep ? "bg-purple-600" : "bg-gray-200"
                }`}
              />
            ))}
          </div>
          <p className="text-sm text-gray-600 mt-2">Step {currentStep} of {totalSteps}</p>
        </div>

        {/* macOS Staging Window Layout */}
        <div className="relative w-full h-[800px] flex items-center justify-center">
          
          {/* Staging Area - Left Edge - Fixed to viewport */}
          <div className="fixed left-2 top-1/2 transform -translate-y-1/2 flex flex-col space-y-6 z-50">
            
            {/* Step 1 Card - Staging - Show if we've visited step 1 and it's not currently active */}
            {currentStep !== 1 && maxStepReached > 1 && (
              <motion.div
                initial={{ x: 0, scale: 1 }}
                animate={{
                  x: currentStep === 1 ? 200 : 0,
                  y: currentStep === 1 ? 0 : 0,
                  scale: currentStep === 1 ? 1.3 : 0.8,
                }}
                transition={{ duration: 0.6, ease: "easeInOut" }}
                onClick={() => handleCardClick(1)}
                className="cursor-pointer hover:scale-[0.85] transition-transform duration-200"
              >
                <Card className="shadow-2xl border-0 bg-white/95 backdrop-blur w-96 hover:shadow-xl transition-shadow">
                  <CardHeader>
                    <CardTitle className="text-xl">Let's meet your pet</CardTitle>
                    <CardDescription>Tell us about your furry friend</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div className="space-y-2">
                      <Label htmlFor="name">What's your pet's name?</Label>
                      <Input
                        id="name"
                        placeholder="e.g., Max, Luna, Buddy..."
                        value={form.name}
                        onChange={(e) => handleInputChange("name", e.target.value)}
                        className="text-lg"
                        disabled={true}
                      />
                    </div>

                    <div className="space-y-3">
                      <Label>What kind of pet do you have?</Label>
                      <div className="grid grid-cols-2 gap-3">
                        {SPECIES_OPTIONS.map((option) => (
                          <button
                            key={option.value}
                            type="button"
                            disabled={true}
                            className={`p-4 rounded-lg border-2 transition-all ${
                              form.species === option.value
                                ? "border-purple-500 bg-purple-50"
                                : "border-gray-200"
                            } opacity-50 cursor-not-allowed`}
                          >
                            <div className="text-3xl mb-2">{option.icon}</div>
                            <div className="font-medium">{option.label}</div>
                          </button>
                        ))}
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="breed">What breed?</Label>
                      <Input
                        id="breed"
                        placeholder="e.g., Golden Retriever, Persian, Mixed..."
                        value={form.breed}
                        onChange={(e) => handleInputChange("breed", e.target.value)}
                        disabled={true}
                      />
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )}

            {/* Step 2 Card - Staging - Show if we've visited step 2 and it's not currently active */}
            {currentStep !== 2 && maxStepReached > 2 && (
              <motion.div
                initial={{ x: 0, scale: 1 }}
                animate={{
                  x: currentStep === 2 ? 200 : 0,
                  y: currentStep === 2 ? 0 : 0,
                  scale: currentStep === 2 ? 1.3 : 0.8,
                }}
                transition={{ duration: 0.6, ease: "easeInOut" }}
                onClick={() => handleCardClick(2)}
                className="cursor-pointer hover:scale-[0.85] transition-transform duration-200"
              >
                <Card className="shadow-2xl border-0 bg-white/95 backdrop-blur w-96 hover:shadow-xl transition-shadow">
                  <CardHeader>
                    <CardTitle className="text-xl">A few more details</CardTitle>
                    <CardDescription>This helps us personalize their journey</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div className="space-y-2">
                      <Label htmlFor="age">How old is {form.name}? (in months)</Label>
                      <Input
                        id="age"
                        type="number"
                        placeholder="e.g., 18"
                        value={form.ageMonths}
                        onChange={(e) => handleInputChange("ageMonths", e.target.value ? Number(e.target.value) : "")}
                        min="1"
                        max="300"
                        disabled={true}
                      />
                      <p className="text-sm text-gray-500">
                        Tip: 12 months = 1 year, 24 months = 2 years, etc.
                      </p>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="allergies">Any known allergies or dietary restrictions?</Label>
                      <Input
                        id="allergies"
                        placeholder="e.g., Chicken, grain-free, none..."
                        value={form.allergies}
                        onChange={(e) => handleInputChange("allergies", e.target.value)}
                        disabled={true}
                      />
                      <p className="text-sm text-gray-500">Optional - helps us personalize recommendations</p>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )}

            {/* Step 3 Card - Staging - Show if we've visited step 3 and it's not currently active */}
            {currentStep !== 3 && maxStepReached >= 3 && (
              <motion.div
                initial={{ x: 0, scale: 1 }}
                animate={{
                  x: currentStep === 3 ? 200 : 0,
                  y: currentStep === 3 ? 0 : 0,
                  scale: currentStep === 3 ? 1.3 : 0.8,
                }}
                transition={{ duration: 0.6, ease: "easeInOut" }}
                onClick={() => handleCardClick(3)}
                className="cursor-pointer hover:scale-[0.85] transition-transform duration-200"
              >
                <Card className="shadow-2xl border-0 bg-white/95 backdrop-blur w-96 hover:shadow-xl transition-shadow">
                  <CardHeader>
                    <CardTitle className="text-xl">Final touches</CardTitle>
                    <CardDescription>We're almost ready to begin!</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div className="space-y-2">
                      <Label htmlFor="about">Tell us about {form.name}</Label>
                      <textarea
                        id="about"
                        placeholder="e.g., Very energetic, loves to play fetch, sleeps a lot, gets anxious during storms..."
                        value={form.about}
                        onChange={(e) => handleInputChange("about", e.target.value)}
                        rows={4}
                        className="w-full px-3 py-2 border border-input rounded-md bg-background text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                        disabled={true}
                      />
                      <p className="text-sm text-gray-500">Optional - helps our AI provide better recommendations</p>
                    </div>

                    <div className="bg-blue-50 p-4 rounded-lg">
                      <h4 className="font-semibold text-blue-900 mb-2">Ready to start your journey!</h4>
                      <p className="text-blue-800 text-sm">
                        We'll create a personalized 15-month journey for {form.name} with curated 
                        recommendations for each stage of their growth and development.
                      </p>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )}
          </div>

          {/* Main Card - Center */}
          <motion.div
            key={currentStep}
            initial={
              animationSource === 'staging' 
                ? {
                    x: -700, // Start from left edge staging area
                    y: (currentStep - 1) * 250 - 250, // Vertical offset based on card position
                    scale: 0.8,
                    opacity: 1
                  }
                : { x: 400, opacity: 0, scale: 0.8 }
            }
            animate={{ x: 0, y: 0, opacity: 1, scale: 1 }}
            exit={{ x: 400, opacity: 0, scale: 0.8 }}
            transition={{ duration: 0.7, ease: "easeOut", type: "spring", stiffness: 100, damping: 20 }}
            className="absolute left-1/2 top-1/2 transform -translate-x-1/2 -translate-y-1/2 z-20"
          >
            
            {currentStep === 1 && (
              <Card className="shadow-2xl border-0 bg-white/95 backdrop-blur w-[550px] max-h-[70vh] overflow-y-auto">
                <CardHeader>
                  <CardTitle className="text-xl">Let's meet your pet</CardTitle>
                  <CardDescription>Tell us about your furry friend</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="space-y-2">
                    <Label htmlFor="name">What's your pet's name?</Label>
                    <Input
                      id="name"
                      placeholder="e.g., Max, Luna, Buddy..."
                      value={form.name}
                      onChange={(e) => handleInputChange("name", e.target.value)}
                      className="text-lg"
                    />
                  </div>

                  <div className="space-y-3">
                    <Label>What kind of pet do you have?</Label>
                    <div className="grid grid-cols-2 gap-3">
                      {SPECIES_OPTIONS.map((option) => (
                        <button
                          key={option.value}
                          type="button"
                          onClick={() => handleInputChange("species", option.value)}
                          className={`p-4 rounded-lg border-2 transition-all ${
                            form.species === option.value
                              ? "border-purple-500 bg-purple-50"
                              : "border-gray-200 hover:border-gray-300"
                          }`}
                        >
                          <div className="text-3xl mb-2">{option.icon}</div>
                          <div className="font-medium">{option.label}</div>
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="breed">What breed?</Label>
                    <Input
                      id="breed"
                      placeholder="e.g., Golden Retriever, Persian, Mixed..."
                      value={form.breed}
                      onChange={(e) => handleInputChange("breed", e.target.value)}
                    />
                  </div>

                  <div className="space-y-3">
                    <Label>Gender</Label>
                    <div className="grid grid-cols-3 gap-3">
                      {GENDER_OPTIONS.map((option) => (
                        <button
                          key={option.value}
                          type="button"
                          onClick={() => handleInputChange("gender", option.value)}
                          className={`p-3 rounded-lg border-2 transition-all ${
                            form.gender === option.value
                              ? "border-purple-500 bg-purple-50"
                              : "border-gray-200 hover:border-gray-300"
                          }`}
                        >
                          <div className="font-medium text-sm">{option.label}</div>
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-3">
                    <Label>Housing type</Label>
                    <div className="grid grid-cols-2 gap-3">
                      {HOUSEHOLD_OPTIONS.map((option) => (
                        <button
                          key={option.value}
                          type="button"
                          onClick={() => handleInputChange("householdType", option.value)}
                          className={`p-4 rounded-lg border-2 transition-all ${
                            form.householdType === option.value
                              ? "border-purple-500 bg-purple-50"
                              : "border-gray-200 hover:border-gray-300"
                          }`}
                        >
                          <div className="text-2xl mb-2">{option.icon}</div>
                          <div className="font-medium">{option.label}</div>
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-3">
                    <Label>Yard access</Label>
                    <div className="grid grid-cols-3 gap-3">
                      {YARD_OPTIONS.map((option) => (
                        <button
                          key={option.value}
                          type="button"
                          onClick={() => handleInputChange("yardAccess", option.value)}
                          className={`p-3 rounded-lg border-2 transition-all ${
                            form.yardAccess === option.value
                              ? "border-purple-500 bg-purple-50"
                              : "border-gray-200 hover:border-gray-300"
                          }`}
                        >
                          <div className="font-medium text-sm">{option.label}</div>
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="zipCode">Zip code (optional)</Label>
                    <Input
                      id="zipCode"
                      placeholder="e.g., 90210"
                      value={form.zipCode}
                      onChange={(e) => handleInputChange("zipCode", e.target.value)}
                      maxLength={5}
                    />
                    <p className="text-sm text-gray-500">Helps us find local stores and services</p>
                  </div>
                </CardContent>
              </Card>
            )}

            {currentStep === 2 && (
              <Card className="shadow-2xl border-0 bg-white/95 backdrop-blur w-[550px] max-h-[70vh] overflow-y-auto">
                <CardHeader>
                  <CardTitle className="text-xl">A few more details</CardTitle>
                  <CardDescription>This helps us personalize their journey</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="space-y-2">
                    <Label htmlFor="age">How old is {form.name}? (in months)</Label>
                    <Input
                      id="age"
                      type="number"
                      placeholder="e.g., 18"
                      value={form.ageMonths}
                      onChange={(e) => handleInputChange("ageMonths", e.target.value ? Number(e.target.value) : "")}
                      min="1"
                      max="300"
                    />
                    <p className="text-sm text-gray-500">
                      Tip: 12 months = 1 year, 24 months = 2 years, etc.
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="weight">Weight (lbs)</Label>
                      <Input
                        id="weight"
                        type="number"
                        placeholder="e.g., 25"
                        value={form.weightLbs}
                        onChange={(e) => handleInputChange("weightLbs", e.target.value ? Number(e.target.value) : "")}
                        min="0.5"
                        max="200"
                        step="0.5"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="height">Height at shoulder (inches)</Label>
                      <Input
                        id="height"
                        type="number"
                        placeholder="e.g., 24"
                        value={form.heightAtShoulderInches}
                        onChange={(e) => handleInputChange("heightAtShoulderInches", e.target.value ? Number(e.target.value) : "")}
                        min="1"
                        max="40"
                        step="0.5"
                      />
                      <p className="text-sm text-gray-500">Optional - for dogs only</p>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <Label>Chew strength</Label>
                    <div className="grid grid-cols-3 gap-3">
                      {CHEW_STRENGTH_OPTIONS.map((option) => (
                        <button
                          key={option.value}
                          type="button"
                          onClick={() => handleInputChange("chewStrength", option.value)}
                          className={`p-3 rounded-lg border-2 transition-all ${
                            form.chewStrength === option.value
                              ? "border-purple-500 bg-purple-50"
                              : "border-gray-200 hover:border-gray-300"
                          }`}
                        >
                          <div className="font-medium text-sm">{option.label}</div>
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-3">
                    <Label>Activity level</Label>
                    <div className="grid grid-cols-3 gap-3">
                      {ACTIVITY_LEVEL_OPTIONS.map((option) => (
                        <button
                          key={option.value}
                          type="button"
                          onClick={() => handleInputChange("activityLevel", option.value)}
                          className={`p-3 rounded-lg border-2 transition-all ${
                            form.activityLevel === option.value
                              ? "border-purple-500 bg-purple-50"
                              : "border-gray-200 hover:border-gray-300"
                          }`}
                        >
                          <div className="font-medium text-sm">{option.label}</div>
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="allergies">Any known allergies or dietary restrictions?</Label>
                    <Input
                      id="allergies"
                      placeholder="e.g., Chicken, grain-free, none..."
                      value={form.allergies}
                      onChange={(e) => handleInputChange("allergies", e.target.value)}
                    />
                    <p className="text-sm text-gray-500">Optional - helps us personalize recommendations</p>
                  </div>
                </CardContent>
              </Card>
            )}

            {currentStep === 3 && (
              <Card className="shadow-2xl border-0 bg-white/95 backdrop-blur w-[550px] max-h-[70vh] overflow-y-auto">
                <CardHeader>
                  <CardTitle className="text-xl">Final touches</CardTitle>
                  <CardDescription>We're almost ready to begin!</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="space-y-2">
                    <Label htmlFor="about">Tell us about {form.name}</Label>
                    <textarea
                      id="about"
                      placeholder="e.g., Very energetic, loves to play fetch, sleeps a lot, gets anxious during storms..."
                      value={form.about}
                      onChange={(e) => handleInputChange("about", e.target.value)}
                      rows={3}
                      className="w-full px-3 py-2 border border-input rounded-md bg-background text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    />
                    <p className="text-sm text-gray-500">Optional - helps our AI provide better recommendations</p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="appearance">Describe {form.name}'s appearance</Label>
                    <textarea
                      id="appearance"
                      placeholder="e.g., Golden fur with white patches, short-haired, brown eyes, floppy ears..."
                      value={form.appearance}
                      onChange={(e) => handleInputChange("appearance", e.target.value)}
                      rows={3}
                      className="w-full px-3 py-2 border border-input rounded-md bg-background text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                    />
                    <p className="text-sm text-gray-500">Optional - helps create your pet's avatar</p>
                  </div>

                  <div className="space-y-4">
                    <h3 className="font-semibold text-gray-900">Parent preferences</h3>
                    
                    <div className="space-y-3">
                      <Label>Budget range per month</Label>
                      <div className="grid grid-cols-1 gap-3">
                        {BUDGET_OPTIONS.map((option) => (
                          <button
                            key={option.value}
                            type="button"
                            onClick={() => handleInputChange("budgetBand", option.value)}
                            className={`p-3 rounded-lg border-2 transition-all text-left ${
                              form.budgetBand === option.value
                                ? "border-purple-500 bg-purple-50"
                                : "border-gray-200 hover:border-gray-300"
                            }`}
                          >
                            <div className="font-medium text-sm">{option.label}</div>
                          </button>
                        ))}
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="brandPreferences">Brand preferences</Label>
                      <textarea
                        id="brandPreferences"
                        placeholder="e.g., Prefer Blue Buffalo, avoid grain products, like premium brands..."
                        value={form.brandPreferences}
                        onChange={(e) => handleInputChange("brandPreferences", e.target.value)}
                        rows={2}
                        className="w-full px-3 py-2 border border-input rounded-md bg-background text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                      />
                      <p className="text-sm text-gray-500">Optional - brands you like or want to avoid</p>
                    </div>
                  </div>

                  <div className="bg-blue-50 p-4 rounded-lg">
                    <h4 className="font-semibold text-blue-900 mb-2">Ready to start your journey!</h4>
                    <p className="text-blue-800 text-sm">
                      We'll create a personalized 15-month journey for {form.name} with curated 
                      recommendations for each stage of their growth and development.
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}
          </motion.div>
        </div>

        {/* Navigation */}
        <div className="flex justify-between w-full max-w-lg mt-12 mb-8">
          <Button
            variant="outline"
            onClick={handleBack}
            disabled={currentStep === 1}
            className="flex items-center space-x-2"
          >
            <ChevronLeft className="h-4 w-4" />
            <span>Back</span>
          </Button>

          {currentStep < totalSteps ? (
            <Button
              onClick={handleNext}
              disabled={!canProceed()}
              className="flex items-center space-x-2"
            >
              <span>Next</span>
              <ChevronRight className="h-4 w-4" />
            </Button>
          ) : (
            <Button
              onClick={handleSubmit}
              disabled={!canProceed() || isSubmitting}
              className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
            >
              {isSubmitting ? "Creating Journey..." : "Start Journey"}
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
