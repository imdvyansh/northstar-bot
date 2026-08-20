# Northstar Homes — AI Sales Agent (Aanya)

A FastAPI backend with an integrated chat UI for an AI sales agent that qualifies real estate leads for **Northstar One** (Sector 79, Gurugram) across chat, in English/Hindi/Hinglish.

## 🎯 Project Overview

**Northstar Bot** is an AI-powered lead qualification system designed to:
- Engage prospective home buyers in natural conversation
- Qualify leads based on interest, budget, timeline, and purpose
- Facilitate site visit bookings
- Extract actionable analytics from conversations
- Support multi-lingual interactions (English, Hindi, Hinglish)
- Provide authentication and session management

The agent, **Aanya**, acts as a warm and respectful sales representative, following strict anti-hallucination guidelines to ensure all stated facts are accurate and verifiable.

---

## 📋 Core Features

### 1. **AI-Powered Conversation Engine**
- **Real LLM Mode**: Uses Google Gemini API with system prompts for production-grade responses
- **Mock Agent Mode**: Deterministic, rule-based fallback for offline testing and demos
- **Multi-Channel Support**: Identical behavior on chat and voice (with channel-specific style adaptation)
- **Language Detection**: Automatically detects and responds in English, Hindi, or Hinglish

### 2. **Lead Qualification**
Captures and tracks:
- Configuration interest (2 BHK / 3 BHK)
- Budget comfort signals
- Timeline (ready now / 3–6 months / exploring)
- Purpose (self-use / investment)
- Objections and hesitations
- Interest level (hot / warm / cold / unknown)

### 3. **Site Visit Booking**
- Collects preferred date, time, customer name, and phone
- Confirms details before finalizing
- Handles booking failures gracefully with alternative slots
- Simulates real booking backend with success/failure logic

### 4. **Conversation Analytics**
- Extracts insights post-conversation using LLM or rule-based logic
- Tracks language used, interest signals, objections, and next steps
- Supports human escalation tracking
- Provides conversation summary and actionable follow-up notes

### 5. **Authentication & Session Management**
- JWT-based user authentication (signup/login)
- Session isolation with in-memory or MongoDB storage
- Conversation history persistence
- Per-user conversation tracking

### 6. **Web UI** (I just created the UI using AI. I don’t have much knowledge of frontend development yet.
)
- Minimal, responsive chat interface
- Real-time message exchange
- Session management (start/end conversation)
- Analytics display
- Auth toggle (login/signup)

---

## 🏗️ Architecture

### Tech Stack
- **Backend**: FastAPI 0.115+ (async Python web framework)
- **Database**: MongoDB (async via Motor driver)
- **LLM**: Google Generative AI (Gemini 2.5 Flash)
- **Authentication**: JWT + bcrypt password hashing
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Dependency Management**: Poetry

### Key Dependencies
```
fastapi, uvicorn, pydantic, google-genai, motor, pymongo, 
python-jose, passlib[bcrypt], python-dotenv
```

---

## 📁 Project Structure

