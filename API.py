import os
import requests
from bs4 import BeautifulSoup
from flask import Flask
from flask_cors import CORS, cross_origin

def fonction_infos(url):

    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    soupourNom = soup.find_all("div",class_="refs date")
    soupourGolf = soup.find_all("span",class_="refs date")
    soupourIndex = soup.find_all("strong")
    nom = soupourNom[0].string
    golf = soupourGolf[0].string
    golf = golf.split("-")[0]
    sexe= nom.split(" ")[0]
    indexffg = float(soupourIndex[1].string)

    #determination des coleurs de départ
    if "M." in sexe:
        if indexffg <= 11.4:
            couleurDepart = "Blanc"
        else :
            couleurDepart = "Jaune"
    else:
        if indexffg <= 18.4:
            couleurDepart = "Bleu"
        else :
            couleurDepart = "Rouge"

    resultats=[]
    resultats.append({"index":indexffg,"golf":golf,"couleurDepart":couleurDepart,"nom":nom,"sexe":sexe})

    return(resultats)

def fonction_totale(url,sss,slope,par):

    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    sousoupe = soup.find_all("td", class_="all")
    soupourAjst = soup.find_all("td", class_="hidden-md hidden-xs")
    soupourNom = soup.find_all("div",class_="refs date")
    vingt = []
    dix_neuf = []
    index = 0.0
    futur_index7 = 0.000
    nom = soupourNom[0].string

    #extraction des vingt meilleurs scores
    i=0
    cptNbCompet=0
    while cptNbCompet<20 and 8+9*i<soupourAjst.__sizeof__():
        if(soupourAjst[i*9].string):
            score=float(sousoupe [i*5+3].string)
            if soupourAjst[8+i*9].string=="-1":
                score-=1
            if soupourAjst[8+i*9].string=="-2":
                score-=2
            vingt.append(score)

            if cptNbCompet !=19:
                dix_neuf.append(score)
            cptNbCompet+=1
        i+=1

    vingtOriginal=vingt.copy()
    vingt.sort()
    dix_neuf.sort()

    #calcule de l'index
    for i in range(8):
        index+=vingt[i]
    index = (round((index+0.001)/8,1))

    #calule 7 meilleur des 19
    for i in range(7):
        futur_index7+=dix_neuf[i]

    #determination du score a battre
    diff_a_battre = dix_neuf[7]
    score_min = diff_a_battre*slope/113-par+sss

    #verification des arrondis, si l'index bouge trop peu pour le voir a un chiffre pres, je ne le compte pas comme une descente
    if round(113/slope*(int(score_min)+par-sss),1) == diff_a_battre :
        score_min-=1

    #risque t'on de monter à la prochaine compet?
    i=19
    huitmeilleurs = vingt[0:8].copy()
    cpt=vingt.count(diff_a_battre)-huitmeilleurs.count(diff_a_battre)

    while (vingtOriginal[i]>diff_a_battre and cpt>=0):
        i-=1
        if vingtOriginal[i]==diff_a_battre:
            cpt-=1

    if (i==19):
        phrase="Attention!!! ton index va augmenter en cas de contre perf"
    elif (i==18):
        phrase="Plus qu'une competition avant une carte!"
    else:
        phrase="Bonne nouvelle, tu ne risques pas de monter pendant encore "+str(19-i)+" compétitions!"
        
    if(cptNbCompet!=20):
        phrase="!!!!!!!! Ce programme n'est pas encore prevu pour tenir en compte les joueurs ayant moins de 20 competitions validées!!!!!!!!!!!"
    
    #On est partis pour les calcules
    resultats=[]
    resultats.append({"index":index,"phrase":phrase,"nom":nom})
    if(cptNbCompet!=20):
        return(resultats)
    i=int(score_min+1)
    while i >-14:
        score_diff = round(113/slope*(i+par-sss),1)
        if index-score_diff>10:
            resultats.append({"score":i,"diff":str(round(score_diff,1))+" - 2","nouvel_index":round((futur_index7+min(score_diff-2,diff_a_battre)+0.001)/8,1 )})
        elif index-score_diff>7:
            resultats.append({"score":i,"diff":str(round(score_diff,1))+" - 1","nouvel_index":round((futur_index7+min(score_diff-1,diff_a_battre)+0.001)/8,1 )})
        else:
            resultats.append({"score":i,"diff":round(score_diff,1),"nouvel_index":round((futur_index7+min(score_diff,diff_a_battre)+0.001)/8,1 )})
        i-=1

    return(resultats)

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route('/info/<url>', methods=['GET'])
def go_url(url):
    return (fonction_infos("https://pages.ffgolf.org/histoindex/fiche/"+url))

@app.route('/perso/<url>/<sss>/<slope>/<par>', methods=['GET'])
def perso(url,sss,slope,par):
    return (fonction_totale("https://pages.ffgolf.org/histoindex/fiche/"+url,float(sss),float(slope),int(par)))

@app.route('/test', methods=['GET'])
def test():
    return("API active")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
             
