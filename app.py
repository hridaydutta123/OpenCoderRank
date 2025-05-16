import flask # Flask core library
from flask import Flask, render_template, request, redirect, url_for, session, jsonify # Specific Flask modules
import sqlite3 # For database interaction
import json # For handling JSON data, especially in Python code evaluation
import subprocess # For running external processes (Python code evaluation)
import os # For interacting with the operating system (file paths, environment variables)
import time # For timing tests and questions
import tempfile # For creating temporary files (Python code evaluation)
# Updated import:
import questions_data # Custom module to store question data. Use module prefix for clarity
import sys # For system-specific parameters and functions (e.g., stderr)
import re # For regular expressions (not explicitly used in this file but might be useful, e.g. for input validation)

# Initialize Flask App
app = Flask(__name__)
app.secret_key = os.urandom(24) # Secret key for session management; ensure this is strong and kept secret in production

# --- Constants ---
DATABASE = 'scoreboard.db' # SQLite database file name
SCHEMA_FILE = 'schema.sql' # SQL schema file name

# In-memory dictionary defining available challenges
# The key is the challenge_id, used internally and in URLs.
# 'name' is the display name for the challenge.
# 'description' provides more details about the challenge.
CHALLENGES = {
    "sql_basics": {
        "id": "sql_basics",
        "name": "SQL Basics", # Display name for the SQL basics challenge
        "description": "A collection of fundamental SQL questions.",
    },
    "python_basic_problems": {
        "id": "python_basic_problems",
        "name": "Python Basic Problems", # Consider changing to "Python Basic Problems" for better display
        "description": "A collection of python basic and theory questions.", # Updated description
    }
    # Add more challenges here if needed, e.g., for mixed types or pure MCQ
    # "mcq_theory": {
    #     "id": "mcq_theory",
    #     "name": "Theory & Concepts (MCQ)",
    #     "description": "Test your theoretical knowledge with multiple-choice questions."
    # }
}

# --- Database Helper Functions ---
# These functions provide an abstraction layer for interacting with the SQLite database.

def get_db():
    """
    Opens a new database connection if one is not already open for the current application context.
    Uses flask.g to store the database connection, making it available throughout the request.
    """
    db = getattr(flask.g, '_database', None)
    if db is None:
        db = flask.g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row # Access columns by name (e.g., row['column_name'])
    return db

@app.teardown_appcontext
def close_connection(exception):
    """
    Closes the database connection at the end of the request.
    This is automatically called by Flask.
    """
    db = getattr(flask.g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """
    Initializes the database using the schema defined in SCHEMA_FILE.
    This function is typically called via the 'flask initdb' CLI command.
    """
    with app.app_context(): # Ensures operations are within Flask application context
        db = get_db()
        # Construct the full path to the schema file relative to the app's root path
        schema_path = os.path.join(app.root_path, SCHEMA_FILE)
        if not os.path.exists(schema_path):
            print(f"ERROR: {SCHEMA_FILE} not found at {schema_path}. Database cannot be initialized properly via CLI.", file=sys.stderr)
            return
        with app.open_resource(SCHEMA_FILE, mode='r') as f: # app.open_resource finds files relative to app root
            db.cursor().executescript(f.read()) # Executes all SQL statements in the schema file
        db.commit()
        print("Initialized the database.")

def query_db(query, args=(), one=False):
    """
    Executes a SELECT query and returns the results.
    :param query: The SQL query string.
    :param args: A tuple of arguments to substitute into the query.
    :param one: If True, returns only the first row; otherwise, returns all rows.
    :return: A single row or a list of rows, or None if no results and 'one' is True.
    """
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=()):
    """
    Executes an INSERT, UPDATE, or DELETE query (or other non-SELECT statements).
    Commits the changes to the database.
    :param query: The SQL query string.
    :param args: A tuple of arguments to substitute into the query.
    """
    db = get_db()
    cur = db.cursor()
    cur.execute(query, args)
    db.commit()
    cur.close()

# Helper function to generate QNP data
def _get_qnp_data(session_question_ids, session_answers):
    qnp_data = []
    for q_id_in_list in session_question_ids:
        # Ensure q_id_in_list is string for dictionary lookup, as keys in session['answers'] are strings
        status = session_answers.get(str(q_id_in_list), {}).get('status', 'unattempted')
        qnp_data.append({'id': q_id_in_list, 'status': status})
    return qnp_data

