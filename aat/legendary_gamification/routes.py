from click import option
from flask import (
    copy_current_request_context,
    render_template,
    request,
    redirect,
    url_for,
)
from flask_login import current_user
import flask_login
import random
from aat import db
from aat.legendary_gamification.forms import ChallengeForm
from . import legendary_gamification
from werkzeug.exceptions import BadRequestKeyError
from ..models import *
from ..db_utils import get_all_assessment_marks

question_counter = 0
score_counter = 0
challenge_questions = []
challenge_options = []
rapid_responses = []
correct_responses = []
rapid_fire_reason = ""


@legendary_gamification.route("/achievements/<int:user_id>", methods=["GET", "POST"])
def achievements(user_id):
    global challenge_questions
    global challenge_options
    global rapid_fire_reason
    get_all_assessment_marks(debug=True)
    leaderboard_user = User.query.filter_by(id=user_id).first()
    badges = []
    achievements = []
    lines_ranks = []
    all_users = User.query.all()
    all_friends = Friends.query.filter_by(user_id=current_user.id).all()
    all_challenge_friends = []
    for friend in all_friends:
        all_challenge_friends.append(
            (
                User.query.filter_by(id=friend.friend_id).first().id,
                User.query.filter_by(id=friend.friend_id).first().name,
            )
        )
    all_challenge_friends_names = [item[1] for item in all_challenge_friends]
    all_takenChallenges = ChallengesTaken.query.all()
    takenChallengesIDs = (
        ChallengesTaken.query.with_entities(ChallengesTaken.challenge_id)
        .filter_by(user_id=user_id)
        .all()
    )
    takenChallengesList = [item[0] for item in takenChallengesIDs]

    user_stats = []
    for user in all_users:
        if user.role_id == 1:
            user_stats.append(
                (
                    get_all_assessment_marks(
                        input_user_id=user.id, highest_scoring_attempt_only=True
                    ),
                    user.name,
                    user.id,
                )
            )
    print("#####################################")
    for stat in user_stats:
        print(stat)

    for user in user_stats:
        user_score = 0
        for stat in user[0]:
            if not stat["is_summative"]:
                user_score += stat["correct_marks"]
        lines_ranks.append((user_score, user[1], user[2]))

    award_badges = Awarded_Badge.query.filter_by(user_id=user_id).all()
    # for awards in award_badges:
    #     print(awards.badge_id)
    award_achievements = Awarded_Achievement.query.filter_by(user_id=user_id).all()
    for awards in award_badges:
        badge = Badge.query.filter_by(badge_id=awards.badge_id).first()
        badges.append(badge)
    for awards in award_achievements:
        achievement = Achievement.query.filter_by(
            achievement_id=awards.achievement_id
        ).first()
        achievements.append(achievement)

    in_challenges = (
        Challenge.query.with_entities(
            Challenge.from_user,
            Challenge.to_user,
            Challenge.challenge_id,
            Challenge.difficulty,
        )
        .filter_by(to_user=user_id, status="Pending")
        .all()
    )
    out_challenges = (
        Challenge.query.with_entities(
            Challenge.from_user, Challenge.to_user, Challenge.difficulty
        )
        .filter_by(from_user=user_id, status="Pending")
        .all()
    )
    active_challenges = Challenge.query.filter_by(status="Active").all()
    in_users = []
    out_users = []
    active_users = []
    challenge_ids = []
    incoming_challenge_difficulty = []
    outgoing_challenge_difficulty = []

    for challenge in in_challenges:
        user_from = User.query.filter_by(id=challenge[0]).first()
        in_users.append((user_from.id, user_from.name))
        challenge_ids.append(challenge[2])
        incoming_challenge_difficulty.append(challenge[3])
    for challenge in out_challenges:
        user_to = User.query.filter_by(id=challenge[1]).first()
        out_users.append((user_to.id, user_to.name))
        outgoing_challenge_difficulty.append(challenge[2])
    for challenge in active_challenges:
        all_taken = ChallengesTaken.query.filter_by(
            challenge_id=challenge.challenge_id
        ).all()
        all_taken_users = [item.user_id for item in all_taken]
        if not (
            challenge.from_user in all_taken_users
            and challenge.to_user in all_taken_users
        ):
            if challenge.from_user == user_id:
                user = User.query.filter_by(id=challenge.to_user).first()
                difficulty = challenge.difficulty
                active_users.append((challenge.challenge_id, user.name, difficulty))
            elif challenge.to_user == user_id:
                user = User.query.filter_by(id=challenge.from_user).first()
                difficulty = challenge.difficulty
                active_users.append((challenge.challenge_id, user.name, difficulty))
        else:
            challenge.status = "Completed"
            db.session.add(challenge)
            db.session.commit()
    # print(active_users)

    # print(in_users)
    # print(out_users)
    # print(active_users)
    challenge = ChallengeForm()
    ids_finished_challenge = []
    # with open("aat/legendary_gamification/ranks.txt", 'r') as f:
    #     lines_ranks = f.readlines()
    # with open("aat/legendary_gamification/awards.txt", 'r') as f:
    #     lines_achievements = f.readlines()
    if request.method == "POST":
        try:
            choice = request.form["button"]
        except:
            pass

        try:
            choice = request.form["accept_challenge_button"]
        except:
            pass

        try:
            choice = request.form["take_challenge_button"]
        except:
            pass
        if choice == "Practice Rapid Fire Tests" or choice == "Take Rank Up Test":
            if choice == "Practice Rapid Fire Tests":
                rapid_fire_reason = "practice"
            else:
                rapid_fire_reason = "rankup"
            questions_t1 = QuestionT1.query.all()
            max_questions = len(questions_t1)
            question_ids = []
            while len(question_ids) < 3:
                q_id = random.randrange(1, max_questions + 1)
                if q_id not in question_ids:
                    question_ids.append(q_id)
            for i in question_ids:
                question = (
                    QuestionT1.query.with_entities(
                        QuestionT1.q_t1_id, QuestionT1.question_text
                    )
                    .filter_by(q_t1_id=i)
                    .first()
                )
                challenge_questions.append(question)
            for i in question_ids:
                option = (
                    Option.query.with_entities(
                        Option.option_id, Option.option_text, Option.is_correct
                    )
                    .filter_by(q_t1_id=i)
                    .all()
                )
                challenge_options.append(option)

            return redirect(url_for(".rapid_fire"))

        elif choice == "Challenge User":
            challenge_details = Challenge(
                from_user=user_id,
                to_user=int(request.form.get("Users")),
                difficulty=int(challenge.difficulty.data),
                number_of_questions=int(request.form.get("Question_Numbers")),
            )
            db.session.add(challenge_details)
            db.session.commit()
            return redirect(url_for(".get_id"))

        elif choice == "Accept Challenge":
            try:
                chosen_challenge = request.form["accept_options"]
                challenge_active = Challenge.query.filter_by(
                    challenge_id=chosen_challenge
                ).first()
                challenge_active.status = "Active"
                db.session.add(challenge_active)
                db.session.commit()
                questions_t1 = QuestionT1.query.all()
                max_questions = len(questions_t1)
                question_ids = []
                while len(question_ids) < challenge_active.number_of_questions:
                    q_id = random.randrange(1, max_questions + 1)
                    if q_id not in question_ids:
                        question_ids.append(q_id)
                for i in question_ids:
                    question = ChallengeQuestions(
                        challenge_id=chosen_challenge, question_id=i
                    )
                    db.session.add(question)
                    db.session.commit()

                return redirect(url_for(".get_id"))
            except BadRequestKeyError:
                pass
        elif choice == "Take Challenge":
            try:
                chosen_challenge = request.form["active_options"]
                challenge_question_all = ChallengeQuestions.query.filter_by(
                    challenge_id=chosen_challenge
                ).all()

                takenChallenge = ChallengesTaken(
                    user_id=user_id, challenge_id=chosen_challenge
                )
                db.session.add(takenChallenge)
                db.session.commit()

                for question in challenge_question_all:
                    question = (
                        QuestionT1.query.with_entities(
                            QuestionT1.q_t1_id, QuestionT1.question_text
                        )
                        .filter_by(q_t1_id=question.question_id)
                        .first()
                    )
                    challenge_questions.append(question)
                # print(challenge_questions)
                for question in challenge_question_all:
                    option = (
                        Option.query.with_entities(
                            Option.option_id, Option.option_text, Option.is_correct
                        )
                        .filter_by(q_t1_id=question.question_id)
                        .all()
                    )
                    challenge_options.append(option)
                # print(challenge_options)
                rapid_fire_reason = "practice"
                return redirect(
                    url_for(
                        ".rapid_fire",
                        challenge_questions=challenge_questions,
                        challenge_options=challenge_options,
                    )
                )
            except BadRequestKeyError:
                pass
        elif choice == "Add Friend":
            friend1 = Friends(user_id=current_user.id, friend_id=user_id)
            friend2 = Friends(user_id=user_id, friend_id=current_user.id)
            db.session.add_all([friend1, friend2])
            db.session.commit()
            return redirect(url_for(".get_id"))
        elif choice == "Remove Friend":
            friend1 = Friends.query.filter_by(
                user_id=current_user.id, friend_id=user_id
            ).first()
            friend2 = Friends.query.filter_by(
                user_id=user_id, friend_id=current_user.id
            ).first()
            db.session.delete(friend1)
            db.session.delete(friend2)
            db.session.commit()
            return redirect(url_for(".get_id"))
    return render_template(
        "achievements.html",
        ranks=sorted(lines_ranks, key=lambda x: x[0], reverse=True),
        badges=badges,
        achievements=achievements,
        incoming_challenges=in_users,
        outgoing_challenges=out_users,
        challenge=challenge,
        all_users=all_users,
        challenge_ids=challenge_ids,
        in_difficulty=incoming_challenge_difficulty,
        out_difficulty=outgoing_challenge_difficulty,
        active_users=active_users,
        taken_challenges=takenChallengesList,
        leaderboard_user=leaderboard_user,
        all_friends=all_challenge_friends,
        all_friends_names=all_challenge_friends_names,
    )


