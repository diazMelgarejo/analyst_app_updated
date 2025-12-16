from flask import Flask, render_template, request, redirect, url_for, session
import os
try:
    import openai  # type: ignore
except ImportError:
    openai = None

"""
Another AI Liquidity Stock Trader (AnALiST)

This simple Flask application demonstrates how you could integrate the OpenAI ChatGPT API
to generate hypothetical stock price projections based on a user‑supplied ticker symbol.

Functionality:
  * Presents a minimal login screen with a single button to continue.
  * Once "logged in", the user can input a U.S. stock ticker symbol.
  * The app sends a prompt to the OpenAI API (if available) asking for a hypothetical
    30‑day outlook for the given ticker. The response is displayed back to the user.
  * If the OpenAI library is unavailable or no API key is set, a default message is shown.

Important Disclaimer:
  This application is for educational purposes only. It does not constitute financial
  advice, and the projections returned are hypothetical and not based on real market data.
  Always consult a qualified financial advisor before making any investment decisions.
"""

app = Flask(__name__)
# Set a secret key for sessions; in a production system, use a strong random value.
app.secret_key = os.getenv("SECRET_KEY", "replace_with_a_secure_random_key")

# Configure OpenAI API key via environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if openai and OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY


@app.route("/", methods=["GET"])
def home():
    """
    Landing page that redirects users to login if they have not yet logged in.
    """
    if session.get("logged_in"):
        return redirect(url_for("index"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Presents a simple login form. No credentials are required; clicking the button
    will set a session flag that allows access to the main page.
    """
    if request.method == "POST":
        # Simply mark the session as logged in and redirect to main page
        session["logged_in"] = True
        return redirect(url_for("index"))
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    """
    Clears the session and returns the user to the login page.
    """
    session.clear()
    return redirect(url_for("login"))


@app.route("/predict", methods=["POST"])
def predict():
    """
    Handles form submission from the index page. Retrieves the ticker symbol from the
    form, calls the OpenAI API to generate a hypothetical projection, and renders
    the result page.
    """
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    ticker = request.form.get("ticker", "").strip().upper()
    days_str = request.form.get("days", "").strip()
    # Validate ticker: must be 1-5 uppercase letters
    if not ticker or not ticker.isalpha() or len(ticker) > 5:
        return render_template(
            "index.html",
            error="Please enter a valid U.S. stock ticker symbol (1-5 letters).",
            ticker="",
        )
    # Validate days input; default to 30 if invalid
    try:
        days = int(days_str)
        if days < 1 or days > 60:
            raise ValueError
    except Exception:
        days = 30

    # Build a prompt for the AI model with user-specified days
    user_prompt = (
        f"You are a helpful financial assistant. Provide a hypothetical price prediction "
        f"for the U.S. stock ticker symbol '{ticker}' {days} days from today. "
        f"Give the projected closing price down to the cent, followed by a brief commentary "
        f"on why the price might move in that direction. This analysis is for educational "
        f"purposes only and should not be taken as financial advice. Avoid providing any "
        f"guarantees or promises about returns."
    )

    # Default message if OpenAI isn't available
    prediction = (
        "The AI prediction service is currently unavailable. "
        "Ensure that the OpenAI library is installed and the OPENAI_API_KEY environment "
        "variable is set."
    )
    if openai and OPENAI_API_KEY:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an assistant providing hypothetical stock outlooks. "
                            "Your responses should emphasize that predictions are not "
                            "financial advice and should avoid guaranteeing returns."
                        ),
                    },
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=250,
            )
            prediction = response["choices"][0]["message"]["content"].strip()
        except Exception:
            # If any exception occurs (network issues, invalid key, etc.), keep default message
            pass

    return render_template("result.html", ticker=ticker, days=days, prediction=prediction)


@app.route("/index", methods=["GET"])
@app.route("/main", methods=["GET"])
def index():
    """
    Main page where users can enter a stock ticker symbol.
    """
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return render_template("index.html", error=None, ticker="")


if __name__ == "__main__":
    # For local development only; in production use a proper WSGI server
    app.run(host="0.0.0.0", port=5000, debug=True)
