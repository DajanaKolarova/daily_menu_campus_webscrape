from flask import Flask, render_template
from dailymenu_webscrape import restaurants_all
app = Flask(__name__)
@app.route('/')
def index():
    restaurants_result = restaurants_all()
    return render_template("index.html", restaurants=restaurants_result)

if __name__ == "__main__":
    app.run(debug=True, port=9999)