```
northstar-bot/
├── app/
│   ├── __init__.py              # Package initialization
│   ├── main.py                  # FastAPI app & core routes
│   ├── prompt.py                # System prompt (core deliverable)
│   ├── llm_client.py            # Gemini API integration
│   ├── mock_agent.py            # Offline deterministic agent
│   ├── booking.py               # Site visit booking simulation
│   ├── analytics.py             # Post-conversation analytics extraction
│   ├── auth.py                  # JWT & password utilities
│   ├── auth_routes.py           # Signup/login endpoints
│   ├── schemas.py               # Pydantic request/response models
│   ├── store.py                 # In-memory session storage
│   └── database.py              # MongoDB connection & collections
├── static/
│   └── index.html               # Chat UI (single-page app)
├── run_tests.py                 # Scripted test scenarios
├── pyproject.toml               # Poetry config & dependencies
├── poetry.toml                  # Poetry local config
└── README.md                    # Original quickstart guide
```

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.10+
- Poetry (https://python-poetry.org/)
- MongoDB instance (local or cloud)
- Google Gemini API key (for production mode)

### 1. Install Dependencies
```bash
cd northstar-bot
poetry install
poetry shell
```

### 2. Environment Configuration
Create a `.env` file in the project root:
```bash
# LLM Configuration
GEMINI_API_KEY=your-gemini-key-here

# Authentication
JWT_SECRET=your-super-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Database
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=your db name
```

**Notes**:
- If `GEMINI_API_KEY` is not set, the bot falls back to mock agent mode
- For production, use a strong JWT_SECRET and secure MongoDB connection
- MongoDB can run locally (`mongod`) or via Docker/Atlas

### 3. Start MongoDB (if running locally)
```bash
# Using Homebrew (macOS)
brew services start mongodb-community

# Using Docker
docker run -d -p 27017:27017 --name mongo mongo:latest

# Or connect to MongoDB Atlas
MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/
```

### 4. Run the Application
```bash
# Start the FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The app will be available at: **http://localhost:8000**

---

## 🔌 API Endpoints

All endpoints require JWT authentication (except signup/login).

### Authentication

#### `POST /api/auth/signup`
Create a new user account.
```json
{
  "username": "john_doe",
  "password": "secure_password",
  "email": "john@example.com"
}
```
**Response**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

#### `POST /api/auth/login`
Authenticate an existing user.
```json
{
  "username": "john_doe",
  "password": "secure_password"
}
```
**Response**: Same as signup

---

### Chat & Conversation

#### `POST /api/chat`
Send a message and get a reply from Aanya.

**Headers**: `Authorization: Bearer {access_token}`

**Request**:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",  // optional, auto-generated if null
  "message": "Hi, I'm interested in a 3 BHK apartment"
}
```

**Response**:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "reply": "Thanks for reaching out! A 3 BHK at Northstar One starts at ₹1.75 crore onwards...",
  "ended": false
}
```

#### `POST /api/end/{session_id}`
Explicitly end a conversation and retrieve analytics.

**Response**:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "language_used": "English",
  "configuration_interest": "3 BHK",
  "budget_signal": "Looking for premium options",
  "timeline": "3-6 months",
  "purpose": "self-use",
  "interest_level": "warm",
  "objections_raised": ["price_concerns"],
  "site_visit_status": "proposed",
  "site_visit_datetime": "25 August 3:00 PM",
  "escalated_to_human": false,
  "do_not_contact": false,
  "follow_up_required": true,
  "follow_up_note": "Customer requested callback after 2 weeks",
  "summary": "Customer interested in 3 BHK with budget concerns, proposed site visit."
}
```

#### `GET /api/analytics/{session_id}`
Retrieve analytics for a specific conversation session.

**Response**: Same as `POST /api/end/{session_id}`

---

## 💬 Conversation Flow

### 1. **Initial Greeting**
Agent introduces itself and Northstar One.

### 2. **Lead Qualification** (natural, not interrogative)
Agent weaves in questions one at a time:
- Configuration interest (2 BHK / 3 BHK)
- Budget comfort
- Timeline
- Purpose
- Location fit

### 3. **Objection Handling**
- **Price objections**: Acknowledge, don't argue, offer alternatives
- **Busy/Not interested**: Respect the customer, offer respectful follow-up
- **Hard stop ("stop contacting")**: Comply immediately, end conversation
- **Unknown questions**: Admit honestly, offer escalation or follow-up

### 4. **Site Visit Booking**
When genuine interest is shown:
- Collect: date, time, name, phone
- Confirm details before finalizing
- Handle booking failures gracefully

### 5. **Closing**
Restate agreed next step, thank customer by name, sign off warmly.

---

## 🤖 Agent Modes

