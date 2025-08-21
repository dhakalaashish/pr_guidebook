# PR Guidebook
A web app that guides users—from absolute newbies to pros—through the GitHub contribution process. Paste a GitHub Issue URL to generate a dynamic, skill-adaptive checklist that walks users step-by-step from understanding the issue to submitting a pull request.

This project helps make open source onboarding easier by automating guidance, checking best practices, and simplifying the pull request workflow.


## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/your-username/prguidebook.git
cd prguidebook
```

### 2. Setup and run the backend (Flask API)
```bash
cd server
python -m venv venv
# On Linux/macOS:
source venv/bin/activate
# On Windows PowerShell:
 .\venv\Scripts\activate

pip install -r requirements.txt

# Create a .env file in the api/ folder with the following content:
FLASK_APP="api.py"
GITHUB_AUTH_TOKEN="your_github_auth_token"
GEMINI_API_KEY="your_gemini_api_key"

flask run
```

Backend will be running on http://localhost:5000


### 3. Setup and run the frontend (React + Vite)

```bash
cd ../client
npm install

# Create a .env file in the client/ folder with:
# VITE_SERVER_URL=http://127.0.0.1:5000

npm run dev
```

Frontend will be running on http://localhost:5173