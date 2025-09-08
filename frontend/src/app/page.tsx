"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Heart, Sparkles } from "lucide-react"
import { useRouter } from "next/navigation"

export default function Welcome() {
  const router = useRouter()

  const handleCreateProfile = () => {
    router.push('/onboarding')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl space-y-8">
        
        {/* Logo/Brand */}
        <div className="text-center space-y-4">
          <div className="flex justify-center items-center space-x-2">
            <Heart className="h-8 w-8 text-purple-600" />
            <h1 className="text-4xl font-bold text-gray-900">Chewy Journey</h1>
            <Sparkles className="h-8 w-8 text-blue-600" />
          </div>
          <p className="text-xl text-gray-600">
            A personalized monthly adventure for your furry family member
          </p>
        </div>

        {/* Main card */}
        <Card className="w-full shadow-xl border-0 bg-white/80 backdrop-blur">
          <CardHeader className="text-center space-y-4">
            <CardTitle className="text-2xl text-gray-900">
              Welcome to Your Pet's Journey
            </CardTitle>
            <CardDescription className="text-lg">
              Discover personalized products, nutrition, and care recommendations 
              tailored specifically for your pet's life stage, breed, and unique needs.
            </CardDescription>
          </CardHeader>
          
          <CardContent className="space-y-6">
            {/* Features */}
            <div className="grid md:grid-cols-3 gap-4 text-center">
              <div className="space-y-2">
                <div className="h-12 w-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto">
                  <Heart className="h-6 w-6 text-purple-600" />
                </div>
                <h3 className="font-semibold">Personalized</h3>
                <p className="text-sm text-gray-600">Recommendations based on your pet's unique profile</p>
              </div>
              <div className="space-y-2">
                <div className="h-12 w-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto">
                  <Sparkles className="h-6 w-6 text-blue-600" />
                </div>
                <h3 className="font-semibold">Monthly Journey</h3>
                <p className="text-sm text-gray-600">15 curated months of growth and care</p>
              </div>
              <div className="space-y-2">
                <div className="h-12 w-12 bg-green-100 rounded-full flex items-center justify-center mx-auto">
                  <div className="h-6 w-6 bg-green-600 rounded-full"></div>
                </div>
                <h3 className="font-semibold">AI-Powered</h3>
                <p className="text-sm text-gray-600">Smart recommendations that adapt to your pet</p>
              </div>
            </div>

            {/* CTA */}
            <div className="text-center pt-4">
              <Button 
                onClick={handleCreateProfile}
                size="lg"
                className="text-lg px-8 py-6 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
              >
                Create Your Pet's Profile
              </Button>
              <p className="text-sm text-gray-500 mt-3">
                Takes just 2 minutes to get started
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}