"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Sparkles, Send, Loader2 } from "lucide-react"
import { api } from "@/lib/api"

interface AIRecommendationBoxProps {
  journeyId: string
  monthIdx: number
  petName: string
  onRecommendation: (summary: string, items: any[]) => void
}

const QUICK_PROMPTS = [
  "teething this week",
  "super energetic lately", 
  "seems anxious during storms",
  "scratching more than usual",
  "loves to chew everything",
  "very playful and active"
]

export function AIRecommendationBox({ 
  journeyId, 
  monthIdx, 
  petName, 
  onRecommendation 
}: AIRecommendationBoxProps) {
  const [note, setNote] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [lastResponse, setLastResponse] = useState<string | null>(null)

  const handleSubmit = async () => {
    if (!note.trim() || isLoading) return

    setIsLoading(true)
    try {
      const response = await api.getAIRecommendations(journeyId, monthIdx, note)
      
      // Update local state with AI response
      onRecommendation(response.summary, response.items)
      setLastResponse(response.summary)
      
      // Clear the input
      setNote("")
      
      // Track AI usage
      await api.trackEvent("ai_recommendation_used", journeyId, {
        monthIdx,
        note: note.trim(),
        itemCount: response.items.length
      })
      
    } catch (error) {
      console.error('Failed to get AI recommendations:', error)
      setLastResponse("Sorry, I couldn't process that request right now. Please try again.")
    } finally {
      setIsLoading(false)
    }
  }

  const handleQuickPrompt = (prompt: string) => {
    setNote(prompt)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="relative w-full">
      <Card className="w-full shadow-lg bg-gradient-to-br from-purple-50 to-blue-50 border-0">
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center space-x-2 text-lg">
          <Sparkles className="h-5 w-5 text-purple-600" />
          <span>AI Recommendations</span>
        </CardTitle>
        <p className="text-sm text-gray-600">
          Tell me about {petName}'s current needs and I'll suggest additional items
        </p>
      </CardHeader>

      <CardContent className="space-y-4">
        
        {/* Text Input */}
        <div className="space-y-2">
          <div className="flex space-x-2 items-stretch">
            {/* Flowing border around the input only - masked stroke to avoid white cutoff */}
            <div className="relative flex-1">
              <div
                className="absolute inset-0 rounded-lg p-[2px] pointer-events-none"
                style={{
                  background:
                    'linear-gradient(90deg, #9333ea, #ec4899, #3b82f6, #10b981, #f59e0b, #ef4444, #8b5cf6, #9333ea)',
                  backgroundSize: '200% 200%',
                  animation: 'aiGradient 8s linear infinite',
                  WebkitMask: 'linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0)',
                  WebkitMaskComposite: 'xor',
                  maskComposite: 'exclude'
                }}
              />
              <Input
                placeholder={`e.g., "${petName} has been teething a lot lately..."`}
                value={note}
                onChange={(e) => setNote(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={isLoading}
                className="w-full rounded-lg bg-white"
              />
            </div>
            <Button
              onClick={handleSubmit}
              disabled={!note.trim() || isLoading}
              size="sm"
              className="bg-purple-600 hover:bg-purple-700"
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>

        {/* Quick Prompts */}
        <div className="space-y-2">
          <p className="text-sm font-medium text-gray-700">Quick prompts:</p>
          <div className="flex flex-wrap gap-2">
            {QUICK_PROMPTS.map((prompt, index) => (
              <button
                key={index}
                onClick={() => handleQuickPrompt(prompt)}
                disabled={isLoading}
                className="px-3 py-1.5 text-xs bg-white border border-purple-200 rounded-full hover:bg-purple-50 hover:border-purple-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>

        {/* AI Response */}
        {lastResponse && (
          <div className="bg-white/80 backdrop-blur p-4 rounded-lg border border-purple-200">
            <div className="flex items-start space-x-2">
              <Sparkles className="h-4 w-4 text-purple-600 mt-0.5 flex-shrink-0" />
              <div>
                <p className="font-medium text-purple-900 text-sm mb-1">AI Response:</p>
                <p className="text-sm text-gray-700">{lastResponse}</p>
              </div>
            </div>
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="bg-white/80 backdrop-blur p-4 rounded-lg border border-purple-200">
            <div className="flex items-center space-x-2">
              <Loader2 className="h-4 w-4 animate-spin text-purple-600" />
              <p className="text-sm text-gray-600">Analyzing {petName}'s needs...</p>
            </div>
          </div>
        )}

        {/* Help Text */}
        <div className="text-xs text-gray-500 space-y-1">
          <p>💡 <strong>Tip:</strong> Be specific about behaviors, symptoms, or situations</p>
          <p>🎯 <strong>Examples:</strong> "scratching more", "very energetic", "afraid of loud noises"</p>
        </div>
      </CardContent>
    </Card>
    <style jsx>{`
      @keyframes aiGradient {
        0% { background-position: 0% 50%; }
        100% { background-position: 200% 50%; }
      }
    `}</style>
    </div>
  )
}
