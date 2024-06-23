import streamlit as st
import subprocess
from groq import Groq
import google.generativeai as genai
from openai import OpenAI
import os
import time

# Set up environment variables for sensitive information
os.environ['GROQ_API_KEY'] = "YOUR_API_KEY"
os.environ['GENAI_API_KEY'] = "YOUR_API_KEY"
os.environ['MIXTRAL_API_KEY'] = "YOUR_API_KEY"

# Initialize clients
groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))
genai.configure(api_key=os.getenv('GENAI_API_KEY'))
gemini_model = genai.GenerativeModel('gemini-1.5-flash')
mixtral_client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv('MIXTRAL_API_KEY')
)
st.set_page_config(layout="wide")

def home():
    st.markdown("<h1 style='text-align: center; font-family: Arial, sans-serif;'>Welcome to AI Coding Assistant</h1>", unsafe_allow_html=True)
    st.write("""
    This application offers several powerful AI-driven coding tools to assist you with your programming needs:
    """)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div class='fadeIn'>", unsafe_allow_html=True)
        st.subheader("Compiler AI")
        st.write("Debug and fix your code with AI assistance.")
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<div class='fadeIn'>", unsafe_allow_html=True)
        st.subheader("Documentation Writer")
        st.write("Generate documentation for your code using AI.")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='fadeIn'>", unsafe_allow_html=True)
        st.subheader("Coding Guru")
        st.write("Generate complex code from scratch using multiple AI models.")
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<div class='fadeIn'>", unsafe_allow_html=True)
        st.subheader("Code Translator")
        st.write("Translate code from one programming language to another using AI.")
        st.markdown("</div>", unsafe_allow_html=True)

def get_llama3_response(prompt):
    chat_completion = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama3-70b-8192",
    )
    return chat_completion.choices[0].message.content

def get_mixtral_response(prompt, llama3_response):
    combined_prompt = f"""You have been provided with a response from LLaMA3 to the latest user query. Your task is to synthesize this response into a single, high-quality response. Ensure your response is well-structured, coherent, and adheres to the highest standards of accuracy and reliability.
The User Query: {prompt}
LLaMA3 Response: {llama3_response}
Don't write Any Explanation just Write the Code no need for Explanation
Your Response: """

    completion = mixtral_client.chat.completions.create(
        model="mistralai/mistral-large",
        messages=[{"role": "user", "content": combined_prompt}],
        temperature=0.5,
        top_p=1,
        max_tokens=1024,
        stream=True
    )
    response = ""
    for chunk in completion:
        if chunk.choices[0].delta.content is not None:
            response += chunk.choices[0].delta.content
    return response

def get_gemini_response(prompt, mixtral_response):
    combined_prompt = f"""You have been provided with a response from Mixtral to the latest user query. Your task is to synthesize this response into a single, high-quality response. Ensure your response is well-structured, coherent, and adheres to the highest standards of accuracy and reliability.
The User Query: {prompt}
Mixtral Response: {mixtral_response}
Don't write Any Explanation just Write the Code no need for Explanation
Your Response: """

    response = gemini_model.generate_content(combined_prompt)
    return response.text

