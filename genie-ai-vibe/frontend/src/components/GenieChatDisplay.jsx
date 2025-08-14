import { motion, AnimatePresence } from 'framer-motion'
import { useEffect, useRef } from 'react'

const GenieChatDisplay = ({ messages, isLoading }) => {
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const messageVariants = {
    hidden: { opacity: 0, y: 15, scale: 0.98 },
    visible: { 
      opacity: 1, 
      y: 0, 
      scale: 1,
      transition: { duration: 0.25, ease: "easeOut" }
    },
    exit: { opacity: 0, scale: 0.95, transition: { duration: 0.15 } }
  }

  const LoadingIndicator = () => (
    <motion.div 
      className="genie-bubble"
      variants={messageVariants}
      initial="hidden"
      animate="visible"
      exit="exit"
      style={{ maxWidth: 'fit-content' }}
    >
      <div className="genie-loading-dots-container">
        <div className="sender-avatar mr-2">G</div>
        <span className="genie-loading-dots-text">Genie is thinking</span>
        {[0, 1, 2].map((i) => (
          <motion.div
            key={i}
            className="loading-dot"
            animate={{
              scale: [1, 1.3, 1],
              opacity: [0.6, 1, 0.6]
            }}
            transition={{
              duration: 1.2,
              repeat: Infinity,
              delay: i * 0.25
            }}
          />
        ))}
      </div>
    </motion.div>
  )

  return (
    <div className="h-full overflow-y-auto pr-2 space-y-3">
      <AnimatePresence mode="popLayout">
        {messages.map((message, index) => (
          <motion.div
            key={index}
            variants={messageVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`chat-bubble ${message.sender === 'user' ? 'user-bubble' : 'genie-bubble'}`}
            >
              {message.sender === 'genie' && (
                <div className="chat-message-sender">
                  <div className="sender-avatar">G</div>
                  <span>Genie</span>
                </div>
              )}
              
              <p className="chat-message-text">
                {message.text}
              </p>
              
              {message.sender === 'user' && (
                <div className="text-xs opacity-60 mt-1 text-right">
                  <span>You</span>
                </div>
              )}
            </div>
          </motion.div>
        ))}
        
        {isLoading && <LoadingIndicator />}
      </AnimatePresence>
      <div ref={messagesEndRef} />
    </div>
  )
}

export default GenieChatDisplay 