### **Real LLM Mode** (Production)
```
Enabled when: GEMINI_API_KEY environment variable is set
```
- Uses Google Gemini 2.5 Flash API
- Powered by `app/prompt.py` system prompt
- Supports `book_site_visit` function tool
- Max output: 600 tokens
- Handles function calls with retry logic

### **Mock Agent Mode** (Offline/Testing)
```
Enabled when: GEMINI_API_KEY is NOT set
```
- Deterministic, rule-based responses
- Fast, no external API calls
- Supports all conversation flows
- Language detection via keywords
- Simulates booking with blocked time slots (9 AM unavailable)
- Useful for testing and demos

---

## 📊 Analytics & Extraction

### Automatic Extraction (Post-Conversation)
After a conversation ends, the system extracts:

| Field | Type | Captured By |
|-------|------|-------------|
| `language_used` | string | Language detection in mock agent or LLM analysis |
| `configuration_interest` | string | Keyword matching (2 BHK / 3 BHK) |
| `budget_signal` | string | Customer's stated budget comments |
| `timeline` | string | When customer plans to purchase |
| `purpose` | string | Self-use or investment |
| `interest_level` | enum | Derived from booking, escalation, objections |
| `objections_raised` | array | Tracked during conversation |
| `site_visit_status` | enum | booked / failed / proposed / not_discussed |
| `escalated_to_human` | boolean | Set when customer requests human contact |
| `do_not_contact` | boolean | Set on hard-stop requests |
| `follow_up_required` | boolean | Set for callbacks or pending questions |
| `follow_up_note` | string | Specific action required |
| `summary` | string | One-liner capturing lead quality |

### Interest Level Classification
```
hot      → Site visit booked or high-intent signals
warm     → Configuration interest OR site visit proposed/failed OR human escalation
cold     → Do not contact request
unknown  → General inquiry, no strong signals
```

---

## 🔐 Authentication & Security

### JWT Token Flow
1. User signs up/logs in at `/api/auth/signup` or `/api/auth/login`
2. Server returns JWT token
3. Client stores token in `localStorage`
4. Client includes token in `Authorization: Bearer {token}` header
5. Server validates token on each protected endpoint
6. Token expires after `ACCESS_TOKEN_EXPIRE_MINUTES` (default: 1440 = 24 hours)

### Password Security
- Passwords hashed using bcrypt
- Never stored in plain text
- Verified using `passlib.context.CryptContext`

### Session Isolation
- Each conversation bound to a `session_id`
- Sessions linked to authenticated user
- MongoDB stores all conversation history tagged with username

---

## 📱 Web UI (Frontend)

### Features
- **Auth Screen**: Login/signup with error handling
- **Chat Screen**: Real-time message exchange
- **Analytics Display**: Shows conversation insights (hidden until end)
- **Session Management**: Start new, end current conversation
- **Responsive Design**: Works on desktop and mobile

### Key JavaScript Functions
- `handleAuthSubmit()` - Process login/signup
- `sendMessage()` - Send user message and display reply
- `endConversation()` - Close conversation and show analytics
- `authFetch()` - Wrapper that attaches JWT to all requests
- `toggleAuthMode()` - Switch between login and signup

---

## 🧪 Testing

### Included Test Cases (`run_tests.py`)

#### TC1: Hinglish + Booking Success
```
Namaste → capture 3 BHK → confirm site visit → book for 25 Aug 3 PM
```

#### TC2: Booking Failure (Blocked Slot)
```
English → 2 BHK → site visit → attempt 9 AM (blocked) → receive alternative slots
```

#### TC3: Price Objection
```
English → 3 BHK too expensive → capture objection
```

#### TC4: Unknown Question
```
English → ask possession date → agent escalates, follow-up needed
```

### Run Tests
```bash
# Start the server in one terminal
uvicorn app.main:app --reload

# In another terminal
python run_tests.py
```

Expected output:
```
### TC1: Hinglish, config capture + successful booking ###
>> Namaste
<< Namaste! Aanya here from Northstar Homes...
...
ANALYTICS: { "session_id": "...", "language_used": "Hinglish", ... }
```

