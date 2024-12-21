from flask import Flask,render_template,redirect,url_for,request,flash,session
from flask_session import Session
import mysql.connector
from otp import genotp
from cmail import sendmail
import os
from datetime import datetime
from  datetime import date
app=Flask(__name__)
app.config['SESSION_TYPE']='filesystem'
Session(app)
app.secret_key = 'a8b9c2d40f214e7a8d1d29a04a3c5f7e9b1d6c0a9f2b3a4e'
#for aws quries
user=os.environ.get('RDS_USERNAME')
db=os.environ.get('RDS_DB_NAME')
password=os.environ.get('RDS_PASSWORD')
host=os.environ.get('RDS_HOSTNAME')
port=os.environ.get('RDS_PORT')
with mysql.connector.connect(host=host,password=password,db=db,user=user,port=port) as conn:
    cursor=conn.cursor()
    cursor.execute("CREATE TABLE if not exists emp_registration(emp_id varchar(20) NOT NULL,first_name varchar(50) NOT NULL,last_name varchar(50) NOT NULL,designation varchar(20) NOT NULL,email varchar(50) NOT NULL,password varchar(20) NOT NULL,address text,phone_number varchar(10) NOT NULL,department varchar(20) NOT NULL,salary int unsigned NOT NULL,gender enum('Male','Female','Others') DEFAULT NULL,PRIMARY KEY (emp_id),UNIQUE KEY email (email))")
    cursor.execute("CREATE TABLE if not exists emp_records(emp_id varchar(20) NOT NULL,username varchar(50) DEFAULT NULL,date date DEFAULT NULL,checkin_time time DEFAULT NULL,checkout_time time DEFAULT NULL,KEY emp_id (emp_id),CONSTRAINT emp_records_ibfk_1 FOREIGN KEY (emp_id) REFERENCES emp_registration (emp_id))")
    cursor.execute("CREATE TABLE if not exists otp(OID int NOT NULL AUTO_INCREMENT,Email varchar(80) DEFAULT NULL,otp varchar(9) DEFAULT NULL,PRIMARY KEY (OID))")
    cursor.execute("CREATE TABLE if not exists work_status(emp_id varchar(20) NOT NULL,date datetime DEFAULT CURRENT_TIMESTAMP,work_status text NOT NULL,KEY emp_id(emp_id),CONSTRAINT work_status_ibfk_1 FOREIGN KEY (emp_id) REFERENCES emp_registration(emp_id))")

mydb=mysql.connector.connect(host=host,password=password,db=db,user=user,port=port)


@app.route('/')
def welcome():
    return render_template('welcome.html')
@app.route("/admin",methods = ['GET','POST'])
def admin():
     if request.method == 'POST':
          #frontend data
          email = request.form['email']
          password = request.form['password']
          scecurty = request.form['passcode']
          print("frontent data",email,password,scecurty)
          if email=='sudharanikancherla1@gmail.com' and password=='asd@123' and scecurty =='123#' :        
        #database connection
        #   cursor=mydb.cursor(buffered=True)
        #   cursor.execute('select email,username,password,passcode from admin')#already inserted values in the table
        #   data=cursor.fetchone()
        #   cursor.close()
          
        #   print("mysql data",data[0],data[2],data[3])
        #   if data[0] == email and data[2]==password and data[3]==scecurty:
            print('Login successfully')
            return redirect(url_for('admin_dashboard'))
          else:
                flash('Invalid credentials, please try again')
                return redirect(url_for('admin'))          
     return render_template('adminlogin.html')
#admin_dashboard route
@app.route('/admin_dashboard')
def admin_dashboard():
     return render_template('admin_dashboard.html')

