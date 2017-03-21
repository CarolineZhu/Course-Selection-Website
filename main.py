from flask import Flask, render_template, session, request, redirect, flash
import jaydebeapi
import json
import hashlib

conn = jaydebeapi.connect('com.informix.jdbc.IfxDriver',
                          'jdbc:informix-sqli://crl.ptopenlab.com:9088/d_1460372203599252:INFORMIXSERVER=ifxserver1;USER=yixyfluu;PASSWORD=4cYCBtPafd;DB_LOCALE=zh_cn.utf8',
                          '/Users/Zry/Desktop/Database/ifxjdbc.jar', )

app = Flask(__name__, static_url_path='')
app.secret_key ='123456'



# def get_model(table_name, attributes, sql_override=None):
#     def func(id):
#         if (id == None):
#             print "=-=-=-="
#             return None
#
#         cursor = conn.cursor()
#         print 21
#
#         cursor.execute(sql_override if sql_override is not None else 'select ' + ','.join(
#             attributes) + ' from ' + table_name + ' where id=?', [id])
#         print 22
#         result = cursor.fetchall()
#         if len(result) == 0:
#             return None
#         else:
#             ret = {}
#             for i in range(0, len(attributes)):
#                 ret[attributes[i]] = result[0][i]
#
#             return ret
#
#     return func
#
#
# get_user = get_model('user', ['id', 'user_type', 'password'])
# get_student = get_model('student', ['student_id', 'student_name', 'gender', 'grade'])
# get_teacher = get_model('teacher', ['teacher_id', 'teacher_name', 'gender', 'department'])
# get_course = get_model('course', ['course_id', 'course_name', 'teacher_id', 'time', 'capacity', 'occupied'])


@app.route('/')
def page_welcome():
    return render_template('Welcome.html')


@app.route('/', methods=["POST"])
def page_login_post():
    user_id = request.form['id']
    password = request.form['password']
    user_type = request.form['user_type']
    cursor = conn.cursor()
    # print user_id
    # result = get_user(user_id)
    # print "====="
    #print user_id, password, user_type
    cursor.execute('select user_id,password, user_type from user where user_id= ?', [user_id])
    #print "========="
    result = cursor.fetchall()
    if len(result) == 0:
        flash("Wrong ID.", 'error')
        return redirect('/')

    if password_hash(password) != result[0][1]:
        flash("Wrong password.", 'error')
        return redirect('/')

    session['user_id'] = result[0][0]
    #print session['user_id']
    if user_type == 'student' and result[0][2] == 1:
        print "======"
        flash("Log in successfully.", 'success')
        return redirect('/StudentIndex')

    elif user_type == 'teacher' and result[0][2] == 0:
        print "-----"
        flash("Log in successfully.", 'success')
        return redirect('/TeacherIndex')

    else:
        flash("Wrong identity.", 'error')
        return redirect('/')


@app.route('/StudentIndex')
def page_student_index():
    # cursor = conn.cursor()
    # cursor.execute('select student_name from student where student_id = %s', [session['user_id']])
    # student_name = cursor.fetchall()

    # query all courses related to the student
    # courses=curs.fetchall()

    student_id = session['user_id']

    cursor = conn.cursor()
    cursor.execute(
        'select course_name, course_time, student_name from course, selectcourse, student where student.student_id = selectcourse.student_id and course.course_id = selectcourse.course_id and student.student_id = ?', [student_id])
    all_course_init = cursor.fetchall()
    #  [ [Math,12] , [Computer,44] ]     {{ course[0] }}
    # [{name:"Math",time:12},{name:"Computer",time:44}]   {{ course['name'] }}
    student_name = all_course_init[0][2]
    cursor.execute('select course.course_id, course_name, course_time, teacher_name from course, teacher, selectcourse where course.course_id = selectcourse.course_id and course.teacher_id = teacher.teacher_id and selectcourse.student_id = ?;', [session['user_id']])
    course_list = cursor.fetchall()
    all_course = {}
    # time 1-6 11-16
    for i in range(1,6):
        all_course[i] = {}
    for item in all_course_init:
        day = item[1] / 10
        # if day+1 not in all_course:
        #     print "================="
        #     all_course[day + 1] = {}
        all_course[day + 1][item[1] % 10] = item[0]
    return render_template('StudentIndex.html', username=student_name, course_table=all_course, course_list = course_list)


