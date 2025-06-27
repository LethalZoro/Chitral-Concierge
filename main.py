import streamlit as st
import openai
import os
from dotenv import load_dotenv
from tavily import TavilyClient # Import the Tavily client

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Chitral Concierge",
    page_icon="🏔️",
    layout="wide",
)

# --- API KEY MANAGEMENT ---
load_dotenv()
openai.api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
tavily_api_key = st.secrets.get("TAVILY_API_KEY") or os.getenv("TAVILY_API_KEY")


# --- UI STYLING ---
st.markdown("""
<style>
    .stTextInput > div > div > input {
        border-radius: 20px;
        padding: 10px 15px;
    }
    .stButton > button {
        border-radius: 20px;
        border: 1px solid #FF4B4B;
        background-color: #FF4B4B;
        color: white;
        padding: 10px 20px;
    }
    .stButton > button:hover {
        background-color: #FF6B6B;
        border: 1px solid #FF6B6B;
    }
    .footer {
        text-align: center;
        margin-top: 2rem;
        color: grey;
    }
</style>
""", unsafe_allow_html=True)


# --- CORE FUNCTIONS (MODIFIED FOR TAVILY) ---

def get_web_context(query: str):
    """
    Performs a targeted, advanced web search using the Tavily API.

    Args:
        query: The user's original question.

    Returns:
        A tuple containing:
        - A structured context string for the AI.
        - A list of source dictionaries for display.
        Returns (None, []) if the search fails or the API key is missing.
    """
    if not tavily_api_key:
        st.warning("Tavily API key not found. Web search is disabled.")
        return None, []

    # 1. Create a more effective search query
    search_query = f"latest information on {query} in Chitral, Pakistan"
    st.session_state.search_query = search_query # Store for display

    try:
        tavily_client = TavilyClient(api_key=tavily_api_key)

        # 2. Perform a more focused and in-depth search
        response = tavily_client.search(
            query=search_query,
            search_depth="advanced", # Use advanced search for higher quality results
            max_results=5,           # Reduced from 15 to 5 for quality over quantity
        )

        # 3. Handle cases with no results
        if not response or not response.get("results"):
            return "No relevant information found from web search.", []

        # 4. Create a structured context for the LLM
        sources = response["results"]
        context_parts = []
        for result in sources:
            # Structure each piece of context clearly
            context_parts.append(f"Source URL: {result['url']}\nContent: {result['content']}")

        # Join with clear separators
        structured_context = "\n\n---\n\n".join(context_parts)

        return structured_context, sources

    except Exception as e:
        st.error(f"An error occurred during web search: {e}")
        return None, []


def get_ai_response_with_context(query, web_context):
    """
    Interacts with OpenAI, providing web context to formulate a better answer.
    (This function does not need to be changed)
    """
    if not openai.api_key:
        return "Error: OpenAI API key is not configured."

    if web_context:
        system_message = (
            "You are a helpful assistant specializing in Chitral, Pakistan. "
            "Use the provided 'Web Context' from a search to give a comprehensive and up-to-date answer to the user's question. "
            "Synthesize the information from the context into your response."
        )
        user_prompt = f"""
        Web Context:
        ---
        {web_context}
        ---
        Question: {query}
        """
    else:
        system_message = (
            "You are a helpful assistant specializing in Chitral, Pakistan. "
            "Answer the user's question based on your general knowledge. "
            "Mention that web search was not available or did not return relevant information."
        )
        user_prompt = query

    try:
        client = openai.OpenAI(api_key=openai.api_key)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.5,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"An OpenAI API error occurred: {e}")
        return None
left_spacer, main_col, right_spacer = st.columns([1, 3, 1])

with main_col:
    st.title("🏔️ Chitral Concierge Service")
    st.markdown("##### Your personal AI guide to the culture, sights, and adventures of Chitral")
    st.markdown("---")

    # Wrap the inputs in a form
    with st.form(key='query_form'):
        user_input = st.text_input(
            "Ask me anything about Chitral...",
            label_visibility="collapsed",
            key="main_input",
            placeholder="e.g., What are the best places to visit in the Kalash Valleys?"
        )

        # The submit button for the form
        submitted = st.form_submit_button("Get Info", use_container_width=True, type="primary")

    # The logic now runs only when the form is submitted (button click or Enter key)
    if submitted:
        if user_input:
            # The spinner now shows the *actual* search query for transparency
            with st.spinner(f"Searching for the latest information on '{user_input}'..."):
                web_context, sources = get_web_context(user_input)

            with st.spinner("Scaling the mountains of knowledge and exploring the valleys of the web for you..."):
                final_response = get_ai_response_with_context(user_input, web_context)

            st.subheader("💡 Concierge Response:")
            if final_response:
                st.markdown(final_response)

                # Display the sources in a clean, expandable section
                if sources:
                    with st.expander("📚 View Sources Used"):
                        for i, source in enumerate(sources):
                            st.markdown(f"**{i+1}. {source['title']}**\n"
                                        f"   [Read more]({source['url']})")
            else:
                st.error("Sorry, I encountered an issue and was unable to process your request.")
        else:
            st.warning("Please ask a question first.")

    st.markdown('<div class="footer">Built with ❤️ using Streamlit, Tavily, and OpenAI</div>', unsafe_allow_html=True)