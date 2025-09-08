"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Check, X, Package, Truck } from "lucide-react"
import { JourneyState } from "@/lib/store"

interface MonthRecapProps {
  monthIndex: number
  journey: JourneyState
  recommendations?: {
    subscriptions: any[]
    bundles: any[]
    singles: any[]
  }
}

export function MonthRecap({ monthIndex, journey, recommendations }: MonthRecapProps) {
  const monthKey = monthIndex.toString()
  const monthDecisions = journey.decisions[monthKey] || {}

  // Get actual user decisions for this month
  const getRecapData = () => {
    const acceptedSections: string[] = []
    const skippedSections: string[] = []
    const acceptedItems: { [section: string]: string[] } = {}
    const skippedItems: { [section: string]: string[] } = {}

    // Process each section (subscriptions, bundles, singles)
    Object.entries(monthDecisions).forEach(([section, sectionDecisions]) => {
      const sectionItems = Object.entries(sectionDecisions)
      const acceptedCount = sectionItems.filter(([_, decision]) => decision === true).length
      const skippedCount = sectionItems.filter(([_, decision]) => decision === false).length
      const totalCount = sectionItems.length

      if (acceptedCount === totalCount) {
        // All items accepted
        acceptedSections.push(section)
        acceptedItems[section] = sectionItems.map(([itemId, _]) => {
          // Try to find the actual item name from recommendations
          if (recommendations) {
            const sectionRecs = recommendations[section as keyof typeof recommendations] || []
            const item = sectionRecs.find((rec: any) => rec.id === itemId)
            return item?.title || `Item ${itemId}`
          }
          return `Item ${itemId}`
        })
      } else if (skippedCount === totalCount) {
        // All items skipped
        skippedSections.push(section)
      } else if (acceptedCount > 0) {
        // Mixed decisions - show as accepted section with specific items
        acceptedSections.push(section)
        acceptedItems[section] = sectionItems
          .filter(([_, decision]) => decision === true)
          .map(([itemId, _]) => {
            // Try to find the actual item name from recommendations
            if (recommendations) {
              const sectionRecs = recommendations[section as keyof typeof recommendations] || []
              const item = sectionRecs.find((rec: any) => rec.id === itemId)
              return item?.title || `Item ${itemId}`
            }
            return `Item ${itemId}`
          })
      }
    })

    return {
      accepted: acceptedSections.map(section => ({
        section: section.charAt(0).toUpperCase() + section.slice(1),
        items: acceptedItems[section] || [],
        nextShipDate: getNextShipDate(section)
      })),
      skipped: skippedSections.map(section => ({
        section: section.charAt(0).toUpperCase() + section.slice(1),
        reason: "User chose to skip this month"
      }))
    }
  }



  const getNextShipDate = (section: string) => {
    if (section === "subscriptions") {
      const futureDate = new Date()
      futureDate.setDate(futureDate.getDate() + 28) // 4 weeks
      return futureDate.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric' 
      })
    }
    return null
  }

  const recapData = getRecapData()

  if (Object.keys(monthDecisions).length === 0) {
    return null // No decisions made for this month yet
  }

  return (
    <Card className="w-full shadow-sm bg-white/90 backdrop-blur">
      <CardHeader className="pb-4">
        <CardTitle className="text-lg font-bold text-gray-900 flex items-center space-x-2">
          <Package className="h-5 w-5 text-blue-600" />
          <span>Month {monthIndex + 1} Recap</span>
        </CardTitle>
        <p className="text-sm text-gray-600">Summary of your previous selections</p>
      </CardHeader>

      <CardContent className="space-y-4">
        
        {/* Accepted Items */}
        {recapData.accepted.length > 0 && (
          <div className="space-y-3">
            <h4 className="font-semibold text-green-800 flex items-center space-x-2">
              <Check className="h-4 w-4" />
              <span>Accepted ({recapData.accepted.length})</span>
            </h4>
            
            {recapData.accepted.map((item, index) => (
              <div key={index} className="bg-green-50 p-3 rounded-lg border border-green-200">
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <p className="font-medium text-green-900">{item.section}</p>
                    <div className="space-y-0.5">
                      {item.items.map((product, idx) => (
                        <p key={idx} className="text-sm text-green-800">• {product}</p>
                      ))}
                    </div>
                  </div>
                  
                  {item.nextShipDate && (
                    <div className="text-right">
                      <div className="flex items-center space-x-1 text-xs text-green-700">
                        <Truck className="h-3 w-3" />
                        <span>Next ship</span>
                      </div>
                      <p className="text-sm font-medium text-green-800">
                        ~{item.nextShipDate}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Skipped Items */}
        {recapData.skipped.length > 0 && (
          <div className="space-y-3">
            <h4 className="font-semibold text-red-800 flex items-center space-x-2">
              <X className="h-4 w-4" />
              <span>Skipped ({recapData.skipped.length})</span>
            </h4>
            
            {recapData.skipped.map((item, index) => (
              <div key={index} className="bg-red-50 p-3 rounded-lg border border-red-200">
                <p className="font-medium text-red-900">{item.section}</p>
                <p className="text-sm text-red-700">{item.reason}</p>
              </div>
            ))}
          </div>
        )}

        {/* Summary Stats */}
        <div className="bg-gray-50 p-3 rounded-lg">
          <div className="grid grid-cols-2 gap-4 text-center">
            <div>
              <p className="text-2xl font-bold text-green-600">{recapData.accepted.length}</p>
              <p className="text-xs text-gray-600">Sections Accepted</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-red-600">{recapData.skipped.length}</p>
              <p className="text-xs text-gray-600">Sections Skipped</p>
            </div>
          </div>
        </div>

        {/* Note about subscriptions */}
        {recapData.accepted.some(item => item.section === "Subscriptions") && (
          <div className="bg-blue-50 p-3 rounded-lg border border-blue-200">
            <p className="text-sm text-blue-800">
              <strong>Subscription Note:</strong> Your ongoing subscriptions will continue to ship automatically. 
              You can modify or pause them anytime.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
