from flask import session,Flask,render_template,request,redirect,flash
from cs50 import SQL
from flask_session import Session
from flask_mail import Mail, Message
from datetime import datetime
import random
import os


app = Flask(__name__)

app.config['MAIL_SERVER'] = 'smtp.gmail.com' 
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'blackcustomercare07@gmail.com'
app.config['MAIL_PASSWORD'] = 'drsr nfhc imhf yxkc'
app.config['MAIL_DEFAULT_SENDER'] = 'blackcustomercare07@gmail.com'

mail = Mail(app)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///users.db")

def order_no():
     while True:
        order_id = random.randint(1000, 9999)
        existing = db.execute("select * from orders where order_number = ?", order_id)
        if not existing:
             return order_id

@app.context_processor
def inject_globals():
     if "user" not in session:
          session["user"] = "guest"

     if "cart" not in session:
        session["cart"] = {"item": 0 , "total": 0}
        
     session["cart"]["total"] = int(session["cart"]["item"]) * 1849
    
     return {"user": session["user"], "cart": session["cart"]}
    

@app.route("/", methods=["GET", "POST"])
def home():
       return render_template("home.html")

@app.route("/login", methods=["GET", "POST"])
def login():
        if request.method=="POST":
          action = request.form.get('action')
          username = request.form.get("username")
          password = request.form.get("password")
          email = request.form.get("email")
          if action == "reg":
               session.clear()
               rows = db.execute("select * from users where name=?", username)
               if len(rows) != 0:
                    return render_template("error.html", error="username already exists" , status="Error!")
               if not password:
                    return render_template("error.html",error="Please type in a password" , status="Error!")
               db.execute("insert into users(name,email,password) values(?,?,?)", username,email,password)
               session["user"] = username
               return redirect("/")

          if action == "login":
               session.clear()
               rows = db.execute("SELECT * FROM users WHERE name = ?", username)
               if len(rows) != 1:
                    return render_template("error.html",error="username doesn't exist" , status="Error!")
               if rows[0]["password"] != password:
                    return render_template("error.html",error="wrong password" , status="Error!")
               if rows[0]["password"]==password:
                    session["user"] = username
                    flash("Your are logged in!", "success")
                    return redirect("/")
               
          if action == "forgetpass":
               session.clear()
               rows = db.execute("select * from users where name=?", username)
               if len(rows) !=1:
                    return render_template("error.html",error="username is not registered" , status="Error!")
               subject = "Password Change"
               otp = random.randint(100000, 999999)
               session["otp"]= otp
               session["tempname"]= username
               message_body = "Your OTP is " + str(otp)

               try:
                    msg = Message(subject, recipients=[email], body=message_body)
                    mail.send(msg)
                    return render_template ("reset.html",msg="email sent to " + email)
               except Exception:
                    return render_template("error.html",error="could not send email to " + email , status="Error!")

                 
        return render_template("login.html")

@app.route("/logout")
def logout():
     session.clear()
     flash("You are logged out", "success")
     return redirect("/") 

@app.route("/products")
def products():
     return render_template("products.html")


@app.route('/verifyotp', methods=["GET", "POST"])
def verifyotp():
     if request.method == "POST":
          otp= request.form.get("otp")
          npass = request.form.get("npass")
          if int(otp) != session["otp"]:
               return render_template("error.html", error="OTP doesn't match" , status="Error!")
          if int(otp) == session["otp"]:
               db.execute("update users set password=? where name=?" , npass,session["tempname"])
               session.clear()
               return redirect("/login")

          
               
@app.route("/buy", methods=["GET", "POST"])
def buy():
     if request.method == "POST":
          amount = request.form.get("amount")
          stock = db.execute("select * from stock")
          if (int(amount) + int(session["cart"]["item"])) >  stock[0]["stock"]:
               flash("We dont have that much stock!!", "success")
               return redirect("/products")
          session["cart"]["item"]  = int(amount) + int(session["cart"]["item"])
          return redirect("/cart")

