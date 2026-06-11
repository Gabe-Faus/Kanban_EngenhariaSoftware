from io import BytesIO

from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
import psycopg2
from psycopg2 import sql

from app.db.connection import Database
from app.services.raia_service import *
from app.services.cartao_service import *
from app.services.quadro_service import *
from app.services.usuario_service import *
from app.services.usuariocartao_service import *
from app.services.usuarioquadro_service import *

app = Flask(
    __name__,
    template_folder='app/templates',
    static_folder='app/static'
)

@app.route('/')
def login():
    return render_template('login.html')


@app.errorhandler(404)
def pagina_nao_encontrada(error):
    return redirect(url_for('inicio'))

if __name__ == '__main__':
    app.run(debug=True)