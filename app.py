from flask import Flask, render_template, redirect, session, flash, request, make_response
from flask_debugtoolbar import DebugToolbarExtension
from surveys import surveys

CURRENT_SURVEY_KEY = 'current_survey'
RESPONSES_KEY = "responses"

app = Flask(__name__)

app.config['SECRET_KEY'] = "survey"
app.config['DEBUG_TO_INTERCEPT_REDIRECTS'] = False
debug = DebugToolbarExtension(app)

@app.route('/')
def start():
    """Show the user a form to pick a survey"""
    return render_template('pick.html', surveys=surveys)

@app.route('/', methods=["POST"])
def pick_survey():
    """Select a survey."""
    
    survey_id = request.form['survey_code']

    #functionality to only allow the survey to be taken once (until the cookie times out)
    if request.cookies.get(f"completed_{survey_id}"):
        return render_template("already-done.html")
    
    survey = surveys[survey_id]
    session[CURRENT_SURVEY_KEY] = survey_id

    return render_template("start.html", survey=survey)

@app.route('/begin', methods=["POST"])
def start_survey():
    """Clear the session of any previous responses"""

    session[RESPONSES_KEY] = []

    return redirect("/questions/0")

@app.route('/answer', methods=["POST"])
def answers():
    """Append responses and redirect to the next question"""
    # get the response choice form
    choice = request.form['answer']
    text = request.form.get("text", "")

    # add responses to this session
    responses = session[RESPONSES_KEY]
    responses.append({"choice": choice, "text": text})
    session[RESPONSES_KEY] = responses
    survey_code = session[CURRENT_SURVEY_KEY]
    survey = surveys[survey_code]

    #conditional to check if all questions have been answered
    if (len(responses) == len(survey.questions)):
        return redirect('/finished') 
    
    else:
        return redirect(f'/questions/{len(responses)}')

@app.route('/questions/<int:qid>')
def show_question(qid):
    """Display the current question"""
    responses = session.get(RESPONSES_KEY)
    survey_code = session[CURRENT_SURVEY_KEY]
    survey = surveys[survey_code]

    #conditionals checking the responses
    if (responses is None):
        # Not answering the question or accessing a future question too soon
        return redirect("/")
    
    if (len(responses) == len(survey.questions)):
        # All questions have been answered
        return redirect('/finished') 
    
    if (len(responses) != qid):
        # Answering the questions out of order
        flash(f'Invalid question id: {qid}.')
        return redirect(f"/questions/{len(responses)}")
    
    question = survey.questions[qid]
    return render_template('question.html', question_num=qid, question=question)

@app.route('/finished')
def finish():
    """Survey completed. Show final page"""

    survey_id = session[CURRENT_SURVEY_KEY]
    survey = surveys[survey_id]
    responses = session[RESPONSES_KEY]

    html = render_template("finished.html", survey=survey, responses=responses)

    # set cooking so this survey can't be redone
    response = make_response(html)
    response.set_cookie(f'completed_{survey_id}', "yes", max_age=60)
    return response