@legendary_gamification.route("/redirect-page-achievement")
def refresh():
    return redirect("achievements")


@legendary_gamification.route("/get-id-page-achievement")
def get_id():
    global question_counter
    global challenge_questions
    global challenge_options
    global score_counter
    global rapid_responses
    global correct_responses
    current_user_id = current_user.id
    question_counter = 0
    challenge_questions = []
    challenge_options = []
    score_counter = 0
    rapid_responses = []
    correct_responses = []
    print(current_user_id)
    return redirect(url_for(".achievements", user_id=current_user_id))


@legendary_gamification.route("/correctement")
def correct_answer():
    global question_counter
    global rapid_responses
    global correct_responses
    correct_responses.append(
        [item for item in challenge_options[question_counter] if item[2]]
    )
    rapid_responses.append((False, ""))
    question_counter += 1
    return redirect("rapid-fire")


@legendary_gamification.route("/rapid-fire-victory-royale", methods=["GET", "POST"])
def assessment_success():
    if request.method == "POST":
        try:
            choice = request.form["button"]
        except BadRequestKeyError:
            return redirect("rapid-fire-victory-royale")
        if choice == "return":
            return redirect(url_for(".get_id"))
    if rapid_fire_reason == "rankup":
        if current_user.tier != "Diamond":
            if score_counter == len(rapid_responses):
                current_user_tier = Tier.query.filter_by(name=current_user.tier).first()
                new_tier_id = current_user_tier.tier_id + 1
                new_user_tier = Tier.query.filter_by(tier_id=new_tier_id).first()
                currentUser = User.query.filter_by(id=current_user.id).first()
                currentUser.tier = new_user_tier.name
                db.session.commit()
    return render_template(
        "assess_success.html",
        rapid_responses=rapid_responses,
        challenge_options=challenge_options,
        challenge_questions=challenge_questions,
        correct_responses=correct_responses,
        reason=rapid_fire_reason,
        score_count=score_counter,
    )


