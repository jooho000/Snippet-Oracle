"""
Generates fake snippet and user data for testing purposes.
"""

from datetime import datetime, timedelta, timezone
import os
import random
import faker
import requests
import re
import data

fake = faker.Faker()


# -------------------------------------------
# 🔹 Sample Coding Snippets by Language
# -------------------------------------------
CODE_SNIPPETS = {
    "Python": [
        "def hello_world():\n    print('Hello, world!')",
        "import numpy as np\narr = np.array([1, 2, 3])\nprint(arr)",
        "from flask import Flask\napp = Flask(__name__)\n@app.route('/')\ndef home():\n    return 'Hello, Flask!'",
    ],
    "JavaScript": [
        "function greet() {\n    console.log('Hello, world!');\n}",
        "const add = (a, b) => a + b;",
        "document.querySelector('#btn').addEventListener('click', () => alert('Button clicked!'));",
    ],
    "Java": [
        "public class Main {\n    public static void main(String[] args) {\n        System.out.println('Hello, world!');\n    }\n}",
        "List<String> names = Arrays.asList('Alice', 'Bob', 'Charlie');\nnames.forEach(System.out::println);",
    ],
    "C++": [
        "#include <iostream>\nusing namespace std;\nint main() {\n    cout << 'Hello, world!';\n    return 0;\n}",
        "vector<int> nums = {1, 2, 3, 4};\nfor (int num : nums) {\n    cout << num << endl;\n}",
    ],
    "Go": [
        'package main\nimport "fmt"\nfunc main() {\n    fmt.Println("Hello, World!")\n}',
        "func add(a int, b int) int {\n    return a + b\n}",
    ],
    "Rust": [
        'fn main() {\n    println!("Hello, world!");\n}',
        "fn add(a: i32, b: i32) -> i32 {\n    a + b\n}",
    ],
    "Swift": [
        'import Foundation\nprint("Hello, World!")',
        "func add(a: Int, b: Int) -> Int {\n    return a + b\n}",
    ],
    "R": [
        'print("Hello, World!")',
        "sum <- function(a, b) { return(a + b) }",
    ],
    "PHP": [
        '<?php\necho "Hello, World!";\n?>',
        "<?php\nfunction add($a, $b) {\n    return $a + $b;\n}\n?>",
    ],
    "SQL": [
        "SELECT * FROM users WHERE active = 1;",
        "CREATE TABLE snippets (id INTEGER PRIMARY KEY, code TEXT, tags TEXT);",
    ],
    "HTML/CSS": [
        "<!DOCTYPE html>\n<html>\n<head><title>My Page</title></head>\n<body>\n<h1>Hello World</h1>\n</body>\n</html>",
        "button {\n    padding: 10px;\n    background-color: blue;\n    color: white;\n    border: none;\n    cursor: pointer;\n}",
    ],
}


