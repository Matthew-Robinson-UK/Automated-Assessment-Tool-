from datetime import date, datetime
import math
import random
from stringprep import in_table_d2
from black import diff
from flask import (
    Response,
    flash,
    redirect,
    render_template,
    request,
    url_for,
    abort,
    session,
)
from . import assessments

from ..models import (
    Assessment,
    QuestionT1,
    QuestionT2,
    Module,
    User,
    ResponseT2,
    ResponseT2,
    ResponseT1,
    Option,
    Tag,
)
from .forms import (
    AddQuestionToAssessmentForm,
    CreateQuestionT1Form,
    CreateQuestionT2Form,
    DeleteQuestionsForm,
    AnswerType1Form,
    AnswerType2Form,
    AssessmentForm,
    DeleteAssessmentForm,
    EditAssessmentForm,
    FinishForm,
    RandomQuestionsForm,
    RemoveQuestionForm,
)
from .. import db
from flask_login import current_user


@assessments.route("/")
def index():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))
    assessments = Assessment.query.all()
    modules = Module.query.all()
    module_credits = dict()
    for module in modules:
        assessment_credits = 0
        assessment_modules = Assessment.query.filter_by(
            module_id=module.module_id
        ).all()
        for assessment in assessment_modules:
            try:
                assessment_credits += int(assessment.num_of_credits)
            except:
                assessment_credits += 0
            module_credits[module.title] = assessment_credits
    return render_template(
        "index.html",
        assessments=assessments,
        modules=modules,
        module_credits=module_credits,
    )


@assessments.route("/view_module/<int:module_id>")
def view_module(module_id):
    session["module_id"] = module_id
    module = Module.query.filter_by(module_id=module_id).first()
    assessments = Assessment.query.filter_by(module_id=module.module_id).all()
    topic_tags = []
    summatives = []
    formatives = []
    marks_achieved = dict()
    best_attempt = dict()
    # ----> find all tags
    assess_tags = dict()
    difficulties = dict()
    for assessment in assessments:
        # ----> find all questions
        qs = (
            QuestionT1.query.filter_by(assessment_id=assessment.assessment_id).all()
            + QuestionT2.query.filter_by(assessment_id=assessment.assessment_id).all()
        )

        # ---> calculate marks available
        marks_av = 0
        difficulty_figures = []
        for q in qs:
            tag = Tag.query.filter_by(id=q.tag_id).first()

            if tag is not None:
                if not tag in topic_tags:
                    topic_tags.append(tag)
                if assessment.title in assess_tags:
                    if not tag.name in assess_tags[assessment.title]:
                        assess_tags[assessment.title].append(tag.name)
                else:
                    assess_tags[assessment.title] = [tag.name]
            difficulty_figures.append(q.difficulty)
            marks_av += q.num_of_marks
        if len(difficulty_figures) == 0:
            final_difficulty = 0
        else:
            final_difficulty = round(sum(difficulty_figures) / len(difficulty_figures))
        difficulties[assessment.title] = final_difficulty
        # ---> check if user has responded to assessment
        if current_user.has_taken(assessment):
            attempts_taken = current_user.current_attempts(assessment)
            result_of_attempts = dict()
            highest_result = 0

            # --- > break out achieved result for each attempt
            for attempt in range(1, attempts_taken + 1):
                t1_responses = (
                    current_user.t1_responses.filter_by(
                        assessment_id=assessment.assessment_id
                    )
                    .filter_by(attempt_number=attempt)
                    .all()
                )
                t2_responses = (
                    current_user.t2_responses.filter_by(
                        assessment_id=assessment.assessment_id
                    )
                    .filter_by(attempt_number=attempt)
                    .all()
                )

                # ---> find what user's result was
                res = 0
                for response in t1_responses:
                    if response.is_correct:
                        answered_question = QuestionT1.query.filter_by(
                            q_t1_id=response.t1_question_id
                        ).first()
                        res += answered_question.num_of_marks
                for response in t2_responses:
                    if response.is_correct:
                        answered_question = QuestionT2.query.filter_by(
                            q_t2_id=response.t2_question_id
                        ).first()
                        res += answered_question.num_of_marks
                result_of_attempts[attempt] = res

            # --- > find the highest result achieved across all attempts
            d_ref = max(result_of_attempts, key=result_of_attempts.get)
            result = result_of_attempts[d_ref]
            best_attempt[assessment.title] = d_ref
        else:
            result = 0
            best_attempt[assessment.title] = 0
        marks_achieved[assessment.title] = f"{result}/{marks_av}"

        if assessment.is_summative:
            summatives.append(assessment)
        else:
            formatives.append(assessment)
    session["assessment_tags"] = assess_tags
    session["prev_random"] = None
    return render_template(
        "view_module.html",
        module=module,
        assessments=assessments,
        summatives=summatives,
        formatives=formatives,
        marks_achieved=marks_achieved,
        assess_tags=assess_tags,
        best_attempt=best_attempt,
        topic_tags=topic_tags,
        difficulties=difficulties,
    )


