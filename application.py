from flask import Flask, render_template, request, redirect
import os
from cs50 import SQL

# Configure application
app = Flask(__name__)

db = SQL("postgres://bcbfedessydwun:dbdc8f53173f93f71ff4b7c1ea51fefee2e4dac7d785d312c4f426eae16ce8ab@ec2-54-163-230-178.compute-1.amazonaws.com:5432/dat9s8lnbu4obk")

@app.route("/", methods=["POST", "GET"])
def index():
    return render_template("index.html")

@app.route("/error", methods=["GET"])
def error():
    img = open('Partial-Credit.jpg', 'r')
    return render_template("error.html", img=img)

@app.route("/input", methods=["POST", "GET"])
def input():
    return render_template("error.html")

@app.route("/search", methods=["POST", "GET"])
def search():
    return render_template("error.html")

@app.route("/login", methods=["POST", "GET"])
def login():
    return render_template("error.html")

@app.route("/logout", methods=["POST", "GET"])
def logout():
    return render_template("error.html")
