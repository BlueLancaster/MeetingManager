import os
from flask import Flask, render_template, url_for, jsonify, request, redirect, send_from_directory, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

from MeetingManager import app, db
from MeetingManager.models import *

UPLOAD_FOLDER = os.path.abspath(os.getcwd()) + '\\MeetingManager\\static\\files'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}


@app.route("/")
@app.route("/home")
def home():
    return render_template("home.html")


@app.route("/meetingManage")
@login_required
def meetingManage():
    if not current_user.permission:
        return redirect(url_for('meeting'))
    memberList = Member.query.with_entities(Member.id, Member.name).all()
    meetingList = Meeting.query.with_entities(Meeting.id, Meeting.name).all()
    return render_template("meeting_manage.html", meetingList=meetingList, memberList=memberList)


@app.route("/meeting")
@login_required
def meeting():
    if current_user.permission:
        return redirect(url_for('meetingManage'))
    tempList = Attend.query.filter_by(memberId=current_user.id).all()
    resultList = []
    for element in tempList:
        resultList.append([element.meeting.id, element.meeting.name])
    return render_template("meeting.html", meetingList=resultList)


@app.route("/memberManage")
@login_required
def memberManage():
    if not current_user.permission:
        return redirect(url_for('member'))
    memberList = Member.query.with_entities(Member.id, Member.name).all()
    return render_template("member_manage.html", memberList=memberList)


@app.route("/member")
@login_required
def member():
    if current_user.permission:
        return redirect(url_for('memberManage'))
    memberData = Member.query.filter_by(id=current_user.id).first()
    return render_template("member.html", member=memberData)


@app.route("/fileManage")
@login_required
def fileManage():
    if not current_user.permission:
        return redirect(url_for('home'))
    meetingList = Meeting.query.with_entities(Meeting.id, Meeting.name).all()
    return render_template('file_manage.html', meetingList=meetingList)


@app.route("/absent")
@login_required
def absent():
    if not current_user.permission:
        return redirect(url_for('home'))
    meetingList = Meeting.query.with_entities(Meeting.id, Meeting.name).all()
    return render_template('absent.html', meetingList=meetingList)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.values.get("email") and request.values.get("password"):
        user = Member.query.filter_by(email=request.values.get("email")).first()
        if user and user.password == request.values.get("password"):
            login_user(user)
            flash('登入成功', 'success')
            return redirect(url_for('home'))
    return render_template('login.html')


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


# ajax請求會議資料
@app.route("/getMeetingMinutes", methods=["GET", 'POST'])
@login_required
def getMeetingMinutes():
    meetingId = request.form.get('meetingId')
    meeting = Meeting.query.filter_by(id=meetingId).first()
    discussionList = modelToList(Discussion.query.filter_by(meetingId=meeting.id))
    announceList = modelToList(Announce.query.filter_by(meetingId=meeting.id))
    extemporeList = modelToList(Extempore.query.filter_by(meetingId=meeting.id))
    appendixList = modelToList(Appendix.query.filter_by(meetingId=meeting.id))
    tempList1 = Attend.query.filter_by(meetingId=meetingId, type='出席').with_entities(Attend.memberId).all()
    tempList2 = Attend.query.filter_by(meetingId=meetingId, type='列席').with_entities(Attend.memberId).all()
    attendeeList = []
    observerList = []
    for attendee in tempList1:
        attendeeList.append(attendee[0])
    for observer in tempList2:
        observerList.append(observer[0])

    if current_user.permission:
        return jsonify(
            {'id': meeting.id, 'name': meeting.name, 'date': meeting.datetime, 'place': meeting.place,
             'type': meeting.type, 'chairman': meeting.chairman, 'minuteTaker': meeting.minuteTaker,
             'welcomeSpeech': meeting.welcomeSpeech,
             'discussionList': discussionList, 'announceList': announceList, 'extemporeList': extemporeList,
             'appendixList': appendixList, 'attendeeList': attendeeList, 'observerList': observerList})
    else:
        chairmanName = Member.query.filter_by(id=meeting.chairman).first().name
        minuteTakerName = Member.query.filter_by(id=meeting.minuteTaker).first().name
        return jsonify(
            {'id': meeting.id, 'name': meeting.name, 'date': meeting.datetime, 'place': meeting.place,
             'type': meeting.type, 'chairman': chairmanName, 'minuteTaker': minuteTakerName,
             'welcomeSpeech': meeting.welcomeSpeech,
             'discussionList': discussionList, 'announceList': announceList, 'extemporeList': extemporeList,
             'appendixList': appendixList, 'attendeeList': attendeeList, 'observerList': observerList})


