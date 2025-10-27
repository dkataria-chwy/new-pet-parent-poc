"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Check, X, Sparkles, ChevronDown, ChevronUp } from "lucide-react"
import { RecommendationItem } from "@/lib/store"
import { cn } from "@/lib/utils"

interface SubscriptionProduct {
  slot_id: number
  sku: string
  product_name: string
  product_link: string
  product_price_current: number
  autoship_eligible: boolean
  top_family: string
  bucket: string
  subscription_rationale: string
  estimated_frequency: string
  personalized_note: string
}

interface OneTimeProduct {
  slot_id: number
  sku: string
  product_name: string
  product_link: string
  product_price_current: number
  autoship_eligible: boolean
  top_family: string
  bucket: string
  one_time_rationale: string
  personalized_note: string
}

interface ProductSectionProps {
  title: string
  subtitle: string
  items: RecommendationItem[]
  monthIndex: number
  section: string
  getItemDecision: (monthIdx: number, section: string, itemId: string) => boolean | undefined
  getSectionDecision: (monthIdx: number, section: string) => boolean | undefined
  onItemDecision: (itemId: string, decision: boolean) => void
  onSectionDecision: (decision: boolean) => void
  isReadOnly?: boolean
  subscriptionPlanData?: SubscriptionProduct[]
  oneTimePlanData?: OneTimeProduct[]
  isLoadingPlan?: boolean
  overallStrategy?: string
  petName?: string
}


// Collapsible component for Overall Strategy Summary
function OverallStrategyCollapsible({ strategy }: { strategy: string }) {
  const [isExpanded, setIsExpanded] = useState(false)
  
  return (
    <div className="mt-4 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg border border-purple-200 overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-4 flex items-center justify-between text-left hover:bg-purple-100/50 transition-colors"
      >
        <div className="flex items-start gap-2 flex-1">
          <Sparkles className="h-5 w-5 text-purple-600 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-sm font-semibold text-purple-900">AI Strategy Summary</p>
            {!isExpanded && (
              <p className="text-xs text-purple-700 mt-0.5">Click to view personalized plan</p>
            )}
          </div>
        </div>
        {isExpanded ? (
          <ChevronUp className="h-5 w-5 text-purple-600 flex-shrink-0" />
        ) : (
          <ChevronDown className="h-5 w-5 text-purple-600 flex-shrink-0" />
        )}
      </button>
      
      {isExpanded && (
        <div className="px-4 pb-4">
          <p className="text-sm text-gray-700 leading-relaxed">
            {strategy}
          </p>
        </div>
      )}
    </div>
  )
}

