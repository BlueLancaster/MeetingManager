from flask import Flask, render_template, url_for
from MeetingManager import app


@app.route("/")
@app.route("/home")
def home():
    return render_template("home.html")


@app.route("/meetingManage")
def meetingManage():
    return render_template("meeting_manage.html")


@app.route("/memberManage")
def memberManage():
    return render_template("member_manage.html")


@app.route("/fileManage")
def fileManage():
    return render_template('file_manage.html')


@app.route("/absent")
def absent():
    return render_template('absent.html')


@app.route("/login")
def login():
    return render_template('login.html')