# -------------------------------------------
# 🔹 Function to Generate Descriptions
# -------------------------------------------
def generate_description(language, tags):
    """Generate a meaningful description based on the snippet's language and tags."""

    descriptions = {
        "Python": [
            "A Python function demonstrating {} to solve common programming problems.",
            "This {} example showcases best practices in Python development.",
            "A Python snippet for handling {} efficiently in real-world applications.",
            "Learn how to use {} in Python with this concise example.",
        ],
        "JavaScript": [
            "A JavaScript snippet showcasing {} to enhance web interactivity.",
            "This {} example demonstrates how to optimize JavaScript code.",
            "A useful JavaScript function for handling {} in front-end applications.",
            "Explore how to use {} effectively in JavaScript.",
        ],
        "Java": [
            "A Java program implementing {} for scalable applications.",
            "This Java snippet illustrates {} with best coding practices.",
            "Learn how {} works in Java with this practical example.",
            "A useful Java technique for {} in object-oriented programming.",
        ],
        "C++": [
            "A C++ implementation demonstrating {} for efficient performance.",
            "This C++ snippet showcases {} using modern coding principles.",
            "Learn how to apply {} in C++ for system-level programming.",
            "A great example of using {} to optimize C++ applications.",
        ],
        "SQL": [
            "An SQL query designed for {} to manage databases effectively.",
            "This SQL snippet demonstrates best practices for {} queries.",
            "Learn how to use SQL for {} in real-world scenarios.",
            "A powerful SQL command to handle {} efficiently.",
        ],
        "HTML/CSS": [
            "A clean HTML/CSS example for designing {} with best practices.",
            "This snippet helps in styling {} using modern CSS techniques.",
            "Learn how to create {} layouts using HTML and CSS.",
            "A web design pattern for building {} effectively.",
        ],
        "Go": [
            "A Go snippet demonstrating {} for high-performance applications.",
            "This Go example showcases how to implement {} with simplicity.",
            "Learn how to use Go for {} in cloud-native development.",
            "A concise GoLang snippet illustrating {}.",
        ],
        "Rust": [
            "A Rust snippet showcasing {} for safe and efficient code.",
            "This Rust example demonstrates how to implement {} effectively.",
            "Learn how to write {} in Rust with this practical example.",
            "A Rust-based solution for {} in systems programming.",
        ],
        "Swift": [
            "A Swift example for {} in iOS app development.",
            "This Swift snippet demonstrates {} for Apple platforms.",
            "Learn how {} works in Swift with this practical example.",
            "An essential Swift function for handling {} in mobile apps.",
        ],
        "R": [
            "An R script for {} in statistical computing and data science.",
            "This R example demonstrates {} for data visualization.",
            "Learn how to use R for {} in analytics and machine learning.",
            "A practical R implementation of {} for researchers.",
        ],
        "PHP": [
            "A PHP snippet demonstrating {} for web development.",
            "This PHP function is useful for handling {} efficiently.",
            "Learn how to build {} in PHP with this concise example.",
            "A practical PHP solution for {} in backend development.",
        ],
    }

    description_template = random.choice(
        descriptions.get(language, ["A code snippet showcasing {}."])
    )
    relevant_tags = (
        random.sample(tags, k=description_template.count("{}"))
        if tags
        else ["general programming"]
    )

    return description_template.format(*relevant_tags)


# -------------------------------------------
# 🔹 Function to Generate Relevant Tags
# -------------------------------------------
def tags(language):
    """
    Generate programming-related tags relevant to the given language.
    """

    relevant_tags = {
        "Python": ["Flask", "Django", "NumPy", "Pandas", "TensorFlow", "FastAPI"],
        "JavaScript": [
            "Node.js",
            "React",
            "Vue.js",
            "Express",
            "Angular",
            "TypeScript",
        ],
        "Java": ["Spring", "Android", "Hibernate"],
        "C++": ["Qt", "GameDev", "OpenCV"],
        "Go": ["Golang", "Microservices"],
        "Rust": ["Systems", "Memory-Safety", "Concurrency"],
        "Swift": ["iOS", "Xcode", "SwiftUI"],
        "R": ["Statistics", "DataScience", "MachineLearning"],
        "PHP": ["Laravel", "WordPress", "Web"],
        "SQL": ["PostgreSQL", "MySQL", "SQLite"],
        "HTML/CSS": ["Bootstrap", "Tailwind", "Sass"],
    }

    # Ensure the first tag is the language
    selected_tags = [language]

    # Get additional relevant tags (if available)
    if language in relevant_tags and relevant_tags[language]:  # Ensure tags exist
        max_sample_size = min(len(relevant_tags[language]), 3)  # Avoid oversampling
        selected_tags.extend(
            random.sample(relevant_tags[language], k=random.randint(1, max_sample_size))
        )

    return selected_tags


# -------------------------------------------
# 🔹 Function to Generate a Code Snippet Object
# -------------------------------------------
def code():
    """
    Return a randomly selected meaningful coding snippet along with its matching tags.
    """

    language = random.choice(list(CODE_SNIPPETS.keys()))
    snippet = random.choice(CODE_SNIPPETS[language])
    snippet_tags = tags(language)
    snippet_description = generate_description(language, snippet_tags)

    return {
        "snippet": f"// Language: {language}\n{snippet}",
        "tags": snippet_tags,
        "description": snippet_description,
    }


# -------------------------------------------
# 🔹 Function to Generate Other Random Data
# -------------------------------------------
def username():
    return fake.user_name()