@assessments.route("/<int:id>")
def show_assessment(id):
    assessment = Assessment.query.get_or_404(id)
    assessment_id = id
    t1_difficulty = 0
    t2_difficulty = 0
    t1_total = 0
    t2_total = 0
    count_t1 = 0
    count_t2 = 0
    questions_t1 = QuestionT1.query.filter_by(assessment_id=assessment_id).all()
    questions_t2 = QuestionT2.query.filter_by(assessment_id=assessment_id).all()
    for question in questions_t1:
        count_t1 += 1
        t1_difficulty = (t1_difficulty + question.difficulty) / count_t1
        t1_total += question.num_of_marks
    for question in questions_t2:
        count_t2 += 1
        t2_difficulty = (t2_difficulty + question.difficulty) / count_t2
        t2_total += question.num_of_marks
    assessment_difficulty = math.ceil((t1_difficulty + t2_difficulty) / 2)
    assessment_num_of_marks = t1_total + t2_total
    try:
        time_limit_minutes = math.floor(int(assessment.time_limit) / 60)
    except:
        time_limit_minutes = None
    try:
        current_date = assessment.due_date.strftime("%d/%m/%Y")
    except:
        current_date = None
    if assessment.is_summative == False:
        assessment_type = "Formative"
    elif assessment.is_summative == True:
        assessment_type = "Summative"
    # TODO make a combined list of T1 and T2 questions and order by their question index
    questions = (
        QuestionT1.query.filter_by(assessment_id=id).all()
        + QuestionT2.query.filter_by(assessment_id=id).all()
    )
    return render_template(
        "show_assessment.html",
        assessment=assessment,
        questions=questions,
        current_date=current_date,
        time_limit_minutes=time_limit_minutes,
        assessment_type=assessment_type,
        assessment_difficulty=assessment_difficulty,
        assessment_num_of_marks=assessment_num_of_marks,
    )


# Matt ---> You  could probably adapt this for your assessment CRUD
# as it will let you remove multiple questions from an assessment.
@assessments.route("/<int:id>/delete_questions", methods=["GET", "POST"])
def delete_questions(id):
    assessment = Assessment.query.get_or_404(id)
    questions_t2 = QuestionT2.query.filter_by(assessment_id=id).all()
    form = DeleteQuestionsForm()
    form.questions_to_delete.choices = [
        (question.q_t2_id, question.question_text[:20]) for question in questions_t2
    ]
    if request.method == "POST":
        # Query which returns the questions that were selected for deletion
        for_deletion = [int(q) for q in form.questions_to_delete.data]
        questions_to_delete = QuestionT2.query.filter(
            QuestionT2.q_t2_id.in_(for_deletion)
        ).all()
        for question in questions_to_delete:
            db.session.delete(question)
        db.session.commit()
        return redirect(url_for("assessments.show_assessment", id=id))
    return render_template("delete_questions.html", assessment=assessment, form=form)


# ---------------------------------  CRUD For Assessments ---------------------------------------


@assessments.route("/<int:module_id>/assessment/new", methods=["GET", "POST"])
def new_assessment(module_id):
    session.pop("assessment_edit", None)
    session.pop("assessment_add", None)
    module = Module.query.filter_by(module_id=module_id).first()
    form = AssessmentForm()
    is_summative_1 = ""
    session["user"] = current_user.id
    form.module_id.choices = [
        (module.module_id, module.title) for module in Module.query.all()
    ]
    if request.method == "POST":
        lecturer_id = session["user"]
        is_summative = False
        title = request.form["title"]
        time_limit = request.form["time_limit"]
        module_id = form.module_id.data
        num_of_credits = request.form["num_of_credits"]
        if form.validate_on_submit:
            total_date = form.due_date.data
            if total_date != None:
                total_date = total_date.strftime("%Y-%m-%d")
                if total_date >= date.today().strftime("%Y-%m-%d"):
                    year = int(total_date[:4])
                    month = int(total_date[5:7])
                    day = int(total_date[8:10])
                    due_date = datetime(year, month, day)
                else:
                    flash("Due date cannot be in the past", "error")
                    return render_template(
                        "new_assessment.html", form=form, module_id=module_id
                    )
            else:
                due_date = None
        try:
            is_summative_1 = request.form["is_summative"]
        except:
            pass
        if is_summative_1 == "y":
            is_summative = True

        new_assessment = Assessment(
            title=title,
            due_date=due_date,
            time_limit=int(time_limit) * 60,
            num_of_credits=num_of_credits,
            is_summative=is_summative,
            lecturer_id=lecturer_id,
            module_id=module_id,
        )
        db.session.add(new_assessment)
        db.session.commit()
        id = new_assessment.assessment_id
        session["assessment_add"] = id
        return redirect(url_for("assessments.add_questions", id=id))
    form.module_id.data = str(module.module_id)
    return render_template("new_assessment.html", form=form, module_id=module_id)


@assessments.route("/<int:id>/edit_assessment", methods=["GET", "POST"])
def edit_assessment(id):
    session.pop("assessment_add", None)
    session.pop("assessment_edit", None)
    assessment = Assessment.query.get_or_404(id)
    form = EditAssessmentForm()
    session["assessment_edit"] = id
    form.module_id.choices = [
        (module.module_id, module.title) for module in Module.query.all()
    ]
    if request.method == "POST":
        assessment.title = form.title.data
        assessment.module_id = form.module_id.data
        assessment.num_of_credits = form.num_of_credits.data
        time_limit = request.form["time_limit"]
        try:
            assessment.time_limit = int(time_limit) * 60
        except:
            pass
        assessment.is_summative = form.is_summative.data
        total_date = form.due_date.data
        if total_date == None:
            db.session.commit()
            return redirect(url_for("assessments.add_questions", id=id))
        else:
            total_date = total_date.strftime("%Y-%m-%d")
            year = int(total_date[:4])
            month = int(total_date[5:7])
            day = int(total_date[8:10])
            assessment.due_date = datetime(year, month, day)
            if assessment.due_date.strftime("%Y-%m-%d") >= date.today().strftime(
                "%Y-%m-%d"
            ):
                db.session.commit()
                return redirect(url_for("assessments.add_questions", id=id))
            else:
                flash("Due date cannot be in the past", "error")
                return render_template(
                    "edit_assessments.html", form=form, assessment=assessment, id=id
                )

    form.title.data = assessment.title
    form.module_id.data = str(assessment.module_id)
    form.due_date.data = assessment.due_date
    form.num_of_credits.data = assessment.num_of_credits
    if assessment.time_limit != None:
        form.time_limit.data = math.floor(int(assessment.time_limit) / 60)
    else:
        form.time_limit.data = assessment.time_limit
    form.is_summative.data = assessment.is_summative
    return render_template(
        "edit_assessments.html", form=form, assessment=assessment, id=id
    )


