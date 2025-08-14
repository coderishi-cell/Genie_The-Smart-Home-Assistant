import { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'

const VoiceInputArea = ({ onSendMessage, isLoading }) => {
  const [inputMessage, setInputMessage] = useState('')
  const [isListening, setIsListening] = useState(false)
  const [speechSupported, setSpeechSupported] = useState(false)
  const recognitionRef = useRef(null)

  // Check if speech recognition is supported
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      setSpeechSupported(true)
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
      recognitionRef.current = new SpeechRecognition()
      
      // Configure speech recognition
      recognitionRef.current.continuous = true
      recognitionRef.current.interimResults = true
      recognitionRef.current.lang = 'en-US'

      // Handle speech recognition results
      recognitionRef.current.onresult = (event) => {
        let transcript = ''
        for (let i = event.resultIndex; i < event.results.length; i++) {
          if (event.results[i].isFinal) {
            transcript += event.results[i][0].transcript
          }
        }
        if (transcript) {
          setInputMessage(prev => prev + transcript)
        }
      }

      // Handle speech recognition errors
      recognitionRef.current.onerror = (event) => {
        console.error('Speech recognition error:', event.error)
        setIsListening(false)
        if (event.error === 'not-allowed') {
          alert('Microphone access denied. Please enable microphone permissions and try again.')
        }
      }

      // Handle speech recognition end
      recognitionRef.current.onend = () => {
        setIsListening(false)
      }
    }

    // Cleanup
    return () => {
      if (recognitionRef.current && isListening) {
        recognitionRef.current.stop()
      }
    }
  }, [])

  const handleVoiceToggle = () => {
    if (!speechSupported) {
      alert('Speech recognition is not supported in your browser. Please try using Chrome or Edge.')
      return
    }

    if (isListening) {
      recognitionRef.current.stop()
      setIsListening(false)
    } else {
      try {
        recognitionRef.current.start()
        setIsListening(true)
      } catch (error) {
        console.error('Error starting speech recognition:', error)
        alert('Could not start voice recognition. Please check your microphone permissions.')
      }
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (inputMessage.trim() && !isLoading) {
      onSendMessage(inputMessage)
      setInputMessage('')
      // Stop listening if still active
      if (isListening) {
        recognitionRef.current.stop()
        setIsListening(false)
      }
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  // Auto-resize textarea
  const handleTextareaInput = (e) => {
    setInputMessage(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${e.target.scrollHeight}px`;
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="chat-input-container"
    >
      <form onSubmit={handleSubmit} className="chat-input-form">
        {/* Voice Button */}
        <motion.button
          type="button"
          whileHover={{ scale: speechSupported ? 1.05 : 1 }}
          whileTap={{ scale: speechSupported ? 0.95 : 1 }}
          onClick={handleVoiceToggle}
          disabled={!speechSupported || isLoading}
          className={`chat-icon-button ${isListening ? 'voice-button-active' : 'voice-button-placeholder'}`}
          title={
            !speechSupported 
              ? 'Voice input not supported in this browser' 
              : isListening 
                ? 'Stop listening (Click or press Enter to send)' 
                : 'Start voice input'
          }
        >
          {isListening ? (
            <motion.svg
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ duration: 1, repeat: Infinity }}
              className="w-5 h-5"
              fill="currentColor" 
              viewBox="0 0 20 20"
            >
              <path 
                fillRule="evenodd" 
                d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" 
                clipRule="evenodd" 
              />
            </motion.svg>
          ) : (
            <svg 
              className="w-5 h-5"
              fill="currentColor" 
              viewBox="0 0 20 20"
            >
              <path 
                fillRule="evenodd" 
                d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" 
                clipRule="evenodd" 
              />
            </svg>
          )}
        </motion.button>

        {/* Text Input */}
        <div className="chat-input-wrapper">
          <textarea
            value={inputMessage}
            onChange={handleTextareaInput}
            onKeyPress={handleKeyPress}
            placeholder={isListening ? "Listening... Speak now!" : "Ask Genie"}
            className="chat-input-textarea"
            rows="1"
            disabled={isLoading}
          />
          
          {/* Listening indicator */}
          {isListening && (
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              className="absolute top-2 right-2 flex items-center space-x-1 text-xs text-red-400 bg-black bg-opacity-50 px-2 py-1 rounded-full"
            >
              <motion.div
                animate={{ scale: [1, 1.5, 1] }}
                transition={{ duration: 1, repeat: Infinity }}
                className="w-2 h-2 bg-red-400 rounded-full"
              />
              <span>Recording</span>
            </motion.div>
          )}
          
          {/* Character count or status indicator */}
          {inputMessage.length > 400 && !isListening && (
            <div className={`absolute bottom-1 right-2 text-xs ${inputMessage.length > 500 ? 'text-red-400' : 'text-gray-500'}`}>
              {inputMessage.length}/500
            </div>
          )}
        </div>

        {/* Send Button */}
        <motion.button
          type="submit"
          disabled={!inputMessage.trim() || isLoading}
          whileHover={{ scale: inputMessage.trim() && !isLoading ? 1.05 : 1 }}
          whileTap={{ scale: inputMessage.trim() && !isLoading ? 0.95 : 1 }}
          className="chat-icon-button chat-send-button"
          title={isLoading ? 'Sending...' : 'Send message'}
        >
          {isLoading ? (
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 0.7, repeat: Infinity, ease: "linear" }}
              className="w-5 h-5 border-2 border-[var(--bgColorPrimary)] border-t-transparent rounded-full"
            />
          ) : (
            <svg 
              className="w-5 h-5"
              fill="currentColor" 
              viewBox="0 0 20 20"
            >
              <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
            </svg>
          )}
        </motion.button>
      </form>

      {/* Quick Actions */}
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.15 }}
        className="quick-action-buttons-container"
      >
        {[
          "Turn on all lights",
          "Set AC to 22°C", 
          "Play relaxing music",
          "Goodnight routine"
        ].map((suggestion, index) => (
          <motion.button
            key={index}
            whileHover={{ scale: 1.02, y: -1 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => !isLoading && onSendMessage(suggestion)}
            disabled={isLoading}
            className="quick-action-button"
          >
            {suggestion}
          </motion.button>
        ))}
      </motion.div>
    </motion.div>
  )
}

export default VoiceInputArea 