from flask import Flask,request,redirect,url_for,render_template,flash,session,send_file,jsonify
from io import BytesIO
import flask_excel as excel
from flask_session import Session
from otp import genotp
from cmail import send_mail
from stoken import endata,dndata
from mysql.connector import(connection)
import re
db=connection.MySQLConnection(user='flaskuser',password='password',host='localhost',database='flaskdb')
app=Flask(__name__)
excel.init_excel(app)
app.secret_key='aqthar12345'
app.config['SESSION_TYPE']='filesystem'
app.config['SERVER_NAME']='32.236.18.22'
app.config['PREFERRED_URL_SCHEME']='https'
Session(app)
#home------------------------------------------------------------------------------------------------------------------------------>
@app.route('/',methods=['GET'])
def home():
     return render_template('Welcome.html')
#register--------------------------------------------------------------------------------------------------------->
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        useremail = request.form['email']
        password = request.form['password']

        try:
            cursor = db.cursor(buffered=True)
            cursor.execute(
                'select count(*) from usersdata where useremail=%s',
                [useremail]
            )
            email_count = cursor.fetchone()[0]
            cursor.close()
        except Exception as e:
            print(e)
            flash('could not verify email')
            return redirect(url_for('register'))

        if email_count == 0:
            gotp = genotp()
            userdetails = {
                'username': username,
                'useremail': useremail,
                'password': password,
                'userotp': gotp
            }

            subject = 'User validation OTP FOR SNM'
            body = f'Use the given otp {gotp}'

            send_mail(
                to=useremail,
                subject=subject,
                body=body
            )

            flash('OTP sent successfully to mail')
            return redirect(
                url_for(
                    'verifyotp',
                    serverdata=endata(data=userdetails)
                )
            )

        elif email_count == 1:
            flash('Email already existed')
            return redirect(url_for('register'))

    return render_template('registerform.html')
#otpverify------------------------------------------------------------------------------------------------------->
@app.route('/otpverify/<serverdata>',methods=['GET','POST'])
def verifyotp(serverdata):
     if request.method=='POST':
          try:
               user_details=dndata(data=serverdata)
          except Exception as e:
               print('error in decryption',str(e))
               return redirect(url_for('register'))
          userotp=request.form['otp']
          if user_details['userotp']==userotp:
               try:
                    #db connection
                    cursor=db.cursor(buffered=True) # which is used to interact with mysql
                    cursor.execute('insert into usersdata(username,useremail,userpassword) values(%s,%s,%s)',
                    [user_details['username'],user_details['useremail'],user_details['password']])
                    db.commit()#to save  the insert permanently
                    cursor.close()
               except Exception as e:
                    print("MY SQL ERROR",e)
                    flash('cannot soore the details')
                    return redirect(url_for('vefifyotp',serverdata=serverdata))
               else:
                    flash('user Registerd successfully')
                    return redirect(url_for('login'))
          else:
               flash('OTP was wrong')
               return redirect(url_for('verifyotp',serverdata=serverdata))
     return render_template('otpverify.html')
#login----------------------------------------------------------------------------------------------------------->
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        login_useremail=request.form['email']
        login_userpassword=request.form['password']
        try:
            cursor=db.cursor(buffered=True)
            cursor.execute('select count(*) from usersdata where useremail=%s',[login_useremail])
            email_count=cursor.fetchone() #(1,) or (0,)
        except Exception as e:
            print('Mysql ERROR :',str(e))
            flash('Could not verify email')
            return redirect(url_for('dashboard'))
        else:
            if email_count[0] > 0:
                cursor.execute(
                    'select userpassword from usersdata where useremail=%s',
                    [login_useremail]
                )
                stored_password = cursor.fetchone()[0]

                if stored_password == login_userpassword:
                    session['user']=login_useremail
                    print(session,'after session')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Password was wrong')
                    return redirect(url_for('login'))

            elif email_count <= 0:
                flash('No Email found pls check')
                return redirect(url_for('login'))

    return render_template('login.html')

#dashboard---------------------------------------------------------------------------------------------------------------------->
@app.route('/dashboard',methods=['GET'])
def dashboard():
     if not session.get('user'):
        flash('PLZ LOGIN FIRST')
        return redirect(url_for('login'))
     return render_template('dashboard.html')
