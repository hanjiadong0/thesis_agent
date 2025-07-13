# 🎓 Thesis Helper - AI-Powered Thesis Planning System

An intelligent thesis planning and progress tracking system that helps students complete their thesis on time with personalized AI guidance, automated scheduling, and daily motivational emails.

## 🚀 Features

### Core Functionality
- **AI-Powered Timeline Generation**: Creates personalized thesis timelines based on user characteristics and field of study
- **Daily Progress Tracking**: Monitors task completion and productivity patterns
- **Automated Email Notifications**: Sends daily motivational emails with progress updates at 8 AM
- **Emergency Replan System**: Automatically adjusts timeline when users fall behind schedule
- **Multi-Platform Integration**: Syncs with Notion for task management and Google Calendar for scheduling

### Smart Personalization
- **Field-Specific Knowledge**: Tailored phases and timelines for different academic fields
- **Procrastination Adaptation**: Adjusts timeline based on self-assessed procrastination level
- **Work Style Recognition**: Adapts to user's preferred writing style and focus duration
- **Productivity Pattern Learning**: AI learns user patterns over time for better recommendations

### User Experience
- **Web-Based Interface**: Clean, intuitive React frontend
- **Real-Time Updates**: Live progress tracking and timeline adjustments
- **Motivational System**: Streak tracking and personalized encouragement
- **Analytics Dashboard**: Detailed insights into productivity patterns

## 🏗️ Architecture

### Backend Stack
- **FastAPI** - Modern, fast web framework
- **SQLAlchemy** - Database ORM with SQLite
- **Gemini AI** - Timeline generation and insights
- **Gmail SMTP** - Email delivery system
- **Notion API** - Task management integration
- **Google Calendar API** - Scheduling and reminders

### Frontend Stack
- **React** - User interface framework
- **Modern CSS** - Responsive design
- **REST API** - Communication with backend

### Database Design
- **Users** - Profile, preferences, thesis info
- **Daily Progress** - Task completion tracking
- **User Patterns** - AI-learned behavior patterns
- **System Events** - Audit trail and logs
- **Thesis Timeline** - Milestones and phases

## 📋 Prerequisites

- Python 3.9+
- Node.js 16+
- Gmail account with app password
- Notion workspace
- Google Cloud Platform account

## 🛠️ Installation

### 1. Clone Repository
```bash
git clone <repository-url>
cd thesis_agent
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables
Create a `.env` file in the root directory:

```bash
# Database
DATABASE_URL=sqlite:///./thesis_helper.db

# API Keys
NOTION_TOKEN=your_notion_integration_token
GEMINI_API_KEY=your_gemini_api_key

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Email Settings
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_gmail_app_password

