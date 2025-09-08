# Chewy Journey

A gamified monthly journey application for pets, built with Next.js (frontend) and FastAPI (backend).

## Project Structure

```
.
├── frontend/          # Next.js React app
├── backend/           # FastAPI Python service
└── README.md
```

## Features

- **Onboarding Flow**: Welcome page → pet profile creation → journey initialization
- **Journey Overview**: 15-checkpoint visual progress strip with dog animation
- **Monthly Details**: Product recommendations with Accept/Skip decisions
- **AI Recommendations**: Context-aware suggestions based on pet needs
- **Progress Tracking**: Visual journey progression and month completion

## Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.8+ and pip

### 1. Start Backend (Terminal 1)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Backend runs at: http://localhost:8000

### 2. Start Frontend (Terminal 2)

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: http://localhost:3000

## Development

### Frontend Architecture
- **Framework**: Next.js 15 with App Router
- **Styling**: Tailwind CSS + shadcn/ui components
- **State**: Zustand store for client state
- **Animation**: Framer Motion for dog movement
- **Validation**: Zod schemas

### Backend Architecture
- **Framework**: FastAPI with Pydantic models
- **Database**: SQLite for development (easily replaceable)
- **Policy Engine**: Pluggable recommendation system
- **API Design**: RESTful endpoints with clear contracts

### Key Components

**Frontend:**
- `CheckpointStrip`: Visual journey progress with dog animation
- `ProductSection`: Accept/Skip recommendation sections
- `AIRecommendationBox`: Context-aware AI suggestions
- `PetProfileCard`: Pet information and journey status

**Backend:**
- `RecommendationPolicy`: Pluggable policy system (rules → LLM → ML)
- `Database`: SQLite with simple schema
- `API Endpoints`: Pet/Journey CRUD + recommendations

## Testing

### Frontend Tests
```bash
cd frontend

# Unit tests
npm run test

# E2E tests
npm run test:e2e

# All tests
npm run test:all
```

### Backend Tests
```bash
cd backend
source venv/bin/activate
pytest
```

## API Endpoints

- `POST /profile` - Create pet profile
- `POST /journey` - Initialize 15-month journey
- `PATCH /journey/state` - Update decisions/completion
- `GET /recommendations` - Get baseline recommendations
- `POST /ai/recs` - Get AI-generated suggestions
- `POST /events` - Log analytics events

## Architecture Decisions

### Pluggable Recommendation System
The backend uses a policy pattern for recommendations:
- **Rules-based** (current): Simple logic based on pet profile
- **LLM-ready**: Easy integration with language models
- **ML-ready**: Placeholder for machine learning models

Environment variable `AI_POLICY` controls which system to use.

### State Management
- **Frontend**: Zustand for UI state, API for persistence
- **Backend**: SQLite for simple local development
- **Sync**: Frontend state mirrors backend, with optimistic updates

### Animation System
- Dog icon animates between checkpoints using Framer Motion
- 1.2s smooth transitions as specified
- Non-blocking UI during animations
- Accessibility-friendly with proper ARIA labels

## Acceptance Criteria ✅

- [x] Runs locally: Next.js (3000) + FastAPI (8000)
- [x] Complete onboarding flow: welcome → profile → journey
- [x] 15 checkpoints with start button placement
- [x] Dog animation between checkpoints
- [x] Visual locks on future checkpoints
- [x] Month detail pages with Accept/Skip sections
- [x] AI input box with quick prompts
- [x] "Why for {petName}" explanations
- [x] Previous month recap functionality
- [x] Sample recommendations with concierge tone
- [x] Architecture supports real AI/ML replacement
- [x] All tests passing
- [x] Clean, chic UI without extraneous effects

## Future Enhancements

1. **Real AI Integration**: Replace rule-based policy with LLM
2. **Production Database**: PostgreSQL/MongoDB replacement
3. **User Authentication**: Multi-pet household support
4. **Push Notifications**: Shipping and milestone alerts
5. **Analytics Dashboard**: Journey insights and metrics
6. **Mobile App**: React Native companion
7. **E-commerce Integration**: Real product catalog

## Development Notes

- Frontend uses API rewrites (`/api/*` → `http://localhost:8000/*`)
- Backend CORS configured for frontend domain
- Test database automatically cleaned up between tests
- Responsive design works on mobile and desktop
- Accessibility features built-in (ARIA labels, keyboard navigation)

## Troubleshooting

**Backend won't start:**
- Check Python version (3.8+)
- Ensure virtual environment is activated
- Try `pip install --upgrade pip` then reinstall requirements

**Frontend build errors:**
- Clear `.next` folder: `rm -rf .next`
- Clear node_modules: `rm -rf node_modules && npm install`
- Check Node.js version (18+)

**API calls failing:**
- Verify backend is running on port 8000
- Check browser network tab for CORS errors
- Ensure rewrites are configured in next.config.ts
