from PIL import Image
import requests
import logging
import os
import re
import base64
from io import BytesIO
import markdown
import random

def include_css(st, filenames):
    content = ""
    for filename in filenames:
        with open(filename) as f:
            content += f.read()
    st.markdown(f"<style>{content}</style>", unsafe_allow_html=True)

def get_size_of_image(pil_image):
    height = pil_image.size[1]
    width = pil_image.size[0]
    return {"width": width, "height": height}

def download_image(url, download_filename):
    im = Image.open(requests.get(url, stream=True).raw)
    im.save(download_filename)
    logging.info(f"downloaded file from {url} to {download_filename}")
    return get_size_of_image(im)

def save_uploaded_file(input_filename, uploaded_image_file):
    uploaded_image = Image.open(uploaded_image_file)
    uploaded_image.save(input_filename)
    logging.info("uploaded file to " + input_filename)
    return get_size_of_image(uploaded_image)

def copy_file(src, dest):
    with open(src, 'r') as f:
        data = f.read()
        f.close()
        with open(dest, 'w') as f:
            f.write(data)
            f.close()

# Convert Image to Base64 
def im_2_b64(image):
    buff = BytesIO()
    image.save(buff, format="PNG")
    img_str = base64.b64encode(buff.getvalue())
    return img_str

def replace_index_html(index_html, index_html_change_indicator_file, new_title, new_meta_description, canonical_url, new_noscript_content, favicon_base64, additional_html_head_content, page_icon_with_path):
    with open(index_html, 'r') as f:
        data = f.read()
        f.close()

        newdata = re.sub('<title>Streamlit</title>',
                         f"<title>{new_title}</title>{new_meta_description}{canonical_url}", data)

        if new_noscript_content is not None and new_noscript_content != "":
            newdata = re.sub('<noscript>You need to enable JavaScript to run this app.</noscript>',
                             f'<noscript>{new_noscript_content}</noscript>', newdata)

        if page_icon_with_path is not None:
            # Do not forget to add the favicon variable also as parameter to set_page_config
            newdata = re.sub('./favicon.png', favicon_base64, newdata)
            
        if additional_html_head_content is not None and additional_html_head_content != "":
            newdata = re.sub('</head>', f'{additional_html_head_content}</head>', newdata)

        with open(index_html, 'w') as f:
            f.write(newdata)
            f.close()

        with open(index_html_change_indicator_file, 'w') as f:
            f.write("This file indicates that the index.html file has been changed. If you want to change the values again, please delete this file.")
            f.close()
            logging.info("to enable a new adaption of the index.html file, please delete the file: " +
                         index_html_change_indicator_file)

def replace_values_in_index_html(st, activate, new_title, new_meta_description=None, new_noscript_content=None, canonical_url=None, page_icon_with_path=None, additional_html_head_content=None):
    """
        This method replaces values in the index.html file of the Streamlit package.
        The intention is to change the title of the page, the favicon and the meta description.
    """

    if not activate:
        return

    index_html = os.path.dirname(st.__file__) + '/static/index.html'
    index_html_backup = index_html + ".backup"
    index_html_change_indicator_file = index_html + ".changed"
    
    logging.warning("The index.html file is located at " + index_html + ".")

    # stop if index.html has already been changed
    if os.path.exists(index_html_change_indicator_file):
        return
    else:
        # make a backup of the index.html file
        if not os.path.exists(index_html_backup):
            copy_file(index_html, index_html_backup)
            logging.warning("Created a backup of the " +
                            index_html + " at " + index_html_backup + ".")
        else:
            logging.warning("Backup of the  " + index_html +
                            " already exists at " + index_html_backup + ".")

    logging.warning("Replacing values in index.html. Thereafter, the index.html file will be overwritten. Don't do this on a system where multiple Streamlit applications are using the same Streamlit package.")

    # only replace favicon if it is not None
    if page_icon_with_path is not None:
        with open(page_icon_with_path, "rb") as image_file:
            page_icon = Image.open(image_file)
            # just use a size of 128x128 for the embedded favicon
            page_icon = page_icon.resize((128, 128), Image.Resampling.LANCZOS)
            encoded_string = im_2_b64(page_icon)
            favicon_base64 = "data:image/png;base64," + encoded_string.decode('utf-8')

    # only set canonical_url if it is not None
    if canonical_url is not None and canonical_url != "":
        canonical_url = f'<link rel="canonical" href="{canonical_url}"/>'
    else:
        canonical_url = ""

    # only set new_meta_description if it is not None
    if new_meta_description is not None and new_meta_description != "":
        new_meta_description = f'<meta name="description" content="{new_meta_description}"/>'
    else:
        new_meta_description = ""
        
    # render noscript content if it is not None and not empty as Markdown
    if new_noscript_content is not None and new_noscript_content != "":
        new_noscript_content = markdown.markdown(new_noscript_content)
    else:
        new_noscript_content = ""    
    new_noscript_content = markdown.markdown("# " + new_title) + "\n" + new_noscript_content

    # replace content in index.html
    replace_index_html(index_html, index_html_change_indicator_file, new_title, new_meta_description, canonical_url, new_noscript_content, favicon_base64, additional_html_head_content, page_icon_with_path)

