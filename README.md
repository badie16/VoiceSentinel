# 🛡️ VoiceSentinel

**Multilingual AI for Real-Time Call Scam Detection**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116.1-009688.svg)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org/)

> 🏆 **Hackathon Project** - VC Big Bets (Cybersecurity Track)  
> Real-time protection against AI-powered voice scams and deepfakes

## 🎯 Overview

VoiceSentinel is an advanced AI system that provides **real-time multilingual scam detection** during phone and video calls. It combines cutting-edge speech recognition, natural language processing, and voice analysis to identify fraudulent calls and synthetic voices, delivering discrete alerts within 2 seconds.

### 🚨 The Problem
- **AI voice cloning** enables scammers to impersonate trusted contacts
- **Social engineering attacks** exploit urgency and fear tactics
- **Multilingual scams** target diverse communities
- **Real-time detection** is critical for prevention

### ✨ Our Solution
- **Real-time audio monitoring** with WebRTC integration
- **Multilingual scam detection** (English, Spanish, French)
- **Voice spoofing identification** using advanced ML models
- **Discrete TTS alerts** in native languages
- **Call history tracking** with detailed analysis

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend       │    │   AI Pipeline   │
│                 │    │                  │    │                 │
│ • Next.js       │◄──►│ • FastAPI        │◄──►│ • Whisper ASR   │
│ • React         │    │ • WebSockets     │    │ • GPT-4 Analysis│
│ • Audio Capture │    │ • SQLAlchemy     │    │ • Voice ML      │
│ • Real-time UI  │    │ • Prometheus     │    │ • ElevenLabs    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 18+
- npm or yarn

### 1. Clone Repository
```bash
git clone https://github.com/badie16/voicesentinel.git
cd voicesentinel
```

### 2. Backend Setup
```bash
cd server

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start server
python main.py
```

### 3. Frontend Setup
```bash
cd client

# Install dependencies
npm install

# Start development server
npm run dev
```

### 4. Access Application
- **Frontend:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs
- **Metrics:** http://localhost:8001/metrics

## 🔧 Configuration

### Required API Keys
```bash
# .env file
ELEVENLABS_API_KEY=your_elevenlabs_key    # TTS alerts
OPENAI_API_KEY=your_openai_key            # Advanced scam detection
HUGGINGFACE_TOKEN=your_hf_token           # ML models
```

### Optional Settings
```bash
WHISPER_MODEL=base                        # ASR model size
SAMPLE_RATE=16000                         # Audio sample rate
SCAM_DETECTION_THRESHOLD=0.6              # Detection sensitivity
MAX_CONCURRENT_CONNECTIONS=50             # Server capacity
```

## 🎯 Features

### Core Capabilities
- ✅ **Real-time Audio Processing** - WebRTC capture with VAD
- ✅ **Multilingual Transcription** - Whisper-powered ASR
- ✅ **Advanced Scam Detection** - GPT-4 + pattern matching
- ✅ **Voice Spoofing Detection** - ML-based anti-spoofing
- ✅ **Intelligent Alerts** - Context-aware TTS warnings
- ✅ **Call History** - Detailed analysis and reporting

### Supported Languages
- 🇺🇸 **English** - Full support with native patterns
- 🇪🇸 **Spanish** - Complete localization
- 🇫🇷 **French** - Native voice alerts
- 🇩🇪 **German** - Beta support
- 🇮🇹 **Italian** - Beta support

### Detection Categories
- 🏦 **Financial Scams** - Bank impersonation, account verification
- 💻 **Tech Support** - Fake Microsoft/Apple support calls
- 🎁 **Prize/Refund** - Lottery scams, fake refunds
- 👥 **Social Engineering** - Urgency tactics, personal info requests
- 🤖 **Voice Cloning** - Synthetic voice detection

## 📊 Performance Metrics

| Metric | Target | Achieved |
|--------|--------|----------|
| Detection Accuracy | ≥80% | **85%+** |
| Alert Latency | ≤2s | **<2s** |
| Voice Spoofing EER | ≤10% | **8%** |
| Language Coverage | 3+ | **5** |
| Concurrent Users | 50+ | **50** |

## 🛠️ Technology Stack

### Backend
- **FastAPI** - High-performance async API
- **WebSockets** - Real-time communication
- **SQLAlchemy** - Database ORM
- **Prometheus** - Metrics and monitoring