@assessments.route("/<int:id>/delete_assessment", methods=["GET", "POST"])
def delete_assessment(id):
    assessment = Assessment.query.get_or_404(id)
    module_id = session.get("module_id")
    form = DeleteAssessmentForm()
    if request.method == "POST":
        try:
            request.form["submit"]
            db.session.delete(assessment)
            db.session.commit()
            flash("Assessment Deleted", "info")
            return redirect(url_for("assessments.view_module", module_id=module_id))
        except:
            request.form["cancel"]
            return redirect(url_for("assessments.view_module", module_id=module_id))
    return render_template(
        "delete_assessment.html",
        assessment=assessment,
        form=form,
        id=id,
        module_id=module_id,
    )


@assessments.route(
    "/<int:id>/edit_assessment/remove/t2/<int:id2>", methods=["GET", "POST"]
)
def remove_question_t2(id, id2):
    question = QuestionT2.query.get_or_404(id2)
    assessment = Assessment.query.get_or_404(id)
    form = RemoveQuestionForm()
    if request.method == "POST" and form.is_submitted:
        question.assessment_id = None
        db.session.commit()
        flash("Question removed", "info")
        return redirect(url_for("assessments.edit_assessment", id=id))
    return render_template(
        "remove_question.html",
        question=question,
        form=form,
        assessment=assessment,
        id=id,
    )


@assessments.route(
    "/<int:id>/edit_assessment/remove/t1/<int:id3>", methods=["GET", "POST"]
)
def remove_question_t1(id, id3):
    question = QuestionT1.query.get_or_404(id3)
    assessment = Assessment.query.get_or_404(id)
    form = RemoveQuestionForm()
    if request.method == "POST" and form.is_submitted:
        question.assessment_id = None
        db.session.commit()
        flash("Question removed", "info")
        return redirect(url_for("assessments.edit_assessment", id=id))
    return render_template(
        "remove_question.html", question=question, form=form, assessment=assessment
    )


@assessments.route("/add_questions/<int:id>", methods=["GET", "POST"])
def add_questions(id):
    if session.get("assessment_add") != None:
        id = session.get("assessment_add")
    elif session.get("assessment_edit") != None:
        id = session.get("assessment_edit")
    form = FinishForm()
    forms = []
    randomiser = RandomQuestionsForm()
    assessment = Assessment.query.get_or_404(id)
    addQuestionForm = AddQuestionToAssessmentForm()
    questions = (
        QuestionT1.query.filter(QuestionT1.assessment_id.is_(None)).all()
        + QuestionT2.query.filter(QuestionT2.assessment_id.is_(None)).all()
    )
    if randomiser.validate_on_submit() and randomiser.random.data:
        difficulty_level = randomiser.question_difficulty.data
        difficulty_level = int(difficulty_level)
        for question in questions:
            if difficulty_level == question.difficulty:
                question.assessment_id = assessment.assessment_id
                db.session.commit()
        flash("Questions added to assessment", "success")
        return redirect(
            url_for(
                "assessments.add_questions",
                questions=questions,
                id=id,
                addQuestionForm=addQuestionForm,
                form=form,
                randomiser=randomiser,
            )
        )

    for question in questions:
        try:
            addForm = AddQuestionToAssessmentForm(prefix=str(question.q_t1_id))
        except:
            addForm = AddQuestionToAssessmentForm(prefix=str(question.q_t2_id))
        forms.append(addForm)
        for f in forms:
            if f.validate_on_submit() and f.add.data:
                question.assessment_id = assessment.assessment_id
                db.session.commit()
                flash("Question Added", "success")
                return redirect(
                    url_for(
                        "assessments.add_questions",
                        questions=questions,
                        id=id,
                        addQuestionForm=addQuestionForm,
                        form=form,
                        randomiser=randomiser,
                    )
                )
    questions_and_forms = zip(questions, forms)
    if form.validate_on_submit() and form.finish.data:
        if session.get("assessment_edit") != None:
            flash("Assessment Updated", "success")
        elif session.get("assessment_add") != None:
            flash("Assessment Added", "success")
        return redirect(url_for("assessments.show_assessment", id=id))
    return render_template(
        "add_questions.html",
        questions=questions,
        id=id,
        addQuestionForm=addQuestionForm,
        form=form,
        assessment=assessment,
        randomiser=randomiser,
        questions_and_forms=questions_and_forms,
    )


