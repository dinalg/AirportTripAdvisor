from flask import Flask, render_template, request, redirect
import mysql.connector

app = Flask(__name__, template_folder = 'templates')

cnx = mysql.connector.connect(
    host = '127.0.0.1',
    user = 'root',
    database = 'tables',
    password = 'dbmerchants'
)

@app.route('/', methods = ['GET', 'POST'])
def index():
    return render_template('crud.html')

@app.route('/search', methods = ['GET', 'POST'])
def search():
    form = request.form
    if 'submit_button' in request.form:
        selected_table = form['list']
        search = form['search']
        cur = cnx.cursor()

        if selected_table == "airlines":
            cur.execute("SELECT * FROM airlines WHERE airline_name like %s", (search, ))

        if selected_table == "airports":
            cur.execute("SELECT * FROM airports WHERE iata_code like %s", (search, ))

        if selected_table == "covid":
            cur.execute("SELECT * FROM covid WHERE state like %s", (search, ))

        if selected_table == "reviews":
            cur.execute("SELECT * FROM reviews WHERE author like %s", (search, ))

        if selected_table == "User":
            cur.execute("SELECT * FROM User WHERE userName like %s", (search, ))

    results = cur.fetchall()

    if cur.rowcount != 0:
        return render_template('searchResults.html', var = "Search", results = results)

    cnx.commit()
    cur.close()
    return render_template('crud.html')

@app.route('/query1', methods = ['POST'])
def query1():
    cur = cnx.cursor()
    cur.execute('''select r.airline_name, round(avg(r.rating),2) as avgRating
                    from reviews r natural join airports a
                    where a.iata_code = 'BWI'
                    group by r.airline_name
                    order by avgRating desc;''')
    results = cur.fetchall()
    if cur.rowcount != 0:
        return render_template('searchResults.html', var = "Query", results = results)
    cnx.commit()
    cur.close()
    return redirect("/")

@app.route('/query2', methods = ['POST'])
def query2():
    cur = cnx.cursor()
    cur.execute('''select a.airline_name, r.author
                   from routes ro natural join airlines a join reviews r using (airline_name)
                   where r.rating >= all(select r1.rating
                                         from routes ro1 natural join airlines a1 join reviews r1 using (airline_name)
                                         where ro1.destination_airport_iata = 'ORD')
                   group by a.airline_id;''')
    results = cur.fetchall()
    if cur.rowcount != 0:
        return render_template('searchResults.html', var = "Query", results = results)
    cnx.commit()
    cur.close()
    return redirect("/")

@app.route('/stored-procedure', methods = ['POST'])
def stored_procedure():
    cur = cnx.cursor()
    cur.execute("drop procedure if exists pp;")
    cur.close()
    cur = cnx.cursor()
    cur.execute('''create procedure pp()
                    begin
                        declare varAvgRating INT;
                        declare varDestAirline VARCHAR(255);
                        declare varAuthor VARCHAR(255);
                        declare varAirline VARCHAR(255);
                        declare varQuality VARCHAR(255);
                        declare varRatingDiff VARCHAR(255);

                        declare exit_loop boolean default false;
                        declare cusCur cursor for (select r.airline_name, round(avg(r.rating),2) as avgRating
                                                from reviews r natural join airports a
                                                where a.iata_code = "BWI"
                                                group by r.airline_name
                                                order by avgRating desc);
                        declare continue handler for not found set exit_loop = true;
                        drop table if exists FinalTable;
                        create table FinalTable(airline VARCHAR(255), destAirline VARCHAR(255), quality VARCHAR(255));
                        open cusCur;
                        cloop: loop 
                            fetch cusCur into varAirline, varAvgRating;
                            if(exit_loop) then
                                leave cloop;
                            end if;

                            set varDestAirline = (select distinct a.airline_name
                                                from routes ro natural join airlines a join reviews r using (airline_name)
                                                where r.rating >= all(select rv1.rating
                                                                        from routes r1 natural join airlines a1 join airports ai on (r1.destination_airport_iata = ai.iata_code) join reviews rv1 on (a1.airline_name = rv1.airline_name)
                                                                        where r1.destination_airport_iata = "ORD")
												limit 1);
                            

                            if(varAvgRating >= 8) then
                                set varQuality = "Excellent";
                            elseif
                            (varAvgRating >= 6.5) then
                                set varQuality = "Good";
                            elseif
                            (varAvgRating >= 5) then
                                set varQuality = "Average";
                            elseif
                            (varAvgRating >= 3.5) then
                                set varQuality = "Below Average";
                            else
                                set varQuality = "Poor";
                            end if;

                            insert into FinalTable values(varAirline,varQuality,varDestAirline);
                            end loop cloop;
                            close cusCur;

                            select *
                            from FinalTable;
                    end;''')
    cur.close()
    cur = cnx.cursor()
    cur.execute("call pp;")
    results = cur.fetchall()
    if cur.rowcount != 0:
        return render_template('searchResults.html', var = "Stored Procedure", results = results)
    cnx.commit()
    cur.close()
    return redirect("/")