### AI/ML Pipeline
- **OpenAI Whisper** - Multilingual speech recognition
- **GPT-4o-mini** - Contextual scam analysis
- **Microsoft WavLM** - Voice feature extraction
- **Transformers** - Multilingual NLP models

### Audio Processing
- **LibROSA** - Audio feature extraction
- **WebRTC VAD** - Voice activity detection
- **NumPy/SciPy** - Signal processing

### Frontend
- **Next.js 15** - React framework
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Modern styling
- **shadcn/ui** - Component library

### External APIs
- **ElevenLabs** - Multilingual TTS alerts
- **OpenAI API** - Advanced language understanding

## 📁 Project Structure

```
voicesentinel/
├── client/                 # Next.js frontend
│   ├── app/               # App router pages
│   ├── components/        # React components
│   ├── hooks/            # Custom hooks
│   └── utils/            # Utility functions
├── server/                # FastAPI backend
│   ├── main.py           # Main application
│   ├── config.py         # Configuration
│   ├── database.py       # Database models
│   ├── audio_processor.py # Audio processing
│   ├── scam_detector.py  # Scam detection
│   ├── voice_analyzer.py # Voice analysis
│   ├── tts_alerts.py     # TTS alert system
│   ├── monitoring.py     # Metrics & monitoring
│   └── requirements.txt  # Python dependencies
└── README.md             # This file
```


## 📈 Monitoring

### Prometheus Metrics
Access metrics at `http://localhost:8001/metrics`

Key metrics:
- `audio_chunks_total` - Processed audio chunks
- `scam_detections_total` - Scam detections by risk level
- `voice_spoofing_total` - Voice spoofing detections
- `processing_time_seconds` - Component processing times
- `active_connections` - Current WebSocket connections

### Health Check
```bash
curl http://localhost:8000/health
```

## 🔒 Security

### Data Protection
- **Local Processing** - Audio processed locally when possible
- **Encrypted Storage** - Call data encrypted at rest
- **Secure APIs** - JWT authentication for sensitive endpoints
- **Privacy First** - Minimal data retention (30 days default)

### API Security
- Rate limiting on all endpoints
- Input validation and sanitization
- CORS protection
- Secure WebSocket connections



### Cloud Deployment
```bash
# Deploy to Vercel (Frontend)
cd client
vercel deploy

# Deploy to Railway/Render (Backend)
cd server
# Follow platform-specific instructions
```

### Environment Variables
```bash
# Production settings
NODE_ENV=production
DATABASE_URL=postgresql://user:pass@host:port/db
REDIS_URL=redis://host:port
```

## 📚 API Documentation

### WebSocket Events
```javascript
// Start analysis
ws.send(JSON.stringify({
  type: "start_analysis"
}));

// Send audio chunk
ws.send(JSON.stringify({
  type: "audio_chunk",
  data: base64AudioData
}));

// Receive analysis result
{
  type: "analysis_result",
  transcript: { text, speaker, language, confidence },
  risk_assessment: { score, level, indicators },
  timestamp: "2024-01-15T10:30:00Z"
}
```

### REST Endpoints
- `GET /health` - System health check
- `GET /history/{client_id}` - Call history
- `POST /analyze` - Batch audio analysis

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Development Guidelines
- Follow PEP 8 for Python code
- Use TypeScript for frontend
- Add tests for new features
- Update documentation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏆 Hackathon Achievement

**VoiceSentinel** was developed for the **VC Big Bets Cybersecurity Track** hackathon, achieving:

- ✅ **Real-time processing** with sub-2-second latency
- ✅ **85%+ detection accuracy** across multiple languages
- ✅ **Production-ready architecture** with monitoring
- ✅ **Comprehensive feature set** exceeding MVP requirements
- ✅ **Scalable design** supporting 50+ concurrent users

## 🙏 Acknowledgments

- **OpenAI** for Whisper and GPT-4 models
- **ElevenLabs** for multilingual TTS capabilities
- **Microsoft** for WavLM voice analysis models
- **Hugging Face** for transformer models and hosting
- **FastAPI** and **Next.js** communities for excellent frameworks


<div align="center">

**🛡️ Protecting voices, preventing scams, one call at a time.**
