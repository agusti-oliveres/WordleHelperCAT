import io
from flask import Flask, render_template, Response
from flask import request as f_request

import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

from bs4 import BeautifulSoup
import requests
from requests.exceptions import HTTPError
import json
import unidecode

import pandas as pd
import numpy as np


app = Flask(__name__)

def get_data():
    with open("assets/catala.txt", encoding="utf8") as f:
        paraules = f.readlines()
    paraules = [paraula.strip("\n") for paraula in paraules]
    df_paraules = pd.DataFrame(paraules, columns=["mot"])
    df_paraules["length"] = df_paraules["mot"].str.len()
    df_paraules_5 = df_paraules[df_paraules["length"] == 5]
    df_paraules_5 = df_paraules_5.reset_index(drop=True)

    # Crear DF amb cada lletra a una columna i eliminar accents, etc.
    arr = np.array(list(df_paraules_5["mot"].apply(lambda x: list(unidecode.unidecode(x)))))
    df_lletres = pd.DataFrame(arr)
    df_lletres.columns = [1, 2, 3, 4, 5]
    # Ajuntar paraula i lletres en un mateix DF
    df_lletres = pd.concat((df_paraules_5, df_lletres), axis=1)
    # Eliminar accents, etc. de les paraules
    df_lletres["mot_net"] = df_lletres["mot"].apply(lambda x: unidecode.unidecode(x))
    # Eliminar paraules que comencen en majúscula
    df_lletres = df_lletres[~df_lletres[1].str.isupper()]
    # Eliminar duplicats
    df_lletres = df_lletres.drop_duplicates()
    return df_lletres

def lletres_in_paraula(paraula, lletres):
    """
    Retorna TRUE si la paraula conte alguna de les lletres "negres"
    
    paraula: str
    lletres: str amb les lletres "negres"
    """
    l_lletres = [i for i in lletres]
    
    l_coincidencies = [
        lletra in paraula
        for lletra in l_lletres
    ]
    return True in l_coincidencies

    
# APLICAR TOTS ELS FILTRES
def retornar_candidats(df_lletres, d_filtres):

    candidats = df_lletres.copy()

    # Paraules negres
    candidats = candidats[
        candidats['mot_net'].apply(
            lambda x: not lletres_in_paraula(x, d_filtres['negre'])
        ).values
    ]
    # Paraules grogues
    for posicio, lletres in d_filtres['groc'].items():
        if lletres is not None:
            # Lletra groga no pot estar a la posicio on surt
            candidats = candidats[
                candidats[posicio].apply(
                    lambda x: not lletres_in_paraula(x, lletres)
                ).values
            ]

            # Lletres groga han d'apareixer a la paraula
            for lletra in lletres:
                candidats = candidats[
                    candidats['mot_net'].apply(
                        lambda x: lletres_in_paraula(x, lletra)
                    ).values
                ]
    # Paraules verdes
    for posicio, lletres in d_filtres['verd'].items():
        if lletres is not None:
            # Lletra verda ha d'apareixer a la posicio on surt
            candidats = candidats[
                candidats[posicio].apply(
                    lambda x: lletres_in_paraula(x, lletres)
                ).values
            ]
    return candidats

def read_form(form_id):
    value = f_request.form[form_id]
    if len(value) == 0:
        return None
    else:
        return str(value)

@app.route('/', methods=['GET', 'POST'])
def read_filters():
    if f_request.method == 'POST':

        # Get data
        df_lletres = get_data()

        # Get filters
        d_filtres ={
            "negre": read_form("negre"),
            "groc": {k: read_form(f"groc_{k}") for k in range(1, 6)},
            "verd": {k: read_form(f"verd_{k}") for k in range(1, 6)},
        }
        
        # Get shortlisted values
        df = retornar_candidats(df_lletres, d_filtres)

        # Get charts
        fig, ax = plt.subplots()
        lletres_uniques = (
            df.drop_duplicates(["mot_net"])
            [[1, 2 , 3, 4, 5]]
            .stack()
            .value_counts()
        )
        lletres_uniques.plot(kind="bar", title="Histogram", ax=ax)
        fig.savefig('images/hist.png')


        # # Dummy authentication (replace it with proper authentication logic)
        # if any(user['username'] == username and user['password'] == password for user in users):
        #     return "Logged in successfully!"  # Redirect to dashboard or another page
        # else:
        #     return "Invalid username or password. Try again."

        return render_template(
            "index.html",
            tables=[df.to_html(classes='data', header=True)],
            titles=df.columns.values,
            plot1_url='images/hist.png',
            )

    return render_template(
        "index.html",
        )

if __name__ == '__main__':
    app.run(debug=True)
