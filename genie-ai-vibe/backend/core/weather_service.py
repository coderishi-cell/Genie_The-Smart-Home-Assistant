import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

class WeatherService:
    def __init__(self):
        # Use the same API key from the frontend
        self.api_key = 'd74bcc220de466c388696f75f8a8d449'
        self.city_id = '1275004'  # Kolkata City ID
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self._cached_weather = None
        self._cache_timestamp = None
        self._cache_duration = timedelta(minutes=30)  # Cache for 30 minutes

    def get_current_weather(self) -> Optional[Dict[str, Any]]:
        """Get current weather data with caching"""
        try:
            # Check if we have valid cached data
            if (self._cached_weather and self._cache_timestamp and 
                datetime.now() - self._cache_timestamp < self._cache_duration):
                return self._cached_weather

            # Fetch fresh weather data
            url = f"{self.base_url}/weather?id={self.city_id}&appid={self.api_key}&units=metric"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                weather_info = self._format_weather_data(data)
                
                # Cache the data
                self._cached_weather = weather_info
                self._cache_timestamp = datetime.now()
                
                return weather_info
            else:
                print(f"Weather API error: {response.status_code}")
                return self._cached_weather  # Return cached data if available
                
        except Exception as e:
            print(f"Error fetching weather data: {e}")
            return self._cached_weather  # Return cached data if available

    def get_weather_forecast(self, hours: int = 24) -> Optional[Dict[str, Any]]:
        """Get weather forecast for next few hours"""
        try:
            url = f"{self.base_url}/forecast?id={self.city_id}&appid={self.api_key}&units=metric"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                forecast_list = data.get('list', [])
                
                # Get forecast for next 'hours' hours
                relevant_forecasts = []
                for forecast in forecast_list[:hours//3]:  # API gives 3-hour intervals
                    relevant_forecasts.append(self._format_forecast_data(forecast))
                
                return {
                    'city': data.get('city', {}).get('name', 'Unknown'),
                    'forecasts': relevant_forecasts
                }
            else:
                print(f"Weather forecast API error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error fetching weather forecast: {e}")
            return None

    def _format_weather_data(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format weather data for internal use"""
        if not api_data:
            return {}
        
        weather_main = api_data.get('weather', [{}])[0]
        
        return {
            'location': api_data.get('name', 'Unknown'),
            'temperature': round(api_data.get('main', {}).get('temp', 0)),
            'feels_like': round(api_data.get('main', {}).get('feels_like', 0)),
            'humidity': api_data.get('main', {}).get('humidity', 0),
            'pressure': api_data.get('main', {}).get('pressure', 0),
            'condition': weather_main.get('main', 'Unknown'),
            'description': weather_main.get('description', 'No description'),
            'icon': weather_main.get('icon', '01d'),
            'wind_speed': api_data.get('wind', {}).get('speed', 0),
            'wind_direction': api_data.get('wind', {}).get('deg', 0),
            'clouds': api_data.get('clouds', {}).get('all', 0),
            'visibility': api_data.get('visibility', 10000) / 1000,  # Convert to km
            'sunrise': api_data.get('sys', {}).get('sunrise'),
            'sunset': api_data.get('sys', {}).get('sunset'),
            'timestamp': datetime.now().isoformat()
        }

    def _format_forecast_data(self, forecast_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format forecast data"""
        weather_main = forecast_data.get('weather', [{}])[0]
        
        return {
            'datetime': forecast_data.get('dt_txt'),
            'temperature': round(forecast_data.get('main', {}).get('temp', 0)),
            'feels_like': round(forecast_data.get('main', {}).get('feels_like', 0)),
            'humidity': forecast_data.get('main', {}).get('humidity', 0),
            'condition': weather_main.get('main', 'Unknown'),
            'description': weather_main.get('description', 'No description'),
            'wind_speed': forecast_data.get('wind', {}).get('speed', 0),
            'precipitation_prob': forecast_data.get('pop', 0) * 100  # Convert to percentage
        }

    def is_weather_extreme(self, weather_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Check if current weather conditions are extreme"""
        if not weather_data:
            weather_data = self.get_current_weather()
        
        if not weather_data:
            return {'is_extreme': False, 'reasons': []}
        
        extreme_conditions = []
        temperature = weather_data.get('temperature', 0)
        humidity = weather_data.get('humidity', 0)
        condition = weather_data.get('condition', '').lower()
        wind_speed = weather_data.get('wind_speed', 0)
        
        # Temperature extremes (for India/Kolkata)
        if temperature > 35:
            extreme_conditions.append(f"Very hot temperature: {temperature}°C")
        elif temperature < 10:
            extreme_conditions.append(f"Very cold temperature: {temperature}°C")
        
        # Humidity extremes
        if humidity > 80:
            extreme_conditions.append(f"Very high humidity: {humidity}%")
        elif humidity < 20:
            extreme_conditions.append(f"Very low humidity: {humidity}%")
        
        # Weather condition extremes
        if any(word in condition for word in ['storm', 'heavy', 'severe', 'extreme']):
            extreme_conditions.append(f"Severe weather: {condition}")
        
        # Wind extremes (convert m/s to km/h)
        wind_kmh = wind_speed * 3.6
        if wind_kmh > 50:
            extreme_conditions.append(f"High winds: {wind_kmh:.1f} km/h")
        
        return {
            'is_extreme': len(extreme_conditions) > 0,
            'reasons': extreme_conditions,
            'temperature': temperature,
            'humidity': humidity,
            'condition': condition
        }

    def get_comfort_recommendations(self, weather_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get comfort recommendations based on weather"""
        if not weather_data:
            weather_data = self.get_current_weather()
        
        if not weather_data:
            return {'ac_temp': 24, 'lighting': 'normal', 'recommendations': []}
        
        temperature = weather_data.get('temperature', 25)
        humidity = weather_data.get('humidity', 50)
        condition = weather_data.get('condition', '').lower()
        
        recommendations = []
        
        # AC temperature recommendations
        ac_temp = 24  # Default
        if temperature > 30:
            ac_temp = 22
            recommendations.append("Cool down with AC due to hot weather")
        elif temperature > 25:
            ac_temp = 24
            recommendations.append("Moderate cooling recommended")
        elif temperature < 20:
            ac_temp = 26
            recommendations.append("Gentle heating might be needed")
        
        # Adjust for humidity
        if humidity > 70:
            ac_temp -= 1  # Lower temp for high humidity
            recommendations.append("Dehumidification recommended")
        elif humidity < 30:
            ac_temp += 1  # Higher temp for low humidity
            recommendations.append("Add some humidity if possible")
        
        # Lighting recommendations
        lighting = 'normal'
        if 'rain' in condition or 'storm' in condition or 'cloud' in condition:
            lighting = 'bright'
            recommendations.append("Increase lighting due to gloomy weather")
        elif 'clear' in condition and datetime.now().hour > 18:
            lighting = 'warm'
            recommendations.append("Use warm lighting for clear evening")
        
        return {
            'ac_temp': max(18, min(28, ac_temp)),  # Clamp between 18-28°C
            'lighting': lighting,
            'recommendations': recommendations,
            'weather_context': {
                'temperature': temperature,
                'humidity': humidity,
                'condition': condition
            }
        }

# Global weather service instance
weather_service = WeatherService() 