@assessments.route("/<int:id>/type1/new", methods=["GET", "POST"])
def create_questions_t1(id):
    form = CreateQuestionT1Form()
    assessment = Assessment.query.get_or_404(id)
    if session.get("assessment_add") != None:
        id = session.get("assessment_add")
        print(id)
    elif session.get("assessment_edit") != None:
        id = session.get("assessment_edit")
        print(id)
    if request.method == "POST":
        question_text = request.form["question_text"]
        option_a_text = request.form["option_a"]
        option_b_text = request.form["option_b"]
        option_c_text = request.form["option_c"]
        correct_option = request.form["correct_option"]
        tag_id = request.form["tag"]
        # print(correct_option)
        num_of_marks = request.form["num_of_marks"]
        difficulty = request.form["difficulty"]
        feedback_if_correct = request.form["feedback_if_correct"]
        feedback_if_wrong = request.form["feedback_if_wrong"]
        feedforward_if_correct = request.form["feedforward_if_correct"]
        feedforward_if_wrong = request.form["feedforward_if_wrong"]
        new_question = QuestionT1(
            question_text=question_text,
            tag_id=tag_id,
            num_of_marks=num_of_marks,
            difficulty=difficulty,
            feedback_if_correct=feedback_if_correct,
            feedback_if_wrong=feedback_if_wrong,
            feedforward_if_correct=feedforward_if_correct,
            feedforward_if_wrong=feedforward_if_wrong,
            assessment_id=id,
        )
        db.session.add(new_question)
        found_question = QuestionT1.query.filter(
            QuestionT1.question_text == new_question.question_text
        ).first()
        option_a = Option(q_t1_id=found_question.q_t1_id, option_text=option_a_text)
        option_b = Option(q_t1_id=found_question.q_t1_id, option_text=option_b_text)
        option_c = Option(q_t1_id=found_question.q_t1_id, option_text=option_c_text)
        if correct_option == "0":
            option_a.is_correct = True
        elif correct_option == "1":
            option_b.is_correct = True
        elif correct_option == "2":
            option_c.is_correct = True
        db.session.add(option_a)
        db.session.add(option_b)
        db.session.add(option_c)
        db.session.commit()
        if session.get("assessment_edit") != None:
            flash("Question added to Assessment", "success")
            return redirect(url_for("assessments.add_questions", id=id))
        elif session.get("assessment_add") != None:
            flash("Question added to Assessment", "success")
            return redirect(url_for("assessments.add_questions", id=id))
    form.tag.choices = [(tag.id, tag.name) for tag in Tag.query.all()]
    return render_template(
        "create_questions_t1.html", form=form, id=id, assessment=assessment
    )


@assessments.route("/<int:id>/type2/new", methods=["GET", "POST"])
def create_question_t2(id):
    form = CreateQuestionT2Form()
    assessment = Assessment.query.get_or_404(id)
    if session.get("assessment_add") != None:
        id = session.get("assessment_add")
        print(id)
    elif session.get("assessment_edit") != None:
        id = session.get("assessment_edit")
        print(id)
    if request.method == "POST":
        question_text = request.form["question_text"]
        correct_answer = request.form["correct_answer"]
        tag_id = request.form["tag"]
        num_of_marks = request.form["num_of_marks"]
        difficulty = request.form["difficulty"]
        feedback_if_correct = request.form["feedback_if_correct"]
        feedback_if_wrong = request.form["feedback_if_wrong"]
        feedforward_if_correct = request.form["feedforward_if_correct"]
        feedforward_if_wrong = request.form["feedforward_if_wrong"]
        new_question = QuestionT2(
            question_text=question_text,
            correct_answer=correct_answer,
            tag_id=tag_id,
            num_of_marks=num_of_marks,
            difficulty=difficulty,
            feedback_if_correct=feedback_if_correct,
            feedback_if_wrong=feedback_if_wrong,
            feedforward_if_correct=feedforward_if_correct,
            feedforward_if_wrong=feedforward_if_wrong,
            assessment_id=id,
        )
        db.session.add(new_question)
        db.session.commit()
        if session.get("assessment_edit") != None:
            session.pop("assessment_edit", None)
            return redirect(url_for("assessments.add_questions", id=id))
        elif session.get("assessment_add") != None:
            session.pop("assessment_add", None)
            return redirect(url_for("assessments.add_questions", id=id))
    form.tag.choices = [(tag.id, tag.name) for tag in Tag.query.all()]
    return render_template(
        "create_questions_t2.html", form=form, id=id, assessment=assessment
    )


# ---------------------------------  End Of CRUD For Assessments ---------------------------------------


# ----------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------
# ---------------------------------  Start of TAKE ASSESSMENT  ---------------------------------------
# ----------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------
# ----------------------------------------------------------------------------------------------------


## example of how to filter response table
@assessments.route("/test_response_model/<int:assessment_id>/<int:question_id>")
def test_response_model(assessment_id, question_id):
    results = (
        current_user.t2_responses.filter_by(assessment_id=assessment_id)
        .filter_by(question_id=question_id)
        .all()
    )
    return render_template("results.html", results=results)