#emp_sign route
@app.route('/emp_signup',methods=['GET','POST'])
def emp_signup():
     if request.method=='POST':
          email = request.form.get('email')
          print(email)
          #database connection backend
          cursor=mydb.cursor(buffered=True)
          cursor.execute('select * from emp_registration where email=%s',(email,))
          data1=cursor.fetchone()
          cursor.close()
          if data1:
               flash('You Are Already Registered.Please Login With Valid Credentials.')
               return render_template('emp_login.html')
               
          else: 
               print(request.form)
               #frontend data
               emp_id=request.form.get('emp_id')
               first_name=request.form.get('first_name')
               last_name=request.form.get('last_name')
               desig=request.form.get('designation')
               emp_email=request.form.get('email')
               pwd=request.form.get('password')
               addr=request.form.get('address')
               phone_number=request.form.get('phone_number')
               dep=request.form.get('department')
               sal=request.form.get('salary')
               gen=request.form.get('gender')
               #full_name concate
               full_name=f'{first_name}{last_name}'
               #insert data emp_reg table
               cursor=mydb.cursor(buffered=True)
               cursor.execute('insert into emp_registration (emp_id,first_name,last_name,designation,email,password,address,phone_number,department,salary,gender) values(concat("EMP00",%s),%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(emp_id,first_name,last_name,desig,emp_email,pwd,addr,phone_number,dep,sal,gen))
               mydb.commit()
               cursor.close()
               #sending message to email
               subject='Employee Registration Verification'
               body=f'Hi {first_name}{last_name},\t Hypernova IT Solutions Welcomes you.\nYour Registration is completed Successfully.\nThank You for Enrolling.'
               sendmail(to=email,subject=subject,body=body)
               flash('Registration is successful.','success')
          return render_template('emp_login.html')  # Redirect to the login page after successful signup

    # If it's a GET request, just render the signup form
     return render_template('emp_signup.html')

#emp_list
@app.route('/emp_list')
def emp_list():
    cursor = mydb.cursor(buffered=True,dictionary=True)
    cursor.execute('select * from emp_registration')
    data = cursor.fetchall()
    cursor.close()
    # print("Fetched Data:", data)  
    return render_template('emp_list.html',emp_data = data)

#view route
@app.route('/view_details/<emp_id>')
def view_details(emp_id):
    print(emp_id)
    cursor = mydb.cursor(buffered=True)
    cursor.execute('select * from emp_records where emp_id = %s',(emp_id,))
    view_data = cursor.fetchall()
    cursor.close()
    print(view_data)
     # Check if no records are found
    if not view_data:
        message = "User has not checked in yet."
        cursor = mydb.cursor(buffered=True)
        cursor.execute('select first_name, last_name from emp_registration where emp_id = %s',(emp_id,))
        data = cursor.fetchone()
        username = f'{data[0]} {data[1]}'
        print(username)
        cursor.close()
     
        view_data = [(emp_id, username, 'Not Check In', 'Not Checked In', 'Not Checked Out')] 
        print(view_data)
        return render_template('view_details.html', message=message,view_data = view_data)
        
    return render_template('view_details.html',view_data = view_data)
#search route
@app.route('/search',methods=['GET','POST'])
def search():
    query = ""  # Ensure query is always defined
    results = []  # Default to an empty list of results
    if request.method == 'POST':
        query = request.form.get("search", "").strip() 
        cursor = mydb.cursor(buffered = True)
        
        # Check if the query is not empty
        if query:  # Check if the query is not empty (ignoring whitespace)
        # SQL query to search the database
            print(query)
            search_query = "SELECT emp_id, first_name,last_name, designation, email, department FROM emp_registration WHERE emp_id LIKE %s OR first_name LIKE %s OR last_name LIKE %s OR designation LIKE %s OR email LIKE %s OR department LIKE %s"
            cursor.execute(search_query, (f"%{query}%", f"%{query}%",f"%{query}%",f"%{query}%",f"%{query}%", f"%{query}%"))
            results = cursor.fetchall()  # Fetch all matching rows
            cursor.close()
            print(results)
            
    # else:
    #     results = []  # Empty list for no results or no query

    # Pass the query and results to the template
    return render_template("search.html", query=query, results=results)


@app.route('/emp_login',methods=['GET','POST'])
def emp_login():
     if  'email' in session:
        
        return redirect(url_for('emp_dashboard'))
     else:
          if request.method=='POST':
               #get data from the form
               email=request.form.get('email') # no chance to show error to user
               pwd=request.form.get('password')
               print("frontend data",email,pwd)
               if not email or not pwd: 
                    flash("All fields (Email,pwd) are required","error")
                    return render_template('emp_login.html') # showing the same form with the error
               #database connection for checking  if the email exists in the emp_reg table
               cursor=mydb.cursor(buffered=True)
               cursor.execute('select * from emp_registration where email=%s',(email,))
               emp_record=cursor.fetchone()
               cursor.close()
               print("mysql data",emp_record)
          
               if emp_record:
                    #Email exists,now validate pwd
                    if emp_record[5]== pwd:
                         #valid the given credentials
                         session['email']=email #creating session
                         return redirect(url_for('emp_dashboard'))
                    else:
                         #Invalid password
                         flash("Invalid password.Please try again.","error")
                         # print(' Employee Login successfully')
                         # flash('Employee Login Successfully')
                         # return redirect(url_for('emp_dashboard'))
                         return redirect(url_for('welcome'))
               else:
                  flash("Email not registered ,Please contact Your Admin to get Register.","error") 
               #    return render_template('emp_login.html')   
     return render_template('emp_login.html')
     
#emp_dashboard
@app.route('/emp_dashboard')
def emp_dashboard():
     if session.get('email'):
          email=session.get('email')
          #fetching the username in the database
          cursor=mydb.cursor(buffered=True)
          cursor.execute('select first_name,last_name from emp_registration where email=%s',(email,))
          username=cursor.fetchone()
          if username:
               username=f'{username[0]}{username[1]}'
               cursor.close()
               return render_template('emp_dashboard.html',username=username)
          else:
               flash("username not found in Database...! update your Profile")
     else:
          flash('You are not logged in.')
          return redirect(url_for('emp_login'))
    
     # flash('Login successfully ,Welcome to  emp_dashboard')
     return render_template('emp_dashboard.html',username=username)

#workstatus route
@app.route('/work_status',methods=['GET','POST'])
def work_status():
    if 'email' not in session:
        flash('To submit the work status you need to login.')
        return redirect(url_for('emp_login'))
    else:
        email=session.get('email')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select emp_id from emp_registration where email=%s',(email,))
        emp_id=cursor.fetchone()[0]
        #this will work when emp check-in and updated his work_status
        today = date.today().strftime('%Y-%m-%d')  # Get today's date in 'YYYY-MM-DD' format
        cursor.execute('SELECT * FROM emp_records WHERE emp_id = %s AND date = %s', (emp_id, today))
        checkin_record = cursor.fetchone()
        
        if not checkin_record:
            flash("Check in before you submit your work status.")
            return redirect(url_for('emp_dashboard'))  # Redirect to dashboard if no check-in today
        if request.method=='POST':
            work_status=request.form.get('work_status')
            #insert the work_status describtion in the work_status table
            cursor=mydb.cursor(buffered=True)
            cursor.execute('insert into work_status(emp_id,work_status) values(%s,%s)',(emp_id,work_status))
            mydb.commit()
            cursor.close()
            flash('Work Description Submitted Successfully')
            return redirect(url_for('emp_dashboard'))
        
#logout route
@app.route('/logout')
def logout():
     #to clear the user session
     session.pop('email',None) #remove the "email from the session"
     flash('Logged out Successfully.','success')
     return redirect(url_for('welcome'))
#update profile route
@app.route('/update_profile',methods=['GET','POST'])
def update_profile():
    if session.get('email'):
        # Check if user is logged in (session email exists)
        email = session.get('email')
        if not email:
            # If no email in session, redirect to login page
            flash("You must be logged in to update your profile.", "error")
            return redirect(url_for('emp_login'))
        # Get updated data from the form
            
        if request.method == 'POST':
            emp_id = request.form.get('emp_id')
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            designation = request.form.get('designation')
            address=request.form.get('address')
            phone_number = request.form.get('phone_number')
            #password = request.form.get('password')
            address = request.form.get('address')
            department = request.form.get('department')
            salary = request.form.get('salary')
            #gender = request.form.get('gender')
        # Connect to the database
            cursor = mydb.cursor()
            fullname = f'{first_name} {last_name}'
            print(fullname)
            cursor.execute('update emp_registration set emp_id = %s,first_name=%s,last_name=%s,designation=%s,address=%s,phone_number=%s,department=%s,salary=%s where email=%s',(emp_id,first_name,last_name,designation,address,phone_number,department,salary,email))
            mydb.commit()
            cursor.close() 
        # Redirect to login page with a success message
            flash("Your profile has been updated successfully. Please login with updated credentials.", "success")
            return redirect(url_for('emp_login'))  # Assuming 'login' is the name of your login route

        cursor = mydb.cursor(buffered=True)
        cursor.execute('select * from emp_registration where email = %s',(email,))
        emp_data = cursor.fetchone()
        cursor.close()
        if emp_data:
            return render_template('update_profile.html', emp_data=emp_data)
        else:
            flash("No profile data found for the current user.", "error")
            return redirect(url_for('emp_login'))



#checkin route
@app.route('/checkin', methods=['GET', 'POST'])
def checkin():
    if session.get('email'):
        email = session.get('email')

        # Get Employee Details
        cursor = mydb.cursor(buffered=True)
        cursor.execute('SELECT emp_id, first_name, last_name FROM emp_registration WHERE email = %s', (email,))
        result = cursor.fetchone()

        if not result:
            flash('Employee not found', 'error')
            return redirect(url_for('emp_login'))

        emp_id = result[0]
        username = result[1] + result[2]
        cursor.close()

        if request.method == 'POST':
            date = request.form['date']
            current_date = datetime.now().strftime('%Y-%m-%d')

            # Date Validation
            if not date:
                flash('Please Select the Date', 'error')
                return redirect(url_for('checkin'))

            if date != current_date:
                flash(f'Please checkin with valid DATE __: {current_date}', 'error')
                return redirect(url_for('checkin'))

            # Insert Check-in Record
            cursor = mydb.cursor(buffered=True)
            try:
               cursor.execute('INSERT INTO emp_records (emp_id, username, date, checkin_time) VALUES (%s, %s, %s, CURTIME())',
                    (emp_id, username, date))
               mydb.commit()
               flash('Check-in successful!', 'success')
            except Exception as e:
                print(f'Error during check-in: {e}', 'error')
                mydb.rollback()
            finally:
                cursor.close()

            return redirect(url_for('checkin_details', emp_id=emp_id))

        # Render the Employee Dashboard
        return render_template('emp_dashboard.html', username=username)

    else:
        flash('You Are Not Logged In', 'error')
        return redirect(url_for('emp_login'))
   
#checkin details..
@app.route('/checkin_details/<emp_id>')
def checkin_details(emp_id):
    if 'email' in session: #already checkin means in session
        email = session.get('email')
        print(emp_id)
        cursor = mydb.cursor(buffered=True,dictionary=True)
        cursor.execute('select * from emp_records where emp_id = %s and date = CURDATE()'
        , (emp_id,))
        checkin_data = cursor.fetchall()
        cursor.close()
        print("checkin_data:",checkin_data)
        if checkin_data:
            # Render the template with the check-in details
            return render_template('checkin_details.html', checkin_data = checkin_data)                           
        else:
            flash('No check-in records found', 'error')
            return redirect(url_for('emp_dashboard'))  # If no check-in found
    else:
        flash('User not found', 'error')
        return redirect(url_for('emp_login')) # If user not login

#checkout route
@app.route('/checkout/',methods=['GET','POST'])
def checkout():
    if session.get('email'):
        email = session.get('email')
        cursor = mydb.cursor(buffered=True)
        cursor.execute('select emp_id,first_name,last_name from emp_registration where email = %s',(email,))
        result = cursor.fetchone()
        emp_id = result[0]
        username = f'{result[1]} {result[2]}'
        cursor.close()
        if request.method == 'POST':
            
            cursor = mydb.cursor(buffered=True)
            # cursor.execute('insert into emp_records(checkout_time) values(CURTIME())')
            cursor.execute("UPDATE emp_records SET checkout_time = CURTIME() WHERE emp_id = %s and date = CURDATE() and checkout_time is NULL",(emp_id,))
            mydb.commit()
            cursor.close()
            # flash('You Have Been \n Check-out Successfully')
            return redirect(url_for('checkout_details',emp_id=emp_id))# Redirect to the checkout_details with emp_id
        
        return render_template('emp_dashboard.html')# Render the dashboard if not POST
    else:
        flash('You Are Not Logged In')
        return redirect(url_for('emp_login'))# Redirect to login if session does not exist
    
@app.route('/checkout_details/<emp_id>')
def checkout_details(emp_id):
    if 'email' in session:  # Check if the user is logged in
        email = session.get('email')
        cursor = mydb.cursor(buffered=True)
        #fetch the first check-in record today
        cursor.execute('SELECT * FROM emp_records WHERE emp_id = %s and date=CURDATE() ORDER BY checkin_time asc limit 1', (emp_id,))
        checkin_data= cursor.fetchone()#to get the first record
        print("checkin_data:",checkin_data)

        if checkin_data:
            #check-in  record exists, proceed to update check-out time
            checkin_time = checkin_data[3]  # Assuming 4th column is checkin_time
            checkout_time = datetime.now().strftime('%H:%M:%S')  # Get current time


            #update the record with the check-out time
            cursor.execute('update emp_records set checkout_time=CURTIME() where emp_id=%s and date=CURDATE() and checkin_time=%s',(emp_id,checkin_time))
            mydb.commit()
            cursor.close()

            #fetching the update record  to display
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select *from emp_records where emp_id=%s and date=CURDATE() order by checkin_time asc limit 1',(emp_id,))
            update_record=cursor.fetchone()
            flash('Check out Successfully!')
            #rendering to checkout_details.html
            return render_template('checkout_details.html',checkin_data=update_record)
        else:
            flash('No check-in records found','error')
            cursor.close()
            return redirect(url_for('emp_dashboard'))
    else:
          #user not logged in   
          flash('Employee record not found.', 'error')
          return redirect(url_for('emp_login'))
        
        
           

#salary route
@app.route('/salary/<emp_id>')
def salary(emp_id):
     #fetch emp_salary from emp_registration table
     cursor=mydb.cursor(buffered=True)
     cursor.execute('select  first_name,last_name,salary from emp_registration where emp_id=%s',(emp_id,))
     emp_data=cursor.fetchone()
     if not emp_data:
          return 'Employee details not Found',404 #Handle case where employee is not found
     first_name,last_name,salary=emp_data
     username=f'{first_name}{last_name}'
     #count distinct working days from emp_records for the employee
     cursor.execute('select count(distinct date) from emp_records where emp_id=%s',(emp_id,))
     num_working_days = cursor.fetchone()[0]  # Get the count of distinct dates
     company_working_days = 26
     #Calculate daily salary. Assuming 30 days in a month for simplicity (adjust if needed based on actual working days)
     daily_salary = salary / 26
     # Calculate the total salary for the working days
     total_salary = daily_salary * num_working_days
     return render_template("salary.html", emp_data=[{'emp_id': emp_id, 'username': username}],
     num_working_days=num_working_days,
     company_working_days=company_working_days,total_salary=round(total_salary,2))

#forgot route
@app.route('/forgot_pwd' ,methods=['GET','POST'])
def forgot_pwd():
     if request.method=='POST':
          #frontend email
          email=request.form['email']
          #database email checking
          cursor=mydb.cursor(buffered=True)
          cursor.execute('select count(email) from emp_registration where email=%s',(email,))
          count=cursor.fetchone()[0] 
          if count==0:
               flash('Email not exists try agin after sometime...!.')
               return redirect(url_for('forgot_pwd'))
          elif count==1:
               otp=genotp()
               # print(otp)
               #otp sending to email
               subject='Reset link for PAYROLL Application'
               body=f"PAYROLL application:{otp} "
               sendmail(to=email,subject=subject,body=body)
               #insert otp table
               cursor=mydb.cursor(buffered=True) 
               cursor.execute('insert into otp(email,otp) values(%s,%s)',(email,otp))
               mydb.commit()
               cursor.close()
               flash('Reset link has been sent to given Email.')
               return render_template('otp.html')
               
          else:
               flash('something went wrong')
               return render_template('forgot_pwd.html')
     return render_template('forgot_pwd.html')
@app.route('/otp',methods=['GET','POST'])
def otp():
     if request.method=='POST':
          if 'otp1' not in request.form:  # Check if 'otp' exists in the form
            flash('OTP field is missing in the form. Please try again.')
            return redirect(url_for('otp'))
          frontotp = request.form['otp1']
          print(f'OTP provided by the user:{frontotp}')
     
          cursor=mydb.cursor(buffered=True)
          cursor.execute('SELECT otp FROM otp ORDER BY OID DESC LIMIT 1')
          db_otp = cursor.fetchone()[0]
          print(f'dasbase otp:{db_otp}')
          if db_otp == frontotp:
               # return redirect('new_pwd')
               return redirect(url_for('update_pwd'))
          else:
               flash('invalid otp,please try again')
               return redirect(url_for('otp'))
     return render_template('otp.html')
@app.route('/update_pwd',methods=['GET','POST'])
def update_pwd():
     
     if request.method=='POST':
          #frontend email
          email=request.form['email']
          # if email==session['email']:
          return redirect(url_for('new_pwd',email=email))
     return render_template('update_pwd.html')
@app.route('/new_pwd/<email>',methods=['GET','POST'])
def new_pwd(email):
     
     if request.method=='POST':
          new_pwd=request.form.get('new-password')
          con_pwd=request.form.get('conform-password')
          # email=request.form['email']
          print(new_pwd,con_pwd)
          if new_pwd==con_pwd:
               #update password in the emp_reg table
               cursor=mydb.cursor(buffered=True)
               cursor.execute('update emp_registration set password=%s where email=%s',(new_pwd,email) )
               mydb.commit()
               cursor.close()
               print(new_pwd)
               flash('Your newpassword has been updated successfully')
               return redirect(url_for('emp_login'))
          else:
               flash('Your newpassword has not updated .Try again')
               return redirect(url_for('new_pwd',email=email))
               
     return render_template('new_pwd.html',email=email)
     



if __name__ == "__main__":
    app.run()