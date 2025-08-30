from flask import Flask, render_template

# Create a Flask application instance
app = Flask(__name__)

# Define a route for the home page.
# The '/' URL corresponds to the root of the site.
@app.route('/')
def home():
    """
    This function renders the 'index.html' template when the user
    navigates to the home page.
    """
    return render_template('index.html')

# This block ensures the application runs only when the script is executed directly.
if __name__ == '__main__':
    # Start the Flask development server.
    # The 'debug=True' option enables live reloading for easier development.
    app.run(debug=True)
