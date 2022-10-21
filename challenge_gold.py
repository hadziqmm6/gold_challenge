from flask import Flask, request, jsonify
import re
import string
import pandas as pd
from flasgger import Swagger, LazyString, LazyJSONEncoder, swag_from
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt

app = Flask(__name__)
app.json_encoder = LazyJSONEncoder

swagger_template = dict(
info = {
    'title': LazyString(lambda: 'Membuat Cleansing API untuk CSV dan JSON'),
    'version': LazyString(lambda: '1'),
    'description': LazyString(lambda: 'Gold Challenge'),
    },
    host = LazyString(lambda: request.host)
)

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'docs',
            "route": '/docs.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs/"
}

conn = sqlite3.connect("challenge_gold.db",check_same_thread=False)
#conn.execute("CREATE TABLE cleansing_json (input_kotor varchar(255),  output_bersih varchar(50));")


swagger = Swagger(app, template=swagger_template,             
                  config=swagger_config)

def _remove_punct(s):
    return re.sub(r"[^\w\d\s]+", "",s)

def _remove_double_space(s):
    return re.sub(' +', ' ',s)

def _remove_more_punct(s):
    return re.sub(r'\\x[A-Za-z0-9./:)(*&^%$#@!_;]+','', s)

@swag_from("swagger_config.yml", methods=['POST'])
@app.route("/clean_text/v1", methods=['POST'])
def remove_punct_post():
    s = request.get_json()
    non_double = _remove_double_space(s['text'])
    non_punct = _remove_punct(non_double)
    more_clean = _remove_more_punct(non_punct)
    lower_case = more_clean.lower()
    masukan = str(s)
    keluaran = str(lower_case)
    #cur = conn.cursor()
    #cur.execute("INSERT INTO cleansing_json (input_kotor, output_bersih) values (?,?);",(masukan,keluaran))
    df = pd.DataFrame([[masukan,keluaran]],columns=['input_kotor','output_bersih'])
    df.to_sql('db_table2', conn, if_exists='append')
    return jsonify(lower_case)

@swag_from("swagger_upload.yml", methods=['POST'])
@app.route("/clean_csv/v1", methods=['POST'])
def remove_punct_csv():
    file = request.files.get('file')
    df = pd.read_csv(file,encoding='latin')
    #print(df.head(20))
    df['Clean_Tweet'] = df['Tweet']
    df['Banyak_Char_Kotor'] = df['Tweet'].str.len()
    df['Clean_Tweet'] = df['Clean_Tweet'].str.strip()
    df['Clean_Tweet'] = df['Clean_Tweet'].replace(r'([A-Z]+)\s(\d+)', r'\1\2', regex=True)
    df['Clean_Tweet'] = df['Clean_Tweet'].str.replace(r'\\x[A-Za-z0-9./:)(*&^%$#@!_;]+', '')
    df['Clean_Tweet'] = df['Clean_Tweet'].str.replace(r'[^\w\d\s]+', '')
    df['Clean_Tweet'] = df['Clean_Tweet'].str.lower()
    df['Clean_Tweet'] = df['Clean_Tweet'].str.replace(r'user', '')
    df['Clean_Tweet'] = df['Clean_Tweet'].str.replace(r'_', '')
    df['Banyak_Char_Bersih'] = df['Clean_Tweet'].str.len()
    df[['Banyak_Char_Kotor','Banyak_Char_Bersih']].sum().plot.bar()
    plt.show()

    current_datetime = str(datetime.now())
    df.to_sql("uploadtable"+current_datetime, conn)
    #return df.to_html()
    return jsonify({"say":"success"})
    

if __name__ == "__main__":
    app.run(port=4444, debug=True)