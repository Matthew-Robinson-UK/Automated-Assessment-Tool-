from io import StringIO
from . import staff_stats
from flask_login import current_user
from flask import render_template, url_for, session, make_response
import csv

from ..models import (
    Module,
    Assessment,
    QuestionT1,
    QuestionT2,
    ResponseT1,
    User,
    ResponseT2,
)
from ..db_utils import *

###################################################################
##################### 1. MODULE SELET #############################
###################################################################


@staff_stats.route("/")
def index():
    # establish user's lecturer_id, used throughout Assessment db
    user = User.query.filter_by(name=current_user.name).first()
    user_id = user.id
    name = user.name
    # establish assessments linked to user within Assessment db
    Assessments = Assessment.query.all()
    Modules = Module.query.all()

    lecturersModules = []
    other_modules = []
    lecturersAssessments = []
    for assessment in Assessments:
        if assessment.lecturer_id == user_id:
            lecturersAssessments.append(assessment)

            # establish Modules associated with selected assessments and therefore user.
            moduleId = assessment.module_id
            for module in Modules:
                if (
                    moduleId == module.module_id
                    and module.title not in lecturersModules
                ):
                    lecturersModules.append(module.title)
    for module in Modules:
        if module.title not in lecturersModules:
            other_modules.append(module.title)
    return render_template(
        "Staff-stats.html",
        name=name,
        lecturersModules=lecturersModules,
        other_modules=other_modules,
    )


###################################################################
##################### 2. COHORT VIEW ##############################
###################################################################


@staff_stats.route("/module/<string:Module_title>")
def module(Module_title):
    # restablish user lecturer_id
    session["Module_title"] = Module_title
    user = User.query.filter_by(name=current_user.name).first()
    t1Response = ResponseT1.query.all()
    t2Response = ResponseT2.query.all()
    users = User.query.all()
    module = Module.query.filter_by(title=Module_title).first()
    moduleId = module.module_id
    # print("moduleId",moduleId)
    # print("user id", user.id)
    userInfo = get_all_response_details(None, None, moduleId)
    # print("userInfo",userInfo)

    students = []
    number_of_students = 0
    for user_student in users:
        if user_student.role_id == 1:
            if user_student not in students:
                students.append(user_student)
    moduleAssessments = []
    assessments = Assessment.query.filter_by(module_id=moduleId).all()
    for assessment in assessments:
        assessmentInfo = {}
        if assessment.module_id == moduleId:
            assessmentInfo["assessment_title"] = assessment.title
            if assessment.lecturer_id == user.id:
                assessmentInfo["your_assessment"] = True
            else:
                assessmentInfo["your_assessment"] = False
            assessmentInfo["number_of_credits"] = assessment.num_of_credits
            assessmentInfo["is_summative"] = assessment.is_summative
            assessmentInfo["assessment_id"] = assessment.assessment_id
            assessmentInfo["amount_of_questions"] = 0
            passed = 0
            failed = 0
            for user in users:
                if user.role_id == 1:
                    student_assessment_info = get_all_assessment_marks(
                        user.id, None, None, assessment.assessment_id, True
                    )
                    try:
                        student_assessment_info[0].get("passed")
                        if student_assessment_info[0].get("passed"):
                            passed += 1
                        else:
                            failed += 1

                    except:
                        pass

            assessmentInfo["pass_total"] = passed + failed
            assessmentInfo["passed"] = passed

            moduleAssessments.append(assessmentInfo)
    # print(moduleAssessments)

    moduleAssessmentIds = []
    for assessment in moduleAssessments:
        moduleAssessmentIds.append(assessment.get("assessment_id"))
    # print(moduleAssessmentIds)

    questions = []

    for question in userInfo:
        # print("question",question)
        for assessment in moduleAssessments:
            if assessment.get("assessment_id") == question.get("assessment_id"):
                assessment_title = assessment.get("assessment_title")
        questionDetails = {}
        questionAssessmentId = question.get("assessment_id")
        questionId = question.get("question_id")
        questionDetails["question_assessment_title"] = assessment_title
        questionDetails["question_assessment_id"] = questionAssessmentId
        questionDetails["questionId"] = questionId
        # print("question ID",questionId, "assessmentId",questionAssessmentId)
        nay = 0
        yay = 0

        questionInfo = get_all_assessment_marks(
            None, None, None, questionAssessmentId, True
        )
        for stat in questionInfo:
            if stat.get("assessment_id") == questionAssessmentId:
                assId = stat.get("assessment_id")
                user = stat.get("user_id")
                attempt = stat.get("attempt_number")
                bestAttempt = stat.get("highest_scoring_attempt")

                if bestAttempt == True:
                    bestAttempt = attempt
                # print("user",user,"assId",assId,"best attempt",bestAttempt, "questionID",questionId)

                for user1 in users:
                    if user1.id == user:
                        userRole = user1.role_id
                # print("user role", userRole)
                if userRole == 1:

                    if question.get("question_type") == 2:
                        for response in t2Response:
                            if response.user_id == user:
                                if response.attempt_number == bestAttempt:
                                    if response.assessment_id == assId:
                                        if response.t2_question_id == questionId:
                                            if response.is_correct == True:
                                                # print("YAY")
                                                yay += 1
                                                break

                                            else:
                                                # print("NAY")
                                                nay += 1
                                                break
                    else:
                        for response in t1Response:

                            if response.user_id == user:
                                if response.attempt_number == bestAttempt:
                                    if response.assessment_id == assId:
                                        if response.t1_question_id == questionId:
                                            if response.is_correct == True:
                                                # print("YAY")
                                                yay += 1
                                                break

                                        else:
                                            # print("NAY")
                                            nay += 1
                                            break
                # print("yay", yay)
                # print("nay",nay)

        if yay == 0:
            pass_percentage = 0
            total = yay + nay
        if nay == 0:
            pass_percentage = 100
            total = yay + nay
        else:
            total = yay + nay
            pass_percentage = int((yay / total) * 100)

        students_answered_question = total
        number_of_students = len(students)
        students_not_answered_question = number_of_students - students_answered_question
        if total == 0:
            taken_percentage = 0
        if number_of_students == 0:
            taken_percentage = 100
        else:
            taken_percentage = int(
                (students_answered_question / number_of_students) * 100
            )

        questionDetails[
            "students_not_answered_question"
        ] = students_not_answered_question
        questionDetails["students_answered_question"] = total
        questionDetails["correct_answers"] = yay
        questionDetails["wrong_answers"] = nay
        questionDetails["pass_percentage"] = pass_percentage
        questionDetails["question_text"] = question.get("question_text")
        questionDetails["question_difficulty"] = question.get("question_difficulty")
        questionDetails["question_type"] = question.get("question_type")
        questionDetails["taken_percentage"] = taken_percentage
        # questionDetails["number_of_students"]= len(students)

        questions.append(questionDetails)

    # gets rid of dupped questions
    seen = set()
    questions2 = []
    for question in questions:
        t = tuple(question.items())
        if t not in seen:
            seen.add(t)
            questions2.append(question)
    for question in questions2:
        for assessment in moduleAssessments:
            if question.get("question_assessment_id") == assessment.get(
                "assessment_id"
            ):
                assessment["amount_of_questions"] = (
                    assessment.get("amount_of_questions") + 1
                )

    session["info"] = questions2
    # print("questions", questions2[0])
    # print(moduleAssessments)

    return render_template(
        "module.html",
        Module_title=Module_title,
        moduleAssessments=moduleAssessments,
        questions=questions2,
        number_of_students=number_of_students,
    )


