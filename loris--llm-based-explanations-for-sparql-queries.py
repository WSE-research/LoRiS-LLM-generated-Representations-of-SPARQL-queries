import streamlit as st
from streamlit.components.v1 import html
from code_editor import code_editor
import extra_streamlit_components as stx

from PIL import Image
import base64
import requests
import urllib
import logging
from decouple import config
import os
import signal
import random

from util import include_css, replace_values_in_index_html, get_sparql_query_examples, get_random_element, feedback_messages, feedback_icons


BACKEND_URL = config('BACKEND_URL')
PAGE_ICON = config('PAGE_ICON')
PAGE_IMAGE = config('PAGE_IMAGE')
GITHUB_REPO = config('GITHUB_REPO')
DESCRIPTION = config('DESCRIPTION').replace("\\n", "\n") % (
    GITHUB_REPO, GITHUB_REPO + "/issues/new", GITHUB_REPO + "/issues/new")
META_DESCRIPTION = config('META_DESCRIPTION', default=None)
CUSTOM_HEADER = config('CUSTOM_HEADER', default=None)
FEEDBACK_ENDPOINT = config('FEEDBACK_ENDPOINT', default=None)

FEEDBACK_BEST = 5
FEEDBACK_WORST = 1

REPLACE_INDEX_HTML_CONTENT = config('REPLACE_INDEX_HTML_CONTENT', default=False, cast=bool)
CANONICAL_URL = config('CANONICAL_URL', default=None)
ADDITIONAL_HTML_HEAD_CONTENT = config('ADDITIONAL_HTML_HEAD_CONTENT', default=None)
WRAP = True

PAGE_TITLE = "LoRiS -- LLM-based natural-language representations for SPARQL queries over Wikidata and DBpedia"

GPT3_5_TURBO = "GPT-3.5 (from OpenAI)"
GPT4 = "GPT-4 (from OpenAI)"
MISTRAL = "Mistral 7B (from Mistral AI)"
MISTRAL_FINETUNED = "Mistral 7B, fine-tuned"
ONESHOT = "①" # "One-shot"
ZEROSHOT = "⓪" # "Zero-shot"


MODEL_KEY = "model"
LANGUAGE_KEY = "lang"
SHOTS_KEY = "shots"

GPT3_5_MODEL = "gpt-3.5-turbo"
GPT4_MODEL = "gpt-4-1106-preview"
MISTRAL_MODEL = "mistral-7b"
MISTRAL_MODEL_FINETUNED = "mistral-7b-finetuned"

SEPARATOR = """, shots: """
GPT3_5_ZERO_SHOT = GPT3_5_TURBO + SEPARATOR + ZEROSHOT
GPT3_5_ONE_SHOT = GPT3_5_TURBO + SEPARATOR + ONESHOT
GPT4_ZERO_SHOT = GPT4 + SEPARATOR + ZEROSHOT
GPT4_ONE_SHOT = GPT4 + SEPARATOR + ONESHOT
MISTRAL_ZERO_SHOT = MISTRAL + SEPARATOR + ZEROSHOT
MISTRAL_ONE_SHOT = MISTRAL + SEPARATOR + ONESHOT
MISTRAL_MODEL_FINETUNED_ZERO_SHOT = MISTRAL_FINETUNED + SEPARATOR + ZEROSHOT  
MISTRAL_MODEL_FINETUNED_ONE_SHOT = MISTRAL_FINETUNED + SEPARATOR + ONESHOT   

explanation_last = { "explanation": "" }
explanation_models_dict = { 
    GPT3_5_ZERO_SHOT: {
        MODEL_KEY: GPT3_5_MODEL,
        SHOTS_KEY: 0
        },
    GPT3_5_ONE_SHOT: {
        MODEL_KEY: GPT3_5_MODEL,
        SHOTS_KEY: 1
        },
    GPT4_ZERO_SHOT: {
        MODEL_KEY: GPT4_MODEL,
        SHOTS_KEY: 0
        },
    GPT4_ONE_SHOT: {
        MODEL_KEY: GPT4_MODEL,
        SHOTS_KEY: 1
        },
    # MISTRAL_ZERO_SHOT: {
    #     MODEL_KEY: MISTRAL_ZERO_SHOT,
    #     SHOTS_KEY: 0
    #     },
    # MISTRAL_ONE_SHOT: {
    #     MODEL_KEY: MISTRAL_ONE_SHOT,
    #     SHOTS_KEY: 1
    #     },
    MISTRAL_MODEL_FINETUNED_ZERO_SHOT: {
        MODEL_KEY: MISTRAL_MODEL_FINETUNED,
        SHOTS_KEY: 0
    },
    MISTRAL_MODEL_FINETUNED_ONE_SHOT: {
        MODEL_KEY: MISTRAL_MODEL_FINETUNED,
        SHOTS_KEY: 1
    }
}
explanation_models = explanation_models_dict.keys()


EN_STRING = "🇺🇸 en"
DE_STRING = "🇩🇪 de" 
RU_STRING = "🇷🇺 ru"
explanation_languages_dict = {
    EN_STRING: "en",
    DE_STRING: "de",
    RU_STRING: "ru"
}
language_text = {
    EN_STRING: "🇺🇸",
    DE_STRING: "🇩🇪",
    RU_STRING: "🇷🇺"
}

