from pydoc import describe
from unicodedata import name
from aat import db
from aat import Role
from aat import app

from aat.models import *


with app.app_context():
    db.drop_all()
    db.create_all()
    Role.insert_roles()

    ###########
    # MODULES #
    ###########
    db.session.add_all(
        [
            Module(  # 1
                title="Databases and Modelling",
                total_credits=120,
            ),
            Module(  # 2
                title="Advanced BennieScript",
                total_credits=30,
            ),
            Module(  # 3
                title="Jinjavitus",
                total_credits=80,
            ),
        ]
    )

    ###############
    # ASSESSMENTS #
    ###############
    db.session.add_all(
        [
            Assessment(  # 1
                module_id=1,
                lecturer_id=1,
                title="Git Basics",
                due_date=None,
                time_limit=60 * 60 * 30,
                num_of_credits=12,
                is_summative=True,
            ),
            Assessment(  # 2
                module_id=1,
                lecturer_id=2,
                title="Advanced Git",
                due_date=None,
                time_limit=60 * 60 * 45,
                num_of_credits=10,
                is_summative=True,
            ),
            Assessment(  # 3
                module_id=1,
                lecturer_id=3,
                title="DOM Manipulation in JS",
                due_date=None,
                time_limit=60 * 60 * 20,
                num_of_credits=0,
                is_summative=False,
            ),
            Assessment(  # 4
                module_id=2,
                lecturer_id=1,
                title="Woof",
                due_date=None,
                num_of_credits=10,
                is_summative=True,
            ),
            Assessment(  # 5
                module_id=2,
                lecturer_id=1,
                title="Formative Assessment",
                due_date=None,
                time_limit=60 * 60 * 30,
                num_of_credits=12,
                is_summative=False,
            ),
            Assessment(  # 6
                lecturer_id=2,
                title="No Module Summative",
                due_date=None,
                time_limit=60 * 60 * 45,
                num_of_credits=10,
                is_summative=True,
            ),
            Assessment(  # 7
                lecturer_id=3,
                title="No module Formative",
                due_date=None,
                time_limit=60 * 60 * 20,
                num_of_credits=40,
                is_summative=False,
            ),
            Assessment(  # 8
                lecturer_id=1,
                title=" A title",
                due_date=None,
                num_of_credits=10,
                is_summative=True,
            ),
            Assessment(  # 9
                module_id=3,
                lecturer_id=1,
                title="Tuesday Trauma",
                due_date=None,
                num_of_credits=20,
                is_summative=True,
            ),
        ]
    )
    #######
    # TAG #
    #######
    db.session.add_all(
        [
            Tag(name="abstract"),
            Tag(name="boolean"),
            Tag(name="computational"),
            Tag(name="decimal"),
            Tag(name="environments"),
        ]
    )

    #####################
    # QUESTIONS: TYPE 1 #
    #####################
    db.session.add_all(
        [
            # Questions on assignments
            QuestionT1(  # 1
                assessment_id=1,
                tag_id=1,
                num_of_marks=2,
                question_text="Which command do use use to view a particular commit?",
                difficulty=1,
                feedback_if_correct="Well done!",
                feedback_if_wrong="Better luck next time :)",
            ),
            QuestionT1(  # 2
                assessment_id=2,
                num_of_marks=5,
                question_text="What does git rebase do?",
                difficulty=3,
                feedback_if_correct="Well done!",
                feedback_if_wrong="Better luck next time :)",
            ),
            QuestionT1(  # 3
                assessment_id=2,
                num_of_marks=5,
                question_text="What does git stash do?",
                difficulty=2,
                feedback_if_correct="Well done!",
                feedback_if_wrong="Better luck next time :)",
            ),
            # Floating Questions
            QuestionT1(  # 4
                num_of_marks=5,
                question_text="What is the initial capacity of an array list?",
                difficulty=1,
                feedback_if_correct="Well done!",
                feedback_if_wrong="Better luck next time :)",
            ),
            QuestionT1(  # 5
                num_of_marks=5,
                question_text="What does SQL stand for?",
                difficulty=1,
                feedback_if_correct="Well done!",
                feedback_if_wrong="Better luck next time :)",
            ),
        ]
    )

    #################################
    # OPTIONS (FOR TYPE 1 QUESTIONS #
    #################################
    db.session.add_all(
        [
            Option(q_t1_id=1, option_text="checkout", is_correct=True),  # 1
            Option(q_t1_id=1, option_text="reset"),  # 2
            Option(q_t1_id=1, option_text="commit"),  # 3
            Option(q_t1_id=2, option_text="wrong answer"),  # 4
            Option(q_t1_id=2, option_text="right answer", is_correct=True),  # 5
            Option(q_t1_id=2, option_text="also the wrong answer"),  # 6
            Option(q_t1_id=3, option_text="wrong answer"),  # 7
            Option(q_t1_id=3, option_text="right answer", is_correct=True),  # 8
            Option(q_t1_id=3, option_text="another wrong answer"),  # 9
            Option(q_t1_id=4, option_text="12"),  # 10
            Option(q_t1_id=4, option_text="10", is_correct=True),  # 11
            Option(q_t1_id=4, option_text="100"),  # 12
            Option(q_t1_id=5, option_text="Super Quick Lunch"),  # 13
            Option(
                q_t1_id=5, option_text="Standard Query Language", is_correct=True
            ),  # 14
            Option(
                q_t1_id=5, option_text="Why did I choose the databases module?????"
            ),  # 15
        ]
    )

    #####################
    # QUESTIONS: TYPE 2 #
    #####################
    db.session.add_all(
        [
            # Questions (with Assessments)
            QuestionT2(  # 1
                assessment_id=1,
                tag_id=1,
                num_of_marks=5,
                question_text="What flag do you use to add a commit message?",
                correct_answer="-m",
                difficulty=1,
                feedback_if_correct="Well done!",
                feedback_if_wrong="Better luck next time :)",
            ),
            QuestionT2(  # 2
                assessment_id=1,
                num_of_marks=10,
                question_text="which command is used to upload your commits to a remote repository?",
                correct_answer="push",
                difficulty=1,
                feedback_if_correct="Well done!",
                feedback_if_wrong="Better luck next time :)",
            ),
            QuestionT2(  # 3
                assessment_id=3,
                num_of_marks=10,
                question_text="Which symbol is used to select by class using document.querySelector()?",
                correct_answer=".",
                difficulty=2,
                feedback_if_correct="Well done!",
                feedback_if_wrong="Better luck next time :)",
            ),
            QuestionT2(  # 4
                assessment_id=4,
                num_of_marks=5,
                question_text="Bark?",
                correct_answer="Bark!",
                difficulty=3,
                feedback_if_correct="WOOF!",
                feedback_if_wrong="GRRRRRRRRRR",
            ),
            # Floating Questions
            QuestionT2(  # 5
                num_of_marks=10,
                question_text="Why didn't the eagles take the ring to Mordor?",
                correct_answer="Dunno",
                difficulty=3,
                feedback_if_correct="Thats's right!",
                feedback_if_wrong="WRONG",
            ),
            QuestionT2(  # 6
                num_of_marks=4,
                question_text="What year was the Norman invasion?",
                correct_answer="1066",
                difficulty=1,
                feedback_if_correct="Indeed it was!",
                feedback_if_wrong="WRONG!!!",
            ),
            QuestionT2(  # 7
                num_of_marks=5,
                question_text="What does JSON stand for?",
                correct_answer="JavaScript Object Notation",
                difficulty=2,
                feedback_if_correct="Yup!",
                feedback_if_wrong="nope that's wrong",
            ),
            # More Questions (with Assessments)
            QuestionT2(  # 8
                assessment_id=9,
                num_of_marks=5,
                question_text="1 When is a door not a door",
                correct_answer="When it's a jar",
                difficulty=3,
                feedback_if_correct="Truth incarnate",
                feedback_if_wrong="YOU SUCK",
            ),
            QuestionT2(  # 9
                assessment_id=9,
                num_of_marks=5,
                question_text="2 When is a door not a door",
                correct_answer="When it's a jar",
                difficulty=3,
                feedback_if_correct="Truth incarnate",
                feedback_if_wrong="YOU SUCK",
            ),
            QuestionT2(  # 10
                assessment_id=9,
                num_of_marks=5,
                question_text="3 When is a door not a door",
                correct_answer="When it's a jar",
                difficulty=3,
                feedback_if_correct="Truth incarnate",
                feedback_if_wrong="YOU SUCK",
            ),
            QuestionT2(  # 11
                assessment_id=9,
                num_of_marks=5,
                question_text="4 When is a door not a door",
                correct_answer="When it's a jar",
                difficulty=3,
                feedback_if_correct="Truth incarnate",
                feedback_if_wrong="YOU SUCK",
            ),
            QuestionT2(  # 12
                assessment_id=9,
                num_of_marks=5,
                question_text="5 When is a door not a door",
                correct_answer="When it's a jar",
                difficulty=3,
                feedback_if_correct="Truth incarnate",
                feedback_if_wrong="YOU SUCK",
            ),
        ]
    )

    #########
    # USERS #
    #########
    db.session.add_all(
        [
            User(  # 1
                name="Jim",
                password="j",
                is_admin=True,
                role_id=1,
                tier="Silver"
            ),
            User(  # 2
                name="Kate",
                password="k",
                is_admin=True,
                role_id=1,
                tier="Gold"
            ),
            User(  # 3
                name="Al",
                password="a",
                is_admin=True,
                role_id=1,
            ),
            # made one letter accounts for ease of logging in as different roles (student=s, lecturer=l, admin=a)
            # NOTE: is_admin must be set to false, otherwise role will be overriden and User will be given lecturer role
            User(  # 4
                name="s",
                password="s",
                is_admin=False,
                role_id=1,
            ),
            User(  # 5
                name="l",
                password="l",
                is_admin=True,
                role_id=2,
            ),
            User(  # 6
                name="a",
                password="a",
                is_admin=False,
                role_id=3,
            ),
        ]
    )

    #####################
    # RESPONSES: TYPE 1 #
    #####################

    db.session.add_all(
        [
            ResponseT1(  # 1
                user_id=1,
                assessment_id=1,
                t1_question_id=1,
                selected_option=1,
                is_correct=True,
            ),
            ResponseT1(  # 2
                user_id=1,
                assessment_id=2,
                t1_question_id=2,
                selected_option=5,
                is_correct=True,
            ),
            ResponseT1(  # 1
                user_id=4,
                assessment_id=1,
                t1_question_id=1,
                selected_option=1,
                is_correct=True,
            ),
            ResponseT1(  # 2
                user_id=4,
                assessment_id=2,
                t1_question_id=2,
                selected_option=5,
                is_correct=True,
            ),
        ]
    )

    #####################
    # RESPONSES: TYPE 2 #
    #####################
    db.session.add_all(
        [
            ResponseT2(  # 1
                user_id=1,
                assessment_id=1,
                t2_question_id=1,
                response_content="-m",
                is_correct=True,
            ),
            ResponseT2(  # 2
                user_id=1,
                assessment_id=1,
                t2_question_id=2,
                response_content="push",
                is_correct=True,
            ),
            ResponseT2(  # 3
                user_id=2,
                assessment_id=1,
                t2_question_id=1,
                response_content="-m",
                is_correct=True,
            ),
            # RESPONSES for Student "s"
            ResponseT2(  # 4
                user_id=4,
                assessment_id=1,
                t2_question_id=1,
                response_content="-m",
                is_correct=True,
            ),
            ResponseT2(  # 5
                user_id=4,
                assessment_id=1,
                t2_question_id=2,
                response_content="adad",
                is_correct=False,
            ),
            # PLEASE NOTE CAREFUL NOT TO CREATE RESPONSES
            # FOR QUESTIONS THAT ARE NOT LINKED TO THE GIVEN
            # ASSESSMENT 
            # THE POINTS WILL ADD TO THEIR RESULT 
            # BUT THE QUESTION STILL WON'T SHOW IN THE 
            # ASSESSMENT ITSELF 
            # ResponseT2(  # 6
            #     user_id=4,
            #     assessment_id=1,
            #     t2_question_id=3,
            #     response_content=".",
            #     is_correct=True,
            # ),
            ResponseT2(  # 6
                user_id=4,
                assessment_id=6,
                t2_question_id=3,
                response_content=".",
                is_correct=True,
            ),
            ResponseT2(  # 7
                user_id=4,
                assessment_id=4,
                t2_question_id=4,
                response_content="Bark!",
                is_correct=True,
            ),
            ResponseT2(  # 8
                user_id=4,
                assessment_id=9,
                t2_question_id=8,
                response_content="When it's a jar",
                is_correct=True,
            ),
            ResponseT2(  # 9
                user_id=4,
                assessment_id=9,
                t2_question_id=9,
                response_content="When it's a jar",
                is_correct=False,
            ),
            ResponseT2(  # 10
                user_id=4,
                assessment_id=9,
                t2_question_id=10,
                response_content="When it's a jar",
                is_correct=True,
            ),
            ResponseT2(  # 11
                user_id=4,
                assessment_id=9,
                t2_question_id=11,
                response_content="Huh?",
                is_correct=False,
            ),
            ResponseT2(  # 11
                user_id=4,
                assessment_id=9,
                t2_question_id=12,
                response_content="Didn't I answer this already?",
                is_correct=False,
            ),
        ]
    )

    ##########
    # BADGES #
    ##########
    db.session.add_all(
        [
            Badge(
                badge_id=1,
                name="A Worthy Challenge",
                description="Dethrone the Top of the Leaderboard with the 'Ace' badge",
            ),
            Badge(
                badge_id=2,
                name="Troublemaker",
                description="Dethrone the Top of Leaderboard with the 'Untouchable' badge",
            ),
            Badge(
                badge_id=3,
                name="Ace",
                description="Stay at the top of the leaderboard for a month",
            ),
            Badge(
                badge_id=4,
                name="Untouchable",
                description="Stay at the top of the leaderboard for a week",
            ),
            Badge(
                badge_id=5,
                name="Loyalty",
                description="Keep returning to practice for 7 weeks",
            ),
            Badge(
                badge_id=6,
                name="Clandestine",
                description="Attempt an exercise after midnight",
            ),
            Badge(
                badge_id=7,
                name="Brobdingnagian",
                description="Achieve very high stat numbers",
            ),
        ]
    )

    ################
    # ACHIEVEMENTS #
    ################
    db.session.add_all(
        [
            Achievement(
                achievement_id=1, name="A Star is Born", description="Create an account"
            ),
            Achievement(
                achievement_id=2,
                name="Salutations!",
                description="Solve the classic 'Hello, World!' question",
            ),
            Achievement(
                achievement_id=3,
                name="Snaking my way downtown",
                description="Get 5 questions wrong in a row",
            ),
            Achievement(
                achievement_id=4,
                name="Would you like some py?",
                description="Solve your first python problem",
            ),
            Achievement(
                achievement_id=5,
                name="It's sort-a-cool",
                description="Solve a sorting problem",
            ),
            Achievement(
                achievement_id=6,
                name="Primal Power",
                description="Solve a primes question",
            ),
            Achievement(
                achievement_id=7,
                name="Laddie up the Ladders",
                description="Reach the top of the leaderboard",
            ),
            Achievement(
                achievement_id=8,
                name="Time waits for no man",
                description="Solve 10 assessments rapidly",
            ),
            Achievement(
                achievement_id=9,
                name="...That's it?",
                description="Complete rapid-fire questions with under 5 seconds spent on each question",
            ),
            Achievement(
                achievement_id=10,
                name="Inception",
                description="Solve a recursive problem",
            ),
        ]
    )

    db.session.add_all(
        [
            Awarded_Badge(id=1, user_id=1, badge_id=1),
            Awarded_Badge(id=2, user_id=2, badge_id=3),
            Awarded_Badge(id=3, user_id=3, badge_id=5),
            Awarded_Badge(id=4, user_id=2, badge_id=2),
        ]
    )

    db.session.add_all(
        [
            Awarded_Achievement(id=1, user_id=2, achievement_id=6),
            Awarded_Achievement(id=2, user_id=1, achievement_id=4),
            Awarded_Achievement(id=3, user_id=2, achievement_id=9),
            Awarded_Achievement(id=4, user_id=3, achievement_id=9),
        ]
    )

    db.session.commit()
