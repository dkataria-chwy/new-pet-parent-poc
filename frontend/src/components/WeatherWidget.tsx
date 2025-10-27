"use client"

import { useState, useEffect } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { MapPin, Sun, Cloud, CloudRain, CloudSnow, Zap, AlertTriangle, X } from "lucide-react"
import { AnimatePresence, motion } from "framer-motion"

interface WeatherWidgetProps {
  zipCode: string
  petName: string
}

interface CurrentWeather {
  temperature_f: number | null
  temperature_c: number | null
  conditions: string | null
  humidity: number | null
  wind_speed_mph: number | null
}

interface WeatherData {
  location: {
    zip: string
    state: string | null
  }
  current: CurrentWeather | null
  triggers: Array<{
    category: string
    description: string
    confidence: number
  }>
}

export function WeatherWidget({ zipCode, petName }: WeatherWidgetProps) {
  const [weatherData, setWeatherData] = useState<WeatherData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showAlerts, setShowAlerts] = useState(false)

  useEffect(() => {
    const fetchWeather = async () => {
      if (!zipCode || zipCode === "00000") {
        setLoading(false)
        return
      }

      try {
        setLoading(true)
        // Call backend weather API with CSV alerts enabled
        const response = await fetch(`/api/weather/${zipCode}?include_csv_alerts=true`)
        
        if (!response.ok) {
          throw new Error('Weather data unavailable')
        }
        
        const data = await response.json()
        setWeatherData(data.data)
        setError(null)
      } catch (err) {
        console.error('Failed to fetch weather:', err)
        setError('Weather unavailable')
      } finally {
        setLoading(false)
      }
    }

    fetchWeather()
  }, [zipCode])

  // Close alerts popup when clicking outside (copied from allergies logic)
  useEffect(() => {
    const handleClickOutside = () => {
      if (showAlerts) {
        setShowAlerts(false)
      }
    }

    if (showAlerts) {
      document.addEventListener('click', handleClickOutside)
    }

    return () => {
      document.removeEventListener('click', handleClickOutside)
    }
  }, [showAlerts])

  // Get current date info
  const now = new Date()
  const dayName = now.toLocaleDateString('en-US', { weekday: 'long' })
  const dateStr = now.toLocaleDateString('en-US', { 
    day: 'numeric',
    month: 'long'
  })

  // Get weather icon based on conditions - 3D style like your screenshot
  const getWeatherIcon = (conditions: string | null, temp: number | null) => {
    const condition = conditions?.toLowerCase() || ""
    
    // Partly Cloudy (like your screenshot) - Sun behind cloud with proper positioning
    if (condition.includes('partly') || condition.includes('partial')) {
      return (
        <div className="relative w-24 h-20">
          {/* Sun behind cloud - bigger and positioned like your screenshots */}
          <div className="absolute top-0 right-0 w-16 h-16 rounded-full bg-gradient-to-br from-yellow-300 via-orange-300 to-orange-400 shadow-2xl">
            {/* Sun highlight */}
            <div className="absolute top-2 left-2 w-4 h-4 bg-white/30 rounded-full blur-sm"></div>
          </div>
          {/* Cloud in front with better visibility - no negative positioning */}
          <div className="absolute bottom-2 left-0 w-18 h-14">
            <div className="relative">
              {/* Main cloud body with border */}
              <div className="absolute top-4 left-0 w-14 h-7 bg-gradient-to-br from-white via-gray-50 to-gray-100 rounded-full shadow-xl border-2 border-gray-300/50"></div>
              {/* Cloud bumps with borders - no negative positioning */}
              <div className="absolute top-2 left-3 w-7 h-7 bg-gradient-to-br from-white via-gray-50 to-gray-100 rounded-full shadow-lg border-2 border-gray-300/50"></div>
              <div className="absolute top-3 right-2 w-5 h-5 bg-gradient-to-br from-white via-gray-50 to-gray-100 rounded-full shadow-lg border-2 border-gray-300/50"></div>
            </div>
          </div>
        </div>
      )
    }
    
    // Clear/Sunny - 3D Sun (like your screenshots)
    if (condition.includes('clear') || condition.includes('sunny')) {
      return (
        <div className="w-20 h-20 rounded-full bg-gradient-to-br from-yellow-300 via-orange-300 to-orange-400 shadow-2xl relative">
          {/* Sun highlight for 3D effect */}
          <div className="absolute top-3 left-3 w-6 h-6 bg-white/30 rounded-full blur-sm"></div>
          <div className="absolute top-4 left-4 w-3 h-3 bg-white/50 rounded-full"></div>
        </div>
      )
    }
    
    // Cloudy - 3D Cloud with better visibility and proper positioning
    if (condition.includes('cloud') || condition.includes('overcast')) {
      return (
        <div className="relative w-16 h-14 mt-2">
          {/* Main cloud body with border for contrast */}
          <div className="absolute top-4 left-2 w-12 h-6 bg-gradient-to-br from-white via-gray-100 to-gray-200 rounded-full shadow-xl border-2 border-gray-300/50"></div>
          {/* Cloud bumps with borders - no negative positioning */}
          <div className="absolute top-2 left-4 w-6 h-6 bg-gradient-to-br from-white via-gray-100 to-gray-200 rounded-full shadow-lg border-2 border-gray-300/50"></div>
          <div className="absolute top-3 right-3 w-4 h-4 bg-gradient-to-br from-white via-gray-100 to-gray-200 rounded-full shadow-lg border-2 border-gray-300/50"></div>
          <div className="absolute top-5 left-8 w-5 h-5 bg-gradient-to-br from-white via-gray-100 to-gray-200 rounded-full shadow-lg border-2 border-gray-300/50"></div>
        </div>
      )
    }
    
    // Rainy - Cloud with rain (darker clouds are more visible, proper positioning)
    if (condition.includes('rain') || condition.includes('shower')) {
      return (
        <div className="relative w-16 h-16 mt-2">
          {/* Cloud with borders for definition - no negative positioning */}
          <div className="relative w-16 h-10">
            <div className="absolute top-4 left-2 w-12 h-6 bg-gradient-to-br from-gray-300 via-gray-400 to-gray-500 rounded-full shadow-xl border-2 border-gray-400/60"></div>
            <div className="absolute top-2 left-4 w-6 h-6 bg-gradient-to-br from-gray-300 via-gray-400 to-gray-500 rounded-full shadow-lg border-2 border-gray-400/60"></div>
            <div className="absolute top-3 right-1 w-4 h-4 bg-gradient-to-br from-gray-300 via-gray-400 to-gray-500 rounded-full shadow-lg border-2 border-gray-400/60"></div>
          </div>
          {/* Rain drops */}
          <div className="absolute bottom-0 left-2 w-0.5 h-4 bg-blue-300 rounded-full opacity-70"></div>
          <div className="absolute bottom-0 left-6 w-0.5 h-3 bg-blue-300 rounded-full opacity-70"></div>
          <div className="absolute bottom-0 left-10 w-0.5 h-4 bg-blue-300 rounded-full opacity-70"></div>
        </div>
      )
    }
    
    // Default - Partly cloudy with proper positioning
    return (
      <div className="relative w-24 h-20">
        <div className="absolute top-0 right-0 w-16 h-16 rounded-full bg-gradient-to-br from-yellow-300 via-orange-300 to-orange-400 shadow-2xl">
          <div className="absolute top-2 left-2 w-4 h-4 bg-white/30 rounded-full blur-sm"></div>
        </div>
        <div className="absolute bottom-2 left-0 w-18 h-14">
          <div className="relative">
            <div className="absolute top-4 left-0 w-14 h-7 bg-gradient-to-br from-white via-gray-50 to-gray-100 rounded-full shadow-xl border-2 border-gray-300/50"></div>
            <div className="absolute top-2 left-3 w-7 h-7 bg-gradient-to-br from-white via-gray-50 to-gray-100 rounded-full shadow-lg border-2 border-gray-300/50"></div>
            <div className="absolute top-3 right-2 w-5 h-5 bg-gradient-to-br from-white via-gray-50 to-gray-100 rounded-full shadow-lg border-2 border-gray-300/50"></div>
          </div>
        </div>
      </div>
    )
  }

  // Simple gradient - one consistent style
  const getGradient = () => {
    return "from-blue-400 via-indigo-500 to-purple-600"
  }

  if (loading) {
    return (
      <Card className="relative overflow-hidden shadow-xl">
        <div className="bg-gradient-to-br from-blue-400 via-sky-400 to-cyan-400 p-6 text-white">
          <div className="flex items-center space-x-2">
            <div className="animate-pulse">
              <div className="w-4 h-4 bg-white/30 rounded"></div>
            </div>
            <p className="text-sm opacity-90">Loading weather...</p>
          </div>
        </div>
      </Card>
    )
  }

  if (error || !weatherData?.current) {
    return (
      <Card className="relative overflow-hidden shadow-xl">
        <div className="bg-gradient-to-br from-gray-400 via-gray-500 to-gray-600 p-6 text-white">
          <div className="flex justify-between items-start">
            <div>
              <div className="text-lg font-light mb-1">Weather</div>
              <div className="text-4xl font-light mb-2">--°</div>
              <div className="text-sm opacity-90">{dayName}, {dateStr}</div>
              <div className="flex items-center text-sm opacity-90 mt-1">
                <MapPin className="w-3 h-3 mr-1" />
                {zipCode}
              </div>
            </div>
            <div className="opacity-50">
              <Cloud className="w-16 h-16" />
            </div>
          </div>
        </div>
      </Card>
    )
  }

  const { current, triggers } = weatherData
  const temp = current.temperature_f
  
  // Use real alerts only
  const allTriggers = triggers || []
  const hasAlerts = allTriggers && allTriggers.length > 0
  const conditions = current.conditions || "Clear"
  
  // Debug: Log what we're receiving
  console.log("Weather data triggers:", triggers)
  console.log("All triggers:", allTriggers)
  console.log("Has alerts:", hasAlerts)

  return (
    <div className="relative">
      <Card className="relative shadow-xl rounded-2xl overflow-hidden">
        {/* Weather Icon - Badge style overlay like your pet image */}
        <div className="absolute -top-4 -right-4 z-20">
          {getWeatherIcon(conditions, temp)}
        </div>

        {/* Alerts Tag - Bottom right of card (styled like allergies) */}
        {hasAlerts && (
          <div className="absolute bottom-3 right-3 z-20">
            <div className="relative inline-block">
              <button 
                className="text-xs bg-orange-100 text-orange-700 px-2 py-0.5 rounded-full hover:bg-orange-200 transition-colors cursor-pointer"
                onClick={(e) => {
                  e.stopPropagation();
                  setShowAlerts(!showAlerts);
                }}
                title="Click to view weather alerts"
              >
                ⚠️ Alerts
              </button>
            </div>
          </div>
        )}

        {/* Main Weather Card */}
        <div className={`bg-gradient-to-br ${getGradient()} p-4 text-white relative`}>
          
          {/* Weather Content */}
          <div className="relative z-10">
            
            {/* Weather Info Layout - Like Paris reference */}
            <div className="flex items-start pr-16">
              
              {/* Left Side - Condition & Temperature */}
              <div>
                {/* Weather Condition */}
                <div className="text-lg font-light mb-1 opacity-95">
                  {conditions}
                </div>
                
                {/* Temperature */}
                <div className="text-5xl font-light leading-none">
                  {temp ? `${Math.round(temp)}°` : '--°'}
                </div>
              </div>

              {/* Right Side - Date & Location (closer to temperature) */}
              <div className="mt-8 ml-6">
                {/* Date */}
                <div className="text-sm opacity-90 mb-1">
                  {dayName}, {dateStr}
                </div>
                
                {/* Location */}
                <div className="flex items-center text-sm opacity-90">
                  <MapPin className="w-3 h-3 mr-1" />
                  {zipCode}
                </div>
              </div>
              
            </div>
            
          </div>

        </div>
      </Card>

      {/* Alerts Popup Card - Outside the card to avoid clipping */}
      {hasAlerts && (
        <AnimatePresence>
          {showAlerts && (
            <motion.div
              initial={{ opacity: 0, y: -10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.95 }}
              transition={{ duration: 0.2 }}
              className="absolute top-full right-3 mt-1 z-50 bg-white border border-orange-200 rounded-lg shadow-lg p-3 min-w-48"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center gap-2 mb-2">
                <span className="text-orange-600">⚠️</span>
                <span className="font-semibold text-orange-800 text-sm">Weather Alerts</span>
              </div>
              
              {/* Alert Content */}
              <div className="space-y-2">
                {allTriggers.map((trigger, index) => (
                  <div key={index} className="text-sm text-gray-700 bg-orange-50 p-2 rounded border-l-2 border-orange-300">
                    <div className="font-medium text-orange-800 mb-1">
                      {trigger.category}
                    </div>
                    <div className="text-gray-700">
                      {trigger.description}
                    </div>
                    <div className="text-xs text-orange-600 mt-1">
                      Confidence: {Math.round(trigger.confidence * 100)}%
                    </div>
                  </div>
                ))}
              </div>
              
              <button 
                onClick={(e) => {
                  e.stopPropagation();
                  setShowAlerts(false);
                }}
                className="absolute top-1 right-1 text-gray-400 hover:text-gray-600 text-sm"
              >
                ✕
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      )}
    </div>
  )
}