explanation_languages = explanation_languages_dict.keys()

agree_on_showing_additional_information = True

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

replace_values_in_index_html(st, REPLACE_INDEX_HTML_CONTENT,
                             new_title=PAGE_TITLE,
                             new_meta_description=META_DESCRIPTION,
                             new_noscript_content=DESCRIPTION,
                             canonical_url=CANONICAL_URL,
                             page_icon_with_path=PAGE_ICON,
                             additional_html_head_content=ADDITIONAL_HTML_HEAD_CONTENT
                             )

st.set_page_config(layout="wide", initial_sidebar_state="expanded",
                   page_title=PAGE_TITLE,
                   page_icon=Image.open(PAGE_ICON)
                   )
include_css(st, ["css/style_github_ribbon.css", "css/style_menu_logo.css",
            "css/style_logo.css", "css/style_tabs.css", "css/style_buttons.css"])

# if the dry run is enabled, we will stop the script
if config('DRY_RUN', default=False, cast=bool):
    logging.info("dry run enabled, will stop script, now")
    os.kill(os.getpid(), signal.SIGTERM)


@st.cache_data
def get_examples_from_qald9plus():
    return get_sparql_query_examples()

example_codes = get_examples_from_qald9plus()

try:
    example_id = int(st.query_params.get("example_id", -1))
    if example_id == -1 or example_id is None or example_id > len(example_codes) - 1:
        example_id = 0
except Exception as e:
    logging.error("Error occurred: " + str(e))
    example_id = 0
    
example_code = example_codes[example_id]

@st.cache_data
def get_explanation(sparql_query, model, lang):
    model_name = model[MODEL_KEY]
    shots = model[SHOTS_KEY]
    
    query = urllib.parse.quote(sparql_query)
    custom_url = f"{BACKEND_URL}/explanation?query_text={query}&language={lang}&shots={shots}&model={model_name}"
    
    headers = {}
    if CUSTOM_HEADER is not None and CUSTOM_HEADER != "": 
        headers["X-Custom-Header"] = CUSTOM_HEADER
        logging.info(f"Generating explanation for '{sparql_query}' using {model_name} via {custom_url} with headers {headers}"  )
    
    response = requests.get(custom_url, headers=headers) 
    logging.info("response.status_code: " + str(response.status_code))
    

    if response.status_code == 200 and len(response.json()) > 0 and "explanation" in response.json()[0] and "message" not in response.json()[0] and "explanation" in response.json()[0]:
        logging.info(response.json())
        explanations = {
                "subtitle": "Natural-language representation generated by ***" + model_name + "***",
                "explanation": response.json()[0]["explanation"],
                "ok": True
        }
    else:
        try:
            if len(response.json()) > 0 and "message" in response.json()[0]:
                message = response.json()[0]["message"]
        except Exception as e:
            logging.error("Error occurred: " + str(e))
            message = str(response.status_code) + " " + response.text
        
        explanations = {
            "subtitle": "Failed to generate the natural-language representation by *" + model_name + "*",
            "explanation": message if "message" in locals() else str(response.status_code) + " " + response.text,
            "ok": False 
        }
    
    return explanations
    

def update_width_slider():
    st.session_state.width_slider = st.session_state.width_input


def update_width_input():
    st.session_state.width_input = st.session_state.width_slider