---

## 🎛️ System Prompt (Part 1)

Located in `app/prompt.py`, the system prompt defines:

1. **Agent Identity**: Aanya from Northstar Homes
2. **Knowledge Boundary**: Only facts from Section 2 (project details, pricing)
3. **Language Support**: Auto-detect English/Hindi/Hinglish
4. **Channel Adaptation**: Same rules, different delivery (voice vs. chat)
5. **Conversation Flow**: Qualification → objection handling → booking
6. **Objection Routing**: Hard stops, soft objections, escalations
7. **Anti-Hallucination**: Never invent facts, admit unknowns
8. **Booking Flow**: Collect date/time/name/phone, confirm, handle failures
9. **Ending Rules**: Graceful close with restatement of next steps
10. **Hard Rules**: Applied universally, on every channel

### Fact Boundary (Section 2)
```
Project:        Northstar One
Location:       Sector 79, Gurugram
Configurations: 2 BHK, 3 BHK
Pricing:        
  - 2 BHK: ₹1.35 crore onwards
  - 3 BHK: ₹1.75 crore onwards
```

**Never invent**: possession dates, RERA numbers, floor plans, amenities, discounts, payment plans, loan tie-ups, availability of specific units.

---

## 📂 Key Files Deep Dive

### `app/main.py`
**FastAPI application core**
- Route definitions: `/api/chat`, `/api/end/{session_id}`, `/api/analytics/{session_id}`
- Session management: `new_session()`, `get_session()`, `end_session()`
- MongoDB persistence on each turn
- Static file serving for `index.html`

### `app/prompt.py`
**System prompt & project facts**
- 12 sections covering agent behavior, rules, and knowledge
- Language adaptation logic
- Objection handling patterns
- Hard rules and boundaries

### `app/llm_client.py`
**LLM integration**
- Gemini API client setup
- System prompt injection
- Function tool declaration (book_site_visit)
- Content building from message history
- Fallback to mock agent if no API key

### `app/mock_agent.py`
**Offline agent for testing**
- Keyword-based routing
- Language detection via regex & hints
- Configuration capture (2 BHK / 3 BHK)
- Objection flows: hard stop, not interested, busy, escalation
- Booking simulation with blocked time slots
- Analytics generation from state

### `app/booking.py`
**Site visit booking backend**
- Simulates booking with success/failure logic
- Blocked time markers (9 AM unavailable)
- MongoDB logging of all booking attempts
- Alternative slots on failure

### `app/analytics.py`
**Post-conversation insights**
- LLM-based extraction (real mode) with JSON response
- Rule-based fallback (mock mode) from session state
- Interest level classification
- Summary generation
- Support for both modes with graceful degradation

### `app/store.py`
**In-memory session management**
- Session dictionary with unique UUIDs
- Tracks messages, state, and end status
- Simple but production-grade for demo

### `app/database.py`
**MongoDB connection**
- Collections: `users`, `conversations`, `bookings`
- Motor async driver for FastAPI compatibility

### `app/auth.py`
**Authentication utilities**
- JWT creation and validation
- Password hashing (bcrypt)
- OAuth2 dependency injection for FastAPI

### `static/index.html`
**Web UI (SPA)**
- Auth screen (login/signup)
- Chat interface with real-time messaging
- Analytics display on conversation end
- localStorage-based token management
- Responsive design for mobile & desktop

---

## 🔧 Configuration

### Environment Variables
```bash
# LLM
GEMINI_API_KEY=sk-...          # Set for production mode; omit for mock mode

# Authentication
JWT_SECRET=your-secret-key      # REQUIRED
JWT_ALGORITHM=HS256             # Default
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Database
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=northstar_bot
```

### Optional Tuning
In `app/llm_client.py`:
- `MODEL` - Currently "gemini-2.5-flash" (changeable)
- `max_output_tokens` - Set to 600 (reduce for shorter responses)

