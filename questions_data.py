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
#   - "language": (String) The programming language/type ("sql", "python", or "mcq").
#   - "description": (String) A detailed description of the problem or task.
#   - "points": (Integer) Points awarded for correctly solving the question.
#   - "time_limit_seconds": (Integer) Suggested time limit for the question in seconds.
#                           (Currently informational, not strictly enforced by backend to stop submission).
#   - "remarks": (String, Optional) Additional notes or hints about the question (e.g., interview source).
#
# Fields specific to SQL questions ("language": "sql"):
#   - "schema": (String) SQL DDL (Data Definition Language) and DML (Data Manipulation Language)
#               statements to set up the necessary tables and initial data for the question.
#               This schema is executed in an in-memory SQLite database for evaluation.
#   - "expected_query_output": (String) A SQL query that produces the correct result set.
#                              The user's query output is compared against the output of this query.
#   - "starter_query": (String, Optional) A pre-filled SQL query for the user to start with or fix.
#
# Fields specific to Python questions ("language": "python"):
#   - "starter_code": (String) Boilerplate code provided to the user to start with.
#                     Typically includes the function signature.
#   - "test_cases": (List of Dictionaries) Each dictionary defines a test case:
#       - "input_args": (List) A list of arguments that will be passed to the user's function.
#       - "expected_output": The value that the user's function is expected to return for the given `input_args`.
#       - "name": (String, Optional) A descriptive name for the test case (e.g., "Edge case: empty list").
#
# Fields specific to Multiple Choice Questions ("language": "mcq"):
#   - "options": (List of Strings) The list of choices for the MCQ.
#   - "correct_answer_index": (Integer) The 0-based index of the correct option in the "options" list.

