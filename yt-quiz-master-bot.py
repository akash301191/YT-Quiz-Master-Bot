from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.youtube import YouTubeTools
from textwrap import dedent

import re, json
import streamlit as st

def render_sidebar():
    st.sidebar.title("🔐 API Configuration")
    st.sidebar.markdown("---")

    # OpenAI API Key input
    openai_api_key = st.sidebar.text_input(
        "OpenAI API Key",
        type="password",
        help="Don't have an API key? Get one [here](https://platform.openai.com/account/api-keys)."
    )
    if openai_api_key:
        st.session_state.openai_api_key = openai_api_key
        st.sidebar.success("✅ OpenAI API key updated!")

    st.sidebar.markdown("---")

def render_quiz_preferences():
    st.markdown("---")
    col1, col2 = st.columns(2)

    # Column 1: YouTube Video Input
    with col1:
        st.subheader("🎥 Input YouTube Video")
        youtube_url = st.text_input(
            "Paste the YouTube video URL you want to convert into a quiz",
            placeholder="https://www.youtube.com/watch?v=example"
        )

    # Column 2: Quiz Generation Preferences
    with col2:
        st.subheader("🧠 Quiz Preferences")

        question_style = st.selectbox(
            "What type of questions should be generated?",
            ["Multiple Choice", "Short Answer", "Mixed"]
        )

        quiz_difficulty = st.selectbox(
            "Choose the quiz difficulty level:",
            ["Beginner", "Intermediate", "Advanced"]
        )

    return {
        "youtube_url": youtube_url,
        "question_style": question_style,
        "quiz_difficulty": quiz_difficulty
    }

def generate_youtube_quiz(user_quiz_preferences) -> str:
    youtube_url = user_quiz_preferences["youtube_url"]
    question_style = user_quiz_preferences["question_style"]
    quiz_difficulty = user_quiz_preferences["quiz_difficulty"]

    concept_extraction_agent = Agent(
        name="Concept Extraction Agent",
        model=OpenAIChat(id="gpt-4o", api_key=st.session_state.openai_api_key),
        tools=[YouTubeTools()],
        instructions=dedent("""\
            You are a concept extraction assistant. Your goal is to extract and explain core learning concepts from educational YouTube videos. Do not describe what the video is doing — focus purely on the underlying ideas being taught.

            ## Output Requirements:
            - Extract the **main learning concepts** from the video.
            - Each concept should be explained in **4-6 sentences** with enough depth and clarity to serve as input for quiz question generation.
            - Focus on what the concept **means**, **why it matters**, and **how it works**.
            - Avoid narrative phrases like “the video explains…” or “this segment shows…”.
            - Do not mention the video, narrator, presenter, or structure.
            - No markdown formatting, headings, or metadata.
            - Do not list definitions or terminology separately.
            - Return a numbered list of concepts with plain-text, explanatory descriptions.

            Your response should be structured and informative, not conversational or descriptive.
        """),
        add_datetime_to_instructions=False,
        markdown=False,
    )  

    concept_response = concept_extraction_agent.run(f"Analyze this video: {youtube_url}")
    core_concepts = concept_response.content 

    quiz_generation_agent = Agent(
        name="Quiz Generation Agent",
        role="Generates markdown-formatted quiz questions from core learning concepts based on user preferences.",
        model=OpenAIChat(id="gpt-4o", api_key=st.session_state.openai_api_key),
        
        description="""
            You are a quiz generation expert. You receive a set of core learning concepts along with user preferences such as question style and difficulty.
            Your job is to turn those concepts into a clean, consistently structured quiz that can be presented directly to learners.
        """,

        instructions=[
            "Carefully read the provided list of learning concepts. These are your only source of truth for creating questions.",
            "Respect the user's preferences for question style and difficulty:",
            "- If 'Multiple Choice': Write 4 options (A–D). **Bold the correct answer**.",
            "- If 'Short Answer': Ask an open-ended question suitable for a 1–2 sentence response.",
            "- If 'Mixed': Mix both styles logically.",
            "Apply the specified difficulty level:",
            "- 'Beginner': Basic recall questions.",
            "- 'Intermediate': Conceptual or reasoning-based.",
            "- 'Advanced': Analytical, comparative, or applied questions.",
            "Generate 2–3 questions per concept depending on depth.",
            "Follow this exact structure for output:",
            "1. Question text",
            "   - A. Option A",
            "   - B. Option B",
            "   - C. Option C",
            "   - D. Option D",
            "",
            "   **Correct Answer: C**",
            "",
            "OR for short answer:",
            "2. Question text",
            "   (Short Answer)",
            "",
            "Title your output with:",
            "### 📘 Quiz Title: Concept Review Quiz",
            "Do not include additional commentary or explanation before or after the quiz.",
        ],

        markdown=True,
        add_datetime_to_instructions=False,
    )

    # Prepare the prompt
    quiz_prompt = f"""
    ## Core Concepts:
    {core_concepts}

    ## User Preferences:
    Question Style: {question_style}
    Difficulty: {quiz_difficulty}
    """

    quiz_response = quiz_generation_agent.run(quiz_prompt)
    youtube_quiz = quiz_response.content

    return youtube_quiz
    