#addnotes------------------------------------------------------------------------------------------------->
@app.route('/addnotes',methods=['GET','POST'])
def addnotes():
     if not session.get('user'):
          flash('Please login first')
          return redirect(url_for('login'))
     if request.method=='POST':
          notes_title=request.form['title']
          notes_body=request.form['description']
          try:
               useremail=session.get('user')
               cursor=db.cursor(buffered=True)
               cursor.execute('select userid from usersdata where useremail=%s',[useremail])
               user_id=cursor.fetchone()[0] #(1,) #none[0]
               cursor.execute('insert into notesdata(title,description,userid) values(%s,%s,%s)',
               [notes_title,notes_body, user_id])
               db.commit()
               cursor.close()
          except Exception as e:
               print('MYSQL Error:',str(e))
               flash('Could save notes')
               return redirect(url_for('addnotes'))
          else:
               flash('Notes details successfully stored')
               return redirect(url_for('addnotes'))
     return render_template('addnotes.html')

#view all notes------------------------------------------------------------------------------------------------------------------------------------------------------->
@app.route('/viewallnotes',methods=['GET'])
def viewallnotes():
    if not session.get('user'):
        flash('pls login first')
        return redirect(url_for('login'))
    try:
        useremail=session.get('user')
        cursor=db.cursor(buffered=True)
        cursor.execute('select userid from usersdata where useremail=%s',[useremail])
        user_id=cursor.fetchone()[0] #(1,) #none[0]
        cursor.execute('select notesid,title,created_at from notesdata where userid=%s',[user_id])
        allnotesdata=cursor.fetchall()
        cursor.close()
    except Exception as e:
        print('Mysql Error:',str(e))
        flash('Could not fetch the notes details')
        return redirect(url_for('dashboard'))
    else:
        return render_template('viewallnotes.html',allnotesdata=allnotesdata)
#viewsingle notes------------------------------------------------------------------------------------------------------------------------------------------------------------------------>
@app.route('/viewnotes/<nid>',methods=['GET'])
def viewnotes(nid):
    if not session.get('user'):
        flash('pls login first')
        return redirect(url_for('login'))
    try:
        useremail=session.get('user')
        cursor=db.cursor(buffered=True)
        cursor.execute('select userid from usersdata where useremail=%s',[useremail])
        user_id=cursor.fetchone()[0] #(1,) #none[0]
        cursor.execute('select notesid,title,description,created_at from notesdata where userid=%s and notesid=%s',[user_id,nid])
        notesdata=cursor.fetchone() #(1,'Mysql','2026-06-12'),
        print(notesdata)
        cursor.close()
    except Exception as e:
        print('MYsql Error:',str(e))
        flash('Could not fetch the notes details')
        return redirect(url_for('dashboard'))
    else:
        return render_template('viewnotes.html',notesdata=notesdata)
#deletenotes------------------------------------------------------------------------------------------------------------------->
@app.route('/delete/<notesid>',methods=['GET'])
def delete(notesid):
    if not session.get('user'):
        flash('pls login first')
        return redirect(url_for('login'))
    try:
         useremail=session.get('user')
         cursor=db.cursor(buffered=True)
         cursor.execute('DELETE FROM notesdata WHERE notesid=%s',[notesid])
         db.commit()
         cursor.close()
    except Exception as e:
        print('Mysql Error:',str(e))
        flash('Could not delete the notes')
        return redirect(url_for('dashboard'))
    else:
        flash('Notes deleted successfully' )
        return redirect(url_for ('viewallnotes'))
# #UPDATE NOTES------------------------------------------------------------------------------------------------------------------------------------------------------------------------>

@app.route('/update/<nid>', methods=['GET', 'POST'])
def update(nid):
    if not session.get('user'):
        flash('plz login first')
        return redirect(url_for('login'))

    try:
        useremail = session.get('user')
        cursor = db.cursor(buffered=True)

        cursor.execute('select userid from usersdata where useremail=%s', [useremail])
        user_id = cursor.fetchone()[0]

        cursor.execute('SELECT notesid, title, description FROM notesdata WHERE userid=%s AND notesid=%s',[user_id, nid])
        notesdata = cursor.fetchone()
        cursor.close()
    except Exception as e:
        print('Mysql Error:', str(e))
        flash('Could not fetch the notes details')
        return redirect(url_for('dashboard'))

    else:

        if request.method == 'POST':
            updated_title = request.form['title']
            updated_description = request.form['description']

            try:
                cursor = db.cursor(buffered=True)
                cursor.execute('UPDATE notesdata SET title=%s, description=%s WHERE userid=%s AND notesid=%s',
                [updated_title, updated_description, user_id, nid])

                db.commit()
                cursor.close()
            except Exception as e:
                print('Mysql Error:', str(e))
                flash('Could not update the notes')
                return redirect(url_for('update', nid=nid))
            else:
                flash('Notes updated successfully')
                return redirect(url_for('update', nid=nid))
        return render_template('updatenotes.html', notesdata=notesdata)
