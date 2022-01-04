from flask import Flask, render_template, url_for, jsonify, request, redirect

from MeetingManager import app, db
from MeetingManager.models import *


@app.route("/")
@app.route("/home")
def home():
    return render_template("home.html")


@app.route("/meetingManage")
def meetingManage():
    meetingList = Meeting.query.with_entities(Meeting.id, Meeting.name).all()
    return render_template("meeting_manage.html", meetingList=meetingList)


@app.route("/memberManage")
def memberManage():
    memberList = Member.query.with_entities(Member.id, Member.name).all()
    return render_template("member_manage.html", memberList=memberList)


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
         'type': meeting.type,
         'discussionList': discussionList, 'announceList': announceList, 'extemporeList': extemporeList})


# ajax請求人員資料
@app.route("/getMemberData", methods=['POST'])
def getMemberData():
    memberId = request.values.get('memberId')
    member = Member.query.filter_by(id=memberId).first()
    data = {'id': member.id, 'name': member.name, 'identity': member.identity, 'sex': member.sex, 'phone': member.phone,
            'email': member.email,
            'password': member.password}
    if member.identity == '系上老師':
        data['rank'] = member.intramuralTeacher.rank
        data['officePhone'] = member.intramuralTeacher.officePhone
    elif member.identity == '系助理':
        data['officePhone'] = member.assistant.officePhone
    elif member.identity == '校外老師':
        data['school'] = member.externalTeacher.school
        data['department'] = member.externalTeacher.department
        data['title'] = member.externalTeacher.title
        data['officePhone'] = member.externalTeacher.officePhone
        data['address'] = member.externalTeacher.address
        data['bankAccount'] = member.externalTeacher.bankAccount
    elif member.identity == '業界專家':
        data['companyName'] = member.expert.companyName
        data['title'] = member.expert.title
        data['officePhone'] = member.expert.officePhone
        data['address'] = member.expert.address
        data['bankAccount'] = member.expert.bankAccount
    elif member.identity == '學生代表':
        data['studentId'] = member.student.studentId
        data['ESystem'] = member.student.eSystem
        data['grade'] = member.student.grade
    return jsonify(data)


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
    meeting = Meeting.query.filter_by(id=request.values.get('id')).first()

    if meeting is None:
        newMeeting = Meeting(data.get('name'), data.get('type'), data.get('date'), data.get('place'))
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
        meeting.type = data.get('type')
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


# 接收人員資料表單 Member('mouse','男','0645462','b5645@xuite.net','校外老師','00000')
@app.route("/submitMemberData", methods=['POST'])
def submitMemberData():
    data = request.values
    identity = data.get('identity')
    member = Member.query.filter_by(id=data.get('id')).first()
    if member is None:
        newMember = Member(data.get('name'), data.get('sex'), data.get('phone'), data.get('email'),
                           data.get('identity'),
                           data.get('password'))
        if identity == '系上老師':
            moreInfo = IntramuralTeacher(data.get('rank'), data.get('officePhone'))
            newMember.intramuralTeacher = moreInfo
            db.session.add(moreInfo)
        elif identity == '系助理':
            moreInfo = Assistant(data.get('officePhone'))
            newMember.assistant = moreInfo
            db.session.add(moreInfo)
        elif identity == '校外老師':
            moreInfo = ExternalTeacher(data.get('school'), data.get('department'), data.get('title'),
                                       data.get('officePhone'), data.get('address'), data.get('bankAccount'))
            newMember.externalTeacher = moreInfo
            db.session.add(moreInfo)
        elif identity == '業界專家':
            moreInfo = Expert(data.get('companyName'), data.get('title'), data.get('officePhone'), data.get('address'),
                              data.get('bankAccount'))
            newMember.expert = moreInfo
            db.session.add(moreInfo)
        elif identity == '學生代表':
            moreInfo = Student(data.get('studentId'), data.get('ESystem'), eval(data.get('grade')))
            newMember.student = moreInfo
            db.session.add(moreInfo)
        db.session.add(newMember)
    else:
        if identity == member.identity:
            if identity == '系上老師':
                member.intramuralTeacher.set(data.get('rank'), data.get('officePhone'))
            elif identity == '系助理':
                member.assistant.set(data.get('officePhone'))
            elif identity == '校外老師':
                member.externalTeacher.set(data.get('school'), data.get('department'), data.get('title'),
                                           data.get('officePhone'), data.get('address'), data.get('bankAccount'))
            elif identity == '業界專家':
                member.expert.set(data.get('companyName'), data.get('title'), data.get('officePhone'),
                                  data.get('address'),
                                  data.get('bankAccount'))
            elif identity == '學生代表':
                member.student.set(data.get('studentId'), data.get('ESystem'), eval(data.get('grade')))
        else:
            if member.identity == '系上老師':
                db.session.delete(member.intramuralTeacher)
            elif member.identity == '系助理':
                db.session.delete(member.assistant)
            elif member.identity == '校外老師':
                db.session.delete(member.externalTeacher)
            elif member.identity == '業界專家':
                db.session.delete(member.expert)
            elif member.identity == '學生代表':
                db.session.delete(member.student)
            if identity == '系上老師':
                moreInfo = IntramuralTeacher(data.get('rank'), data.get('officePhone'))
                member.intramuralTeacher = moreInfo
                db.session.add(moreInfo)
            elif identity == '系助理':
                moreInfo = Assistant(data.get('officePhone'))
                member.assistant = moreInfo
                db.session.add(moreInfo)
            elif identity == '校外老師':
                moreInfo = ExternalTeacher(data.get('school'), data.get('department'), data.get('title'),
                                           data.get('officePhone'), data.get('address'), data.get('bankAccount'))
                member.externalTeacher = moreInfo
                db.session.add(moreInfo)
            elif identity == '業界專家':
                moreInfo = Expert(data.get('companyName'), data.get('title'), data.get('officePhone'),
                                  data.get('address'),
                                  data.get('bankAccount'))
                member.expert = moreInfo
                db.session.add(moreInfo)
            elif identity == '學生代表':
                moreInfo = Student(data.get('studentId'), data.get('ESystem'), eval(data.get('grade')))
                member.student = moreInfo
                db.session.add(moreInfo)
        member.set(data.get('name'), data.get('sex'), data.get('phone'), data.get('email'), data.get('identity'),
                   data.get('password'))

    db.session.commit()
    return redirect(url_for('memberManage'))


@app.route("/deleteMeeting", methods=['POST'])
def deleteMeeting():
    meetingId = request.values.get('deleteId')
    db.session.delete(Meeting.query.filter_by(id=meetingId).first())
    db.session.commit()
    return redirect(url_for('meetingManage'))


@app.route("/deleteMember", methods=['POST'])
def deleteMember():
    memberId = request.values.get('deleteId')
    db.session.delete(Member.query.filter_by(id=memberId).first())
    db.session.commit()
    return redirect(url_for('memberManage'))


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
