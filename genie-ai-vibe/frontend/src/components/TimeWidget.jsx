import { motion } from 'framer-motion';
import { useState, useEffect } from 'react';

const TimeWidget = () => {
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timerId = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timerId);
  }, []);

  const formatDate = (date) => {
    return date.toLocaleDateString(undefined, {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const formatTime = (date) => {
    return date.toLocaleTimeString(undefined, {
      hour: '2-digit',
      minute: '2-digit',
      // second: '2-digit', // Optional: include seconds
      hour12: true, 
    });
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, delay: 0.1 }}
      className="time-widget-container glass-effect content-panel"
    >
      <div className="time-display">{formatTime(currentTime)}</div>
      <div className="date-display">{formatDate(currentTime)}</div>
    </motion.div>
  );
};

export default TimeWidget; 