from enum import Enum
from typing import Set, Dict


class Role(str, Enum):
    STUDENT = "student"
    FACULTY = "faculty"
    MENTOR = "mentor"
    HOD = "hod"
    COUNSELLOR = "counsellor"
    FINANCE = "finance"
    PLACEMENT = "placement"
    LEADERSHIP = "leadership"
    INSTITUTION_ADMIN = "institution_admin"
    PLATFORM_ADMIN = "platform_admin"


STAFF_ROLES: Set[Role] = {
    Role.FACULTY,
    Role.MENTOR,
    Role.HOD,
    Role.COUNSELLOR,
    Role.FINANCE,
    Role.PLACEMENT,
    Role.LEADERSHIP,
    Role.INSTITUTION_ADMIN,
}


class Action(str, Enum):
    MANAGE_PLATFORM_CONFIG = "platform.config.manage"
    MANAGE_CAMPUS_USERS = "campus.users.manage"
    VIEW_INSTITUTIONAL_DASHBOARD = "dashboard.institutional.view"
    VIEW_ASSIGNED_CASES = "case.assigned.view"
    UPDATE_ASSIGNED_CASES = "case.assigned.update"
    ASSIGN_CASES = "case.assign"
    MANAGE_INTERVENTIONS = "intervention.manage"
    MANAGE_FOLLOWUPS = "followup.manage"
    VIEW_CONFIDENTIAL_NOTES = "counselling.notes.confidential.view"
    CREATE_CONFIDENTIAL_NOTES = "counselling.notes.confidential.create"
    VIEW_AUDIT_HISTORY = "audit.history.view"
    VIEW_FACULTY_DASHBOARD = "faculty.dashboard.view"
    VIEW_FACULTY_COURSES = "faculty.courses.view"
    VIEW_FACULTY_SECTIONS = "faculty.sections.view"
    VIEW_FACULTY_ROSTER = "faculty.roster.view"
    VIEW_FACULTY_STUDENT = "faculty.student.view"
    MANAGE_ATTENDANCE = "faculty.attendance.manage"
    MANAGE_ASSESSMENTS = "faculty.assessments.manage"
    MANAGE_MARKS = "faculty.marks.manage"
    VIEW_GRADEBOOK = "faculty.gradebook.view"
    VIEW_OBSERVATIONS = "faculty.observations.view"
    EVALUATE_SIGNALS = "faculty.signals.evaluate"
    VIEW_SIGNALS = "faculty.signals.view"
    REVIEW_SIGNALS = "faculty.signals.review"
    VIEW_STUDENT_RECORDS = "student.records.view"
    VIEW_STUDENT_SUPPORT = "student.support.view"
    CREATE_STUDENT_SUPPORT = "student.support.create"
    VIEW_SELF_NOTIFICATIONS = "notification.self.view"


ACTION_PERMISSIONS: Dict[Action, Set[Role]] = {
    Action.MANAGE_PLATFORM_CONFIG: {Role.PLATFORM_ADMIN},
    Action.MANAGE_CAMPUS_USERS: {Role.PLATFORM_ADMIN, Role.INSTITUTION_ADMIN},
    Action.VIEW_INSTITUTIONAL_DASHBOARD: {Role.PLATFORM_ADMIN, Role.INSTITUTION_ADMIN},
    Action.VIEW_ASSIGNED_CASES: {
        Role.PLATFORM_ADMIN,
        Role.INSTITUTION_ADMIN,
        Role.COUNSELLOR,
        Role.FACULTY,
        Role.HOD,
        Role.MENTOR,
    },
    Action.UPDATE_ASSIGNED_CASES: {Role.PLATFORM_ADMIN, Role.COUNSELLOR, Role.FACULTY},
    Action.ASSIGN_CASES: {Role.PLATFORM_ADMIN, Role.INSTITUTION_ADMIN, Role.HOD, Role.COUNSELLOR},
    Action.MANAGE_INTERVENTIONS: {Role.PLATFORM_ADMIN, Role.INSTITUTION_ADMIN, Role.COUNSELLOR, Role.FACULTY},
    Action.MANAGE_FOLLOWUPS: {Role.PLATFORM_ADMIN, Role.COUNSELLOR, Role.FACULTY, Role.MENTOR},
    Action.VIEW_CONFIDENTIAL_NOTES: {Role.COUNSELLOR},
    Action.CREATE_CONFIDENTIAL_NOTES: {Role.COUNSELLOR},
    Action.VIEW_AUDIT_HISTORY: {Role.PLATFORM_ADMIN, Role.INSTITUTION_ADMIN, Role.COUNSELLOR},
    Action.VIEW_FACULTY_DASHBOARD: {Role.FACULTY, Role.HOD, Role.PLATFORM_ADMIN},
    Action.VIEW_FACULTY_COURSES: {Role.FACULTY, Role.HOD, Role.PLATFORM_ADMIN},
    Action.VIEW_FACULTY_SECTIONS: {Role.FACULTY, Role.HOD, Role.PLATFORM_ADMIN},
    Action.VIEW_FACULTY_ROSTER: {Role.FACULTY, Role.HOD, Role.PLATFORM_ADMIN},
    Action.VIEW_FACULTY_STUDENT: {Role.FACULTY, Role.HOD, Role.PLATFORM_ADMIN},
    Action.MANAGE_ATTENDANCE: {Role.FACULTY, Role.HOD, Role.PLATFORM_ADMIN},
    Action.MANAGE_ASSESSMENTS: {Role.FACULTY, Role.HOD, Role.PLATFORM_ADMIN},
    Action.MANAGE_MARKS: {Role.FACULTY, Role.HOD, Role.PLATFORM_ADMIN},
    Action.VIEW_GRADEBOOK: {Role.FACULTY, Role.HOD, Role.PLATFORM_ADMIN},
    Action.VIEW_OBSERVATIONS: {Role.FACULTY, Role.HOD, Role.PLATFORM_ADMIN},
    Action.EVALUATE_SIGNALS: {Role.FACULTY, Role.HOD, Role.PLATFORM_ADMIN},
    Action.VIEW_SIGNALS: {Role.FACULTY, Role.HOD, Role.PLATFORM_ADMIN},
    Action.REVIEW_SIGNALS: {Role.FACULTY, Role.HOD, Role.PLATFORM_ADMIN},
    Action.VIEW_STUDENT_RECORDS: {Role.STUDENT, Role.FACULTY, Role.COUNSELLOR, Role.PLATFORM_ADMIN},
    Action.VIEW_STUDENT_SUPPORT: {Role.STUDENT, Role.FACULTY, Role.COUNSELLOR, Role.PLATFORM_ADMIN},
    Action.CREATE_STUDENT_SUPPORT: {Role.STUDENT},
    Action.VIEW_SELF_NOTIFICATIONS: {Role.STUDENT, Role.FACULTY, Role.COUNSELLOR, Role.PLATFORM_ADMIN},
}
