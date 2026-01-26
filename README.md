# AI Data Analyzer

A FastAPI-based web application for analyzing data files with AI-powered insights using Google Gemini or OpenRouter.

## Features

- 📊 Upload and analyze CSV, Excel, and PDF files
- 🤖 AI-powered data analysis using Google Gemini or OpenRouter (configurable)
- 📝 Dynamic form builder with templates
- 🎯 GitHub repository analysis
- 💾 PostgreSQL database for data persistence
- 🎨 Modern web interface

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.9+**
- **PostgreSQL** (running on port 5432)
- **pip** (Python package manager)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ai-data-analyzer
```

### 2. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note**: If using PostgreSQL, also install:
```bash
pip install psycopg2-binary
```

### 4. Set Up Environment Variables

Create a `.env` file in the project root:

```bash
# Database Configuration
MYSQL_URL=postgresql://Anoop_2:1234@localhost:5432/ai_analyzer

# AI Client Configuration
# Set to 'true' to use Gemini, 'false' (or omit) to use OpenRouter
USE_GEMINI=false

# OpenRouter Configuration (used when USE_GEMINI=false)
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Gemini Configuration (used when USE_GEMINI=true)
GEMINI_API_KEY=your_gemini_api_key_here
```

**Important Configuration**:
- Set `USE_GEMINI=true` to use Google Gemini AI, or `USE_GEMINI=false` to use OpenRouter
- Replace `your_gemini_api_key_here` with your actual Google Gemini API key
- Replace `your_openrouter_api_key_here` with your actual OpenRouter API key
- You only need to configure the API key for the provider you're using

**Quick Start**: Copy the example file and customize it:
```bash
cp .env.example .env
# Then edit .env with your actual credentials
```

## Database Setup

### PostgreSQL Configuration

1. **Ensure PostgreSQL is running**:
   ```bash
   # Check if PostgreSQL is running on port 5432
   lsof -i :5432
   ```

2. **Create the database**:
   ```bash
   python3 -c "import psycopg2; conn = psycopg2.connect(host='localhost', port=5432, user='Anoop_2', password='1234', database='postgres'); conn.autocommit = True; cur = conn.cursor(); cur.execute('CREATE DATABASE ai_analyzer'); cur.close(); conn.close()"
   ```

   Or manually using `psql`:
   ```sql
   CREATE DATABASE ai_analyzer;
   ```

3. **Database tables will be created automatically** when you first run the application via the `init_db()` function in `app/services/db.py`.

### Database Tables

The application will automatically create the following tables:

- **templates** - Predefined form templates (e.g., HR forms)
- **forms** - Custom form definitions with dynamic fields
- **submissions** - Form submission data

## AI Client Configuration

This application supports two AI providers:

### **Option 1: Google Gemini** (Recommended)

1. Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Set in `.env`:
   ```bash
   USE_GEMINI=true
   GEMINI_API_KEY=your_actual_gemini_api_key
   ```

**Default Model**: `gemini-2.0-flash-exp`

### **Option 2: OpenRouter**

1. Get your API key from [OpenRouter](https://openrouter.ai/keys)
2. Set in `.env`:
   ```bash
   USE_GEMINI=false
   OPENROUTER_API_KEY=your_actual_openrouter_api_key
   ```

**Default Model**: `amazon/nova-2-lite-v1:free`

### Switching Between Providers

Simply change the `USE_GEMINI` value in your `.env` file and restart the application:
- `USE_GEMINI=true` → Uses Gemini
- `USE_GEMINI=false` → Uses OpenRouter

## Running the Application

### Development Server

```bash
python run.py
```

The application will be available at: **http://localhost:8000**

### Using Docker (Alternative)

If you prefer using Docker with MySQL:

1. Update `.env` to use MySQL:
   ```bash
   MYSQL_URL=mysql+pymysql://Anoop2:1234@localhost:3306/data_analyzer
   ```

2. Install MySQL driver:
   ```bash
   pip install pymysql
   ```

3. Start Docker services:
   ```bash
   docker-compose up -d
   ```

## Project Structure

```
ai-data-analyzer/
├── app/
│   ├── api/              # API endpoints
│   ├── models/           # Database models
│   ├── services/         # Business logic
│   │   ├── ai_client.py        # Unified AI client router
│   │   ├── gemini_client.py    # Google Gemini client
│   │   ├── openrouter_client.py # OpenRouter client
│   │   ├── db.py               # Database configuration
│   │   ├── github_agent.py
│   │   ├── github_questions.py
│   │   └── match_agent.py
│   └── main.py          # FastAPI application
├── static/              # Static files (CSS, JS)
├── templates/           # HTML templates
├── uploads/             # File upload directory
├── .env                 # Environment variables (create from .env.example)
├── .env.example         # Environment variables template
├── docker-compose.yml   # Docker configuration
├── requirements.txt     # Python dependencies
└── run.py              # Application entry point
```

## Troubleshooting

### Database Connection Issues

**Error**: `[init_db] Database not ready, retrying...`

**Solutions**:

1. **Check if PostgreSQL is running**:
   ```bash
   lsof -i :5432
   ```

2. **Verify database exists**:
   ```bash
   python3 -c "import psycopg2; conn = psycopg2.connect(host='localhost', port=5432, user='Anoop_2', password='1234', database='ai_analyzer'); print('✅ Connection successful'); conn.close()"
   ```

3. **Create database if it doesn't exist**:
   ```bash
   python3 -c "import psycopg2; conn = psycopg2.connect(host='localhost', port=5432, user='Anoop_2', password='1234', database='postgres'); conn.autocommit = True; cur = conn.cursor(); cur.execute('CREATE DATABASE ai_analyzer'); cur.close(); conn.close()"
   ```

4. **Check credentials**: Ensure the username (`Anoop_2`) and password (`1234`) in `.env` match your PostgreSQL configuration.

### Common Issues

**Issue**: `psycopg2.OperationalError: database "ai_analyzer" does not exist`
- **Fix**: Run the database creation command above

**Issue**: `ModuleNotFoundError: No module named 'psycopg2'`
- **Fix**: `pip install psycopg2-binary`

**Issue**: Docker daemon not running
- **Fix**: Start Docker Desktop application

**Issue**: `OPENROUTER_API_KEY is not configured` or `GEMINI_API_KEY is not configured`
- **Fix**: Ensure you've set the correct API key in `.env` based on your `USE_GEMINI` setting
- **Fix**: Copy `.env.example` to `.env` and add your actual API keys

**Issue**: AI client errors or no responses
- **Fix**: Verify your API key is valid
- **Fix**: Check your internet connection
- **Fix**: For Gemini, ensure you've enabled the API in Google Cloud Console
- **Fix**: For OpenRouter, check your account has credits/free tier access

**Issue**: Port 8000 already in use
- **Fix**: Change port in `run.py` or kill the process using port 8000

## API Endpoints

- `GET /` - Home page
- `POST /upload` - Upload and analyze files
- `GET /forms` - List all forms
- `POST /forms` - Create new form
- `POST /forms/{form_id}/submit` - Submit form data
- Additional GitHub analysis endpoints

## Configuration

### Database Connection String Format

PostgreSQL:
```
postgresql://USERNAME:PASSWORD@HOST:PORT/DATABASE_NAME
```

MySQL:
```
mysql+pymysql://USERNAME:PASSWORD@HOST:PORT/DATABASE_NAME
```

### Environment Variables

#### Required Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MYSQL_URL` | Database connection string | - | Yes |
| `USE_GEMINI` | Set to `true` for Gemini, `false` for OpenRouter | `false` | Yes |
| `GEMINI_API_KEY` | Google Gemini API key | - | Conditional* |
| `OPENROUTER_API_KEY` | OpenRouter API key | - | Conditional* |