# ajax請求人員資料
@app.route("/getMemberData", methods=['POST'])
@login_required
def getMemberData():
    memberId = request.values.get('memberId')
    member = Member.query.filter_by(id=memberId).first()
    data = {'id': member.id, 'name': member.name, 'identity': member.identity, 'sex': member.sex, 'phone': member.phone,
            'email': member.email,
            'password': member.password, 'permission': member.permission}
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


@app.route("/getFile", methods=['POST'])
def getFile():
    appendix = Appendix.query.filter_by(id=request.values.get('appendixId')).first()
    return send_from_directory(os.path.dirname(appendix.filePath), os.path.basename(appendix.filePath),
                               as_attachment=True)


@app.route("/getAbsent", methods=['POST'])
def getAbsent():
    meetingId = request.values.get('meetingId')
    attendeeList = Attend.query.filter_by(meetingId=meetingId).order_by(Attend.memberId).all()
    resultList = []
    for attendee in attendeeList:
        resultList.append([attendee.memberId, attendee.member.name, attendee.attendOrNot])
    return jsonify({'attendeeList': resultList})


# 接收會議紀錄表單
@app.route("/submitMeetingMinutes", methods=['POST'])
def submitMeetingMinutes():
    data = request.values
    # 傳入str型態變數
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
    attendeeList = request.form.getlist('attendee')
    observerList = request.form.getlist('observer')
    if meeting is None:
        newMeeting = Meeting(data.get('name'), data.get('type'), data.get('date'), data.get('place'),
                             data.get('welcomeSpeech'))
        newMeeting.chairman = data.get("chairman")
        newMeeting.minuteTaker = data.get("minuteTaker")
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
        for attendeeId in attendeeList:
            newMeeting.attendanceAssociation.append(Attend(meeting.id, attendeeId, "出席"))
        for observerId in observerList:
            newMeeting.attendanceAssociation.append(Attend(meeting.id, observerId, "列席"))
        db.session.add(newMeeting)
        db.session.commit()
    else:
        meeting.set(data.get('name'), data.get('type'), data.get('date'), data.get('place'), data.get('welcomeSpeech'))
        meeting.chairman = data.get('chairman')
        meeting.minuteTaker = data.get('minuteTaker')
        oldDiscussionList = getModelIdList(Discussion.query.filter_by(meetingId=meeting.id).all())
        oldAnnounceList = getModelIdList(Announce.query.filter_by(meetingId=meeting.id).all())
        oldExtemporeList = getModelIdList(Extempore.query.filter_by(meetingId=meeting.id).all())
        if oldDiscussionList:
            for id in oldDiscussionList:
                if id not in discussionIdList:
                    temp = Discussion.query.filter_by(id=id).first()
                    db.session.delete(temp)
                    oldDiscussionList.remove(id)
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
        if oldAnnounceList:
            for id in oldAnnounceList:
                if id not in announceIdList:
                    temp = Announce.query.filter_by(id=id).first()
                    db.session.delete(temp)
                    oldAnnounceList.remove(id)
        if announceContentList:
            for i in range(len(announceIdList)):
                if announceIdList[i] == '0':
                    announce = Announce(announceContentList[i])
                    meeting.announce.append(announce)
                    db.session.add(announce)
                else:
                    announce = Announce.query.filter_by(id=announceIdList[i]).first()
                    announce.content = announceContentList[i]
        if oldExtemporeList:
            for id in oldExtemporeList:
                if id not in extemporeIdList:
                    temp = Extempore.query.filter_by(id=id).first()
                    db.session.delete(temp)
                    oldExtemporeList.remove(id)
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
        for attendee in meeting.attendanceAssociation:
            if str(attendee.memberId) in attendeeList:
                attendee.type = "出席"
                attendeeList.remove(str(attendee.memberId))
            elif str(attendee.memberId) in observerList:
                attendee.type = "列席"
                observerList.remove(str(attendee.memberId))
            else:
                db.session.delete(attendee)

        for attendeeId in attendeeList:
            meeting.attendanceAssociation.append(Attend(meeting.id, attendeeId, "出席"))
        for observerId in observerList:
            meeting.attendanceAssociation.append(Attend(meeting.id, observerId, "列席"))
        db.session.commit()
    flash('儲存成功', 'success')
    return redirect(url_for('meetingManage'))


