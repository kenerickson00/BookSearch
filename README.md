# Book Search 
Uses LLMs (powered by GroqCloud and HuggingFace Zero Spaces) to search for books using natural language queries

## How to Run
### Deployed Version
Open a browser and navigate to https://book-search-frontend-vert.vercel.app/ and start a search.
Deployed using Vercel (frontend) and render (backend)
    (Note: the backend instance spins down with inactivity and can take a minute or so to start up, so your initial request may be delayed by up to 50 seconds or so)

### Local/Development
#### Frontend
cd book-search-front
npm install
npm run dev

#### Backend
cd book-search-front
python3 -m venv venv
source venv/bin/activate
pip install requirements.txt
fastapi dev main.py

#### Browser
Open http://localhost:3000/ in a browser and start a search