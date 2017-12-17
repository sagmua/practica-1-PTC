#Samuel Cardenete Rodríguez
#Practica 1 DAI. 
'''
FICHERO QUE CONTIENE TODAS LAS FUNCIONES PARA LA OBTENCIÓN DE LAS GRÁFICAS 
Y DE LOS DATOS DE LAS PREDICCIONES ACTUALES DE GRANADA/AEROPUERTO

PARA LAS GRÁFICAS LA INFORMACIÓN RECOGIDA EN CADA HORA SE ALMACENA EN UN 
FICHERO (ULTIMOS 7 DIAS), DE EL CUAL SE OBTIENEN LAS GRÁFICAS.
'''

import requests
import json
import numpy as np
import xml.etree.ElementTree as ET

from datetime import datetime
from datetime import timedelta
from urllib.request import urlopen

import copy
import matplotlib.pyplot as plt
import shelve


def get_url_data(direccion):
    """Fetches rows from a Bigtable.

    Retrieves a url from AEMET API and returns the data given from AEMET.

    Args:
        URL: URL from AEMET API

    Returns:
        data: The data given from AEMET

    """
    
    
    #we define the URL:
    url = "https://opendata.aemet.es/opendata" + direccion
    
    #we define the API_key and the headers of the HTTP:
    querystring = {"api_key":"eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJzYW11ZWxjcjE5OTVAZ21haWwuY29tIiwianRpIjoiZGIzZmUyOGMtYWRlYS00ZTI3LTllN2YtMGU3MWJhN2U0Yjg5IiwiaXNzIjoiQUVNRVQiLCJpYXQiOjE1MTIyMjUxODQsInVzZXJJZCI6ImRiM2ZlMjhjLWFkZWEtNGUyNy05ZTdmLTBlNzFiYTdlNGI4OSIsInJvbGUiOiIifQ.J5cf554ZrmOdsOJ412TFwfp--4VJng7ZuRUqVT6kZz4"}
    headers = {'cache-control': "no-cache"}
     
    #we obtain the HTTP response from AEMET API:
    response = requests.request("GET", url, headers=headers, params=querystring, verify=False)
    
    #Now we parse JSON result to a dictionary:
    respuesta = json.loads (response.text)
    
    #and we obtain the data:
    datos = json.loads(requests.request("GET", respuesta["datos"], verify=False).text)
    
    return datos





def obtain_observation_data(name = 'ta'):
    """return the information and the date asociated with the data.
        It stores the data from the last 7 days

    Needed by the graph representation.

    Args:
        name: Name of the data we want to obtain

    Returns:
        data: The data given from AEMET and or data base.
        fechas: dates of each data.
        

    """
    
    datos=0
    fechas=0
    
    #obtenemos los datos de observacion actuales:
    observaciones = get_url_data("/api/observacion/convencional/datos/estacion/5530E")
    
    #comprobamos si es la primera vez que obtenemos datos o no:
    data_base = shelve.open('db')
    
    if len(data_base) != 0:
        #creamos la estructura donde guardaremos nuestros ficheros:
        #temperatura, dia
        data_base['ta'] = [[], []]
        #presion, dia
        data_base['pres'] = [[], []]
        #humedad, dia
        data_base['hr'] = [[], []]
        #precipitacion, dia
        data_base['prec'] = [[], []]
        #velocidad viento, dia
        data_base['vv'] = [[], []]
        #velocidad max, dia
        data_base['vmax'] = [[], []]
        #direccion viento, dia
        data_base['dv'] = [[], []]
        #direccion viento max, dia
        data_base['dmax'] = [[], []]
        
    
    
        
    #accedemos al fichero donde guardamos la información recopilada:
    #obtenemos los datos que nos interesan para las gráficas: 
    campo = data_base[name]
    for i in observaciones:
        #comprobamos si no se encuentra repetido:
        f = datetime.strptime(i['fint'], '%Y-%m-%dT%H:%M:%S')
        if f not in campo[1]:
            #añadimos cada temperatura con su fecha correspondiente:
            campo[0].append(i[name])
            campo[1].append(f)
            
    #Borramos información obsoleta (más de 7 dias) en caso de existir:
    fecha_obsoleta = max(campo[1])-timedelta(days=7)
    campo[0], campo[1] = borrar_obsoletos(campo[0], campo[1], fecha_obsoleta)
    
    
    
        
    data_base[name] = campo    
    #devolvemos los datos en np para poder ser representados en la gráfica:
    datos = np.array(campo[0])
    fechas = np.array(campo[1])
    
    data_base.close()
    
    return datos, fechas

    
def borrar_obsoletos(datos, fechas, obsoleta):
    i=0
    while i < len(fechas):
        if fechas[i] < obsoleta:
            del fechas[i]
            del datos[i]
            i = 0
        else:
            i+=1
    
    return datos, fechas


def generar_graficas():
    #nombres de los datos a generar:
    generar = {
            'ta': 'Temperatura (Cº)',
            'pres': 'Presion (hPa)',
            'hr': 'Humedad (%)',
            'prec': 'precipitacion (l/m2)',
            'vv': 'velocidad viento (m/s)',
            'vmax' : 'velocidad viento max.(m/s)',
            'dv': 'direccion viento (grados)',
            'dmax': 'direccion viento max.(grados)'
            }
    
    #vamos generando una a una las gráficas:
    
    for key, value in generar.items():
        #obtenemos los datos actualizados:
        datos, fechas = obtain_observation_data(name=key)
        #pintamos:
        fig = plt.figure()
        ax = plt.subplot(111)
        
        plt.xticks(rotation='vertical')
        plt.xlabel('Fecha')
        plt.ylabel(value)
        
        ax.plot(fechas, datos)
        
        datemin = fechas.max()-timedelta(days=7)
        datemax = fechas.max()
        ax.set_xlim(datemin, datemax)
        
        
        
        
        ax.grid(True)
        fig.autofmt_xdate()
        
        fig.savefig('./static/img/'+key+'.png')
        
    #Ahora la gráfica de las precipitaciones:
    fig = plt.figure()
    ax = plt.subplot(111)
    
    plt.ylabel('(L/m2)')
    mensuales, anuales = resumen_precipitaciones()
    ax.bar(['mes','anio'], [mensuales, anuales])
    fig.savefig('./static/img/anio_mes.png')
        
    
