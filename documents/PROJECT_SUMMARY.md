# Chewy Journey - AI-Powered Pet Care Concierge System

## 🎯 Project Overview

**Chewy Journey** is a sophisticated AI-powered pet care concierge system that provides personalized product recommendations through a gamified 15-month journey experience. The system combines advanced AI/ML capabilities with a modern web interface to deliver context-aware pet product suggestions based on comprehensive pet profiles, environmental factors, and behavioral patterns.

## 🏗️ System Architecture

### Frontend (Next.js 15 + React 19)
- **Framework**: Next.js 15 with App Router and Turbopack
- **UI Components**: shadcn/ui + Radix UI primitives
- **Styling**: Tailwind CSS v4
- **State Management**: Zustand for client state
- **Animation**: Framer Motion for smooth dog movement animations
- **Validation**: Zod schemas for type safety
- **Testing**: Vitest (unit) + Playwright (E2E)

### Backend (FastAPI + Python)
- **API Framework**: FastAPI with Pydantic models
- **Database**: SQLite (development) with easy production migration path
- **AI Integration**: OpenAI GPT-5/GPT-4.1 for semantic query generation
- **Vector Search**: Custom embeddings pipeline with 117K+ product embeddings
- **Policy Engine**: Pluggable recommendation system (Rules → LLM → ML)

## 🧠 AI/ML Capabilities

### 1. Semantic Query Composition System
- **Purpose**: Generates intelligent product search queries using advanced AI
- **Models**: GPT-5 (primary) with GPT-4.1 fallback
- **Input Processing**: 
  - Pet profiles (breed, age, weight, activity level, allergies, etc.)
  - Weather context (heat waves, storms, seasonal changes)
  - Calendar events (travel, fireworks, vet visits)
  - User preferences and brand biases
- **Output**: Structured JSON with multiple "slots" containing:
  - Embedding queries (semantic vector search)
  - BM25 queries (lexical boolean search)
  - Product filters and constraints
  - Evidence trails for transparency

### 2. Product Embeddings Pipeline
- **Scale**: 117,584 products with 3072-dimensional embeddings
- **Cost**: $17.15 one-time investment for unlimited searches
- **Performance**: ~100ms search response time
- **Features**:
  - Species filtering (dog/cat)
  - Semantic similarity matching
  - Brand preference integration
  - Safety constraint enforcement

### 3. Checkpoint Validation System
- **Purpose**: AI-powered validation of pet profile updates
- **Functionality**:
  - Detects anomalies in pet data changes (weight, activity, health)
  - Generates intelligent follow-up questions
  - Provides confidence scoring
  - Maintains pet health history tracking
- **Use Cases**: Monthly check-ins, health monitoring, growth tracking

### 4. Context-Aware Recommendations
- **Multi-Modal Input Processing**:
  - Pet characteristics (comprehensive 20+ attributes)
  - Environmental factors (weather alerts, seasonal changes)
  - Calendar events (travel, holidays, vet appointments)
  - Historical preferences and decisions
- **Output Categories**:
  - Subscriptions (recurring essentials)
  - Bundles (curated product combinations)
  - Singles (one-time purchases)

## 📊 Data Models & Intelligence

### Pet Profile Attributes
```
Core: name, species, breed, age, gender
Physical: weight, height, chew strength, activity level
Environmental: household type, yard access, zip code
Health: allergies, health conditions, dietary restrictions
Behavioral: about (personality), appearance (for avatars)
Preferences: budget band, brand preferences
```

### Environmental Context Integration
- **Weather API**: Real-time alerts and forecasts affecting pet needs
- **Calendar Events**: Zip code-based events (fireworks, parades, storms)
- **Seasonal Adjustments**: Automatic product recommendations based on time of year

### Journey State Management
- **15-Month Timeline**: Gamified progression through pet care milestones
- **Decision Tracking**: Accept/Skip decisions for each recommendation
- **Progress Visualization**: Animated dog character moving through checkpoints
- **Historical Analysis**: Learning from past decisions to improve future recommendations

## 🔧 Technical Implementation

### AI Query Generation Pipeline
1. **Context Building**: Aggregates pet profile, weather, calendar, and historical data
2. **Prompt Engineering**: Uses sophisticated templates with 150+ line system prompts
3. **Model Orchestration**: GPT-5 with automatic fallback to GPT-4.1 on timeout
4. **Schema Validation**: Ensures structured output with retry mechanisms
5. **Output Storage**: Saves all AI outputs with run history tracking

### Vector Search Architecture
```
Input Query → Embedding Generation → Similarity Search → Filtering → Ranking
```
- **Embedding Model**: OpenAI text-embedding-3-large (3072 dimensions)
- **Search Strategy**: Hybrid approach combining semantic and lexical search
- **Filtering**: Species, allergens, safety constraints, brand preferences
- **Ranking**: Reciprocal Rank Fusion (RRF) for optimal results