export function ProductSection({ 
  title, 
  subtitle, 
  items, 
  monthIndex, 
  section, 
  getItemDecision, 
  getSectionDecision, 
  onItemDecision, 
  onSectionDecision,
  isReadOnly = false,
  subscriptionPlanData,
  oneTimePlanData,
  isLoadingPlan = false,
  overallStrategy,
  petName
}: ProductSectionProps) {
  // If subscription plan data is provided, use it instead of legacy items
  const useSubscriptionPlan = subscriptionPlanData && subscriptionPlanData.length > 0
  const useOneTimePlan = oneTimePlanData && oneTimePlanData.length > 0
  
  if (!items.length && !useSubscriptionPlan && !useOneTimePlan) return null

  const sectionDecision = getSectionDecision(monthIndex, section)

  const ProductCard = ({ item }: { item: RecommendationItem }) => {
    const itemDecision = getItemDecision(monthIndex, section, item.id)
    
    return (
    <Card className="h-full bg-white/80 backdrop-blur border border-gray-200 hover:shadow-md transition-shadow">
      <CardContent className="p-4 space-y-3">
        
        {/* Header */}
        <div className="space-y-2">
          <div className="flex items-start justify-between">
            <h4 className="font-semibold text-gray-900 leading-tight">{item.title}</h4>
            {item.isAIGenerated && (
              <Badge className="flex items-center space-x-1 ml-2 bg-purple-100 text-purple-800">
                <Sparkles className="h-3 w-3" />
                <span>AI</span>
              </Badge>
            )}
          </div>
          
          {item.subtitle && (
            <p className="text-sm text-gray-600">{item.subtitle}</p>
          )}
        </div>

        {/* Tags */}
        {item.tags.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {item.tags.map((tag, index) => (
              <Badge key={index} variant="secondary">
                {tag}
              </Badge>
            ))}
          </div>
        )}

        {/* Price & Cadence */}
        <div className="flex items-center justify-between">
          <span className="font-semibold text-lg text-gray-900">{item.price}</span>
          {item.cadence && (
            <span className="text-sm text-gray-500">{item.cadence}</span>
          )}
        </div>

        {/* Why for Pet */}
        <div className="bg-blue-50 p-3 rounded-lg">
          <p className="text-sm text-blue-900 font-medium mb-1 flex items-center gap-1">
            <Sparkles className="h-3 w-3 text-purple-600" />
            Why for your pet:
            <span className="text-xs text-purple-600 font-normal">(AI Generated)</span>
          </p>
          <p className="text-sm text-blue-800">{item.whyForPet}</p>
        </div>

        {/* Individual Item Decision Buttons */}
        <div className="flex gap-2 pt-2">
          <Button
            type="button"
            variant={itemDecision === true ? "default" : "outline"}
            size="sm"
            disabled={isReadOnly}
            onClick={(e) => {
              e.preventDefault()
              e.stopPropagation()
              if (!isReadOnly) onItemDecision(item.id, true)
            }}
            className={cn(
              "flex-1 flex items-center justify-center space-x-1",
              itemDecision === true && "bg-green-600 hover:bg-green-700 text-white",
              isReadOnly && "opacity-50 cursor-not-allowed"
            )}
          >
            <Check className="h-3 w-3" />
            <span>Accept</span>
          </Button>
          
          <Button
            type="button"
            variant={itemDecision === false ? "default" : "outline"}
            size="sm"
            disabled={isReadOnly}
            onClick={(e) => {
              e.preventDefault()
              e.stopPropagation()
              if (!isReadOnly) onItemDecision(item.id, false)
            }}
            className={cn(
              "flex-1 flex items-center justify-center space-x-1",
              itemDecision === false && "bg-red-600 hover:bg-red-700 text-white",
              isReadOnly && "opacity-50 cursor-not-allowed"
            )}
          >
            <X className="h-3 w-3" />
            <span>Skip</span>
          </Button>
        </div>

        {/* Individual Decision Status */}
        {typeof itemDecision === 'boolean' && (
          <div className={cn(
            "text-xs p-2 rounded-lg font-medium text-center",
            itemDecision 
              ? "bg-green-50 text-green-800 border border-green-200" 
              : "bg-red-50 text-red-800 border border-red-200"
          )}>
            {itemDecision ? "✓ Accepted" : "⊘ Skipped"}
          </div>
        )}
      </CardContent>
    </Card>
    )
  }

  const SubscriptionProductCard = ({ product, index }: { product: SubscriptionProduct, index: number }) => {
    const [showRationale, setShowRationale] = useState(false)
    const [showNote, setShowNote] = useState(false)
    const itemDecision = getItemDecision(monthIndex, section, product.sku)
    
    // Create personalized labels
    const whyLabel = petName ? `Why this for ${petName}?` : "Why for your pet"
    const rationaleLabel = "Why subscribe?"
    
    return (
      <Card className="h-full bg-white/80 backdrop-blur border border-gray-200 hover:shadow-md transition-shadow">
        <CardContent className="p-4 space-y-3">
          
          {/* Header with hyperlinked product name */}
          <div className="space-y-2">
            {product.product_link ? (
              <a 
                href={product.product_link} 
                target="_blank" 
                rel="noopener noreferrer"
                className="font-semibold text-gray-900 leading-tight hover:text-blue-600 hover:underline transition-colors"
              >
                {product.product_name}
              </a>
            ) : (
              <h4 className="font-semibold text-gray-900 leading-tight">{product.product_name}</h4>
            )}
          </div>

          {/* Price & Frequency Badge */}
          <div className="flex items-center justify-between">
            <span className="font-semibold text-lg text-gray-900">
              ${product.product_price_current?.toFixed(2) || 'N/A'}
            </span>
            <Badge variant="secondary" className="bg-blue-100 text-blue-800">
              {product.estimated_frequency}
            </Badge>
          </div>

          {/* Why for your pet - Collapsible */}
          <div className="bg-blue-50 rounded-lg overflow-hidden">
            <button
              onClick={() => setShowNote(!showNote)}
              className="w-full p-3 flex items-center justify-between text-left hover:bg-blue-100 transition-colors"
            >
              <p className="text-sm text-blue-900 font-medium flex items-center gap-1">
                <Sparkles className="h-3 w-3 text-purple-600" />
                {whyLabel}
              </p>
              {showNote ? <ChevronUp className="h-4 w-4 text-blue-600" /> : <ChevronDown className="h-4 w-4 text-blue-600" />}
            </button>
            {showNote && (
              <div className="px-3 pb-3">
                <p className="text-sm text-blue-800">{product.personalized_note}</p>
              </div>
            )}
          </div>

          {/* Rationale - Collapsible */}
          <div className="bg-gray-50 rounded-lg overflow-hidden">
            <button
              onClick={() => setShowRationale(!showRationale)}
              className="w-full p-3 flex items-center justify-between text-left hover:bg-gray-100 transition-colors"
            >
              <p className="text-sm text-gray-700 font-medium">{rationaleLabel}</p>
              {showRationale ? <ChevronUp className="h-4 w-4 text-gray-600" /> : <ChevronDown className="h-4 w-4 text-gray-600" />}
            </button>
            {showRationale && (
              <div className="px-3 pb-3">
                <p className="text-sm text-gray-700">{product.subscription_rationale}</p>
              </div>
            )}
          </div>

          {/* Individual Item Decision Buttons */}
          <div className="flex gap-2 pt-2">
            <Button
              type="button"
              variant={itemDecision === true ? "default" : "outline"}
              size="sm"
              disabled={isReadOnly}
              onClick={(e) => {
                e.preventDefault()
                e.stopPropagation()
                if (!isReadOnly) onItemDecision(product.sku, true)
              }}
              className={cn(
                "flex-1 flex items-center justify-center space-x-1",
                itemDecision === true && "bg-green-600 hover:bg-green-700 text-white",
                isReadOnly && "opacity-50 cursor-not-allowed"
              )}
            >
              <Check className="h-3 w-3" />
              <span>Accept</span>
            </Button>
            
            <Button
              type="button"
              variant={itemDecision === false ? "default" : "outline"}
              size="sm"
              disabled={isReadOnly}
              onClick={(e) => {
                e.preventDefault()
                e.stopPropagation()
                if (!isReadOnly) onItemDecision(product.sku, false)
              }}
              className={cn(
                "flex-1 flex items-center justify-center space-x-1",
                itemDecision === false && "bg-red-600 hover:bg-red-700 text-white",
                isReadOnly && "opacity-50 cursor-not-allowed"
              )}
            >
              <X className="h-3 w-3" />
              <span>Skip</span>
            </Button>
          </div>

          {/* Individual Decision Status */}
          {typeof itemDecision === 'boolean' && (
            <div className={cn(
              "text-xs p-2 rounded-lg font-medium text-center",
              itemDecision 
                ? "bg-green-50 text-green-800 border border-green-200" 
                : "bg-red-50 text-red-800 border border-red-200"
            )}>
              {itemDecision ? "✓ Accepted" : "⊘ Skipped"}
            </div>
          )}
        </CardContent>
      </Card>
    )
  }

  const OneTimeProductCard = ({ product, index }: { product: OneTimeProduct, index: number }) => {
    const [showRationale, setShowRationale] = useState(false)
    const [showNote, setShowNote] = useState(false)
    const itemDecision = getItemDecision(monthIndex, section, product.sku)
    
    // Create personalized labels
    const whyLabel = petName ? `Why this for ${petName}?` : "Why for your pet"
    const rationaleLabel = "Why one-time?"
    
    return (
      <Card className="h-full bg-white/80 backdrop-blur border border-gray-200 hover:shadow-md transition-shadow">
        <CardContent className="p-4 space-y-3">
          
          {/* Header with hyperlinked product name */}
          <div className="space-y-2">
            {product.product_link ? (
              <a 
                href={product.product_link} 
                target="_blank" 
                rel="noopener noreferrer"
                className="font-semibold text-gray-900 leading-tight hover:text-blue-600 hover:underline transition-colors"
              >
                {product.product_name}
              </a>
            ) : (
              <h4 className="font-semibold text-gray-900 leading-tight">{product.product_name}</h4>
            )}
          </div>

          {/* Price & One-Time Badge */}
          <div className="flex items-center justify-between">
            <span className="font-semibold text-lg text-gray-900">
              ${product.product_price_current?.toFixed(2) || 'N/A'}
            </span>
            <Badge variant="secondary" className="bg-green-100 text-green-800">
              One-Time
            </Badge>
          </div>

          {/* Why for your pet - Collapsible */}
          <div className="bg-blue-50 rounded-lg overflow-hidden">
            <button
              onClick={() => setShowNote(!showNote)}
              className="w-full p-3 flex items-center justify-between text-left hover:bg-blue-100 transition-colors"
            >
              <p className="text-sm text-blue-900 font-medium flex items-center gap-1">
                <Sparkles className="h-3 w-3 text-purple-600" />
                {whyLabel}
              </p>
              {showNote ? <ChevronUp className="h-4 w-4 text-blue-600" /> : <ChevronDown className="h-4 w-4 text-blue-600" />}
            </button>
            {showNote && (
              <div className="px-3 pb-3">
                <p className="text-sm text-blue-800">{product.personalized_note}</p>
              </div>
            )}
          </div>

          {/* Rationale - Collapsible */}
          <div className="bg-gray-50 rounded-lg overflow-hidden">
            <button
              onClick={() => setShowRationale(!showRationale)}
              className="w-full p-3 flex items-center justify-between text-left hover:bg-gray-100 transition-colors"
            >
              <p className="text-sm text-gray-700 font-medium">{rationaleLabel}</p>
              {showRationale ? <ChevronUp className="h-4 w-4 text-gray-600" /> : <ChevronDown className="h-4 w-4 text-gray-600" />}
            </button>
            {showRationale && (
              <div className="px-3 pb-3">
                <p className="text-sm text-gray-700">{product.one_time_rationale}</p>
              </div>
            )}
          </div>

          {/* Individual Item Decision Buttons */}
          <div className="flex gap-2 pt-2">
            <Button
              type="button"
              variant={itemDecision === true ? "default" : "outline"}
              size="sm"
              disabled={isReadOnly}
              onClick={(e) => {
                e.preventDefault()
                e.stopPropagation()
                if (!isReadOnly) onItemDecision(product.sku, true)
              }}
              className={cn(
                "flex-1 flex items-center justify-center space-x-1",
                itemDecision === true && "bg-green-600 hover:bg-green-700 text-white",
                isReadOnly && "opacity-50 cursor-not-allowed"
              )}
            >
              <Check className="h-3 w-3" />
              <span>Accept</span>
            </Button>
            
            <Button
              type="button"
              variant={itemDecision === false ? "default" : "outline"}
              size="sm"
              disabled={isReadOnly}
              onClick={(e) => {
                e.preventDefault()
                e.stopPropagation()
                if (!isReadOnly) onItemDecision(product.sku, false)
              }}
              className={cn(
                "flex-1 flex items-center justify-center space-x-1",
                itemDecision === false && "bg-red-600 hover:bg-red-700 text-white",
                isReadOnly && "opacity-50 cursor-not-allowed"
              )}
            >
              <X className="h-3 w-3" />
              <span>Skip</span>
            </Button>
          </div>

          {/* Individual Decision Status */}
          {typeof itemDecision === 'boolean' && (
            <div className={cn(
              "text-xs p-2 rounded-lg font-medium text-center",
              itemDecision 
                ? "bg-green-50 text-green-800 border border-green-200" 
                : "bg-red-50 text-red-800 border border-red-200"
            )}>
              {itemDecision ? "✓ Accepted" : "⊘ Skipped"}
            </div>
          )}
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="w-full shadow-sm bg-white/90 backdrop-blur">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center space-x-2">
              <CardTitle className="text-xl font-bold text-gray-900">{title}</CardTitle>
              {isReadOnly && (
                <Badge variant="secondary" className="text-xs">
                  Completed
                </Badge>
              )}
            </div>
            <p className="text-gray-600 mt-1">
              {isReadOnly ? "This month has been completed. View-only mode." : subtitle}
            </p>
          </div>
          
          {/* Section-Level Decision Buttons */}
          <div className="flex items-center space-x-2">
            <Button
              type="button"
              variant={sectionDecision === true ? "default" : "outline"}
              size="sm"
              disabled={isReadOnly}
              onClick={(e) => {
                e.preventDefault()
                e.stopPropagation()
                if (!isReadOnly) onSectionDecision(true)
              }}
              className={cn(
                "flex items-center space-x-2",
                sectionDecision === true && "bg-green-600 hover:bg-green-700 text-white",
                isReadOnly && "opacity-50 cursor-not-allowed"
              )}
            >
              <Check className="h-4 w-4" />
              <span>Accept All</span>
            </Button>
            
            <Button
              type="button"
              variant={sectionDecision === false ? "default" : "outline"}
              size="sm"
              disabled={isReadOnly}
              onClick={(e) => {
                e.preventDefault()
                e.stopPropagation()
                if (!isReadOnly) onSectionDecision(false)
              }}
              className={cn(
                "flex items-center space-x-2",
                sectionDecision === false && "bg-red-600 hover:bg-red-700 text-white",
                isReadOnly && "opacity-50 cursor-not-allowed"
              )}
            >
              <X className="h-4 w-4" />
              <span>Skip All</span>
            </Button>
          </div>
        </div>


        {/* Section Decision Status */}
        {typeof sectionDecision === 'boolean' && (
          <div className={cn(
            "mt-3 p-2 rounded-lg text-sm font-medium",
            sectionDecision 
              ? "bg-green-50 text-green-800 border border-green-200" 
              : "bg-red-50 text-red-800 border border-red-200"
          )}>
            {sectionDecision 
              ? `✓ All Accepted - You've chosen to add all ${title.toLowerCase()} to this month` 
              : `⊘ All Skipped - You've chosen to skip all ${title.toLowerCase()} this month`
            }
          </div>
        )}
      </CardHeader>

      <CardContent className="pt-0">
        {/* Loading State */}
        {isLoadingPlan && (useSubscriptionPlan || useOneTimePlan) && (
          <div className="flex items-center justify-center p-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-gray-600">Loading plan...</span>
          </div>
        )}

        {/* Products Grid - With Scrollbar for Subscription Plan */}
        {!isLoadingPlan && useSubscriptionPlan && (
          <div className="max-h-[600px] overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100">
            <div className="grid gap-4 sm:grid-cols-1 lg:grid-cols-2">
              {subscriptionPlanData!.map((product, index) => (
                <SubscriptionProductCard key={product.sku} product={product} index={index} />
              ))}
            </div>
          </div>
        )}

        {/* Products Grid - With Scrollbar for One-Time Plan */}
        {!isLoadingPlan && useOneTimePlan && (
          <div className="max-h-[600px] overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100">
            <div className="grid gap-4 sm:grid-cols-1 lg:grid-cols-2">
              {oneTimePlanData!.map((product, index) => (
                <OneTimeProductCard key={product.sku} product={product} index={index} />
              ))}
            </div>
          </div>
        )}

        {/* Legacy Products Grid */}
        {!useSubscriptionPlan && !useOneTimePlan && (
          <div className="grid gap-4 sm:grid-cols-1 lg:grid-cols-2">
            {items.map((item) => (
              <ProductCard key={item.id} item={item} />
            ))}
          </div>
        )}

        {/* Section Summary */}
        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-700">
            <span className="font-medium">
              {useSubscriptionPlan ? subscriptionPlanData!.length : 
               useOneTimePlan ? oneTimePlanData!.length : 
               items.length} item{(useSubscriptionPlan ? subscriptionPlanData!.length : 
                                useOneTimePlan ? oneTimePlanData!.length : 
                                items.length) > 1 ? 's' : ''}
            </span> in this section
            {!useSubscriptionPlan && !useOneTimePlan && items.some(item => item.isAIGenerated) && (
              <span className="ml-2 text-purple-600">• Includes AI-suggested items</span>
            )}
            {useSubscriptionPlan && (
              <span className="ml-2 text-blue-600">• AI-optimized subscription plan</span>
            )}
            {useOneTimePlan && (
              <span className="ml-2 text-green-600">• AI-optimized one-time purchases</span>
            )}
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