*Required based on which AI provider you're using (controlled by `USE_GEMINI`)

#### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_MODEL` | Override default Gemini model | `gemini-2.0-flash-exp` |
| `GEMINI_MAX_TOKENS` | Max tokens for Gemini responses | `2048` |
| `OPENROUTER_MODEL` | Override default OpenRouter model | `amazon/nova-2-lite-v1:free` |
| `OPENROUTER_MAX_TOKENS` | Max tokens for OpenRouter responses | `2048` |
| `OPENROUTER_BASE_URL` | OpenRouter API endpoint | `https://openrouter.ai/api/v1/chat/completions` |
| `OPENROUTER_HTTP_REFERER` | HTTP Referer for OpenRouter | `http://localhost` |
| `OPENROUTER_TITLE` | App title for OpenRouter | `AI Data Analyzer` |
| `GITHUB_TOKEN` | GitHub personal access token for higher API rate limits | - |

See [`.env.example`](file:///Users/anoopchandra/repositories/ai-data-analyzer/.env.example) for a complete configuration template.

## Dependencies

Key dependencies include:
- **FastAPI** - Web framework
- **SQLAlchemy** - Database ORM
- **Uvicorn** - ASGI server
- **Pandas** - Data analysis
- **PyMuPDF** - PDF processing
- **google-generativeai** - Google Gemini API client
- **requests** - OpenRouter HTTP client
- **python-dotenv** - Environment variable management

See `requirements.txt` for full list of dependencies.

## Development

### Running Tests

```bash
# Add test commands here
pytest
```

### Code Structure

- Database models are defined in `app/services/db.py`
- API routes are in `app/api/`
- Business logic services are in `app/services/`
- Frontend templates are in `templates/`

## License

[Add your license here]

## Support

For issues or questions, please open an issue in the repository.

---

**Last Updated**: January 2026