### Recommendation Policy System
```
Rules-Based (Current) → LLM-Enhanced → ML-Powered (Future)
```
- **Pluggable Architecture**: Easy switching between recommendation strategies
- **Environment Control**: `AI_POLICY` environment variable controls active system
- **Extensibility**: Ready for production ML model integration

## 🎮 User Experience Features

### Onboarding Flow
1. **Welcome Page**: Introduction to the journey concept
2. **Pet Profile Creation**: 3-step comprehensive profile building
3. **Journey Initialization**: 15-checkpoint timeline setup
4. **First Month**: Immediate recommendations based on profile

### Journey Interface
- **Visual Progress Strip**: 15 checkpoints with animated dog character
- **Month Detail Pages**: Detailed product recommendations with explanations
- **Accept/Skip Decisions**: Simple binary choices for each product category
- **AI Input Box**: Natural language input for custom recommendations
- **"Why for {PetName}"**: Personalized explanations for each suggestion

### Interactive Elements
- **Smooth Animations**: 1.2s dog movement between checkpoints
- **Responsive Design**: Works on mobile and desktop
- **Accessibility**: ARIA labels, keyboard navigation
- **Real-time Updates**: Optimistic UI with backend synchronization

## 📈 Analytics & Monitoring

### Event Tracking
- Journey creation and progression
- Recommendation acceptance/rejection rates
- AI query performance and costs
- Checkpoint completion patterns
- User engagement metrics

### Performance Monitoring
- API response times
- AI model success rates
- Vector search performance
- Database query optimization
- Error tracking and alerting

## 🔮 Advanced AI Features

### Intelligent Product Matching
- **Breed-Specific Recommendations**: Considers breed characteristics and common needs
- **Life Stage Optimization**: Puppy/kitten growth, adult maintenance, senior care
- **Activity Level Matching**: High-energy vs. low-activity product suggestions
- **Health Condition Awareness**: Allergen avoidance, special dietary needs
- **Seasonal Intelligence**: Weather-appropriate products and seasonal care items

### Natural Language Processing
- **User Intent Recognition**: Processes free-form text input about pet needs
- **Context Understanding**: Interprets requests in context of pet profile and history
- **Explanation Generation**: Creates personalized "why" explanations for recommendations
- **Follow-up Questions**: Intelligent clarification requests for ambiguous input

### Predictive Capabilities
- **Growth Tracking**: Predicts puppy/kitten development needs
- **Seasonal Preparation**: Anticipates weather-related product needs
- **Health Monitoring**: Flags unusual changes in pet metrics
- **Preference Learning**: Adapts recommendations based on historical decisions

## 🚀 Production Readiness

### Scalability Features
- **Modular Architecture**: Easy component replacement and scaling
- **Database Migration Ready**: Simple switch from SQLite to PostgreSQL/MongoDB
- **API Rate Limiting**: Built-in protection against abuse
- **Caching Strategy**: Optimized for high-traffic scenarios

### Security & Privacy
- **Data Validation**: Comprehensive input sanitization
- **CORS Configuration**: Secure cross-origin resource sharing
- **Environment Variables**: Secure API key management
- **Error Handling**: Graceful failure modes with user-friendly messages

### Monitoring & Observability
- **Structured Logging**: Comprehensive event and error tracking
- **Performance Metrics**: API response times and success rates
- **Cost Tracking**: AI API usage and optimization
- **Health Checks**: System status monitoring endpoints

## 💡 Innovation Highlights

1. **Multi-Modal AI Integration**: Combines pet profiles, weather, calendar, and behavioral data
2. **Hybrid Search Architecture**: Semantic + lexical search for optimal product discovery
3. **Gamified Pet Care**: Makes routine pet care engaging through journey progression
4. **Explainable AI**: Transparent reasoning for all recommendations
5. **Real-Time Context Awareness**: Dynamic adaptation to environmental changes
6. **Comprehensive Pet Intelligence**: 20+ attributes for nuanced recommendations

## 🎯 Business Value

- **Personalization at Scale**: AI-driven recommendations for thousands of pet profiles
- **Increased Engagement**: Gamified experience encourages regular interaction
- **Higher Conversion**: Context-aware suggestions improve purchase likelihood
- **Customer Retention**: Journey format creates long-term engagement
- **Operational Efficiency**: Automated recommendation generation reduces manual curation
- **Data-Driven Insights**: Rich analytics for product and marketing optimization

---

This system represents a cutting-edge application of AI/ML in e-commerce, specifically designed for the pet care industry. It combines sophisticated technical capabilities with an intuitive user experience to deliver personalized, intelligent product recommendations that adapt to each pet's unique needs and circumstances.
