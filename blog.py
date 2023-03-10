from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps

def login_required(f):
     @wraps(f)
     def decorated_function(*args, **kwargs):
         if "logged_in" in session:
             return f(*args, **kwargs)
         else:
             flash("Bu Sayfayı Görüntülemek İçin Lütfen Giriş Yapınız.","danger")
             return redirect(url_for("login"))
     return decorated_function
#Kayıt Formu
class RegisterForm(Form):
    name = StringField("İsim Soyisim",validators=[validators.Length(min=4,max=30),(validators.DataRequired("Lütfen Doldurunuz..."))])   
    username = StringField("Kullanıcı Adı",validators=[validators.Length(min=5,max=36),(validators.DataRequired("Lütfen Doldurunuz..."))])
    email = StringField("Email Adresi",validators=[validators.Email(message = "Lütfen Geçerli Bir Email Giriniz...")])
    password = PasswordField("Parola",validators=[validators.DataRequired(message = "Lütfen bir parola belirleyiniz..."),validators.EqualTo(fieldname = "confirm",message = "Parolanız Uyuşmuyor...")])
    confirm = PasswordField("Parola Doğrulama")

class LoginForm(Form):
    username = StringField("Kullanıcı Adı")
    password = PasswordField("Parola")  


app= Flask(__name__)
app.secret_key= "RTK Blog"

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "rtkblog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)


@app.route("/i")
def layout():
    return render_template("layout.html")

#Anasayfa
@app.route("/Anasayfa")
def index():
    return render_template("home.html")

@app.route("/")
def b():
    return render_template("b.html")    

#Hakkımda
@app.route("/Hakkımda")
def about():
    return render_template("about.html") 

#Makaleler
@app.route("/Makaleler")
def articles():
    cursor = mysql.connection.cursor()
    
    sorgu = "Select * From articles"
    
    result = cursor.execute(sorgu)
    
    if result > 0:
        articles = cursor.fetchall()
        
        return render_template("articles.html", articles = articles)
    else:
        return render_template("articles.html")
######################################################################################################################
#Makale İçerikleri
@app.route("/Makaleler/<string:id>")
def article(id):
    
    cursor = mysql.connect.cursor()
    
    sorgu = "Select * from articles where id = %s"
    
    result = cursor.execute(sorgu,(id,))
    
    if result > 0:
        article = cursor.fetchone()
        return render_template("article.html", article = article)
    else:
        return render_template("article.html")
    
#İletişim
@app.route("/İletişim")
def contact():
    return render_template("contact.html")  

#Kontrol Paneli
@app.route("/Kontrol Paneli")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    
    sorgu = "Select * From articles where author = %s"
    
    result = cursor.execute(sorgu,(session["username"],))
    
    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html",articles = articles)
    else:
        return render_template("dashboard.html")

#Kayıt Olma
@app.route("/Kaydol",methods = ["GET","POST"])
def register():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():
        name=form.name.data
        username=form.username.data
        email=form.email.data
        password=sha256_crypt.encrypt(form.password.data)
        cursor=mysql.connection.cursor()
        sorgu = "Insert into users(name,email,username,password)  VALUES(%s,%s,%s,%s)"
        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit()
        cursor.close()
        flash("Başarılıyla Kayıt Oldunuz...","success")
        return redirect(url_for("login"))
        
    else:
        return render_template("register.html",form = form)        

#Giriş
@app.route("/Giriş",methods = ["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()

        sorgu = "Select * From  users where username = %s"

        result = cursor.execute(sorgu,(username,))

        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered,real_password):
                flash("Başarıyla Giriş Yapıldı","success")

                session["logged_in"] = True
                session["username"] = username
                return redirect(url_for("index"))
            else:
                flash("Parola Hatalı...","danger")
                return redirect(url_for("login"))
        else:
            flash("Kullamıcı Adı Hatalı...","danger")
            return redirect(url_for("login"))                                                              
    return render_template("login.html", form = form)

#Makale Ekleme
@app.route("/Makale Ekle",methods = ["GET","POST"])
def addarticle():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data 
        
        cursor = mysql.connection.cursor()
        
        sorgu = "Insert into articles(title,author,content) VALUES(%s,%s,%s)"
        
        cursor.execute(sorgu,(title,session["username"],content))
        
        mysql.connection.commit()
        
        cursor.close()
        
        flash("Makale Başarıyla Eklendi","success")
        return redirect(url_for("dashboard"))
        
    return render_template("addarticle.html",form = form)

#Makale Silme
@app.route("/Sil/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    
    sorgu = "Select * from articles where author = %s and id = %s"
    
    result = cursor.execute(sorgu,(session["username"],id))
    
    if result > 0:
        sorgu2 = "Delete from articles where id = %s"
        
        cursor.execute(sorgu2,(id,))
        
        mysql.connection.commit()
        
        return redirect(url_for("dashboard"))
    
    else:
        flash("Böyle Bir Makale Yok veya Bu İşleme Yetkiniz Yok...","danger")
        return redirect(url_for("index"))

#Makale Güncelleme
@app.route("/Güncelle/<string:id>",methods = ["GET","POST"])
def update(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        
        sorgu = "Select * from articles where id = %s and author = %s"
        result = cursor.execute(sorgu,(id,session["username"]))
        
        if result == 0:
            flash("Böyle Bir Makale Yok veya Bu İşleme Yetkiniz Yok...","danger")
            return redirect(url_for("index"))
        
        else:
            article = cursor.fetchone()
            form = ArticleForm()
            
            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update.html", form = form)
            
    else:
        #POST REQUEST
        form =  ArticleForm(request.form)
        
        newTitle = form.title.data
        newContent = form.content.data
        
        sorgu2 = "Update articles Set title = %s,content = %s where id = %s"
        
        cursor = mysql.connection.cursor()
        
        cursor.execute(sorgu2,(newTitle,newContent,id))
        
        mysql.connection.commit()
        
        flash("Makale Başarıyla Güncellendi","success")
        
        return redirect(url_for("dashboard"))

#Arama Motoru
@app.route("/Ara",methods = ["GET","POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("articles"))
    
    else:
        keyword = request.form.get("keyword")
        
        cursor = mysql.connection.cursor()
        
        sorgu = "Select * form articles where title like '% keyword %' "
        
        result = cursor.execute(sorgu)
        
        if result == 0:
            flash("Maalesef Böyle Bir Makale Bulunmuyor...","warning")
            return redirect(url_for("articles"))
        else:
            articles = cursor.fetchall()
            
            return render_template("articles.html",articles = articles)

# Makale  Form 
class ArticleForm(Form):
    title = StringField("Makale Başlığı",validators=[validators.Length(min=5,max=50)])
    content = TextAreaField("Makale İçeriği", validators=[validators.Length(min=10)])
    
#Çıkış
@app.route("/Çıkış")
def logout():
    session.clear()
    return redirect(url_for("index")) 
if __name__ == "__main__":
    app.run(debug=True)