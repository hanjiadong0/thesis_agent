# Thesis Helper

A web application to help students manage their thesis projects with AI assistance.

## Setup

1. **Clone the repository**
```bash
git clone https://github.com/ananmouaz/thesis_agent.git
cd thesis_agent
```

2. **Create virtual environment**
```bash
conda activate spenv (python version 3.10)

```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Install Node.js dependencies**
```bash
cd frontend
npm install
cd ..
```

5. **Set up environment variables**
```bash
cp env.template .env
```
Edit `.env` file with your API keys:
- `GEMINI_API_KEY` - Google Gemini API key (optional, for cloud AI)
- `NOTION_TOKEN` - Notion integration token
- `EMAIL_USER` and `EMAIL_PASSWORD` - Gmail credentials for notifications
- `DATABASE_URL` - Database connection (SQLite by default, PostgreSQL for production)

6. **Install Ollama (optional, for local AI)**
```bash
# Visit https://ollama.ai and install
ollama pull llama3.2
ollama serve
```

## Running the Application

1. **Start the backend server**
```bash
cd backend
conda activate spenv
python -m uvicorn app.simple_main:app --reload --host 0.0.0.0 --port 8000
```

2. **Start the frontend (in a new terminal)**
```bash
cd frontend
npm run dev
```

3. **Open your browser**
Go to `http://localhost:3000`

## Features

- Brainstorm thesis topics with AI
- Generate detailed project timelines
- Connect to Notion for task management
- Work on tasks with 18 built-in academic tools
- Email progress updates
- SQLite database (development) or PostgreSQL (production)

## Tools Available

Grammar checker, web search, Wikipedia lookup, survey generator, math solver, citation generator, PDF summarizer, and more.
