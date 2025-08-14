import { motion, AnimatePresence } from 'framer-motion'
import { useState, useEffect } from 'react'

const MoodSelector = ({ onMoodChange, currentMood, availableMoods }) => {
  const [isOpen, setIsOpen] = useState(false)
  const [hoveredMood, setHoveredMood] = useState(null)

  const moodEmojis = {
    'Relax': '🧘',
    'Energetic': '⚡',
    'Movie Mode': '🎬',
    'Good Morning': '🌅',
    'Focus': '🎯',
    'Sleep': '😴'
  }

  const moodDescriptions = {
    'Relax': 'Calm and peaceful ambiance',
    'Energetic': 'Bright and vibrant atmosphere',
    'Movie Mode': 'Dark and cinematic setting',
    'Good Morning': 'Warm and welcoming start',
    'Focus': 'Clean and distraction-free',
    'Sleep': 'Dim and restful environment'
  }

  const handleMoodSelect = (mood) => {
    onMoodChange(mood)
    setIsOpen(false)
  }

  return (
    <div className="relative">
      {/* Current Mood Display */}
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={() => setIsOpen(!isOpen)}
        className="mood-button px-6 py-3 rounded-xl font-medium flex items-center space-x-3 min-w-[200px] justify-between"
      >
        <div className="flex items-center space-x-3">
          <span className="text-2xl">{moodEmojis[currentMood]}</span>
          <div className="text-left">
            <div className="font-semibold">{currentMood}</div>
            <div className="text-xs opacity-70">{moodDescriptions[currentMood]}</div>
          </div>
        </div>
        <motion.svg
          animate={{ rotate: isOpen ? 180 : 0 }}
          transition={{ duration: 0.3 }}
          className="w-5 h-5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </motion.svg>
      </motion.button>

      {/* Dropdown Menu */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="absolute top-full left-0 right-0 mt-2 bg-black bg-opacity-80 backdrop-blur-lg rounded-xl border border-gray-600 overflow-hidden z-50"
          >
            <div className="p-2 space-y-1">
              {availableMoods.map((mood) => (
                <motion.button
                  key={mood}
                  whileHover={{ scale: 1.02, x: 4 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => handleMoodSelect(mood)}
                  onMouseEnter={() => setHoveredMood(mood)}
                  onMouseLeave={() => setHoveredMood(null)}
                  className={`mood-button w-full text-left flex items-center space-x-3 px-4 py-3 justify-between ${
                    mood === currentMood ? 'active' : ''
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <span className="text-xl">{moodEmojis[mood]}</span>
                    <div className="flex-1">
                      <div className="font-medium">{mood}</div>
                      <div className="text-xs opacity-70">{moodDescriptions[mood]}</div>
                    </div>
                  </div>
                  
                  {/* Selection indicator - replaced with checkmark for active state */}
                  {mood === currentMood && (
                    <motion.div
                      initial={{ scale: 0.5, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      transition={{ duration: 0.2 }}
                      className="w-5 h-5 flex items-center justify-center"
                    >
                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    </motion.div>
                  )}
                </motion.button>
              ))}
            </div>

            {/* Mood Preview */}
            <AnimatePresence>
              {hoveredMood && hoveredMood !== currentMood && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="border-t border-gray-600 p-3 bg-gray-800 bg-opacity-50"
                >
                  <div className="text-sm">
                    <div className="font-medium mb-1">Preview: {hoveredMood}</div>
                    <div className="text-xs opacity-70">
                      Click to apply this mood and change your smart home ambiance
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Backdrop to close dropdown */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  )
}

export default MoodSelector 