from flask import Flask, request, render_template, redirect, url_for, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
import sqlite3 
import socket

app = Flask(__name__)


app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config["SQLALCHEMY_DATABASE_URI"]= "sqlite:///blog.sqlite3"
app.config['SECRET_KEY'] = 'secret'

db = SQLAlchemy(app)


class Post(db.Model):
    __tablename__ = 'post'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    content = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(50), nullable=False)
    
    def __init__(self, title, content, author):
        self.title = title
        self.content = content
        self.author = author
        
        
    # função para converter cada objeto de post em um  dicionario json ==> (para REST-API)    
    def to_dict(self): 
        result = {}
        for key in self.__mapper__.c.keys():
            if getattr(self, key) is not None:
                result[key] = str(getattr(self, key))
            else:
                result[key] = getattr(self, key)
        return result
    


# Rata para estudo
@app.route('/') #ROTA VULNERAVEL PARA XSS
def home():
    nome = request.args.get('nome')
    return "<h2 <style>Olá {}</h2>".format(nome)


# Rota para estudo de cookie
@app.route('/example')
def example():
    test = request.args.get("test")
    response = make_response("Ola{}".format(test))
    response.set_cookie("info", "exemplo de sessao de login", httponly=True) #setando um cookie para teste
    return response # flasg httponly ==> block de manipulação de cookies pelo DOM da pagina
    # outra forma eh configurar um CSP
    
# Metodo que carrega antes de fazer o request 
# Segurança nos cabeçalhos
@app.after_request
def add_header(response):
    response.headers["X-Drame-Options"] = "Deny" # Block de gerador de iframe de site
    response.headers["Content-Security-Policy"] = "script-src 'none'" # block de execut de script na pagina
    response.headers["Access-Control-Allow-Origin"] = "*" # acesso total do conteudo por outro site podendo tambem de finir um dominio para ter acesso(Headers PERIGOSO)
    response.headers["Access-Control-Allow-Credentials"] = "true" # PERIGOSO, para dar acesso a requisiçoes com as credenciais autenticadas
    return response   

# ROTA PRINCIPAL do BLOGGER
@app.route('/index') #VULNERABILIDADE XSS CORRIGIDA, COM A CHAMADA DE TEMPLATE
def index():
    posts = Post.query.all()
    return render_template("teste.html", posts=posts)


@app.route('/post/add', methods=["POST"])
def add_post():
    try:        
        form = request.form
        post = Post(title=form['title'], content=form['content'], author=form['author'])
        db.session.add(post)
        db.session.commit()
    except Exception as error:
        print("Error", error)
        
    return redirect(url_for("index"))


@app.route('/post/<id>/del')
def delete_post(id):
    try:        
        post = Post.query.get(id)
        db.session.delete(post)
        db.session.commit()
    except Exception as error:
        print("Error", error)
        
    return redirect(url_for("index"))
    
    
@app.route('/post/<id>/edit', methods=["POST", "GET"])
def edit_post(id):
    if request.method == "POST":
        try:
            post = Post.query.get(id)        
            form = request.form
            post.title = form["title"]
            post.content = form["content"]
            post.author = form["author"]
            db.session.commit()
        except Exception as error:
            print("Error", error)
            
        return redirect(url_for("index")) 
    else:
        try:
            post = Post.query.get(id)        
            return render_template("edit.html", post=post) 
        except Exception as error:
            print("Error", error)
            
    return redirect(url_for("index"))






# REST-API - PARA CRUD

@app.route('/api/index') #VULNERABILIDADE XSS CORRIGIDA, COM A CHAMADA DE TEMPLATE
def api_index():
    try:
        posts = Post.query.all()
        return jsonify([post.to_dict() for post in posts])
        # loop para cada post com list conprehencion
        #jsonify para serializaçao  objeto para json
    except Exception as error:
        print("Error", error)
        
    return jsonify([])
         
    
@app.route('/api/post', methods=["PUT"])
def api_add_post():
    try:        
        data = request.get_json()
        post = Post(title=data['title'], content=data['content'], author=data['author'])
        db.session.add(post)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as error:
        print("Error", error)
        
    return jsonify({"success": False})


@app.route('/api/post/<id>', methods=["DELETE"])
def api_delete_post(id):
    try:        
        post = Post.query.get(id)
        db.session.delete(post)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as error:
        print("Error", error)
        
    return jsonify({"success": False})
    
    
@app.route('/api/post/<id>', methods=["PUT"])
def api_edit_post(id):
    try:
        post = Post.query.get(id)        
        data = request.get_json()
        post.title = data["title"]
        post.content = data["content"]
        post.author = data["author"]
        db.session.commit()
        return jsonify({"success": True})
    except Exception as error:
        print("Error", error)
            
    return jsonify({"success": False})

app.app_context().push()



# port = 5000
# debug = True
# host = "127.0.0.1"
   
db.create_all()
app.run(debug=True)