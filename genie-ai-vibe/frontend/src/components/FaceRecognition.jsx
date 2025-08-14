import React, { useState, useRef, useEffect } from 'react';

const FaceRecognition = () => {
  const [activeTab, setActiveTab] = useState('manage');
  const [knownPersons, setKnownPersons] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [systemStatus, setSystemStatus] = useState(null);
  
  // Add person states
  const [newPersonName, setNewPersonName] = useState('');
  const [newPersonAccessLevel, setNewPersonAccessLevel] = useState('standard');
  const [newPersonNotes, setNewPersonNotes] = useState('');
  const [selectedPhoto, setSelectedPhoto] = useState(null);
  const [photoPreview, setPhotoPreview] = useState(null);
  
  // Recognition states
  const [recognitionImage, setRecognitionImage] = useState(null);
  const [recognitionPreview, setRecognitionPreview] = useState(null);
  const [recognitionResults, setRecognitionResults] = useState(null);
  const [doorbellMode, setDoorbellMode] = useState(false);
  
  // Live camera states
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [lastRecognition, setLastRecognition] = useState(null);
  const [monitoringInterval, setMonitoringInterval] = useState(null);
  const [videoStream, setVideoStream] = useState(null);
  const [streamError, setStreamError] = useState(null);
  const [frameRate, setFrameRate] = useState(0);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const frameCountRef = useRef(0);
  const lastTimeRef = useRef(Date.now());
  
  const photoInputRef = useRef(null);
  const recognitionInputRef = useRef(null);

  const API_BASE = 'http://localhost:8000/api';

  useEffect(() => {
    loadKnownPersons();
    loadSystemStatus();
  }, []);

  const showMessage = (msg, type = 'info') => {
    setMessage({ text: msg, type });
    setTimeout(() => setMessage(''), 5000);
  };

  const loadSystemStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/face-recognition/status`);
      const data = await response.json();
      setSystemStatus(data);
    } catch (error) {
      console.error('Error loading system status:', error);
      showMessage('Failed to load system status', 'error');
    }
  };

  const loadKnownPersons = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/face-recognition/persons`);
      const data = await response.json();
      
      if (data.success) {
        setKnownPersons(data.persons);
      } else {
        showMessage('Failed to load known persons', 'error');
      }
    } catch (error) {
      console.error('Error loading known persons:', error);
      showMessage('Failed to connect to face recognition service', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handlePhotoSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedPhoto(file);
      const reader = new FileReader();
      reader.onload = (e) => setPhotoPreview(e.target.result);
      reader.readAsDataURL(file);
    }
  };

  const handleRecognitionImageSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      setRecognitionImage(file);
      const reader = new FileReader();
      reader.onload = (e) => setRecognitionPreview(e.target.result);
      reader.readAsDataURL(file);
    }
  };

  const addKnownPerson = async () => {
    if (!newPersonName.trim() || !selectedPhoto) {
      showMessage('Please provide both name and photo', 'warning');
      return;
    }

    try {
      setLoading(true);
      const formData = new FormData();
      formData.append('name', newPersonName.trim());
      formData.append('photo', selectedPhoto);
      formData.append('access_level', newPersonAccessLevel);
      formData.append('notes', newPersonNotes);

      const response = await fetch(`${API_BASE}/face-recognition/add-person`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (data.success) {
        showMessage(`Successfully added ${newPersonName}`, 'success');
        setNewPersonName('');
        setNewPersonNotes('');
        setSelectedPhoto(null);
        setPhotoPreview(null);
        if (photoInputRef.current) photoInputRef.current.value = '';
        loadKnownPersons();
      } else {
        showMessage(data.detail || 'Failed to add person', 'error');
      }
    } catch (error) {
      console.error('Error adding person:', error);
      showMessage('Failed to add person', 'error');
    } finally {
      setLoading(false);
    }
  };

  const removePerson = async (personName) => {
    if (!window.confirm(`Are you sure you want to remove ${personName}?`)) {
      return;
    }

    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/face-recognition/persons/${encodeURIComponent(personName)}`, {
        method: 'DELETE',
      });

      const data = await response.json();

      if (data.success) {
        showMessage(`Successfully removed ${personName}`, 'success');
        loadKnownPersons();
      } else {
        showMessage(data.detail || 'Failed to remove person', 'error');
      }
    } catch (error) {
      console.error('Error removing person:', error);
      showMessage('Failed to remove person', 'error');
    } finally {
      setLoading(false);
    }
  };

  const recognizeFaces = async () => {
    if (!recognitionImage) {
      showMessage('Please select an image for recognition', 'warning');
      return;
    }

    try {
      setLoading(true);
      const formData = new FormData();
      formData.append('image', recognitionImage);
      formData.append('doorbell_mode', doorbellMode);

      const response = await fetch(`${API_BASE}/face-recognition/recognize`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (data.success) {
        setRecognitionResults(data);
        showMessage(`Recognition complete: ${data.faces_detected} face(s) detected`, 'success');
      } else {
        showMessage(data.detail || 'Recognition failed', 'error');
        setRecognitionResults(null);
      }
    } catch (error) {
      console.error('Error in face recognition:', error);
      showMessage('Face recognition failed', 'error');
      setRecognitionResults(null);
    } finally {
      setLoading(false);
    }
  };

  const simulateDoorbellRing = async () => {
    if (!recognitionImage) {
      showMessage('Please select an image to simulate doorbell camera', 'warning');
      return;
    }

    try {
      setLoading(true);
      const formData = new FormData();
      formData.append('image', recognitionImage);
      formData.append('auto_open', 'true');

      const response = await fetch(`${API_BASE}/doorbell/ring`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (data.success) {
        const message = data.auto_open 
          ? `Door opened automatically for ${data.recognized_person} (confidence: ${(data.confidence * 100).toFixed(1)}%)`
          : `Doorbell rang. ${data.recognized_person ? `Recognized ${data.recognized_person} but door not opened` : 'No recognized persons'}`;
        
        showMessage(message, data.auto_open ? 'success' : 'info');
        
        // Also set recognition results for display
        setRecognitionResults({
          ...data,
          recognized_persons: data.all_recognized_persons || []
        });
      } else {
        showMessage('Doorbell simulation failed', 'error');
      }
    } catch (error) {
      console.error('Error simulating doorbell:', error);
      showMessage('Doorbell simulation failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Live camera functions
  const startCameraMonitoring = async () => {
    try {
      setLoading(true);
      setStreamError(null);
      
              // First, try to access user's camera using WebRTC
        try {
          console.log('Requesting camera access...');
          const stream = await navigator.mediaDevices.getUserMedia({ 
            video: { 
              width: { ideal: 640, min: 320 },
              height: { ideal: 480, min: 240 },
              facingMode: 'user', // Use front camera, change to 'environment' for back camera
              frameRate: { ideal: 30, min: 10 }
            },
            audio: false
          });
          
          console.log('Camera stream obtained:', stream.getVideoTracks()[0].getSettings());
        
        setVideoStream(stream);
        
        if (videoRef.current) {
          // Video playback will be handled by useEffect
          console.log('Camera stream obtained, setting up video...');
        }
        
        setIsMonitoring(true);
        showMessage('Live camera monitoring started', 'success');
        
        // Start automatic face recognition polling (every 2 seconds)
        const recognitionInterval = setInterval(async () => {
          console.log('Automatic recognition triggered at', new Date().toLocaleTimeString());
          await captureAndRecognizeFromVideo();
        }, 2000);
        
        // Start frame rate monitoring
        const fpsInterval = setInterval(() => {
          const now = Date.now();
          const elapsed = now - lastTimeRef.current;
          if (elapsed >= 1000) {
            const fps = Math.round((frameCountRef.current * 1000) / elapsed);
            setFrameRate(fps);
            frameCountRef.current = 0;
            lastTimeRef.current = now;
          }
        }, 1000);
        
        // Store both intervals
        setMonitoringInterval({ recognition: recognitionInterval, fps: fpsInterval });
        
      } catch (cameraError) {
        console.warn('WebRTC camera not available, falling back to server camera:', cameraError);
        
        // Fallback to server-side camera
        const response = await fetch(`${API_BASE}/doorbell/camera/start-monitoring`, {
          method: 'POST'
        });
        
        const data = await response.json();
        
                  if (data.success) {
            setIsMonitoring(true);
            showMessage('Live camera monitoring started (server camera)', 'success');
            
            // Start polling for face recognition (server camera fallback)
            const recognitionInterval = setInterval(() => {
              console.log('Automatic recognition triggered (server camera)');
              captureAndRecognize();
            }, 2000);
            setMonitoringInterval({ recognition: recognitionInterval, fps: null });
          } else {
            throw new Error('Failed to start server camera monitoring');
          }
      }
      
    } catch (error) {
      console.error('Error starting camera monitoring:', error);
      setStreamError('Failed to access camera. Please check camera permissions.');
      showMessage('Failed to start camera monitoring', 'error');
    } finally {
      setLoading(false);
    }
  };

  const stopCameraMonitoring = async () => {
    try {
      // Stop WebRTC stream
      if (videoStream) {
        videoStream.getTracks().forEach(track => track.stop());
        setVideoStream(null);
      }
      
      // Clear video source
      if (videoRef.current) {
        videoRef.current.srcObject = null;
      }
      
      // Stop monitoring intervals
      if (monitoringInterval) {
        if (typeof monitoringInterval === 'object') {
          clearInterval(monitoringInterval.recognition);
          clearInterval(monitoringInterval.fps);
        } else {
          clearInterval(monitoringInterval);
        }
        setMonitoringInterval(null);
      }
      
      // Reset frame rate
      setFrameRate(0);
      frameCountRef.current = 0;
      
      // Notify server to stop monitoring
      try {
        await fetch(`${API_BASE}/doorbell/camera/stop-monitoring`, {
          method: 'POST'
        });
      } catch (e) {
        console.warn('Failed to notify server about stopping monitoring:', e);
      }
      
      setIsMonitoring(false);
      setStreamError(null);
      showMessage('Live camera monitoring stopped', 'info');
      
    } catch (error) {
      console.error('Error stopping camera monitoring:', error);
      showMessage('Failed to stop camera monitoring', 'error');
    }
  };

  // Enhanced capture function that works with live video
  const captureAndRecognizeFromVideo = async () => {
    if (!videoRef.current || !canvasRef.current) {
      console.log('Video or canvas ref not available');
      return;
    }
    
    try {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');
      
      // Check if video is actually playing
      if (video.readyState < 2) {
        console.log('Video not ready for capture, readyState:', video.readyState);
        return;
      }
      
      // Set canvas size to optimal resolution for face recognition
      const targetWidth = 640;
      const targetHeight = 480;
      canvas.width = targetWidth;
      canvas.height = targetHeight;
      
      console.log(`Capturing frame: ${canvas.width}x${canvas.height} from video ${video.videoWidth}x${video.videoHeight}`);
      
      // Clear canvas and draw video frame with better quality settings
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = 'high';
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      
      // Convert canvas to blob with higher quality for better face recognition
      canvas.toBlob(async (blob) => {
        if (!blob) {
          console.error('Failed to create blob from canvas');
          return;
        }
        
        console.log('Sending frame for recognition, blob size:', blob.size, 'bytes');
        
        const formData = new FormData();
        formData.append('image', blob, 'frame.jpg');
        formData.append('doorbell_mode', 'true');
        
        try {
          const response = await fetch(`${API_BASE}/face-recognition/recognize`, {
            method: 'POST',
            body: formData,
          });
          
          console.log('Recognition response status:', response.status);
          
          if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
          }
          
          const data = await response.json();
          console.log('Recognition result:', data);
          
          if (data.success) {
            // Update recognition results with frame capture
            const enhancedData = {
              ...data,
              captured_image: canvas.toDataURL('image/jpeg', 0.8),
              timestamp: new Date().toISOString()
            };
            
            setLastRecognition(enhancedData);
            
            // Check if door should be opened
            const shouldOpenDoor = data.recognized_persons.some(person => 
              person.access_level === 'admin' || person.access_level === 'standard'
            );
            
            if (shouldOpenDoor && data.recognized_persons.length > 0) {
              const recognizedNames = data.recognized_persons.map(p => p.name).join(', ');
              showMessage(`🚪 Door opened automatically for: ${recognizedNames}`, 'success');
            } else if (data.faces_detected > 0 && data.recognized_persons.length === 0) {
              showMessage('👤 Unknown person detected at door', 'warning');
            } else if (data.faces_detected === 0) {
              console.log('No faces detected in frame');
            }
            
            // Show confidence scores for debugging
            if (data.recognized_persons && data.recognized_persons.length > 0) {
              data.recognized_persons.forEach(person => {
                console.log(`Person: ${person.name}, Confidence: ${(person.confidence * 100).toFixed(1)}%`);
              });
            }
          } else {
            console.error('Recognition failed:', data.detail || 'Unknown error');
            showMessage('Face recognition failed: ' + (data.detail || 'Unknown error'), 'error');
          }
        } catch (error) {
          console.error('Error in live recognition:', error);
          showMessage('Face recognition error: ' + error.message, 'error');
        }
      }, 'image/jpeg', 0.95); // Higher quality for better face recognition
      
    } catch (error) {
      console.error('Error capturing from video:', error);
      showMessage('Video capture error: ' + error.message, 'error');
    }
  };

  const captureAndRecognize = async () => {
    try {
      const response = await fetch(`${API_BASE}/doorbell/camera/capture-and-recognize`, {
        method: 'POST'
      });
      
      const data = await response.json();
      
      if (data.success) {
        setLastRecognition(data);
        
        // If door was opened automatically, show message
        if (data.door_opened && data.recognized_persons.length > 0) {
          const recognizedNames = data.recognized_persons.map(p => p.name).join(', ');
          showMessage(`🚪 Door opened automatically for: ${recognizedNames}`, 'success');
        } else if (data.faces_detected > 0 && data.recognized_persons.length === 0) {
          showMessage('👤 Unknown person detected at door', 'warning');
        }
      }
    } catch (error) {
      console.error('Error in live recognition:', error);
      // Don't show error messages during monitoring to avoid spam
    }
  };

  // Video stream effect - handle connection and playback
  useEffect(() => {
    if (videoStream && videoRef.current) {
      console.log('Setting up video stream');
      const video = videoRef.current;
      video.srcObject = videoStream;
      
      // Force video to play
      const playVideo = async () => {
        try {
          await video.play();
          console.log('Video is now playing');
          setStreamError(null);
        } catch (error) {
          console.error('Video play error:', error);
          setStreamError('Failed to play video. Try clicking the video area.');
        }
      };

      // Wait for metadata to load, then play
      if (video.readyState >= 1) {
        playVideo();
      } else {
        video.addEventListener('loadedmetadata', playVideo, { once: true });
      }

      return () => {
        video.removeEventListener('loadedmetadata', playVideo);
      };
    }
  }, [videoStream]);

  // Cleanup interval on unmount
  useEffect(() => {
    return () => {
      if (monitoringInterval) {
        if (typeof monitoringInterval === 'object') {
          clearInterval(monitoringInterval.recognition);
          clearInterval(monitoringInterval.fps);
        } else {
          clearInterval(monitoringInterval);
        }
      }
      // Cleanup video stream
      if (videoStream) {
        videoStream.getTracks().forEach(track => track.stop());
      }
    };
  }, [monitoringInterval, videoStream]);

  const getPersonPhoto = (personName) => {
    return `${API_BASE}/face-recognition/persons/${encodeURIComponent(personName)}/photo`;
  };

  const getAccessLevelColor = (level) => {
    switch (level) {
      case 'admin': return '#ff6b6b';
      case 'standard': return '#4ecdc4';
      case 'guest': return '#45b7d1';
      default: return '#95a5a6';
    }
  };

  const getAccessLevelIcon = (level) => {
    switch (level) {
      case 'admin': return '👑';
      case 'standard': return '🏠';
      case 'guest': return '👤';
      default: return '❓';
    }
  };

  return (
    <>
      <style>
        {`
          @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
          }
        `}
      </style>
      <div style={{
        fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
        maxWidth: '1200px',
        margin: '0 auto',
        padding: '24px',
        backgroundColor: '#f8fafc',
        color: '#1a202c'
      }}>
      <div style={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        padding: '24px',
        borderRadius: '16px',
        marginBottom: '24px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <h2 style={{ margin: 0, fontSize: '28px', fontWeight: '700', color: 'white' }}>
          🔍 Smart Face Recognition System
        </h2>
        {systemStatus && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: systemStatus.system_status === 'operational' ? '#00d4aa' : '#ff6b6b',
              display: 'inline-block'
            }}></span>
            <span style={{ fontSize: '14px', opacity: 0.9, color: 'white' }}>
              {systemStatus.known_persons_count} known persons • 
              Confidence: {Math.round(systemStatus.confidence_threshold * 100)}%
            </span>
          </div>
        )}
      </div>

      {message && (
        <div style={{
          padding: '12px 16px',
          borderRadius: '8px',
          marginBottom: '16px',
          backgroundColor: message.type === 'success' ? '#d1fae5' : 
                         message.type === 'error' ? '#fee2e2' : 
                         message.type === 'warning' ? '#fef3c7' : '#dbeafe',
          color: message.type === 'success' ? '#065f46' : 
                 message.type === 'error' ? '#991b1b' : 
                 message.type === 'warning' ? '#92400e' : '#1e40af',
          border: `1px solid ${message.type === 'success' ? '#a7f3d0' : 
                              message.type === 'error' ? '#fecaca' : 
                              message.type === 'warning' ? '#fde68a' : '#bfdbfe'}`,
          fontWeight: '500'
        }}>
          {message.text}
        </div>
      )}

      <div style={{ display: 'flex', gap: '4px', marginBottom: '24px' }}>
        {['manage', 'recognize', 'live-camera'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              padding: '12px 24px',
              border: 'none',
              borderRadius: '8px',
              backgroundColor: activeTab === tab ? '#4f46e5' : 'white',
              color: activeTab === tab ? 'white' : '#374151',
              cursor: 'pointer',
              fontWeight: '600',
              fontSize: '14px',
              transition: 'all 0.2s',
              boxShadow: activeTab === tab ? '0 4px 12px rgba(79, 70, 229, 0.4)' : '0 1px 3px rgba(0, 0, 0, 0.1)'
            }}
          >
            {tab === 'manage' && '👥 Manage Persons'}
            {tab === 'recognize' && '🔍 Face Recognition'}
            {tab === 'live-camera' && '📹 Live Doorbell'}
          </button>
        ))}
      </div>

      <div style={{
        backgroundColor: 'white',
        borderRadius: '12px',
        padding: '24px',
        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
        minHeight: '500px',
        color: '#1a202c'
      }}>
        {activeTab === 'manage' && (
          <div>
            <div style={{ marginBottom: '32px' }}>
              <h3 style={{ marginBottom: '16px', color: '#111827', fontSize: '20px', fontWeight: '600' }}>Add New Person</h3>
              <div style={{ display: 'grid', gap: '16px', maxWidth: '500px' }}>
                <div style={{ display: 'flex', gap: '12px' }}>
                  <input
                    type="text"
                    placeholder="Person's name"
                    value={newPersonName}
                    onChange={(e) => setNewPersonName(e.target.value)}
                    style={{
                      flex: 1,
                      padding: '12px',
                      border: '2px solid #d1d5db',
                      borderRadius: '8px',
                      fontSize: '14px',
                      color: '#111827',
                      backgroundColor: 'white',
                      fontWeight: '500'
                    }}
                  />
                  <select
                    value={newPersonAccessLevel}
                    onChange={(e) => setNewPersonAccessLevel(e.target.value)}
                    style={{
                      padding: '12px',
                      border: '2px solid #d1d5db',
                      borderRadius: '8px',
                      fontSize: '14px',
                      backgroundColor: 'white',
                      color: '#111827',
                      fontWeight: '500'
                    }}
                  >
                    <option value="standard">🏠 Standard Access</option>
                    <option value="admin">👑 Admin Access</option>
                    <option value="guest">👤 Guest Access</option>
                  </select>
                </div>
                <textarea
                  placeholder="Notes (optional)"
                  value={newPersonNotes}
                  onChange={(e) => setNewPersonNotes(e.target.value)}
                  rows="2"
                  style={{
                    padding: '12px',
                    border: '2px solid #d1d5db',
                    borderRadius: '8px',
                    fontSize: '14px',
                    resize: 'vertical',
                    color: '#111827',
                    backgroundColor: 'white',
                    fontWeight: '500'
                  }}
                />
                <div>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handlePhotoSelect}
                    ref={photoInputRef}
                    style={{
                      marginBottom: '12px',
                      padding: '8px',
                      border: '2px solid #d1d5db',
                      borderRadius: '8px',
                      width: '100%',
                      color: '#111827',
                      backgroundColor: 'white',
                      fontWeight: '500'
                    }}
                  />
                  {photoPreview && (
                    <div style={{
                      border: '2px dashed #d1d5db',
                      borderRadius: '8px',
                      padding: '16px',
                      textAlign: 'center'
                    }}>
                      <img
                        src={photoPreview}
                        alt="Preview"
                        style={{
                          maxWidth: '200px',
                          maxHeight: '200px',
                          borderRadius: '8px'
                        }}
                      />
                    </div>
                  )}
                </div>
                <button
                  onClick={addKnownPerson}
                  disabled={loading}
                  style={{
                    padding: '12px 24px',
                    backgroundColor: loading ? '#9ca3af' : '#10b981',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    cursor: loading ? 'not-allowed' : 'pointer',
                    fontWeight: '600',
                    fontSize: '14px',
                    transition: 'background-color 0.2s'
                  }}
                >
                  {loading ? 'Adding...' : 'Add Person'}
                </button>
              </div>
            </div>

            <div>
              <h3 style={{ marginBottom: '16px', color: '#111827', fontSize: '20px', fontWeight: '600' }}>
                Known Persons ({knownPersons.length})
              </h3>
              {loading && knownPersons.length === 0 ? (
                <div style={{ textAlign: 'center', color: '#374151', padding: '32px', fontSize: '16px', fontWeight: '500' }}>
                  Loading known persons...
                </div>
              ) : (
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
                  gap: '16px'
                }}>
                  {knownPersons.map((person) => (
                    <div
                      key={person.name}
                      style={{
                        border: '2px solid #e5e7eb',
                        borderRadius: '12px',
                        overflow: 'hidden',
                        backgroundColor: 'white',
                        boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)'
                      }}
                    >
                      <div style={{ height: '200px', overflow: 'hidden' }}>
                        <img
                          src={getPersonPhoto(person.name)}
                          alt={person.name}
                          style={{
                            width: '100%',
                            height: '100%',
                            objectFit: 'cover'
                          }}
                          onError={(e) => {
                            e.target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iI2Y4ZjlmYSIvPjx0ZXh0IHg9IjEwMCIgeT0iMTAwIiBmb250LWZhbWlseT0iQXJpYWwsIHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMTYiIGZpbGw9IiM2Yzc1N2QiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj5ObyBJbWFnZTwvdGV4dD48L3N2Zz4=';
                          }}
                        />
                      </div>
                      <div style={{ padding: '16px' }}>
                        <h4 style={{ margin: '0 0 8px 0', color: '#111827', fontSize: '18px', fontWeight: '600' }}>{person.name}</h4>
                        <div
                          style={{
                            display: 'inline-block',
                            padding: '4px 8px',
                            borderRadius: '12px',
                            backgroundColor: getAccessLevelColor(person.access_level),
                            color: 'white',
                            fontSize: '12px',
                            fontWeight: '600',
                            marginBottom: '8px'
                          }}
                        >
                          {getAccessLevelIcon(person.access_level)} {person.access_level}
                        </div>
                        {person.notes && (
                          <p style={{ margin: '8px 0', color: '#374151', fontSize: '14px', fontWeight: '500' }}>
                            {person.notes}
                          </p>
                        )}
                        <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '12px', fontWeight: '500' }}>
                          Added: {new Date(person.added_date).toLocaleDateString()}
                        </div>
                        <button
                          onClick={() => removePerson(person.name)}
                          disabled={loading}
                          style={{
                            padding: '8px 16px',
                            backgroundColor: '#ef4444',
                            color: 'white',
                            border: 'none',
                            borderRadius: '6px',
                            cursor: loading ? 'not-allowed' : 'pointer',
                            fontSize: '12px',
                            fontWeight: '600'
                          }}
                        >
                          🗑️ Remove
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'recognize' && (
          <div>
            <h3 style={{ marginBottom: '16px', color: '#111827', fontSize: '20px', fontWeight: '600' }}>Face Recognition Test</h3>
            <div style={{ maxWidth: '500px' }}>
              <input
                type="file"
                accept="image/*"
                onChange={handleRecognitionImageSelect}
                ref={recognitionInputRef}
                style={{
                  marginBottom: '16px',
                  padding: '8px',
                  border: '2px solid #d1d5db',
                  borderRadius: '8px',
                  width: '100%',
                  color: '#111827',
                  backgroundColor: 'white',
                  fontWeight: '500'
                }}
              />
              {recognitionPreview && (
                <div style={{
                  border: '2px dashed #d1d5db',
                  borderRadius: '8px',
                  padding: '16px',
                  textAlign: 'center',
                  marginBottom: '16px'
                }}>
                  <img
                    src={recognitionPreview}
                    alt="Recognition Preview"
                    style={{
                      maxWidth: '400px',
                      maxHeight: '300px',
                      borderRadius: '8px'
                    }}
                  />
                </div>
              )}
              <button
                onClick={recognizeFaces}
                disabled={loading}
                style={{
                  padding: '12px 24px',
                  backgroundColor: loading ? '#9ca3af' : '#3b82f6',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  fontWeight: '600',
                  fontSize: '14px',
                  marginBottom: '24px'
                }}
              >
                {loading ? 'Recognizing...' : '🔍 Recognize Faces'}
              </button>
            </div>

            {recognitionResults && (
              <div style={{
                border: '2px solid #e5e7eb',
                borderRadius: '8px',
                padding: '16px',
                backgroundColor: '#f9fafb'
              }}>
                <h4 style={{ margin: '0 0 12px 0', color: '#111827', fontSize: '18px', fontWeight: '600' }}>Recognition Results</h4>
                <div style={{ marginBottom: '16px', fontSize: '14px', color: '#374151', fontWeight: '500' }}>
                  Faces detected: {recognitionResults.faces_detected} • 
                  Timestamp: {new Date(recognitionResults.timestamp).toLocaleString()}
                </div>
                <div style={{ display: 'grid', gap: '8px' }}>
                  {recognitionResults.recognized_persons.map((person, index) => (
                    <div
                      key={index}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '12px',
                        backgroundColor: 'white',
                        borderRadius: '8px',
                        border: '2px solid #e5e7eb'
                      }}
                    >
                      <span style={{ fontWeight: '600', color: '#111827', fontSize: '16px' }}>{person.name}</span>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <span style={{ fontSize: '14px', color: '#374151', fontWeight: '500' }}>
                          {(person.confidence * 100).toFixed(1)}% confidence
                        </span>
                        <div
                          style={{
                            padding: '4px 8px',
                            borderRadius: '12px',
                            backgroundColor: getAccessLevelColor(person.access_level),
                            color: 'white',
                            fontSize: '12px',
                            fontWeight: '600'
                          }}
                        >
                          {getAccessLevelIcon(person.access_level)} {person.access_level}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'live-camera' && (
          <div>
            <h3 style={{ marginBottom: '16px', color: '#111827', fontSize: '20px', fontWeight: '600' }}>📹 Live Smart Doorbell</h3>
            <p style={{ color: '#374151', marginBottom: '24px', lineHeight: 1.6, fontSize: '16px', fontWeight: '500' }}>
              Live camera feed with real-time face recognition. The system automatically monitors visitors 
              and opens the door for known persons with appropriate access levels.
            </p>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>
              {/* Live Camera Feed */}
              <div>
                <h4 style={{ marginBottom: '12px', color: '#111827', fontSize: '18px', fontWeight: '600' }}>📺 Live Camera Feed</h4>
                <div style={{
                  border: '2px solid #d1d5db',
                  borderRadius: '12px',
                  overflow: 'hidden',
                  backgroundColor: '#000',
                  minHeight: '300px',
                  position: 'relative',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  {isMonitoring && !streamError ? (
                    <>
                      <video
                        ref={videoRef}
                        autoPlay
                        playsInline
                        muted
                        onClick={async () => {
                          if (videoRef.current) {
                            try {
                              await videoRef.current.play();
                              setStreamError(null);
                            } catch (e) {
                              console.error('Manual play failed:', e);
                            }
                          }
                        }}
                        style={{
                          width: '100%',
                          height: 'auto',
                          maxHeight: '400px',
                          objectFit: 'cover',
                          borderRadius: '8px',
                          cursor: 'pointer'
                        }}
                        onLoadedMetadata={() => {
                          console.log('Video metadata loaded');
                        }}
                        onCanPlay={() => {
                          console.log('Video can play');
                        }}
                        onPlaying={() => {
                          console.log('Video is playing');
                          setStreamError(null);
                        }}
                        onTimeUpdate={() => {
                          frameCountRef.current += 1;
                        }}
                        onError={(e) => {
                          console.error('Video error:', e);
                          setStreamError('Video stream error');
                        }}
                      />
                      <canvas
                        ref={canvasRef}
                        style={{
                          display: 'none'
                        }}
                      />
                      {/* Live indicator with frame rate */}
                      <div style={{
                        position: 'absolute',
                        top: '12px',
                        right: '12px',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '4px'
                      }}>
                        <div style={{
                          backgroundColor: 'rgba(239, 68, 68, 0.9)',
                          color: 'white',
                          padding: '4px 8px',
                          borderRadius: '4px',
                          fontSize: '12px',
                          fontWeight: '600',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px'
                        }}>
                          <div style={{
                            width: '6px',
                            height: '6px',
                            borderRadius: '50%',
                            backgroundColor: '#fff',
                            animation: 'pulse 1s infinite'
                          }}></div>
                          LIVE
                        </div>
                        {frameRate > 0 && (
                          <div style={{
                            backgroundColor: 'rgba(0, 0, 0, 0.7)',
                            color: 'white',
                            padding: '2px 6px',
                            borderRadius: '3px',
                            fontSize: '10px',
                            textAlign: 'center'
                          }}>
                            {frameRate} FPS
                          </div>
                        )}
                      </div>
                    </>
                  ) : streamError ? (
                    <div style={{
                      color: '#ef4444',
                      textAlign: 'center',
                      padding: '40px',
                      fontSize: '16px',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      gap: '12px'
                    }}>
                      <div style={{ fontSize: '48px' }}>📹❌</div>
                      <div style={{ fontWeight: '600' }}>Camera Error</div>
                      <div style={{ fontSize: '14px', color: '#6b7280' }}>{streamError}</div>
                      <button
                        onClick={() => {
                          setStreamError(null);
                          if (!isMonitoring) startCameraMonitoring();
                        }}
                        style={{
                          padding: '8px 16px',
                          backgroundColor: '#3b82f6',
                          color: 'white',
                          border: 'none',
                          borderRadius: '6px',
                          fontSize: '14px',
                          cursor: 'pointer'
                        }}
                      >
                        🔄 Retry
                      </button>
                    </div>
                  ) : (
                    <div style={{
                      color: '#9ca3af',
                      textAlign: 'center',
                      padding: '40px',
                      fontSize: '16px',
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      gap: '12px'
                    }}>
                      <div style={{ fontSize: '48px' }}>📹</div>
                      <div style={{ fontWeight: '600' }}>Camera Ready</div>
                      <div style={{ fontSize: '14px' }}>Click "Start Monitoring" to begin live surveillance</div>
                      <div style={{ 
                        fontSize: '12px', 
                        color: '#6b7280', 
                        marginTop: '8px',
                        padding: '8px',
                        backgroundColor: '#f3f4f6',
                        borderRadius: '6px'
                      }}>
                        💡 If video doesn't show, click on the video area to manually start playback
                      </div>
                    </div>
                  )}
                </div>
                
                {/* Camera Controls */}
                <div style={{ marginTop: '16px', display: 'flex', gap: '12px' }}>
                  <button
                    onClick={isMonitoring ? stopCameraMonitoring : startCameraMonitoring}
                    disabled={loading}
                    style={{
                      padding: '12px 24px',
                      backgroundColor: loading ? '#9ca3af' : isMonitoring ? '#ef4444' : '#10b981',
                      color: 'white',
                      border: 'none',
                      borderRadius: '8px',
                      cursor: loading ? 'not-allowed' : 'pointer',
                      fontWeight: '600',
                      fontSize: '14px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px'
                    }}
                  >
                    {loading ? '⏳ Loading...' : isMonitoring ? '⏹️ Stop Monitoring' : '▶️ Start Monitoring'}
                  </button>
                  
                  {isMonitoring && (
                    <button
                      onClick={captureAndRecognizeFromVideo}
                      disabled={loading}
                      style={{
                        padding: '12px 20px',
                        backgroundColor: '#3b82f6',
                        color: 'white',
                        border: 'none',
                        borderRadius: '8px',
                        cursor: loading ? 'not-allowed' : 'pointer',
                        fontWeight: '600',
                        fontSize: '14px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px'
                      }}
                    >
                      📸 Test Capture
                    </button>
                  )}
                  
                  <div style={{
                    padding: '12px 16px',
                    borderRadius: '8px',
                    backgroundColor: isMonitoring ? '#d1fae5' : '#fee2e2',
                    color: isMonitoring ? '#065f46' : '#991b1b',
                    fontSize: '14px',
                    fontWeight: '600',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}>
                    <div style={{
                      width: '8px',
                      height: '8px',
                      borderRadius: '50%',
                      backgroundColor: isMonitoring ? '#10b981' : '#ef4444'
                    }}></div>
                    {isMonitoring ? 'LIVE MONITORING' : 'MONITORING STOPPED'}
                  </div>
                </div>
              </div>

              {/* Recognition Results */}
              <div>
                <h4 style={{ marginBottom: '12px', color: '#111827', fontSize: '18px', fontWeight: '600' }}>🔍 Recognition Status</h4>
                <div style={{
                  border: '2px solid #e5e7eb',
                  borderRadius: '12px',
                  padding: '16px',
                  backgroundColor: '#f9fafb',
                  minHeight: '300px'
                }}>
                  {lastRecognition ? (
                    <div>
                      <div style={{
                        marginBottom: '16px',
                        padding: '12px',
                        borderRadius: '8px',
                        backgroundColor: lastRecognition.door_opened ? '#d1fae5' : '#fef3c7',
                        color: lastRecognition.door_opened ? '#065f46' : '#92400e',
                        fontWeight: '600',
                        fontSize: '16px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px'
                      }}>
                        {lastRecognition.door_opened ? '🚪✅ Door Opened' : '🚪🔒 Door Locked'}
                      </div>

                      <div style={{ marginBottom: '16px', fontSize: '14px', color: '#374151' }}>
                        <strong>Last Check:</strong> {new Date(lastRecognition.timestamp).toLocaleTimeString()}<br />
                        <strong>Faces Detected:</strong> {lastRecognition.faces_detected}
                      </div>

                      {lastRecognition.recognized_persons.length > 0 ? (
                        <div>
                          <h5 style={{ margin: '0 0 12px 0', color: '#111827', fontSize: '16px', fontWeight: '600' }}>Recognized Persons:</h5>
                          {lastRecognition.recognized_persons.map((person, index) => (
                            <div
                              key={index}
                              style={{
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                padding: '8px 12px',
                                backgroundColor: 'white',
                                borderRadius: '6px',
                                border: '1px solid #e5e7eb',
                                marginBottom: '8px'
                              }}
                            >
                              <span style={{ fontWeight: '600', color: '#111827' }}>{person.name}</span>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <span style={{ fontSize: '12px', color: '#374151' }}>
                                  {(person.confidence * 100).toFixed(1)}%
                                </span>
                                <div
                                  style={{
                                    padding: '2px 6px',
                                    borderRadius: '10px',
                                    backgroundColor: getAccessLevelColor(person.access_level),
                                    color: 'white',
                                    fontSize: '10px',
                                    fontWeight: '600'
                                  }}
                                >
                                  {getAccessLevelIcon(person.access_level)}
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : lastRecognition.faces_detected > 0 ? (
                        <div style={{
                          padding: '12px',
                          borderRadius: '8px',
                          backgroundColor: '#fef3c7',
                          color: '#92400e',
                          fontWeight: '600',
                          textAlign: 'center'
                        }}>
                          👤 Unknown person detected
                        </div>
                      ) : (
                        <div style={{
                          padding: '12px',
                          borderRadius: '8px',
                          backgroundColor: '#f3f4f6',
                          color: '#6b7280',
                          fontWeight: '600',
                          textAlign: 'center'
                        }}>
                          👁️ No faces detected
                        </div>
                      )}

                      {lastRecognition.captured_image && (
                        <div style={{ marginTop: '16px' }}>
                          <h5 style={{ margin: '0 0 8px 0', color: '#111827', fontSize: '14px', fontWeight: '600' }}>Last Captured Frame:</h5>
                          <img
                            src={lastRecognition.captured_image}
                            alt="Last Captured"
                            style={{
                              width: '100%',
                              maxHeight: '120px',
                              objectFit: 'cover',
                              borderRadius: '6px',
                              border: '1px solid #e5e7eb'
                            }}
                          />
                        </div>
                      )}
                    </div>
                  ) : (
                    <div style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      justifyContent: 'center',
                      height: '100%',
                      color: '#9ca3af',
                      textAlign: 'center'
                    }}>
                      <div style={{ fontSize: '48px', marginBottom: '16px' }}>🔍</div>
                      <div style={{ fontSize: '16px', fontWeight: '600' }}>
                        {isMonitoring ? 'Monitoring active - checking for faces every 2 seconds...' : 'Start monitoring to see recognition results'}
                      </div>
                      {isMonitoring && (
                        <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '8px' }}>
                          Confidence threshold: 40% | Check console (F12) for detailed logs
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Instructions */}
            <div style={{
              backgroundColor: '#eff6ff',
              border: '2px solid #bfdbfe',
              borderRadius: '12px',
              padding: '16px',
              color: '#1e40af'
            }}>
              <h4 style={{ margin: '0 0 8px 0', fontSize: '16px', fontWeight: '600' }}>📋 How it works:</h4>
              <ul style={{ margin: 0, paddingLeft: '20px', lineHeight: 1.6 }}>
                <li>Click "Start Monitoring" to begin live camera surveillance</li>
                <li>The system automatically captures frames every 2 seconds for recognition</li>
                <li>Use "Test Capture" button to manually test face recognition while monitoring</li>
                <li>Recognition confidence threshold lowered to 40% for better live video detection</li>
                <li>When a known person is detected, the door opens automatically</li>
                <li>Unknown persons trigger an alert but keep the door locked</li>
                <li>Check browser console (F12) for detailed debugging and confidence scores</li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
    </>
  );
};

export default FaceRecognition; 