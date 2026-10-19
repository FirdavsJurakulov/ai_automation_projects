"""Streamlit chat UI.  Run: streamlit run app.py"""
import logging

import streamlit as st
from rag import RagError, answer, build_index

log = logging.getLogger(__name__)
UNEXPECTED = "Произошла непредвиденная ошибка. Подробности — в логах приложения."

st.set_page_config(page_title="Agency Knowledge Assistant", page_icon="🤖")
st.title("🤖 Agency Knowledge Assistant")
st.caption("RAG demo: Gemini embeddings + ChromaDB + Gemini · отвечает только по документам агентства, со ссылками")

with st.sidebar:
    st.header("Документы")
    uploads = st.file_uploader("Добавить .md / .txt / .pdf", accept_multiple_files=True,
                               type=["md", "txt", "pdf"])
    if st.button("Переиндексировать"):
        with st.spinner("Индексирую..."):
            try:
                for f in uploads or []:
                    open(f"docs/{f.name}", "wb").write(f.getbuffer())
                st.success(f"Готово: {build_index('docs')} фрагментов")
            except RagError as e:
                st.error(str(e))
            except Exception:
                log.exception("Indexing failed")
                st.error(UNEXPECTED)
    st.markdown("**Попробуйте спросить:**\n- Сколько стоит пакет «Рост»?\n- Какие цвета у Chaikhana Lounge?\n"
                "- Можно ли рекламировать пиво?\n- Qancha oldindan to'lov kerak?\n- Сколько стоит SEO?  *(нет в документах)*")

if "history" not in st.session_state:
    st.session_state.history = []


def render(m: dict) -> None:
    with st.chat_message(m["role"]):
        if m.get("error"):
            st.error(m["error"])
            return
        st.markdown(m["content"])
        if m.get("sources"):
            with st.expander("Источники (retrieved chunks)"):
                for h in m["sources"]:
                    st.markdown(f"**{h['source']}** · similarity {h['score']}\n\n> {h['text'][:300]}...")


for m in st.session_state.history:
    render(m)

if q := st.chat_input("Спросите что-нибудь о клиентах, ценах, процессах..."):
    user_msg = {"role": "user", "content": q}
    render(user_msg)
    # only successful exchanges go to the model as conversation memory
    context = [m for m in st.session_state.history if not m.get("failed")]
    with st.spinner("Ищу в документах..."):
        try:
            res = answer(q, context)
            reply = {"role": "assistant", "content": res["answer"], "sources": res["sources"]}
        except RagError as e:
            reply = {"role": "assistant", "content": "", "error": str(e)}
        except Exception:
            log.exception("Answer failed")
            reply = {"role": "assistant", "content": "", "error": UNEXPECTED}
    if reply.get("error"):
        user_msg["failed"] = reply["failed"] = True
    render(reply)
    st.session_state.history += [user_msg, reply]
