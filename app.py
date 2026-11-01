import os
import streamlit as st
from pypdf import PdfReader
from dotenv import load_dotenv
from google import genai
import database

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

st.set_page_config(
    page_title="AI PDF Chatbot",
    page_icon="📚"
)

database.create_database()

st.title("📚 AI PDF Question Answering Chatbot")

# Initialize session state
if "chat_id" not in st.session_state:
    st.session_state.chat_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""

if "pdf_name" not in st.session_state:
    st.session_state.pdf_name = None

if "loaded_saved_chat" not in st.session_state:
    st.session_state.loaded_saved_chat = False


# Sidebar - Chat History
st.sidebar.title("Chat History")

if st.sidebar.button("➕ New Chat"):
    st.session_state.chat_id = None
    st.session_state.messages = []
    st.session_state.pdf_text = ""
    st.session_state.pdf_name = None
    st.session_state.loaded_saved_chat = False
    st.rerun()


for chat in database.get_all_chats():
    chat_id, title, pdf_name, pdf_text, created_at = chat

    if st.sidebar.button(title, key=f"chat_{chat_id}"):
        st.session_state.chat_id = chat_id
        st.session_state.pdf_text = pdf_text or ""
        st.session_state.pdf_name = pdf_name

        st.session_state.messages = [
            {"role": role, "content": content}
            for role, content in database.get_chat_messages(chat_id)
        ]

        st.session_state.loaded_saved_chat = True
        st.rerun()
    st.sidebar.caption(f"📄 {pdf_name or 'Unknown PDF'}")

if st.sidebar.button("🗑️ Delete Current Chat"):
    if st.session_state.chat_id is not None:
        database.delete_chat(st.session_state.chat_id)

    st.session_state.chat_id = None
    st.session_state.messages = []
    st.session_state.pdf_text = ""
    st.session_state.pdf_name = None
    st.session_state.loaded_saved_chat = False
    st.rerun()


# PDF Upload
st.write("Upload a PDF and ask questions about its content.")

uploaded_file = st.file_uploader(
    "Upload your PDF file",
    type=["pdf"]
)

# Load a newly uploaded PDF
if uploaded_file is not None and not st.session_state.loaded_saved_chat:

    if uploaded_file.name != st.session_state.pdf_name:
       
      try:
            pdf_reader = PdfReader(uploaded_file)

            if pdf_reader.is_encrypted:
                raise ValueError("This PDF is password protected.")

            extracted_text = ""

            for page in pdf_reader.pages:
                text = page.extract_text()

                if text:
                    extracted_text += text + "\n"

            if not extracted_text.strip():
                st.session_state.pdf_text = ""
                st.session_state.pdf_name = None
                st.error("No readable text found in this PDF.")
                st.stop()

            st.session_state.pdf_text = extracted_text
            st.session_state.pdf_name = uploaded_file.name

            if st.session_state.chat_id is not None:
                st.session_state.chat_id = None
                st.session_state.messages = []

      except Exception as e:
            st.session_state.pdf_text = ""
            st.session_state.pdf_name = None
            st.error(f"Unable to read this PDF: {e}")
            st.stop()

    st.success("PDF uploaded successfully!")
    st.write("PDF:", st.session_state.pdf_name)

    if st.session_state.pdf_text.strip():
        st.success("PDF text extracted successfully!")
        # A new PDF starts a new chat
        if st.session_state.chat_id is not None:
            st.session_state.chat_id = None
            st.session_state.messages = []

    st.success("PDF uploaded successfully!")
    st.write("PDF:", st.session_state.pdf_name)

    if st.session_state.pdf_text.strip():
        st.success("PDF text extracted successfully!")
    else:
        st.warning("No readable text found in this PDF.")


# Show selected PDF
if st.session_state.pdf_text.strip():

    st.info("Current PDF: " + str(st.session_state.pdf_name))

    # Display previous messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Ask questions
    question = st.chat_input("Ask a question about your PDF:")

    if question:

        if st.session_state.chat_id is None:
            st.session_state.chat_id = database.create_chat(
                question[:40],
                st.session_state.pdf_name,
                st.session_state.pdf_text
            )

        st.session_state.messages.append({
            "role": "user",
            "content": question
        })

        database.save_message(
            st.session_state.chat_id,
            "user",
            question
        )

        with st.chat_message("user"):
            st.markdown(question)

        if not api_key:
            st.error("Gemini API key not found. Check your .env file.")
        else:
            try:
                client = genai.Client(api_key=api_key)

                conversation = ""

                for message in st.session_state.messages[-10:]:
                    conversation += (
                        message["role"] + ": "
                        + message["content"] + "\n"
                    )

                prompt = f"""
                Answer using only the PDF content.
                If the answer is not in the PDF, say so.
                Use conversation history to understand follow-up questions.

                PDF CONTENT:
                {st.session_state.pdf_text[:30000]}

                CONVERSATION HISTORY:
                {conversation}
                """

                with st.chat_message("assistant"):
                    with st.spinner("AI is thinking..."):

                        response = client.models.generate_content(
                            model="gemini-3.8-flash",
                            contents=prompt
                        )

                    answer = response.text
                    st.markdown(answer)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer
                })

                database.save_message(
                    st.session_state.chat_id,
                    "assistant",
                    answer
                )

            except Exception as e:
                st.error(f"Something went wrong: {e}")

else:
    st.info("Please upload a PDF or select an old chat from the sidebar.")

# Reset saved-chat flag after restoring its PDF
st.session_state.loaded_saved_chat = False