##excel data---------------------------------------------------------------------------------------------------------------------->
@app.route('/exceldata',methods=['GET'])
def exceldata():
    if not session.get('user'):
        flash('plz login first')
        return redirect(url_for('login'))
    try:
        useremail = session.get('user')
        cursor = db.cursor(buffered=True)

        cursor.execute('select userid from usersdata where useremail=%s', [useremail])
        user_id = cursor.fetchone()[0]

        cursor.execute('SELECT notesid, title, description FROM notesdata WHERE userid=%s',[user_id,])
        allnotesdata = cursor.fetchall()
        cursor.close()
    except Exception as e:
        print('Mysql Error:', str(e))
        flash('Could not fetch the notes details')
        return redirect(url_for('dashboard'))
    else:
        notesdata=[list(i) for i in allnotesdata]
        colums=['Notesid','Title','Description','Created_at']
        notesdata.insert(0,colums)
        return excel.make_response_from_array(notesdata,'xlsx',file_name='Notesdata')


#upload file------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------->
@app.route('/upload',methods=['GET','POST'])
def upload():
    if not session.get('user'):
        flash('plz login first')
        return redirect(url_for('login'))
    if request.method=='POST':
        filedata=request.files['file']
        fdata=filedata.read()
        fname=filedata.filename
        try:
            useremail=session.get('user')
            cursor=db.cursor(buffered=True)
            cursor.execute('select userid from usersdata where useremail=%s',[useremail])
            user_id=cursor.fetchone()[0]
            cursor.execute('insert into filesdata(filename,filedata,userid) values(%s,%s,%s)',[fname,fdata,user_id])
            db.commit()
            cursor.close()
        except Exception as e:
            print('Mysql Error:',str(e))
            flash('Could not upload the file')
            return redirect(url_for('upload'))
        else:
            flash('File uploaded successfully')
            return redirect(url_for('upload'))
    return render_template('uploadfile.html')

#viewall files data---------------->
@app.route('/viewallfiles',methods=['GET'])
def viewallfiles():
    if not session.get('user'):
        flash('plz login first')
        return redirect(url_for('login'))
    try:
        useremail=session.get('user')
        cursor=db.cursor(buffered=True)
        cursor.execute('select userid from usersdata where useremail=%s',[useremail])
        user_id=cursor.fetchone()[0]
        cursor.execute('select fileid,filename,created_at from filesdata where userid=%s',[user_id])
        allfilesdata=cursor.fetchall()
        cursor.close()
    except Exception as e:
        print('Mysql Error:',str(e))
        flash('Could not fetch the file details')
        return redirect(url_for('dashboard'))
    else:
        return render_template('viewallfiles.html',allfilesdata=allfilesdata)
#viewfile------------------------------------------------------------------------------------------------------------->
@app.route('/viewfile/<fid>',methods=['GET'])
def viewfile(fid):
    if not session.get('user'):
        flash('pls login first')
        return redirect(url_for('login'))
    try:
        useremail=session.get('user')
        cursor=db.cursor(buffered=True)
        cursor.execute('select userid from usersdata where useremail=%s',[useremail])
        user_id=cursor.fetchone()[0] #(1,) #none[0]
        cursor.execute('select fileid,filename,filedata,created_at from filesdata where userid=%s and fileid=%s',[user_id,fid])
        filesdata=cursor.fetchone() #(1,'Mysql','2026-06-12'),
        # print(filesdata)
        cursor.close()
    except Exception as e:
        print('MYsql Error:',str(e))
        flash('Could not fetch the notes details')
        return redirect(url_for('dashboard'))
    else:
       filename=filesdata[1]
       bytes_array=(BytesIO(filesdata[2]))
       return send_file(bytes_array,as_attachment=False,download_name=filename)


#Downloadfile------------------------------------------------------------------------------------------------------------->
@app.route('/download/<fid>',methods=['GET'])
def downloadfile(fid):
    if not session.get('user'):
        flash('pls login first')
        return redirect(url_for('login'))
    try:
        useremail=session.get('user')
        cursor=db.cursor(buffered=True)
        cursor.execute('select userid from usersdata where useremail=%s',[useremail])
        user_id=cursor.fetchone()[0] #(1,) #none[0]
        cursor.execute('select fileid,filename,filedata,created_at from filesdata where userid=%s and fileid=%s',[user_id,fid])
        filesdata=cursor.fetchone() #(1,'Mysql','2026-06-12'),
        # print(filesdata)
        cursor.close()  
    except Exception as e:
        print('MYsql Error:',str(e))
        flash('Could not fetch the notes details')
        return redirect(url_for('dashboard'))
    else:
       filename=filesdata[1]
       bytes_array=(BytesIO(filesdata[2]))
       return send_file(bytes_array,as_attachment=True,download_name=filename)