@legendary_gamification.route("/tortement")
def wrong_answer():
    return render_template("wrong_answer.html")


@legendary_gamification.route("/level-up")
def level_up():
    return render_template("levelup.html")


@legendary_gamification.route("/rapid-fire", methods=["GET", "POST"])
def rapid_fire():
    global question_counter
    global score_counter
    global rapid_responses
    global correct_responses
    try:
        if request.method == "POST":
            try:
                choice = request.form["options"].split(",")
                if choice[0] == "True":
                    score_counter += 1
                    rapid_responses.append((True, choice[1]))
                else:
                    rapid_responses.append((False, choice[1]))
                correct_responses.append(
                    [item for item in challenge_options[question_counter] if item[2]]
                )
                print(correct_responses)
                question_counter += 1
            except BadRequestKeyError:
                pass
        return render_template(
            "fire.html",
            question=challenge_questions[question_counter],
            options=challenge_options[question_counter],
            question_counter=question_counter,
        )
    except IndexError:
        return redirect("rapid-fire-victory-royale")


@legendary_gamification.route("/profile-page")
def profile():
    badges = []
    achievements = []
    award_badges = Awarded_Badge.query.filter_by(user_id=current_user.id).all()
    print(current_user.id)
    # for awards in award_badges:
    #     print(awards.badge_id)
    print(award_badges)
    award_achievements = Awarded_Achievement.query.filter_by(
        user_id=current_user.id
    ).all()
    print(award_achievements)
    for awards in award_badges:
        badge = Badge.query.filter_by(badge_id=awards.badge_id).first()
        badges.append(badge)
        print("Added")
    for awards in award_achievements:
        achievement = Achievement.query.filter_by(
            achievement_id=awards.achievement_id
        ).first()
        achievements.append(achievement)
    for badge in badges:
        print(badge.name)
    return render_template("profile.html", badges=badges, achievements=achievements)


