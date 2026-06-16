import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import pandas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ruta_datos = os.path.join(BASE_DIR, "datos")
ruta_jugadores = os.path.join(ruta_datos,"world_cup_2026_squads.csv")
ruta_partidos = os.path.join(ruta_datos,"partidos.csv")


df_jugadores = pandas.read_csv(ruta_jugadores)
df_partidos =pandas.read_csv(ruta_partidos)
orden = ['N/A','GK', 'LB', 'CB', 'RB','DM','CM','AM','LW','ST','RW']
prioridades = {valor: indice for indice, valor in enumerate(orden)}

app = Flask(__name__)
url=os.environ.get('DATABASE_URL')
if url is None:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:Aq96hgqvXCQRe1hypDpLMzYk77Byb2Ak@dpg-d8ng70ugvqtc7398ng40-a.oregon-postgres.render.com:5432/mundial_ivdg'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = url

db = SQLAlchemy(app)

class Persona(db.Model):
    id= db.Column(db.Integer, primary_key=True)
    nombre=db.Column(db.String(20), nullable=False)
    puntuacion=db.Column(db.Integer,nullable=False)
    cervezas=db.Column(db.Integer,nullable=False)
    
    def __str__(self):
        return f'{self.nombre} {self.puntuacion}'
    
    def cambiar_puntuacion(self,puntos):
        self.puntuacion=puntos
        db.session.commit()
        
class Seleccion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    
    def __str__(self):
        return self.nombre

