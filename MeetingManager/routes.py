from flask import Flask, render_template, url_for, jsonify
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


@app.route("/getMeetingMinutes")
def getMeetingMinutes():
    return jsonify({'name': '高雄大學第987次會議', 'date': '2021/01/01', 'place': '工學院廁所'})


@app.route("/getMemberData")
def getMemberData():
    return jsonify({'name': '黑奴', 'sex': '男', 'phone': '09755111'})