@app.route('/TeacherIndex')
def page_teacher_index():
    teacher_id = session['user_id']
    cursor = conn.cursor()
    cursor.execute('select teacher_name from teacher where teacher_id = ?', [teacher_id])
    # result = get_teacher(teacher_id)
    # teacher_name = result['teacher_name']
    name = cursor.fetchall()
    teacher_name = name[0][0]
    #cursor.execute('select student_id, student_name, gender, grade from student, selectcourse, course_id where selectcourse.student_id = student.student_id selectcourse.course_id =course.course_id and course.teacher_id = ?', [teacher_id])
    cursor.execute('select course_id, course_name, course_time, capacity, occupied from course where course.teacher_id = ?', [teacher_id])
    teach_course = cursor.fetchall()

    return render_template('TeacherIndex.html', username=teacher_name, teach_course = teach_course)


@app.route('/StudentInfo/<course_id>')
def page_student_information_index(course_id):
    cursor = conn.cursor()
    cursor.execute(
        'select student.student_id, student_name, gender, major, grade, tel, email, address from student, selectcourse where student.student_id = selectcourse.student_id and course_id = ?;',
        [course_id])
    student_info = cursor.fetchall()
    cursor.execute('select course_id, course_name from course where course_id = ?', [course_id])
    query_course = cursor.fetchall()
    return render_template('StudentInformation.html', student_info=student_info, course_info = query_course)


@app.route('/logout')
def page_logout():
    flash('Logout Successfully!', 'success')
    del session['user_id']
    return redirect('/')


@app.route('/passwordchange')
def page_index():
    return render_template('Change_password.html')

@app.route('/passwordchange', methods = ["POST"])
def page_index_post():
    cursor = conn.cursor()
    #print "===="
    #print 'select password from user where user_id = ?', session['user_id']
    #exit();
    cursor.execute('select password, user_type from user where user_id = ?', [session['user_id']])
    result = cursor.fetchall()
    if result[0][0] != password_hash(request.form['current_password']):
        flash("Wrong password", 'error')
        return redirect('/passwordchange')
    else:
        if len(request.form['new_password']) < 4:
            flash("Too short password.", 'error')
            return redirect('/passwordchange')
        if request.form['new_password'] != request.form['repeat_password']:
            flash("Two password are not the same", 'error')
            return redirect('/passwordchange')
        else:
            flash("Change password successfully.", 'success')
            cursor.execute('update user set password =? where user_id =?', [password_hash(request.form['new_password']),session['user_id']])
            if result[0][1] == 1:
                return redirect('/StudentIndex')
            if result[0][1] == 0:
                return redirect('/TeacherIndex')