def get_random_element(elements):
    return elements[random.randint(0, len(elements) - 1)]

feedback_messages = [
    "Hey, thanks a bunch for your help!",
    "You rock! Thanks for your feedback.",
    "You're the best; thanks for your help!",
    "Much appreciated. Thanks!",
    "You're a lifesaver; thank you!",
    "I can't thank you enough for your support.",
    "Big thanks for all your help!",
    "I owe you one, thanks!",
    "You're a \u2605; thanks for your help!",
    "Thanks a million for your support!",
    "Thanks for being such a great supporter!",
    "Your help meant the world to me. Here's a hug-filled thank you!",
    "Super grateful for your help.",
    "Thanks a ton for your support!",
    "Couldn't have done it without you. Thanks!",
    "You're awesome; thanks for everything!",
    "Thanks for being so supportive!",
    "I really appreciate it; you're so kind!",
    "Your help was right on time. Thanks!",
    "I appreciate your help more than you'll ever know.",
    "Kudos to you, and thanks a million!",
    "Thank you for brightening my day!",
    "You've been incredible! Thanks a ton.",
    "Thank you. Let's go for a drink at the next opportunity!"
]

feedback_icons = [
    "🙏",
    "🤗",
    "👍",
    "👏",
    "👌"
]

def get_sparql_query_examples():
    try:
        examples = []
        qald_9_plus_train_dbpedia = requests.get("https://raw.githubusercontent.com/KGQA/QALD_9_plus/main/data/qald_9_plus_test_dbpedia.json").json()
        qald_9_plus_train_wikidata = requests.get("https://raw.githubusercontent.com/KGQA/QALD_9_plus/main/data/qald_9_plus_test_wikidata.json").json()
        
        for question in qald_9_plus_train_dbpedia["questions"] + qald_9_plus_train_wikidata["questions"]:
            if "query" in question and "sparql" in question["query"]:
                examples.append((question["query"]["sparql"] + " \n").replace("\\n", "\n").replace(" PREFIX ", "\nPREFIX ").replace(" SELECT ", "\nSELECT ").replace(" sSELECT ", "\nSELECT ").replace(" WHERE ", "\nWHERE ").replace(" ORDER BY ", "\nORDER BY ").replace(" LIMIT ", "\nLIMIT ").replace(". ", ".\n").replace("; ", ";\n\t").replace(" } ", "\n}\n").replace(" { ", "\n{\n").replace("GROUP BY ", "\nGROUP BY ").replace(" UNION ", "\nUNION\n"))
        
        logging.info(f"Loaded {len(examples)} SPARQL query examples from QALD-9-plus.")
        return examples
    
    except Exception as e: # fallback if the QALD-9-plus data could not be loaded
        logging.error(f"Could not load QALD-9-plus train data: {e}")
        return ["""PREFIX wdt: <http://www.wikidata.org/prop/direct/> 
PREFIX wd: <http://www.wikidata.org/entity/> 
SELECT DISTINCT ?uri 
WHERE {  
    ?type wdt:P279* wd:Q4830453 . 
    ?aerospace wdt:P279* wd:Q3477363 . 
    ?healthcare wdt:P279* wd:Q15067276 . 
    ?pharma wdt:P279* wd:Q507443 . 
    ?uri wdt:P452 ?aerospace ; 
         wdt:P452 ?healthcare . 
} 
""", 
"""
SELECT * WHERE { ?s ?p ?o } LIMIT 10
"""] 
