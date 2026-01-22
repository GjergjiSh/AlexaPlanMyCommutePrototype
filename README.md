# VVS Commute Planner

AI-powered commute planner that analyzes Stuttgart VVS trip data and provides voice-friendly recommendations using Google's Gemini API.

- Calls VVS API to get trip data between two stations for your work commute
- Uses Gemini API to summarize trip data into a concise response and suggest best route
- Deployed as a Vercel serverless function

## Features

- Real-time trip data fetching from VVS
- AI-powered route recommendations
- Delay and service alert detection
- Multiple departure time analysis

## Prerequisites

- Python 3.9+
- Vercel account
- Google Gemini API key

## Setup & Deployment

### 1. Install Vercel CLI

```bash
npm install -g vercel
```

### 2. Set Up Environment Variables

Create a `.env.local` file locally:
```
GEMINI_API_KEY=your_api_key_here
```

### 3. Test Locally

```bash
vercel dev
```

The API will be available at `http://localhost:3000/api`

### 4. Deploy to Vercel

```bash
vercel --prod
```

### 5. Add Environment Variables to Vercel

In your Vercel project dashboard:
- Go to Settings → Environment Variables
- Add `GEMINI_API_KEY` with your API key

## API Usage

### GET /api

Returns commute data and AI-generated recommendation.

**Response:**
```json
{
  "trip_data": "...",
  "recommendation": "Recommendation text"
}
```

## Project Structure

```
vvs-api/
├── api/
│   └── index.py          # Serverless function handler
├── vercel.json           # Vercel configuration
├── package.json          # Node.js metadata
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Technology Stack

- **Python 3.9** - Backend runtime
- **Vercel** - Deployment & hosting
- **vvspy** - Stuttgart VVS API client
- **Google Gemini API** - AI recommendations
- **python-dotenv** - Environment configuration

## Notes

- Execution time: ~30 seconds (trip analysis + AI generation)
- Maximum duration: 30 seconds (Vercel limit)
- Memory: 3GB allocated
- CORS enabled for API access