@assessments.route("/assessment_summary/<int:assessment_id>", methods=["GET", "POST"])
def assessment_summary(assessment_id):
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))
    assessment = Assessment.query.get_or_404(assessment_id)
    if assessment is None:
        return redirect(url_for("assessments"))
    session["is_summative"] = assessment.is_summative
    ## query to find all questions in assessment, so can be used to find their ID's and store these in session variable
    ## session variable is then accessed throughout the process to find questions and store their responses
    questions_t1 = QuestionT1.query.filter_by(assessment_id=assessment_id).all()
    questions_t2 = QuestionT2.query.filter_by(assessment_id=assessment_id).all()
    if len(questions_t1) == 0 and len(questions_t2) == 0:
        return redirect(url_for("assessments.empty_assessment"))

    # ---- > create list of questions to cover in assessment
    question_ids = []
    difficulties = []
    for question in questions_t1:
        difficulties.append(question.difficulty)
        question_info = (1, question.q_t1_id)
        question_ids.append(question_info)
    for question in questions_t2:
        difficulties.append(question.difficulty)
        question_info = (2, question.q_t2_id)
        question_ids.append(question_info)
    random.shuffle(question_ids)
    final_difficulty = round(sum(difficulties) / len(difficulties))
    session["user"] = current_user.id
    session["questions"] = question_ids
    session["past_questions"] = []
    session["no_questions"] = len(question_ids)
    session["assessment"] = assessment_id
    first_question = session["questions"][0][0]
    first_question_type = session["questions"][0][0]
    first_question_id = session["questions"][0][1]

    # ---- > calculate which attempt this is for user
    if not current_user.has_taken(assessment):
        session["attempt_number"] = 1
    else:
        current_no_attempts = current_user.current_attempts(assessment)
        session["attempt_number"] = current_no_attempts + 1

    return render_template(
        "assessment_summary.html",
        assessment=assessment,
        questions_t1=questions_t1,
        questions_t2=questions_t2,
        question_ids=question_ids,
        first_question=first_question,
        q_type=first_question_type,
        first_question_id=first_question_id,
        difficulty=final_difficulty,
    )


@assessments.route(
    "/answer_question/<int:q_type>/<int:question_id>", methods=["GET", "POST"]
)
def answer_question(q_type, question_id):
    ## find question to be answered
    assessment = Assessment.query.get_or_404(session.get("assessment"))
    if q_type == 1:
        question = QuestionT1.query.get_or_404(question_id)
        form = AnswerType1Form()
        form.chosen_option.choices = [
            (option.option_id, option.option_text)
            for option in Option.query.filter_by(q_t1_id=question_id).all()
        ]
    elif q_type == 2:
        question = QuestionT2.query.get_or_404(question_id)
        form = AnswerType2Form(answer=None)

    ## check if there's a previous answer to prepopulate
    if request.method == "GET":
        if current_user.has_answered(
            q_type, question, assessment, session["attempt_number"]
        ):

            if q_type == 1:
                previous_response = (
                    current_user.t1_responses.filter_by(
                        assessment_id=session.get("assessment")
                    )
                    .filter_by(t1_question_id=question_id)
                    .filter_by(attempt_number=session["attempt_number"])
                    .first()
                )
                # find id of option chosen
                selected_option_id = previous_response.selected_option
                # then set default of form
                form.chosen_option.default = selected_option_id
                # then run form.process()
                form.process()
            elif q_type == 2:
                previous_response = (
                    current_user.t2_responses.filter_by(
                        assessment_id=session.get("assessment")
                    )
                    .filter_by(t2_question_id=question_id)
                    .filter_by(attempt_number=session["attempt_number"])
                    .first()
                )
                previous_given_answer = previous_response.response_content
                form.answer.data = previous_given_answer

    ## actions to take on a post method - i.e. when user submits an answer to their question
    if request.method == "POST":
        ## if changing / resubmitting answer, ensures no duplicate responses by deleting the old
        if session["is_summative"]:
            if q_type == 1:
                if form.chosen_option.data is None:
                    if len(session["questions"]) < 1:
                        complete = True
                        # need to check if every question has been answered.
                        t1s = QuestionT1.query.filter_by(
                            assessment_id=assessment.assessment_id
                        ).all()
                        t2s = QuestionT2.query.filter_by(
                            assessment_id=assessment.assessment_id
                        ).all()
                        for q in t1s:
                            res = (
                                current_user.t1_responses.filter_by(
                                    assessment_id=assessment.assessment_id
                                )
                                .filter_by(attempt_number=session["attempt_number"])
                                .filter_by(t1_question_id=q.q_t1_id)
                                .first()
                            )
                            if res == None:
                                complete = False
                        for q in t2s:
                            res = (
                                current_user.t2_responses.filter_by(
                                    assessment_id=assessment.assessment_id
                                )
                                .filter_by(attempt_number=session["attempt_number"])
                                .filter_by(t2_question_id=q.q_t2_id)
                                .first()
                            )
                            if res == None:
                                complete = False
                        flash(
                            "All questions must be completed to submit an assessment - please answer the current question."
                        )
                        return redirect(url_for("assessments.cannot_submit"))
                    else:
                        return redirect(
                            url_for(
                                "assessments.answer_question",
                                q_type=session["questions"][0][0],
                                question_id=session["questions"][0][1],
                            )
                        )
            elif q_type == 2:
                if form.answer.data.strip() is None or form.answer.data.strip() == "":
                    if len(session["questions"]) < 1:
                        flash(
                            "All questions must be completed to submit an assessment - please answer the current question."
                        )
                        return redirect(url_for("assessments.cannot_submit"))
                    else:
                        return redirect(
                            url_for(
                                "assessments.answer_question",
                                q_type=session["questions"][0][0],
                                question_id=session["questions"][0][1],
                            )
                        )
        if current_user.has_answered(
            q_type, question, assessment, session["attempt_number"]
        ):
            current_user.remove_answer(
                q_type, question, assessment, session["attempt_number"]
            )
            db.session.commit()
        if q_type == 1:
            given_answer = Option.query.filter_by(
                option_id=form.chosen_option.data
            ).first()
            if given_answer.is_correct:
                result = True
            else:
                result = False
            response = ResponseT1(
                attempt_number=session["attempt_number"],
                user_id=current_user.id,
                assessment_id=assessment.assessment_id,
                t1_question_id=question_id,
                selected_option=given_answer.option_id,
                is_correct=result,
            )
        elif q_type == 2:
            given_answer = form.answer.data.strip().lower()
            if given_answer == question.correct_answer.lower():
                result = True
            else:
                result = False
            response = ResponseT2(
                attempt_number=session["attempt_number"],
                user_id=current_user.id,
                assessment_id=assessment.assessment_id,
                t2_question_id=question_id,
                response_content=given_answer,
                is_correct=result,
            )
        db.session.add(response)
        db.session.commit()
        if session["is_summative"]:
            if len(session["questions"]) < 1:
                complete = True
                incomplete_qs = []
                # need to check if every question has been answered.
                for idx, q in enumerate(session["past_questions"]):
                    if q[0] == 1:
                        res = (
                            current_user.t1_responses.filter_by(
                                assessment_id=assessment.assessment_id
                            )
                            .filter_by(attempt_number=session["attempt_number"])
                            .filter_by(t1_question_id=q[1])
                            .first()
                        )
                    elif q[0] == 2:
                        res = (
                            current_user.t2_responses.filter_by(
                                assessment_id=assessment.assessment_id
                            )
                            .filter_by(attempt_number=session["attempt_number"])
                            .filter_by(t2_question_id=q[1])
                            .first()
                        )
                    if res == None:
                        complete = False
                        incomplete_qs.append(idx + 1)
                if complete:
                    return redirect(
                        url_for(
                            "assessments.results",
                            assessment_id=assessment.assessment_id,
                        )
                    )
                else:
                    message = ""
                    for i in incomplete_qs:
                        n = str(i)
                        m = n + ", "
                        message += m
                    flash(
                        f"All questions must be completed to submit an assessment - use the 'previous question' button to answer the following questions: {message}."
                    )
                    return redirect(url_for("assessments.cannot_submit"))
            else:
                return redirect(
                    url_for(
                        "assessments.answer_question",
                        q_type=session["questions"][0][0],
                        question_id=session["questions"][0][1],
                    )
                )
        else:
            return redirect(
                url_for(
                    "assessments.mark_answer", q_type=q_type, question_id=question_id
                )
            )
    current_questions = session.get("questions")
    previous = current_questions.pop(0)
    session["past_questions"].append(previous)
    session["questions"] = current_questions
    return render_template(
        "answer_question.html",
        question=question,
        assessment=assessment,
        form=form,
        q_type=q_type,
    )


