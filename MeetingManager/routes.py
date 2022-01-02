from flask import Flask, render_template, url_for, jsonify, request, redirect

from MeetingManager import app, db
from MeetingManager.models import *


@app.route("/")
@app.route("/home")
def home():
    db.create_all()
    return render_template("home.html")


@app.route("/meetingManage")
def meetingManage():
    meetingList = Meeting.query.with_entities(Meeting.id, Meeting.name).all()
    return render_template("meeting_manage.html", meetingList=meetingList)


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
@app.route("/getMeetingMinutes", methods=["GET", 'POST'])
def getMeetingMinutes():
    meetingId = request.form.get('meetingId')
    meeting = Meeting.query.filter_by(id=meetingId).first()
    discussionList = ModelToList(Discussion.query.filter_by(meetingId=meeting.id))
    announceList = ModelToList(Announce.query.filter_by(meetingId=meeting.id))
    extemporeList = ModelToList(Extempore.query.filter_by(meetingId=meeting.id))
    return jsonify(
        {'id': meeting.id, 'name': meeting.name, 'date': meeting.datetime, 'place': meeting.place,
         'type': meetingTypeTrans(meeting.type),
         'discussionList': discussionList, 'announceList': announceList, 'extemporeList': extemporeList})


# ajax請求人員資料
@app.route("/getMemberData")
def getMemberData():
    return jsonify({'name': '黑奴', 'sex': '男', 'phone': '09755111'})


# 接收會議紀錄表單
@app.route("/submitMeetingMinutes", methods=['POST'])
def submitMeetingMinutes():
    data = request.values
    discussionIdList = request.form.getlist('discussionId')
    discussionBriefList = request.form.getlist('discussionName')
    discussionContentList = request.form.getlist('discussionContent')
    discussionResultList = request.form.getlist('discussionResult')
    announceIdList = request.form.getlist('announceId')
    announceContentList = request.form.getlist('announceContent')
    extemporeIdList = request.form.getlist('extemporeId')
    extemporeBriefList = request.form.getlist('extemporeName')
    extemporeContentList = request.form.getlist('extemporeContent')
    extemporeResultList = request.form.getlist('extemporeResult')
    meetingType = meetingTypeTrans(eval(data.get('type')))
    meeting = Meeting.query.filter_by(id=request.values.get('id')).first()

    if meeting is None:
        newMeeting = Meeting(data.get('name'), meetingType, data.get('date'), data.get('place'))
        if discussionBriefList:
            for i in range(len(discussionBriefList)):
                discussion = Discussion(discussionBriefList[i], discussionContentList[i], discussionResultList[i])
                newMeeting.discussion.append(discussion)
                db.session.add(discussion)
        if announceContentList:
            for i in range(len(announceContentList)):
                announce = Announce(announceContentList[i])
                newMeeting.announce.append(announce)
                db.session.add(announce)
        if extemporeBriefList:
            for i in range(len(extemporeBriefList)):
                extempore = Extempore(extemporeBriefList[i], extemporeContentList[i], extemporeResultList[i])
                newMeeting.extempore.append(extempore)
                db.session.add(extempore)
        db.session.add(newMeeting)
        db.session.commit()
    else:
        meeting.name = data.get('name')
        meeting.type = meetingType
        meeting.datetime = data.get('date')
        meeting.place = data.get('place')
        if discussionBriefList:
            for i in range(len(discussionIdList)):
                if discussionIdList[i] == '0':
                    discussion = Discussion(discussionBriefList[i], discussionContentList[i], discussionResultList[i])
                    meeting.discussion.append(discussion)
                    db.session.add(discussion)
                else:
                    discussion = Discussion.query.filter_by(id=discussionIdList[i]).first()
                    discussion.brief = discussionBriefList[i]
                    discussion.content = discussionContentList[i]
                    discussion.result = discussionResultList[i]
        if announceContentList:
            for i in range(len(announceIdList)):
                if announceIdList[i] == '0':
                    announce = Announce(announceContentList[i])
                    meeting.announce.append(announce)
                    db.session.add(announce)
                else:
                    announce = Announce.query.filter_by(id=announceIdList[i]).first()
                    announce.content = announceContentList[i]

        if extemporeBriefList:
            for i in range(len(extemporeIdList)):
                if extemporeIdList[i] == '0':
                    extempore = Extempore(extemporeBriefList[i], extemporeContentList[i], extemporeResultList[i])
                    meeting.extempore.append(extempore)
                    db.session.add(extempore)
                else:
                    extempore = Extempore.query.filter_by(id=extemporeIdList[i]).first()
                    extempore.brief = extemporeBriefList[i]
                    extempore.content = extemporeContentList[i]
                    extempore.result = extemporeResultList[i]
        db.session.commit()

    return redirect(url_for('meetingManage'))


#    return render_template("meeting_manage.html")


# 接收人員資料表單
@app.route("/submitMemberData", methods=['POST'])
def submitMemberData():
    print(request.values.get('name'))
    print(request.values.get('role'))
    print(request.values.get('sex'))
    print(request.values.get('phone'))
    print(request.values.get('email'))

    return render_template("member_manage.html")


@app.route("/deleteMeeting", methods=['POST'])
def deleteMeeting():
    meetingId = request.values.get('deleteId')
    db.session.delete(Meeting.query.filter_by(id=meetingId).first())
    db.session.commit()
    return redirect(url_for('meetingManage'))


def meetingTypeTrans(meetingType):
    if type(meetingType) == int:
        if meetingType == 0:
            return '系務會議'
        elif meetingType == 1:
            return '系教評會'
        elif meetingType == 2:
            return '系課程委員會'
        elif meetingType == 3:
            return '招生暨學生事務委員會'
        elif meetingType == 4:
            return '系發展委員會'
    elif type(meetingType) == str:
        if meetingType == '系務會議':
            return 0
        elif meetingType == '系教評會':
            return 1
        elif meetingType == '系課程委員會':
            return 2
        elif meetingType == '招生暨學生事務委員會':
            return 3
        elif meetingType == '系發展委員會':
            return 4


def ModelToList(ModelList):
    if not ModelList.all():
        return None
    resultList = []
    if isinstance(ModelList[0], Discussion) or isinstance(ModelList[0], Extempore):
        for discussion in ModelList:
            resultList.append([discussion.id, discussion.brief, discussion.content, discussion.result])
        return resultList
    elif isinstance(ModelList[0], Announce):
        for announce in ModelList:
            resultList.append([announce.id, announce.content])
        return resultList
