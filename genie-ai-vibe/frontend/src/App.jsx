import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import GenieChatDisplay from './components/GenieChatDisplay'
import VoiceInputArea from './components/VoiceInputArea'
import DeviceCard from './components/DeviceCard'
import MoodSelector from './components/MoodSelector'
import TimeWidget from './components/TimeWidget'
import WeatherWidget from './components/WeatherWidget'
import ProactiveIntelligenceWidget from './components/ProactiveIntelligenceWidget'
import FaceRecognition from './components/FaceRecognition'

function App() {
  const [messages, setMessages] = useState([
    {
      text: "Hello! I'm Genie, your AI-powered smart home assistant. How can I help you control your smart devices today?",
      sender: 'genie'
    }
  ])
  const [isLoading, setIsLoading] = useState(false)
  const [deviceStates, setDeviceStates] = useState({})
  const [lastUpdate, setLastUpdate] = useState(Date.now())
  const [currentThemeVars, setCurrentThemeVars] = useState({
    bgGradientStart: '#0D1B2A',
    bgGradientEnd: '#003F5C',
    accentColor: '#00E5FF',
    accentColorRGB: '0, 229, 255',
    textColorPrimary: '#F8F8FF',
    textColorPrimaryRGB: '248, 248, 255',
    cardBgColor: 'rgba(23, 37, 59, 0.5)',
    glowColor: '#00E5FF',
    bgColorPrimary: '#0D1B2A',
  })
  const [currentMood, setCurrentMood] = useState('Relax')
  const [availableMoods, setAvailableMoods] = useState([])
  const [isInitializing, setIsInitializing] = useState(true)
  const [showDashboard, setShowDashboard] = useState(false)
  const [activeTab, setActiveTab] = useState('dashboard')

  // Initialize app data
  useEffect(() => {
    const initializeApp = async () => {
      try {
        // Load device states
        const devicesResponse = await fetch('http://localhost:8000/api/devices')
        if (devicesResponse.ok) {
          const devicesData = await devicesResponse.json()
          console.log('Initial device states loaded:', devicesData.devices)
          setDeviceStates(devicesData.devices)
        } else {
          console.error('Failed to load device states:', devicesResponse.status)
        }

        // Load available moods and current mood
        const moodsResponse = await fetch('http://localhost:8000/api/moods')
        if (moodsResponse.ok) {
          const moodsData = await moodsResponse.json()
          setAvailableMoods(moodsData.moods)
          setCurrentMood(moodsData.current_mood)
        }

        // Load current theme
        const currentMoodResponse = await fetch('http://localhost:8000/api/mood/current')
        if (currentMoodResponse.ok) {
          const currentMoodData = await currentMoodResponse.json()
          setCurrentThemeVars(currentMoodData.theme_vars)
        }
      } catch (error) {
        console.error('Error initializing app:', error)
      } finally {
        setIsInitializing(false)
      }
    }

    initializeApp()
  }, [])

  // Apply theme variables to CSS
  useEffect(() => {
    const root = document.documentElement
    Object.entries(currentThemeVars).forEach(([key, value]) => {
      root.style.setProperty(`--${key}`, value)
    })
  }, [currentThemeVars])

  const handleSendMessage = async (userMessage) => {
    if (!userMessage.trim()) return

    // Add user message immediately
    const newUserMessage = { text: userMessage, sender: 'user' }
    setMessages(prev => [...prev, newUserMessage])
    setIsLoading(true)

    try {
      // Make API call to backend
      const response = await fetch('http://localhost:8000/api/talk', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: userMessage }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      
      // Debug: Log the full response
      console.log('API Response:', data)
      
      // Handle device changes if any
      if (data.device_changes) {
        console.log('Device changes detected:', data.device_changes)
        const { devices_updated, scene_applied, mood_changed } = data.device_changes
        
        // Update device states
        if (devices_updated && Object.keys(devices_updated).length > 0) {
          console.log('Updating device states:', devices_updated)
          setDeviceStates(prev => {
            const newStates = { ...prev }
            // Update each device individually to ensure React detects changes
            Object.entries(devices_updated).forEach(([deviceId, deviceState]) => {
              newStates[deviceId] = { ...deviceState }
            })
            console.log('Previous device states:', prev)
            console.log('New device states:', newStates)
            return newStates
          })
          // Force re-render by updating timestamp
          setLastUpdate(Date.now())
        }
        
        // Update mood and theme if changed
        if (mood_changed) {
          console.log('Updating mood:', mood_changed)
          setCurrentMood(mood_changed.mood_name)
          setCurrentThemeVars(mood_changed.theme_vars)
        }
      } else {
        console.log('No device changes in response')
      }
      
      // Add Genie's response
      const genieMessage = { text: data.response, sender: 'genie' }
      setMessages(prev => [...prev, genieMessage])
      
    } catch (error) {
      console.error('Error communicating with Genie:', error)
      const errorMessage = { 
        text: "I'm sorry, I'm having trouble connecting right now. Please make sure the backend server is running and try again.", 
        sender: 'genie' 
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleDeviceUpdate = async (deviceId, updates) => {
    try {
      const response = await fetch('http://localhost:8000/api/device/update', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ device_id: deviceId, updates }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      
      // Update device state
      setDeviceStates(prev => ({
        ...prev,
        [deviceId]: data.state
      }))

      // Add a message about the device update
      const updateMessage = {
        text: `Updated ${data.state.name}: ${Object.entries(updates).map(([key, value]) => `${key} set to ${value}`).join(', ')}`,
        sender: 'genie'
      }
      setMessages(prev => [...prev, updateMessage])
      
    } catch (error) {
      console.error('Error updating device:', error)
    }
  }

  const handleSceneChange = async (sceneName) => {
    try {
      const response = await fetch('http://localhost:8000/api/device/scene', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ scene_name: sceneName }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      
      // Update all device states
      setDeviceStates(data.devices)

      // Add a message about the scene change
      const sceneMessage = {
        text: `Applied "${sceneName}" scene to your smart home devices.`,
        sender: 'genie'
      }
      setMessages(prev => [...prev, sceneMessage])
      
    } catch (error) {
      console.error('Error applying scene:', error)
    }
  }

  const handleMoodChange = async (moodName) => {
    try {
      const response = await fetch('http://localhost:8000/api/mood/set', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ mood_name: moodName }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      
      // Update theme and device states
      setCurrentThemeVars(data.theme_vars)
      setDeviceStates(data.device_states)
      setCurrentMood(moodName)

      // Add a message about the mood change
      const moodMessage = {
        text: `Mood changed to "${moodName}". Your smart home ambiance has been updated!`,
        sender: 'genie'
      }
      setMessages(prev => [...prev, moodMessage])
      
    } catch (error) {
      console.error('Error changing mood:', error)
    }
  }

  if (isInitializing) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center"
        >
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full mx-auto mb-4"
          />
          <p className="text-xl font-medium">Initializing Genie...</p>
          <p className="text-sm opacity-70 mt-2">Setting up your smart home dashboard</p>
        </motion.div>
      </div>
    )
  }

  return (
    <div className={`app-container min-h-screen font-futuristic transition-colors duration-1000 flex flex-col ${showDashboard ? 'dashboard-active' : 'landing-active'}`}>
      {/* Header / Status Bar - Structure changes based on showDashboard */}
      <motion.header 
        layout 
        transition={{ duration: 0.8, ease: [0.25, 0.46, 0.45, 0.94] }}
        className={`app-header glass-effect ${showDashboard ? 'dashboard-header' : 'landing-header'}`}
      >
        <div className={`header-content-wrapper ${showDashboard ? 'dashboard-header-content' : 'landing-header-content'}`}>
          {/* Dashboard: Widgets on left corner */}
          {showDashboard && (
            <motion.div 
              layout 
              initial={{ opacity: 0, x: -30 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8, ease: [0.25, 0.46, 0.45, 0.94], delay: 0.2 }}
              className="dashboard-widgets-left"
            >
              <motion.div layout className="widget-wrapper time-widget-wrapper"><TimeWidget /></motion.div>
              <motion.div layout className="widget-wrapper weather-widget-wrapper"><WeatherWidget /></motion.div>
            </motion.div>
          )}
          
          {/* Genie Title - different presentation based on view */}
          <motion.div layout className={`genie-title-container ${showDashboard ? 'dashboard-genie-title' : 'landing-genie-title'}`}>
            <h1 className="text-6xl sm:text-7xl md:text-8xl font-bold tracking-tight">
              {"GENIE".split("").map((char, index) => (
                <motion.span
                  key={index}
                  initial={{ opacity: 0, y: showDashboard ? 0: 30 }}
                  animate={{
                    opacity: showDashboard ? [1, 0.7, 1] : 1,
                    y: 0,
                    letterSpacing: showDashboard ? ["0.05em", "0.1em", "0.05em"] : "0.05em",
                    textShadow: showDashboard ? [
                      "0 0 10px rgba(var(--accentColorRGB), 0.3)",
                      "0 0 20px rgba(var(--accentColorRGB), 0.6)",
                      "0 0 10px rgba(var(--accentColorRGB), 0.3)"
                    ] : "0 0 10px rgba(var(--accentColorRGB), 0.3)",
                  }}
                  transition={{
                    type: 'spring', stiffness: 100, damping:10, delay: (showDashboard ? 0.3 : 0.3) + index * 0.08,
                    ...(showDashboard && {
                      opacity: {
                        duration: 3,
                        repeat: Infinity,
                        repeatType: "mirror",
                        delay: index * 0.2,
                        ease: "easeInOut"
                      },
                      letterSpacing: {
                        duration: 4,
                        repeat: Infinity,
                        repeatType: "mirror",
                        delay: index * 0.15,
                        ease: "easeInOut"
                      },
                      textShadow: {
                        duration: 2.5,
                        repeat: Infinity,
                        repeatType: "mirror",
                        delay: index * 0.25,
                        ease: "easeInOut"
                      }
                    })
                  }}
                  className="bg-gradient-to-br from-[var(--accentColor)] via-sky-400 to-blue-500 bg-clip-text text-transparent inline-block mr-[-0.05em]"
                >
                  {char}
                </motion.span>
              ))}
            </h1>
            <AnimatePresence>
              {!showDashboard && (
                <motion.p 
                  initial={{opacity:0, y:10}} animate={{opacity:1, y:0}} exit={{opacity:0, y:-10}}
                  transition={{ duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] }}
                  className="text-lg md:text-xl opacity-70 mt-3 tracking-wide">
                  Your Personal Smart Home AI
                </motion.p>
              )}
            </AnimatePresence>
          </motion.div>

          {/* Landing: Widgets Container - only on landing page */}
          {!showDashboard && (
            <motion.div 
              className="landing-main-content"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.8, ease: [0.25, 0.46, 0.45, 0.94], delay: 0.4 }}
            >
              {/* Time and Weather Widgets */}
              <motion.div 
                layout 
                initial={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                transition={{ duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] }}
                className="landing-widgets"
              >
                <motion.div layout className="widget-wrapper time-widget-wrapper"><TimeWidget /></motion.div>
                <motion.div layout className="widget-wrapper weather-widget-wrapper"><WeatherWidget /></motion.div>
              </motion.div>
            </motion.div>
          )}
          
          {/* Dashboard: Tab Navigation and Mood Selector */}
          {showDashboard && (
            <div className="flex items-center gap-6">
              {/* Tab Navigation */}
              <motion.div 
                layout 
                initial={{ opacity: 0, x: -30 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.8, ease: [0.25, 0.46, 0.45, 0.94], delay: 0.4 }}
                className="flex gap-2"
              >
                <button
                  onClick={() => setActiveTab('dashboard')}
                  className={`px-4 py-2 rounded-lg font-medium transition-all ${
                    activeTab === 'dashboard' 
                      ? 'bg-[var(--accentColor)] text-white shadow-lg' 
                      : 'bg-white/10 text-white/70 hover:bg-white/20'
                  }`}
                >
                  🏠 Dashboard
                </button>
                <button
                  onClick={() => setActiveTab('face-recognition')}
                  className={`px-4 py-2 rounded-lg font-medium transition-all ${
                    activeTab === 'face-recognition' 
                      ? 'bg-[var(--accentColor)] text-white shadow-lg' 
                      : 'bg-white/10 text-white/70 hover:bg-white/20'
                  }`}
                >
                  🔍 Face Recognition
                </button>
              </motion.div>
              
              {/* Mood Selector - only show on dashboard tab */}
              {activeTab === 'dashboard' && (
                <motion.div 
                  layout 
                  initial={{ opacity: 0, x: 30 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.8, ease: [0.25, 0.46, 0.45, 0.94], delay: 0.4 }}
                  className="mood-selector-dashboard-header"
                >
                  <MoodSelector
                    currentMood={currentMood}
                    availableMoods={availableMoods}
                    onMoodChange={handleMoodChange}
                  />
                </motion.div>
              )}
            </div>
          )}

          {/* "Enter Smart Dashboard" Button - Now part of landing-header-content */}
          {!showDashboard && (
            <motion.button
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.8, delay: 0.9, ease: [0.25, 0.46, 0.45, 0.94] }}
              onClick={() => setShowDashboard(true)}
              className="landing-dashboard-button"
            >
              Enter Smart Dashboard
            </motion.button>
          )}
        </div>
      </motion.header>

      {/* Main Content Area */}
      <div className="main-content-area flex-grow flex flex-col">
        <AnimatePresence mode="wait">
          {!showDashboard ? (
            <motion.section
              key="landing-content"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20, scale: 0.98 }}
              transition={{ duration: 0.8, ease: [0.25, 0.46, 0.45, 0.94], delay: 0.2 }}
              className="landing-page-content flex-grow flex flex-col items-center justify-center text-center p-4"
            >
              {/* Content here is removed as button moved to header */}
            </motion.section>
          ) : (
            <motion.div
              key="dashboard-content"
              initial={{ opacity: 0, y: 40, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -40, scale: 0.98 }}
              transition={{ duration: 0.9, ease: [0.25, 0.46, 0.45, 0.94], delay: 0.3 }}
              className="dashboard-main-content flex-grow"
            >
              {/* Tab Content */}
              <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <AnimatePresence mode="wait">
                  {activeTab === 'dashboard' && (
                    <motion.div
                      key="dashboard-tab"
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -20 }}
                      transition={{ duration: 0.5 }}
                    >
                      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                        <motion.div 
                          initial={{ opacity: 0, x: -40 }} 
                          animate={{ opacity: 1, x: 0 }} 
                          transition={{ delay: 0.5, duration: 0.8, ease: [0.25, 0.46, 0.45, 0.94] }}
                          className="lg:col-span-2 content-panel"
                        >
                          <h2 className="text-2xl font-bold mb-6 flex items-center"><span className="mr-3 text-2xl">🏠</span>Smart Devices</h2>
                          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                            {Object.entries(deviceStates).map(([deviceId, deviceState]) => (
                              <DeviceCard
                                key={`${deviceId}-${lastUpdate}`}
                                deviceId={deviceId}
                                deviceState={deviceState}
                                onUpdate={handleDeviceUpdate}
                              />
                            ))}
                          </div>
                        </motion.div>

                        <motion.div 
                          initial={{ opacity: 0, x: 40 }} 
                          animate={{ opacity: 1, x: 0 }} 
                          transition={{ delay: 0.6, duration: 0.8, ease: [0.25, 0.46, 0.45, 0.94] }}
                          className="lg:col-span-1 content-panel"
                        >
                          <h2 className="text-2xl font-bold mb-6 flex items-center"><span className="mr-3 text-2xl">💬</span>Chat with Genie</h2>
                          <div className="glass-effect rounded-2xl p-1 h-[600px] flex flex-col">
                            <div className="flex-1 mb-4 p-3 bg-[rgba(0,0,0,0.1)] rounded-lg overflow-y-auto">
                              <GenieChatDisplay messages={messages} isLoading={isLoading} />
                            </div>
                            <div className="p-3"><VoiceInputArea onSendMessage={handleSendMessage} isLoading={isLoading} /></div>
                          </div>
                        </motion.div>
                      </div>
                      <motion.div
                        initial={{ opacity: 0, y: 40 }} 
                        animate={{ opacity: 1, y: 0 }} 
                        transition={{ delay: 0.7, duration: 0.8, ease: [0.25, 0.46, 0.45, 0.94] }}
                        className="mt-10 content-panel"
                      >
                        <h2 className="text-2xl font-bold mb-6 flex items-center"><span className="mr-3 text-2xl">🎬</span>Quick Scenes</h2>
                        <div className="flex flex-wrap gap-4">
                          {['Movie Mode', 'Good Morning', 'Focus', 'Sleep'].map((scene) => (
                            <motion.button
                              key={scene}
                              whileHover={{ scale: 1.05, y: -1 }}
                              whileTap={{ scale: 0.95 }}
                              onClick={() => handleSceneChange(scene)}
                              className="mood-button"
                            >
                              {scene}
                            </motion.button>
                          ))}
                        </div>
                      </motion.div>
                      <motion.div
                        initial={{ opacity: 0, y: 40 }} 
                        animate={{ opacity: 1, y: 0 }} 
                        transition={{ delay: 0.8, duration: 0.8, ease: [0.25, 0.46, 0.45, 0.94] }}
                        className="mt-10 content-panel"
                      >
                        <ProactiveIntelligenceWidget />
                      </motion.div>
                    </motion.div>
                  )}

                  {activeTab === 'face-recognition' && (
                    <motion.div
                      key="face-recognition-tab"
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -20 }}
                      transition={{ duration: 0.5 }}
                    >
                      <FaceRecognition />
                    </motion.div>
                  )}
                </AnimatePresence>
              </main>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <motion.footer layout className="text-center py-6 text-sm opacity-70 mt-auto">
        <p>GENIE: Generative Entity for Nurturing Interactive ELements</p>
      </motion.footer>
    </div>
  )
}

export default App 