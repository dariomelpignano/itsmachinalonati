import streamlit as st
import anthropic
import time
import random
import os
import datetime

# Must be the first Streamlit command
st.set_page_config(page_title="Customer Service Training")

# Hide Streamlit's default buttons but keep the menu
st.markdown("""
<style>
button[kind="secondary"] {display: none;}
.stDeployButton {display: none;}
.stStopButton {display: none;}
footer {visibility: hidden;}
[data-testid="stToolbar"] {display: none;}
button[data-testid="baseButton-secondary"] {display: none;}

@keyframes ellipsis {
    0% { content: ""; }
    25% { content: "."; }
    50% { content: ".."; }
    75% { content: "..."; }
}

.typing-animation::after {
    content: "";
    display: inline-block;
    animation: ellipsis 2s steps(1) infinite;
}
</style>
""", unsafe_allow_html=True)

# --- Funzioni ---
def calcola_punteggio_e_raccomandazioni(punteggi):
    """Calcola il punteggio medio e fornisce raccomandazioni basate sul punteggio."""
    punteggio_medio = sum(punteggi) / len(punteggi)

    if 10 <= punteggio_medio <= 30:
        livello = "Da colmare"
        raccomandazioni = """
        **Raccomandazioni:**
        - **Comunicazione:** È necessario migliorare la grammatica, l'ortografia e la chiarezza delle risposte. Concentrati su un registro linguistico più appropriato e professionale.
        - **Capacità commerciale:** Approfondisci la conoscenza dei prodotti e delle offerte. Cerca di identificare meglio le esigenze del cliente e di proporre soluzioni pertinenti.
        - **Caring:** Fai più attenzione ai dati sensibili del cliente e assicurati di proteggerli adeguatamente.
        - **Fidelizzazione:** Lavora sull'empatia e sull'ascolto attivo per costruire un rapporto di fiducia con il cliente.
        - **Efficienza:** Cerca di ridurre i tempi di risposta e di gestire le conversazioni in modo più rapido e produttivo.
        """
    elif 31 <= punteggio_medio <= 60:
        livello = "Da perfezionare"
        raccomandazioni = """
        **Raccomandazioni:**
        - **Comunicazione:** Continua a migliorare la precisione e l'organizzazione delle risposte. Assicurati di essere sempre sintetico ed esaustivo.
        - **Capacità commerciale:** Esercitati a riconoscere le opportunità di cross-selling e upselling anche quando il cliente non le esplicita.
        - **Caring:** Presta maggiore attenzione alle richieste del cliente e cerca di risolvere i problemi in modo più efficace.
        - **Fidelizzazione:** Cerca di creare una connessione più forte con il cliente, dimostrando interesse e comprensione.
        - **Efficienza:** Continua a migliorare la velocità di gestione delle conversazioni, ottimizzando i tempi di risposta.
        """
    elif punteggio_medio > 60:
        livello = "Adeguato"
        raccomandazioni = ""
    else:
        livello = "Da colmare completamente"
        raccomandazioni = """
        **Raccomandazioni:**
        - **Comunicazione:** È necessario un percorso formativo approfondito su grammatica, ortografia, sintassi e registro linguistico.
        - **Capacità commerciale:** Necessità di formazione completa sui prodotti, le offerte, le tecniche di vendita e di analisi del cliente.
        - **Caring:** Formazione obbligatoria sulla privacy e sulla gestione dei dati sensibili. Esercitarsi a risolvere i problemi in modo efficace e tempestivo.
        - **Fidelizzazione:** Partecipare a corsi di comunicazione interpersonale, ascolto attivo ed empatia.
        - **Efficienza:** Seguire un training specifico sulla gestione del tempo e sull'ottimizzazione dei processi di assistenza clienti.
        """

    return punteggio_medio, livello, raccomandazioni

def genera_cliente():
    """Genera un profilo cliente casuale con caratteristiche diverse."""
    personalita = random.choice(["Calmo", "Nervoso", "Esigente", "Gentile", "Confuso"])
    umore = random.choice(["Positivo", "Negativo", "Neutrale"])
    stile_scrittura = random.choice(["Corretto", "Sgrammaticato", "Confuso"])
    tipo_richiesta = random.choice(["Assistenza tecnica", "Assistenza amministrativa", "Informazioni commerciali", "Acquisto"])
    conoscenza_problema = random.choice(["Specifica", "Confusa"])
    disponibilita_dati = random.choice(["Completa", "Incompleta"])

    return personalita, umore, stile_scrittura, tipo_richiesta, conoscenza_problema, disponibilita_dati

# --- Inizializzazione Session State ---
if 'start_time' not in st.session_state:
    st.session_state.start_time = time.time()
if 'interazioni' not in st.session_state:
    st.session_state.interazioni = 0
if 'punteggi' not in st.session_state:
    st.session_state.punteggi = {"Comunicazione": 0, "Capacità commerciale": 0, "Caring": 0, "Fidelizzazione": 0, "Efficienza": 0}
