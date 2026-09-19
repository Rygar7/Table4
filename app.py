from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def dashboard():
    return render_template("index.html")

@app.route("/money")
def money():
    return render_template("money.html")

@app.route("/calendar")
def calendar():
    return render_template("calendar.html")

@app.route("/goals")
def goals():
    return render_template("goals.html")

@app.route("/stocks")
def stocks():
    return render_template("stocks.html")

@app.route("/nemotron")
def nemotron():
    return render_template("nemotron.html")

if __name__ == "__main__":
    app.run(debug=True)