class Jugador(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    posicion= db.Column(db.String (10),nullable=False)
    numero =db.Column(db.Integer, nullable=False)
    seleccion_id = db.Column(db.Integer, db.ForeignKey('seleccion.id'), nullable=False)
    
    seleccion = db.relationship('Seleccion', backref=db.backref('jugadores', lazy=True))
    
    def __str__(self):
        return f'{self.nombre} {self.seleccion}'

class Goleadores(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    partido_id=db.Column(db.Integer, db.ForeignKey('partido.id'),nullable=False)
    goleador_id=db.Column(db.Integer,db.ForeignKey('jugador.id'),nullable=False)
    cantidad=db.Column(db.Integer,nullable=False)
    
    partido=db.relationship('Partido', foreign_keys=[partido_id],lazy="joined")
    goleador=db.relationship('Jugador', foreign_keys=[goleador_id],lazy="joined")
    
    def __str__(self):
        return f'{self.partido.local} - {self.partido.visitante} {self.goleador.nombre} {self.cantidad}'
    
class Partido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    local_id=db.Column(db.Integer, db.ForeignKey('seleccion.id'), nullable=False)
    visitante_id=db.Column(db.Integer, db.ForeignKey('seleccion.id'), nullable=False)
    goles_local=db.Column(db.Integer,nullable=True)
    goles_visitante=db.Column(db.Integer,nullable=True)
    
    local=db.relationship('Seleccion', foreign_keys=[local_id])
    visitante=db.relationship('Seleccion', foreign_keys=[visitante_id])
    
    def __str__(self):
        return f'{self.local} {self.goles_local} - {self.goles_visitante} {self.visitante}'
    
    def goles (self,goles_local,goles_visitante):
        self.goles_local=goles_local
        self.goles_visitante=goles_visitante
    
class Prediccion(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    partido_id = db.Column(db.Integer, db.ForeignKey('partido.id'), nullable=False)
    goleador_local_id = db.Column(db.Integer, db.ForeignKey('jugador.id'), nullable=False)
    goleador_visitante_id = db.Column(db.Integer, db.ForeignKey('jugador.id'), nullable=False)
    persona_id = db.Column(db.Integer, db.ForeignKey('persona.id'), nullable=False)
    
    goles_local = db.Column(db.Integer, nullable=False)
    goles_visitante = db.Column(db.Integer, nullable=False)

    # Relaciones (El motor de la magia)
    partido = db.relationship('Partido', foreign_keys=[partido_id])
    goleador_local = db.relationship('Jugador', foreign_keys=[goleador_local_id])
    goleador_visitante = db.relationship('Jugador', foreign_keys=[goleador_visitante_id])
    persona = db.relationship('Persona', backref='predicciones')
    
    def __str__(self):
        return f'{self.partido.local} {self.goles_local} {self.goleador_local} - {self.goles_visitante} {self.goleador_visitante} {self.partido.visitante}'
    
    

def llenar_db():
    aux = []
    for index, row in df_jugadores.iterrows():
        seleccion =Seleccion(nombre=row["country"])
        
        if seleccion.nombre not in aux:
            aux.append(seleccion.nombre)
            db.session.add(seleccion)
            db.session.commit()
            id=seleccion.id
            
        jugador = Jugador(nombre =row ["name"],
                          posicion=row["position"],
                          numero=row["jerseyNumber"],
                          seleccion_id=id)
        
        db.session.add(jugador)
        db.session.commit()
        
    for index, row in df_partidos.iterrows():
        local_obj = Seleccion.query.filter_by(nombre=row["local"]).first()
        visitante_obj = Seleccion.query.filter_by(nombre=row["visitante"]).first()
        if pandas.isna( row["goles_local"]):
            partido = Partido(
                local=local_obj, 
                visitante=visitante_obj, 
                goles_local=999, 
                goles_visitante=999
            )
        else:
             partido = Partido(
                local=local_obj, 
                visitante=visitante_obj, 
                 goles_local=row["goles_local"], 
                goles_visitante=row["goles_visitante"]
            )   
        
        db.session.add(partido)
        db.session.commit()
    anton=Persona(nombre="Anton",puntuacion=0)
    yo=Persona(nombre="Nico",puntuacion=0)
    db.session.add(anton)
    db.session.commit()
    db.session.add(yo)
    db.session.commit()
    
    
with app.app_context():
    db.create_all()
    if Seleccion.query.first() is None:
        llenar_db()    

def cuenta(partido,prediccion):
    count=0
    count+=cuenta_resultado(partido=partido,prediccion=prediccion)
    count+=cuenta_goleador(partido=partido,prediccion=prediccion,goleador=prediccion.goleador_local)
    count+=cuenta_goleador(partido=partido,prediccion=prediccion,goleador=prediccion.goleador_visitante)
    return count

def cuenta_resultado(partido,prediccion):
    count=0
    if partido.goles_local !=999:
        if partido.goles_local==prediccion.goles_local and partido.goles_visitante==prediccion.goles_visitante:
            count+=4
        elif (partido.goles_local-partido.goles_visitante)!=0 and ((prediccion.goles_local-prediccion.goles_visitante)/(partido.goles_local-partido.goles_visitante))>0:
            count+=1
        elif (prediccion.goles_local-prediccion.goles_visitante)==(partido.goles_local-partido.goles_visitante):
            count+=1
    
    return count

def cuenta_goleador(partido,prediccion,goleador):
    count=0
    local=Goleadores.query.filter_by(partido_id=partido.id, goleador=prediccion.goleador_local).first()
    visitante=Goleadores.query.filter_by(partido_id=partido.id, goleador=prediccion.goleador_visitante).first()
        
    if local is not None and local.goleador_id==goleador.goleador_id:
        count+=2*local.cantidad
    if visitante is not None and visitante.goleador_id==goleador.goleador_id:
        count+=2*visitante.cantidad
    return count
    
def contar_cerveza(persona):
    persona.cervezas+=1
    persona.puntuacion-=3
    db.session.commit()
        

def descontar_cerveza(persona):
    persona.cervezas-=1
    persona.puntuacion+=3
    db.session.commit()
    
def contar_prediccion(persona,prediccion):
    partido=prediccion.partido
    persona.puntuacion+=cuenta(prediccion=prediccion,partido=partido)
    db.session.commit()
    
def descontar_prediccion(persona,prediccion):
    partido=prediccion.partido
    persona.puntuacion-=cuenta(prediccion=prediccion,partido=partido)
    db.session.commit()
    
def contar_partido(persona,partido):
    for prediccion in persona.predicciones:
        if prediccion.partido_id==partido.id:
            persona.puntuacion+=cuenta_resultado(partido=partido,prediccion=prediccion)
            break
    db.session.commit()
    
def descontar_partido(persona,partido):
    for prediccion in persona.predicciones:
        if prediccion.partido_id==partido.id:
            persona.puntuacion-=cuenta_resultado(partido=partido,prediccion=prediccion)
            break
    db.session.commit()
    
def contar_goleador(persona,goleador):
    partido=goleador.partido
    for prediccion in persona.predicciones:
        if prediccion.partido_id==partido.id:
            persona.puntuacion+=cuenta_goleador(partido=partido,prediccion=prediccion,goleador=goleador)
    db.session.commit()
    
def descontar_goleador(persona,goleador):
    partido=goleador.partido
    for prediccion in persona.predicciones:
        if prediccion.partido_id==partido.id:
            persona.puntuacion-=cuenta_goleador(partido=partido,prediccion=prediccion,goleador=goleador)
    db.session.commit()
@app.route('/')
def index():
    selecciones=Seleccion.query.all()
    partidos=Partido.query.all()
    predicciones=Prediccion.query.all()
    personas=Persona.query.all()
    return render_template('index.html',selecciones=selecciones,partidos=partidos,personas=personas)

@app.route('/persona/<int:id>')
def persona(id):
    persona = Persona.query.get_or_404(id)
    partidos = Partido.query.all()
    jugadores = Jugador.query.all()

    jugadores.sort(
        key=lambda j: (
            j.seleccion_id,
            prioridades.get(j.posicion, 999),
            j.nombre
        )
    )
    return render_template('persona.html', 
                           persona=persona, 
                           partidos=partidos, 
                           jugadores=jugadores)
    
@app.route('/predicciones/<int:id>',methods=['POST'])
def predicciones(id):
    partido_id=request.form["partido"]
    goles_local=request.form["goles_local"]
    goles_visitante=request.form["goles_visitante"]
    goleador_local_id=request.form["goleador_local"]
    goleador_visitante_id=request.form["goleador_visitante"]
    
    partido=Partido.query.get(partido_id)
    goleador_local=Jugador.query.get(goleador_local_id)
    goleador_visitante=Jugador.query.get(goleador_visitante_id)
    persona=Persona.query.get(id)
    prediccion=Prediccion(partido=partido,
                              goles_local=goles_local,
                              goles_visitante=goles_visitante,
                              goleador_local=goleador_local,
                              goleador_visitante=goleador_visitante,
                              persona=persona)
    db.session.add(prediccion)
    db.session.commit()
    contar_prediccion(persona=persona,prediccion=prediccion)
    return redirect(url_for('persona', id=id))
@app.route('/predicciones/borrar/<int:id>')
def borrar_prediccion(id):
    prediccion=Prediccion.query.get(id)
    persona=prediccion.persona
    aux=prediccion.persona_id
    descontar_prediccion(persona=persona,prediccion=prediccion)
    db.session.delete(prediccion)
    db.session.commit()
    return redirect(url_for('persona', id=aux))

@app.route('/cerveza/sumar/<int:id>')
def sumar_cerveza(id):
    persona=Persona.query.get(id)
    
    contar_cerveza(persona)
    return redirect(url_for('persona', id=id))
    
@app.route('/cerveza/restar/<int:id>')
def restar_cerveza(id):
    persona=Persona.query.get(id)
    
    descontar_cerveza(persona)
    return redirect(url_for('persona', id=id))

@app.route('/partidos',methods=['GET','POST'])
def partido():
    if request.method=="POST":
        local_id=request.form["local"]
        visitante_id=request.form["visitante"]
        
        partido=Partido(local_id=local_id,visitante_id=visitante_id,goles_local=999,goles_visitante=999)
        db.session.add(partido)
        db.session.commit()
        return redirect(url_for('partido'))
    else:
        partidos=Partido.query.all()
        selecciones=Seleccion.query.all()
        jugadores = Jugador.query.all()

        jugadores.sort(
            key=lambda j: (
                j.seleccion_id,
                prioridades.get(j.posicion, 999),
                j.nombre
            )
        )
        goleadores=Goleadores.query.all()
        return render_template('partidos.html',selecciones=selecciones,partidos=partidos,jugadores=jugadores,goleadores=goleadores)
    
@app.route('/partidos/modificar',methods=['POST'])
def partido_goles():
    id=request.form["partido_id"]
    goles_local=request.form["goles_local"]
    goles_visitante=request.form["goles_visitante"]
    
    partido=Partido.query.get(id)
    personas=Persona.query.all()
    if partido.goles_local !=999:
        for persona in personas:
            descontar_partido(persona=persona,partido=partido)
    partido.goles(goles_local,goles_visitante)
    db.session.commit()
    for persona in personas:
        contar_partido(persona=persona,partido=partido)
    return redirect(url_for('partido'))
@app.route('/goleadores',methods=['POST'])
def goleadores():
    partido_id=request.form["partido_id"]
    goleador=request.form["goleador"]
    cantidad=request.form["cantidad"]
    
    goleador=Goleadores(partido_id=partido_id,goleador_id=goleador,cantidad=cantidad)
    db.session.add(goleador)
    db.session.commit()
    personas=Persona.query.all()
    for persona in personas:
        contar_goleador(persona=persona,goleador=goleador)
    return redirect(url_for('partido'))

@app.route('/goleadores/borrar/<int:id>')
def borrar_goleador(id):
    goleador=Goleadores.query.get(id)
    personas=Persona.query.all()
    for persona in personas:
        descontar_goleador(persona=persona,goleador=goleador)
    db.session.delete(goleador)
    db.session.commit()
    return redirect(url_for('partido'))

if __name__=='__main__':
    app.run(debug=True)
