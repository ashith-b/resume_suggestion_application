import os
import streamlit as st
from streamlit_feedback import streamlit_feedback
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_openai import ChatOpenAI
from constants import OPENAI_API_KEY, OPENAI_MODEL_NAME, TEMPLATE_CONTENT, comparison_prompt, resume_analysis_prompt, \
    job_description_analysis_prompt, gap_analysis_prompt, actionable_steps_prompt, experience_enhancement_prompt, \
    additional_qualifications_prompt, resume_tailoring_prompt, relevant_skills_highlight_prompt, \
    resume_formatting_prompt, resume_length_prompt
from directory_reader import DirectoryReader

st.set_page_config(page_title="Resume Reviewer")
os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY
resume_content = None
job_description_content = None


with st.sidebar:
    st.title('Resume Reviewer')
    st.write("Upload your resume and JD for my recommendations.")
    # Resume and JD file uploader in the sidebar
    resume_file = st.file_uploader("Upload your resume (pdf file only)", type=["pdf"])
    jd_file = st.file_uploader("Upload your JD (txt file only)", type=["txt"])


if resume_file is not None and jd_file is not None:
    directory_reader = DirectoryReader("", "")
    resume_content = directory_reader.extract_text_from_pdf(resume_file)
    if jd_file.type == 'text/plain':
        from io import StringIO
        stringio = StringIO(jd_file.getvalue().decode('utf-8'))
        read_data = stringio.read()
        job_description_content = read_data
else:
    resume_content = None
    job_description_content = None

SYSTEM_PROMPT = "\n\n" + TEMPLATE_CONTENT + "<RESUME STARTS HERE> {}. <RESUME ENDS HERE> with the job description: <JOB DESCRIPTION STARTS HERE> {}.<JOB DESCRIPTION ENDS HERE>\n\nBe crisp and clear in response.DO NOT provide the resume and job description in the response\n\n".format(resume_content, job_description_content)
llm = ChatOpenAI(temperature=0.0, model=OPENAI_MODEL_NAME)


# Store LLM generated responses
if "messages" not in st.session_state.keys():
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]

# Display or clear chat messages
for message in st.session_state.messages:
    if message["role"] != "feedback":
        with st.chat_message(message["role"]):
            st.write(message["content"])


def clear_chat_history():
    global resume_chain
    st.session_state.messages = [{"role": "assistant", "content": "How may I help you today?"}]
    resume_chain = ConversationChain(
        llm=llm,
        prompt=prompt_template,
        memory=memory,
        verbose=False
    )


def generate_report():
    user_message = {"role": "user", "content": "Generate a Report!"}
    st.session_state.messages.append(user_message)
    if resume_file is not None and jd_file is not None:
        with st.chat_message("assistant"):
            with st.spinner("Just a moment..."):

                comparison_analysis = generate_response(comparison_prompt.format(resume_content, job_description_content))
                resume_analysis = generate_response(resume_analysis_prompt.format(resume_content))
                job_description_analysis = generate_response(
                    job_description_analysis_prompt.format(job_description_content))
                gap_analysis = generate_response(gap_analysis_prompt.format(resume_content,
                                                                            job_description_content))
                actionable_steps_analysis = generate_response(actionable_steps_prompt.format(
                    resume_content, job_description_content))
                experience_enhancement_analysis = generate_response(
                    experience_enhancement_prompt.format(resume_content, job_description_content))
                additional_qualifications_analysis = generate_response(
                    additional_qualifications_prompt.format(resume_content, job_description_content))
                resume_tailoring_analysis = generate_response(
                    resume_tailoring_prompt.format(resume_content, job_description_content))
                relevant_skills_highlight_analysis = generate_response(
                    relevant_skills_highlight_prompt.format(resume_content, job_description_content))
                resume_formatting_analysis = generate_response(
                    resume_formatting_prompt.format(resume_content, job_description_content))
                resume_length_analysis = generate_response(
                    resume_length_prompt.format(resume_content, job_description_content))

                # Compile the report
                report = f"Comparison Analysis:\n{comparison_analysis}\n\n" \
                         f"Resume Analysis:\n{resume_analysis}\n\n" \
                         f"Job Description Analysis:\n{job_description_analysis}\n" \
                         f"\nGap Analysis:\n{gap_analysis} \n\n" \
                         f"Actionable Steps:\n{actionable_steps_analysis}\n\n" \
                         f"Experience Enhancement:\n{experience_enhancement_analysis}\n\n" \
                         f"Additional Qualifications:\n{additional_qualifications_analysis}\n\n" \
                         f"Resume Tailoring:\n{resume_tailoring_analysis}\n\n" \
                         f"Relevant Skills Highlight:\n{relevant_skills_highlight_analysis}\n\n" \
                         f"Resume Formatting:\n{resume_formatting_analysis}\n\n" \
                         f"Resume Length:\n{resume_length_analysis} "

        report_message = {"role": "assistant", "content": report}
        st.session_state.messages.append(report_message)
    else:
        st.error("Please upload a resume and enter a job description!")


system_message = SystemMessage(content=TEMPLATE_CONTENT)
human_message = HumanMessagePromptTemplate.from_template("{history} User:{input} Assistant:")
prompt_template = ChatPromptTemplate(messages=[system_message, human_message], validate_template=True)
memory = ConversationBufferWindowMemory(k=2)

if llm is not None:
    resume_chain = ConversationChain(
        llm=llm,
        prompt=prompt_template,
        memory=memory,
        verbose=False
    )
else:
    resume_chain = None


def generate_response(prompt_input):
    output = resume_chain.predict(input=prompt_input)
    return output


st.sidebar.button('Clear Chat History', on_click=clear_chat_history)
st.sidebar.button('Generate Report', on_click=generate_report)


def get_feedback():
    st.session_state.messages.append({"role": "feedback", "content": st.session_state.fbk})


# User-provided prompt
if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.write(prompt)


def get_llm_response():
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_response(prompt + SYSTEM_PROMPT)
            placeholder = st.empty()
            full_response = ''
            for item in response:
                full_response += item
                placeholder.markdown(full_response)
            placeholder.markdown(full_response)
    message = {"role": "assistant", "content": full_response}
    st.session_state.messages.append(message)
    with st.form("form"):
        streamlit_feedback(feedback_type="thumbs", optional_text_label="[Optional] Please provide an explanation", key="fbk")
        st.form_submit_button('Save feedback', on_click=get_feedback)


# Generate a new response if last message is not from assistant
if st.session_state.messages[-1]["role"] not in ["assistant", "feedback"]:
    get_llm_response()

if st.session_state.messages[-1]["role"] in ["feedback"]:
    try:
        feedback_response = st.session_state.messages[-1]["content"]
        score_mappings = {
            "thumbs": {"👍": 1, "👎": 0},
        }
        score = score_mappings[feedback_response["type"]][feedback_response["score"]]
        if score == 0:
            feedback = st.session_state.messages[-1]["content"]['text']
            prompt = "Please respond according to feedback '{0}' on the previous response on \n".format(feedback) \
                     + st.session_state.messages[-3]["content"]
            get_llm_response()
    except:
        pass