QUESTIONS = [
    {
        "id": 1,
        "challenge_id": "sql_basics",
        "title": "Select Customer Names",
        "level": "Easy",
        "language": "sql",
        "description": "Write a SQL query to select only the 'CustomerName' column from the 'Customers' table.",
        "schema": """
CREATE TABLE Customers (
    CustomerID INT PRIMARY KEY,
    CustomerName VARCHAR(255),
    Country VARCHAR(100)
);
INSERT INTO Customers (CustomerID, CustomerName, Country) VALUES (1, 'Maria Anders', 'Germany');
INSERT INTO Customers (CustomerID, CustomerName, Country) VALUES (2, 'Francisco Chang', 'Mexico');
    """,
        "expected_query_output": "SELECT CustomerName FROM Customers;",
        "points": 10,
        "time_limit_seconds": 300,
        "remarks": "A fundamental SELECT statement."
    },
    {
        "id": 2,
        "challenge_id": "sql_basics",
        "title": "Select Unique Countries",
        "level": "Easy",
        "language": "sql",
        "description": "Write a SQL query to select all unique countries from the 'Customers' table.",
        "schema": """
CREATE TABLE Customers (
    CustomerID INT PRIMARY KEY,
    CustomerName VARCHAR(255),
    Country VARCHAR(100)
);
INSERT INTO Customers (CustomerID, CustomerName, Country) VALUES (1, 'Thomas Hardy', 'UK');
INSERT INTO Customers (CustomerID, CustomerName, Country) VALUES (2, 'Christina Berglund', 'Sweden');
INSERT INTO Customers (CustomerID, CustomerName, Country) VALUES (3, 'Hanna Moos', 'Germany');
INSERT INTO Customers (CustomerID, CustomerName, Country) VALUES (4, 'Frédérique Citeaux', 'France');
    """,
        "expected_query_output": "SELECT DISTINCT Country FROM Customers;",
        "points": 10,
        "time_limit_seconds": 300
    },
    {
        "id": 3,
        "challenge_id": "sql_basics",
        "title": "Order Customers by Name",
        "level": "Easy",
        "language": "sql",
        "description": "Write a SQL query to select all customers ordered alphabetically by 'CustomerName'.",
        "schema": """
CREATE TABLE Customers (
    CustomerID INT PRIMARY KEY,
    CustomerName VARCHAR(255),
    Country VARCHAR(100)
);
INSERT INTO Customers (CustomerID, CustomerName, Country) VALUES (1, 'Ernst Handel', 'Austria');
INSERT INTO Customers (CustomerID, CustomerName, Country) VALUES (2, 'Island Trading', 'UK');
INSERT INTO Customers (CustomerID, CustomerName, Country) VALUES (3, 'Laughing Bacchus Winecellars', 'Canada');
    """,
        "expected_query_output": "SELECT * FROM Customers ORDER BY CustomerName;",
        "points": 10,
        "time_limit_seconds": 300
    },
    {
        "id": 4,
        "challenge_id": "sql_basics",
        "title": "Customers Not From USA",
        "level": "Medium",
        "language": "sql",
        "description": "Write a SQL query to select 'CustomerName' and 'Country' for all customers who are not from the USA.",
        "schema": """
CREATE TABLE Customers (
    CustomerID INT PRIMARY KEY,
    CustomerName VARCHAR(255),
    Country VARCHAR(100)
);
INSERT INTO Customers (CustomerID, CustomerName, Country) VALUES (1, 'Wolski Zajazd', 'Poland');
INSERT INTO Customers (CustomerID, CustomerName, Country) VALUES (2, 'Tradição Hipermercados', 'Brazil');
INSERT INTO Customers (CustomerID, CustomerName, Country) VALUES (3, 'Great Lakes Food Market', 'USA');
    """,
        "expected_query_output": "SELECT CustomerName, Country FROM Customers WHERE Country != 'USA';",
        "points": 15,
        "time_limit_seconds": 300,
        "remarks": "Often asked in screening tests."
    },
    # ... (other existing SQL questions remain, can add remarks to them if needed)
    {
        "id": 18,  # Assuming this was the last SQL question from your snippet
        "challenge_id": "sql_basics",
        "title": "Full List of Orders and Customers",
        "level": "Hard",
        "language": "sql",
        "description": "Write a SQL query using FULL OUTER JOIN to list all customers and orders including unmatched rows.",
        "schema": """
    CREATE TABLE Customers (
        CustomerID INT PRIMARY KEY,
        CustomerName VARCHAR(255)
    );
    CREATE TABLE Orders (
        OrderID INT PRIMARY KEY,
        CustomerID INT
    );
    INSERT INTO Customers VALUES (1, 'Anna');
    INSERT INTO Orders VALUES (101, 2);
        """,
        "expected_query_output": "SELECT Customers.CustomerName, Orders.OrderID FROM Customers FULL OUTER JOIN Orders ON Customers.CustomerID = Orders.CustomerID;",
        "points": 25,
        "time_limit_seconds": 300
    },
    # New "Fix the Query" SQL Question
    {
        "id": 19,
        "challenge_id": "sql_basics",
        "title": "Fix Faulty Product Query",
        "level": "Medium",
        "language": "sql",
        "description": "The following query attempts to select product names that cost more than 50, but it has a syntax error and a logical error regarding the price. Fix it to show products with Price > 50.",
        "starter_query": "SELECT ProductName, Price FROM Prodcts WHERE Price > '50';",  # Intentional errors
        "schema": """
CREATE TABLE Products (
    ProductID INT PRIMARY KEY,
    ProductName VARCHAR(255),
    Price DECIMAL(10,2)
);
INSERT INTO Products (ProductID, ProductName, Price) VALUES (1, 'Chai', 18.00);
INSERT INTO Products (ProductID, ProductName, Price) VALUES (2, 'Chang', 19.00);
INSERT INTO Products (ProductID, ProductName, Price) VALUES (3, 'Aniseed Syrup', 10.00);
INSERT INTO Products (ProductID, ProductName, Price) VALUES (4, 'Mishi Kobe Niku', 97.00);
INSERT INTO Products (ProductID, ProductName, Price) VALUES (5, 'Ikura', 31.00);
    """,
        "expected_query_output": "SELECT ProductName, Price FROM Products WHERE Price > 50;",
        "points": 20,
        "time_limit_seconds": 400,
        "remarks": "Common task: Debugging existing SQL queries. Asked in XYZ Corp 2024."
    },
    # New Multiple Choice Questions (MCQs)
    {
        "id": 20,
        "challenge_id": "python_basic_problems",  # Or create a new challenge for theory
        "title": "Python Variable Scope",
        "level": "Easy",
        "language": "mcq",
        "description": "What is the scope of a variable defined inside a function in Python, by default?",
        "options": [
            "Global scope",
            "Local scope",
            "Class scope",
            "Module scope"
        ],
        "correct_answer_index": 1,
        "points": 5,
        "time_limit_seconds": 60,
        "remarks": "Fundamental concept for understanding Python functions."
    },
    {
        "id": 21,
        "challenge_id": "python_basic_problems",
        "title": "Primary Key in SQL",
        "level": "Easy",
        "language": "mcq",
        "description": "What is the primary purpose of a PRIMARY KEY constraint in a SQL table?",
        "options": [
            "To sort the data automatically.",
            "To uniquely identify each record in a table.",
            "To allow NULL values in the column.",
            "To create an index for faster text searching."
        ],
        "correct_answer_index": 1,
        "points": 5,
        "time_limit_seconds": 90,
        "remarks": "Core database concept. Frequently appears in SQL theory questions."
    },
    {
        "id": 22,  # Example Python question with remarks
        "challenge_id": "python_basic_problems",
        "title": "Sum of Two Numbers",
        "level": "Easy",
        "language": "python",
        "description": "Write a Python function `sum_two(a, b)` that returns the sum of two numbers.",
        "starter_code": "def sum_two(a, b):\n    # Your code here\n    pass",
        "test_cases": [
            {"input_args": [1, 2], "expected_output": 3, "name": "Positive numbers"},
            {"input_args": [-1, 1], "expected_output": 0, "name": "Negative and positive"},
            {"input_args": [0, 0], "expected_output": 0, "name": "Zeros"},
        ],
        "points": 10,
        "time_limit_seconds": 180,
        "remarks": "A very basic Python coding warm-up. Good for checking syntax understanding."
    },
    {
        "id": 23,
        "challenge_id": "java_intro",
        "title": "Sum of Two Numbers",
        "level": "Easy",
        "language": "java",
        "description": "Write a Java function `sum_two(a, b)` that returns the sum of two numbers.",
        "starter_code": "public class Solution{\n\tpublic int solve(int a,int b){\n\t\t// Write Code here\n\t\treturn 0;\n\t}\n}",
        "test_cases": [
            {"input_args": [1, 2], "expected_output": 3, "name": "Positive numbers"},
            {"input_args": [-1, 1], "expected_output": 0, "name": "Negative and positive"},
            {"input_args": [0, 0], "expected_output": 0, "name": "Zeros"},
        ],
        "points": 10,
        "time_limit_seconds": 180,
        "remarks": "A very basic Java coding warm-up. Good for checking syntax understanding."
    },
    # Ensure ID 6 from README example is distinct or updated. Assuming original question ID 6 (Sum of two numbers) might be like the one above.
    # Let's assume there was a Python challenge "python_advanced_problems".
    # If we used that ID 6 earlier in description for python sum. Let's make it ID 22 in the actual list.
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
    return None  # Return None if no question with the given ID is found


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
    return [{"id": q["id"], "time_limit_seconds": q["time_limit_seconds"], "title": q["title"]} for q in
            challenge_questions]

# Note: The function `get_all_questions_metadata` is designed to filter by challenge.
# If a function to get *all* questions (irrespective of challenge) metadata were needed,
# a new function or modification would be required. For the current application flow,
# filtering by challenge is appropriate for setting up a specific test session.