def compiler_ai():
    st.markdown("<h1 style='text-align: center; font-family: Arial, sans-serif;'>Compiler AI</h1>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.header("Paste your code here:")
        code = st.text_area("Enter your code", height=370)

        user_input_needed = st.checkbox("Does your code require input?")
        if user_input_needed:
            input_prompt = "Provide the input for your code:"
            input_text = st.text_area(input_prompt, height=150)
        else:
            input_text = None

        if st.button("Run Code"):
            try:
                with open("user_code.py", "w") as f:
                    f.write(code)
                command = ['python', 'user_code.py']

                if input_text:
                    result = subprocess.run(command, input=input_text, capture_output=True, text=True)
                else:
                    result = subprocess.run(command, capture_output=True, text=True)

                output = result.stdout
                error = result.stderr

                st.session_state.output = output if output else "No output."
                st.session_state.error = error

                if error:
                    chat_completion = groq_client.chat.completions.create(
                        messages=[
                            {"role": "user", "content": f"Explain this error and how to fix it:\n```python\n{error}\n```"}
                        ],
                        model="llama3-70b-8192",
                    )
                    ai_response = chat_completion.choices[0].message.content
                    start_errors = ai_response.find("**Errors in the code**")
                    start_resolution = ai_response.find("**How to resolve errors**")

                    errors_in_code = ai_response[start_errors + len("**Errors in the code**"):start_resolution].strip()
                    how_to_resolve_errors = ai_response[start_resolution + len("**How to resolve errors**"):].strip()

                    st.session_state.user_code = code
                    st.session_state.errors_in_code = errors_in_code
                    st.session_state.how_to_resolve_errors = how_to_resolve_errors
                    st.session_state.code_ran = True

            except Exception as e:
                st.error(f"An error occurred: {e}")

        if "output" in st.session_state:
            st.subheader("Output:")
            st.code(st.session_state.output)
        if "error" in st.session_state and st.session_state.error:
            st.subheader("Error's in the code:")
            st.markdown(f"```\n{st.session_state.error}\n```")

    with col2:
        if "errors_in_code" in st.session_state and "how_to_resolve_errors" in st.session_state:
            st.header("Errors in the code:")
            st.write(st.session_state.errors_in_code)
            st.header("How to resolve errors:")
            st.write(st.session_state.how_to_resolve_errors)

        if st.session_state.get("code_ran"):
            if st.button("Reveal Correct Code"):
                try:
                    if "corrected_code" not in st.session_state:
                        chat_completion = groq_client.chat.completions.create(
                            messages=[
                                {"role": "user", "content": f"The code and error is given to you. Return the corrected code that doesn't have any errors and only code without any explanation. The code and errors are given below:\n```python\n{st.session_state.user_code}\n{st.session_state.error}\n```"}
                            ],
                            model="llama3-70b-8192",
                        )
                        ai_code = chat_completion.choices[0].message.content
                        st.session_state.corrected_code = ai_code

                except Exception as e:
                    st.error(f"An error occurred while fetching the corrected code: {e}")

        if "corrected_code" in st.session_state:
            st.subheader("Corrected Code:")
            st.code(st.session_state.corrected_code)

def coding_guru():
    st.markdown("<h1 style='text-align: center; font-family: Arial, sans-serif;'>Coding Guru</h1>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.header("Paste your Query here:")
        query = st.text_area("I can generate complex codes from scratch:", height=400)
        
        if st.button("Submit"):
            st.success("Your Query is submitted")
            st.balloons()

            language = st.session_state.get("coding_guru_language", "Python")
            prompt = f"Generate a complex {language} code for the following query: {query}"

            llama3_response = get_llama3_response(prompt)
            mixtral_response = get_mixtral_response(prompt, llama3_response)
            gemini_response = get_gemini_response(prompt, mixtral_response)

            with col2:
                st.header("Final Response:")
                st.subheader(f"{language} Code")
                st.code(gemini_response)

def documentation_writer():
    st.markdown("<h1 style='text-align: center; font-family: Arial, sans-serif;'>Documentation Writer</h1>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.header("Paste your code here:")
        code = st.text_area("Enter your code for documentation", height=400)

        if st.button("Document Code"):
            if code:
                try:
                    chat_completion = groq_client.chat.completions.create(
                        messages=[
                            {"role": "user", "content": f"Generate  code with comments so that can explain code and generate documentation for the following code:\n```python\n{code}\n ```"}
                        ],
                        model="llama3-70b-8192",
                    )
                    documentation = chat_completion.choices[0].message.content
                    st.session_state.documentation = documentation

                except Exception as e:
                    st.error(f"An error occurred while generating documentation: {e}")

    with col2:
        if "documentation" in st.session_state:
            st.header("Generated Documentation:")
            st.markdown(st.session_state.documentation, unsafe_allow_html=True)

def code_translator():
    st.markdown("<h1 style='text-align: center; font-family: Arial, sans-serif;'>Code Translator</h1>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.header("Paste your code here:")
        code = st.text_area("Enter the code to be translated", height=400)

        if st.button("Translate Code"):
            if code:
                try:
                    target_language = st.session_state.get("code_translator_language", "Python")
                    chat_completion = groq_client.chat.completions.create(
                        messages=[
                            {"role": "user", "content": f"Translate the following code to {target_language}:\n```python\n{code}\n```"}
                        ],
                        model="llama3-70b-8192",
                    )
                    translated_code = chat_completion.choices[0].message.content
                    st.session_state.translated_code = translated_code

                except Exception as e:
                    st.error(f"An error occurred while translating the code: {e}")

    with col2:
        if "translated_code" in st.session_state:
            st.header("Translated Code:")
            st.code(st.session_state.translated_code)

def main():
    st.sidebar.title("Navigation")
    app_mode = st.sidebar.selectbox("Choose the app mode", ["Home", "Compiler AI", "Coding Guru", "Documentation Writer", "Code Translator"])

    if app_mode == "Coding Guru":
        st.sidebar.header("Coding Guru Settings")
        st.sidebar.selectbox("Select Programming Language", ["Python", "Java", "C", "C++", "R"], key="coding_guru_language")
    elif app_mode == "Code Translator":
        
        st.sidebar.selectbox("Select Target Programming Language", ["C", "C++", "Python", "R", "Java", "Go", "Bash"], key="code_translator_language")

    if app_mode == "Compiler AI":
        compiler_ai()
    elif app_mode == "Coding Guru":
        coding_guru()
    elif app_mode == "Code Translator":
        code_translator()
    elif app_mode == "Home":
        home()
    elif app_mode == "Documentation Writer":
        documentation_writer()

    # Add JavaScript to hide sidebar after 5 seconds of inactivity
    st.markdown("""
    <script>
    const sidebar = window.parent.document.querySelector('.sidebar-content');
    let timer;
    
    function showSidebar() {
        sidebar.style.left = '0';
    }
    
    function hideSidebar() {
        sidebar.style.left = '-20rem';
    }
    
    function resetTimer() {
        clearTimeout(timer);
        showSidebar();
        timer = setTimeout(hideSidebar, 5000);
    }
    
    sidebar.addEventListener('mousemove', resetTimer);
    sidebar.addEventListener('mouseleave', resetTimer);
    
    resetTimer();
    </script>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
