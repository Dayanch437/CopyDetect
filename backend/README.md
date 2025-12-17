# CopyDetect Backend# CopyDetect Backend



Plagiarism detection API for Turkmen language texts using Google Gemini AI.A FastAPI-based plagiarism detection service for Turkmen language texts using Google Gemini AI.



## Quick Start## Features



1. **Install dependencies:**- 🔒 **Secure**: API keys stored in environment variables

```bash- ⚡ **Fast**: Async background processing

pip install -r requirements.txt- 🛡️ **Protected**: Rate limiting and input validation

```- 📝 **Logged**: Comprehensive logging system

- 🌐 **CORS**: Configured for frontend integration

2. **Configure environment:**- 🔄 **Resilient**: Automatic retries with fallback models

```bash- 🧹 **Clean**: Automatic task cleanup

cp .env.example .env

# Edit .env and add your GEMINI_API_KEY## Quick Start

```

### 1. Install Dependencies

3. **Run server:**

```bash```bash

python main.pypip install -r requirements.txt

# or```

uvicorn main:app --reload --host 0.0.0.0 --port 8000

```### 2. Configure Environment



## API EndpointsCopy `.env.example` to `.env` and update your settings:



- `POST /plagiarism-check/` - Submit plagiarism check```bash

- `GET /result/{task_id}` - Get analysis resultscp .env.example .env

- `GET /health` - Health check```



## ConfigurationEdit `.env`:

```env

Edit `.env` file:GEMINI_API_KEY=your_actual_api_key_here

- `GEMINI_API_KEY` - Your Google Gemini API key (required)CORS_ORIGINS=http://localhost:5173,http://localhost:3000

- `CORS_ORIGINS` - Allowed origins (comma-separated)RATE_LIMIT_PER_MINUTE=10

- `RATE_LIMIT_PER_MINUTE` - Rate limit (default: 10)MAX_TEXT_LENGTH=50000

- `MAX_TEXT_LENGTH` - Max text length (default: 50000)MAX_FILE_SIZE_MB=5

- `MAX_FILE_SIZE_MB` - Max file size (default: 5)```



## Features### 3. Run the Server



- ✅ Async background processing```bash

- ✅ Rate limiting (10 req/min)# Development mode with auto-reload

- ✅ Input validationuvicorn main:app --reload --host 0.0.0.0 --port 8000

- ✅ Automatic task cleanup

- ✅ Professional logging# Or using Python directly

- ✅ Health monitoringpython main.py

- ✅ Secure configuration```



## API DocumentationThe API will be available at: `http://localhost:8000`



Interactive docs: `http://localhost:8000/docs`## API Endpoints


### POST `/plagiarism-check/`
Submit a plagiarism check request.

**Request:**
- `original_text` (form): Original Turkmen text
- `suspect_text` (form): Suspect Turkmen text
- OR `original_file` (file): Original text file
- OR `suspect_file` (file): Suspect text file

**Response:**
```json
{
  "task_id": "uuid-string",
  "status": "success",
  "message": "Barlagynyz kabul edildi..."
}
```

**Rate Limit:** 10 requests/minute per IP

### GET `/result/{task_id}`
Get the result of a plagiarism check.

**Response:**
```json
{
  "status": "completed",  // or "processing" or "not_found"
  "message": "Analysis result in Turkmen..."
}
```

**Rate Limit:** 20 requests/minute per IP

### GET `/health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-17T...",
  "tasks_in_store": 5,
  "api_configured": true
}
```

### GET `/`
API information.

## Configuration

All configuration is managed through environment variables (`.env` file):

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | *Required* |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | `http://localhost:5173,...` |
| `RATE_LIMIT_PER_MINUTE` | Rate limit per IP | `10` |
| `MAX_TEXT_LENGTH` | Maximum text length in characters | `50000` |
| `MAX_FILE_SIZE_MB` | Maximum file size in MB | `5` |
| `TASK_CLEANUP_HOURS` | Hours before old tasks are deleted | `24` |

## Project Structure

```
backend/
├── main.py              # FastAPI application
├── ai.py                # AI integration (Gemini)
├── config.py            # Configuration management
├── models.py            # Pydantic models
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (not in git)
├── .env.example         # Environment template
├── .gitignore          # Git ignore rules
├── README.md            # This file
└── app.log             # Application logs
```

## Architecture

### Background Processing
- Requests are immediately accepted and returned with a task ID
- Processing happens asynchronously in the background
- Results are retrieved using the task ID

### AI Models
The system tries multiple Gemini models in order:
1. `gemini-2.0-flash` (fastest)
2. `gemini-1.5-pro` (fallback)
3. `gemini-1.5-flash` (final fallback)

Each model has 3 retry attempts with exponential backoff (3s, 7s, 15s).

### Security Features
- ✅ API keys in environment variables
- ✅ Rate limiting (SlowAPI)
- ✅ Input validation (text length, file size)
- ✅ CORS configuration
- ✅ Error handling without exposing internals

### Logging
- All requests and errors are logged
- Log file: `app.log`
- Console output for development
- Log levels: INFO, WARNING, ERROR

## Development

### Running Tests
```bash
pytest  # (tests to be implemented)
```

### Code Style
```bash
black .
flake8 .
```

### Debugging
Set log level to DEBUG in code or:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Production Deployment

### Recommendations

1. **Use Redis** for task storage instead of in-memory dict
2. **Add authentication** (API keys, JWT)
3. **Use a process manager** (systemd, supervisor, PM2)
4. **Set up monitoring** (Prometheus, Grafana)
5. **Use HTTPS** (nginx reverse proxy with SSL)
6. **Scale horizontally** (multiple workers)
7. **Add database** for persistent storage
8. **Implement caching** (Redis)

### Docker Deployment (Future)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables in Production
Never commit `.env` to git. Use:
- Docker secrets
- Kubernetes secrets
- Cloud provider secret management (AWS Secrets Manager, etc.)

## Troubleshooting

### "GEMINI_API_KEY is not set"
- Make sure `.env` file exists
- Check that `GEMINI_API_KEY` is set in `.env`
- Restart the server after changing `.env`

### Rate Limit Errors
- Increase `RATE_LIMIT_PER_MINUTE` in `.env`
- Or wait before making more requests

### "System is currently unavailable"
- Check your internet connection
- Verify API key is valid
- Check Google Gemini API status

### File Too Large
- Increase `MAX_FILE_SIZE_MB` in `.env`
- Or reduce file size before uploading

## API Documentation

Interactive API documentation available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## License

[Your License Here]

## Support

For issues and questions, please contact the development team.

