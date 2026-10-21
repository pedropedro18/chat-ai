import requests
import streamlit as st
from urllib.parse import quote

WHATSAPP = "244923030010"
MENSAGEM_WHATSAPP = "Olá Teacher Pedro, quero saber mais sobre as aulas de inglês."

SISTEMA = """És o assistente virtual do "Teacher Pedro", professor de inglês em Angola.
Respondes em português, de forma curta, simpática e clara.

Cursos de inglês (níveis CEFR), preços a partir de:
- A1 Iniciante: 8 semanas, Kz 15.000/mês
- A2 Elementar: 8 semanas, Kz 15.000/mês
- B1 Intermédio (o mais procurado): 10 semanas, Kz 18.000/mês
- B2 Intermédio Alto: 10 semanas, Kz 18.000/mês
- C1 Avançado: 12 semanas, preço no WhatsApp
- C2 Proficiente: 12 semanas, preço no WhatsApp

Também há cursos de Excel e programação/web.
Se não souberes algo, não inventes: sugere falar com o professor no WhatsApp.
Responde sempre em no máximo 4 frases curtas ou uma lista breve."""

# Podes definir GEMINI_MODEL nos secrets para mudar de modelo sem mexer no código
MODELO = st.secrets.get("GEMINI_MODEL", "gemini-2.5-flash")
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODELO}:generateContent"

ERRO = "Não consegui responder agora. Fala diretamente com o professor no WhatsApp."

st.set_page_config(page_title="Teacher Pedro")
st.title("Teacher Pedro")

if "msgs" not in st.session_state:
    st.session_state.msgs = [
        {
            "role": "assistant",
            "content": "Olá! Em que posso ajudar? Pergunta sobre cursos, níveis, preços ou inscrições.",
        }
    ]


def perguntar(historico):
    chave = st.secrets["GEMINI_API_KEY"]

    recentes = historico[1:][-10:]
    # a conversa tem de começar com uma mensagem do utilizador
    while recentes and recentes[0]["role"] != "user":
        recentes = recentes[1:]

    contents = [
        {
            "role": "user" if m["role"] == "user" else "model",
            "parts": [{"text": m["content"]}],
        }
        for m in recentes
    ]

    r = requests.post(
        URL,
        headers={"x-goog-api-key": chave},
        json={
            "systemInstruction": {"parts": [{"text": SISTEMA}]},
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": 2000,
                "thinkingConfig": {"thinkingBudget": 0},
            },
        },
        timeout=30,
    )

    if not r.ok:
        raise RuntimeError(f"Gemini devolveu {r.status_code}: {r.text[:300]}")

    dados = r.json()
    partes = dados["candidates"][0]["content"]["parts"]
    texto = "".join(p.get("text", "") for p in partes).strip()
    if not texto:
        raise RuntimeError("Resposta vazia do Gemini")
    return texto


for m in st.session_state.msgs:
    with st.chat_message(m["role"]):
        st.write(m["content"])

pergunta = st.chat_input("Escreve a tua pergunta...", max_chars=300)

if pergunta:
    st.session_state.msgs.append({"role": "user", "content": pergunta})
    with st.chat_message("user"):
        st.write(pergunta)

    with st.chat_message("assistant"):
        try:
            with st.spinner("A escrever..."):
                resposta = perguntar(st.session_state.msgs)
            st.session_state.msgs.append({"role": "assistant", "content": resposta})
            st.write(resposta)
        except Exception as e:
            print(e)  # o erro técnico fica só nos logs
            st.session_state.msgs.pop()  # tira a pergunta falhada do histórico
            st.write(ERRO)

st.link_button(
    "Falar no WhatsApp",
    f"https://wa.me/{WHATSAPP}?text={quote(MENSAGEM_WHATSAPP)}",
)