with st.sidebar:
    with open(PAGE_IMAGE, "rb") as f:
    # Read the optional file VERSION.txt containing version number
        version = ""
        version_long = ""
        if os.path.exists("VERSION.txt"):
            with open("VERSION.txt", "r") as version_file:
                version = version_file.read().strip()
                version_long = ", current version " + version 

        image_data = base64.b64encode(f.read()).decode("utf-8")
        st.sidebar.markdown(
            f"""
            <div style="display:table;margin-top:-10%;margin-bottom:15%;margin-left:auto;margin-right:auto;text-align:center">
                <a href="{GITHUB_REPO}" title="go to GitHub repository{version_long}"><img src="data:image/png;base64,{image_data}" class="app_logo"></a>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.subheader("💬 Verbalization options")
        
    default_model = st.radio("Select the model to generate the explanation by default", explanation_models, index=0)
    selected_model = explanation_models_dict[default_model]
    
    
    default_language_string = st.selectbox("Select a language to generate the explanation", explanation_languages, index=0)
    language = explanation_languages_dict[default_language_string]
    
    st.markdown("""---""")
    
    st.subheader("🖵 Visualization options")

    theme = st.selectbox("Select a theme for the code editor", ["default", "light", "dark", "contrast"], index=0)
    shortcuts = st.selectbox("shortcuts:", ["vscode", "emacs", "vim", "sublime"], index=0)

    help = "Activate to focus on the editor. It will remove some white space and text from the UI."
    agree_on_showing_additional_information = not st.checkbox(
        'minimize layout', value=(not agree_on_showing_additional_information), help=help)


buttons = [{
    "name": "copy",
    "feather": "Copy",
    "hasText": True,
    "alwaysOn": True,
    "commands": ["copyAll"],
    "style": {"top": "0rem", "right": "0.4rem"}
},{
    "name": "translate me",
    "feather": "Play",
    "primary": True,
    "hasText": True,
    "alwaysOn": True,
    "showWithIcon": True,
    "commands": ["submit"],
    "style": {"bottom": "0.44rem", "right": "0.4rem", "color": "white", "border-color": "#f63366", "border-width": "thin", "border-radius": "0.5rem", "border-style": "solid"}
}]

# introduce the tool
page_header = """## {}

{}                    
""".format(PAGE_TITLE.replace("--", "—"), DESCRIPTION)

# show the page header only if the user is not minimizing the layout
if agree_on_showing_additional_information:
    with st.container():
        st.markdown(page_header, unsafe_allow_html=True)
else:
    include_css(st, ["css/remove_space_around_streamlit_body.css"])

header_column, button_column = st.columns([3, 1])
with header_column:
    st.subheader("Enter a SPARQL query")
with button_column:
    st.markdown(f"<a href='?example_id={random.randint(0, len(example_codes) - 1)}' class='random_example' target='_top'>Set a random SPARQL query</a>", unsafe_allow_html=True)
        
response_dict = code_editor(example_code, height=20, lang="sparql", theme=theme, shortcuts=shortcuts, options={"wrap": WRAP}, buttons=buttons)

logging.info(response_dict)

def send_feedback(feedback_endpoint, sparql_query, model, language, textual_representation, feedback):
    if feedback_endpoint is None:
        logging.warning(f"No feedback endpoint is provided: {feedback_endpoint}.")
        return

    response = requests.post(feedback_endpoint, json={
        "sparql_query": sparql_query,
        "model": model,
        "language": language,
        "textual_representation": textual_representation,
        "feedback": feedback
    })
    logging.info("Feedback sent: " + str(response.status_code))

st.subheader(f"Natural-language representation ({language}) for the given SPARQL query")
if response_dict["type"] == "submit":
    sparql_query = response_dict["text"]
    logging.debug(selected_model)
    
    with st.spinner("Generating natural-language representation of the SPARQL query..."):
        explanation = get_explanation(sparql_query, selected_model, language)
        if explanation_last["explanation"] == explanation["explanation"]:
            st.toast(f"The representation has been generated successfully using *{selected_model[MODEL_KEY]}*.", icon="🎉")
        else:
            explanation_last = explanation
    
    try:
        subtitle = explanation["subtitle"]
        explanation_text = explanation["explanation"]
        ok = explanation["ok"]
    except Exception as e:
        if "explanation" in explanation:
            explanation_text = explanation["explanation"] + f" (error: {str(e)})"
        else:
            explanation_text = "An error occurred: " + str(e)
        ok = False

    if ok:
        st.markdown(subtitle + ":")
        left, right = st.columns([1,1])
        
        left.success(explanation_text)
        with right:
            st.warning("We think the generated natural-language representation is correct. Do you agree?")
            placeholder, correct_column, incorrect_column = st.columns([2,2,3])
            with correct_column:
                if st.button("✅ Yes", key="correct", type="primary"):
                    send_feedback(FEEDBACK_ENDPOINT, sparql_query, selected_model, language, explanation_text, FEEDBACK_BEST)
                    st.toast(get_random_element(feedback_messages), icon=get_random_element(feedback_icons))
            with incorrect_column:
                if st.button("⤬ No", key="incorrect", type="secondary"):
                    send_feedback(FEEDBACK_ENDPOINT, sparql_query, selected_model, language, explanation_text, FEEDBACK_WORST)
                    st.toast(get_random_element(feedback_messages), icon=get_random_element(feedback_icons))
            
    else:
        st.error("An error occurred: " + explanation_text, icon="⚠")
            
else:
    st.warning("Please click on the 'translate me' button to generate the natural-language representation.")

st.markdown("""
---
Brought to you by the [<img style="height:3ex;border:0" src="https://avatars.githubusercontent.com/u/120292474?s=96&v=4"> WSE research group](https://wse-research.org/?utm_source=loris&utm_medium=footer) at the [Leipzig University of Applied Sciences](https://www.htwk-leipzig.de/).

See our [GitHub team page](http://wse.technology/) for more projects and tools.
""", unsafe_allow_html=True)

with open("js/change_menu.js", "r") as f:
    javascript = f.read()
    html(f"<script style='display:none'>{javascript}</script>")

html("""
<script>
parent.window.document.querySelectorAll("section[data-testid='stFileUploadDropzone']").forEach(function(element) {
    element.classList.add("fileDropHover")   
});

github_ribbon = parent.window.document.createElement("div");            
github_ribbon.innerHTML = '<a id="github-fork-ribbon" class="github-fork-ribbon right-bottom" href="%s" target="_blank" data-ribbon="Fork me on GitHub" title="Fork me on GitHub">Fork me on GitHub</a>';
if (parent.window.document.getElementById("github-fork-ribbon") == null) {
    parent.window.document.body.appendChild(github_ribbon.firstChild);
}
</script>
""" % (GITHUB_REPO,))
