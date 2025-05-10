# coding_platform_flask/questions_data.py

# This list stores all the questions for the coding platform.
# Each question is a dictionary with a specific structure.
#
# Common fields for all questions:
#   - "id": (Integer) A unique identifier for the question. Must be globally unique.
#   - "challenge_id": (String) Identifier for the challenge this question belongs to.
#                     This should match a key in the CHALLENGES dictionary in `app.py`.
#   - "title": (String) The display title of the question.
#   - "level": (String) Difficulty level (e.g., "Easy", "Medium", "Hard").
#   - "language": (String) The programming language for the question ("sql" or "python").
#   - "description": (String) A detailed description of the problem or task.
#   - "points": (Integer) Points awarded for correctly solving the question.
#   - "time_limit_seconds": (Integer) Suggested time limit for the question in seconds.
#                           (Currently informational, not strictly enforced by backend to stop submission).
#
# Fields specific to SQL questions ("language": "sql"):
#   - "schema": (String) SQL DDL (Data Definition Language) and DML (Data Manipulation Language)
#               statements to set up the necessary tables and initial data for the question.
#               This schema is executed in an in-memory SQLite database for evaluation.
#   - "expected_query_output": (String) A SQL query that produces the correct result set.
#                              The user's query output is compared against the output of this query.
#
# Fields specific to Python questions ("language": "python"):
#   - "starter_code": (String) Boilerplate code provided to the user to start with.
#                     Typically includes the function signature.
#   - "test_cases": (List of Dictionaries) Each dictionary defines a test case:
#       - "input_args": (List) A list of arguments that will be passed to the user's function.
#       - "expected_output": The value that the user's function is expected to return for the given `input_args`.
#       - "name": (String, Optional) A descriptive name for the test case (e.g., "Edge case: empty list").

