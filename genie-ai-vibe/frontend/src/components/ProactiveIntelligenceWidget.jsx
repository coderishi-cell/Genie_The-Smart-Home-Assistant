import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

const ProactiveIntelligenceWidget = () => {
  const [automationStatus, setAutomationStatus] = useState(null);
  const [insights, setInsights] = useState(null);
  const [recentDecisions, setRecentDecisions] = useState([]);
  const [weatherRecs, setWeatherRecs] = useState(null);
  const [advancedFeatures, setAdvancedFeatures] = useState(null);
  const [moodSuggestion, setMoodSuggestion] = useState(null);
  const [energyAnalysis, setEnergyAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [applyingMood, setApplyingMood] = useState(false);
  const [autoApplyCountdown, setAutoApplyCountdown] = useState(null);
  const [moodAppliedSuccess, setMoodAppliedSuccess] = useState(null);

  const API_BASE = 'http://localhost:8000/api';

  useEffect(() => {
    fetchAutomationData();
    // Refresh data every 30 seconds
    const interval = setInterval(fetchAutomationData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchAutomationData = async () => {
    try {
      setLoading(true);
      
      // Fetch automation status
      const statusResponse = await fetch(`${API_BASE}/automation/status`);
      const statusData = await statusResponse.json();
      setAutomationStatus(statusData);
      
      // Fetch insights
      const insightsResponse = await fetch(`${API_BASE}/automation/insights`);
      const insightsData = await insightsResponse.json();
      setInsights(insightsData.insights);
      
      // Fetch recent decisions
      const decisionsResponse = await fetch(`${API_BASE}/automation/decisions?limit=5`);
      const decisionsData = await decisionsResponse.json();
      setRecentDecisions(decisionsData.decisions);
      
      // Fetch weather recommendations
      const weatherResponse = await fetch(`${API_BASE}/weather/recommendations`);
      const weatherData = await weatherResponse.json();
      setWeatherRecs(weatherData.recommendations);
      
      // Fetch advanced features
      try {
        const advancedResponse = await fetch(`${API_BASE}/automation/advanced-insights`);
        const advancedData = await advancedResponse.json();
        setAdvancedFeatures(advancedData);
      } catch (err) {
        console.log('Advanced features not available');
      }
      
      // Fetch mood suggestion
      try {
        const moodResponse = await fetch(`${API_BASE}/automation/suggest-mood`, { method: 'POST' });
        const moodData = await moodResponse.json();
        if (moodData.status === 'success') {
          setMoodSuggestion(moodData.mood_suggestion);
        }
      } catch (err) {
        console.log('Mood suggestions not available');
      }
      
      // Fetch energy analysis
      try {
        const energyResponse = await fetch(`${API_BASE}/automation/energy-analysis`);
        const energyData = await energyResponse.json();
        setEnergyAnalysis(energyData.energy_analysis);
      } catch (err) {
        console.log('Energy analysis not available');
      }
      
      setError(null);
    } catch (err) {
      console.error('Error fetching automation data:', err);
      setError('Failed to load proactive intelligence data');
    } finally {
      setLoading(false);
    }
  };

  const toggleAutomation = async () => {
    try {
      const action = automationStatus.is_running ? 'stop' : 'start';
      const response = await fetch(`${API_BASE}/automation/control`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ action }),
      });
      
      if (response.ok) {
        fetchAutomationData(); // Refresh data
      }
    } catch (err) {
      console.error('Error toggling automation:', err);
    }
  };

  const applyMoodSuggestion = async (suggestedMood, isAutomatic = false) => {
    try {
      setApplyingMood(true);
      
      // Apply mood automation
      const automationResponse = await fetch(`${API_BASE}/automation/apply-mood-automation?mood=${encodeURIComponent(suggestedMood)}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (automationResponse.ok) {
        console.log('✅ Mood automation applied successfully');
        
        // Apply mood to the interface
        const moodResponse = await fetch(`${API_BASE}/mood/apply`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ mood_name: suggestedMood }),
        });
        
        if (moodResponse.ok) {
          console.log('✅ Mood interface theme applied successfully');
          // Refresh data to show updated states
          fetchAutomationData();
          
          // Trigger a custom event to notify other components about mood change
          window.dispatchEvent(new CustomEvent('moodChanged', { 
            detail: { mood: suggestedMood, source: isAutomatic ? 'ai_automatic' : 'ai_manual' } 
          }));
          
          console.log(`✅ Applied AI-suggested mood: ${suggestedMood} (${isAutomatic ? 'automatic' : 'manual'})`);
          
          // Show success notification
          setMoodAppliedSuccess({
            mood: suggestedMood,
            isAutomatic,
            timestamp: new Date()
          });
          
          // Clear the mood suggestion after successful application
          setMoodSuggestion(null);
          
          // Clear success notification after 5 seconds
          setTimeout(() => setMoodAppliedSuccess(null), 5000);
        } else {
          console.error('Failed to apply mood to interface:', await moodResponse.text());
        }
      } else {
        console.error('Failed to apply mood automation:', await automationResponse.text());
      }
    } catch (err) {
      console.error('Error applying mood suggestion:', err);
    } finally {
      setApplyingMood(false);
      setAutoApplyCountdown(null);
    }
  };

  // Auto-apply high confidence mood suggestions with countdown
  React.useEffect(() => {
    if (moodSuggestion && moodSuggestion.confidence > 0.8 && automationStatus?.is_running && !applyingMood) {
      let countdown = 5; // 5 second countdown
      setAutoApplyCountdown(countdown);
      
      const countdownInterval = setInterval(() => {
        countdown -= 1;
        setAutoApplyCountdown(countdown);
        
        if (countdown <= 0) {
          clearInterval(countdownInterval);
          applyMoodSuggestion(moodSuggestion.suggested_mood, true);
        }
      }, 1000);
      
      return () => {
        clearInterval(countdownInterval);
        setAutoApplyCountdown(null);
      };
    }
  }, [moodSuggestion, automationStatus?.is_running, applyingMood]);

  if (loading && !automationStatus) {
    return (
      <motion.div
        className="proactive-widget glass-effect content-panel"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-[var(--accentColor)] border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
          <p>Loading Intelligence Status...</p>
        </div>
      </motion.div>
    );
  }

  if (error) {
    return (
      <motion.div
        className="proactive-widget glass-effect content-panel"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        <div className="text-center text-red-400">
          <p>⚠️ {error}</p>
          <button onClick={fetchAutomationData} className="mt-2 px-4 py-2 bg-[var(--accentColor)] rounded">
            Retry
          </button>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      className="proactive-widget glass-effect content-panel"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-semibold flex items-center">
          🧠 Proactive Intelligence
        </h3>
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${automationStatus?.is_running ? 'bg-green-400' : 'bg-gray-400'}`}></div>
          <span className="text-sm">
            {automationStatus?.is_running ? 'Active' : 'Inactive'}
          </span>
        </div>
      </div>

      {/* Main Status */}
      <div className="mb-4">
        <button
          onClick={toggleAutomation}
          className={`w-full py-2 px-4 rounded-lg font-medium transition-colors ${
            automationStatus?.is_running
              ? 'bg-red-500 hover:bg-red-600 text-white'
              : 'bg-[var(--accentColor)] hover:bg-[var(--accentColor)]/80 text-white'
          }`}
        >
          {automationStatus?.is_running ? 'Stop Automation' : 'Start Automation'}
        </button>
      </div>

      {/* Quick Stats */}
      {insights && (
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="text-center p-3 bg-white/5 rounded-lg">
            <div className="text-2xl font-bold text-[var(--accentColor)]">
              {insights.total_patterns}
            </div>
            <div className="text-xs opacity-80">Learned Patterns</div>
          </div>
          <div className="text-center p-3 bg-white/5 rounded-lg">
            <div className="text-2xl font-bold text-[var(--accentColor)]">
              {insights.automation_success_rate}%
            </div>
            <div className="text-xs opacity-80">Success Rate</div>
          </div>
        </div>
      )}

      {/* Weather Recommendations */}
      {weatherRecs && (
        <div className="mb-4 p-3 bg-blue-500/10 rounded-lg">
          <h4 className="text-sm font-semibold mb-2 flex items-center">
            🌤️ Weather-Based Suggestions
          </h4>
          <div className="text-xs space-y-1">
            <div>AC: {weatherRecs.ac_temp}°C recommended</div>
            <div>Lighting: {weatherRecs.lighting} mode</div>
            {weatherRecs.recommendations.length > 0 && (
              <div className="text-yellow-400">
                💡 {weatherRecs.recommendations[0]}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Recent Decisions */}
      {recentDecisions.length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-semibold mb-2">🤖 Recent Automation</h4>
          <div className="space-y-2 max-h-32 overflow-y-auto">
            {recentDecisions.slice(0, 3).map((decision, index) => (
              <div key={index} className="text-xs p-2 bg-white/5 rounded">
                <div className="flex items-center justify-between">
                  <span className="text-[var(--accentColor)]">
                    {decision.decision_type.replace('_', ' ')}
                  </span>
                  <span className="opacity-60">
                    {new Date(decision.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <div className="opacity-80 mt-1">
                  {decision.action_taken}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Advanced Features Status */}
      {advancedFeatures && (
        <div className="mb-4 p-3 bg-purple-500/10 rounded-lg">
          <h4 className="text-sm font-semibold mb-2 flex items-center">
            🚀 Advanced Features
          </h4>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className={`p-2 rounded ${advancedFeatures.advanced_automation?.energy_optimization_active ? 'bg-green-500/20' : 'bg-gray-500/20'}`}>
              <div>⚡ Energy Optimization</div>
            </div>
            <div className={`p-2 rounded ${advancedFeatures.advanced_automation?.sleep_optimization_active ? 'bg-green-500/20' : 'bg-gray-500/20'}`}>
              <div>💤 Sleep Optimization</div>
            </div>
            <div className={`p-2 rounded ${advancedFeatures.advanced_automation?.occupancy_detection_active ? 'bg-green-500/20' : 'bg-gray-500/20'}`}>
              <div>👥 Occupancy Detection</div>
            </div>
            <div className={`p-2 rounded ${advancedFeatures.advanced_automation?.predictive_scheduling_active ? 'bg-green-500/20' : 'bg-gray-500/20'}`}>
              <div>🔮 Predictive Scheduling</div>
            </div>
          </div>
        </div>
      )}

      {/* AI Mood Suggestion */}
      {moodSuggestion && (
        <motion.div 
          className="mb-4 p-3 bg-pink-500/10 rounded-lg border border-pink-500/20"
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.3 }}
        >
          <h4 className="text-sm font-semibold mb-2 flex items-center justify-between">
            <span>🎭 AI Mood Suggestion</span>
            {autoApplyCountdown !== null && (
              <span className="text-xs bg-[var(--accentColor)] text-white px-2 py-1 rounded-full">
                Auto-applying in {autoApplyCountdown}s
              </span>
            )}
          </h4>
          <div className="text-xs space-y-2">
            <div className="flex justify-between items-center">
              <span>Suggested Mood:</span>
              <span className="text-[var(--accentColor)] font-semibold">{moodSuggestion.suggested_mood}</span>
            </div>
            <div className="opacity-80">{moodSuggestion.reason}</div>
            <div className="flex justify-between items-center">
              <span>Confidence:</span>
              <span className="text-green-400">{Math.round(moodSuggestion.confidence * 100)}%</span>
            </div>
            
            {/* Action Buttons */}
            <div className="flex space-x-2 mt-3">
              <button
                onClick={() => applyMoodSuggestion(moodSuggestion.suggested_mood, false)}
                disabled={applyingMood}
                className="flex-1 py-2 px-3 bg-[var(--accentColor)] hover:bg-[var(--accentColor)]/80 text-white text-xs rounded-lg font-medium transition-colors disabled:opacity-50"
              >
                {applyingMood ? (
                  <span className="flex items-center justify-center">
                    <div className="w-3 h-3 border border-white border-t-transparent rounded-full animate-spin mr-1"></div>
                    Applying...
                  </span>
                ) : (
                  'Apply Now'
                )}
              </button>
              <button
                onClick={() => {
                  setMoodSuggestion(null);
                  setAutoApplyCountdown(null);
                }}
                disabled={applyingMood}
                className="px-3 py-2 bg-gray-500/20 hover:bg-gray-500/30 text-gray-300 text-xs rounded-lg font-medium transition-colors disabled:opacity-50"
              >
                Dismiss
              </button>
            </div>
            
            {moodSuggestion.confidence > 0.8 && autoApplyCountdown === null && !applyingMood && (
              <div className="text-xs text-yellow-400 mt-2 flex items-center">
                <span className="mr-1">⚡</span>
                High confidence - will auto-apply when automation is active
              </div>
            )}
          </div>
        </motion.div>
      )}

      {/* Mood Applied Success Notification */}
      {moodAppliedSuccess && (
        <motion.div 
          className="mb-4 p-3 bg-green-500/10 rounded-lg border border-green-500/20"
          initial={{ scale: 0.95, opacity: 0, y: -10 }}
          animate={{ scale: 1, opacity: 1, y: 0 }}
          exit={{ scale: 0.95, opacity: 0, y: -10 }}
          transition={{ duration: 0.3 }}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <span className="text-green-400 mr-2">✅</span>
              <div>
                <div className="text-sm font-semibold text-green-400">
                  Mood Applied Successfully!
                </div>
                <div className="text-xs opacity-80">
                  {moodAppliedSuccess.mood} mood {moodAppliedSuccess.isAutomatic ? 'automatically' : 'manually'} applied
                </div>
              </div>
            </div>
            <button
              onClick={() => setMoodAppliedSuccess(null)}
              className="text-gray-400 hover:text-white text-xs"
            >
              ✕
            </button>
          </div>
        </motion.div>
      )}

      {/* Energy Analysis */}
      {energyAnalysis && (
        <div className="mb-4 p-3 bg-yellow-500/10 rounded-lg">
          <h4 className="text-sm font-semibold mb-2 flex items-center">
            ⚡ Energy Analysis
          </h4>
          <div className="text-xs space-y-1">
            <div className="flex justify-between">
              <span>Current Usage:</span>
              <span className="text-[var(--accentColor)]">{energyAnalysis.estimated_usage_watts}W</span>
            </div>
            <div className="flex justify-between">
              <span>Lights On:</span>
              <span>{energyAnalysis.lights_on_count}</span>
            </div>
            <div className="flex justify-between">
              <span>AC Running:</span>
              <span className={energyAnalysis.ac_running ? 'text-blue-400' : 'text-gray-400'}>
                {energyAnalysis.ac_running ? 'Yes' : 'No'}
              </span>
            </div>
            {energyAnalysis.optimization_suggestions > 0 && (
              <div className="text-green-400 mt-2">
                💡 {energyAnalysis.optimization_suggestions} optimization suggestions available
              </div>
            )}
          </div>
        </div>
      )}

      {/* Learning Insights */}
      {insights && insights.most_used_devices.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold mb-2">📊 Usage Patterns</h4>
          <div className="space-y-1">
            {insights.most_used_devices.slice(0, 3).map(([device, count], index) => (
              <div key={index} className="flex justify-between text-xs">
                <span className="opacity-80">{device.replace('_', ' ')}</span>
                <span className="text-[var(--accentColor)]">{count} times</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Refresh Indicator */}
      {loading && (
        <div className="absolute top-2 right-2">
          <div className="w-4 h-4 border-2 border-[var(--accentColor)] border-t-transparent rounded-full animate-spin"></div>
        </div>
      )}
    </motion.div>
  );
};

export default ProactiveIntelligenceWidget; 