# --- Routes ---
# Define the application's URL endpoints and their corresponding view functions.

@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Handles the homepage (challenge selection and user name input).
    GET: Displays the form.
    POST: Validates input, initializes session, and redirects to the test page.
    """
    if request.method == 'POST':
        username = request.form.get('username')
        challenge_id = request.form.get('challenge_id')

        # Validate username
        if not username or len(username.strip()) < 2:
            flask.flash("Please enter a valid name (at least 2 characters).", "error")
            return render_template('index.html', challenges=CHALLENGES)
        
        # Validate challenge selection
        if not challenge_id or challenge_id not in CHALLENGES:
            flask.flash("Please select a valid challenge.", "error")
            return render_template('index.html', challenges=CHALLENGES)
        
        # Initialize session for the new test
        session.clear() # Clear any previous session data
        session['username'] = username.strip()
        session['challenge_id'] = challenge_id
        session['current_question_idx'] = 0 # Start with the first question
        session['score'] = 0
        session['start_time'] = time.time() # Overall test start time
        session['question_start_time'] = time.time() # Start time for the first question
        
        # Get question IDs for the selected challenge
        challenge_questions_metadata = questions_data.get_all_questions_metadata(challenge_id)
        session['question_ids'] = [q['id'] for q in challenge_questions_metadata]

        # Check if the selected challenge has any questions
        if not session['question_ids']:
            flask.flash(f"No questions found for challenge '{CHALLENGES[challenge_id]['name']}'. Please select another.", "warning")
            session.clear() # Ensure session is cleared if no questions
            return render_template('index.html', challenges=CHALLENGES)

        # Initialize answers status for QNP: keys are stringified question IDs
        session['answers'] = {str(qid): {"status": "unattempted", "attempt_detail": None} for qid in session['question_ids']}
        
        return redirect(url_for('test_page')) # Redirect to the test interface
    
    # For GET request, render the index page with available challenges
    return render_template('index.html', challenges=CHALLENGES)

@app.route('/test')
def test_page():
    """
    Displays the main test interface.
    Requires user to be 'logged in' (i.e., username and challenge_id in session).
    """
    # Redirect to index if session is not properly set up
    if 'username' not in session or 'challenge_id' not in session:
        flask.flash("Please start a new test.", "warning")
        return redirect(url_for('index'))
    
    challenge_id = session['challenge_id']
    challenge_name = CHALLENGES.get(challenge_id, {}).get('name', "Unknown Challenge")
    num_questions = len(session.get('question_ids', []))

    # Safeguard: if no questions, redirect (should be caught at index, but good to have)
    if num_questions == 0:
        flask.flash("No questions available for this challenge. Please restart.", "error")
        return redirect(url_for('index'))
        
    # Render the test page template
    return render_template('test.html', 
                           username=session['username'], 
                           num_questions=num_questions,
                           challenge_name=challenge_name)

@app.route('/api/question', methods=['GET'])
def get_current_question_api():
    """
    API endpoint to fetch the current question data.
    Used by the client-side JavaScript on the test page.
    Returns JSON data for the question or a test completion message.
    """
    # Authentication/session check
    if 'username' not in session or 'challenge_id' not in session:
        return jsonify({"error": "Not authenticated or challenge not selected"}), 401

    current_idx = session.get('current_question_idx', 0)
    question_ids = session.get('question_ids', [])
    challenge_id = session['challenge_id']
    
    # Prepare QNP data based on current answers in session
    qnp_data = _get_qnp_data(session.get('question_ids', []), session.get('answers', {}))

    # Check if all questions have been answered or no questions
    if not question_ids or (current_idx >= len(question_ids) and len(question_ids) > 0) :
        return jsonify({
            "test_completed": True, 
            "score": session.get('score', 0),
            "qnp_data": qnp_data, # Still send QNP data for final state display
            "message": "No questions in this challenge." if not question_ids else "Test completed."
        })

    q_id = question_ids[current_idx]
    question = questions_data.get_question_by_id(q_id)

    if not question or question.get('challenge_id') != challenge_id:
        return jsonify({"error": "Question not found or not part of this challenge"}), 404
    
    session['question_start_time'] = time.time()

    # Prepare client-safe question data
    client_question = {
        'id': question['id'],
        'title': question['title'],
        'level': question['level'],
        'language': question['language'],
        'description': question['description'],
        'points': question['points'],
        'time_limit_seconds': question['time_limit_seconds'],
        'remarks': question.get('remarks') # Add remarks
    }

    if question['language'] == 'python':
        client_question['starter_code'] = question.get('starter_code', '')
    elif question['language'] == 'sql':
        client_question['schema'] = question.get('schema', '')
        client_question['starter_query'] = question.get('starter_query', '') # Add starter_query
    elif question['language'] == 'mcq':
        client_question['options'] = question.get('options', [])
    
    client_question['current_q_num'] = current_idx + 1
    client_question['total_questions'] = len(question_ids)
    client_question['user_score'] = session.get('score', 0)
    client_question['challenge_name'] = CHALLENGES.get(challenge_id, {}).get('name', "Unknown Challenge")
    client_question['qnp_data'] = qnp_data # Add QNP data to response

    return jsonify(client_question)

@app.route('/api/evaluate', methods=['POST'])
def evaluate_code_api():
    """
    API endpoint to evaluate user-submitted code (SQL, Python, or MCQ answer).
    Receives code/answer and question ID, returns evaluation results including updated QNP data.
    """
    if 'username' not in session or 'challenge_id' not in session:
        return jsonify({"error": "Not authenticated or challenge not selected"}), 401

    data = request.get_json()
    user_submission = data.get('code') # For code; for MCQ, this will be the selected index as a string
    q_id = data.get('question_id') 
    challenge_id = session['challenge_id']
    q_id_str = str(q_id) # Use string version for session key

    if user_submission is None or q_id is None: # Allow empty string for code, but not None
        return jsonify({"error": "Missing code/answer or question_id"}), 400

    question = questions_data.get_question_by_id(int(q_id))
    if not question or question.get('challenge_id') != challenge_id:
        return jsonify({"error": "Invalid question_id or not part of this challenge"}), 400
    
    # Prevent re-evaluation/scoring if already answered correctly
    # For MCQs, once answered, it's final (correct or incorrect) for QNP status, but allow re-submission view
    current_answer_info = session['answers'].get(q_id_str, {})
    if current_answer_info.get('status') == 'correct':
        updated_qnp_data = _get_qnp_data(session.get('question_ids', []), session.get('answers', {}))
        return jsonify({
            "status": "already_correct",
            "message": "You have already answered this question correctly.",
            "output": current_answer_info.get('attempt_detail', ''), # Show previous correct output/detail
            "qnp_data": updated_qnp_data,
            "new_score": session.get('score')
        })

    result = {"status": "error", "output": "Evaluation failed.", "passed_all_tests": False}

    if question['language'] == 'sql':
        result = evaluate_sql(user_submission, question)
    elif question['language'] == 'python':
        result = evaluate_python(user_submission, question)
    elif question['language'] == 'mcq':
        result = evaluate_mcq(user_submission, question)
    
    # Update score and session answers based on evaluation
    if result.get('passed_all_tests'):
        if current_answer_info.get('status') != 'correct': # Only add points if not previously correct
            session['score'] = session.get('score', 0) + question['points']
        session['answers'][q_id_str] = {"status": "correct", "attempt_detail": result.get("output", "")}
        result['new_score'] = session['score']
    else:
        # If it was previously correct, don't change status to incorrect. This path usually for first incorrect attempts.
        if current_answer_info.get('status') != 'correct':
             session['answers'][q_id_str] = {"status": "incorrect", "attempt_detail": result.get("output", "")}
        else: # If it was correct, and user resubmits something that is now marked "incorrect" (e.g. they changed code)
              # We keep the status as "correct" from the first successful attempt for QNP, but show new output.
              # This behavior can be debated. Current QNP shows first correct state.
              result['message'] = "Evaluated, but score retained from first correct answer."

    # Prepare updated QNP data to send back for immediate UI update
    result['qnp_data'] = _get_qnp_data(session.get('question_ids', []), session.get('answers', {}))
    
    return jsonify(result)

def evaluate_mcq(selected_option_index_str, question_data):
    """
    Evaluates a user's MCQ answer.
    :param selected_option_index_str: The index of the selected option (as a string).
    :param question_data: Dictionary with question details, including 'options' and 'correct_answer_index'.
    :return: A dictionary with evaluation status and output message.
    """
    try:
        selected_index = int(selected_option_index_str)
    except ValueError:
        return {
            "status": "error",
            "output": "<p class='text-danger'>Invalid answer format.</p>",
            "passed_all_tests": False
        }

    is_correct = (selected_index == question_data['correct_answer_index'])
    output_html = ""

    if is_correct:
        output_html = f"<p class='text-success mt-2'><strong>Status: Correct!</strong></p>"
    else:
        correct_option_text = "N/A"
        if 0 <= question_data['correct_answer_index'] < len(question_data['options']):
             correct_option_text = question_data['options'][question_data['correct_answer_index']]
        output_html = f"<p class='text-danger mt-2'><strong>Status: Incorrect.</strong></p>"
        output_html += f"<p>The correct answer was: '{flask.escape(correct_option_text)}'</p>"
        
    return {
        "status": "correct" if is_correct else "incorrect",
        "output": output_html,
        "passed_all_tests": is_correct
    }

def evaluate_sql(user_query, question_data):
    """
    Evaluates a user's SQL query.
    It sets up an in-memory SQLite database, applies the question's schema,
    runs the user's query and the expected query, then compares results.
    :param user_query: The SQL query submitted by the user.
    :param question_data: The dictionary containing question details (schema, expected_query_output).
    :return: A dictionary with evaluation status, HTML output, and error messages.
    """
    db_eval = sqlite3.connect(':memory:') # Use an in-memory database for evaluation
    cursor_eval = db_eval.cursor()
    output_html = "" # To build HTML representation of results
    is_correct = False
    error_message = None

    try:
        # Apply schema if provided for the question
        if question_data.get('schema'):
            cursor_eval.executescript(question_data['schema'])
        
        # Execute user's query
        cursor_eval.execute(user_query)
        user_results_raw = cursor_eval.fetchall()
        user_cols = [desc[0] for desc in cursor_eval.description] if cursor_eval.description else []
        
        # Execute expected (correct) query
        cursor_eval.execute(question_data['expected_query_output'])
        expected_results_raw = cursor_eval.fetchall()
        expected_cols = [desc[0] for desc in cursor_eval.description] if cursor_eval.description else []

        # Format user's output as HTML table
        output_html += "<h4>Your Output:</h4>"
        if user_results_raw:
            output_html += "<table class='results-table'><thead><tr>"
            for col in user_cols:
                output_html += f"<th>{col}</th>"
            output_html += "</tr></thead><tbody>"
            for row in user_results_raw:
                output_html += "<tr>"
                for val in row:
                    output_html += f"<td>{val}</td>"
                output_html += "</tr>"
            output_html += "</tbody></table>"
        else:
            output_html += "<p>Your query returned no results.</p>"
        
        # Compare column names and row data for correctness
        if user_cols == expected_cols and user_results_raw == expected_results_raw:
            is_correct = True
            output_html += "<p class='text-success mt-2'><strong>Status: Correct!</strong></p>"
        else:
            output_html += "<p class='text-danger mt-2'><strong>Status: Incorrect.</strong></p>"
            # Optionally, for debugging, one might add expected output here,
            # but typically not shown to users in a test environment.

    except sqlite3.Error as e:
        error_message = f"SQL Error: {e}"
        output_html += f"<p class='text-danger'><strong>Error:</strong> {e}</p>"
    finally:
        db_eval.close() # Ensure the in-memory database is closed

    return {
        "status": "correct" if is_correct else "incorrect",
        "output": output_html,
        "error": error_message, # SQL execution error, if any
        "passed_all_tests": is_correct # For SQL, "correct" means all tests (i.e., data match) passed
    }


@app.route('/api/jump_to_question', methods=['POST'])
def jump_to_question_api():
    if 'username' not in session or 'challenge_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    data = request.get_json()
    target_idx = data.get('index')
    question_ids = session.get('question_ids', [])

    if target_idx is None or not (0 <= target_idx < len(question_ids)):
        return jsonify({"jumped": False, "message": "Invalid question index."}), 400
    
    session['current_question_idx'] = target_idx
    session['question_start_time'] = time.time() # Reset timer for the jumped-to question
    return jsonify({"jumped": True, "new_idx": target_idx})


@app.route('/api/previous_question', methods=['POST'])
def previous_question_api():
    """
    API endpoint to navigate to the previous question.
    Updates the current question index in the session.
    """
    if 'username' not in session or 'challenge_id' not in session:
        return jsonify({"error": "Not authenticated or challenge not selected"}), 401

    current_idx = session.get('current_question_idx', 0)
    
    if current_idx > 0:
        current_idx -= 1
        session['current_question_idx'] = current_idx
        session['question_start_time'] = time.time() 
        return jsonify({"navigated": True, "new_idx": current_idx})
    else:
        return jsonify({"navigated": False, "message": "Already at the first question."})


@app.route('/api/next_question', methods=['POST'])
def next_question_api():
    """
    API endpoint to advance to the next question or finalize the test.
    Updates the current question index in the session.
    If it's the last question, it finalizes the score and records it.
    """
    if 'username' not in session or 'challenge_id' not in session:
        return jsonify({"error": "Not authenticated or challenge not selected"}), 401

    current_idx = session.get('current_question_idx', 0)
    question_ids = session.get('question_ids', [])
    challenge_id = session['challenge_id'] 
    
    current_idx += 1 
    session['current_question_idx'] = current_idx

    if current_idx >= len(question_ids): 
        total_time_taken = time.time() - session['start_time']
        execute_db("INSERT INTO scoreboard (username, challenge_id, score, time_taken_seconds) VALUES (?, ?, ?, ?)",
                   (session['username'], challenge_id, session['score'], round(total_time_taken)))
        
        # Prepare QNP data for the completion screen as well
        qnp_data = _get_qnp_data(session.get('question_ids', []), session.get('answers', {}))

        return jsonify({
            "test_completed": True, 
            "score": session['score'], 
            "total_time": round(total_time_taken),
            "challenge_id": challenge_id,
            "qnp_data": qnp_data # Send final QNP state
        })
    else: 
        session['question_start_time'] = time.time() 
        return jsonify({"test_completed": False, "next_question_loaded": True, "new_idx": current_idx})

@app.route('/scoreboards')
def scoreboards_list_page():
    """
    Displays a page listing all available challenges, linking to their respective scoreboards.
    """
    return render_template('scoreboards_list.html', challenges=CHALLENGES)

@app.route('/scoreboard/<challenge_id>')
def scoreboard_page(challenge_id):
    """
    Displays the scoreboard for a specific challenge.
    Fetches scores from the database for the given challenge_id.
    """
    if challenge_id not in CHALLENGES:
        flask.flash("Invalid challenge selected for scoreboard.", "error")
        return redirect(url_for('scoreboards_list_page')) 
    
    challenge = CHALLENGES[challenge_id] 
    scores = query_db("SELECT username, score, time_taken_seconds, timestamp FROM scoreboard WHERE challenge_id = ? ORDER BY score DESC, time_taken_seconds ASC LIMIT 20", (challenge_id,))
    return render_template('scoreboard.html', scores=scores, challenge=challenge)


@app.route('/restart_test', methods=['POST'])
def restart_test():
    """
    Allows the user to restart the test process.
    Clears the session, redirecting the user to the homepage to select a new challenge/name.
    """
    session.clear() 
    flask.flash("Test restarted. Please select a challenge and enter your name.", "info")
    return redirect(url_for('index'))

# --- CLI command to initialize DB ---
@app.cli.command('initdb')
def initdb_command():
    """
    Flask CLI command: 'flask initdb'
    Initializes the database by calling the init_db() function.
    """
    init_db()

# --- Main execution block ---
if __name__ == '__main__':
    schema_full_path = os.path.join(os.path.dirname(__file__), SCHEMA_FILE)
    if not os.path.exists(DATABASE):
        print(f"Database {DATABASE} not found. Attempting to initialize...")
        if not os.path.exists(schema_full_path):
            print(f"CRITICAL ERROR: {SCHEMA_FILE} not found at {schema_full_path}. Database cannot be created automatically.", file=sys.stderr)
            print(f"Please create '{SCHEMA_FILE}' or run 'flask initdb' if Flask is installed and '{SCHEMA_FILE}' exists.", file=sys.stderr)
            sys.exit(1) 
        try:
            db_conn = sqlite3.connect(DATABASE)
            with open(schema_full_path, mode='r') as f:
                db_conn.cursor().executescript(f.read())
            db_conn.commit()
            db_conn.close()
            print(f"Database {DATABASE} created and schema from {SCHEMA_FILE} initialized successfully.")
        except Exception as e:
            print(f"Error initializing database directly: {e}", file=sys.stderr)
            sys.exit(1) 
            
    app.run(debug=True, host='0.0.0.0', port='5555')