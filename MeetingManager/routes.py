import os
import time
import smtplib
import email.message

import flask
from flask import render_template, url_for, jsonify, request, redirect, send_from_directory, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

from MeetingManager import app
from MeetingManager.models import *

# 設置附件檔案路徑以及接受檔案格式
UPLOAD_FOLDER = os.path.abspath(os.getcwd()) + '\\MeetingManager\\static\\files'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}


# 格式:
# @app.route("網址")
# def function() --> 當進入網址，執行的function

# redirect()重新導向某頁面，需放入網址頁
# url_for(A)回傳該function A對應的網址頁
# 以上兩者搭配使用

# render_template(網頁,傳入參數) -->選一個html檔案呈現，並先給前端引擎jinja跑再送出，傳入參數可以用於前端呈現

# 基本query方式:class名.query.(all()/first()) 前者全選後者只選第一個
# all()會回還list並把查詢的物件放入 first則支接回傳一個物件

# db.session.commit()當對db做任何更動後必須執行這行才能更新到db內
# db.session.add()若物件還不吋在於db必須先add，若是靠查詢得到則物件只要記得執行上面這行
# db.session.delete()刪除已存在db的資料

# current_user為登入的使用者，並連接到對應的資料庫的member，所以可以直接取用Member屬性
# current_user.permission實際上為Member的屬性，透過這個屬性辨別是否為管理員權限
# @login_required表示需要登入才能進這個網頁

# request是從前端送來後端的資訊
# request.values.get(a)透過a得到對應的value值，概念如同dict有著key:value
# request.form.getlist(a)透過a得到對應的list
# flash()為用來傳訊息給前端

@app.route("/")
@app.route("/home")
def home():
    return render_template("home.html")


# 管理員的會議頁面
@app.route("/meetingManage")
@login_required
def meetingManage():
    if not current_user.permission:
        flash('您的權限不足', 'error')
        return redirect(url_for('meeting'))
    memberList = Member.query.with_entities(Member.id, Member.name).all()  # 查出所有成員，並只留id和名字兩欄
    meetingList = Meeting.query.with_entities(Meeting.id, Meeting.name).all()  # 查出所有會議，並只留id和名字兩欄
    return render_template("meeting_manage.html", meetingList=meetingList, memberList=memberList)


# 一般人查看的會議頁面
@app.route("/meeting")
@login_required
def meeting():
    if current_user.permission:
        return redirect(url_for('meetingManage'))
    tempList = Attend.query.filter_by(memberId=current_user.id).all()  # 查詢有參與的會議
    resultList = []  # 只取其中的id和name
    for element in tempList:
        resultList.append([element.meeting.id, element.meeting.name])
    return render_template("meeting.html", meetingList=resultList)


# 管理員的人員資料管理頁面
@app.route("/memberManage")
@login_required
def memberManage():
    if not current_user.permission:
        flash('您的權限不足', 'error')
        return redirect(url_for('member'))
    memberList = Member.query.with_entities(Member.id, Member.name).all()  # 查出所有成員，並只留id和名字兩欄
    return render_template("member_manage.html", memberList=memberList)


# 個人資料的管理頁面
@app.route("/member")
@login_required
def member():
    if current_user.permission:
        return redirect(url_for('memberManage'))
    memberData = Member.query.filter_by(id=current_user.id).first()  # 查出個人的資料
    return render_template("member.html", member=memberData)


# 附件檔案的管理頁面
@app.route("/fileManage")
@login_required
def fileManage():
    if not current_user.permission:
        flash('您的權限不足', 'error')
        return redirect(url_for('home'))
    meetingList = Meeting.query.with_entities(Meeting.id, Meeting.name).all()  # 查出所有會議，並只留id和名字兩欄
    return render_template('file_manage.html', meetingList=meetingList)


# 出缺席紀錄管理頁面
@app.route("/absent")
@login_required
def absent():
    if not current_user.permission:
        flash('您的權限不足', 'error')
        return redirect(url_for('home'))
    meetingList = Meeting.query.with_entities(Meeting.id, Meeting.name).all()  # 查出所有會議，並只留id和名字兩欄
    return render_template('absent.html', meetingList=meetingList)


