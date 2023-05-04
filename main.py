import requests
from bs4 import BeautifulSoup as bs
import re
import csv
import os
      
# On crée une fonction pour récupérer le lien dans la balise a
def infos(element):
    reslutat = []
    #On parcours chaque article comprenant le html d'un livre 
    for e in element:
        #On recupère la première balise a 
        link = e.find('a')
        #On extrait le lien 
        url= link.get('href')
        #On l'ajoute à la liste en remplçant les ../ par l'url du site
        reslutat.append('http://books.toscrape.com/catalogue/' + url[9:])
    return reslutat

# Fonction pour récupérer l'url des images 
def link_img(element):
    for e in element:
        link = e.get('src')
        url = link[6:]
        return url

# Fonction pour recupérer tout les a d'un element
def find_category(element):
    for e in element:
        liste = e.find_all('a')
        return liste

# Fonction pour recupérer les liens et recréer l'url compléte puis la passer dans un tableau
def link_category(element):
    resultat = []
    for link in element:
        url = link.get('href')
        resultat.append('http://books.toscrape.com/' + url)
    return resultat

# Fonction pour telecharger une image et la sauvegarder dans le dossier de sa catégorie à l'intérieur du dossier image
def telecharger_image(url_I, categorie_I, nom_fichier):
    # Si le dossier de la catégorie du livre n'existe pas on le crée
    if not os.path.exists(f"images/{categorie_I}"):
        os.makedirs(f"images/{categorie_I}")
    
    # On va chercher l'image    
    response = requests.get(url_I)
    # On l'enregistre dans le dossier en la nommant comme le titre du livre
    with open(f"images/{categorie_I}/{nom_fichier}.jpg", "wb") as f:
        f.write(response.content)
              
# Fonction pour netoyer le nom d'un fichier en supprimant les caractères invalides
def nettoyer_nom_fichier(element):
    nom_fichier= re.sub(r'[^\w\-_\.\# ]', '-', element)
    nom_fichier = nom_fichier.strip()
    return(nom_fichier)

# Fonction pour extraire les informations de tous les livres d'une même catégorie
def extraction_livre(url):
    
    # On crée un tableau vide qui acceuillera les livres
    data =[]
    
    while True:
        
        page = requests.get(url)

        soup = bs(page.content, 'html.parser')

        book = soup.find_all('article', attrs={'class': 'product_pod'})
        
        # On recupère notre liste de liens de livre 
        book_lien= infos(book)
        #print(book_lien)
               
        # Pour chaque lien dans la liste
        for e in book_lien:
            
            url_book = e
            
            page_book = requests.get(url_book)

            soup_book = bs(page_book.content, 'html.parser')
            
            ul_categorie = soup_book.find('ul', attrs={'class': 'breadcrumb'})
            li_categorie = ul_categorie.find_all('li')[2]
            a_categorie = li_categorie.find('a')
            categorie = a_categorie.text

            titre = soup_book.find('h1').string

            description = soup_book.select_one('article > p').string

            product_information = soup_book.find_all('td')

            upc = product_information[0].string

            price_noTax = product_information[2].string

            price_Tax = product_information[3].string

            # On recupère l'entier du nombre d'articles available
            # On separe le 'In stock(' du '19 available)' et on separe une deuxième fois pour garder le 19 qu'on pass en entier 
            availability = product_information[5].string
            number_available = int(availability.split('(')[1].split()[0])

            image = soup_book.select('div > img')
            url_image = ('http://books.toscrape.com/' + link_img(image))
            
            # On utilise re.compile pour les similitudes de classe
            # Une fois la classe trouvée on recupère son nom complet et on extrait le deuxième element correspondant à la note
            rating = soup_book.find(class_=re.compile('star-rating'))
            classe = rating['class']
            review_rating = classe[1] + ' on Five'
            
            # On récupère toutes les informations de chaque livre dans un objet
            data.append({'Categorie': categorie,
                'Url produit': url_book, 
                'Code produit': upc, 
                'Titre': titre, 
                'Prix taxe inclue': price_Tax, 
                'Prix taxe exclue': price_noTax, 
                'Disponible': number_available, 
                'Description': description,
                'Note': review_rating,
                'Url image': url_image})
            
            url_I = url_image 
            categorie_I = categorie
            nom_fichier = nettoyer_nom_fichier(titre)
            telecharger_image(url_I, categorie_I, nom_fichier)       
        
        # On cherche le bouton next de la page pour vérifier si il y a d'autres pages        
        next_button = soup.find('li', class_='next')
        
        # Si il y a une autre page on recupère son url et on remplace l'url en cours
        if next_button is not None:
            url = url + '/' + next_button.a['href']
        else:
            break
        
    return data

def écriture_csv(data, categorie):
    # Création d'un dossier livre
    if not os.path.exists('bibliothèque'):
        os.makedirs('bibliothèque')
    # Ouverture fichier csv en mode écriture dans en passant egalement l'argument categorie qui nous permettre de nommer le fichier csv
    with open(f'bibliothèque/{categorie}.csv', mode='w', newline='', encoding='utf-8') as fichier_csv:
        # Création d'un objet Dictwriter pour ecrire dans le csv. fieldnames correspond aux noms des colonnes
        writer = csv.DictWriter(fichier_csv, fieldnames=['Categorie', 'Url produit', 'Code produit', 'Titre', 'Prix taxe inclue', 'Prix taxe exclue', 'Disponible', 'Description', 'Note', 'Url image'] )
        
        # On recupère les noms des colonnes pour les mettre en en tête
        writer.writeheader()
        
        # Pour chaque objet dans la liste on écrit les données dans le fichier csv
        for row in data:
            writer.writerow(row)

def main_action():
    
    url = "http://books.toscrape.com/index.html"
    page = requests.get(url)
    soup = bs(page.content, 'html.parser')   
    
    # On decortique le html pour récupérer les balises a
    list_category = soup.find_all('ul', attrs= {'class': 'nav nav-list'})
    category = find_category(list_category)
    
    # On recupère les liens stockés dans la liste de balises a
    url_category = link_category(category)
    # On supprime le bloc book
    url_category.pop(0)
    # On supprime le index.html à la fin de chaque lien
    lien_category = []
    for e in url_category:
        new_link = e.replace('index.html', '')
        lien_category.append(new_link)
    
    # Pour chaque lien dans la liste de catégories on execute tout le code 
    for data in lien_category:
        url= data
        livres = extraction_livre(url)
        categorie = livres[0]['Categorie']
        écriture_csv(livres,categorie)
        
main_action()
    

