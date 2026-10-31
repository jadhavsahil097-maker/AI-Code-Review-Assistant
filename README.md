#  AI-Based Code Review Assistant

An AI-powered Python code review web application that analyzes source code, detects errors, identifies security vulnerabilities, and suggests improvements with corrected code.

##  Features

- **Code Analysis:** Analyze submitted Python code.
- **Code Quality Score:** Get an overall code quality score.
- **Error Detection:** Identify coding errors and potential bugs.
- **Security Analysis:** Detect possible security vulnerabilities.
- **Performance Analysis:** Identify performance-related issues.
- **Code Smell Detection:** Find bad coding practices.
- **AI Code Review:** Get intelligent suggestions and explanations.
- **Corrected Code:** Receive improved code suggestions.

##  Technologies Used

- Python
- Flask
- HTML
- CSS
- JavaScript
- Pylint
- Ollama / AI Integration

##  Project Structure

```text
AI-CODE-REVIEW-ASSISTANT/
│
├── app.py
├── services/
│   └── ai_reviewer.py
├── templates/
│   ├── index.html
│   └── result.html
├── static/
│   ├── css/
│   └── js/
├── requirements.txt
└── README.md
```

##  Installation & Setup

**1. Clone the repository**

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

**2. Open project folder**

```bash
cd AI-CODE-REVIEW-ASSISTANT
```

**3. Create virtual environment**

```bash
python -m venv venv
```

**4. Activate virtual environment**

```bash
venv\Scripts\activate
```

**5. Install dependencies**

```bash
pip install -r requirements.txt
```

**6. Run the application**

```bash
python app.py
```

**7. Open in browser**

```text
http://127.0.0.1:5000
```

##  How It Works

1. Enter or paste Python code into the application.
2. Submit the code for analysis.
3. The system performs code quality and security checks.
4. AI analyzes the submitted code.
5. View the quality score, detected issues, and suggestions.
6. Get corrected code to improve your programming.

##  Project Objective

The main objective of this project is to simplify code reviewing through AI technology, helping developers identify programming mistakes, improve code quality, and write more secure and efficient Python programs.

##  Author

**Sahil Jadhav**

## License

This project is developed for educational purposes.