# 接收人員資料表單 Member('mouse','男','0645462','b5645@xuite.net','校外老師','00000')
@app.route("/submitMemberData", methods=['POST'])
@login_required
def submitMemberData():
    data = request.values
    identity = data.get('identity')
    member = Member.query.filter_by(id=data.get('id')).first()
    if not current_user.permission:
        member = Member.query.filter_by(id=current_user.id).first()
    if member is None:
        newMember = Member(data.get('name'), data.get('sex'), data.get('phone'), data.get('email'),
                           data.get('identity'),
                           data.get('password'), eval(data.get("permission")))
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
        if not current_user.permission:
            member.set(data.get('name'), data.get('sex'), data.get('phone'), data.get('email'), data.get('identity'),
                       data.get('password'), False)
        else:
            member.set(data.get('name'), data.get('sex'), data.get('phone'), data.get('email'), data.get('identity'),
                       data.get('password'), eval(data.get("permission")))
    db.session.commit()
    flash('儲存成功', 'success')
    if not current_user.permission:
        return redirect(url_for('member'))
    else:
        return redirect(url_for('memberManage'))


@app.route("/submitFile", methods=['POST'])
def submitFile():
    file = request.files['file']
    if file and allowed_file(file.filename):
        fileName = secure_filename(file.filename)
        filePath = os.path.join(UPLOAD_FOLDER, fileName)
        file.save(filePath)
        appendix = Appendix(request.values.get('name'), filePath, eval(request.values.get('belongingMeeting')))
        db.session.add(appendix)
        db.session.commit()
    flash('儲存成功', 'success')
    return redirect(url_for('fileManage'))


@app.route("/submitAbsent", methods=['POST'])
def submitAbsent():
    flag = 0
    presentList = request.form.getlist('present')
    meetingId = request.values.get('meetingId')
    oldPresentList = Attend.query.filter_by(meetingId=meetingId).order_by(Attend.memberId).all()
    if len(presentList) == 0:
        for attendee in oldPresentList:
            attendee.attendOrNot = 0
    else:
        for attendee in oldPresentList:
            if attendee.memberId == eval(presentList[flag]):
                attendee.attendOrNot = 1
                if flag != len(presentList) - 1:
                    flag += 1
            else:
                attendee.attendOrNot = 0
    db.session.commit()
    flash('儲存成功', 'success')
    return redirect(url_for('absent'))


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


@app.route("/deleteFile", methods=["POST"])
def deleteFile():
    appendix = Appendix.query.filter_by(id=request.values.get('appendixId')).first()
    os.remove(appendix.filePath)
    db.session.delete(appendix)
    db.session.commit()
    return redirect(url_for('meetingManage'))


def modelToList(modelList):
    if not modelList.all():
        return None
    resultList = []
    if isinstance(modelList[0], Discussion) or isinstance(modelList[0], Extempore):
        for discussion in modelList:
            resultList.append([discussion.id, discussion.brief, discussion.content, discussion.result])
        return resultList
    elif isinstance(modelList[0], Announce):
        for announce in modelList:
            resultList.append([announce.id, announce.content])
        return resultList
    elif isinstance(modelList[0], Appendix):
        for appendix in modelList:
            resultList.append([appendix.id, appendix.name])
        return resultList


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def getModelIdList(modelList):
    if not modelList:
        return None
    resultList = []
    for model in modelList:
        resultList.append(str(model.id))
    return resultList
