from flask import Flask, render_template, url_for, jsonify, request
from MeetingManager import app, db
from MeetingManager.models import *


@app.route("/")
@app.route("/home")
def home():
    db.create_all()
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


# ajax請求會議資料
@app.route("/getMeetingMinutes")
def getMeetingMinutes():
    return jsonify({'name': '高雄大學第987次會議', 'date': '2021/01/01', 'place': '工學院廁所'})


# ajax請求人員資料
@app.route("/getMemberData")
def getMemberData():
    return jsonify({'name': '黑奴', 'sex': '男', 'phone': '09755111'})


# 接收會議紀錄表單
@app.route("/submitMeetingMinutes", methods=['POST'])
def submitMeetingMinutes():
    #   discussionNameList = request.form.getlist('discussionName')
    #   print(request.values.get('name'))
    discussionBriefList = request.form.getlist('discussionName')
    discussionContentList = request.form.getlist('discussionContent')
    discussionResultList = request.form.getlist('discussionResult')
    announceContentList = request.form.getlist('announceContent')
    extemporeBriefList = request.form.getlist('extemporeName')
    extemporeContentList = request.form.getlist('extemporeContent')
    extemporeResultList = request.form.getlist('extemporeResult')
    # print(request.values.get('name'))
    # print(request.values.get('date'))
    # print(request.values.get('place'))
    # print(request.values.get('type'))
    # 系務會議 系教評會 系課程委員會 招生暨學生事務委員會 系發展委員會
    data = request.values
    temp = data.get('type')
    meetingType = '系務會議'
    if temp == 0:
        meetingType = '系務會議'
    elif temp == 1:
        meetingType = '系教評會'
    elif temp == 2:
        meetingType = '系課程委員會'
    elif temp == 3:
        meetingType = '招生暨學生事務委員會'
    elif temp == 4:
        meetingType = '系發展委員會'

    newMeeting = Meeting(data.get('name'), meetingType, data.get('date'), data.get('place'))

    if discussionBriefList:
        for i in range(len(discussionBriefList)):
            discussion = Discussion(discussionBriefList[i], discussionContentList[i])
            newMeeting.discussion.append(discussion)
            db.session.add(discussion)
    if announceContentList:
        for i in range(len(announceContentList)):
            announce = Announce(announceContentList[i])
            newMeeting.announce.append(announce)
            db.session.add(announce)
    if extemporeBriefList:
        for i in range(len(extemporeBriefList)):
            extempore = Extempore(extemporeBriefList[i], extemporeContentList[i])
            newMeeting.extempore.append(extempore)
            db.session.add(extempore)

    db.session.add(newMeeting)
    db.session.commit()

    return render_template("meeting_manage.html")


# 接收人員資料表單
@app.route("/submitMemberData", methods=['POST'])
def submitMemberData():
    print(request.values.get('name'))
    print(request.values.get('role'))
    print(request.values.get('sex'))
    print(request.values.get('phone'))
    print(request.values.get('email'))

    return render_template("member_manage.html")