# 通知頁面，通知要到來的會議
@app.route("/notification")
@login_required
def notification():
    localtime = time.strftime('%Y-%m-%d', time.localtime())  # 當下時間
    attendMeeting = Attend.query.filter_by(memberId=current_user.id).all()  # 登入的人有參加的
    meetingIdList = []
    for meeting in attendMeeting:
        meetingIdList.append(meeting.meetingId)  # 取出會議的id部分
    attendMeeting = Meeting.query.filter(Meeting.id.in_(meetingIdList)).order_by(Meeting.datetime).all()  # 把有參加的會議照時間排序
    resultList = []
    for meeting in attendMeeting:
        if meeting.datetime > localtime:  # 若時間還沒到即是我們要的
            datetime = meeting.datetime.split('T', 1)  # 字串切割1次，回傳長度為2的陣列，[0]:日期 [1]:時間
            resultList.append(
                [meeting.name, datetime[0], datetime[1], meeting.place, meeting.id])  # 將時間以及需要的額外資訊都加入List
    return render_template("notification.html", meetingList=resultList)


# 追蹤決議事項執行情況
@app.route("/follow")
@login_required
def follow():
    if not current_user.permission:
        flash('您的權限不足', 'error')
        return redirect(url_for('home'))
    completeList = Discussion.query.filter_by(completeOrNot=True).all() + Extempore.query.filter_by(
        completeOrNot=True).all()  # 為完成的事項表
    underwayList1 = Discussion.query.filter_by(completeOrNot=False).all()  # 仍在執行的討論事項決議
    underwayList2 = Extempore.query.filter_by(completeOrNot=False).all()  # 仍在執行的臨時動議決議
    return render_template("follow.html", underwayList1=underwayList1,
                           underwayList2=underwayList2, completeList=completeList)


# 登入頁面
@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.values.get("email") and request.values.get("password"):  # 若email和密碼存在
        user = Member.query.filter_by(email=request.values.get("email")).first()  # 找到email對應的user
        if user and user.password == request.values.get("password"):       # 比對密碼
            login_user(user)    # 登入
            flash('登入成功，歡迎回來，' + current_user.name, 'success')
            return redirect(url_for('home'))
        else:
            flash('帳號或密碼錯誤', 'error')
            return render_template('login.html')
    return render_template('login.html')


# 登出
@app.route("/logout")
def logout():
    logout_user()
    flash('登出成功', 'success')
    return redirect(url_for('home'))


# 請求會議資料
@app.route("/getMeetingMinutes", methods=["GET", 'POST'])
@login_required
def getMeetingMinutes():
    meetingId = request.values.get('meetingId')
    meeting = Meeting.query.filter_by(id=meetingId).first()
    discussionList = modelToList(Discussion.query.filter_by(meetingId=meeting.id))  # 將discussion物件使用自訂函式轉換成二維list形式
    announceList = modelToList(Announce.query.filter_by(meetingId=meeting.id))
    extemporeList = modelToList(Extempore.query.filter_by(meetingId=meeting.id))
    appendixList = modelToList(Appendix.query.filter_by(meetingId=meeting.id)) # 以上都同上
    tempList1 = Attend.query.filter_by(meetingId=meetingId, type='出席').with_entities(Attend.memberId).all()  # 查出該會議的所有出席人員Id
    tempList2 = Attend.query.filter_by(meetingId=meetingId, type='列席').with_entities(Attend.memberId).all()  # 查出該會議的所有列席人員Id
    attendeeList = []
    observerList = []
    for attendee in tempList1:
        attendeeList.append(attendee[0])        # 轉換成一維list形式
    for observer in tempList2:
        observerList.append(observer[0])        # 轉換成一維list形式

    if current_user.permission:     # 判斷是哪種權限索取，回傳不一樣的json檔案回去給前端
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


# 請求人員資料
@app.route("/getMemberData", methods=['POST'])
@login_required
def getMemberData():
    memberId = request.values.get('memberId')
    member = Member.query.filter_by(id=memberId).first()    # 查出對應的成員
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
    return jsonify(data)   # 回傳json回去給前端，data為dict型態


# 下載檔案
@app.route("/getFile", methods=['POST'])
def getFile():
    appendix = Appendix.query.filter_by(id=request.values.get('appendixId')).first()
    return send_from_directory(os.path.dirname(appendix.filePath), os.path.basename(appendix.filePath),
                               as_attachment=True)


# 請求出缺席紀錄
@app.route("/getAbsent", methods=['POST'])
def getAbsent():
    meetingId = request.values.get('meetingId')
    attendeeList = Attend.query.filter_by(meetingId=meetingId).order_by(Attend.memberId).all()
    resultList = []
    for attendee in attendeeList:
        resultList.append([attendee.memberId, attendee.member.name, attendee.attendOrNot])
    return jsonify({'attendeeList': resultList})