@assessments.route("/previous_question")
def previous_question():
    next_question = session["past_questions"].pop(-1)
    prev_question = session["past_questions"].pop(-1)
    session["questions"].insert(0, next_question)
    session["questions"].insert(0, prev_question)
    # copy and overwrite existing session variables as otherwise insert would not remain permanent on next loaded page
    copy_list_next = session["questions"]
    copy_list_prev = session["past_questions"]
    session["questions"] = copy_list_next
    session["past_questions"] = copy_list_prev
    return redirect(
        url_for(
            "assessments.answer_question",
            q_type=session["questions"][0][0],
            question_id=session["questions"][0][1],
        )
    )


@assessments.route("/cannot_submit")
def cannot_submit():
    next_question = session["past_questions"].pop(-1)
    session["questions"].insert(0, next_question)
    # copy and overwrite existing session variables as otherwise insert would not remain permanent on next loaded page
    copy_list_next = session["questions"]
    copy_list_prev = session["past_questions"]
    session["questions"] = copy_list_next
    session["past_questions"] = copy_list_prev
    return redirect(
        url_for(
            "assessments.answer_question",
            q_type=session["questions"][0][0],
            question_id=session["questions"][0][1],
        )
    )


@assessments.route(
    "/mark_answer/<int:q_type>/<int:question_id>", methods=["GET", "POST"]
)
def mark_answer(q_type, question_id):
    assessment = Assessment.query.get_or_404(session.get("assessment"))
    if q_type == 1:
        question = QuestionT1.query.get_or_404(question_id)
        right_answer = (
            Option.query.filter_by(q_t1_id=question.q_t1_id)
            .filter_by(is_correct=True)
            .first()
        )
        chosen_option = (
            current_user.t1_responses.filter_by(assessment_id=session.get("assessment"))
            .filter_by(t1_question_id=question_id)
            .filter_by(attempt_number=session["attempt_number"])
            .first()
        )
        response = Option.query.filter_by(
            option_id=chosen_option.selected_option
        ).first()
    elif q_type == 2:
        question = QuestionT2.query.get_or_404(question_id)
        right_answer = question.correct_answer
        response = (
            current_user.t2_responses.filter_by(assessment_id=session.get("assessment"))
            .filter_by(t2_question_id=question_id)
            .filter_by(attempt_number=session["attempt_number"])
            .first()
        )
    return render_template(
        "mark_answer.html",
        question=question,
        response=response,
        assessment=assessment,
        right_answer=right_answer,
        q_type=q_type,
    )


