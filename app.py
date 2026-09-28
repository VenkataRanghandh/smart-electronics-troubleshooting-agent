import os
import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from hindsight_client import Hindsight

# Load .env
load_dotenv()

# Get API keys
groq_key = os.getenv("GROQ_API_KEY")
hindsight_key = os.getenv("HINDSIGHT_API_KEY")
hindsight_base_url = os.getenv("HINDSIGHT_BASE_URL")
bank_id = os.getenv("HINDSIGHT_BANK_ID")

# Check configuration
if not groq_key:
    st.error("Groq API key not found.")
    st.stop()

if not hindsight_key:
    st.error("Hindsight API key not found.")
    st.stop()

if not bank_id:
    st.error("Hindsight memory bank ID not found.")
    st.stop()

# Create clients
groq_client = Groq(api_key=groq_key)

hindsight = Hindsight(
    base_url=hindsight_base_url,
    api_key=hindsight_key
)

# Page configuration
st.set_page_config(
    page_title="Smart Electronics Troubleshooting Agent",
    page_icon="🔧"
)

# Title
st.title("🔧 Smart Electronics Troubleshooting Agent")

st.write(
    "An AI troubleshooting assistant that learns from previous electronics problems."
)

# Problem input
problem = st.text_area(
    "🔌 Describe your electronics problem:",
    placeholder="Example: My ESP32 restarts when I connect a servo."
)

# Diagnose button
if st.button("🔍 Diagnose"):

    if not problem:
        st.warning("Please describe your electronics problem first.")

    else:

        with st.spinner("🧠 Checking previous troubleshooting experience..."):

            try:
                # Hindsight Recall
                recall_result = hindsight.recall(
                    bank_id=bank_id,
                    query=problem
                )

                memories = recall_result.results

                memory_text = ""

                for memory in memories:
                    memory_text += "- " + memory.text + "\n"

            except Exception as e:
                memories = []
                memory_text = ""
                st.warning("Could not retrieve previous memories.")

        # Show previous experience
        if memories:

            st.subheader("🧠 Previous Experience Found")

            for memory in memories:
                st.info(memory.text)

        else:

            st.info(
                "No similar previous troubleshooting case was found."
            )

        # Ask Groq to diagnose
        with st.spinner("🤖 AI is analyzing the problem..."):

            response = groq_client.chat.completions.create(
                model="openai/gpt-oss-120b",

                messages=[
                    {
                        "role": "system",
                        "content": """
You are Smart Electronics Troubleshooting Agent.

You help students, technicians, and electronics hobbyists troubleshoot
electronics problems.

Use previous troubleshooting experience when it is provided.

For every problem provide:

1. Possible causes
2. Simple tests to perform
3. Recommended solution
4. Safety warning when appropriate

Do not claim that a cause is certain unless there is enough evidence.

Give beginner-friendly and practical instructions.

Clearly mention when a previous case helped with the diagnosis.
"""
                    },

                    {
                        "role": "user",
                        "content": f"""
CURRENT ELECTRONICS PROBLEM:

{problem}

PREVIOUS HINDSIGHT EXPERIENCE:

{memory_text if memory_text else "No previous experience found."}

Use the previous experience when relevant, but do not blindly assume
that the current problem is identical.
"""
                    }
                ]
            )

            answer = response.choices[0].message.content

        # Display diagnosis
        st.subheader("🤖 AI Diagnosis")

        st.write(answer)

        # Store information for feedback
        st.session_state["current_problem"] = problem
        st.session_state["current_answer"] = answer


# Feedback section
if "current_problem" in st.session_state:

    st.divider()

    st.subheader("✅ Did this troubleshooting help?")

    col1, col2 = st.columns(2)

    with col1:

        if st.button("👍 Yes, problem solved"):

            try:

                case_information = f"""
Electronics troubleshooting case:

Problem:
{st.session_state["current_problem"]}

Diagnosis and solution:
{st.session_state["current_answer"]}

Outcome:
The user reported that the troubleshooting solution solved the problem.
"""

                hindsight.retain(
                    bank_id=bank_id,
                    content=case_information
                )

                st.success(
                    "✅ Case saved to Hindsight memory!"
                )

            except Exception as e:

                st.error(
                    "Could not save the case to Hindsight."
                )

    with col2:

        if st.button("👎 No, still not solved"):

            try:

                case_information = f"""
Electronics troubleshooting case:

Problem:
{st.session_state["current_problem"]}

AI diagnosis:
{st.session_state["current_answer"]}

Outcome:
The user reported that the suggested troubleshooting did not solve the problem.
Further investigation is required.
"""

                hindsight.retain(
                    bank_id=bank_id,
                    content=case_information
                )

                st.info(
                    "🧠 The unsuccessful case was also saved to Hindsight."
                )

            except Exception as e:

                st.error(
                    "Could not save the case to Hindsight."
                )
