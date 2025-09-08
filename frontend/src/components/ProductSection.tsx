"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Check, X, Sparkles } from "lucide-react"
import { RecommendationItem } from "@/lib/store"
import { cn } from "@/lib/utils"

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
  onSectionDecision 
}: ProductSectionProps) {
  if (!items.length) return null

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
            onClick={(e) => {
              e.preventDefault()
              e.stopPropagation()
              onItemDecision(item.id, true)
            }}
            className={cn(
              "flex-1 flex items-center justify-center space-x-1",
              itemDecision === true && "bg-green-600 hover:bg-green-700 text-white"
            )}
          >
            <Check className="h-3 w-3" />
            <span>Accept</span>
          </Button>
          
          <Button
            type="button"
            variant={itemDecision === false ? "default" : "outline"}
            size="sm"
            onClick={(e) => {
              e.preventDefault()
              e.stopPropagation()
              onItemDecision(item.id, false)
            }}
            className={cn(
              "flex-1 flex items-center justify-center space-x-1",
              itemDecision === false && "bg-red-600 hover:bg-red-700 text-white"
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
            <CardTitle className="text-xl font-bold text-gray-900">{title}</CardTitle>
            <p className="text-gray-600 mt-1">{subtitle}</p>
          </div>
          
          {/* Section-Level Decision Buttons */}
          <div className="flex items-center space-x-2">
            <Button
              type="button"
              variant={sectionDecision === true ? "default" : "outline"}
              size="sm"
              onClick={(e) => {
                e.preventDefault()
                e.stopPropagation()
                onSectionDecision(true)
              }}
              className={cn(
                "flex items-center space-x-2",
                sectionDecision === true && "bg-green-600 hover:bg-green-700 text-white"
              )}
            >
              <Check className="h-4 w-4" />
              <span>Accept All</span>
            </Button>
            
            <Button
              type="button"
              variant={sectionDecision === false ? "default" : "outline"}
              size="sm"
              onClick={(e) => {
                e.preventDefault()
                e.stopPropagation()
                onSectionDecision(false)
              }}
              className={cn(
                "flex items-center space-x-2",
                sectionDecision === false && "bg-red-600 hover:bg-red-700 text-white"
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
        {/* Products Grid */}
        <div className="grid gap-4 sm:grid-cols-1 lg:grid-cols-2">
          {items.map((item) => (
            <ProductCard key={item.id} item={item} />
          ))}
        </div>

        {/* Section Summary */}
        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-700">
            <span className="font-medium">{items.length} item{items.length > 1 ? 's' : ''}</span> in this section
            {items.some(item => item.isAIGenerated) && (
              <span className="ml-2 text-purple-600">• Includes AI-suggested items</span>
            )}
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