QUESTIONS = [
    {
        "id": 1,
        "challenge_id": "sql_basics",
        "title": "Select All Customers",
        "level": "Easy",
        "language": "sql",
        "description": "Write a SQL query to select all columns for all records from the 'Customers' table.",
        "schema": """
CREATE TABLE Customers (
    CustomerID INT PRIMARY KEY,
    CustomerName VARCHAR(255),
    Country VARCHAR(100)
);
INSERT INTO Customers (CustomerID, CustomerName, Country) VALUES (1, 'Alfreds Futterkiste', 'Germany');
INSERT INTO Customers (CustomerID, CustomerName, Country) VALUES (2, 'Ana Trujillo Emparedados y helados', 'Mexico');
INSERT INTO Customers (CustomerID, CustomerName, Country) VALUES (3, 'Antonio Moreno Taquería', 'Mexico');
        """,
        "expected_query_output": "SELECT * FROM Customers;",
        "points": 10,
        "time_limit_seconds": 300
    },
    {
        "id": 2,
        "challenge_id": "sql_basics",
        "title": "Customers in Mexico",
        "level": "Medium",
        "language": "sql",
        "description": "Write a SQL query to select the 'CustomerName' and 'Country' for all customers located in 'Mexico'.",
        "schema": """
CREATE TABLE Customers (
    CustomerID INT PRIMARY KEY,
    CustomerName VARCHAR(255),
    Country VARCHAR(100)
);
INSERT INTO Customers (CustomerID, CustomerName, Country) VALUES (1, 'Alfreds Futterkiste', 'Germany');
INSERT INTO Customers (CustomerID, CustomerName, Country) VALUES (2, 'Ana Trujillo Emparedados y helados', 'Mexico');
INSERT INTO Customers (CustomerID, CustomerName, Country) VALUES (3, 'Antonio Moreno Taquería', 'Mexico');
INSERT INTO Customers (CustomerID, CustomerName, Country) VALUES (4, 'Around the Horn', 'UK');
        """,
        "expected_query_output": "SELECT CustomerName, Country FROM Customers WHERE Country = 'Mexico';",
        "points": 15,
        "time_limit_seconds": 300
    },
    {
        "id": 3,
        "challenge_id": "sql_basics",
        "title": "Count Customers by Country",
        "level": "Hard",
        "language": "sql",
        "description": "Write a SQL query to count the number of customers in each country. Return 'Country' and the count aliased as 'NumberOfCustomers'. Order by 'NumberOfCustomers' descending.",
        "schema": """
CREATE TABLE Customers (
    CustomerID INT PRIMARY KEY,
    CustomerName VARCHAR(255),
    Country VARCHAR(100)
);
INSERT INTO Customers (CustomerID, CustomerName, Country) VALUES (1, 'Alfreds Futterkiste', 'Germany');
INSERT INTO Customers (CustomerID, CustomerName, Country) VALUES (2, 'Ana Trujillo Emparedados y helados', 'Mexico');
INSERT INTO Customers (CustomerID, CustomerName, Country) VALUES (3, 'Antonio Moreno Taquería', 'Mexico');
INSERT INTO Customers (CustomerID, CustomerName, Country) VALUES (4, 'Berglunds snabbköp', 'Sweden');
INSERT INTO Customers (CustomerID, CustomerName, Country) VALUES (5, 'Blauer See Delikatessen', 'Germany');
        """,
        "expected_query_output": "SELECT Country, COUNT(CustomerID) AS NumberOfCustomers FROM Customers GROUP BY Country ORDER BY NumberOfCustomers DESC;",
        "points": 25,
        "time_limit_seconds": 300
    },
    {
        "id": 4,
        "challenge_id": "python_basic_problems", # This question belongs to the Python challenge
        "title": "Find Max in List",
        "level": "Medium",
        "language": "python",
        "description": "Write a Python function called `find_max(numbers)` that takes a list of numbers and returns the largest number in the list. Return `None` if the list is empty.",
        "starter_code": "def find_max(numbers):\n    # Your code here\n    pass",
        "test_cases": [
            {"input_args": [[1, 2, 3, 2, 1]], "expected_output": 3, "name": "Positive numbers"},
            {"input_args": [[-1, -5, -2]], "expected_output": -1, "name": "Negative numbers"},
            {"input_args": [[]], "expected_output": None, "name": "Empty list"},
            {"input_args": [[5]], "expected_output": 5, "name": "Single element"},
        ],
        "points": 15,
        "time_limit_seconds": 300
    },
    {
        "id": 5, # New question ID
        "challenge_id": "python_basic_problems",
        "title": "Check Palindrome",
        "level": "Medium",
        "language": "python",
        "description": "Write a Python function called `is_palindrome(text)` that takes a string and returns `True` if the string is a palindrome, `False` otherwise. Ignore case and non-alphanumeric characters.",
        "starter_code": "import re\n\ndef is_palindrome(text):\n    # Your code here\n    # Hint: You might want to preprocess the text to remove non-alphanumeric characters and convert to a consistent case.\n    pass",
        "test_cases": [
            {"input_args": ["Racecar!"], "expected_output": True, "name": "Mixed case with punctuation"},
            {"input_args": ["A man, a plan, a canal: Panama"], "expected_output": True, "name": "Classic palindrome"},
            {"input_args": ["hello"], "expected_output": False, "name": "Simple non-palindrome"},
            {"input_args": [""], "expected_output": True, "name": "Empty string"}, # An empty string is often considered a palindrome
            {"input_args": ["Was it a car or a cat I saw?"], "expected_output": True, "name": "Longer palindrome"},
        ],
        "points": 20,
        "time_limit_seconds": 360 # Slightly longer time limit
    }
]

def get_question_by_id(q_id):
    """
    Retrieves a single question dictionary from the QUESTIONS list by its unique ID.
    :param q_id: The integer ID of the question to find.
    :return: The question dictionary if found, otherwise None.
    """
    # Assumes q_id is globally unique among all questions.
    for q in QUESTIONS:
        if q['id'] == q_id:
            return q
    return None # Return None if no question with the given ID is found

def get_all_questions_metadata(challenge_id_filter):
    """
    Retrieves metadata for all questions belonging to a specific challenge.
    Metadata includes 'id', 'time_limit_seconds', and 'title'.
    This is used, for example, to populate the session with question IDs for a test.
    :param challenge_id_filter: The ID of the challenge for which to retrieve question metadata.
    :return: A list of dictionaries, where each dictionary contains metadata for a question.
    """
    # Filter questions that belong to the specified challenge_id_filter
    challenge_questions = [q for q in QUESTIONS if q.get("challenge_id") == challenge_id_filter]
    # Return a simplified list containing only essential metadata for each question
    return [{"id": q["id"], "time_limit_seconds": q["time_limit_seconds"], "title": q["title"]} for q in challenge_questions]

# Note: The function `get_all_questions_metadata` is designed to filter by challenge.
# If a function to get *all* questions (irrespective of challenge) metadata were needed,
# a new function or modification would be required. For the current application flow,
# filtering by challenge is appropriate for setting up a specific test session.