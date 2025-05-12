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
        "description": "A collection of python basic questions.",
    }
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
        session['answers'] = {} # To store answers and prevent re-scoring correct ones
        
        # Get question IDs for the selected challenge
        challenge_questions_metadata = questions_data.get_all_questions_metadata(challenge_id)
        session['question_ids'] = [q['id'] for q in challenge_questions_metadata]

        # Check if the selected challenge has any questions
        if not session['question_ids']:
            flask.flash(f"No questions found for challenge '{CHALLENGES[challenge_id]['name']}'. Please select another.", "warning")
            return render_template('index.html', challenges=CHALLENGES)

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

    # Check if all questions have been answered
    if current_idx >= len(question_ids) and len(question_ids) > 0 : # Check len > 0 to handle empty challenges properly
        return jsonify({"test_completed": True, "score": session.get('score', 0)})
    elif not question_ids: # No questions in this challenge
         return jsonify({"test_completed": True, "score": session.get('score', 0), "message": "No questions in this challenge."})


    q_id = question_ids[current_idx]
    # Fetch the full question data using its global ID
    question = questions_data.get_question_by_id(q_id)

    # Validate question exists and belongs to the current challenge
    if not question or question.get('challenge_id') != challenge_id:
        # This is a defensive check; question_ids should already be filtered by challenge
        return jsonify({"error": "Question not found or not part of this challenge"}), 404
    
    session['question_start_time'] = time.time() # Reset question start time

    # Prepare question data to send to the client (exclude sensitive info like expected output for SQL)
    client_question = {k: v for k, v in question.items() if k not in ['expected_query_output', 'test_cases', 'challenge_id']}
    if question['language'] == 'python':
        client_question['starter_code'] = question.get('starter_code', '') # Include starter code for Python
    
    # Add metadata for UI display
    client_question['current_q_num'] = current_idx + 1
    client_question['total_questions'] = len(question_ids)
    client_question['user_score'] = session.get('score', 0)
    client_question['challenge_name'] = CHALLENGES.get(challenge_id, {}).get('name', "Unknown Challenge")

    return jsonify(client_question)

@app.route('/api/evaluate', methods=['POST'])
def evaluate_code_api():
    """
    API endpoint to evaluate user-submitted code (SQL or Python).
    Receives code and question ID, returns evaluation results.
    """
    if 'username' not in session or 'challenge_id' not in session:
        return jsonify({"error": "Not authenticated or challenge not selected"}), 401

    data = request.get_json()
    user_code = data.get('code')
    q_id = data.get('question_id') # This is the global question ID
    challenge_id = session['challenge_id']

    if not user_code or q_id is None:
        return jsonify({"error": "Missing code or question_id"}), 400

    question = questions_data.get_question_by_id(int(q_id)) # Fetch question by its global ID
    # Validate question and ensure it's part of the current user's challenge
    if not question or question.get('challenge_id') != challenge_id:
        return jsonify({"error": "Invalid question_id or not part of this challenge"}), 400
    
    # Prevent re-evaluation if already answered correctly
    # str(q_id) because session keys are typically strings when coming from JSON or forms
    if session['answers'].get(str(q_id), {}).get('correct'):
        return jsonify({
            "status": "already_correct",
            "message": "You have already answered this question correctly.",
            "output": session['answers'][str(q_id)].get('output', '') # Show previous correct output
        })

    result = {"status": "error", "output": "Evaluation failed.", "passed_all_tests": False}

    # Delegate to language-specific evaluation function
    if question['language'] == 'sql':
        result = evaluate_sql(user_code, question)
    elif question['language'] == 'python':
        result = evaluate_python(user_code, question)
    
    # Update score and session if evaluation was successful and tests passed
    if result.get('passed_all_tests'):
        session['score'] = session.get('score', 0) + question['points']
        session['answers'][str(q_id)] = {"correct": True, "output": result.get("output", "")}
        result['new_score'] = session['score'] # Send updated score back to client
    else:
        # Record that an attempt was made, even if incorrect
        session['answers'][str(q_id)] = {"correct": False, "output": result.get("output", "")}

    # Flask automatically converts dicts to JSON with jsonify
    return jsonify(result)


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


