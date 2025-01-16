# Book Search 
Uses LLMs (powered by GroqCloud and HuggingFace Zero Spaces) to search for books using natural language queries

## How to Run
### Frontend
cd book-search-front
npm install
npm run dev

### Backend
cd book-search-front
python3 -m venv venv
source venv/bin/activate
pip install requirements.txt
fastapi dev main.py

### Browser
Open http://localhost:3000/ in a browser and start a search