if 'conversazione_finita' not in st.session_state:
    st.session_state.conversazione_finita = False
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

# Add new session state variables
if 'pending_operator_message' not in st.session_state:
    st.session_state.pending_operator_message = None
if 'input_key' not in st.session_state:
    st.session_state.input_key = 0

# Inizializza 'cliente' e 'messaggio_cliente' SOLO SE non esistono già
if 'cliente' not in st.session_state:
    st.session_state.cliente = genera_cliente()

    # Genera il messaggio iniziale del cliente
    saluto = "Buongiorno" if time.localtime().tm_hour < 12 else "Buonasera"
    messaggio_cliente = f"{saluto}, sono Giorgio e ho un problema che spero possa aiutarmi a risolvere."
    # Ora è sicuro accedere agli elementi di st.session_state.cliente
    if st.session_state.cliente[3] == "Acquisto":
        messaggio_cliente = f"{saluto}, sono Giorgio e sono interessato ad un vostro prodotto."
    elif st.session_state.cliente[3] == "Informazioni commerciali":
        messaggio_cliente = f"{saluto}, sono Giorgio e vorrei avere maggiori informazioni sui vostri prodotti e servizi."
    elif st.session_state.cliente[3] == "Assistenza amministrativa":
        messaggio_cliente = f"{saluto}, sono Giorgio e ho un problema amministrativo da risolvere."
    if st.session_state.cliente[2] == "Sgrammaticato":
        messaggio_cliente = messaggio_cliente.replace("sono", "ze so")
        messaggio_cliente = messaggio_cliente.replace("un", "n'")
    elif st.session_state.cliente[2] == "Confuso":
        messaggio_cliente += " Forse... non so bene come spiegarmi."

    st.session_state.messaggio_cliente = messaggio_cliente
    st.session_state.conversation_history.append(f"**:blue[Cliente]:** {messaggio_cliente}")

# --- Sidebar ---
with st.sidebar:
    if 'anthropic_api_key' not in st.session_state:
        anthropic_api_key = st.text_input("Anthropic API Key", key="file_qa_api_key", type="password")
        if anthropic_api_key:
            st.session_state.anthropic_api_key = anthropic_api_key
            # If there's a pending message when API key is added, rerun to process it
            if st.session_state.pending_operator_message:
                st.rerun()
    else:
        anthropic_api_key = st.session_state.anthropic_api_key
        st.text_input("Anthropic API Key", value="API Key salvata", disabled=True)

# Get file timestamp
file_path = __file__  # Gets the current script's path
timestamp = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
formatted_timestamp = timestamp.strftime("%d/%m/%Y %H:%M:%S")

st.title("📝 Customer Service Training")
st.caption(f"Script aggiornato il: {formatted_timestamp}")

# Visualizza la conversazione in alto - Usa un placeholder
chat_placeholder = st.empty()
with chat_placeholder.container():
    st.markdown("## Conversazione:")
    for message in st.session_state.conversation_history:
        st.markdown(message)

# Aggiungi il placeholder per il messaggio "sta scrivendo"
typing_placeholder = st.empty()

# Stile CSS personalizzato per fissare la casella di input in basso
st.markdown("""
<style>
.bottom-container {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    background-color: white;
    padding: 10px;
    border-top: 1px solid #ddd;
}
</style>
""", unsafe_allow_html=True)

# Input dell'operatore in basso, fisso
st.markdown("<div class='bottom-container'>", unsafe_allow_html=True)
with st.form(key='my_form', clear_on_submit=True):
    if not st.session_state.conversazione_finita:
        messaggio_operatore = st.text_input("Scrivi la tua risposta:", 
                                          key=f"input_{st.session_state.input_key}",
                                          value="")
    else:
        messaggio_operatore = None

    submit_button = st.form_submit_button(label='Invia')
st.markdown("</div>", unsafe_allow_html=True)

# --- Logica di conversazione ---
if submit_button and messaggio_operatore and messaggio_operatore.strip():
    # Store the operator's message and increment input key
    st.session_state.pending_operator_message = messaggio_operatore.strip()
    st.session_state.input_key += 1
    st.rerun()