def resumen_precipitaciones():
    
    #obtenemos los valores del mes y del año:
    hoy = datetime.now().date()
    data = get_url_data('/api/valores/climatologicos/mensualesanuales/datos/anioini/'+str(hoy.year)+'/aniofin/'+str(hoy.year)+'/estacion/5530E')
    
    #recorremos los meses, sumando las precipitaciones para obtener las anuales:
    anuales = 0
    mensuales = float(data[hoy.month-2]['p_mes'])
    for mes in data:
        if 'p_mes' in mes:
            anuales += float(mes['p_mes'])
    
    return mensuales, anuales
        
 
def obtener_datos_tabla():
    #accedemos al xml con las predicciones de AEMET:
    tree = ET.parse(urlopen('http://www.aemet.es/xml/municipios/localidad_18087.xml'))
    root = tree.getroot()
    
    #Obtenemos la cabecera del XML con la fecha de obtencion:
    fecha = root.find("elaborado")
    date = datetime.strptime(fecha.text, '%Y-%m-%dT%H:%M:%S')
    
    #obtenemos además de la API, la informacion actual:
    observaciones = get_url_data("/api/observacion/convencional/datos/estacion/5530E")
    observaciones_actuales = observaciones[len(observaciones)-1]
    
    t_actual = observaciones_actuales['ta']
    h_actual = observaciones_actuales['hr']
    rocio_actual = observaciones_actuales['tpr']
    
    
    t_actual_granada_aero ={
            'Temperatura (C)': t_actual,
            'Humedad (%)' : h_actual,
            'Punto Rocio (C)':  rocio_actual,
            'Viento (Km/h)' : observaciones_actuales['vv'],
            'Presion (hPa)' : observaciones_actuales['pres'],
            'Precipitacion (l/m2)' : observaciones_actuales['prec']
            
    }
    
    predicciones = root.find("prediccion")
    
    #temperaturas extremas del XML:
    temperaturas = predicciones[0].find('temperatura')
    t_max_min = (temperaturas[0].text, temperaturas[1].text)
    
    #humedades extremas del XML:
    humedad = predicciones[0].find('humedad_relativa')
    h_max_min = (humedad[0].text, humedad[1].text)
    
    #velocidad viento máxima:
    viento_max = 0
    viento = predicciones[0].findall('viento')
    for intervalo in viento:
        if intervalo[1].text != None:
            if int(intervalo[1].text) > viento_max:
                viento_max = int(intervalo[1].text)
                
    #the minimum termical sensation:
    min_sensacion_t = predicciones[0].find('sens_termica')[1].text
    
    max_min_actual = {
            'Temperatura maxima': t_max_min[0],
            'Temperatura minima': t_max_min[1],
            'Humedad maxima': h_max_min[0],
            'Humedad minima': h_max_min[1],
            'Velocidad viento max': viento_max,
            'Sensacion termica min': min_sensacion_t  
    }
    
    
    
    #las del mes:
    
    #we obtain the fist day of the month:
    date_ini_mes = copy.deepcopy(date)
    date_ini_mes = date.replace(day = 1, hour=0, minute = 0,second = 1)
    
    #Now we can obtain the observations about the last month:
    url = '/api/valores/climatologicos/diarios/datos/fechaini/'+date_ini_mes.isoformat()+'UTC'+'/fechafin/'+date.isoformat()+'UTC'+'/estacion/5530E'
    observaciones_mes = get_url_data(url)
    
    t_min_mes = 10000
    t_max_mes = -10000
    p_min_mes = 10000
    p_max_mes = -10000
    
    
    for dia in observaciones_mes:
        
        if float(dia['tmin'].replace(',','.')) < t_min_mes:
            t_min_mes = float(dia['tmin'].replace(',','.'))
            
        if float(dia['tmax'].replace(',','.')) > t_max_mes:
            t_max_mes = float(dia['tmax'].replace(',','.'))
            
        if float(dia['presMax'].replace(',','.')) > p_max_mes:
            p_max_mes = float(dia['presMax'].replace(',','.'))
        
        if float(dia['presMin'].replace(',','.')) < p_min_mes:
            p_min_mes = float(dia['presMin'].replace(',','.'))
            
    
    max_min_mes = {
            'Temperatura maxima mes': t_max_mes,
            'Temperatura minima mes': t_min_mes,
            'Presion maxima mes': p_max_mes,
            'Presion minima mes': p_min_mes 
    }
    
    
    #diccionario a devolver:
    salida = {
         'Tiempo actual en Granada Aeropuerto': t_actual_granada_aero,
         'Max. y Min. de hoy': max_min_actual,
         'Max. y Min. del mes': max_min_mes
    }
    
    return salida
#%%
    

if __name__ == "__main__":
    
    #Obtenemos los datos de las tablas:
    tabla = obtener_datos_tabla()
    
    #Obtenemos las gráficas:
    generar_graficas()
    
    
    

    
        
        
       
    
    
    