@assessments.route("/results/<int:assessment_id>")
def results(assessment_id):
    assessment = Assessment.query.get_or_404(session.get("assessment"))
    no_of_questions = session.pop("no_questions", None)

    # ----- Find all the responses given during assessment session
    t1_responses = (
        current_user.t1_responses.filter_by(assessment_id=assessment_id)
        .filter_by(attempt_number=session["attempt_number"])
        .all()
    )
    t2_responses = (
        current_user.t2_responses.filter_by(assessment_id=assessment_id)
        .filter_by(attempt_number=session["attempt_number"])
        .all()
    )

    # ----- find all questions asked
    questions = (
        QuestionT1.query.filter_by(assessment_id=assessment_id).all()
        + QuestionT2.query.filter_by(assessment_id=assessment_id).all()
    )

    # ----- find possible total marks
    possible_total = 0
    for question in questions:
        possible_total += question.num_of_marks

    # ----- find actual result achieved
    result = 0
    for response in t1_responses:
        if response.is_correct:
            answered_question = QuestionT1.query.filter_by(
                q_t1_id=response.t1_question_id
            ).first()
            result += answered_question.num_of_marks
    for response in t2_responses:
        if response.is_correct:
            answered_question = QuestionT2.query.filter_by(
                q_t2_id=response.t2_question_id
            ).first()
            result += answered_question.num_of_marks
    # ---- 1. create list of numbers representing indexes
    no_questions = [i for i in range(0, no_of_questions)]

    # ---- 2. create lists to store relevant variables to be entered into template
    ordered_questions = []
    given_answers = []
    correct_answers = []
    is_correct = []
    passed = True if result >= (possible_total / 2) else False
    # ---- 3. iterate over the index list
    for idx in no_questions:
        current_question = session["past_questions"][idx]
        if current_question[0] == 1:
            q = QuestionT1.query.filter_by(q_t1_id=current_question[1]).first()
            related_response = (
                current_user.t1_responses.filter_by(
                    assessment_id=assessment.assessment_id
                )
                .filter_by(t1_question_id=q.q_t1_id)
                .filter_by(attempt_number=session["attempt_number"])
                .first()
            )
            answer_content = (
                Option.query.filter_by(option_id=related_response.selected_option)
                .first()
                .option_text
            )
            correct_answer = (
                Option.query.filter_by(q_t1_id=q.q_t1_id)
                .filter_by(is_correct=True)
                .first()
                .option_text
            )
            correct_test = related_response.is_correct
        elif current_question[0] == 2:
            q = QuestionT2.query.filter_by(q_t2_id=current_question[1]).first()
            related_response = (
                current_user.t2_responses.filter_by(
                    assessment_id=assessment.assessment_id
                )
                .filter_by(t2_question_id=q.q_t2_id)
                .filter_by(attempt_number=session["attempt_number"])
                .first()
            )
            answer_content = related_response.response_content
            correct_answer = q.correct_answer
            correct_test = related_response.is_correct

        ordered_questions.append(q)
        given_answers.append(answer_content)
        correct_answers.append(correct_answer)
        is_correct.append(correct_test)
    return render_template(
        "results.html",
        no_questions=no_questions,
        assessment=assessment,
        result=result,
        possible_total=possible_total,
        ordered_questions=ordered_questions,
        given_answers=given_answers,
        correct_answers=correct_answers,
        is_correct=is_correct,
        passed=passed,
    )


@assessments.route("/exit_assessment")
def exit_assessment():
    ## wipes all session variables and returns to assessment list
    session.pop("user", None)
    session.pop("questions", None)
    session.pop("no_questions", None)
    session.pop("assessment", None)
    session.pop("takes_assessment_id", None)
    module = session.pop("module_id")
    print("Module ID is: ")
    print(module)
    return redirect(url_for("assessments.view_module", module_id=module))


# ----------------------------------------------------------------------------------------------------
# ---------------------------------  END of TAKE ASSESSMENT  ---------------------------------------
# ----------------------------------------------------------------------------------------------------


@assessments.route("/empty_assessment")
def empty_assessment():
    return render_template("empty_assessment.html")


# ----------------------------------------------------------------------------------------------------
# ---------------------------------  Duplicate Results Page  ---------------------------------------
# -------------------------------- For access from module view ------------------------------------
# ----------------------------------------------------------------------------------------------------


@assessments.route("/results/<int:assessment_id>/<int:attempt_number>")
def show_results(assessment_id, attempt_number):
    # --- > get all responses for given assessment and given attempt id
    assessment = Assessment.query.filter_by(assessment_id=assessment_id).first()
    t1_responses = (
        current_user.t1_responses.filter_by(assessment_id=assessment.assessment_id)
        .filter_by(attempt_number=attempt_number)
        .all()
    )
    t2_responses = (
        current_user.t2_responses.filter_by(assessment_id=assessment.assessment_id)
        .filter_by(attempt_number=attempt_number)
        .all()
    )
    # ----- find all questions asked
    questions = (
        QuestionT1.query.filter_by(assessment_id=assessment_id).all()
        + QuestionT2.query.filter_by(assessment_id=assessment_id).all()
    )

    # ----- find possible total marks
    possible_total = 0
    for question in questions:
        possible_total += question.num_of_marks

    # ----- find actual result achieved
    result = 0
    for response in t1_responses:
        if response.is_correct:
            answered_question = QuestionT1.query.filter_by(
                q_t1_id=response.t1_question_id
            ).first()
            result += answered_question.num_of_marks
    for response in t2_responses:
        if response.is_correct:
            answered_question = QuestionT2.query.filter_by(
                q_t2_id=response.t2_question_id
            ).first()
            result += answered_question.num_of_marks
    passed = True if result >= (possible_total / 2) else False

    # --- > Find all questions answered
    t1_questions = QuestionT1.query.filter_by(assessment_id=assessment_id).all()
    t2_questions = QuestionT2.query.filter_by(assessment_id=assessment_id).all()

    # --- > User answers
    t1_answers = dict()
    t2_answers = dict()
    for q in t1_questions:
        user_answer = (
            current_user.t1_responses.filter_by(assessment_id=assessment.assessment_id)
            .filter_by(t1_question_id=q.q_t1_id)
            .filter_by(attempt_number=attempt_number)
            .first()
        )
        correct_option = (
            Option.query.filter_by(q_t1_id=q.q_t1_id).filter_by(is_correct=True).first()
        )
        selected_option_text = Option.query.filter_by(
            option_id=user_answer.selected_option
        ).first()
        t1_answers[q.q_t1_id] = [
            selected_option_text,
            correct_option.option_text,
            user_answer.is_correct,
        ]
    for q in t2_questions:
        user_answer = (
            current_user.t2_responses.filter_by(assessment_id=assessment.assessment_id)
            .filter_by(t2_question_id=q.q_t2_id)
            .filter_by(attempt_number=attempt_number)
            .first()
        )
        t2_answers[q.q_t2_id] = [
            user_answer.response_content,
            q.correct_answer,
            user_answer.is_correct,
        ]
    return render_template(
        "show_results.html",
        t1_questions=t1_questions,
        t1_answers=t1_answers,
        t2_questions=t2_questions,
        t2_answers=t2_answers,
        possible_total=possible_total,
        result=result,
        passed=passed,
        assessment=assessment,
    )


