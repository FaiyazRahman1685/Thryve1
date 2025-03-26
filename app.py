from flask import session,Flask,render_template,request,redirect,flash,Response
from cs50 import SQL
from flask_session import Session
from flask_mail import Mail, Message
import random
import os
import csv
import io
from datetime import datetime, timezone
from zoneinfo import ZoneInfo 
from flask_compress import Compress

app = Flask(__name__)
Compress(app)

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

@app.route('/download_csv', methods=["GET", "POST"])
def download_csv():
    # Query data
    if request.method == "POST":
     rows = db.execute("SELECT * FROM orders")

     # Create an in-memory file
     output = io.StringIO()
     writer = csv.writer(output)

     # Write header row (column names)
     if rows:
          writer.writerow(rows[0].keys())

     # Write data rows
     for row in rows:
          writer.writerow(row.values())

     # Create a response object
     output.seek(0)
     response = Response(output.getvalue(), content_type="text/csv")
     response.headers["Content-Disposition"] = "attachment; filename=data.csv"
     
     return response

def get_price(product):
     creatine_price = db.execute("select * from products where name=?" , product)
     return int(creatine_price[0]["price"])

def get_stock(product):
     stock = db.execute("select * from products where name=?" , product)
     return int(stock[0]["stock"])

def order_no():
     while True:
        order_id = random.randint(1000, 9999)
        existing = db.execute("select * from orders where order_number = ?", order_id)
        if not existing:
             return order_id
        
@app.before_request
def ensure_session_defaults():
    session.setdefault("user", "guest")
    session.setdefault("cart", {"items": ['creatine300g', 'creatine600g'], "amounts" : [0,0], "price": [], "total": 0})
    session["cart"]["price"] = [get_price(item) for item in session["cart"]["items"]]
    session["cart"]["total"] = 0
    for index,amounts in enumerate(session["cart"]["amounts"]):
         session["cart"]["total"] += amounts * session["cart"]["price"][index]


@app.context_processor
def inject_globals():
    totalitem = 0
    for amounts in session["cart"]["amounts"]:
         totalitem += amounts
    return {"user": session["user"], "cart": session["cart"], "totalitem":totalitem}
    

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
               rows = db.execute("select * from users where name=?", username)
               if len(rows) != 0:
                    return render_template("error.html", error="username already exists" , status="Error!")
               if not password:
                    return render_template("error.html",error="Please type in a password" , status="Error!")
               db.execute("insert into users(name,email,password) values(?,?,?)", username,email,password)
               session.clear()
               session["user"] = username
               return redirect("/")

          if action == "login":
               rows = db.execute("SELECT * FROM users WHERE name = ?", username)
               if len(rows) != 1:
                    return render_template("error.html",error="username doesn't exist" , status="Error!")
               if rows[0]["password"] != password:
                    return render_template("error.html",error="wrong password" , status="Error!")
               if rows[0]["password"]==password:
                    session.clear()
                    session["user"] = username
                    flash("Your are logged in!", "success")
                    return redirect("/admin")
               
          if action == "forgetpass":
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

@app.route("/logout", methods=["GET", "POST"])
def logout():
     if request.method == "POST":
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
               flash("Password changed", "success")
               session.clear()
               return redirect("/login")

          
               
@app.route("/buy", methods=["GET", "POST"])
def buy():
     if request.method == "POST":
          amount = request.form.get("amount")
          product = int(request.form.get("product"))
          if (int(amount) + int(session["cart"]["amounts"][product])) >  get_stock(session["cart"]["items"][product]):
               flash("We dont have that much stock!!", "success")
               return redirect("/products")
          session["cart"]["amounts"][product]  = int(amount) + session["cart"]["amounts"][product]
          return redirect("/cart")

@app.route("/cart" , methods=["GET", "POST"])
def cart():
     if request.method == "POST":
          action = request.form.get("action")
          if action == "clear":
               session["cart"]["amounts"]  = [0,0]
               flash("Cart cleared", "success")
               return redirect("/cart")
          for key,value in request.form.items():
               if key.startswith('quantity-'):  # Ensure it's a quantity field
                    index = int(key.split('-')[1])  # Extract the index from the key
                    new_quantity = int(value)  # Get the new quantity
                    if new_quantity> get_stock(session["cart"]["items"][index]):
                         flash("We dont have that much stock!!", "success")
                         return redirect("/cart")
                    if new_quantity > -1:
                         session["cart"]['amounts'][index] = new_quantity 
          totalitem = 0
          for amounts in session["cart"]["amounts"]:
               totalitem += amounts
          if action == "save":
               return redirect("/cart") 
          if action == "ok" and totalitem == 0:
               flash("Can't proceed with 0 items on cart", "error")
               return redirect("/cart")
          if action == "ok" and totalitem>0:
               return redirect("/placeorder")
          
     
     return render_template("cart.html")

@app.route("/placeorder")
def placeorder():
     return render_template("placeorder.html")


@app.route("/confirm", methods=["GET", "POST"])
def confirm():
     if request.method == "POST":
          subject = "Order Confirmation"
          email = request.form.get("email")
          name = request.form.get("name")
          address = request.form.get("address")
          utc_time = datetime.now(timezone.utc)
          gmt6_time = utc_time.astimezone(ZoneInfo("Asia/Dhaka"))
          order_day = gmt6_time.strftime("%d-%m-%Y")
          order_time = gmt6_time.strftime("%d-%m-%Y %H:%M:%S" )
          phone = request.form.get("phone")
          order_number = order_no()
          try:
               msg = Message(subject, recipients=[email])
               msg.html = render_template("email.html", name=name, time=order_day ,id=order_number,address=address)
               mail.send(msg)
          except Exception:
               return render_template("error.html",error="could not send email to " + email, status="Error!")

          for index,amount in enumerate(session["cart"]["amounts"]):
               if amount >  get_stock(session["cart"]["items"][index]):
                    flash("We dont have that much stock!!", "success")
                    return redirect("/")
               if amount>0:
                    db.execute("insert into orders(product_name,customer_name,email,address,date_time,status,phone,quantity,bill,order_number) values(?,?,?,?,?,?,?,?,?,?)", 
                                   session["cart"]["items"][index],name,email,address,order_time, "pending",phone,amount,session["cart"]["total"]+100, order_number)
                    db.execute("update products set stock= stock-? where name=?" ,amount,session["cart"]["items"][index] )
                    
          flash("Your receipt has been sent to " + email, "success")
          return redirect("/")

@app.route("/editstock" , methods=["GET", "POST"])
def email():
     if request.method == "POST":
          action = request.form.get("action")
          add = request.form.get("amount")
          id = request.form.get("id")
          if action=="editstock":
               db.execute("update products  set stock=? where name=?" ,add, id)
          if action=="editprice":
             db.execute("update products set price=? where name=?" ,add, id)             
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
          row5= db.execute("select * from products")
          db.execute("update stock set active_orders=?,completed_orders=?,shipped_orders=?", len(row),len(row2),len(row4))
          stock = db.execute("select * from stock")
          return render_template("admin.html", row=row , stock=stock[0], row2=row2, row3=row3 , row4 =row4, row5=row5)
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
               db.execute("update products set stock=stock+? where name=?", order[0]["quantity"],order[0]["product_name"])
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

