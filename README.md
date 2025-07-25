# 🎓 Thesis Helper - AI-Powered Academic Planning Tool

An intelligent thesis planning and management system that helps students break down their thesis work into manageable tasks, track progress, and stay motivated throughout their academic journey.

## ✨ Features

### 🤖 AI-Powered Planning
- **Two AI Options**: Choose between local Llama (via Ollama) or Google Gemini
- **Personalized Timelines**: AI generates custom schedules based on your field, deadline, and work style
- **Smart Task Breakdown**: Automatically breaks complex thesis phases into manageable daily tasks
- **Emergency Replanning**: Get back on track when life happens

### 📊 Progress Tracking
- **Real-time Updates**: Track your progress with Notion integration
- **Today's Tasks**: Clear view of what needs to be done today
- **Milestone Tracking**: Visual progress toward major deadlines
- **Analytics Dashboard**: Understand your productivity patterns

### 🔗 Integrations
- **Notion**: Automatic task and milestone management
- **Gmail**: Daily motivational emails and progress reports
- **Google Calendar**: Deadline reminders and milestone alerts (coming soon)

### 🎯 Student-Focused
- **Field-Specific Knowledge**: Tailored advice for Computer Science, Psychology, Biology, and more
- **Procrastination Support**: Built-in buffer time and motivation features
- **Writing Style Adaptation**: Plans adjust to your preferred writing approach
- **Timezone Support**: Works globally with proper time zone handling

### 🛠️ AI-Powered Task Assistance
- **Interactive Task Chat**: AI assistant helps you work through each task
- **Research Tools**: Search academic papers via Semantic Scholar
- **Citation Generator**: Auto-generate BibTeX citations from DOI/arXiv
- **PDF Summarizer**: Extract key insights from research papers
- **LaTeX OCR**: Convert mathematical equations from images to LaTeX
- **AI Content Detection**: Ensure academic integrity with AI detection
- **Ethics Tracking**: Built-in monitoring for responsible AI usage

### 🔬 Academic Research Tools
- **Paper Discovery**: Find relevant research using Semantic Scholar API
- **Citation Management**: Generate proper academic citations automatically  
- **Document Analysis**: Summarize PDFs and extract key information
- **Mathematical Support**: Convert handwritten equations to LaTeX
- **Content Verification**: Detect AI-generated content for integrity
- **Progress Tracking**: Monitor task completion with deliverable management

## 🏃‍♂️ Quick Start

### Prerequisites

- **Python 3.8+** (3.11+ recommended)
- **Node.js 16+** (for frontend)
- **Git**

### AI Provider Setup

Choose your preferred AI assistant:

#### Option 1: Ollama (Local Llama) - **Recommended** 🌟
**Pros**: Free, private, no API keys needed, works offline
**Cons**: Requires local installation (~4GB)

1. **Install Ollama**:
   ```bash
   # macOS
   brew install ollama
   
   # Linux/Windows - Download from: https://ollama.ai/download
   ```

2. **Download Llama model**:
   ```bash
   ollama pull llama3.1
   ```

3. **Start Ollama server**:
   ```bash
   ollama serve
   ```

#### Option 2: Google Gemini (Cloud API)
**Pros**: No local setup, always updated
**Cons**: Requires API key, internet connection, usage costs

1. **Get Gemini API Key**:
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key
   - Save it for the setup step

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/thesis_agent.git
   cd thesis_agent
   ```

2. **Backend Setup**:
   ```bash
   # Create and activate virtual environment
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. **Environment Configuration**:
   ```bash
   # Copy environment template
   cp env.template .env
   
   # Edit .env with your settings
   nano .env  # or your preferred editor
   ```

5. **Configure your `.env` file**:
   ```bash
   # Basic settings (always required)
   EMAIL_USER=your-email@gmail.com
   EMAIL_PASSWORD=your-gmail-app-password
   
   # Notion integration (required)
   NOTION_TOKEN=your-notion-integration-token
   
   # Only if using Gemini (optional)
   GEMINI_API_KEY=your-gemini-api-key
   
   # Google Calendar (optional - for future features)
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   ```

## 🔧 Detailed Setup Guide

### Getting API Keys

#### Gmail App Password (Required for email notifications)
1. Enable 2-factor authentication on your Google account
2. Go to Google Account settings → Security → 2-Step Verification → App passwords
3. Generate a new app password for "Mail"
4. Use this password in your `.env` file

