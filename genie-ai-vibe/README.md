# Genie - AI-Powered Smart Home Assistant

A sophisticated university demonstration project showcasing an AI-powered smart home assistant built with React, FastAPI, and Google's Gemini LLM. Features a **premium "Jarvis-like" landing page experience** with elegant widget transitions leading to a sleek, futuristic 2D dashboard with mood-based ambience control and interactive simulated smart devices.

## 🌟 Key Features

### 💫 Premium Landing Experience
- **Immersive Landing Page**: Full-screen experience with large, real-time Time and Weather widgets
- **Seamless Widget Transitions**: Smooth Framer Motion animations as widgets elegantly scale and reposition from landing to dashboard header
- **Dynamic "Genie" Title**: Character-by-character animation on landing, continuous subtle pulse in dashboard header
- **Responsive Widget Layout**: Horizontal layout on desktop, vertical stacking on mobile

### 🤖 AI-Powered Intelligence
- **Natural Language Processing**: Advanced conversation handling using Google's Gemini LLM
- **Context-Aware Responses**: Intelligent device control through everyday language
- **Real-time Communication**: Instant responses with loading states and visual feedback

### 🏠 Smart Device Simulation
- **Comprehensive Device Control**: Lights, AC, blinds, doors, music systems, security
- **Visual State Feedback**: Real-time updates reflected across the dashboard
- **Quick Scene Actions**: Pre-defined multi-device operations (Movie Mode, Good Morning, etc.)

### 🎨 Futuristic UI/UX
- **Persistent Dashboard Header**: Sticky header with compact widgets, animated title, and mood selector
- **Glassmorphism Design**: Modern layered UI with backdrop blur effects
- **Dynamic Mood-Based Theming**: UI adapts with distinct color schemes based on selected ambience
- **No-Scroll Design**: Fixed viewport with internal content scrolling for focused experience
- **Professional Animations**: Smooth transitions powered by Framer Motion throughout

### 📊 Real-time Data Widgets
- **Time Widget**: Live client-side time and date display
- **Weather Widget**: Real-time weather data via OpenWeatherMap API (temperature, conditions, humidity, wind speed)
- **Responsive States**: Loading and error handling with graceful fallbacks

## 🛠️ Tech Stack

### Backend
- **Python 3.10+** - Modern Python with type hints
- **FastAPI** - High-performance web framework with automatic API documentation
- **Google Generative AI** - Gemini LLM integration for natural language processing
- **Uvicorn** - Lightning-fast ASGI server
- **SQLite** - Lightweight database for device states and configurations
- **Python-dotenv** - Secure environment variable management

### Frontend
- **React 18** - Modern UI library with hooks and functional components
- **Vite** - Ultra-fast build tool and development server
- **Tailwind CSS** - Utility-first CSS framework with extensive custom theming
- **Framer Motion** - Advanced animations and layout transitions
- **Inter Font** - Clean, modern typography

## 📁 Project Structure

```
genie-ai-vibe/
├── backend/                  # FastAPI application
│   ├── main.py              # Application entry point
│   ├── config.py            # Configuration management
│   ├── api/                 # API route handlers
│   │   ├── chat.py         # Chat and AI interaction endpoints
│   │   ├── devices.py      # Device control endpoints
│   │   └── moods.py        # Mood and theming endpoints
│   ├── core/               # Core business logic
│   │   ├── agent_controller.py    # Gemini LLM integration
│   │   ├── device_simulator.py   # Smart device simulation
│   │   └── mood_engine.py        # Dynamic theming engine
│   ├── db/                 # Database management
│   │   └── db_handler.py   # SQLite operations
│   └── genie.db           # SQLite database file
├── frontend/               # React application
│   ├── src/
│   │   ├── App.jsx        # Main app component with state management
│   │   ├── main.jsx       # React entry point
│   │   ├── components/    # Reusable UI components
│   │   │   ├── TimeWidget.jsx      # Live time display
│   │   │   ├── WeatherWidget.jsx   # Weather data widget
│   │   │   ├── GenieChatDisplay.jsx # Chat interface
│   │   │   ├── VoiceInputArea.jsx  # Input and controls
│   │   │   ├── DeviceCard.jsx      # Smart device controls
│   │   │   └── MoodSelector.jsx    # Theme selector
│   │   ├── styles/
│   │   │   └── index.css   # Global styles with CSS variables
│   │   └── assets/         # Static assets
│   ├── public/             # Public assets
│   ├── package.json        # Dependencies and scripts
│   └── tailwind.config.js  # Tailwind configuration
├── .env                    # Environment variables (create this)
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── PROJECT_DETAILS.md     # Comprehensive project documentation
```

## 🚀 Quick Start

### Prerequisites

