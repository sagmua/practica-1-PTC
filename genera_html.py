

from flask import Flask, render_template, session, redirect, url_for, escape, request, g
import practica1

app = Flask(__name__)

@app.route('/',  methods  = ['GET', 'POST'])			# decorador, varia los parametros
def index():
    
    #Obtenemos los datos de las tablas:
    tabla = practica1.obtener_datos_tabla()
    
    #Obtenemos las gráficas:
    practica1.generar_graficas()
    
    #nombres de las imagenes:
    nombre_img = [
            'static/img/ta.png',
            'static/img/pres.png',
            'static/img/hr.png',
            'static/img/prec.png',
            'static/img/vv.png',
            'static/img/vmax.png',
            'static/img/dv.png',
            'static/img/dmax.png',
            'static/img/anio_mes.png'
            ]
    
    return render_template('index.html',tabla=tabla, nombre_img= nombre_img)


if __name__ == '__main__':
	app.run(host='0.0.0.0', debug=True)