#### Notion Integration Token (Required for task management)
1. Go to [Notion Integrations](https://www.notion.com/my-integrations)
2. Click "New Integration"
3. Name it "Thesis Helper" and select your workspace
4. Copy the integration token to your `.env` file

#### Gemini API Key (Optional - only if using Gemini)
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new project or select existing
3. Generate API key
4. Copy to your `.env` file

### Running the Application

1. **Start the backend server**:
   ```bash
   # From project root with venv activated
   cd backend
   python -m uvicorn app.simple_main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Start the frontend** (in a new terminal):
   ```bash
   cd frontend
   npm run dev
   ```

3. **Open your browser**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## 🎯 How to Use

### 1. Fill Out the Questionnaire
- **Personal Info**: Name, email, thesis topic
- **Thesis Details**: Field of study, deadline, description
- **Schedule**: Available hours, preferred working times
- **Work Style**: Procrastination level, focus duration, writing style
- **AI & Notifications**: Choose your AI assistant and email preferences

### 2. Choose Your AI Assistant
- **Ollama (Recommended)**: Free, private, runs locally
- **Gemini**: Cloud-based, requires API key

### 3. Generate Your Timeline
The AI will create a personalized timeline with:
- **Phases**: Major stages of your thesis
- **Tasks**: Daily actionable items
- **Milestones**: Key deadlines and deliverables
- **Time Estimates**: Realistic duration for each task

### 4. Sync with Notion
- Click "Create Notion Workspace" to set up your task management
- Use "Sync to Notion" to update your timeline
- View and manage tasks directly in Notion

### 5. Stay Motivated
- Receive daily email updates with progress and motivation
- Use the emergency replan feature if you fall behind
- Track your progress in real-time

## 🛠️ Development

### Project Structure
```
thesis_agent/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── core/           # Configuration
│   │   ├── models/         # Database models
│   │   ├── services/       # AI, email, integrations
│   │   ├── integrations/   # Notion, Google Calendar
│   │   └── simple_main.py  # Main application
├── frontend/               # Next.js frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Next.js pages
│   │   ├── services/       # API calls
│   │   └── styles/         # CSS styles
├── docs/                   # Documentation
├── requirements.txt        # Python dependencies
└── README.md
```

### Tech Stack
- **Backend**: FastAPI, SQLAlchemy, Pydantic
- **Frontend**: Next.js, React, TypeScript, Tailwind CSS
- **AI**: Ollama (Llama) / Google Gemini
- **Integrations**: Notion API, Gmail SMTP
- **Database**: SQLite (development), PostgreSQL (production)

### API Endpoints
- `GET /health` - Health check
- `POST /api/generate-timeline` - Generate thesis timeline
- `POST /api/test-email` - Send test email
- `POST /api/create-notion-workspace` - Create Notion workspace
- `POST /api/sync-timeline-to-notion` - Sync timeline to Notion

## 🎯 Working on Tasks

### Task Work Workflow

Once your timeline is generated, you can start working on individual tasks with AI assistance:

1. **Start Working**: Click the "Start" button on any task in your timeline
2. **AI Chat Assistant**: Get help with research, analysis, and problem-solving
3. **Use Specialized Tools**: Access research and academic tools as needed
4. **Track Ethics**: Built-in monitoring ensures responsible AI usage
5. **Complete & Save**: Submit your final deliverable to mark the task complete

### Available Tools

#### 📚 Research Tools
- **Paper Search**: Find academic papers using Semantic Scholar
  ```
  "Find papers about machine learning in healthcare"
  ```
- **Citation Generator**: Generate BibTeX from DOI or arXiv ID
  ```
  DOI: 10.1038/nature12373
  arXiv: 1706.03762
  ```

#### 📄 Document Tools  
- **PDF Summarizer**: Extract key insights from research papers
- **LaTeX OCR**: Convert equation images to LaTeX code
- **AI Detection**: Check content for AI generation

#### 🔍 Quality Assurance
- **Ethics Monitoring**: Real-time tracking of AI usage patterns
- **Academic Integrity**: Alerts and guidance for responsible usage
- **Progress Analytics**: Track completion and time spent

### Best Practices

1. **Start with Planning**: Use the AI to break down complex tasks
2. **Research First**: Gather relevant papers and citations before writing
3. **Iterative Development**: Work in small chunks and get feedback
4. **Maintain Integrity**: Use AI as a learning tool, not a replacement
5. **Save Progress**: Complete tasks properly to maintain your timeline

## 🐛 Troubleshooting

### Common Issues

#### "AI service not available"
- **For Ollama**: Make sure `ollama serve` is running
- **For Gemini**: Check your API key in `.env`

#### "Email failed to send"
- Verify Gmail app password is correct
- Check if 2-factor authentication is enabled
- Ensure EMAIL_USER and EMAIL_PASSWORD are set

#### "Notion integration failed"
- Verify NOTION_TOKEN is correct
- Make sure the integration has access to your workspace

#### "Timeline generation takes too long"
- **Ollama**: First run downloads the model (~4GB)
- **Gemini**: Check internet connection and API quotas

### Testing Your Setup

Run the test script to verify everything is working:
```bash
python test_api_keys.py
```

This will test:
- ✅ Environment variables loaded
- ✅ AI service connection
- ✅ Email configuration
- ✅ Notion integration

## 📈 Roadmap

- [ ] Google Calendar integration
- [ ] Mobile app (React Native)
- [ ] Team collaboration features
- [ ] Advanced analytics and insights
- [ ] Citation management integration
- [ ] Voice command support

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♂️ Support

- **Documentation**: Check this README and `/docs` folder
- **Issues**: Report bugs and request features on GitHub Issues
- **Email**: Contact us at your-email@domain.com

## 🌟 Acknowledgments

- Built for university students by students
- Powered by open-source AI models
- Inspired by academic productivity research

---

**Happy thesis writing! 🎓📚**