- **Node.js 18+** and **npm**
- **Python 3.10+** and **pip**
- **Google Gemini API Key** - Get it from [Google AI Studio](https://makersuite.google.com/app/apikey)
- **OpenWeatherMap API Key** - Get a free key from [OpenWeatherMap](https://openweathermap.org/appid)

### 1. Environment Setup

```bash
# Navigate to project directory
cd genie-ai-vibe

# Create environment file
cp .env.example .env  # or create .env manually

# Add your API keys to .env
```

**Create `.env` file with:**
```env
# Backend API Keys
GEMINI_API_KEY=your_actual_gemini_api_key_here
OPENWEATHERMAP_API_KEY=your_actual_openweathermap_api_key_here

# Optional: Backend configuration
HOST=localhost
PORT=8000
```

**⚠️ Important**: You also need to add your OpenWeatherMap API key directly in `frontend/src/components/WeatherWidget.jsx` at line ~8:
```javascript
const API_KEY = 'your_actual_openweathermap_api_key_here';
```

### 2. Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Navigate to backend directory
cd backend

# Start the FastAPI server
python main.py
```
✅ Backend running at `http://localhost:8000`

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Start the development server
npm run dev
```
✅ Frontend running at `http://localhost:5173`

### 4. Access the Application

1. Open your browser to `http://localhost:5173`
2. Experience the premium landing page with live widgets
3. Click "Enter Smart Dashboard" to access the main interface
4. Start chatting with Genie!

## 🎯 Usage Examples

### Natural Language Commands
```
"Turn on the living room lights"
"Set the temperature to 72 degrees"  
"Play some relaxing music"
"Lock all the doors"
"Switch to movie mode"
"What's the weather like?"
"Good morning" (activates morning scene)
```

### Mood-Based Themes
- **Relax**: Calm blues and greens with dimmed lighting
- **Energetic**: Vibrant oranges and yellows with bright lighting  
- **Movie Mode**: Dark theme with ambient lighting
- **Focus**: Clean whites and blues for productivity

## 🎨 UI/UX Highlights

### Landing Page Experience
- **Full-screen immersive design** with focus on Time and Weather widgets
- **Smooth entry transition** into the main dashboard
- **Responsive layout** adapting to different screen sizes

### Dashboard Features
- **Persistent header** with compact widgets and controls
- **Glassmorphism effects** with backdrop blur and subtle borders
- **Dynamic theming** that instantly adapts colors across the entire interface
- **Smooth animations** for all interactions and state changes

### Professional Polish
- **Consistent design language** across all components
- **Loading states** and error handling throughout
- **Accessibility considerations** with proper contrast and focus states
- **Mobile-optimized** responsive design

## 🔧 Development

### Backend Development
```bash
cd backend

# Run with auto-reload for development
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Access API documentation
# http://localhost:8000/docs (Swagger UI)
# http://localhost:8000/redoc (ReDoc)
```

### Frontend Development
```bash
cd frontend

# Development server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

## 🌐 API Endpoints

### Main Endpoints

#### `POST /api/talk`
Send messages to Genie for AI-powered responses and device control.

**Request:**
```json
{
  "message": "Turn on the bedroom lights"
}
```

**Response:**
```json
{
  "response": "I've turned on the bedroom lights for you.",
  "device_changes": {
    "devices_updated": {
      "light_bedroom": {
        "id": "light_bedroom",
        "name": "Bedroom Light", 
        "type": "light",
        "state": "on",
        "brightness": 100,
        "color": "#FFFFFF"
      }
    },
    "scene_applied": null,
    "mood_changed": null
  }
}
```

#### `GET /api/devices`
Retrieve current state of all smart devices.

#### `POST /api/device/update`
Manually update device state.

#### `GET /api/moods`
Get available mood themes.

#### `POST /api/mood/set`
Apply a new mood theme.

## 🎭 Customization

### Theming
- **Dynamic CSS Variables**: Modify colors via the mood engine in `backend/core/mood_engine.py`
- **Custom Moods**: Add new themes by extending the mood definitions
- **Component Styles**: Update global styles in `frontend/src/styles/index.css`

### Adding New Devices
1. Update device definitions in `backend/core/device_simulator.py`
2. Add UI components in `frontend/src/components/`
3. Update the AI prompt context for device recognition

### Extending AI Capabilities
- Modify prompts in `backend/core/agent_controller.py`
- Add new command patterns and responses
- Extend device control logic

## 🚧 Future Enhancements

- [ ] **Voice Input**: Web Speech API integration for hands-free control
- [ ] **User Accounts**: Personal device configurations and preferences
- [ ] **Complex Automations**: Time-based and condition-triggered device actions
- [ ] **Device Discovery**: Dynamic addition of new smart devices
- [ ] **Weather Location**: User-configurable location for weather data
- [ ] **Mobile App**: Native mobile application with push notifications
- [ ] **Energy Monitoring**: Track and visualize device energy consumption
- [ ] **Scene Scheduling**: Time-based automatic scene activation

## 🐛 Troubleshooting

### Common Issues

**Backend won't start:**
- Verify Python 3.10+ is installed
- Check that all dependencies are installed: `pip install -r requirements.txt`
- Ensure API keys are correctly set in `.env`

**Frontend shows no weather data:**
- Verify OpenWeatherMap API key is added to both `.env` and `WeatherWidget.jsx`
- Check browser console for API errors
- Ensure backend is running and accessible

**Widgets not transitioning properly:**
- Clear browser cache and restart development server
- Check for JavaScript errors in browser console
- Verify Framer Motion is installed: `npm list framer-motion`

### Getting Help
- Check the browser developer console for error messages
- Verify both backend (port 8000) and frontend (port 5173) are running
- Ensure all environment variables are properly configured

---

**🎓 Academic Project Notice**: This project is developed for educational and demonstration purposes, showcasing modern full-stack development techniques, AI integration, and advanced UI/UX design principles.

**⭐ If you find this project helpful, please consider giving it a star!** 