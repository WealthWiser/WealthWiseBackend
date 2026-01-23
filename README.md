# WealthWise Backend

A comprehensive FastAPI-based backend service for WealthWise, an AI-powered personal finance management platform. This backend provides secure authentication, transaction processing, AI-driven investment advice, and intelligent financial chatbot capabilities.

## 🚀 Features

- **Secure Authentication**: JWT-based user authentication with Supabase integration
- **Transaction Processing**: PDF bank statement parsing and transaction categorization
- **AI Investment Advisor**: Personalized investment recommendations using OpenAI GPT-4 and market data
- **Financial Chatbot**: Conversational AI assistant for financial queries
- **Real-time Market Data**: Integration with Indian stock market APIs
- **Database Integration**: Supabase for user data and transaction storage
- **Docker Support**: Containerized deployment ready

## 🛠 Tech Stack

- **Framework**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL)
- **AI Services**: OpenAI GPT-4, Google Gemini
- **Authentication**: JWT tokens
- **PDF Processing**: pdfminer.six, pdfplumber
- **Data Processing**: Pandas, NumPy
- **Deployment**: Docker, Uvicorn

## 📁 Project Structure

```
WealthWiseBackend/
├── Dockerfile                    # Docker configuration
├── README.md                     # Project documentation
├── requirements.txt              # Python dependencies
└── app/
    ├── __init__.py
    ├── main.py                   # FastAPI application entry point
    ├── config.py                 # Configuration and Supabase setup
    ├── database.py               # Database connection utilities
    ├── agents/                   # AI agent modules
    │   ├── __init__.py
    │   ├── analyst.py            # Financial analysis agent
    │   ├── educator.py           # Financial education agent
    │   ├── market.py             # Market data agent
    │   ├── orchestrator.py       # Agent coordination
    │   └── risk.py               # Risk assessment agent
    ├── aimodels/                 # AI model integrations
    │   ├── __init__.py
    │   ├── gemini_service.py     # Google Gemini AI service
    │   └── openai_service.py     # OpenAI GPT service
    ├── models/                   # Pydantic models
    │   ├── __init__.py
    │   ├── finance.py            # Financial data models
    │   └── user.py               # User data models
    ├── routes/                   # API route handlers
    │   ├── __init__.py
    │   ├── auth.py               # Authentication endpoints
    │   ├── chat.py               # Chatbot endpoints
    │   ├── finance.py            # Financial operations endpoints
    │   └── user.py               # User management endpoints
    └── utils/                    # Utility functions
        ├── __init__.py
        ├── advice_generator.py   # Investment advice generation
        ├── auth.py               # JWT authentication utilities
        ├── logger.py             # Logging configuration
        └── transactions/         # Transaction processing utilities
            ├── __init__.py
            ├── categories.py     # Transaction categorization
            └── read_pdf.py       # PDF parsing utilities
```

## 🔧 Installation

### Prerequisites

- Python 3.11+
- Docker (optional, for containerized deployment)
- Supabase account
- OpenAI API key
- Indian Stock API key

### Local Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd WealthWiseBackend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**

   Create a `.env` file in the root directory:

   ```env
   # Supabase Configuration
   SUPABASE_URL=your_supabase_url
   SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

   # AI Service Keys
   OPENAI_API_KEY=your_openai_api_key
   GEMINI_API_KEY=your_gemini_api_key

   # Market Data API
   INDIAN_STOCK_API_KEY=your_indian_stock_api_key

   # JWT Secret (generate a secure random string)
   JWT_SECRET_KEY=your_jwt_secret_key
   ```

5. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

   The API will be available at `http://localhost:8000`

### Docker Setup

1. **Build the Docker image**
   ```bash
   docker build -t wealthwise-backend .
   ```

2. **Run the container**
   ```bash
   docker run -p 8000:8000 --env-file .env wealthwise-backend
   ```

## 📖 Usage

### API Endpoints

#### Authentication
- `GET /auth/me` - Get user profile (requires JWT token)

#### Finance
- `POST /finance/extract-transactions` - Extract transactions from PDF bank statement
- `POST /finance/generate-advice` - Generate personalized investment advice

#### Chat
- `POST /chat/query` - Query the financial chatbot

### Example API Usage

#### Extract Transactions
```bash
curl -X POST "http://localhost:8000/finance/extract-transactions" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "pdf=@bank_statement.pdf" \
  -F "password=statement_password"
```

#### Generate Investment Advice
```bash
curl -X POST "http://localhost:8000/finance/generate-advice" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "risk_profile": "Moderate",
    "investment_goal": "Wealth Creation",
    "investment_horizon": "Long-term (7+ years)"
  }'
```

#### Chat Query
```bash
curl -X POST "http://localhost:8000/chat/query" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{"query": "What are some good investment options for beginners?"}'
```

## 🗄 Database Schema

The application uses Supabase with the following main tables:

- `users` - User account information
- `transactions` - Parsed bank transactions
- `categories` - Transaction categorization rules

## 🤖 AI Features

### Investment Advisor
- Analyzes user risk profile and financial data
- Fetches real-time Indian market data
- Provides personalized investment recommendations
- Suggests SIP amounts based on savings

### Financial Chatbot
- Conversational AI for financial queries
- Maintains chat history per user
- Focuses on finance, investing, and budgeting topics
- Uses OpenAI GPT-4 for responses

## 🔒 Security

- JWT-based authentication
- Secure API key management
- CORS configuration for web clients
- Input validation with Pydantic models

## 🚀 Deployment

### Render Deployment

1. Connect your GitHub repository to Render
2. Set environment variables in Render dashboard
3. Deploy with the following settings:
   - **Runtime**: Docker
   - **Dockerfile Path**: `./Dockerfile`
   - **Port**: 8000

### Environment Variables for Production

Ensure all required environment variables are set in your deployment platform:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `OPENAI_API_KEY`
- `GEMINI_API_KEY`
- `INDIAN_STOCK_API_KEY`
- `JWT_SECRET_KEY`
- `PORT` (set by Render, defaults to 8000)

## 🧪 Testing

Run the application and test endpoints using tools like:
- Postman
- curl
- FastAPI's interactive documentation at `/docs`

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Contact the development team

---

**WealthWise Backend** - Empowering financial literacy through AI-driven insights.