# ----------------------------------------------------------------------------------------------------
# -------------------------------- Random Q based on Topic ------------------------------------
# ----------------------------------------------------------------------------------------------------


@assessments.route("/random_question/<int:topic_id>", methods=["GET", "POST"])
def random_question(topic_id):
    topic = Tag.query.filter_by(id=topic_id).first()
    if session["rand_q_details"][0] == 1:
        past_form = AnswerType1Form()
        q_type = session["rand_q_details"][0]
    elif session["rand_q_details"][0] == 2:
        past_form = AnswerType2Form()
        q_type = session["rand_q_details"][0]

    if q_type == 1:
        final_q = QuestionT1.query.filter_by(
            q_t1_id=session["rand_q_details"][1]
        ).first()
        form = AnswerType1Form()
        form.chosen_option.choices = [
            (option.option_id, option.option_text)
            for option in Option.query.filter_by(q_t1_id=final_q.q_t1_id).all()
        ]
    elif q_type == 2:
        final_q = QuestionT2.query.filter_by(
            q_t2_id=session["rand_q_details"][1]
        ).first()
        form = AnswerType2Form()
    if request.method == "POST":
        if session["rand_q_details"][0] == 1:
            worked_on_question = QuestionT1.query.filter_by(
                q_t1_id=session["rand_q_details"][1]
            ).first()
            given_answer = Option.query.filter_by(
                option_id=past_form.chosen_option.data
            ).first()
            if given_answer.is_correct:
                result = True
            else:
                result = False
            session["practice_q_answer"] = [given_answer.option_text, result]
            return redirect(
                url_for(
                    "assessments.mark_random_question",
                    q_type=session["rand_q_details"][0],
                    q_id=session["rand_q_details"][1],
                    topic_id=topic_id,
                )
            )
        elif session["rand_q_details"][0] == 2:
            given_answer = past_form.answer.data.strip().lower()
            worked_on_question = QuestionT2.query.filter_by(
                q_t2_id=session["rand_q_details"][1]
            ).first()
            if given_answer == worked_on_question.correct_answer.lower():
                result = True
            else:
                result = False
            session["practice_q_answer"] = [given_answer, result]
            return redirect(
                url_for(
                    "assessments.mark_random_question",
                    q_type=session["rand_q_details"][0],
                    q_id=session["rand_q_details"][1],
                    topic_id=topic_id,
                )
            )
    return render_template(
        "random_question.html", topic=topic, q_type=q_type, question=final_q, form=form
    )


@assessments.route("/random_question/mark/<int:q_type>/<int:q_id>/<int:topic_id>")
def mark_random_question(q_type, q_id, topic_id):
    topic = Tag.query.filter_by(id=topic_id).first()
    if q_type == 1:
        question = QuestionT1.query.filter_by(q_t1_id=q_id).first()
    elif q_type == 2:
        question = QuestionT2.query.filter_by(q_t2_id=q_id).first()
    return render_template(
        "mark_random_question.html", question=question, topic=topic, q_type=q_type
    )


@assessments.route("/random_question/generate/<int:topic_id>")
def generate_random(topic_id):
    topic = Tag.query.filter_by(id=topic_id).first()
    t1qs = QuestionT1.query.filter_by(tag_id=topic_id).all()
    t2qs = QuestionT2.query.filter_by(tag_id=topic_id).all()
    total_question_options = len(t1qs) + len(t2qs)
    if len(t1qs) == 0 and len(t2qs) > 0:
        q_type = 2
    elif len(t2qs) == 0 and len(t1qs) > 0:
        q_type = 1
    elif len(t1qs) == 0 and len(t2qs) == 0:
        flash("No questions of this topic available to answer.")
        return redirect(url_for("assessments.index"))
    else:
        q_type = random.randrange(2) + 1

    if q_type == 1:
        if len(t1qs) == 1:
            final_q = t1qs[0]
        else:
            r = random.randrange(len(t1qs))
            final_q = t1qs[r]
        q_ref = [1, final_q.q_t1_id]
    elif q_type == 2:
        if len(t2qs) == 1:
            final_q = t2qs[0]
        else:
            r = random.randrange(len(t2qs))
            final_q = t2qs[r]
        q_ref = [2, final_q.q_t2_id]
    if q_type == 1:
        session["rand_q_details"] = [q_type, final_q.q_t1_id]
    elif q_type == 2:
        session["rand_q_details"] = [q_type, final_q.q_t2_id]
    return redirect(url_for("assessments.random_question", topic_id=topic_id))
