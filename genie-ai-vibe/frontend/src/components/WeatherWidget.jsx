import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

const API_KEY = 'd74bcc220de466c388696f75f8a8d449'; // Your OpenWeatherMap API Key
const CITY_ID = '1275004'; // Kolkata City ID

const WeatherWidget = () => {
  const [weatherData, setWeatherData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Function to map OpenWeatherMap icons to more visually appealing ones (example)
  // You might want to use a proper icon library or SVG set for a premium look.
  const getWeatherIcon = (iconCode) => {
    const iconMapping = {
      '01d': '☀️', // clear sky day
      '01n': '🌙', // clear sky night
      '02d': '⛅', // few clouds day
      '02n': '☁️', // few clouds night (using generic cloud)
      '03d': '☁️', // scattered clouds day
      '03n': '☁️', // scattered clouds night
      '04d': '🌥️', // broken clouds day
      '04n': '☁️', // broken clouds night (using generic cloud)
      '09d': '🌦️', // shower rain day
      '09n': '🌧️', // shower rain night (using generic rain)
      '10d': '🌧️', // rain day
      '10n': '🌧️', // rain night
      '11d': '⛈️', // thunderstorm day
      '11n': '⛈️', // thunderstorm night
      '13d': '❄️', // snow day
      '13n': '❄️', // snow night
      '50d': '🌫️', // mist day
      '50n': '🌫️', // mist night
    };
    return iconMapping[iconCode] || '❓'; // Default icon if no match
  };

  const formatWeatherData = (apiData) => {
    if (!apiData) return null;
    return {
      location: apiData.name || 'Unknown Location',
      temperature: Math.round(apiData.main?.temp),
      condition: apiData.weather?.[0]?.main || 'N/A',
      description: apiData.weather?.[0]?.description || 'No description available.',
      icon: getWeatherIcon(apiData.weather?.[0]?.icon),
      humidity: apiData.main?.humidity,
      windSpeed: Math.round(apiData.wind?.speed * 3.6), // m/s to km/h
      feelsLike: Math.round(apiData.main?.feels_like),
    };
  };

  useEffect(() => {
    const fetchWeatherDataByCityID = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(
          `https://api.openweathermap.org/data/2.5/weather?id=${CITY_ID}&appid=${API_KEY}&units=metric`
        );
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.message || `HTTP error! status: ${response.status} - ${response.statusText}`);
        }
        const data = await response.json();
        setWeatherData(formatWeatherData(data));
      } catch (err) {
        console.error("Failed to fetch weather data:", err);
        setError(err.message || 'Could not fetch weather data.');
        setWeatherData(formatWeatherData({ // Provide some default structure on error
          name: 'Error',
          main: {temp: '--', humidity: '--', feels_like: '--'},
          weather: [{main: 'N/A', description: err.message, icon: '01d'}],
          wind: {speed: 0}
        }));
      } finally {
        setLoading(false);
      }
    };

    fetchWeatherDataByCityID();

    const intervalId = setInterval(fetchWeatherDataByCityID, 30 * 60 * 1000); // every 30 mins
    return () => clearInterval(intervalId);

  }, []); // Empty dependency array means this runs once on mount and sets up the interval

  if (loading && !weatherData) {
    return (
      <motion.div
        className="weather-widget-container glass-effect content-panel flex items-center justify-center"
        initial={{ opacity: 0 }} animate={{ opacity: 1 }}
      >
        <div className="text-center">
          <div className="w-10 h-10 border-2 border-[var(--accentColor)] border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
          <p className="text-lg opacity-80">Fetching Weather for Kolkata...</p>
        </div>
      </motion.div>
    );
  }

  if (!weatherData) { 
    return (
        <motion.div className="weather-widget-container glass-effect content-panel text-center">
            <p>Weather data is currently unavailable.</p>
            {error && <p className="text-sm text-red-400 mt-2">Error: {error}</p>}
        </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, delay: 0.2 }}
      className="weather-widget-container glass-effect content-panel"
    >
      {loading && (
          <div className="absolute top-3 right-3 w-5 h-5 border-2 border-[var(--accentColor)] border-t-transparent rounded-full animate-spin z-20" title="Updating weather..."></div>
      )}
      {/* Displaying a general error icon if an error occurred but we still have some (possibly stale) data */}
      {error && !loading && !weatherData.location.includes('Error') && (
          <div className="absolute top-2 right-2 text-red-400 text-xl" title={error}>⚠️</div>
      )}
      <div className="weather-main-info">
        <div className="weather-icon">{weatherData.icon}</div>
        <div className="weather-temp-info">
          <div className="weather-temp">{weatherData.temperature}°C</div>
          <div className="weather-condition">{weatherData.condition}</div>
        </div>
      </div>
      <div className="weather-location">{weatherData.location}</div>
      <div className="weather-description">{weatherData.description}</div>
      
      <div className="weather-details-grid">
        <div className="weather-detail-item">
          <span className="label">Feels Like</span>
          <span className="value">{weatherData.feelsLike}°C</span>
        </div>
        <div className="weather-detail-item">
          <span className="label">Humidity</span>
          <span className="value">{weatherData.humidity}%</span>
        </div>
        <div className="weather-detail-item">
          <span className="label">Wind</span>
          <span className="value">{weatherData.windSpeed} km/h</span>
        </div>
      </div>
      {error && (
        <p className="api-placeholder-note text-red-400 mt-3">
           Error: {error}. Displaying last known or error state data.
        </p>
      )}
    </motion.div>
  );
};

export default WeatherWidget; 