def evaluate_python(user_code, question_data):
    """
    Evaluates a user's Python code by running it against predefined test cases.
    Writes the user's code and a test harness to a temporary file,
    then executes it using a subprocess with a timeout.
    :param user_code: The Python code submitted by the user.
    :param question_data: Dictionary with question details, including 'test_cases'.
    :return: A dictionary with evaluation status, HTML output of test results, and overall success.
    """
    results_html = "" # HTML representation of test case results
    all_tests_passed = True # Flag to track if all test cases pass
    overall_status_message = ""
    
    # Create a temporary file for the user's code + test harness.
    # This provides a basic form of isolation. More advanced sandboxing would use Docker or similar.
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".py", delete=False) as tmp_code_file:
        # Write necessary imports (if any specific are allowed/needed by the harness)
        tmp_code_file.write("import sys\n")
        tmp_code_file.write("import json\n\n")
        
        # Write the user's code
        tmp_code_file.write(user_code + "\n\n")

        # Dynamically generate and write the test harness code
        # This harness will call the user's function with test case inputs
        # and capture results, then print them as JSON.
        harness_code = "def run_tests():\n"
        harness_code += "    results = []\n"
        # Attempt to extract the function name from the user's code (simplistic extraction)
        # Assumes standard `def function_name(...):` format.
        # More robust parsing might be needed for complex scenarios.
        match = re.search(r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", user_code)
        if not match: # Fallback or error if function name cannot be determined
            # This situation should ideally be handled more gracefully,
            # e.g., by returning an error to the user.
            # For now, it might lead to runtime errors in the subprocess.
            func_name = "user_function" # Placeholder, likely to fail if user named it differently
        else:
            func_name = match.group(1)

        for i, test_case in enumerate(question_data["test_cases"]):
            input_args_str = ", ".join(map(repr, test_case["input_args"])) # Format input arguments for the call
            harness_code += f"    try:\n"
            # Call the extracted function name with the test case's input arguments
            harness_code += f"        actual = {func_name}({input_args_str})\n"
            # Compare actual output with expected output
            harness_code += f"        passed_check = actual == {repr(test_case['expected_output'])}\n"
            harness_code += f"        results.append({{'name': '{test_case.get('name', f'Test {i+1}')}', 'input': {test_case['input_args']}, 'expected': {repr(test_case['expected_output'])}, 'actual': actual, 'passed': passed_check, 'error': None}})\n"
            harness_code += f"    except Exception as e_test:\n" # Catch errors during test execution
            harness_code += f"        results.append({{'name': '{test_case.get('name', f'Test {i+1}')}', 'input': {test_case['input_args']}, 'expected': {repr(test_case['expected_output'])}, 'actual': None, 'passed': False, 'error': str(e_test)}})\n"
        
        harness_code += "    print(json.dumps(results))\n\n" # Output results as JSON string
        harness_code += "run_tests()\n" # Execute the test runner function
        
        tmp_code_file.write(harness_code)
        tmp_file_name = tmp_code_file.name # Get the name of the temporary file

    python_executable = sys.executable # Use the same Python interpreter that runs the Flask app
    try:
        # Execute the temporary file in a subprocess
        # Timeout is crucial for preventing infinite loops or very long computations.
        # Resource limits (memory, CPU) are harder to enforce cross-platform without extra libraries or Docker.
        process = subprocess.run(
            [python_executable, tmp_file_name],
            capture_output=True, # Capture stdout and stderr
            text=True,           # Decode output as text
            timeout=5            # 5-second timeout for execution
        )

        if process.returncode == 0: # Successful execution of the script
            try:
                test_results = json.loads(process.stdout) # Parse JSON output from the harness
                results_html += "<ul class='list-group'>"
                for res in test_results:
                    status_icon = "✅" if res['passed'] else "❌"
                    status_class = "text-success" if res['passed'] else "text-danger"
                    results_html += f"<li class='list-group-item'>"
                    results_html += f"<strong>{res['name']}:</strong> {status_icon} <span class='{status_class}'>"
                    results_html += "Passed" if res['passed'] else "Failed"
                    results_html += "</span><br>"
                    results_html += f"<small>Input: <code>{res['input']}</code>, Expected: <code>{res['expected']}</code>, Got: <code>{res['actual'] if not res['error'] else 'Error'}</code></small>"
                    if res['error']:
                         results_html += f"<br><small class='text-danger'>Error during this test: {res['error']}</small>"
                    results_html += "</li>"
                    if not res['passed']:
                        all_tests_passed = False
                results_html += "</ul>"

            except json.JSONDecodeError:
                results_html = "<p class='text-danger'>Error: Could not parse test output from script.</p>"
                results_html += f"<pre>Script STDOUT:\n{process.stdout}</pre>" # Show raw output for debugging
                all_tests_passed = False
        else: # Script execution failed (non-zero return code)
            results_html = f"<p class='text-danger'>Error during code execution (Return Code: {process.returncode}):</p>"
            # Show stderr if available, otherwise stdout, for error diagnosis
            error_output = process.stderr if process.stderr else process.stdout
            results_html += f"<pre>{error_output}</pre>" 
            all_tests_passed = False

    except subprocess.TimeoutExpired:
        results_html = "<p class='text-danger'>Error: Code execution timed out (max 5 seconds).</p>"
        all_tests_passed = False
    except Exception as e_outer: # Catch other potential errors in this evaluation function
        results_html = f"<p class='text-danger'>An unexpected error occurred during evaluation: {e_outer}</p>"
        all_tests_passed = False
    finally:
        os.remove(tmp_file_name) # Clean up (delete) the temporary file

    # Set overall status message based on test results
    if all_tests_passed:
        overall_status_message = "<p class='text-success mt-2'><strong>All tests passed!</strong></p>"
    else:
        overall_status_message = "<p class='text-danger mt-2'><strong>Some tests failed.</strong></p>"
    
    return {
        "status": "success" if all_tests_passed else "failed_tests",
        "output": overall_status_message + results_html, # Combine status message and detailed results
        "passed_all_tests": all_tests_passed
    }


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
        session['question_start_time'] = time.time() # Reset start time for the new question
        return jsonify({"navigated": True})
    else:
        # Already at the first question or invalid state
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
    challenge_id = session['challenge_id'] # Get current challenge ID from session
    
    current_idx += 1 # Move to the next question index
    session['current_question_idx'] = current_idx

    if current_idx >= len(question_ids): # All questions attempted
        total_time_taken = time.time() - session['start_time']
        # Save score to the database
        # The challenge_id is now correctly included in the scoreboard entry
        execute_db("INSERT INTO scoreboard (username, challenge_id, score, time_taken_seconds) VALUES (?, ?, ?, ?)",
                   (session['username'], challenge_id, session['score'], round(total_time_taken)))
        return jsonify({
            "test_completed": True, 
            "score": session['score'], 
            "total_time": round(total_time_taken),
            "challenge_id": challenge_id # Pass challenge_id for constructing scoreboard link on client
        })
    else: # There are more questions
        session['question_start_time'] = time.time() # Reset start time for the new question
        return jsonify({"test_completed": False, "next_question_loaded": True})

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
    # Validate that the requested challenge_id is valid
    if challenge_id not in CHALLENGES:
        flask.flash("Invalid challenge selected for scoreboard.", "error")
        return redirect(url_for('scoreboards_list_page')) # Redirect if challenge ID is unknown
    
    challenge = CHALLENGES[challenge_id] # Get challenge details
    # Query database for scores related to this challenge_id
    scores = query_db("SELECT username, score, time_taken_seconds, timestamp FROM scoreboard WHERE challenge_id = ? ORDER BY score DESC, time_taken_seconds ASC LIMIT 20", (challenge_id,))
    return render_template('scoreboard.html', scores=scores, challenge=challenge)


@app.route('/restart_test', methods=['POST'])
def restart_test():
    """
    Allows the user to restart the test process.
    Clears the session, redirecting the user to the homepage to select a new challenge/name.
    """
    session.clear() # Clear all session data
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
    # print("Initialized the database.") # This is already printed within init_db()

# --- Main execution block ---
if __name__ == '__main__':
    # This block runs when the script is executed directly (e.g., `python app.py`)

    # Construct the full path to schema.sql, assuming it's in the same directory as app.py
    schema_full_path = os.path.join(os.path.dirname(__file__), SCHEMA_FILE)

    # --- Initial Database Setup (if database file doesn't exist) ---
    # This is a convenience for development. For production, `flask initdb` is preferred.
    if not os.path.exists(DATABASE):
        print(f"Database {DATABASE} not found. Attempting to initialize...")
        if not os.path.exists(schema_full_path):
            print(f"CRITICAL ERROR: {SCHEMA_FILE} not found at {schema_full_path}. Database cannot be created automatically.", file=sys.stderr)
            print(f"Please create '{SCHEMA_FILE}' or run 'flask initdb' if Flask is installed and '{SCHEMA_FILE}' exists.", file=sys.stderr)
            sys.exit(1) # Critical error, cannot proceed without schema
        
        # Manually connect and initialize DB (outside app context, for first-time setup)
        try:
            db_conn = sqlite3.connect(DATABASE)
            with open(schema_full_path, mode='r') as f:
                db_conn.cursor().executescript(f.read())
            db_conn.commit()
            db_conn.close()
            print(f"Database {DATABASE} created and schema from {SCHEMA_FILE} initialized successfully.")
        except Exception as e:
            print(f"Error initializing database directly: {e}", file=sys.stderr)
            sys.exit(1) # Exit if automatic DB creation fails
            
    # Run the Flask development server
    # debug=True enables reloader and debugger; should be False in production.
    # host='0.0.0.0' makes the server accessible from any network interface.
    # port='5555' sets the port number.
    app.run(debug=True, host='0.0.0.0', port='5555')