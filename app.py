import time
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

# Modelo principal + modelo de reserva (podes mudar nos secrets sem mexer no código)
MODELOS = [
    st.secrets.get("GEMINI_MODEL", "gemini-3.8-flash"),
    st.secrets.get("GEMINI_MODEL_RESERVA", "gemini-2.5-flash-lite"),
]
TEMPORARIOS = (429, 500, 503, 504)

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


def chamar_gemini(corpo, chave):
    """Tenta cada modelo até 3 vezes (espera 1s, 2s) se o erro for temporário."""
    ultimo_erro = None
    for modelo in MODELOS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"
        for t in range(3):
            try:
                r = requests.post(
                    url,
                    headers={"x-goog-api-key": chave},
                    json=corpo,
                    timeout=30,
                )
                if r.ok:
                    print(f"Resposta obtida com o modelo {modelo}")
                    return r.json()

                ultimo_erro = RuntimeError(
                    f"Gemini {modelo} devolveu {r.status_code}: {r.text[:200]}"
                )
                print("Aviso:", ultimo_erro)
                if r.status_code not in TEMPORARIOS:
                    break  # erro definitivo: passa ao modelo seguinte
            except requests.RequestException as e:
                ultimo_erro = e  # timeout ou rede
                print("Aviso:", e)
            time.sleep(2**t)  # 1s, 2s, 4s
    raise ultimo_erro


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

    dados = chamar_gemini(
        {
            "systemInstruction": {"parts": [{"text": SISTEMA}]},
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": 2000,
                "thinkingConfig": {"thinkingBudget": 0},
            },
        },
        chave,
    )

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
            st.write(ERRO)

st.link_button(
    "Falar no WhatsApp",
    f"https://wa.me/{WHATSAPP}?text={quote(MENSAGEM_WHATSAPP)}",
)