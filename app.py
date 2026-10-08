import streamlit as st
import imaplib
import email
from email.header import decode_header
from bs4 import BeautifulSoup

st.set_page_config(
    page_title="Leitor de E-mails",
    page_icon="📧"
)

st.title("📧 Leitor de E-mails")

quantidade = st.number_input(
    "Quantidade de e-mails",
    min_value=1,
    max_value=100,
    value=1
)

if st.button("📨 Buscar e-mails"):

    try:
        # ==============================
        # CONEXÃO COM GMAIL
        # ==============================

        mail = imaplib.IMAP4_SSL("imap.gmail.com")

        mail.login(
           "luizeduardo071205@gmail.com",
            "ojai fdiy pblu cfhg"
        )

        # Seleciona SOMENTE a Caixa de entrada
        status, _ = mail.select("INBOX", readonly=True)

        if status != "OK":
            st.error("Não foi possível acessar a Caixa de entrada.")
            mail.logout()
            st.stop()

        # ==============================
        # BUSCA DO GMAIL
        # ==============================

        # Usa a busca própria do Gmail:
        # in:inbox = somente mensagens atualmente na caixa de entrada

        status, dados = mail.uid(
            "search",
            None,
            "X-GM-RAW",
            "in:inbox"
        )

        if status != "OK":
            st.error("Erro ao buscar os e-mails.")
            mail.logout()
            st.stop()

        ids = dados[0].split()

        st.write(f"📊 E-mails encontrados atualmente na Caixa de entrada: {len(ids)}")

        if not ids:
            st.info("📭 Nenhum e-mail encontrado na Caixa de entrada.")
            mail.logout()
            st.stop()

        # Pega somente os últimos N
        ids = ids[-int(quantidade):]

        # Mais recente primeiro
        ids = list(reversed(ids))

        # ==============================
        # LER E-MAILS
        # ==============================

        for id_email in ids:

            status, dados_email = mail.uid(
                "fetch",
                id_email,
                "(RFC822)"
            )

            if status != "OK":
                continue

            mensagem_bruta = None

            for parte in dados_email:
                if isinstance(parte, tuple):
                    mensagem_bruta = parte[1]
                    break

            if not mensagem_bruta:
                continue

            mensagem = email.message_from_bytes(mensagem_bruta)

            # ==============================
            # REMETENTE
            # ==============================

            remetente = mensagem.get("From", "")

            partes_remetente = decode_header(remetente)

            remetente_decodificado = ""

            for parte, encoding in partes_remetente:

                if isinstance(parte, bytes):

                    if encoding:
                        try:
                            remetente_decodificado += parte.decode(
                                encoding,
                                errors="replace"
                            )
                        except:
                            remetente_decodificado += parte.decode(
                                "utf-8",
                                errors="replace"
                            )
                    else:
                        remetente_decodificado += parte.decode(
                            "utf-8",
                            errors="replace"
                        )

                else:
                    remetente_decodificado += parte

            # ==============================
            # ASSUNTO
            # ==============================

            assunto = mensagem.get("Subject", "")

            partes_assunto = decode_header(assunto)

            assunto_decodificado = ""

            for parte, encoding in partes_assunto:

                if isinstance(parte, bytes):

                    if encoding:
                        try:
                            assunto_decodificado += parte.decode(
                                encoding,
                                errors="replace"
                            )
                        except:
                            assunto_decodificado += parte.decode(
                                "utf-8",
                                errors="replace"
                            )
                    else:
                        assunto_decodificado += parte.decode(
                            "utf-8",
                            errors="replace"
                        )

                else:
                    assunto_decodificado += parte

            # ==============================
            # DATA
            # ==============================

            data = mensagem.get("Date", "")

            # ==============================
            # CORPO
            # ==============================

            texto = ""
            html = ""

            if mensagem.is_multipart():

                for parte in mensagem.walk():

                    tipo = parte.get_content_type()
                    content_disposition = str(
                        parte.get("Content-Disposition", "")
                    )

                    # Ignora anexos
                    if "attachment" in content_disposition.lower():
                        continue

                    try:
                        payload = parte.get_payload(
                            decode=True
                        )

                        if not payload:
                            continue

                        charset = parte.get_content_charset()

                        if not charset:
                            charset = "utf-8"

                        conteudo = payload.decode(
                            charset,
                            errors="replace"
                        )

                    except:
                        continue

                    if tipo == "text/plain":
                        texto += conteudo

                    elif tipo == "text/html":
                        html += conteudo

            else:

                try:
                    payload = mensagem.get_payload(
                        decode=True
                    )

                    if payload:

                        charset = mensagem.get_content_charset()

                        if not charset:
                            charset = "utf-8"

                        conteudo = payload.decode(
                            charset,
                            errors="replace"
                        )

                        if mensagem.get_content_type() == "text/html":
                            html = conteudo
                        else:
                            texto = conteudo

                except:
                    pass

            # ==============================
            # CONVERTE HTML PARA TEXTO
            # ==============================

            if html:

                soup = BeautifulSoup(
                    html,
                    "html.parser"
                )

                corpo = soup.get_text(
                    "\n",
                    strip=True
                )

            else:
                corpo = texto

            # ==============================
            # MOSTRAR
            # ==============================

            with st.expander(
                f"📧 {assunto_decodificado}"
            ):

                st.write(
                    f"**De:** {remetente_decodificado}"
                )

                st.write(
                    f"**Data:** {data}"
                )

                st.divider()

                st.text(corpo)

        mail.logout()

    except imaplib.IMAP4.error as erro:

        st.error(
            f"Erro de autenticação/conexão com Gmail: {erro}"
        )

    except Exception as erro:

        st.error(
            f"Erro: {erro}"
        )