@legendary_gamification.route("/leaderboard-test")
def test_leaderboard():
    all_users = User.query.all()
    lines_ranks = []
    for user in all_users:
        if user.role_id == 1:
            assessment_marks = {}
            for response in user.t1_responses:
                if response.assessment not in assessment_marks:
                    assessment_marks[response.assessment] = {
                        "marks_awarded": response.question.num_of_marks
                        if response.is_correct
                        else 0,
                        "marks_possible": response.question.num_of_marks,
                    }
                else:
                    assessment_marks[response.assessment]["marks_awarded"] += (
                        response.question.num_of_marks if response.is_correct else 0
                    )
                    assessment_marks[response.assessment][
                        "marks_possible"
                    ] += response.question.num_of_marks

            ## T2_responses
            for response in user.t2_responses:
                if response.assessment not in assessment_marks:
                    assessment_marks[response.assessment] = {
                        "marks_awarded": response.question.num_of_marks
                        if response.is_correct
                        else 0,
                        "marks_possible": response.question.num_of_marks,
                    }
                else:
                    assessment_marks[response.assessment]["marks_awarded"] += (
                        response.question.num_of_marks if response.is_correct else 0
                    )
                    assessment_marks[response.assessment][
                        "marks_possible"
                    ] += response.question.num_of_marks

            module_dict = {}

            for module in Module.query.all():
                for assessment, data in assessment_marks.items():
                    if assessment.module_id == module.module_id:
                        if module not in module_dict:
                            module_dict[module] = {assessment: data}
                        else:
                            module_dict[module][assessment] = data

            sum_of_marks_awarded = 0
            sum_of_marks_possible = 0

            for module in module_dict:
                for assessment, data in assessment_marks.items():
                    sum_of_marks_awarded += data["marks_awarded"]
                    sum_of_marks_possible += data["marks_possible"]
                    # module_dict[module]["marks_awarded"] += data["marks_awarded"]
                    # module_dict[module]["marks_possible"] += data["marks_possible"]

            # if sum_of_marks_possible == 0:
            #     return render_template("no_questions_answered.html")

            overall_results = {
                "sum_of_marks_awarded": sum_of_marks_awarded,
                "sum_of_marks_possible": sum_of_marks_possible,
            }

            # print(user.name, overall_results)

            lines_ranks.append(
                (overall_results["sum_of_marks_awarded"], user.name, user.id)
            )
            # print(lines_ranks)

            module_totals = {}

            for module, module_details in module_dict.items():
                module_totals[module.title] = {"marks_awarded": 0, "marks_possible": 0}
                for assessment, assessment_details in module_details.items():
                    module_totals[module.title]["marks_awarded"] += assessment_details[
                        "marks_awarded"
                    ]
                    module_totals[module.title]["marks_possible"] += assessment_details[
                        "marks_possible"
                    ]
    return render_template("leaderboard.html", ranks=lines_ranks)