###################################################################
##################### 2.5 CSV DOWNLOAD ############################
###################################################################


@staff_stats.route("/download")
def download():

    module_title = session["Module_title"]
    info = session["info"]
    # print("info",info)
    rows = [
        {
            "Assessment Title": element.get("question_assessment_title"),
            "Question": element.get("question_text"),
            "Difficulty": element.get("question_difficulty"),
            "Question Type": element.get("question_type"),
            "Correct Answers": element.get("correct_answers"),
            "Wrong Answers": element.get("wrong_answers"),
            "Pass rate %": element.get("pass_percentage"),
            "Number of Students answered": element.get("students_answered_question"),
        }
        for element in info
    ]
    string_io = StringIO()
    csv_writer = csv.DictWriter(string_io, rows[0].keys())
    csv_writer.writeheader()
    csv_writer.writerows(rows)
    output = make_response(string_io.getvalue())
    output.headers[
        "Content-Disposition"
    ] = f"attachment; filename={module_title}-aat-export.csv"
    output.headers["Content-type"] = "text/csv"
    return output


###################################################################
##################### 3. STUDENT VIEW #############################
###################################################################


@staff_stats.route("/view-students/<string:assessment>")
def view_students(assessment):
    Module_title = session["Module_title"]
    pass_fail = []
    assessments = Assessment.query.all()
    assessmentID = 0
    for assessment2 in assessments:
        if assessment2.title == assessment:
            assessmentID = assessment2.assessment_id

    users = User.query.all()
    users2 = []

    for user in users:

        if user.role_id == 1:
            userInfo = get_all_response_details(user.id, None, None, assessmentID)
            student_assessment_info = get_all_assessment_marks(
                user.id, None, None, assessmentID, True
            )
            # print(student_assessment_info)
            try:
                student_assessment_info[0].get("passed")
                if student_assessment_info[0].get("passed"):

                    pass_fail.append("Passed")

                else:

                    pass_fail.append("Failed")
            except:
                pass
            attempts = 1
            for question in userInfo:
                if question.get("attempt_number") > attempts:
                    attempts = question.get("attempt_number")
            attemptLists = [[] for i in range(attempts)]
            attemptLists.append(user.name)
            for question in userInfo:
                questions = []
                questions.append(question.get("question_text"))
                questions.append(question.get("question_difficulty"))
                questions.append(question.get("answer_given"))
                questions.append(question.get("is_correct"))
                questions.append(question.get("attempt_number"))
                questions.append(question.get("question_type"))
                if question.get("highest_scoring_attempt"):
                    if question.get("attempt_number") not in attemptLists:
                        attemptLists.append(question.get("attempt_number"))

                attemptLists[question.get("attempt_number") - 1].append(questions)
                # print(user)

            users2.append(attemptLists)
            # print("attemptLists", attemptLists)
    # print(users2)
    # print("pass fail", pass_fail)
    return render_template(
        "view-students.html",
        Module_title=Module_title,
        assessment=assessment,
        users=users,
        users2=users2,
        pass_fail=pass_fail,
    )
