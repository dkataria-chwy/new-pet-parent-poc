"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Sparkles, Send, Loader2, ExternalLink } from "lucide-react"
import { api } from "@/lib/api"

interface AIRecommendationBoxProps {
  journeyId: string
  monthIdx: number
  petName: string
  onRecommendation: (summary: string, items: any[]) => void
}

interface RecommendedProduct {
  rank: number
  sku: string
  parentSKU: string
  name: string
  similarity: number
  product_link: string
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
  const [recommendedProducts, setRecommendedProducts] = useState<RecommendedProduct[]>([])

  const handleSubmit = async () => {
    if (!note.trim() || isLoading) return

    setIsLoading(true)
    try {
      // Use new on-demand recommendations system
      const response = await api.getOnDemandRecommendations(journeyId, monthIdx, note.trim(), 20)
      
      console.log('🔍 API Response:', response) // Debug log
      
      // Check if response has the expected structure
      if (!response.products || !Array.isArray(response.products)) {
        console.error('❌ Invalid response structure:', response)
        throw new Error('Invalid response format: missing products array')
      }
      
      // Store products and rationale in local state (display in this card)
      setRecommendedProducts(response.products.slice(0, 10)) // Show top 10 products
      setLastResponse(response.rationale)
      
      // Log the search query to console for debugging (not shown in UI)
      console.log('🔍 Search Query Used:', response.query_used)
      
      // ✅ NO LONGER adding to main product sections - AI recs are self-contained in this card
      // Just notify parent that recommendations were generated (for analytics/tracking)
      onRecommendation(response.rationale, [])
      
      // Clear the input
      setNote("")
      
      // Track AI usage with new system
      await api.trackEvent("on_demand_recommendation_used", journeyId, {
        user_query: note.trim(),
        total_products: response.total_products,
        pet_name: response.pet_name,
        enhanced_query: response.query_used
      })
      
    } catch (error) {
      console.error('Failed to get on-demand recommendations:', error)
      setLastResponse("Sorry, I couldn't process that request right now. Please try again.")
    } finally {
      setIsLoading(false)
    }
  }

  const handleQuickPrompt = (prompt: string) => {
    setNote(prompt)
  }


  const handleClearResults = () => {
    setLastResponse(null)
    setRecommendedProducts([])
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

        {/* Quick Prompts - Only show if not loading and no response yet */}
        {!isLoading && !lastResponse && (
          <div className="space-y-2">
            <p className="text-sm font-medium text-gray-700">Quick prompts:</p>
            <div className="flex flex-wrap gap-2">
              {QUICK_PROMPTS.map((prompt, index) => (
                <button
                  key={index}
                  onClick={() => handleQuickPrompt(prompt)}
                  className="px-3 py-1.5 text-xs bg-white border border-purple-200 rounded-full hover:bg-purple-50 hover:border-purple-300 transition-colors"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* AI Response */}
        {lastResponse && (
          <div className="space-y-4">
            {/* AI Analysis */}
            <div className="bg-white/80 backdrop-blur p-4 rounded-lg border border-purple-200">
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-2 flex-1">
                  <Sparkles className="h-4 w-4 text-purple-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="font-medium text-purple-900 text-sm mb-1">AI Analysis:</p>
                    <p className="text-sm text-gray-700">{lastResponse}</p>
                  </div>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleClearResults}
                  className="text-xs text-gray-600 border-gray-300 hover:bg-gray-100 ml-2"
                >
                  New Search
                </Button>
              </div>
            </div>


            {/* Recommended Products */}
            {recommendedProducts.length > 0 && (
              <div className="bg-green-50/80 backdrop-blur p-4 rounded-lg border border-green-200">
                <div className="flex items-center gap-2 mb-3">
                  <Sparkles className="h-4 w-4 text-green-600" />
                  <p className="font-medium text-green-800">Recommended Products ({recommendedProducts.length})</p>
                </div>
                
                <div className="space-y-3">
                  {recommendedProducts.map((product, index) => (
                    <div key={`rec-${product.sku}-${product.rank}-${index}`} className="p-3 bg-white/90 rounded-lg border border-green-200">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs font-medium text-green-700 bg-green-100 px-2 py-1 rounded">
                          #{product.rank}
                        </span>
                        <span className="text-xs text-gray-500">SKU: {product.sku}</span>
                        {product.parentSKU && (
                          <span className="text-xs text-gray-400">Parent: {product.parentSKU}</span>
                        )}
                      </div>
                      <div className="flex items-start justify-between gap-2">
                        <h4 className="font-medium text-gray-900 text-sm mb-1 flex-1">{product.name}</h4>
                        {product.product_link && (
                          <a
                            href={product.product_link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 hover:underline flex-shrink-0"
                          >
                            View Product
                            <ExternalLink className="h-3 w-3" />
                          </a>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="bg-white/80 backdrop-blur p-4 rounded-lg border border-purple-200">
            <div className="flex items-center space-x-2">
              <Loader2 className="h-4 w-4 animate-spin text-purple-600" />
              <p className="text-sm text-gray-600">Generating list for {petName}...</p>
            </div>
          </div>
        )}

        {/* Help Text - Only show if not loading and no response yet */}
        {!isLoading && !lastResponse && (
          <div className="text-xs text-gray-500 space-y-1">
            <p>💡 <strong>Tip:</strong> Be specific about behaviors, symptoms, or situations</p>
            <p>🎯 <strong>Examples:</strong> "scratching more", "very energetic", "afraid of loud noises"</p>
          </div>
        )}
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
