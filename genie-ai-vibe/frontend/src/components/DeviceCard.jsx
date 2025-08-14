import { motion } from 'framer-motion'
import { useState, useMemo, useEffect, useRef } from 'react'

const songs = [
  { filename: "Tu Hi Meri Raah (Encore Version).wav", title: "Tu Hi Meri Raah (Encore Version)" },
  { filename: "Tu Hi Meri Raah (Remastered x2) (Remix).wav", title: "Tu Hi Meri Raah (Remix)" },
  { filename: "Tu Hi Meri Raah.wav", title: "Tu Hi Meri Raah" },
  { filename: "Tu Hi Meri Raah (Remastered).wav", title: "Tu Hi Meri Raah (Remastered)" },
  { filename: "Nach Re Patakha 2.wav", title: "Nach Re Patakha 2" },
  { filename: "Nach Re Patakha.wav", title: "Nach Re Patakha" },
  { filename: "Tera Naam Likha (Romantic Universe Version) 2.wav", title: "Tera Naam Likha (Romantic Universe V2)" },
  { filename: "Tera Naam Likha (Romantic Universe Version).wav", title: "Tera Naam Likha (Romantic Universe)" },
  { filename: "Tera Naam Likha (Remastered) (1).wav", title: "Tera Naam Likha (Remastered)" },
  { filename: "Tera Naam Likha (parallel World ver).wav", title: "Tera Naam Likha (Parallel World)" },
  { filename: "Tera Naam Likha.wav", title: "Tera Naam Likha" },
  { filename: "Tod De Deewar.wav", title: "Tod De Deewar" },
  { filename: "मोहतरमा - Final.mp3", title: "मोहतरमा" }
];

