from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import backref

from MeetingManager import db


class Meeting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True, nullable=False)
    type = db.Column(db.String(10), nullable=False)
    datetime = db.Column(db.String(30), nullable=False)
    place = db.Column(db.String(30), nullable=False)
    chairman = db.Column(db.Integer, db.ForeignKey('member.id'))
    minuteTaker = db.Column(db.Integer, db.ForeignKey('member.id'))
    welcomeSpeech = db.Column(db.Text)
    announce = db.relationship('Announce', backref='meeting', lazy=True, cascade='all, delete-orphan')
    appendix = db.relationship('Appendix', backref='meeting', lazy=True, cascade='all, delete-orphan')
    discussion = db.relationship('Discussion', backref='meeting', lazy=True, cascade='all, delete-orphan')
    extempore = db.relationship('Extempore', backref='meeting', lazy=True, cascade='all, delete-orphan')
    attend = association_proxy('attendanceAssociation', 'member', creator=lambda member: Attend(member=member))

    def __init__(self, name, type, datetime, place):
        self.name = name
        self.type = type
        self.datetime = datetime
        self.place = place


'''
meeting=Meeting(name='mouse',type=4,datetime='4/4',place='44')
member=Member(name='a',sex='girl',phone='4234',email='a4122@yahoo.com',identity=4,password='4645')
'''


class Announce(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    meetingId = db.Column(db.Integer, db.ForeignKey('meeting.id'))

    def __init__(self, content):
        self.content = content


class Discussion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    brief = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=False)
    result = db.Column(db.Text)
    meetingId = db.Column(db.Integer, db.ForeignKey('meeting.id'))

    def __init__(self, brief, content, result):
        self.brief = brief
        self.content = content
        self.result = result


class Extempore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    brief = db.Column(db.Text, nullable=False)
    content = db.Column(db.Text, nullable=False)
    result = db.Column(db.Text)
    meetingId = db.Column(db.Integer, db.ForeignKey('meeting.id'))

    def __init__(self, brief, content, result):
        self.brief = brief
        self.content = content
        self.result = result


class Appendix(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filePath = db.Column(db.String(30), nullable=False)
    meetingId = db.Column(db.Integer, db.ForeignKey('meeting.id'))


class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    sex = db.Column(db.String(6), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(60), nullable=False)
    identity = db.Column(db.String(10), nullable=False)
    password = db.Column(db.String(60), nullable=False)
    assistant = db.relationship('Assistant', backref="personalData", uselist=False, cascade='all, delete-orphan')
    expert = db.relationship('Expert', backref="personalData", uselist=False, cascade='all, delete-orphan')
    student = db.relationship('Student', backref="personalData", uselist=False, cascade='all, delete-orphan')
    externalTeacher = db.relationship('ExternalTeacher', backref="personalData", uselist=False,
                                      cascade='all, delete-orphan')
    intramuralTeacher = db.relationship('IntramuralTeacher', backref="personalData", uselist=False,
                                        cascade='all, delete-orphan')
    attend = association_proxy('attendanceAssociation', 'meeting', creator=lambda meeting: Attend(meeting=meeting))

    def __repr__(self):
        return f"Member('{self.id}','{self.name}','{self.sex}',)"


class Attend(db.Model):
    meetingId = db.Column(db.Integer, db.ForeignKey('meeting.id'), primary_key=True)
    memberId = db.Column(db.Integer, db.ForeignKey('member.id'), primary_key=True)
    attendOrNot = db.Column(db.Boolean, default=False)
    meeting = db.relationship(Meeting, backref=backref('attendanceAssociation', cascade='all, delete-orphan'))
    member = db.relationship(Member, backref=backref('attendanceAssociation', cascade='all, delete-orphan'))


class Assistant(db.Model):
    id = db.Column(db.Integer, db.ForeignKey('member.id'), primary_key=True)
    officePhone = db.Column(db.String(15))


class Expert(db.Model):
    id = db.Column(db.Integer, db.ForeignKey('member.id'), primary_key=True)
    companyName = db.Column(db.String(40), nullable=True)
    title = db.Column(db.String(20), nullable=True)
    officePhone = db.Column(db.String(15))
    address = db.Column(db.String(60))
    bankAccount = db.Column(db.String(30))


class Student(db.Model):
    id = db.Column(db.Integer, db.ForeignKey('member.id'), primary_key=True)
    studentId = db.Column(db.String(10), nullable=False, unique=True)
    eSystem = db.Column(db.String(10), nullable=False)
    grade = db.Column(db.Integer, nullable=False)


class ExternalTeacher(db.Model):
    id = db.Column(db.Integer, db.ForeignKey('member.id'), primary_key=True)
    school = db.Column(db.String(30), nullable=False)
    department = db.Column(db.String(30), nullable=False)
    title = db.Column(db.String(20), nullable=True)
    officePhone = db.Column(db.String(15))
    address = db.Column(db.String(60))
    bankAccount = db.Column(db.String(30))


class IntramuralTeacher(db.Model):
    id = db.Column(db.Integer, db.ForeignKey('member.id'), primary_key=True)
    rank = db.Column(db.Integer, nullable=False)
    officePhone = db.Column(db.String(15))
