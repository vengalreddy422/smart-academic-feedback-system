def get_identified_questions(queryset):
    
    questions = []

    for response in queryset:

        for answer in response.formanswer_set.all():

            question = (

                answer.question.question
            )

            if question not in questions:

                questions.append(
                    question
                )

    return questions


# ==========================================
# ANONYMOUS QUESTIONS
# ==========================================

def get_anonymous_questions(queryset):

    questions = []

    for response in queryset:

        # PRIVATE ANONYMOUS
        if hasattr(

            response,

            'formanswer_set'
        ):

            all_answers = (

                response.formanswer_set.all()
            )

        # PUBLIC ANONYMOUS
        else:

            all_answers = (

                response.publicformanswer_set.all()
            )

        for answer in all_answers:

            question = (

                answer.question.question
            )

            if question not in questions:

                questions.append(
                    question
                )

    return questions


# ==========================================
# IDENTIFIED ANSWERS
# ==========================================

def build_identified_answers(response):

    answers_map = {}

    for answer in response.formanswer_set.all():

        answers_map[
            answer.question.question
        ] = answer.answer

    return answers_map


# ==========================================
# ANONYMOUS ANSWERS
# ==========================================

def build_anonymous_answers(response):

    answers_map = {}

    # PRIVATE ANONYMOUS
    if hasattr(

        response,

        'formanswer_set'
    ):

        all_answers = (

            response.formanswer_set.all()
        )

    # PUBLIC ANONYMOUS
    else:

        all_answers = (

            response.publicformanswer_set.all()
        )

    for answer in all_answers:

        answers_map[
            answer.question.question
        ] = answer.answer

    return answers_map