@app.route('/StudentIndex', methods=['POST'])
def student_index_post():
    cursor = conn.cursor()
    course_id = request.form['course_id']
    course_name = request.form['course_name']
    operate_type = request.form['action']

    #authorize.  complete
    cursor.execute('select student_name, user_type from user, student where user_id = student_id and user_id = ?', [session['user_id']])
    user_info = cursor.fetchall()
    # print user_info
    if user_info[0][1] != 1:
        flash("No privilege.", 'error')
        return redirect('/')
    if len(course_id) != 0 or len(course_name) != 0:
        if len(course_id) == 0:
            cursor.execute(
                'select course_id, course_name, course_time, teacher_name, capacity, occupied from course, teacher where course.teacher_id = teacher.teacher_id and course_name = ?;',
                [course_name])
            # print "----------------"
            course_info = cursor.fetchall()
            if len(course_info) == 0:
                flash("Wrong course name.", 'error')
                return redirect('/StudentIndex')
            else:
                if operate_type == 'Search':
                    #render_template
                    #session['course_name'] = course_name
                    # return redirect('/StudentIndex')
                    print "1233243546"
                    return render_template('StudentIndex.html', course_info = course_info, username = user_info[0][0])
                if len(course_info) > 1:
                    # print ">1"
                    if operate_type == 'Select':
                        # print "select x"
                        flash("The course is not unique.", 'error')
                        return redirect('/StudentIndex')
                    if operate_type == 'Delete':
                        # print "delete"
                        cursor.execute(
                            'select course.course_id from selectcourse, course where student_id = ? and selectcourse.course_id = course.course_id and course_name = ?;',
                            [session['user_id'], course_name])
                        selected = cursor.fetchall()
                        if len(selected) == 0:
                            flash("The course has not been selected.", 'error')
                            return redirect('/StudentIndex')
                        if len(selected) > 1:
                            flash("You have more than 1 course with the course name.", 'error')
                            return redirect('/StudentIndex')
                        # print "delete successfully"
                        cursor.execute('delete from selectcourse where student_id = ? and course_id = ?',
                                       [session['user_id'], selected[0][0]])
                        cursor.execute('update course set occupied = occupied - 1 where course_id = ?',
                                       [course_info[0][0]])
                        flash("Delete successfully.", 'success')
                        return redirect('/StudentIndex')
                # if operate_type == 'Select':
                #     if len(course_info) > 1:
                #         flash("The course is not unique.", 'error')
                #         return redirect('/StudentIndex')
                #     cursor.execute(
                #         'select course.course_id from selectcourse,course where student_id = ? and course.course_id = selectcourse.course_id and course_time = ?;',
                #         [session['user_id'], course_info[0][2]])
                #     conflict = cursor.fetchall()
                #     if course_info[0][4] == course_info[0][5]:
                #         flash("The number of student reaches the limit.", 'error')
                #         return redirect('/StudentIndex')
                #     elif len(conflict) != 0:
                #         flash("Time conflicts.", 'error')
                #         return redirect('/StudentIndex')
                #     else:
                #         cursor.execute('insert into selectcourse (student_id, course_id) values (?, ?)',
                #                        [session['user_id'], course_info[0][0]])
                #         cursor.execute('update course set occupied = occupied + 1 where course_id = ?;',
                #                        [course_info[0][0]])
                #         flash("Select successfully.", 'success')
                #         return redirect('/StudentIndex')
                # if operate_type == 'Delete':
                #     cursor.execute('select course.course_id from selectcourse, course where student_id = ? and selectcourse.course_id = course.course_id and course_name = ?;', [session['user_id'], course_name])
                #     selected = cursor.fetchall()
                #     if len(selected) == 0:
                #         flash("The course has not been selected.", 'error')
                #         return redirect('/StudentIndex')
                #     if len(selected) > 1:
                #         flash("You have more than 1 course with the course name.", 'error')
                #         return redirect('/StudentIndex')
                #     cursor.execute('delete from selectcourse where student_id = ? and course_id = ?', [session['user_id'], selected[0][0]])
                #     flash("Delete successfully.", 'success')
                #     return redirect('/StudentIndex')
                else:
                    # print "==1"
                    if operate_type == 'Select':
                        cursor.execute(
                            'select course.course_id from selectcourse,course where student_id = ? and course.course_id = selectcourse.course_id and course_time = ?;',
                            [session['user_id'], course_info[0][2]])
                        conflict = cursor.fetchall()
                        if course_info[0][4] == course_info[0][5]:
                            flash("The number of student reaches the limit.", 'error')
                            return redirect('/StudentIndex')
                        elif len(conflict) != 0:
                            flash("Time conflicts.", 'error')
                            return redirect('/StudentIndex')
                        else:
                            cursor.execute('insert into selectcourse (student_id, course_id) values (?, ?)',
                                           [session['user_id'], course_info[0][0]])
                            cursor.execute('update course set occupied = occupied + 1 where course_id = ?;',
                                           [course_info[0][0]])
                            flash("Select successfully.", 'success')
                            return redirect('/StudentIndex')

                    if operate_type == 'Delete':
                        cursor.execute('select course_id from selectcourse where student_id = ? and course_id = ?',
                                       [session['user_id'], course_info[0][0]])
                        exist = cursor.fetchall()
                        if len(exist) == 0:
                            flash("This course has not been selected.", 'error')
                            return redirect('/StudentIndex')
                        else:
                            cursor.execute('delete from selectcourse where student_id = ? and course_id = ?',
                                           [session['user_id'], course_info[0][0]])
                            cursor.execute('update course set occupied = occupied - 1 where course_id = ?',
                                           [course_info[0][0]])
                            return redirect('/StudentIndex')
        else:
            cursor.execute(
                'select course_id, course_name, course_time, teacher_name, capacity, occupied from course, teacher where course.teacher_id = teacher.teacher_id and course_id = ?;',
                [course_id])
            course_info = cursor.fetchall()
            if len(course_info) == 0:
                flash("Wrong course ID.", 'error')
                return redirect('/StudentIndex')
            else:
                if operate_type == 'Search':
                    #render_template
                    print course_info
                    #return redirect('/StudentIndex')
                    return render_template('StudentIndex.html', course_info = course_info, username = user_info[0][0])
                if operate_type == 'Select':
                    cursor.execute(
                        'select course.course_id from selectcourse,course where student_id = ? and course.course_id = selectcourse.course_id and course_time = ?;', [session['user_id'], course_info[0][2]])
                    # print "----------------"
                    conflict = cursor.fetchall()
                    if course_info[0][4] == course_info[0][5]:
                        flash("The number of student reaches the limit.", 'error')
                        return redirect('/StudentIndex')
                    elif len(conflict) != 0:
                        flash("Time conflicts.", 'error')
                        return redirect('/StudentIndex')
                    else:
                        cursor.execute('insert into selectcourse (student_id, course_id) values (?, ?)',
                                       [session['user_id'], course_id])
                        cursor.execute('update course set occupied = occupied + 1 where course_id = ?;', [course_id])
                        flash("Select the course successfully.", 'success')
                        return redirect('/StudentIndex')
                if operate_type == 'Delete':
                    cursor.execute('select course_id from selectcourse where student_id = ? and course_id = ?',
                                   [session['user_id'], course_id])
                    exist = cursor.fetchall()
                    if len(exist) == 0:
                        flash("This course has not been selected.", 'error')
                        return redirect('/StudentIndex')
                    else:
                        cursor.execute('delete from selectcourse where student_id = ? and course_id = ?',
                                       [session['user_id'], course_id])
                        cursor.execute('update course set occupied = occupied - 1 where course_id = ?;', [course_id])
                        flash("Delete successfully.", 'success')
                        return redirect('/StudentIndex')
    else:
        flash("No Input.", 'error')
        return redirect('/StudentIndex')