# Process pending operator message if exists
if st.session_state.pending_operator_message:
    if not anthropic_api_key:
        st.error("⚠️ Per favore, inserisci la tua Anthropic API key nella barra laterale per continuare.")
        st.stop()
    
    messaggio_operatore = st.session_state.pending_operator_message
    st.session_state.pending_operator_message = None  # Clear the pending message
    
    # Immediately append operator's message to conversation history
    st.session_state.interazioni += 1
    st.session_state.conversation_history.append(f"**:red[Operatore]:** {messaggio_operatore}")
    
    # Force refresh the chat display
    with chat_placeholder.container():
        st.markdown("## Conversazione:")
        for message in st.session_state.conversation_history:
            st.markdown(message)

    # Show typing indicator before processing customer response
    with typing_placeholder:
        st.markdown('<div style="padding: 0.5em; border-radius: 0.5em; background-color: #e6f3ff;"><span style="color: #0066cc;">Il cliente sta scrivendo<span class="typing-animation"></span></span></div>', unsafe_allow_html=True)
        
        # Process customer response
        prompt_content = "\n".join(st.session_state.conversation_history)
        prompt = f"""
        Sei il cliente di un brand retail.

        Ecco lo storico della conversazione:

        {prompt_content}

        Il tuo umore è {st.session_state.cliente[1]}, la tua personalità è {st.session_state.cliente[0]}, il tuo stile di scrittura è {st.session_state.cliente[2]}.
        La tua richiesta è di tipo {st.session_state.cliente[3]}.
        La tua conoscenza del problema è {st.session_state.cliente[4]}.
        La tua disponibilità di dati è {st.session_state.cliente[5]}.

        Continua la conversazione impersonando sempre il cliente. Non impersonare mai l'operatore di customer service.
        Se la richiesta è di tipo "Acquisto" o "Informazioni commerciali", valuta se l'operatore propone upselling o cross-selling.
        Se la richiesta è di tipo "Assistenza tecnica" o "Assistenza amministrativa", valuta se l'operatore ti aiuta a risolvere il problema.
        Mantieni la conversazione coerente e realistica.
        Se hai raggiunto la decima interazione, scrivi "Grazie per l'assistenza. Arrivederci." e termina la conversazione.
        """

        if anthropic_api_key:
            try:
                client = anthropic.Client(api_key=anthropic_api_key)
                response = client.messages.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="claude-3-opus-20240229",
                    max_tokens=500,
                )
                messaggio_cliente = response.content[0].text
                st.session_state.conversation_history.append(f"**:blue[Cliente]:** {messaggio_cliente.strip()}")

                if st.session_state.interazioni >= 10 or "Arrivederci" in messaggio_cliente:
                    st.session_state.conversazione_finita = True

                # Update chat display again with customer's response
                with chat_placeholder.container():
                    st.markdown("## Conversazione:")
                    for message in st.session_state.conversation_history:
                        st.markdown(message)

            except Exception as e:
                st.error(f"Error during API call: {str(e)}")
        else:
            st.error("⚠️ Per favore, inserisci la tua Anthropic API key nella barra laterale per continuare.")
            st.stop()
    
    # Clear the typing indicator after response
    typing_placeholder.empty()

# --- Valutazione (se la conversazione è finita) ---
if st.session_state.conversazione_finita:
    st.markdown("### 📊 Preparazione della valutazione in corso...")
    with st.spinner("Analisi della conversazione..."):
        prompt_valutazione = f"""{anthropic.HUMAN_PROMPT}
        Sei un valutatore di operatori del customer service.

        Ecco lo storico della conversazione:

        {st.session_state.conversation_history}

        Valuta l'operatore in base ai seguenti criteri, assegnando un punteggio da 0 a 100 per ciascuna categoria:

        1. Comunicazione: Valuta la correttezza della comunicazione sul piano dell'ortografia, della precisione e organizzazione della risposta, del registro linguistico, ecc... Valuta inoltre se l'operatore è puntuale, sintetico ed esaustivo nelle risposte, non fa troppe domande e si adatta alla necessità del cliente.
        2. Capacità commerciale: Valuta la capacità di analizzare il profilo del cliente, di descrivere l'offerta commerciale con particolare riferimento ai dettagli sui prezzi, gli sconti applicabili e la validità. Valuta inoltre la capacità di cogliere le opportunità di cross-selling e upselling anche se il cliente non esplicita questo bisogno.
        3. Caring: Valuta la capacità dell'operatore di rivolgere le domande giuste, valuta se risolve il problema del cliente, se gestisce correttamente la sua privacy. Per mettere alla prova l'operatore, nel dialogo fornisci dei dati sensibili e valuta come vengono tutelati.
        4. Fidelizzazione: valuta la capacità di ascolto, l'abilità nel conquistare la fiducia del cliente ed entrare in una connessione empatica con lui o lei.
        5. Efficienza: valuta la produttività media oraria, cioè calcola e mostra la durata della conversazione. Inoltre fai una simulazione di quante conversazioni analoghe a quella sostenuta potrebbero essere gestite in un'ora.

        Fornisci un punteggio per ogni categoria e un punteggio medio.
        Se il punteggio medio è compreso tra 10 e 30, il livello è "Da colmare".
        Se il punteggio medio è compreso tra 31 e 60, il livello è "Da perfezionare".
        Se il punteggio medio è superiore a 60, il livello è "Adeguato".

        Se il livello è diverso da "Adeguato", formula delle raccomandazioni per aiutare l'operatore a migliorare.

        {anthropic.AI_PROMPT}"""

        if anthropic_api_key:
            client = anthropic.Client(api_key=anthropic_api_key)
            response_valutazione = client.messages.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt_valutazione,
                    }
                ],
                model="claude-3-opus-20240229",
                max_tokens=1000,
            )
            st.markdown("### 📈 Risultati della valutazione")
            st.write(response_valutazione.content[0].text.strip())
        else:
            st.info("Please add your Anthropic API key to continue.")