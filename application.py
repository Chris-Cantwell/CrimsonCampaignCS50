from flask import Flask, render_template, request, redirect
import os
from cs50 import SQL

def main():
    # Configure application
    app = Flask(__name__)

@app.route("/", methods=["POST", "GET"])
def index():
    return render_template("index.html")

if __name__ == '__main__':
    main()