const DeviceCard = ({ deviceId, deviceState, onUpdate }) => {
  const [isUpdating, setIsUpdating] = useState(false)
  
  // Debug: Log device state changes
  console.log(`DeviceCard ${deviceId}:`, deviceState)
  
  const { type, name, on, brightness, color, temperature, mode, open, locked, playing, track, volume, armed } = deviceState

  const audioRef = useRef(null); // Ref for the audio element

  const [currentTrackDetails, setCurrentTrackDetails] = useState({
    title: "No Track Selected",
    artist: "", // Artist not shown as per request
    albumArtUrl: null, // Changed from placeholder path to null
    duration: 0,
    filename: null,
  });
  const [playbackTime, setPlaybackTime] = useState(0);
  // isPlayingSimulated will now reflect the audio element's playing state primarily
  const [isPlayingSimulated, setIsPlayingSimulated] = useState(false); 

  const loadRandomTrack = () => {
    const randomIndex = Math.floor(Math.random() * songs.length);
    const randomSong = songs[randomIndex];
    setCurrentTrackDetails({
      ...randomSong,
      artist: "", // No artist
      albumArtUrl: null, // Set to null, as no real art is fetched
      duration: 0, // Will be updated on metadata load
    });
    setPlaybackTime(0);
    if (audioRef.current) {
      audioRef.current.src = `/Songs/${randomSong.filename}`;
      audioRef.current.load(); // Important to load the new source
      // Set initial volume when a new track is loaded
      audioRef.current.volume = (deviceState.volume || 50) / 100; 
    }
  };

  // Effect for handling audio element events
  useEffect(() => {
    const audioElement = audioRef.current;
    if (!audioElement) return;

    const handleLoadedMetadata = () => {
      setCurrentTrackDetails(prev => ({ ...prev, duration: audioElement.duration || 0 }));
      // Ensure volume is set once metadata is loaded, in case it wasn't set before
      audioElement.volume = (volume || 50) / 100; 
    };
    const handleTimeUpdate = () => {
      setPlaybackTime(audioElement.currentTime);
    };
    const handlePlay = () => setIsPlayingSimulated(true);
    const handlePause = () => setIsPlayingSimulated(false);
    const handleEnded = () => {
      // Song ended, load and play next random song
      loadRandomTrack();
      // We need to ensure the global state reflects playing the next song too
      // Or, if the intention is to stop after one song, handleUpdate({ playing: false })
      // For now, let's assume we want to auto-play next and keep the global state `playing` as true
      // If it was already true. If it was false, this was triggered by a direct call. 
      if(deviceState.playing) {
          audioElement.play().catch(e => console.error("Error playing next track:", e));
      }
    };

    audioElement.addEventListener('loadedmetadata', handleLoadedMetadata);
    audioElement.addEventListener('timeupdate', handleTimeUpdate);
    audioElement.addEventListener('play', handlePlay);
    audioElement.addEventListener('pause', handlePause);
    audioElement.addEventListener('ended', handleEnded);

    return () => {
      audioElement.removeEventListener('loadedmetadata', handleLoadedMetadata);
      audioElement.removeEventListener('timeupdate', handleTimeUpdate);
      audioElement.removeEventListener('play', handlePlay);
      audioElement.removeEventListener('pause', handlePause);
      audioElement.removeEventListener('ended', handleEnded);
    };
  }, [currentTrackDetails.filename, volume]); // Added volume to deps to re-apply on external change
  
  // Sync audio element volume with deviceState.volume
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = (volume || 0) / 100; // Ensure volume is between 0.0 and 1.0
    }
  }, [volume]); // Run this effect when the volume prop changes

  // Sync with global playing state from prop
  useEffect(() => {
    if (playing && !isPlayingSimulated) { // Global state wants to play, but not playing locally
      if (!currentTrackDetails.filename) { // No track loaded yet
        loadRandomTrack(); // Load a track first
        // Play will be triggered by the audio element loading and the subsequent effect or click
      } else if (audioRef.current && audioRef.current.paused) {
        audioRef.current.play().catch(e => console.error("Error playing track:", e));
      }
    } else if (!playing && isPlayingSimulated) { // Global state wants to pause, but playing locally
      if (audioRef.current && !audioRef.current.paused) {
        audioRef.current.pause();
      }
    }
    // If playing is false, and playbackTime was not 0, it means a song was playing and was stopped externally.
    // Reset playbackTime for the current track to start from beginning if played again.
    if(!playing && playbackTime > 0) {
        setPlaybackTime(0); 
        if(audioRef.current) audioRef.current.currentTime = 0; // also reset audio element's time
    }

  }, [playing, isPlayingSimulated, currentTrackDetails.filename]);

  const handlePlayPauseClick = () => {
    const newPlayingState = !deviceState.playing;
    handleUpdate({ playing: newPlayingState }); // Update global state

    if (newPlayingState) {
      if (!currentTrackDetails.filename || audioRef.current?.src === window.location.href) { // No track loaded or src is blank
        loadRandomTrack(); 
        // audioRef.current.play() will be called by the effect chain or after metadata load
      } else {
        audioRef.current?.play().catch(e => console.error("Error playing track:", e));
      }
    } else {
      audioRef.current?.pause();
    }
  };

  const formatTime = (totalSeconds) => {
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = Math.floor(totalSeconds % 60); // Ensure seconds are integers
    return `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
  };

  const handleUpdate = async (updates) => {
    setIsUpdating(true)
    try {
      await onUpdate(deviceId, updates)
    } finally {
      setIsUpdating(false)
    }
  }

  const getDeviceIcon = () => {
    const iconMap = {
      light: '/icons/lightbulb.svg',
      ac: '/icons/ac.svg',
      blinds: '/icons/blinds.svg',
      door: '/icons/door.svg',
      music: '/icons/music.svg',
      security: '/icons/security.svg'
    }
    return iconMap[type] || '/icons/lightbulb.svg'
  }

  // Determine if the device is generally in an "active" or "on" state for card styling
  const isActiveForCard = useMemo(() => {
    if (type === 'light') return !!on;
    if (type === 'ac') return !!on;
    if (type === 'blinds') return !!open;
    if (type === 'door') return !locked; // Active if unlocked
    if (type === 'music') return !!playing; // Based on global state
    if (type === 'security') return !!armed;
    return false;
  }, [type, on, open, locked, playing, armed]);

  // Reduced intensity or removed dynamic background glow from original getStatusColor as it might be too busy
  const subtleStatusIndicator = useMemo(() => {
    if (type === 'light' && on) return color || 'var(--accentColor)';
    // Add other subtle indicators if needed, or rely on active-device border
    return 'transparent'; // Default to no specific color override for the subtle indicator
  }, [type, on, color]);

  const renderControls = () => {
    switch (type) {
      case 'light':
        return (
          <div className="space-y-4">
            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={() => handleUpdate({ on: !on })}
              disabled={isUpdating}
              className={`device-control-button ${on ? 'active' : 'inactive'}`}
            >
              {on ? 'Turn Off' : 'Turn On'}
            </motion.button>
            
            {on && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="space-y-3 pt-2"
              >
                <div className="flex items-center justify-between text-sm">
                  <span>Brightness</span>
                  <span className="font-medium">{brightness}%</span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="100"
                  value={brightness}
                  onChange={(e) => handleUpdate({ brightness: parseInt(e.target.value) })}
                  disabled={isUpdating}
                  className="device-slider"
                  style={{
                    background: `linear-gradient(to right, var(--accentColor) 0%, var(--accentColor) ${brightness}%, rgba(var(--textColorPrimaryRGB), 0.15) ${brightness}%, rgba(var(--textColorPrimaryRGB), 0.15) 100%)`
                  }}
                />
              </motion.div>
            )}
          </div>
        )

      case 'ac':
        return (
          <div className="space-y-4">
            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={() => handleUpdate({ on: !on })}
              disabled={isUpdating}
              className={`device-control-button ${on ? 'active' : 'inactive'}`}
            >
              {on ? 'Turn Off' : 'Turn On'}
            </motion.button>
            
            {on && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="space-y-3 pt-2"
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm">Temperature</span>
                  <div className="flex items-center space-x-2">
                    <motion.button
                      whileTap={{ scale: 0.9 }}
                      onClick={() => handleUpdate({ temperature: Math.max(16, temperature - 1) })}
                      disabled={isUpdating}
                      className="device-adjust-button"
                    >
                      -
                    </motion.button>
                    <span className="text-lg font-bold min-w-[3rem] text-center tabular-nums">{temperature}°C</span>
                    <motion.button
                      whileTap={{ scale: 0.9 }}
                      onClick={() => handleUpdate({ temperature: Math.min(30, temperature + 1) })}
                      disabled={isUpdating}
                      className="device-adjust-button"
                    >
                      +
                    </motion.button>
                  </div>
                </div>
              </motion.div>
            )}
          </div>
        )

      case 'blinds':
        return (
          <motion.button
            whileTap={{ scale: 0.95 }}
            onClick={() => handleUpdate({ open: !open, position: open ? 0 : 100 })}
            disabled={isUpdating}
            className={`device-control-button ${open ? 'active' : 'inactive'}`}
          >
            {open ? 'Close Blinds' : 'Open Blinds'}
          </motion.button>
        )

      case 'door':
        return (
          <motion.button
            whileTap={{ scale: 0.95 }}
            onClick={() => handleUpdate({ locked: !locked })}
            disabled={isUpdating}
            className={`device-control-button ${!locked ? 'active' : 'inactive'}`}
          >
            {locked ? 'Unlock Door' : 'Lock Door'}
          </motion.button>
        )

      case 'music':
        return (
          <div className="space-y-4">
            <audio ref={audioRef} />
            {/* Album Art Placeholder - Conditionally Rendered */} 
            {currentTrackDetails.albumArtUrl && (
              <div className="w-full h-32 bg-gray-700 rounded-md flex items-center justify-center mb-3">
                <img 
                  src={currentTrackDetails.albumArtUrl} 
                  alt="Album Art" 
                  className="w-20 h-20 text-gray-400" // Adjust styling if real art is used
                />
              </div>
            )}

            <div className="text-center space-y-1">
              <div className="font-semibold text-md truncate" title={currentTrackDetails.title}>{currentTrackDetails.title}</div>
              {currentTrackDetails.artist && (
                <div className="text-xs opacity-70 truncate" title={currentTrackDetails.artist}>{currentTrackDetails.artist}</div>
              )}
            </div>

            {/* Playback Progress */}
            <div className="space-y-1 pt-1">
              <div className="w-full bg-gray-600 rounded-full h-1.5">
                <motion.div 
                  className="bg-[var(--accentColor)] h-1.5 rounded-full"
                  initial={{ width: "0%" }}
                  animate={{ width: currentTrackDetails.duration > 0 ? `${(playbackTime / currentTrackDetails.duration) * 100}%` : "0%" }}
                  transition={{ duration: 0.2, ease: "linear" }}
                />
              </div>
              <div className="flex justify-between text-xs opacity-70">
                <span>{formatTime(playbackTime)}</span>
                <span>{formatTime(currentTrackDetails.duration)}</span>
              </div>
            </div>

            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={handlePlayPauseClick}
              disabled={isUpdating}
              className={`device-control-button ${deviceState.playing ? 'active' : 'inactive'}`}
            >
              {deviceState.playing ? 'Pause' : 'Play'}
            </motion.button>
            
            {/* Volume control - only show if a track is loaded (duration > 0 implies metadata loaded) */}
            {currentTrackDetails.duration > 0 && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="space-y-3 pt-2"
              >
                <div className="flex items-center justify-between text-sm">
                  <span>Volume</span>
                  <span className="font-medium">{volume || 0}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={volume || 0} // Ensure value is controlled and defaults to 0 if undefined
                  onChange={(e) => {
                    const newVolume = parseInt(e.target.value);
                    handleUpdate({ volume: newVolume });
                    // Immediate update to audio element for responsiveness, though useEffect will also catch it
                    if (audioRef.current) {
                      audioRef.current.volume = newVolume / 100;
                    }
                  }}
                  disabled={isUpdating}
                  className="device-slider"
                  style={{
                    background: `linear-gradient(to right, var(--accentColor) 0%, var(--accentColor) ${volume || 0}%, rgba(var(--textColorPrimaryRGB), 0.15) ${volume || 0}%, rgba(var(--textColorPrimaryRGB), 0.15) 100%)`
                  }}
                />
              </motion.div>
            )}
          </div>
        )

      case 'security':
        return (
          <motion.button
            whileTap={{ scale: 0.95 }}
            onClick={() => handleUpdate({ armed: !armed, mode: armed ? 'off' : 'home' })}
            disabled={isUpdating}
            className={`device-control-button ${armed ? 'active' : 'inactive'}`}
          >
            {armed ? 'Disarm System' : 'Arm System'}
          </motion.button>
        )

      default:
        return <p className="text-xs opacity-50">No controls available for this device type.</p>;
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.3 }}
      className={`device-card p-5 flex flex-col justify-between min-h-[220px] ${isActiveForCard ? 'active-device' : ''}`}
    >
      <div 
        className="absolute top-2 right-2 w-3 h-3 rounded-full z-10 transition-all duration-300"
        style={{ backgroundColor: isActiveForCard ? 'var(--accentColor)' : 'rgba(var(--textColorPrimaryRGB), 0.2)' }} 
      />
      
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-3">
          <motion.img 
            src={getDeviceIcon()} 
            alt={`${type} icon`} 
            className={`device-icon w-8 h-8 ${isActiveForCard ? 'active' : ''}`} 
            initial={{ scale: 0.8, opacity: 0.5 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.1 }}
          />
          <h3 className="text-lg font-semibold leading-tight">{name}</h3>
        </div>
      </div>

      <div className="mt-auto">
        {renderControls()}
      </div>

      {isUpdating && (
        <div className="absolute inset-0 bg-black/30 backdrop-blur-sm flex items-center justify-center rounded-lg z-20">
          <div className="w-6 h-6 border-2 border-[var(--accentColor)] border-t-transparent rounded-full animate-spin"></div>
        </div>
      )}
    </motion.div>
  )
}

export default DeviceCard 