@app.route("/cart" , methods=["GET", "POST"])
def cart():
     if request.method == "POST":
          action = request.form.get("action")
          amount = request.form.get("quantity")
          stock = db.execute("select * from stock")
          if action == "clear":
               session["cart"]["item"]  = 0
               return redirect("/cart")
          if int(amount) >  stock[0]["stock"]:
               flash("We dont have that much stock!!", "success")
               return redirect("/cart")
          if action == "save":
               session["cart"]["item"]  = int(amount)
          if action == "ok" and int(amount)>0:
               session["cart"]["item"]  = int(amount)
               return redirect("/placeorder")
     
     return render_template("cart.html")

@app.route("/placeorder")
def placeorder():
     row= db.execute("select * from users where name=?", session["user"])
     if len(row)!=0:
          return render_template("placeorder.html" , row=row[0])

     return render_template("placeorder.html" , row=row)


@app.route("/confirm", methods=["GET", "POST"])
def confirm():
     if request.method == "POST":
          stock = db.execute("select * from stock")
          if int(session["cart"]["item"]) >  stock[0]["stock"]:
               flash("We dont have that much stock!!", "success")
               return redirect("/")
          subject = "Order Confirmation"
          email = request.form.get("email")
          name = request.form.get("name")
          address = request.form.get("address")
          order_day = datetime.now().strftime("%d-%m-%Y")
          order_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S" )
          phone = request.form.get("phone")
          order_number = order_no()
          try:
               msg = Message(subject, recipients=[email])
               msg.html = render_template("email.html", item=session["cart"]["item"], price=session["cart"]["total"], total=int(session["cart"]["total"])+100,name=name, time=order_day ,id=order_number,address=address)
               mail.send(msg)
          except Exception:
               return render_template("error.html",error="could not send email to " + email, status="Error!")

     db.execute("insert into orders(product_name,customer_name,email,address,date_time,status,phone,quantity,bill,order_number) values(?,?,?,?,?,?,?,?,?,?)", 
                     "Creatine",name,email,address,order_time, "pending",phone,session["cart"]["item"],session["cart"]["total"], order_number)
     db.execute("update stock set stock= stock-?" , session["cart"]["item"])
     flash("Your receipt has been sent to " + email, "success")
     return redirect("/")

@app.route("/editstock" , methods=["GET", "POST"])
def email():
     if request.method == "POST":
          add = request.form.get("amount")
          db.execute("update stock set stock=?" , add)
          return redirect("/admin")

@app.route("/contact", methods=["GET", "POST"])
def contact():
     if request.method == "POST":
          email= request.form.get("email")
          msg= request.form.get("message")
          name = request.form.get("name")
          db.execute("insert into msg(name,email,message) values(?,?,?)" , name,email,msg)
          flash("Your message have been received", "success")
          return redirect("/")

     return render_template("contact.html")


@app.route("/admin", methods=["GET", "POST"])
def admin():
     if session["user"] == "faiyaz" or session["user"] == "mufrad201":
          row = db.execute("select * from orders where status = 'pending' ")
          row2= db.execute("select * from orders where status = 'delivered' ")
          row3 = db.execute("select * from msg")
          row4 = db.execute("select * from orders where status = 'shipping' ")
          db.execute("update stock set active_orders=?,completed_orders=?,shipped_orders=?", len(row),len(row2),len(row4))
          stock = db.execute("select * from stock")
          return render_template("admin.html", row=row , stock=stock[0], row2=row2, row3=row3 , row4 =row4)
     else:
          return redirect("/login")

@app.route("/action" , methods=["GET", "POST"])
def action():
     if request.method == "POST":

          action= request.form.get("action")
          id= request.form.get("id")
          order= db.execute("select * from orders where id=?",id)
          if action == "remove":
               db.execute("delete from orders where id=?", id)
               db.execute("update stock set stock=stock+?", order[0]["quantity"])
               return redirect("/admin")
          if action == "removemsg":
               db.execute("delete from msg where id=? ", id)
               return redirect("/admin")
     
          db.execute("update orders set status = ? where id=?", action ,id)
          return redirect("/admin")
          
@app.route("/about")
def about():
     return render_template("about.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