In `app/mock_agent.py`:
- `BLOCKED_TIME_MARKERS` - Customize blocked booking slots
- `HINGLISH_HINTS` - Add/remove keywords for language detection

---

## 📈 Metrics & Monitoring

### Session Lifecycle
1. `new_session()` - Start
2. `get_session(session_id)` - Retrieve state
3. `send message` → `generate_reply()` - Process turn
4. `end_session(session_id)` - Close & extract analytics

### MongoDB Collections

**users**
```json
{
  "_id": "...",
  "username": "john_doe",
  "email": "john@example.com",
  "hashed_password": "$2b$12$..."
}
```

**conversations**
```json
{
  "_id": "...",
  "session_id": "550e8400...",
  "username": "john_doe",
  "messages": [
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hello!"}
  ],
  "ended": false,
  "analytics": { ... }
}
```

**bookings**
```json
{
  "_id": "...",
  "session_id": "...",
  "username": "...",
  "name": "Rohit Sharma",
  "phone": "9876543210",
  "date": "25 August",
  "time": "3 PM",
  "status": "booked|failed",
  "confirmation_id": "NS-12345",
  "created_at": "2024-08-20T..."
}
```

---

## 🐛 Troubleshooting

### Server Won't Start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill existing process
kill -9 <PID>
```

### MongoDB Connection Errors
```bash
# Verify MongoDB is running
mongodb: connection refused

# Start MongoDB
mongod --dbpath /usr/local/var/mongodb

# Or use Docker
docker run -d -p 27017:27017 mongo:latest
```

### JWT Token Expired
- Clear localStorage and log in again
- Check `ACCESS_TOKEN_EXPIRE_MINUTES` in `.env`

### LLM API Errors
```bash
# Check GEMINI_API_KEY
echo $GEMINI_API_KEY

# If not set, mock agent will run automatically
```

### Session Not Found
- Session IDs are UUIDs generated server-side
- Verify session_id in request matches stored session
- Sessions expire after conversation ends

---

## 📝 Changelog & Version

**Current Version**: 0.1.0  
**Author**: Divyansh  
**Last Updated**: August 2024

### Key Components
- ✅ Multi-language support (English/Hindi/Hinglish)
- ✅ Real LLM (Gemini) + Mock agent fallback
- ✅ Site visit booking with failure handling
- ✅ Analytics extraction
- ✅ JWT authentication
- ✅ MongoDB persistence
- ✅ Web UI with chat & auth
- ✅ Comprehensive test suite

---

## 🚀 Production Deployment

### Checklist
- [ ] Set `JWT_SECRET` to a strong, random value
- [ ] Use MongoDB Atlas or managed MongoDB service
- [ ] Set `GEMINI_API_KEY` to valid API key
- [ ] Deploy FastAPI with `uvicorn` + reverse proxy (nginx/Apache)
- [ ] Enable HTTPS/SSL
- [ ] Set appropriate `CORS` headers if frontend is separate
- [ ] Monitor MongoDB connection pool
- [ ] Implement rate limiting on `/api/chat`
- [ ] Log all conversations for compliance & debugging
- [ ] Set up alerting for booking failures

### Example Deployment (Docker)
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install poetry && poetry install --no-dev
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 📚 References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic v2 Documentation](https://docs.pydantic.dev/latest/)
- [Google Generative AI](https://ai.google.dev/)
- [Motor Async MongoDB](https://motor.readthedocs.io/)
- [JWT Authentication](https://tools.ietf.org/html/rfc7519)

---

## 📞 Support

For issues, questions, or suggestions:
1. Check the troubleshooting section above
2. Review test cases in `run_tests.py` for expected behavior
3. Verify environment variables in `.env`
4. Check MongoDB connection and collections
5. Review logs from FastAPI server startup

---

## 📄 License

This project is part of an internal assessment for Northstar Homes.

---

**Ready to deploy! 🚀**
