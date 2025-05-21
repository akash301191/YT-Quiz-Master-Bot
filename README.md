# YT Quiz Master Bot

YT Quiz Master Bot is a smart Streamlit application that turns any educational YouTube video into a fully interactive quiz. Powered by [Agno](https://github.com/agno-agi/agno) and OpenAI's GPT-4o, the bot analyzes video content, extracts structured concepts, and generates a well-formatted quiz tailored to your preferred question style and difficulty level.

## Folder Structure

```
YT-Quiz-Master-Bot/
├── yt-quiz-master-bot.py
├── README.md
└── requirements.txt
```

* **yt-quiz-master-bot.py**: The main Streamlit application.
* **requirements.txt**: Required Python packages.
* **README.md**: This documentation file.

## Features

* **YouTube Video Input**
  Paste a YouTube link and let the bot extract educational content automatically.

* **Quiz Preference Selection**
  Choose from multiple question styles — Multiple Choice, Short Answer, or Mixed — and set your preferred difficulty level.

* **Two-Agent Pipeline**

  * The **Concept Extraction Agent** analyzes the video and identifies key learning concepts.
  * The **Quiz Generation Agent** uses those concepts to create a structured quiz in Markdown format.

* **Clean Quiz Output**
  Your quiz is displayed using section headers, numbered questions, and bold formatting for correct answers (in multiple-choice format).

* **Download Option**
  Download the quiz as a `.md` file for reuse, review, or distribution.

* **Simple Streamlit UI**
  A user-friendly and responsive interface with clearly structured inputs and outputs.

## Prerequisites

* Python 3.11 or higher
* An OpenAI API key ([Get one here](https://platform.openai.com/account/api-keys))

## Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/akash301191/YT-Quiz-Master-Bot.git
   cd YT-Quiz-Master-Bot
   ```

2. **(Optional) Create and activate a virtual environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate        # On macOS/Linux
   # or
   venv\Scripts\activate           # On Windows
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Run the app**:

   ```bash
   streamlit run yt-quiz-master-bot.py
   ```

2. **In your browser**:

   * Enter your OpenAI API key in the sidebar.
   * Paste a YouTube video URL.
   * Choose your quiz preferences.
   * Click **🎯 Generate YouTube Quiz**.
   * View and download your AI-generated quiz.

3. **Download Option**
   Use the **📥 Download Quiz** button to save the quiz in `.md` format.

## Code Overview

* **`render_quiz_preferences()`**: Collects YouTube video URL and quiz generation preferences.
* **`render_sidebar()`**: Captures and stores OpenAI API key in the session state.
* **`generate_youtube_quiz()`**:

  * Uses the `Concept Extraction Agent` to extract detailed learning concepts.
  * Passes these to the `Quiz Generation Agent` to build a complete quiz in Markdown.
* **`main()`**: Defines the layout, handles inputs, and manages quiz generation and rendering.

## Contributions

Contributions are welcome! Feel free to fork the repo, suggest features, report issues, or open a pull request. Make sure your updates are clear, tested, and enhance the bot’s educational utility.