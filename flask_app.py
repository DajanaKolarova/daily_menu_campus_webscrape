from flask import Flask, render_template

from dailymenu_webscrape import restaurants_all

app = Flask(__name__) # vytvoříme si aplikaci flask na cesty

@app.route('/') #dekorátor (zavináč) kterej definuje url
def index():
    restaurants_result = restaurants_all()
    return render_template("index.html", restaurants=restaurants_result)

if __name__ == "__main__":
    app.run(debug=True)