# 提交會議紀錄表單
@app.route("/submitMeetingMinutes", methods=['POST'])
def submitMeetingMinutes():
    data = request.values  # 用data來代表request.values，所以data.get等於request.values.get
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
    meeting = Meeting.query.filter_by(id=request.values.get('id')).first()  # 找到對應的meeting
    attendeeList = request.form.getlist('attendee')
    if data.get("chairman") not in attendeeList:  # 若使用者忘記把主席或記錄員放入出席者
        attendeeList.append(data.get("chairman"))
    if data.get("minuteTaker") not in attendeeList:
        attendeeList.append(data.get("minuteTaker"))
    observerList = request.form.getlist('observer')
    if data.get("chairman") in observerList:    # 若使用者不小心把主席或記錄員放入列席者
        observerList.remove(data.get("chairman"))
        flash('請勿將主席加入列席人員，已自動修正為出席人員', 'warning')
    if data.get("minuteTaker") in observerList:
        observerList.remove(data.get("minuteTaker"))
        flash('請勿將記錄人加入列席人員，已自動修正為出席人員', 'warning')
    if meeting is None:         # 若沒找到對應的meeting代表是新的會議資料
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
        db.session.add(newMeeting)
        db.session.commit()
        time.sleep(0.2)  # 讓db有時間更新完再做下面，否則會出現error
        newMeeting = Meeting.query.filter_by(name=data.get('name')).first()  # 重新取得物件，加入與會人員
        for attendeeId in attendeeList:
            newMeeting.attendanceAssociation.append(Attend(newMeeting.id, eval(attendeeId), "出席"))
        for observerId in observerList:
            newMeeting.attendanceAssociation.append(Attend(newMeeting.id, eval(observerId), "列席"))
        db.session.commit()
    else:       # 有找到對應meeting，代表是舊有的會議紀錄
        meeting.set(data.get('name'), data.get('type'), data.get('date'), data.get('place'), data.get('welcomeSpeech'))
        meeting.chairman = data.get('chairman')
        meeting.minuteTaker = data.get('minuteTaker')
        oldDiscussionList = getModelIdList(Discussion.query.filter_by(meetingId=meeting.id).all())
        oldAnnounceList = getModelIdList(Announce.query.filter_by(meetingId=meeting.id).all())
        oldExtemporeList = getModelIdList(Extempore.query.filter_by(meetingId=meeting.id).all())
        if oldDiscussionList:    # 若存在舊討論事項
            for id in oldDiscussionList:
                if id not in discussionIdList:    # 若舊有討論事項不再新的討論事項list內則刪除
                    temp = Discussion.query.filter_by(id=id).first()
                    db.session.delete(temp)
                    oldDiscussionList.remove(id)
        if discussionBriefList:    # 若存在新討論事項
            for i in range(len(discussionIdList)):
                if discussionIdList[i] == '0':     # 若id為0則是新討論事項
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
        for attendee in meeting.attendanceAssociation:       # 會議的舊與會人員表
            if str(attendee.memberId) in attendeeList:       # 若其id在出席人員表，設置為出席人員
                attendee.type = "出席"
                attendeeList.remove(str(attendee.memberId))  # 從新與會人員表刪除
            elif str(attendee.memberId) in observerList:     # 若其id在出席人員表，設置為列席人員
                attendee.type = "列席"
                observerList.remove(str(attendee.memberId))  # 從新與會人員表刪除
            else:       # 若都不在，則表示不為與會人員，從db刪除與會關系
                db.session.delete(attendee)
        # 新與會人員表剩下新成員
        for attendeeId in attendeeList:
            meeting.attendanceAssociation.append(Attend(meeting.id, eval(attendeeId), "出席"))
        for observerId in observerList:
            meeting.attendanceAssociation.append(Attend(meeting.id, eval(observerId), "列席"))
        db.session.commit()
    flash('會議資料儲存成功', 'success')
    return redirect(url_for('meetingManage'))


# 提交人員資料表單(來自個人更改或谷管理員更改)
@app.route("/submitMemberData", methods=['POST'])
@login_required
def submitMemberData():
    data = request.values   # 用data來代表request.values，所以data.get等於request.values.get
    identity = data.get('identity')
    member = Member.query.filter_by(id=data.get('id')).first()      # 查找對應的member
    if not current_user.permission:     # 若權限不是管理員則代表只能更改自己的資料
        member = Member.query.filter_by(id=current_user.id).first()
    if member is None:      # 若不存在member資料
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
    else:         # 若存在member
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
    flash('會員資料儲存成功', 'success')
    if not current_user.permission:
        return redirect(url_for('member'))
    else:
        return redirect(url_for('memberManage'))


