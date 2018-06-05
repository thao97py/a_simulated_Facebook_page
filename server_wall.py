from flask import Flask, render_template, request, redirect, session, flash, url_for
from mysqlconnection import MySQLConnector
import re
import md5

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
app = Flask(__name__)
app.secret_key = "j2489rcv98590v"
mysql = MySQLConnector(app, 'user_wall')

@app.route('/')
def index():
    if 'logged_id' in session:
        return redirect ('/wall')
    return render_template('index_wall.html')

@app.route('/register', methods=['POST'])
def register():
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    email = request.form['email']
    password = md5.new(request.form['password']).hexdigest()
    confirm_password = request.form['confirm_password']
    valid = True
#validate name input
    if len(first_name)<1:
        valid = False
        flash("First name contains only letters and at least 2 characters")
    if len(last_name)<1:
        valid = False
        flash("Last name contains only letters and at least 2 characters")
 #validate email input   
    if not EMAIL_REGEX.match(email):
        valid = False
        flash("Email is invalid")
    if email=='':
        valid = False
        flash("Email cannot be blank!")
    query = "SELECT * from users WHERE email =:email"
    email_register =mysql.query_db(query, {'email':email})
    if len(email_register) > 0:
        valid = False
        flash("Email is already regsitered!")
# validate passowrd input
    if len(password)<8:
        valid = False
        flash("password includes at least 8 characters")
    if confirm_password != request.form['password']:
        valid = False
        flash("passwords don't match")
#decide whether ot not user succeeded registering
    if not valid:
        return redirect('/')
    else:
        query = "INSERT INTO users (first_name, last_name, email, password, created_at, updated_at) VALUES (:first_name, :last_name, :email, :password, NOW(), NOW())"
        data = {'first_name':first_name,
                'last_name' : last_name,
                'email': email,
                'password': password}
        mysql.query_db(query, data)
        flash("You has successfully registered and let's log in!")
        return redirect('/')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        valid = True
        user_email = request.form['user_email']
       
        if (len(user_email) <1 or len(request.form['user_password']) <1):
            valid =False
            flash("Your email and password cannot be blank! ")
        if not valid:
            return redirect('/')
        else:
            user_password = md5.new(request.form['user_password']).hexdigest()
            query = "SELECT * FROM users WHERE email= :email"
            user_data = mysql.query_db(query, {'email':user_email})
            if len(user_data) > 0:
                user = user_data[0]
                if user['password'] == user_password:
                    session['logged_id'] = user['id']
                    return redirect('/wall')
            flash("Either your password or email is not correct!")
            return redirect('/')
    elif ( request.method =='GET'):
        return redirect('/clear')

@app.route('/wall')
def wall_page():
    query_1 = "SELECT CONCAT(users.first_name,' ', users.last_name) AS name, users.id, messages.message, messages.id AS message_id, DATE_FORMAT(messages.created_at,'%M %D, %Y %H:%i' ) AS date, messages.updated_at FROM users JOIN messages ON users.id = messages.user_id ORDER BY date DESC"
    all_messages = mysql.query_db(query_1)
    
    query_2 = "SELECT * FROM users WHERE id = :id"
    user = mysql.query_db(query_2, { 'id': session['logged_id'] })
    
    query_3 = "SELECT messages.id, comments.comment, comments.user_id, DATE_FORMAT(comments.created_at, '%M %D, %Y %H:%i') AS date FROM messages JOIN comments ON messages.id = comments.message_id "
    all_comments = mysql.query_db(query_3 )
    
    query_4 = "SELECT CONCAT(users.first_name,' ', users.last_name) AS name, comments.message_id, comments.comment, users.id FROM users JOIN comments ON users.id = comments.user_id"
    user_comment = mysql.query_db( query_4)
    
    return render_template('posting_wall.html', all_messages= all_messages, user= user, all_comments= all_comments, user_comment=user_comment)

@app.route('/posting', methods=['POST'])
def posting_message():
    if  request.form['message'] !='' :
        query = "INSERT INTO messages (message, created_at, updated_at, user_id) VALUES (:message, NOW(), NOW(), :user_id)"
        mysql.query_db(query, {'message': request.form['message'], 'user_id':session['logged_id']})
    return redirect('/wall')

@app.route('/comment', methods=['POST'])
def posting_comment():
    query = "INSERT INTO comments (comment, created_at, updated_at, user_id, message_id) VALUES (:comment, NOW(), NOW(), :user_id, :message_id)"
    data = { 'comment': request.form['comment'],
            'user_id': session['logged_id'], 
            'message_id':request.form['message_id']}
    mysql.query_db(query, data)
    return redirect('/wall')

@app.route('/clear')
def clear_session():
    session.clear()
    return redirect('/')

if __name__ =='__main__':
    app.run(debug = True)