# Development Settings
DEBUG=True
SECRET_KEY=your-secret-key-change-in-production
```

### 4. API Key Setup

#### Notion Integration
1. Go to https://www.notion.so/my-integrations
2. Create a new integration
3. Copy the "Internal Integration Token"
4. Create a database in Notion and share it with your integration

#### Google Gemini API
1. Go to https://ai.google.dev/
2. Create API key
3. Enable Gemini API

#### Gmail App Password
1. Enable 2-Factor Authentication on your Google account
2. Go to https://myaccount.google.com/apppasswords
3. Generate app password for "Mail"
4. Use this password in EMAIL_PASSWORD

#### Google Calendar API
1. Go to https://console.cloud.google.com/
2. Create new project or select existing
3. Enable Google Calendar API
4. Create OAuth 2.0 credentials
5. Download credentials file

### 5. Database Setup
```bash
# Initialize database
python -c "from backend.app.models.database import create_tables, get_database_engine; from backend.app.core.config import get_database_url; create_tables(get_database_engine(get_database_url()))"
```

### 6. Run Application
```bash
# Start backend server
python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, start frontend (when implemented)
cd frontend
npm start
```

## 🔧 Configuration

### AI Model Settings
- **Provider**: Gemini (configurable for other providers)
- **Model**: gemini-1.5-flash
- **Temperature**: 0.7 (balanced creativity/consistency)
- **Buffer Time**: 15% added to all estimates

### Email Settings
- **Daily Email Time**: 8:00 AM (configurable per user)
- **Email Template**: HTML with responsive design
- **Motivational Messages**: Context-aware based on progress

### Emergency Replan Triggers
- **Days Behind**: 3+ days behind schedule
- **Completion Rate**: Below 50% for multiple days
- **Manual Trigger**: User-initiated replan

## 📊 API Endpoints

### Core Endpoints
- `GET /api/health` - System health check
- `POST /api/questionnaire/submit` - Submit user questionnaire
- `GET /api/timeline/current` - Get current timeline
- `POST /api/progress/update` - Update daily progress
- `POST /api/timeline/emergency-replan` - Trigger emergency replan
- `GET /api/analytics/productivity` - Get productivity analytics

### Integration Endpoints
- `POST /api/notion/sync` - Sync with Notion
- `POST /api/calendar/create-events` - Create calendar events
- `POST /api/email/send-daily` - Send daily email (automated)

## 🎯 User Journey

### 1. Initial Setup
1. User completes detailed questionnaire
2. AI generates personalized timeline
3. Notion database is created and populated
4. Google Calendar events are scheduled

### 2. Daily Workflow
1. User receives 8 AM motivational email
2. User works on assigned tasks
3. User updates progress in the app
4. System tracks completion and patterns

### 3. Progress Tracking
1. AI analyzes daily progress
2. Timeline adjustments are made as needed
3. Weekly reports are generated
4. Long-term patterns are identified

### 4. Emergency Handling
1. System detects user falling behind
2. AI generates emergency replan
3. User is notified via email
4. Timeline is automatically adjusted

## 🧠 AI Intelligence Features

### Timeline Generation
- **Field-Specific Phases**: Different academic fields have unique requirements
- **User Personalization**: Adapts to procrastination level, work style, and preferences
- **Realistic Estimation**: Includes buffer time and considers user's focus duration
- **Dependency Management**: Tasks are properly sequenced and scheduled

### Progress Analysis
- **Pattern Recognition**: Identifies productivity patterns and optimal work times
- **Predictive Insights**: Anticipates potential delays and suggests adjustments
- **Motivational Messaging**: Generates personalized encouragement based on progress
- **Adaptive Scheduling**: Adjusts future tasks based on completion patterns

### Emergency Replanning
- **Intelligent Prioritization**: Focuses on critical path tasks
- **Quality Preservation**: Maintains thesis quality while adjusting timeline
- **Risk Assessment**: Evaluates impact of changes on final deliverable
- **Multiple Scenarios**: Provides options for different recovery strategies

## 🔒 Security & Privacy

- **Data Encryption**: All sensitive data is encrypted at rest
- **API Key Management**: Secure storage and rotation of API keys
- **User Privacy**: No sharing of personal data with third parties
- **Audit Trail**: Complete log of all system actions and changes

## 🚀 Future Enhancements

### Phase 2 Features
- **Multi-language Support**: Interface in multiple languages
- **Advanced Analytics**: Machine learning for deeper insights
- **Collaboration Tools**: Support for advisors and peer review
- **Mobile App**: React Native mobile companion

### Phase 3 Features
- **Research Integration**: Connection to academic databases
- **Citation Management**: Automated bibliography generation
- **Plagiarism Detection**: Integration with checking services
- **Multi-user Support**: Team thesis projects

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Team

- **Backend Developer**: Thesis Helper Team
- **AI Integration**: Gemini AI implementation
- **Frontend Developer**: React interface
- **DevOps**: Deployment and monitoring

## 📞 Support

For support, please contact:
- Email: support@thesishelper.com
- GitHub Issues: [Create an issue](https://github.com/your-repo/thesis-helper/issues)

## 🙏 Acknowledgments

- Google Gemini AI for intelligent timeline generation
- Notion for flexible task management
- Gmail for reliable email delivery
- FastAPI for excellent web framework
- React for modern frontend development

---

**Made with ❤️ for students struggling with thesis deadlines**