@app.route('/trip-planner/', methods = ['POST'])
def render_plan_trip():
    return render_template("/tripPlanner.html")

@app.route('/plan-trip/', methods = ['POST'])
def plan_trip():
    trip_info = request.form
    userName = trip_info['userName']
    start_iata = trip_info['start_iata']
    end_iata = trip_info['end_iata']
    airline_name = trip_info['airline_name']
    cur = cnx.cursor()
    cur.execute("UPDATE User SET start_iata = %s, end_iata = %s WHERE userName = %s", (start_iata, end_iata, userName))
    cur.execute('''SELECT source_airport_iata, destination_airport_iata, airline_name
                   FROM routes JOIN airlines using (airline_id)
                   WHERE source_airport_iata like %s AND destination_airport_iata like %s;''', (start_iata, end_iata))
    results = cur.fetchall()
    cur.execute('''SELECT avg(rating), airline_name
                   FROM reviews
                   WHERE airline_name like %s;''', (airline_name, ))
    results2 = cur.fetchall()
    cnx.commit()
    cur.close()
    return render_template("/tripResults.html", results = results, results2 = results2)

@app.route('/add-review/', methods = ['POST'])
def render_add_review():
    return render_template("/addReview.html")

@app.route('/new-review/', methods = ['POST', 'GET'])
def add_review():
    review_info = request.form
    userName = review_info['userName']
    airline_name = review_info['airline_name']
    state = review_info['state']
    rating = review_info['rating']
    cur = cnx.cursor()
    cur.execute("DROP TRIGGER IF EXISTS trig2;")
    cur.close()
    cur = cnx.cursor()
    cur.execute('''CREATE TRIGGER trig2
                   BEFORE INSERT ON reviews FOR EACH ROW
                   BEGIN
                       SET @covidPos = (SELECT AVG(positive)
                                        FROM covid	
                                        WHERE state LIKE %s);
                       IF @covidPos < 504211 THEN
                           SET NEW.rating = NEW.rating + 1;
                       END IF;
                   END;''', (state, ))
    cur.close()
    cur = cnx.cursor()
    cur.execute("INSERT INTO reviews VALUES (%s, %s, %s)", (airline_name, rating, userName))
    cnx.commit()
    cur.close()
    return render_template("/crud.html")

@app.route('/add-user/', methods = ['POST'])
def render_add_user():
    return render_template("/addUser.html")

@app.route('/add/', methods = ['POST', 'GET'])
def add_user():
    user_info = request.form
    firstName = user_info['firstName']
    lastName = user_info['lastName']
    userName = user_info['userName']
    password = user_info['password']
    start_iata = ''
    end_iata = ''
    cur = cnx.cursor()
    cur.execute("SELECT COUNT(*) FROM User")
    user_id = cur.fetchone()[0] + 1
    cur.execute("INSERT INTO User(user_id, firstName, lastName, userName, password, start_iata, end_iata) VALUES (%s, %s, %s, %s, %s, %s, %s)", (user_id, firstName, lastName, userName, password, start_iata, end_iata))
    cnx.commit()
    cur.close()
    return render_template("/crud.html")

@app.route('/change-password/', methods = ['POST'])
def render_change_password():
    return render_template("/changePassword.html")

@app.route('/change/', methods = ['POST', 'GET'])
def change_password():
    user_info = request.form
    userName = user_info['userName']
    password = user_info['newPassword']
    cur = cnx.cursor()
    cur.execute("UPDATE User SET password = %s WHERE userName = %s", (password, userName))
    cnx.commit()
    cur.close()
    return render_template("/crud.html")

@app.route('/delete-user/', methods = ['POST'])
def render_delete_user():
    return render_template("/deleteUser.html")

@app.route('/delete', methods = ['POST'])
def delete_user():
    user_info = request.form
    userName = user_info['userName']
    password = user_info['password']
    cur = cnx.cursor()
    cur.execute("DELETE FROM User where userName = %s and password = %s", (userName, password))
    cnx.commit()
    cur.close()
    return render_template("/crud.html")

if __name__ == '__main__':
    app.run(debug = True, host = '127.0.0.1', port = 8080)