# 上傳檔案
@app.route("/submitFile", methods=['POST'])
def submitFile():
    file = request.files['file']
    if file and allowed_file(file.filename):
        fileName = secure_filename(file.filename)       # 設置檔案名稱
        filePath = os.path.join(UPLOAD_FOLDER, fileName)    # 設置存檔位置以及檔名
        file.save(filePath)     # 存檔
        appendix = Appendix(request.values.get('name'), filePath, eval(request.values.get('belongingMeeting')))   # 建立新附件
        db.session.add(appendix)
        db.session.commit()
    flash('檔案上傳成功', 'success')
    return redirect(url_for('fileManage'))


# 提交出缺席紀錄
@app.route("/submitAbsent", methods=['POST'])
def submitAbsent():
    flag = 0  # 用來確保舊的出席紀錄也被更新得
    presentList = request.form.getlist('present')
    meetingId = request.values.get('meetingId')
    oldPresentList = Attend.query.filter_by(meetingId=meetingId).order_by(Attend.memberId).all()    # 查出舊的缺席紀錄，並依id排序
    if len(presentList) == 0:       # 若新的缺席紀錄list為0代表大家都缺席
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
    flash('出缺席紀錄儲存成功', 'success')
    return redirect(url_for('absent'))


# 提交事項為完成
@app.route("/confirmComplete", methods=['POST'])
def confirmComplete():
    if request.values.get('type') == 'discussion':
        discussion = Discussion.query.filter_by(id=request.values.get('id')).first()
        discussion.completeOrNot = 1
    elif request.values.get('type') == 'extempore':
        extempore = Extempore.query.filter_by(id=request.values.get('id')).first()
        extempore.completeOrNot = 1
    db.session.commit()
    flash('更改執行情況成功', 'success')
    return redirect(url_for('follow'))


# 送出開會通知給與會人員
@app.route("/sendMeetingNotice", methods=['POST'])
def sendMeetingNotice():
    meetingId = request.values.get('meetingId')
    receiverList = []
    attendeeList = Attend.query.filter_by(meetingId=meetingId).all()
    meeting = Meeting.query.filter_by(id=meetingId).first()
    if not attendeeList:
        return jsonify({'title': '失敗', 'type': 'warning', 'result': '請先設定與會人員，並先儲存到資料庫'})
    for attendee in attendeeList:
        receiverList.append(attendee.member.email)
    senderMail = 'bluenuk112@gmail.com'
    senderPassword = 'AaBb0000'
    msg = email.message.EmailMessage()
    msg['From'] = senderMail
    msg['Subject'] = '開會通知'
    meetingTime = meeting.datetime.split('T')       # 將開會時間切成日期與時刻
    msg.add_alternative(meeting.name + '在' + meetingTime[0] + '的' + meetingTime[1] + '舉行')  # mail內容
    sever = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    sever.login(senderMail, senderPassword)     # 登入gmail smtp伺服器
    msg['To'] = ', '.join(receiverList)     # 發送對象
    sever.send_message(msg)
    sever.close()
    return jsonify({'title': '成功', 'type': 'success', 'result': '成功送出通知'})


# 刪除會議記錄
@app.route("/deleteMeeting", methods=['POST'])
def deleteMeeting():
    meetingId = request.values.get('deleteId')
    db.session.delete(Meeting.query.filter_by(id=meetingId).first())
    db.session.commit()
    return redirect(url_for('meetingManage'))


# 刪除人員資料
@app.route("/deleteMember", methods=['POST'])
def deleteMember():
    memberId = request.values.get('deleteId')
    if eval(memberId) == current_user.id:
        flash('不能刪除自己', 'warning')
        return redirect(url_for('memberManage'))
    db.session.delete(Member.query.filter_by(id=memberId).first())
    db.session.commit()
    return redirect(url_for('memberManage'))


# 刪除附件檔案
@app.route("/deleteFile", methods=["POST"])
def deleteFile():
    appendix = Appendix.query.filter_by(id=request.values.get('appendixId')).first()
    os.remove(appendix.filePath)
    db.session.delete(appendix)
    db.session.commit()
    return redirect(url_for('meetingManage'))


# 將物件轉換成需要的list
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


# 允許的上傳副檔名
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


# 取出物件陣列的id
def getModelIdList(modelList):
    if not modelList:
        return None
    resultList = []
    for model in modelList:
        resultList.append(str(model.id))
    return resultList