#search route for notes----------------------------------------------------------------------------------------------------------------------------------------------------------------------->
@app.route('/search',methods=['GET'])
def search():
    if not session.get('user'):
        flash('plz login first')
        return redirect(url_for('login'))
    try:
        searchdata=request.args.get('query')
        strg=['A-Za-z0-9']
        pattern=re.compile(f'^{strg}',re.IGNORECASE)
        if pattern.match(searchdata):
            try:
                cursor=db.cursor(buffered=True)
                cursor.execute('select notesid,title,created_at from notesdata where notesid like %s or title like %s  or description like %s or created_at like %s', 
                [searchdata+'%',searchdata+'%',searchdata+'%',searchdata+'%'])
                allnotesdata=cursor.fetchall()
                cursor.close()
            except Exception as e:
                print('MYSQL error:',str(e))
                flash('could not fetch the notes details')
                return redirect(url_for('dashboard'))
            else:
                return render_template('viewallnotes.html',allnotesdata=allnotesdata)
        else:
            flash('Invalid search data')
            return redirect(url_for('dashboard'))
    except Exception as e:
        print('Error:',str(e))
        flash('could not find the search note')
        return redirect(url_for('dashboard'))
    
#deletefiles----------------------------------------------------------------------------------------------------------------------------------------------------------->
@app.route('/deletefile/<fid>',methods=['GET'])
def deletefile(fid):
    if not session.get('user'):
        flash('plz login first')
        return redirect(url_for('login'))
    try:
        useremail=session.get('user')
        cursor=db.cursor(buffered=True)
        cursor.execute('Delete from filesdata where fileid=%s',[fid])
        db.commit()
        cursor.close()
    except Exception as e:
        print('Mysql Error:',str(e))
        flash('could not delete the file from the databas')
        return redirect(url_for('viewallfiles'))
    else:
        flash('file deleted successfully')
        return redirect(url_for('viewallfiles'))
#logout--------------------------------------------------------------------------------------------------------------------------------------------------->
@app.route('/logout',methods=['GET'])
def logout():
    if not session.get('user'):
        flash('PLZ LOGIN FIRST')
        return redirect(url_for('login'))
    try:
        session.pop('user')
        flash('Logged out successfully')
        return redirect(url_for('login'))
    except Exception as e:
        print('Error:',str(e))
        flash('cloude not logout')
        return redirect(url_for('dashboard'))
#forgotpassword------------------------------------------------------------------------------->
@app.route('/forgotpassword', methods=['GET', 'POST'])
def forgotpassword():
    if request.method == 'POST':
        forgot_email = request.form['useremail']

        try:
            cursor = db.cursor(buffered=True)

            cursor.execute(
                'select count(*) from usersdata where useremail=%s',
                [forgot_email]
            )

            email_count = cursor.fetchone()[0]

            if email_count == 1:
                subject = f'click the reset link for forgotpassword SNM App'
        

                body = f"Click the reset link {url_for('newpassword',data=endata(forgot_email),_extrenal=True)}"

                send_mail(to=forgot_email,subject=subject,body=body)

            elif email_count == 0:
                flash('Email not found plz check')
                return redirect(url_for('forgotpassword'))

        except Exception as e:
            print(e)
            flash('Could not sent the link')
            return redirect(url_for('forgotpassword'))

        else:
            flash('re-set link has been sent to given email')
            return redirect(url_for('forgotpassword'))

    return render_template('forgotpassword.html')
#new password--------------------------------------------------------------------------------------------------------------------------->
@app.route('/newpassword/<data>',methods=['GET','PUT'])
def newpassword(data):
    try:
        forgot_email=dndata(data)
    except Exception as e:
        flash('Could not verify email')
        return redirect (url_for('newpassword',data=data))
    else:
        if request.method=='PUT':
            npassword=request.get_json()['password']
            try:
                cursor=db.cursor(buffered=True)
                cursor.execute('update usersdata set userpassword=%s where useremail=%s',[npassword,forgot_email])
                db.commit()
                cursor.close()
            except Exception as e:
                print(e)
                flash('could not update password in database')
                return redirect(url_for('newpassword',data=data))
            else:
                flash('password update successfully')
                return jsonify({'status':'success','message':'Updated'})

    
    return render_template('newpassword.html',data=data)




        
    

if __name__=='__main__':
    app.run()






































