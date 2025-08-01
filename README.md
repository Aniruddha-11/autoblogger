# AI Blog Generator

An intelligent blog generation platform powered by AI that creates SEO-optimized content with integrated images.

## 🚀 Features

- **Dual Processing Modes**: Manual step-by-step or bulk batch processing
- **AI-Powered Content**: Gemini AI integration for quality blog generation
- **Image Integration**: Multi-source image search and strategic placement
- **SEO Optimization**: Automated metadata, slugs, and structured data
- **Session Management**: Resume interrupted workflows
- **Export Options**: HTML, TXT, JSON formats

## 🏗️ Architecture

### Backend (Flask/Python)
- Flask API with modular route blueprints
- MongoDB for data persistence
- Gemini AI for content generation
- Multi-step blog creation pipeline

### Frontend (React)
- Modern React application
- Real-time progress tracking
- Responsive design
- Session restoration

## 🛠️ Technology Stack

- **Backend**: Flask, MongoDB, Gemini AI, BeautifulSoup
- **Frontend**: React, CSS3, Axios
- **Deployment**: Google Cloud Platform
- **Database**: MongoDB Atlas

## 📦 Installation

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
