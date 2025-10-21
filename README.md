# Wordish — Django Web Game

**Wordish** is a server-side version of the classic Wordle-style word guessing game, implemented using the **Django web framework**.  

This project re-creates the Wordish game logic entirely on the **server side** using Django 5.x.  
Unlike the JavaScript version, the browser only renders responses and submits forms — all logic, validation, and game state handling occur in Python on the backend.

Players first visit a **Start Page**, where they enter a target word. After submitting, the **Game Page** allows players to make guesses until they win or lose.

---

## Key Features
- **Full Django MVC architecture** (no client-side JS logic)  
- **Server-side validation** of target and guess words  
- **Stateless design** — no database or session storage; game state is sent with each request  
- **Error handling** for invalid input or tampered data  
- **Custom HTML templates** for the start and game pages  
- **Minimal front-end dependencies** (pure HTML/CSS only)  

---

## Technologies Used
- **Python 3.12**  
- **Django 5.x**  
- **HTML5 / CSS3** (no JS frameworks)  
- **HTTP GET & POST** form handling  
- **MVC (Model-View-Controller)** architecture  

---

## How to Run
1. **Clone this repository:**
   ```bash
   git clone https://github.com/jeongein574/wordish-project.git
   cd wordish-project

2. **Set up a virtual environment:**
    python3 -m venv venv
    source venv/bin/activate

3. **Install dependencies:**
    pip install django==5.*

4. **Run the server:**
    python manage.py runserver

5. **Open your browser:**
    Visit http://localhost:8000