@app.route('/TeacherIndex', methods=["POST"])
def teacher_index_post():
    cursor = conn.cursor()
    course_id = request.form['course_id']
    course_name = request.form['course_name']
    course_time = request.form['course_time']
    capacity = request.form['capacity']
    operate_type = request.form['action']
    # query_course_id = request.form['query_course']
    cursor.execute('select user_type from user where user_id = ?;', [session['user_id']])
    user_info = cursor.fetchall()

    if user_info[0][0] != 0:
        flash("No privilege.", 'error')
        return redirect('/')

    if operate_type == 'add':

        if len(course_id) != 0 and len(course_name) != 0 and len(course_time) != 0 and len(capacity) != 0:
            #courseinfo = get_course(course_id)
            #print "-=-=-=-"
            cursor.execute('select course_id from course where course_time = ? and teacher_id = ?', [course_time,
                           session['user_id']])
            conflict = cursor.fetchall()
            cursor.execute('select teacher_id from course where course_id = ?', [course_id])
            exist = cursor.fetchall()
            if len(conflict) != 0:
                flash("Time conflicts.", 'error')
                return redirect('/TeacherIndex')
                #modified
            if len(exist) != 0:
                flash("The course exists.", 'error')
                return redirect('/TeacherIndex')
            #add operation
            cursor.execute('insert into course (course_id, course_name, course_time, teacher_id, capacity, occupied) values(?,?,?,?,?,0)', [course_id, course_name, course_time, session['user_id'], capacity])
            flash("Add successfully.", 'success')
            return redirect('/TeacherIndex')
        else:
            flash("Incomplete information.", 'error')
            return redirect('/TeacherIndex')

    if operate_type == 'remove':
        #print "==="
        if len(course_id) != 0:
            cursor.execute('select course_id, teacher_id from course where course_id = ?', [course_id])
            course_exist = cursor.fetchall()
            if len(course_exist) != 0:
                if course_exist[0][1] == session['user_id']:
                    cursor.execute('delete from selectcourse where course_id = ?; delete from course where course_id = ?;', [course_id,course_id])
                    flash("Remove successfully.", 'success')
                    return redirect('/TeacherIndex')
                else:
                    flash("No privilege.", 'error')
                    return redirect('/TeacherIndex')
            else:
                flash("The course does not exist.", 'error')
                return redirect('/TeacherIndex')
        else:
            flash("No input.", 'error')
            return redirect('/TeacherIndex')

    # if len(query_course_id) != 0:
    #     cursor.execute('select * from student, selectcourse where student.student_id = selectcourse.student_id and course_id = ?;', [query_course_id])
    #     student_info = cursor.fetchall()
    #     return render_template('StudentInformation.html', student_info = student_info)

def password_hash(password):
    m = hashlib.md5()
    m.update(password)
    return m.hexdigest()


if __name__ == '__main__':
    # app.config.update(PROPAGATE_EXCEPTIONS=True)
    app.run()
