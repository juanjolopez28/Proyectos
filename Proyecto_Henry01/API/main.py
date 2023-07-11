from fastapi import FastAPI
import pandas as pd
from datetime import datetime
import ast
import os

import re
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.stem.porter import PorterStemmer

app =FastAPI()

# http://127.0.0.1:8000
# la ruta raiz

df_db = pd.read_csv(os.path.join(os.path.dirname(__file__), 'data.csv'), delimiter=',', header='infer')
print(list(df_db.columns))

@app.get("/")
def index():
     return {"message":"Bienvenido, no olvides colocar en la url /docs :3"}

# #@app.get("/libros/{id}") 
# def mostrar_libro(id : int):# podemos espeficicar el tipo de dato
#     return {"data":id}  
    

porter_stemmer = PorterStemmer()

def stemming_tokenizer(str_input):
    # Eliminar signos de puntuación

    str_input=re.sub(r"[^\w\s]", "", str_input)
    # Eliminar números    
    str_input = re.sub(r"\d+", "", str_input)
    
    words = re.sub(r"[^A-Za-z0-9\-]", " ", str_input).lower().split()
    words = [word for word in words if len(word) > 1]
    words = [word.strip() for word in words]
    words = [porter_stemmer.stem(word) for word in words]
    return words

'''Ingresas el idioma, retornando la cantidad de peliculas producidas en el mismo'''
#    return {'idioma':idioma, 'cantidad':respuesta}
@app.get('/peliculas_idioma/{idioma}')
def peliculas_idioma(idioma:str):
    print(df_db)
    #es importante colocar un tipo compatible con fastapi ojo con los tipo: (numpy.int64), por eso se convierte int()
    cantidad= int((df_db['original_language']==idioma).sum())
    print("Cantidad:", cantidad)
    return {'idioma':idioma, 'cantidad':cantidad}




#     '''Ingresas la pelicula, retornando la duracion y el año'''
#   return {'pelicula':pelicula, 'duracion':respuesta, 'anio':anio}
@app.get('/peliculas_duracion/{pelicula}')
def peliculas_duracion(pelicula:str):

    resul=df_db.loc[df_db['title']==pelicula,['runtime','release_date']]
    print(resul)
    duracion=resul.at[0,'runtime']
    anio=datetime.strptime(resul.at[0,'release_date'], '%Y-%m-%d').year
    print(duracion)
    print(anio)
    return {'pelicula':pelicula, 'duracion':duracion, 'anio':anio}





#'''Se ingresa la franquicia, retornando la cantidad de peliculas, ganancia total y promedio'''
# return {'franquicia':franquicia, 'cantidad':respuesta, 'ganancia_total':respuesta, 'ganancia_promedio':respuesta}

@app.get('/franquicia/{franquicia}')
def franquicia(franquicia:str):
    datos = df_db.loc[df_db['name_collection'] == franquicia, ['revenue','title']]
    cantidad_peli=int(datos['title'].count())
    ganancia_total=datos['revenue'].apply(lambda x:  float(x)).sum()
    ganancia_promedio=ganancia_total/cantidad_peli
    print(cantidad_peli,ganancia_total)
    return {'franquicia':franquicia, 'cantidad':cantidad_peli, 'ganancia_total':ganancia_total, 'ganancia_promedio':ganancia_promedio}



'''Ingresas el pais, retornando la cantidad de peliculas producidas en el mismo'''
#return {'pais':pais, 'cantidad':respuesta}
@app.get('/peliculas_pais/{pais}')
def peliculas_pais(pais:str):
    #datos=df_db['production_countries'].apply(lambda x: [1 for valor in x if x ==pais else 0])
    df_db['production_countries'] = df_db['production_countries'].apply(ast.literal_eval)
    cantidad_peliculas = (df_db['production_countries'].apply(lambda x: pais in x)).sum()
    return {'pais':pais, 'cantidad':int(cantidad_peliculas)}

   

'''Ingresas la productora, entregandote el revunue total y la cantidad de peliculas que realizo '''
#return {'productora':productora, 'revenue_total': respuesta,'cantidad':respuesta}
@app.get('/productoras_exitosas/{productora}')
def productoras_exitosas(productora:str):
    df_db['production_companies'] = df_db['production_companies'].apply(ast.literal_eval)   
    datos = df_db[df_db['production_companies'].apply(lambda x: productora in x)]
    total_revenue = datos['revenue'].apply(lambda x: float(x)).sum()
    cantidad=datos['production_companies'].count()
    print(cantidad,total_revenue)
    return {'productora':productora, 'revenue_total': total_revenue,'cantidad':int(cantidad)}
    


#     ''' Se ingresa el nombre de un director que se encuentre dentro de un dataset debiendo devolver el éxito del mismo medido a través del retorno. 
#     Además, deberá devolver el nombre de cada película con la fecha de lanzamiento, retorno individual, costo y ganancia de la misma. En formato lista'''
#     return {'director':nombre_director, 'retorno_total_director':respuesta, 
#     'peliculas':respuesta, 'anio':respuesta,, 'retorno_pelicula':respuesta, 
#     'budget_pelicula':respuesta, 'revenue_pelicula':respuesta}'''




@app.get('/get_director/{nombre_director}')
def get_director(nombre_director:str):
    df_db['crew']=df_db['crew'].apply(ast.literal_eval)
    datos=df_db[df_db['crew'].apply(lambda x: nombre_director in x)]
    lista_peliculas=datos['title'].tolist()
    lista_fechas=datos['release_date'].tolist()
    lista_retorno=datos['return'].apply(lambda x: float(x)).tolist()
    retorno_total=datos['return'].apply(lambda x: float(x)).sum()
    lista_budget=datos['budget'].apply(lambda x: float(x)).tolist()
    lista_revenue=datos['revenue'].apply(lambda x: float(x)).tolist()
    print(nombre_director,retorno_total, lista_peliculas,lista_fechas,lista_retorno,lista_budget,lista_revenue)
    return {'director':nombre_director, 'retorno_total_director':retorno_total,'peliculas':lista_peliculas, 'anio':lista_fechas, 'retorno_pelicula':lista_retorno,'budget_pelicula':lista_budget, 'revenue_pelicula':lista_revenue}

#Se ingresa el nombre de una película y te recomienda las similares en una lista de 5 valores.
@app.get('/recomendacion/{nombre_pelicula}')
def recomendacion( titulo:str ): 
    #Solo utilizamos la columna title
    datos = df_db
    
    datos['title']=datos['title'].str.lower()
    datos = datos.dropna(subset=['title'])
    corpus =datos['title'].tolist()
  
    #Realizamos nuestra matrix tfidf

    tfidf_vectorizer = TfidfVectorizer(stop_words='english', tokenizer=stemming_tokenizer, use_idf=True)
    tfidf_matrix = tfidf_vectorizer.fit_transform(corpus)
    #nuestra query la convertirmos en una array para la comparación
    query_vector = tfidf_vectorizer.transform([titulo])
    print(query_vector.toarray())
    similarities = cosine_similarity(query_vector, tfidf_matrix)
    #Primero vemos si la pelicula no está, si está no se considera en el indice de busqueda y si no igual se busca los mas parecidos
    try:
        toy_index = corpus.index(titulo)
        top_indices = similarities.argsort()[0][::-1][:6]
        top_indices=top_indices[1:6]
    except:
        top_indices = similarities.argsort()[0][::-1][:5]

    print(top_indices)
    resultado=[]
    for index in top_indices:
        resultado.append(corpus[index])
    print(resultado)
    return {'Peliculas recomendadas': resultado}