def clean_markdown(text):
    # Removes bold (**text**), italic (*text* or _text_), inline code (`text`)
    return re.sub(r'[*_`]+', '', text).strip()

def render_structured_quiz(quiz_markdown: str):
    st.markdown("## 🧪 Interactive Quiz")

    user_responses = []

    col1, col2 = st.columns(2)
    with col1:
        # Remove title from markdown
        cleaned_markdown = re.sub(r'### 📘 Quiz Title:.*\n?', '', quiz_markdown).strip()

        # Split questions
        question_blocks = re.split(r'\n(?=\d+\.\s)', cleaned_markdown)

        for idx, block in enumerate(question_blocks):
            lines = block.strip().split('\n')
            if not lines or len(lines[0].strip()) == 0:
                continue

            question_line = lines[0]
            question_text_raw = re.sub(r'^\d+\.\s*', '', question_line).strip()

            # Collect option lines (those that begin with A–D style)
            options = [clean_markdown(line.strip()[3:].strip()) for line in lines[1:] if line.strip().startswith(('-', '–'))]

            # Check if it's a short answer: either explicitly marked or has no options
            is_short_answer = "(Short Answer)" in question_text_raw or len(options) == 0

            # Render the question
            st.markdown(f"**{question_line}**")

            # Capture response
            if is_short_answer:
                response = st.text_input("Your Answer:", key=f"text_input_{idx}")
            else:
                response = st.radio("Select an option:", options, key=f"radio_{idx}", index=None)

            # Append structured response
            user_responses.append({
                "question_number": idx + 1,
                "question_text": question_text_raw,
                "question_type": "short_answer" if is_short_answer else "multiple_choice",
                "options": options if not is_short_answer else None,
                "user_answer": response
            })

    st.markdown("---")

    return user_responses

def grade_quiz_responses(user_responses):
    # Format data to JSON
    user_response_json = json.dumps(user_responses, indent=2)

    grading_agent = Agent(
        name="Quiz Grading Agent",
        role="Evaluates quiz responses and returns a score with detailed feedback.",
        model=OpenAIChat(id="gpt-4o", api_key=st.session_state.openai_api_key),
        description="""
            You are a grading assistant. You are given a list of quiz questions with user responses. 
            Evaluate each answer for correctness and clarity, and assign partial or full credit.
            Return an overall score, and individual feedback per question.
        """,
        instructions=[
            "You will receive a JSON list of user responses.",
            "Each item contains: question text, user answer, question type, and options (if any).",
            "For multiple-choice, check if the answer matches the correct choice (you can infer or reason it from the question text).",
            "For short answer, assess if the user response is factually correct and relevant.",
            "Return the following structured output:",
            "- A numbered list of feedback per question: correctness, explanation, and score (out of 1).",
            "- Final total score out of total questions.",
            "- Bonus: Mention 1 area to improve for the user.",
            "Use clean, readable Markdown in your final output."
        ],
        markdown=True,
        add_datetime_to_instructions=False,
    )

    # Send to grading agent
    prompt = f"""
    You are grading the following user quiz responses. The list is provided as structured JSON.

    {user_response_json}

    Evaluate and return:
    - Feedback per question
    - Score out of total
    - One improvement suggestion
    """
    grading_result = grading_agent.run(prompt)
    return grading_result.content

        
def main() -> None:
    # Page config
    st.set_page_config(page_title="YT Quiz Master Bot", page_icon="❓", layout="wide")

    # Custom styling
    st.markdown(
        """
        <style>
        .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        div[data-testid="stTextInput"] {
            max-width: 1200px;
            margin-left: auto;
            margin-right: auto;
        }
        .stTextInput > div > div > input {
            margin-left: 0 !important;
            text-align: left !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Header and intro
    st.markdown("<h1 style='font-size: 2.5rem;'>❓ YT Quiz Master Bot</h1>", unsafe_allow_html=True)
    st.markdown(
        "Welcome to YT Quiz Master Bot — a smart Streamlit companion that turns YouTube videos into interactive quizzes, helping you learn actively by answering questions based on video content.",
        unsafe_allow_html=True
    )

    render_sidebar()
    user_quiz_preferences = render_quiz_preferences()
    
    st.markdown("---")

    if st.button("🎯 Generate YouTube Quiz"):
        if not hasattr(st.session_state, "openai_api_key"):
            st.error("Please provide your OpenAI API key in the sidebar.")
        else:
            with st.spinner("Analyzing the video and preparing your quiz..."):
                youtube_quiz = generate_youtube_quiz(user_quiz_preferences=user_quiz_preferences)
                st.session_state.youtube_quiz = youtube_quiz

    if "youtube_quiz" in st.session_state:
        user_quiz_responses = render_structured_quiz(st.session_state.youtube_quiz)

        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("📝 Submit & Get Score"):
                with st.spinner("Grading your quiz..."):
                    feedback = grade_quiz_responses(user_quiz_responses)
                    st.markdown("## 📊 Quiz Feedback")
                    st.markdown(feedback, unsafe_allow_html=True)

        with col2:
            st.download_button(
                label="📥 Download Quiz",
                data=st.session_state.youtube_quiz,
                file_name="youtube_quiz.md",
                mime="text/markdown"
            )



if __name__ == "__main__":
    main()

