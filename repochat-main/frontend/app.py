"""
minimal streamlit chat UI for phase1

run with:  streamlit run frontend/app.py
requires the FastAPI backend to already be running (see run.py / README.md).
"""

import os

import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="RepoChat", layout="wide")

if "messages" not in st.session_state:
    st.session_state.messages = []  # list of {"role": "user"/"assistant", "content": str, "citations": list}
if "indexed_repo" not in st.session_state:
    st.session_state.indexed_repo = None


def call_api(method: str, path: str, **kwargs):
    try:
        response = requests.request(method, f"{API_BASE_URL}{path}", timeout=120, **kwargs)
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.ConnectionError:
        return None, f"Could not reach the backend at {API_BASE_URL}. Is it running? (see run.py)"
    except requests.exceptions.HTTPError as exc:
        detail = exc.response.json().get("detail", str(exc)) if exc.response is not None else str(exc)
        return None, detail
    except Exception as exc:  # noqa: BLE001 - surface any unexpected error to the user
        return None, str(exc)


# sidebar
with st.sidebar:
    st.header("Repository")

    repo_path = st.text_input("Local repository path", placeholder="/path/to/your/repo")
    repo_name = st.text_input("Repository name (optional)")

    if st.button("Index repository", type="primary", disabled=not repo_path):
        with st.spinner("Scanning, chunking, and embedding files... this can take a while on the first run."):
            data, error = call_api(
                "POST", "/index", json={"repo_path": repo_path, "repo_name": repo_name or None}
            )
        if error:
            st.error(error)
        else:
            st.session_state.indexed_repo = data
            st.success(f"Indexed {data['files_indexed']} files into {data['chunks_created']} chunks.")

    st.divider()
    st.subheader("Index status")

    status_data, status_error = call_api("GET", "/status")
    if status_error:
        st.warning(status_error)
    elif status_data:
        st.metric("Total chunks in vector DB", status_data["total_chunks_indexed"])
        for warning in status_data.get("config_warnings", []):
            st.warning(warning)

    if st.session_state.indexed_repo:
        info = st.session_state.indexed_repo
        st.write(f"**Last indexed:** {info['repo_name']}")
        st.write(f"**Files indexed:** {info['files_indexed']}")
        st.write(f"**Chunks:** {info['chunks_created']}")
        st.write("**Languages:**")
        for lang in info["languages"]:
            st.write(f"- {lang}")

    st.divider()
    st.caption(
        "questions and retrieved code snippets are sent to the configured "
        "LLM provider (Gemini) to generate answers."
    )

# main
st.title("RepoChat")
st.caption("Ask questions about your codebase. Answers are grounded in the actual repository.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("citations"):
            with st.expander(f"📎 {len(message['citations'])} citation(s)"):
                for citation in message["citations"]:
                    symbol_part = f" — `{citation['symbol']}`" if citation.get("symbol") else ""
                    st.markdown(
                        f"`{citation['file_path']}:{citation['start_line']}-{citation['end_line']}`{symbol_part}"
                    )

question = st.chat_input("e.g. Where is authentication implemented?")
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Retrieving relevant code and asking Gemini..."):
            repo_filter = st.session_state.indexed_repo["repo_name"] if st.session_state.indexed_repo else None
            data, error = call_api(
                "POST", "/ask", json={"question": question, "repo_name": repo_filter}
            )
        if error:
            st.error(error)
            st.session_state.messages.append({"role": "assistant", "content": f"Error: {error}"})
        else:
            st.markdown(data["answer"])
            citations = data.get("citations", [])
            if citations:
                with st.expander(f"📎 {len(citations)} citation(s)"):
                    for citation in citations:
                        symbol_part = f" — `{citation['symbol']}`" if citation.get("symbol") else ""
                        st.markdown(
                            f"`{citation['file_path']}:{citation['start_line']}-{citation['end_line']}`{symbol_part}"
                        )
            st.session_state.messages.append(
                {"role": "assistant", "content": data["answer"], "citations": citations}
            )
