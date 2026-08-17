# How to Run AI Researcher

This application can be run using Docker (recommended for easiest setup) or locally on your machine for development.

---

## Option 1: Running with Docker (Recommended)

This application is fully configured to run using Docker and Docker Compose. All required services (Frontend, Backend, PostgreSQL, and Redis) will run automatically inside containers.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/) (Usually included with Docker Desktop)

### Running the Application

1. Open your terminal or command prompt.
2. Ensure you are in the root directory of this project (`ai-researcher/`).
3. Run the following command to build and start all containers in the background (detached mode):

   ```bash
   docker compose up -d --build
   ```

   *Note: The first run might take a while as Docker needs to download the required images and build the application dependencies.*
   
   *Note: Database migrations (`alembic upgrade head`) will be executed automatically when the backend container starts.*

### Accessing the Application

Once all containers are successfully running, you can access the services via:

- **Frontend (Web App):** [http://localhost:3000](http://localhost:3000)
- **Backend API:** [http://localhost:8000](http://localhost:8000)
- **Backend Swagger UI (API Docs):** [http://localhost:8000/docs](http://localhost:8000/docs)

### Useful Docker Commands

- **View real-time logs:** `docker compose logs -f`
- **View logs for a specific service:** `docker compose logs -f backend`
- **Stop containers without removing them:** `docker compose stop`
- **Stop and remove containers:** `docker compose down`
- **Wipe everything (including database volumes):** `docker compose down -v`

---

## Option 2: Running Locally

If you prefer to run the application natively on your machine for development, follow these steps.

### Prerequisites

- [Python 3.9+](https://www.python.org/downloads/)
- [Node.js 18+](https://nodejs.org/)
- PostgreSQL (or run just the DB with Docker)
- Redis (or run just Redis with Docker)

> **Tip:** You can run just the database and cache using Docker by running: `docker compose up -d db redis` from the root directory.

### 1. Backend Setup

1. Open a terminal and navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate on Windows:
   venv\Scripts\activate
   
   # Activate on Mac/Linux:
   source venv/bin/activate
   ```
3. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy the environment variables template and adjust if necessary (ensure `DATABASE_URL` and `REDIS_URL` match your local setup):
   ```bash
   cp .env.example .env
   ```
5. Run database migrations:
   ```bash
   alembic upgrade head
   ```
6. Start the FastAPI server:
   ```bash
   uvicorn app.main:app --reload
   ```
   *The backend will now be running at [http://localhost:8000](http://localhost:8000).*

### 2. Frontend Setup

1. Open a **new** terminal window and navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install the required Node dependencies:
   ```bash
   npm install
   ```
3. Copy the environment variables template:
   ```bash
   cp .env.example .env
   ```
4. Start the Vite development server:
   ```bash
   npm run dev
   ```
   *The frontend will now be running at [http://localhost:5173](http://localhost:5173).*