def title():
    """
    Generate a coding-related title with a variety of tech-related words.
    """

    tech_words = [
        "Algorithm",
        "Function",
        "Component",
        "Module",
        "Class",
        "Database",
        "Library",
        "Framework",
        "Interface",
        "Service",
        "Protocol",
        "Structure",
        "API",
        "Query",
        "Handler",
        "Parser",
        "Compiler",
        "Pipeline",
        "Processor",
        "Encryption",
        "Security",
        "Validation",
        "Optimization",
        "Pattern",
        "Factory",
        "Decorator",
        "Singleton",
        "Adapter",
        "Observer",
        "Event",
        "Controller",
        "Model",
        "View",
        "Serializer",
        "Router",
        "Endpoint",
        "Webhook",
        "Microservice",
        "Cache",
        "Session",
        "Authentication",
        "Authorization",
        "Migration",
        "Index",
        "Cluster",
        "Transaction",
        "Repository",
        "Schema",
        "Mapping",
        "Generator",
        "Renderer",
        "Context",
        "Resolver",
        "Debugger",
        "Executor",
        "Interpreter",
        "Compiler",
        "Analyzer",
        "Transformer",
        "Expression",
        "Iterator",
        "Stream",
        "Listener",
        "Emitter",
        "Scheduler",
        "Workflow",
        "Trigger",
        "Lambda",
        "Hook",
        "Reducer",
        "Selector",
        "State",
        "Middleware",
        "Thread",
        "Concurrency",
        "Asynchronous",
        "Promise",
        "Callback",
        "EventLoop",
        "WebSocket",
        "Protocol",
        "QueryBuilder",
        "ConnectionPool",
        "Graph",
        "Node",
        "Edge",
        "Vertex",
        "Snapshot",
        "Checkpoint",
        "Sharding",
        "LoadBalancer",
        "Container",
        "Pod",
        "Orchestrator",
        "Registry",
        "Daemon",
        "Monitor",
        "Log",
        "Metrics",
        "Tracer",
        "Telemetry",
        "CLI",
        "SDK",
        "CLI Tool",
        "Plugin",
        "Extension",
        "Data Structure",
        "HashMap",
        "Dictionary",
        "LinkedList",
        "Heap",
        "BinaryTree",
        "GraphQL",
        "REST API",
        "SQL Query",
        "NoSQL",
        "ORM",
        "Machine Learning",
        "Deep Learning",
        "Neural Network",
        "AI Model",
        "Computer Vision",
        "Natural Language Processing",
        "Big Data",
        "Data Science",
        "Data Analysis",
        "Visualization",
        "Regression",
        "Classification",
        "Clustering",
        "Pipeline",
        "ETL",
        "Feature Engineering",
        "Hyperparameter Tuning",
        "Deployment",
        "CI/CD",
        "Testing",
        "Mocking",
        "Version Control",
        "Git",
        "Branching",
        "Commit",
        "Merge",
        "Rebase",
        "CI Pipeline",
        "Docker",
        "Kubernetes",
        "Cloud Function",
        "Lambda Function",
        "Edge Computing",
        "IoT",
        "Blockchain",
        "Smart Contract",
        "Ethereum",
        "WebAssembly",
        "PWA",
        "SPA",
        "Serverless",
        "Microfrontend",
    ]

    return f"{fake.word()} {random.choice(tech_words)}".capitalize()


def time():
    """
    Generate a realistic timestamp.
    """

    days_ago = random.random() * 365 * 2
    return datetime.now(timezone.utc) + timedelta(-days_ago)


# -------------------------------------------
# 🔹 Load Frankenstein Text for Random Paragraphs
# -------------------------------------------
def _load_franken():
    with open("mock_data/frankenstein.txt") as file:
        global franken, franken_starts
        franken = re.sub("[\r\n]+", " ", file.read()).replace("_", "")
        franken_starts = [0]
        for i in range(len(franken) - 1):
            c = franken[i]
            if c == "." or c == "!" or c == "?":
                franken_starts.append(i + 1)
        file.close()


if not os.path.exists("mock_data"):
    os.mkdir("mock_data")
try:
    _load_franken()
except FileNotFoundError:
    with open("mock_data/frankenstein.txt", "x") as file:
        req = requests.get("https://www.gutenberg.org/cache/epub/84/pg84.txt")
        req.encoding = "UTF8"
        text = req.text
        file.write(text[text.find("You will rejoice") : text.rfind("*** END")])
        file.close()
    _load_franken()


def paragraph():
    """
    Generate a paragraph from Frankenstein text.
    """

    sentence_count = random.randint(1, 5)
    ind_start = random.randint(0, len(franken_starts) - sentence_count - 1)
    char_start = franken_starts[ind_start]
    char_end = franken_starts[ind_start + sentence_count]
    return franken[char_start:char_end].strip()
