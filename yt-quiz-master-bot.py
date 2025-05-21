from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.youtube import YouTubeTools
from textwrap import dedent

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
            Your job is to turn those concepts into a clean, well-structured quiz that can be presented directly to learners.
        """,

        instructions=[
            "Read the provided list of learning concepts carefully. These are the only source material for your quiz.",
            "Use the user's preferences to determine the quiz format:",
            "- If 'Multiple Choice': Create 4 answer options (A–D), with one correct answer clearly marked in **bold**.",
            "- If 'Short Answer': Ask concise open-ended questions expecting 1–2 sentence responses.",
            "- If 'Mixed': Combine both types, alternating or mixing formats logically.",
            "Apply the specified difficulty level to control the complexity of the questions:",
            "- 'Beginner': Focus on basic recall and clear understanding.",
            "- 'Intermediate': Emphasize reasoning, comparisons, or multi-step ideas.",
            "- 'Advanced': Include nuanced or applied questions requiring deeper insight.",
            "Generate 3-4 questions per concept depending on its depth.",
            "Number all questions sequentially.",
            "Present the final output in clean **Markdown**.",
            "Do NOT include any introductory text, explanations, or instructions — only the quiz content.",
            "Do not fabricate content. Use only the information explicitly provided in the concepts.",
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
        st.markdown("## 📝 Generated Quiz")
        st.markdown(st.session_state.youtube_quiz, unsafe_allow_html=True)

        st.download_button(
            label="📥 Download Quiz",
            data=st.session_state.youtube_quiz,
            file_name="youtube_quiz.md",
            mime="text/markdown"
        )


if __name__ == "__main__":
    main()

