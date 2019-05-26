from __future__ import division
from flask import jsonify, request, make_response
import jwt, requests, json
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import *
from base64 import b64encode
import datetime as dt
from datetime import date, datetime, timedelta
import base64, binascii, jsonpickle, string, random
from sqlalchemy import cast, desc
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask_httpauth import HTTPBasicAuth
from models import *
from controller import *
from engine_cloudinary import *
import errno
import sys

auth = HTTPBasicAuth()



def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = User.query.filter_by(id=data['id']).first()
        except:
            return jsonify({'message': 'Token is invalid!'}), 401

        return f(current_user, *args, **kwargs)

    return decorated


@app.route('/users', methods=['GET'])
def get_all_user_accounts():
    # if not current_user.admin:
    #     return jsonify({'message' : 'Cannot perform that function!'})

    users = User.query.all()

    output = []

    for user in users:
        user_data = {}
        user_data['id'] = user.id
        user_data['username'] = user.username
        user_data['password'] = user.password
        user_data['first_name'] = user.first_name
        user_data['last_name'] = user.last_name
        user_data['contact_number'] = user.contact_number
        user_data['birth_date'] = user.birth_date
        user_data['gender'] = user.gender
        output.append(user_data)

    return jsonify({'users', output})


@app.route('/user/info/<username>', methods=['GET'])
def get_one_user(username):
    # if not current_user.admin:

    #     return jsonify({'message' : 'Cannot perform that function!'})
    user = User.query.filter_by(username=username).first()

    if not user:
        return make_response('no user found!')
    user_data = {}
    user_data['id'] = user.id
    user_data['username'] = user.username
    user_data['password'] = user.password
    user_data['first_name'] = user.first_name
    user_data['last_name'] = user.last_name
    user_data['contact_number'] = user.contact_number
    user_data['birth_date'] = user.birth_date
    user_data['address'] = user.address
    user_data['gender'] = user.gender
    print(user_data)
    return jsonify({'user': user_data})

@app.route('/user/info/<user_id>/update', methods=['POST'])
def update_profile(user_id):

    data = request.get_json()
    print(data)
    user = User.query.filter_by(id=user_id).first()

    if not user:
        return make_response('no user found!')

    user.username = data['username']
    user.first_name = data['first_name']
    user.last_name = data['last_name']
    user.contact_number = data['contact_number']
    user.gender = user.gender
    user.address = user.address
    user.longitude = 50
    user.latitude = 50
    db.session.commit()

    return jsonify({'message':'profile updated successfully'})


@app.route('/signup', methods=['POST'])
def create_user():
    data = request.get_json()

    hashed_password = generate_password_hash(data['password'], method='sha256')
    address = data['address']
    google_response = requests.get(
        'https://maps.googleapis.com/maps/api/geocode/json?address=' + address + '&key=AIzaSyAOeYMvF7kPJ7ZcAjOVWiRA8PjCk5E_TsM')
    google_dict = json.loads(google_response.text)
    print(google_dict)
    latitude = 50
    longitude = 50
    #latitude = google_dict['results'][0]['geometry']['location']['lat']
    #longitude = google_dict['results'][0]['geometry']['location']['lng']
    new_user = User(username=data['username'], password=hashed_password, first_name=data['first_name'],
                    last_name=data['last_name'], contact_number=data['contact_number'], birth_date=data['birth_date'],
                    gender=data['gender'], address=data['address'], latitude=latitude, longitude=longitude)

    user = User.query.filter_by(username=data['username']).first()
    if user is None:
        db.session.add(new_user)
        db.session.commit()

        user = User.query.filter_by(username=data['username']).first()
        current_user = user.id

        bookshelf = Bookshelf(new_user.id, new_user.username)
        db.session.add(bookshelf)
        db.session.commit()

        token = jwt.encode({'id': new_user.id, 'exp': dt.datetime.now() + datetime.timedelta(days=(30 * 365))}, app.config['SECRET_KEY'])

        new_token = Token(id=current_user, token=token.decode('UTF-8'),
                          TTL=datetime.datetime.utcnow() + datetime.timedelta(days=(30 * 365)))
        db.session.add(new_token)
        db.session.commit()

        return jsonify({'token': token.decode('UTF-8')})
    else:
        return jsonify({'message':'username already used'})

#Profile Edit Current User
#INPUT REQUIRED:  JSON: {username:, first_name, last_name, birth_date, gender, contact_num}
#                 headers: {x-access-token: }
#OUTPUT: 'Change Successful'
@app.route('/user/edit', methods=['POST'])
@token_required
def edit_user(self):
    data = request.get_json()

    user = User.query.filter_by(username=data['username']).first()
    if data['first_name'] == "":
        user.first_name = data['first_name']
    else:
        user.first_name = user.first_name
    if data['last_name'] == "":
        user.last_name = data['last_name']
    else:
        user.last_name = user.last_name
    if data['birth_date'] == "":
        user.birth_date = data['birth_date']
    else:
        user.birth_date = user.birth_date
    if data['gender'] == "":
        user.gender = data['gender']
    else:
        user.gender = user.gender
    if data['contact_num'] == "":
        user.contact_number = data['contact_num']
    else:
        user.contact_number = user.contact_number
    if data['address'] == "":
        user.address = data['address']
    else:
        user.address = user.address
    db.session.commit()
    return jsonify({'message':'Change successful'}) #from make response to jsonify



@app.route('/login', methods=['GET', 'POST'])
def login():
    auth = request.get_json()

    if not auth or not auth['username'] or not auth['password']:
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})

    user = User.query.filter_by(username=auth['username']).first()
    if not user:
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})

    if check_password_hash(user.password, auth['password']):
        token = jwt.encode({'id': user.id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(days=(30 * 365))}, app.config['SECRET_KEY'])
        return jsonify({'token': token.decode('UTF-8')})

    return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})

# @app.route('/user/<int:id>/bookshelf/', methods=['GET'])
# def viewbooks(id):
#
# <<<<<<< HEAD
#     books = ContainsAssociation.query.join(Bookshelf).filter_by(bookshelf_id = id).all()
# =======

#SET USER CURRENT LOCATION TO THE DATABASE
#INPUT REQUIRED: JSON: {current_user, latitude, longitude}
#OUTPUT: "Added successful"
@app.route('/user/set/coordinates', methods=['GET', 'POST'])
def set_coordinates():
    data = request.get_json()
    user = User.query.filter_by(username=data['current_user']).first()
    user.latitude = data['latitude']
    user.longitude = data['longitude']
    db.session.commit()
    return make_response("Added successful")



@app.route('/user/bookshelf/search', methods=['GET', 'POST'])
@token_required
def searchbookshelf(self):
    data = request.get_json()

    item = '%' + data['item'] + '%'
    
    print item

    books1 = Bookshelf.query.filter_by(bookshef_owner=data['current_user']).first()
    shelf_id = books1.bookshelf_id
    
    books = ContainsAssociation.query.join(Books).filter(
        (cast(shelf_id, sqlalchemy.String).like(item)) & ((Books.title.like(item)) | (
            Books.year_published.like(item)) | (Books.types.like(item)) | cast(Books.edition, sqlalchemy.String).like(
            item) | (Books.isbn.like(item)))).all()

    if books is None:
        return jsonify({'message': 'No book found!'})

    output = []

    for book in books:
        user_data = {}
        user_data['title'] = book.title
        user_data['description'] = book.description
        user_data['year_published'] = book.year_published
        user_data['isbn'] = book.isbn
        user_data['types'] = book.types
        user_data['publisher_id'] = book.publisher_id
        output.append(user_data)
    print output
    return jsonify({'book': output})


@app.route('/user/bookshelf', methods=['GET', 'POST'])
@token_required
def viewbook(self):
    data = request.get_json()
    books = Bookshelf.query.filter_by(bookshef_owner= data['current_user']).first()
    shelf_id = books.bookshelf_id

    contains = ContainsAssociation.query.filter_by(shelf_id=shelf_id).first()
    if contains is None:
        return make_response('no books found')
    shelf_id = contains.shelf_id
    Book = Books.query.join(ContainsAssociation).filter_by(shelf_id=shelf_id).all()

    # q = (db.session.query(Books, Bookshelf, ContainsAssociation, Author)
    #      .filter(Bookshelf.bookshef_owner == id)
    #      .filter(ContainsAssociation.shelf_id == Bookshelf.bookshelf_id)
    #      .filter(Books.book_id == ContainsAssociation.book_id)
    #      .filter(Author.author_id == Books.publisher_id)
    #      .all())

    output = []
    if (Book is None) or (contains is None) or (books is None):
        return make_response('no books found')

    for book in Book:
        user_data = {}
        book_contains = ContainsAssociation.query.filter_by(book_id=book.book_id).first()
        user_data['title'] = book.title
        user_data['book_id'] = book.book_id
        genre = HasGenreAssociation.query.filter_by(bookId=book.book_id).first()
        genre_final = Genre.query.filter_by(id_genre=genre.genreId).first()
        user_data['genre'] = genre_final.genre_name
        user_data['book_cover'] = book.book_cover
        book_author = WrittenByAssociation.query.filter_by(book_id=book.book_id).first()
        author = Author.query.filter_by(author_id=book_author.author_id).first()
        user_data['owner_bookshelfid'] = books.bookshelf_id
        user_data['author_name'] = author.author_name
        user_data['description'] = book.description
        user_data['edition'] = book.edition
        user_data['year'] = book.year_published
        user_data['isbn'] = book.isbn
        user_data['types'] = book.types
        user_data['publisher_id'] = book.publisher_id
        output.append(user_data)

    return jsonify({'book': output})

#VIEW BOOK OF A USER (Di ko sure kung magamit ni sa Mobile. Basig lahi ila pag display og libro)
#INPUT REQUIRED: JSON: { book_id, username(owner of book), current_user(viewer)}
              #: headers: {x-access-token}
#OUTPUT:
# fullname of owner
# username of owner
# profpic of viwer(comments)
# ..
@app.route('/user/bookshelf/book', methods=['GET', 'POST'])
@token_required
def view_one_book(self):
    data = request.get_json()
    book = Books.query.filter_by(book_id=data['book_id']).first()

    output = []
    if book is None:
        return make_response('no books found')

    book = Books.query.filter_by(book_id=data['book_id']).first()
    user = User.query.filter_by(username=data['username']).first()
    viewer = User.query.filter_by(username=data['current_user']).first()
    print user.username
    bookshelf = Bookshelf.query.filter_by(bookshef_owner=user.username).first()
    contains = ContainsAssociation.query.filter((ContainsAssociation.book_id == data['book_id']) &
                                                 (ContainsAssociation.shelf_id == bookshelf.bookshelf_id)).first()
    publisher = Publisher.query.filter_by(publisher_id=book.publisher_id).first()
    borrow_check = BorrowsAssociation.query.filter((BorrowsAssociation.owner_shelf_id == bookshelf.bookshelf_id)
                                           & (BorrowsAssociation.bookid == data['book_id'])).first()
    rent_check = RentAssociation.query.filter((RentAssociation.owner_shelf_id == bookshelf.bookshelf_id)
                                           & (RentAssociation.bookid == data['book_id'])).first()
    output = []

    user_data = {}
    if borrow_check is not None:
        user_data['check'] = 'Borrowed'
        borrower = User.query.filter_by(id=borrow_check.borrower).first()
        user_data['borrower'] = borrower.username
        user_data['borrower_fname'] = borrower.first_name
        user_data['borrower_lname'] = borrower.last_name
        user_data['owner_username'] = data['username']
        user_data['method'] = 'Borrow'
    elif rent_check is not None:
        user_data['check'] = 'Rented'
        borrower = User.query.filter_by(id=rent_check.borrower).first()
        user_data['borrower'] = borrower.username
        user_data['borrower_fname'] = borrower.first_name
        user_data['borrower_lname'] = borrower.last_name
        user_data['owner_username'] = data['username']
        user_data['total'] = rent_check.total
        user_data['method'] = 'Rent'
    else:
        user_data['check'] = 'None'
    user_data['owner'] = user.first_name+" "+ user.last_name
    user_data['username'] = user.username
    user_data['viewer_name'] = viewer.first_name+" "+ viewer.last_name
    user_data['viewer_username'] = viewer.username
    user_data['owner_bookshelfid'] = bookshelf.bookshelf_id
    user_data['title'] = book.title
    user_data['book_id'] = book.book_id
    user_data['year'] = book.year_published
    user_data['availability'] = contains.availability
    user_data['quantity'] = contains.quantity
    user_data['book_cover'] = book.book_cover
    user_data['edition'] = book.edition
    user_data['year'] = book.year_published
    genre = HasGenreAssociation.query.filter_by(bookId=book.book_id).first()
    genre_name = Genre.query.filter_by(id_genre=genre.genreId).first()
    user_data['genre'] = genre_name.genre_name
    book_author = WrittenByAssociation.query.filter_by(book_id=book.book_id).first()
    author = Author.query.filter_by(author_id=book_author.author_id).first()
    user_data['author_name'] = author.author_name
    user_data['description'] = book.description
    user_data['price'] = contains.price
    user_data['price_rate'] = contains.price_rate
    user_data['methods'] = contains.methods
    user_data['contains_id'] = contains.contains_id
    user_data['isbn'] = book.isbn
    user_data['types'] = book.types
    user_data['publisher_id'] = publisher.publisher_name
    #Pwede ni ibalhin og lain na function, mo display ni sa rating og rating breakdown
    yourRating = BookRateAssociation.query.filter((BookRateAssociation.book_id == contains.contains_id) & (BookRateAssociation.user_id == viewer.id)).first()
    if yourRating is not None:
        user_data['rating'] = yourRating.rating
    else:
        user_data['rating'] = int('1')
    totalRate = BookRateTotal.query.filter_by(bookRated=contains.contains_id).first()
    if totalRate is not None:
        user_data['totalRate'] = ((totalRate.totalRate/totalRate.numofRates))
        user_data['numofRates'] = totalRate.numofRates
        book_rate = BookRateAssociation.query.filter_by(book_id=contains.contains_id).all()
        num5 = 0
        num4 = 0
        num3 = 0
        num2 = 0
        num1 = 0
        for book in book_rate:
            print(book.rating)
            if book.rating == 1:
                num1 = num1 + 1
            elif book.rating == 2:
                num2 = num2 + 1
            elif book.rating == 3:
                num3 = num3 + 1
            elif book.rating == 4:
                num4 = num4 + 1
            else:
                num5 = num5 + 1
        user_data['num1'] = (num1 / int(totalRate.numofRates))*100 #Percentage kada rating(Rating Breakdown)
        user_data['num2'] = (num2 / int(totalRate.numofRates))*100
        user_data['num3'] = (num3 / int(totalRate.numofRates))*100
        user_data['num4'] = (num4 / int(totalRate.numofRates))*100
        user_data['num5'] = (num5 / int(totalRate.numofRates))*100
    else: #No rating on book
        user_data['totalRate'] = 0.0
        user_data['numofRates'] = 0

    output.append(user_data)
    print(output)
    return jsonify({'book': output})

@app.route('/user/bookshelf/bookdb', methods=['GET', 'POST'])
@token_required
def view_one_bookdb(self):
    data = request.get_json()
    book = Books.query.filter_by(book_id=data['book_id']).first()

    output = []
    if book is None:
        return make_response('no books found')

    book = Books.query.filter_by(book_id=data['book_id']).first()
    user = User.query.filter_by(username=data['username']).first()
    viewer = User.query.filter_by(username=data['current_user']).first()
    bookshelf = Bookshelf.query.filter_by(bookshef_owner=user.username).first()
    contains1 = ContainsAssociation.query.filter((ContainsAssociation.book_id == data['book_id']) &
                                                 (ContainsAssociation.shelf_id != bookshelf.bookshelf_id)).all()
    publisher = Publisher.query.filter_by(publisher_id=book.publisher_id).first()

    for  contains in contains1:
        user_data = {}
        user_owner = Bookshelf.query.filter_by(bookshelf_id=contains.shelf_id).first()
        user_owner_details = User.query.filter_by(username=user_owner.bookshef_owner).first()
        user_data['other_owner'] = user_owner_details.first_name + ' ' + user_owner_details.last_name
        user_data['other_username'] = user_owner_details.username
        user_data['owner_bookshelfid'] = user_owner.bookshelf_id
        user_data['title'] = book.title
        user_data['book_id'] = book.book_id
        user_data['year'] = book.year_published
        user_data['availability'] = contains.availability
        user_data['quantity'] = contains.quantity
        user_data['book_cover'] = book.book_cover
        user_data['edition'] = book.edition
        user_data['year'] = book.year_published
        genre = HasGenreAssociation.query.filter_by(bookId=book.book_id).first()
        genre_name = Genre.query.filter_by(id_genre=genre.genreId).first()
        user_data['genre'] = genre_name.genre_name
        book_author = WrittenByAssociation.query.filter_by(book_id=book.book_id).first()
        author = Author.query.filter_by(author_id=book_author.author_id).first()
        user_data['author_name'] = author.author_name
        user_data['description'] = book.description
        user_data['price'] = contains.price
        user_data['price_rate'] = contains.price_rate
        user_data['methods'] = contains.methods
        user_data['contains_id'] = contains.contains_id
        user_data['isbn'] = book.isbn
        user_data['types'] = book.types
        user_data['publisher_id'] = publisher.publisher_name
        #Pwede ni ibalhin og lain na function, mo display ni sa rating og rating breakdown
        yourRating = BookRateAssociation.query.filter((BookRateAssociation.book_id == contains.contains_id) & (BookRateAssociation.user_id == viewer.id)).first()
        if yourRating is not None:
            user_data['rating'] = yourRating.rating
        else:
            user_data['rating'] = int('1')
        totalRate = BookRateTotal.query.filter_by(bookRated=contains.contains_id).first()
        if totalRate is not None:
            user_data['totalRate'] = ((totalRate.totalRate/totalRate.numofRates))
            user_data['numofRates'] = totalRate.numofRates
            book_rate = BookRateAssociation.query.filter_by(book_id=contains.contains_id).all()
            num5 = 0
            num4 = 0
            num3 = 0
            num2 = 0
            num1 = 0
            for book in book_rate:
                print(book.rating)
                if book.rating == 1:
                    num1 = num1 + 1
                elif book.rating == 2:
                    num2 = num2 + 1
                elif book.rating == 3:
                    num3 = num3 + 1
                elif book.rating == 4:
                    num4 = num4 + 1
                else:
                    num5 = num5 + 1
            user_data['num1'] = (num1 / int(totalRate.numofRates))*100 #Percentage kada rating(Rating Breakdown)
            user_data['num2'] = (num2 / int(totalRate.numofRates))*100
            user_data['num3'] = (num3 / int(totalRate.numofRates))*100
            user_data['num4'] = (num4 / int(totalRate.numofRates))*100
            user_data['num5'] = (num5 / int(totalRate.numofRates))*100
        else: #No rating on book
            user_data['totalRate'] = 0.0
            user_data['numofRates'] = 0

        output.append(user_data)
    print(output)
    return jsonify({'book': output})




#Display Comments on a user's book
#INPUT: JSON: {username(owner of libro), book_id}
#       headers: {x-access-token}
#OUTPUT: All comments

@app.route('/bookshelf/comments/book', methods=['GET','POST'])
@token_required
def get_comments(self):
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    book = Books.query.filter_by(book_id=data['book_id']).first()
    bookshelf = Bookshelf.query.filter_by(bookshef_owner=user.username).first()
    contains = ContainsAssociation.query.filter((ContainsAssociation.book_id == book.book_id) &
                                                (ContainsAssociation.shelf_id == bookshelf.bookshelf_id)).first()
    comments = BookCommentAssociation.query.filter_by(bookshelf_id=contains.contains_id).all()
    output=[]
    for comment in comments:
        comments1={}
        comments1['comment'] = comment.comment
        fmt = "%a, %d %b %Y %H:%M:%S GMT"
        now = comment.date.strftime('%a, %d %b %Y %H:%M') #Convert time to format(Ex. Sat, 26 Jan 2018 13:43)
        comments1['date'] = now
        user_commenter = User.query.filter_by(id=comment.user_id).first()
        comments1['user_fname'] = user_commenter.first_name
        comments1['user_lname'] = user_commenter.last_name
        comments1['user_username'] = user_commenter.username
        output.append(comments1)

    return jsonify({'comments': output})


#Edit  Book
#INPUT: JSON: {username(owner of libro), book_id, quantity, methods(For Sale, For Borrow, For Rent), price(0 if For Borrow)}
#             headers: {x-access-token}
#OUTPUT: 'Successful'
# di pani final, vague pa kaau para sa methods og price
@app.route('/user/edit/book', methods=['POST'])
@token_required
def edit_book(self):
    data = request.get_json()
    book = Books.query.filter_by(book_id=data['book_id']).first()
    bookshelf = Bookshelf.query.filter_by(bookshef_owner=data['username']).first()
    contains = ContainsAssociation.query.filter((ContainsAssociation.book_id == book.book_id) &
                                                (ContainsAssociation.shelf_id == bookshelf.bookshelf_id)).first()
    contains.quantity = data['quantity']
    contains.methods = data['methods']
    contains.price = data['price']
    contains.price_rate = data['price_rate']
    db.session.commit()
    return make_response('Successful')

#Remove Book
#INPUT: JSON: {book_id, username(owner)}
#       headers: {x-access-token}
#OUTPUT: Successful
@app.route('/user/bookshelf/remove/book', methods=['POST', 'GET'])
@token_required
def remove_book(self):
    data = request.get_json()
    book = Books.query.filter_by(book_id=data['book_id']).first()
    bookshelf = Bookshelf.query.filter_by(bookshef_owner=data['username']).first()
    contains = ContainsAssociation.query.filter((ContainsAssociation.book_id == book.book_id)&
                                                 (ContainsAssociation.shelf_id == bookshelf.bookshelf_id)).first()
    bookrate = BookRateAssociation.query.filter_by(book_id=contains.contains_id).first()
    bookratetotal = BookRateTotal.query.filter_by(bookRated=contains.contains_id).first()

    if bookrate is not None and bookratetotal is not None:
        db.session.delete(bookratetotal)
        db.session.commit()
        db.session.delete(bookrate)
        db.session.commit()
    db.session.delete(contains)
    db.session.commit()
    return make_response('Successful')



#Comment Book (Di ko sure kung magamit sa Mobile, kay ang comments sa web kay ContainsAssociation(libro sa user),
                                                                    # dili sa tanan na kaparehas og libro))
#Input: JSON: {username, contains_id, comment}
#       headers: {x-access-token}
#OUTPUT:
#If wala na associate ang libro sa user
#   "Could not comment"
#else
#   "Comment posted"

#Rate Book
#Input: JSON: {username, contains_id, ratings}
#       headers: {x-access-token}
#Output: 'Rate posted!'
@app.route('/rate-book', methods=['GET', 'POST'])
@token_required
def ratebook(self):
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    bookshelf_id = Bookshelf.query.filter_by(bookshef_owner=data['owner']).first()
    book = Books.query.filter_by(book_id=data['book_id']).first()
    contains = ContainsAssociation.query.filter((ContainsAssociation.book_id == book.book_id) & 
    (ContainsAssociation.shelf_id == bookshelf_id.bookshelf_id)).first()
    if contains is None:
        #Walay association ang tag-iya og libro
        return make_response('Could not rate!')
    else:
        rate_check = BookRateAssociation.query.filter((BookRateAssociation.book_id == contains.contains_id) & (BookRateAssociation.user_id == user.id)).first()
        if rate_check is None:
            #naay comment sa db so gipasagdaan lang nako hahaha, pwede rapud tangtangon sa db
            #rate_check = gi check if naka rate na ang user sa libro
            #if wala kay i-add niya ang rating
            rate = BookRateAssociation(comment="", rating=data['ratings'], user_id=user.id, book_id=contains.contains_id)
            db.session.add(rate)
            db.session.commit()
            totalRate = BookRateTotal.query.filter_by(bookRated=contains.contains_id).first()
            if totalRate is None:
                #if wala pa ga exist ang total rating or wala pa jud na rate ang libro
                # mag create siyag total rating
                total_rate = BookRateTotal(bookRated=contains.contains_id, numofRates=1, totalRate=data['ratings'])
                db.session.add(total_rate)
                db.session.commit()
                print('new rate')
            else:
                #if naa ga exist or na rate na sauna ang libro
                # i-add niya ang number of Rates (which is kapila na rate ang libro)
                # tapos i-add niya rating na input sa total ratings
                totalRate.numofRates = totalRate.numofRates + 1
                totalRate.totalRate = totalRate.totalRate + float(data['ratings'])
                db.session.commit()
                print('added!!')
        else:
            #naa ang rate_check so naka rate na ang user sa libro sauna
            #so gi ilisdan ra ang rating sa rate association tapos gi ilisdan sad ang total rating para sakto
            #bahalag na ilisdan
            totalRate2 = BookRateTotal.query.filter_by(bookRated=contains.contains_id).first()
            totalRate2.totalRate = totalRate2.totalRate - rate_check.rating
            rate_check.rating = data['ratings']
            totalRate2.totalRate = totalRate2.totalRate + float(data['ratings'])
            db.session.commit()


    return make_response('Rate posted!')

@app.route('/comment-book', methods=['GET', 'POST'])
@token_required
def commentbook(self):
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    bookshelf = Bookshelf.query.filter_by(bookshef_owner=data['owner']).first()
    book = Books.query.filter_by(book_id=data['book_id']).first()
    contains = ContainsAssociation.query.filter(
        (ContainsAssociation.shelf_id == bookshelf.bookshelf_id) & (ContainsAssociation.book_id == book.book_id)
    ).first()
    if contains is None:
        return make_response('Could not comment!')
    else:
        comment = BookCommentAssociation(comment=data['comment'], user_id=user.id, bookshelf_id=contains.contains_id)
    db.session.add(comment)
    db.session.commit()
    return make_response('Comment posted!')

@app.route('/rate/user', methods=['GET', 'POST'])
@token_required
def rate_user(self):
    data = request.get_json()
    current_user = User.query.filter_by(username=data['current_user']).first()
    user = User.query.filter_by(username=data['username']).first()
    if user is None:
        return make_response('Could not rate!')
    else:
        rate_check = UserRateAssociation.query.filter((UserRateAssociation.user_idRater == current_user.id) & (UserRateAssociation.user_idRatee == user.id)).first()
        if rate_check is None:
            rate = UserRateAssociation(comment="", rating=data['ratings'], user_idRatee=user.id, user_idRater=current_user.id)
            db.session.add(rate)
            db.session.commit()
            totalRate = UserRateTotal.query.filter_by(userRatee=user.id).first()
            if totalRate is None:
                total_rate = UserRateTotal(userRatee=user.id, numOfRates=1, totalRate=data['ratings'])
                db.session.add(total_rate)
                db.session.commit()
                print('new rate')
            else:
                totalRate.numOfRates = totalRate.numOfRates + 1
                totalRate.totalRate = totalRate.totalRate + float(data['ratings'])
                db.session.commit()
                print('added!!')
        else:
            totalRate2 = UserRateTotal.query.filter_by(userRatee=user.id).first()
            totalRate2.totalRate = totalRate2.totalRate - rate_check.rating
            rate_check.rating = data['ratings']
            totalRate2.totalRate = totalRate2.totalRate + float(data['ratings'])
            db.session.commit()


    return make_response('Rate posted!')

@app.route('/comment/user', methods=['GET', 'POST'])
@token_required
def comment_user(self):
    data = request.get_json()
    current_user = User.query.filter_by(username=data['current_user']).first()
    user = User.query.filter_by(username=data['username']).first()
    if user is None:
        return make_response('Could not comment!')
    else:
        comment = UserCommentAssociation(comment=data['comment'], user_idCommenter=current_user.id, user_idCommentee=user.id)
    db.session.add(comment)
    db.session.commit()
    return make_response('Comment posted!')

@app.route('/user/comments', methods=['GET','POST'])
@token_required
def get_user_comments(self):
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    comments = UserCommentAssociation.query.filter_by(user_idCommentee=user.id).all()
    output=[]
    for comment in comments:
        comments1={}
        comments1['comment'] = comment.comment
        fmt = "%a, %d %b %Y %H:%M:%S GMT"
        now = comment.date.strftime('%a, %d %b %Y %H:%M')
        comments1['date'] = now
        user_commenter = User.query.filter_by(id=comment.user_idCommenter).first()
        comments1['user_fname'] = user_commenter.first_name
        comments1['user_lname'] = user_commenter.last_name
        comments1['user_username'] = user_commenter.username
        output.append(comments1)

    return jsonify({'comments': output})

@app.route('/user/ratings', methods=['GET', 'POST'])
@token_required
def get_user_ratings(self):
    data = request.get_json()
    output = []
    user_data = {}
    user = User.query.filter_by(username=data['username']).first()
    current_user = User.query.filter_by(username=data['current_user']).first()
    yourRating = UserRateAssociation.query.filter(
        (UserRateAssociation.user_idRatee == user.id) & (UserRateAssociation.user_idRater == current_user.id)).first()
    if yourRating is not None:
        user_data['rating'] = yourRating.rating
    else:
        user_data['rating'] = int('1')
    totalRate = UserRateTotal.query.filter_by(userRatee=user.id).first()
    if totalRate is not None:
        user_data['totalRate'] = ((totalRate.totalRate / totalRate.numOfRates))
        user_data['numofRates'] = totalRate.numOfRates
        book_rate = UserRateAssociation.query.filter_by(user_idRatee=user.id).all()
        num5 = 0
        num4 = 0
        num3 = 0
        num2 = 0
        num1 = 0
        for book in book_rate:
            print(book.rating)
            if book.rating == 1:
                num1 = num1 + 1
            elif book.rating == 2:
                num2 = num2 + 1
            elif book.rating == 3:
                num3 = num3 + 1
            elif book.rating == 4:
                num4 = num4 + 1
            else:
                num5 = num5 + 1
        user_data['num1'] = (num1 / int(totalRate.numOfRates)) * 100
        user_data['num2'] = (num2 / int(totalRate.numOfRates)) * 100
        user_data['num3'] = (num3 / int(totalRate.numOfRates)) * 100
        user_data['num4'] = (num4 / int(totalRate.numOfRates)) * 100
        user_data['num5'] = (num5 / int(totalRate.numOfRates)) * 100
    else:
        user_data['totalRate'] = 0.0
        user_data['numofRates'] = 0

    output.append(user_data)
    return jsonify({'ratings': output})

#ADDBOOK
#INPUT REQUIRED: JSON: {publisher_name, title, isbn, year(Text-Date of Published), description
#                        author_name(First & Last Name), current_user, category, book_cover(text),
#                       description,  price(0 if borrow), genre, quantity, method(For Sale, For Rent, For Borrow)}
#                headers: {x-access-token}
#Category: Fiction, Non-Fiction, Educational
#Genre(atong nasabotan):
#               fiction = {'Action', 'Adventure', 'Drama', 'Horror', 'Mystery', 'Mythology'}
#            non_fiction = {'Biography', 'Essay', 'Journalism', 'Personal Narrative', 'Reference Book', 'Speech'}
#            educational = {'English', 'Math', 'History', 'Science'}
# IMPORTANT NOTE: Kung mag testing mo ayaw ibalik2 ang ISBN tapos lahi na title, description og year
@app.route('/user/addbook', methods=['POST'])
@token_required
def addbook(self):

    data = request.get_json()
    print(data['publisher_name'])
    book = Books.query.filter((Books.title == data['title']) &
                              (Books.year_published == data['year']) & (Books.isbn == data['isbn'])
                              & (Books.description == data['description'])).first()
    publisher = Publisher.query.filter(Publisher.publisher_name == data['publisher_name']).first()
    author = Author.query.filter((Author.author_name == data['author_name'])).first()
    if (book is None) or (publisher is None) or (author is None):
        if publisher is None:
            newPublisher = Publisher(publisher_name= data['publisher_name'])
            db.session.add(newPublisher)
            db.session.commit()
            publisher_id = Publisher.query.filter((Publisher.publisher_name == data['publisher_name'])).first()
            if author is None:
                author = Author(author_name=data['author_name'])
                db.session.add(author)
                db.session.commit()
            elif author is not None:
                author = Author.query.filter((Author.author_name == data['author_name'])).first()
        elif publisher is not None:
            publisher_id = Publisher.query.filter((Publisher.publisher_name == data['publisher_name'])).first()
            if author is None:
                author = Author(data['author_name'])
                db.session.add(author)
                db.session.commit()
            elif author is not None:
                author = Author.query.filter(Author.author_name == data['author_name']).first()

        publisher = Publisher.query.filter(Publisher.publisher_name == data['publisher_name']).first()
        publisher_id = publisher.publisher_id
        bookshelf = Bookshelf.query.filter_by(bookshef_owner=data['current_user']).first()
        book_check = Books.query.filter_by(isbn=data['isbn']).first()
        author = Author.query.filter((Author.author_name == data['author_name'])).first()
        if book_check is not None and (author is not None):
            author1 = WrittenByAssociation.query.filter((WrittenByAssociation.book_id == book_check.book_id) & (WrittenByAssociation.author_id == author.author_id)).first()
        if book_check is not None and (author1 is not None):
            book_check1 = ContainsAssociation.query.filter((ContainsAssociation.shelf_id == bookshelf.bookshelf_id) and
                                                           (ContainsAssociation.book_id == book_check.book_id)).first()
            if book_check1 is not None:
                #book_check1 = gi check if ga exist ba ang libro sa bookshelf sa user
                return make_response('The book is already in your bookshelf!')

        print(book_check)
        book = Books(title = data['title'], year_published = data['year'], isbn =data['isbn'], types=None, edition=None, publisher_id= publisher_id, description=data['description'], book_cover=data['book_cover'])
        db.session.add(book)
        db.session.commit()
        get_category = Category.query.filter_by(category_name=data['category']).first()
        if get_category is None:
            set_category = Category(category_name=data['category'])
            db.session.add(set_category)
            db.session.commit()

        get_category = Category.query.filter_by(category_name=data['category']).first()
        category = CategoryAssociation(book_id=book.book_id, category_id=get_category.category_id)
        db.session.add(category)
        db.session.commit()

        get_genre = Genre.query.filter_by(genre_name=data['genre']).first()
        if get_genre is None:
            set_genre = Genre(genre_name=data['genre'])
            db.session.add(set_genre)
            db.session.commit()

        get_genre = Genre.query.filter_by(genre_name=data['genre']).first()
        genre = HasGenreAssociation(genreId=get_genre.id_genre, bookId=book.book_id)
        db.session.add(genre)
        db.session.commit()

        author = Author.query.filter_by(author_name=data['author_name']).first()
        written = WrittenByAssociation(author.author_id, book.book_id)
        db.session.add(written)
        db.session.commit()

        bookshelf = Bookshelf.query.filter_by(bookshef_owner=data['current_user']).first()
        shelf_id = bookshelf.bookshelf_id
        book1 = Books.query.filter_by(isbn=data['isbn']).first()
        print(data['quantity'])
        contain = ContainsAssociation(shelf_id=shelf_id, book_id=book.book_id, quantity= data['quantity'], availability='YES', methods=data['method'], price=data['price'], price_rate=data['price_rate'])
        check = ContainsAssociation.query.filter((ContainsAssociation.shelf_id == shelf_id) and
                                                  (ContainsAssociation.book_id == book1.book_id)).first()
        db.session.add(contain)
        db.session.commit()

        followers = Followers.query.filter_by(followed_username=data['current_user']).all()
        for follower in followers:
            follower_user = User.query.filter_by(username=follower.follower_username).first()
            followed_user = User.query.filter_by(username=data['current_user']).first()
            book = Books.query.filter((Books.title == data['title']) &
                                      (Books.year_published == data['year']) & (Books.isbn == data['isbn'])
                                      & (Books.description == data['description'])).first()
            notification = Notifications(current_user=follower_user.id, user_id=followed_user.id, book_id=book.book_id,
                                         bookshelf_id=followed_user.id,
                                         last_open=None, type='follower_new_book')
            db.session.add(notification)
            db.session.commit()
        current_user = User.query.filter_by(username=data['current_user']).first()
        actlogs = ActLogs(current_user_id=current_user.id, other_user_id=None,
                          bookid=None, status=0, type='addbook')
        db.session.add(actlogs)
        db.session.commit()

        return jsonify({'message': 'New book created!'})

    else:

        bookshelf = Bookshelf.query.filter_by(bookshef_owner=data['current_user']).first()
        shelf_id = bookshelf.bookshelf_id

        bookquantity = ContainsAssociation.query.filter((ContainsAssociation.shelf_id == shelf_id) & (ContainsAssociation.book_id == book.book_id)).first()
        if bookquantity is None:
            contain = ContainsAssociation(shelf_id=shelf_id, book_id=book.book_id, quantity= data['quantity'], availability='YES', methods=data['method'], price=data['price'], price_rate=data['price_rate'])
            db.session.add(contain)
            db.session.commit()
            print('book quantity is None')
        else:
            curQuant = bookquantity.quantity
            print('book quantity is not None')
            bookquantity.quantity = int(curQuant) + 1
            db.session.commit()

    followers = Followers.query.filter_by(followed_username=data['current_user']).all()
    for follower in followers:
        follower_user = User.query.filter_by(username=follower.follower_username).first()
        followed_user = User.query.filter_by(username=data['current_user']).first()
        book = Books.query.filter((Books.title == data['title']) &
                                  (Books.year_published == data['year']) & (Books.isbn == data['isbn'])
                                  & (Books.description == data['description'])).first()
        notification = Notifications(current_user=follower_user.id, user_id=followed_user.id, book_id=book.book_id, bookshelf_id=followed_user.id,
                                     last_open=None, type='follower_new_book')
        db.session.add(notification)
        db.session.commit()

    current_user = User.query.filter_by(username=data['current_user']).first()
    actlogs = ActLogs(current_user_id=current_user.id, other_user_id=None,
                      bookid=None, status=0, type='addbook')
    db.session.add(actlogs)
    db.session.commit()

    return jsonify({'message': 'New book counted!'})


# addbook check by ISBN
@app.route('/mobile/user/isbn_check/<isbn>', methods=['GET', 'POST'])
@token_required
def mobile_isbn_check(self, isbn):
    # data = request.get_json()

    book = Books.query.filter_by(isbn=isbn).first()

    if book is not None:
        output = []
        user_data = {}
        user_data['title'] = book.title
        user_data['book_id'] = book.book_id
        user_data['book_cover'] = book.book_cover
        user_data['description'] = book.description
        book_author = WrittenByAssociation.query.filter_by(
            book_id=book.book_id).first()
        author = Author.query.filter_by(
            author_id=book_author.author_id).first()
        publisher = Publisher.query.filter_by(
            publisher_id=book.publisher_id).first()
        user_data['publishers'] = publisher.publisher_name
        user_data['author_name'] = author.author_name
        user_data['year'] = book.year_published
        user_data['isbn'] = book.isbn
        user_data['types'] = book.types
        output.append(user_data)
        return jsonify({'data': output})  # naa kay libro nakit.an sa db
    else:
        url = "https://openlibrary.org/api/books?bibkeys=ISBN:{0}&jscmd=data&format=json".format(
            isbn)
        url2 = "https://www.googleapis.com/books/v1/volumes?q=isbn:{0}&key=AIzaSyAOeYMvF7kPJ7ZcAjOVWiRA8PjCk5E_TsM".format(
            isbn)
        output = []
        book = {}
        response2 = requests.get(url2)
        resp2 = json.loads(response2.text)  # ga requests ka sa API sa google
        response = requests.get(url)
        # ga requests ka sa API sa OPENLibrary
        resp = json.loads(response.text)
        book['isbn'] = isbn
        if (resp2['totalItems'] == 0) and (not resp):  # walay kay nakuha sa API sa duha
            return make_response('No books found!')
        elif not resp:  # wala kay nakuha sa API sa OpenLibrary so ang google imo gamiton
            # gikuha nimong title
            book['title'] = resp2['items'][0]['volumeInfo']['title']
            # usahay walay publisher gikan sa google
            if 'publisher' in resp2['items'][0]['volumeInfo']:
                # gi store nimo ang publisher kay naa
                book['publishers'] = resp2['items'][0]['volumeInfo']['publisher']
            else:
                book['publishers'] = ''  # pag wala
            book['book_cover'] = resp2['items'][0]['volumeInfo']['imageLinks']['thumbnail']
            book['author_name'] = resp2['items'][0]['volumeInfo']['authors'][0]
            book['description'] = resp2['items'][0]['volumeInfo']['description']
            book['year'] = resp2['items'][0]['volumeInfo']['publishedDate']
        else:  # pag naa kay makuha sa duha
            index = "ISBN:{0}".format(isbn)
            book['title'] = resp[index]['title']  # gikan na ni sa OpenLibrary
            book['publishers'] = resp[index]['publishers'][0]['name']
            if 'cover' in resp[index]:  # usahay way cover sad ma return
                book['book_cover'] = resp[index]['cover']['large']
            else:
                book['cover'] = '#'
            book['author_name'] = resp[index]['authors'][0]['name']
            date1 = resp[index]['publish_date']
            book['year'] = date1
            if resp2['totalItems'] != 0:  # pag naa sad sa googlebooks
                book['title'] = resp2['items'][0]['volumeInfo'][
                    'title']  # gistore ang title gikan sa GoogleBooks kay mas tarong ilang title, publisher, authorname og publishedDate
                if 'publisher' in resp2['items'][0]['volumeInfo']:
                    book['publishers'] = resp2['items'][0]['volumeInfo']['publisher']
                else:
                    book['publishers'] = ''
                if 'authors' in resp2['items'][0]['volumeInfo']:
                    book['author_name'] = resp2['items'][0]['volumeInfo']['authors'][0]
                book['description'] = resp2['items'][0]['volumeInfo']['description']
                book['year'] = resp2['items'][0]['volumeInfo']['publishedDate']
        output.append(book)
    return jsonify({'book': output})


# addbook check by TITLE
@app.route('/mobile/user/title_check/<title>', methods=['GET', 'POST'])
@token_required
def mobile_title_check(self, title):
    url = "https://www.googleapis.com/books/v1/volumes?q=intitle:{0}&key=AIzaSyAOeYMvF7kPJ7ZcAjOVWiRA8PjCk5E_TsM&maxResults=40".format(
        title)
    response = requests.get(url)
    resp = json.loads(response.text)
    books = Books.query.filter(Books.title.like(title)).all()
    if int(resp['totalItems']) == 0 and books is None:
        return make_response('No books found')
    elif books is not None:
        output = []
        for book in books:
            books1 = {}
            books1['title'] = book.title
            books1['book_id'] = book.book_id
            books1['book_cover'] = book.book_cover
            books1['description'] = book.description
            book_author = WrittenByAssociation.query.filter_by(
                book_id=book.book_id).first()
            author = Author.query.filter_by(
                author_id=book_author.author_id).first()
            publisher = Publisher.query.filter_by(
                publisher_id=book.publisher_id).first()
            books1['publishers'] = publisher.publisher_name
            books1['author_name'] = author.author_name
            books1['year'] = book.year_published
            books1['isbn'] = book.isbn
            books1['types'] = book.types
            output.append(books1)

        if int(resp['totalItems']) == 0:  # way libro gikan sa google
            return jsonify(output)
        else:
            for book_item in resp['items']:
                books = {}
                if ((('publisher' in book_item['volumeInfo']) and ('industryIdentifiers' in book_item['volumeInfo']))
                    and (('imageLinks' in book_item['volumeInfo']) and ('authors' in book_item['volumeInfo']))) \
                        and ('description' in book_item['volumeInfo'] and 'publishedDate' in book_item['volumeInfo']):
                    books['title'] = book_item['volumeInfo']['title']
                    books['publishers'] = book_item['volumeInfo']['publisher']
                    books['isbn'] = book_item['volumeInfo']['industryIdentifiers'][0]['identifier']
                    books['book_cover'] = book_item['volumeInfo']['imageLinks']['thumbnail']
                    books['author_name'] = book_item['volumeInfo']['authors'][0]
                    books['description'] = book_item['volumeInfo']['description']
                    books['year'] = book_item['volumeInfo']['publishedDate']
                    output.append(books)
                else:
                    continue
            return jsonify({'book': output})


# search by authorname
@app.route('/mobile/user/author_check/<author_name>', methods=['GET', 'POST'])
@token_required
def mobile_author_check(self, author_name):
    author = author_name
    url = "https://www.googleapis.com/books/v1/volumes?q=inauthor:{0}&key=AIzaSyAOeYMvF7kPJ7ZcAjOVWiRA8PjCk5E_TsM&maxResults=40".format(
        author)
    response = requests.get(url)
    resp = json.loads(response.text)
    author = Author.query.filter_by(author_name=author_name).first()
    if int(resp['totalItems']) == 0 and author is None:
        return make_response('No books found')

    elif int(resp['totalItems']) == 0:  # way libro gikan sa google
        output = []
        if author is not None:
            written = WrittenByAssociation.query.filter_by(
                author_id=author.author_id).all()
            for writtenbook in written:  # mga libro sa author gikan sa db
                book = Books.query.filter_by(
                    book_id=writtenbook.book_id).first()
                books1 = {}
                books1['title'] = book.title
                books1['book_id'] = int(book.book_id)
                books1['book_cover'] = book.book_cover
                books1['description'] = book.description
                book_author = WrittenByAssociation.query.filter_by(
                    book_id=book.book_id).first()
                author = Author.query.filter_by(
                    author_id=book_author.author_id).first()
                publisher = Publisher.query.filter_by(
                    publisher_id=book.publisher_id).first()
                books1['publishers'] = publisher.publisher_name
                books1['author_name'] = author.author_name
                books1['year'] = book.year_published
                books1['isbn'] = book.isbn
                books1['types'] = book.types
                output.append(books1)
    else:
        output = []
        for book_item in resp['items']:
            books = {}
            if ((('publisher' in book_item['volumeInfo']) and ('industryIdentifiers' in book_item['volumeInfo']))
                and (('imageLinks' in book_item['volumeInfo']) and ('authors' in book_item['volumeInfo']))) \
                    and ('description' in book_item['volumeInfo'] and 'publishedDate' in book_item[
                        'volumeInfo']):  # usahay mag ka kulang mga result gikan sa google,
                # way publisher, isbn or picture and etc.
                # so if kulang kay iskip siya, mao pulos sa 'continue'
                books['title'] = book_item['volumeInfo']['title']
                books['publishers'] = book_item['volumeInfo']['publisher']
                books['isbn'] = book_item['volumeInfo']['industryIdentifiers'][0]['identifier']
                books['book_cover'] = book_item['volumeInfo']['imageLinks']['thumbnail']
                books['author_name'] = book_item['volumeInfo']['authors'][0]
                books['description'] = book_item['volumeInfo']['description']
                books['year'] = book_item['volumeInfo']['publishedDate']
                output.append(books)
            else:
                continue

        if author is not None:
            written = WrittenByAssociation.query.filter_by(
                author_id=author.author_id).all()
            for writtenbook in written:  # mga libro sa author gikan sa db
                book = Books.query.filter_by(
                    book_id=writtenbook.book_id).first()
                books1 = {}
                books1['title'] = book.title
                books1['book_id'] = int(book.book_id)
                books1['book_cover'] = book.book_cover
                books1['description'] = book.description
                book_author = WrittenByAssociation.query.filter_by(
                    book_id=book.book_id).first()
                author = Author.query.filter_by(
                    author_id=book_author.author_id).first()
                publisher = Publisher.query.filter_by(
                    publisher_id=book.publisher_id).first()
                books1['publishers'] = publisher.publisher_name
                books1['author_name'] = author.author_name
                books1['year'] = book.year_published
                books1['isbn'] = book.isbn
                books1['types'] = book.types
                output.append(books1)

        return jsonify({'book': output})


#ISBN_CHECK - Search ang database if ang libro na ing.ana na ISBN kay ga exist ba sa db
#INPUT: JSON: {isbn}
#       headers: {x-access-token}
#OUTPUT:
#if wala: 'Book not found'
#ireturn niya detail para pang addbook
@app.route('/book/isbn', methods=['POST'])
@token_required
def isbn_check(self):
    data = request.get_json()
    book = Books.query.filter_by(isbn=data['isbn']).first()
    if book is None:
        return make_response('Book not found')
    else:
        output = []
        user_data = {}
        user_data['title'] = book.title
        user_data['book_id'] = book.book_id
        user_data['book_cover'] = book.book_cover
        user_data['description'] = book.description
        book_author = WrittenByAssociation.query.filter_by(book_id=book.book_id).first()
        author = Author.query.filter_by(author_id=book_author.author_id).first()
        publisher = Publisher.query.filter_by(publisher_id=book.publisher_id).first()
        user_data['publishers'] = publisher.publisher_name
        user_data['author_name'] = author.author_name
        user_data['year'] = book.year_published
        user_data['isbn'] = book.isbn
        user_data['types'] = book.types
        output.append(user_data)
        return jsonify({'book': output})


#Author Check - Search ang database if ang mga libro ana nga Author kay ga exist ba sa db
#INPUT: JSON: {author_name}
#       headers: {x-access-token}
#OUTPUT:
#if wala: 'Book not found'
#else ireturn niya ang mga libro nakit-an sa db
#(sa backend sa web kay mapakita ang libro gikan sa db og mga libro makit-an sa API sa google og OPENLib
@app.route('/book/author', methods=['POST'])
@token_required
def author_check(self):
    data = request.get_json()
    author = Author.query.filter_by(author_name=data['author_name']).first()
    if author is None:
        return make_response('Author not found!')
    else:
        written = WrittenByAssociation.query.filter_by(author_id=author.author_id).all()
        output = []
        for writtenbook in written:
            book = Books.query.filter_by(book_id=writtenbook.book_id).first()
            user_data = {}
            user_data['title'] = book.title
            user_data['book_id'] = int(book.book_id)
            user_data['book_cover'] = book.book_cover
            user_data['description'] = book.description
            book_author = WrittenByAssociation.query.filter_by(book_id=book.book_id).first()
            author = Author.query.filter_by(author_id=book_author.author_id).first()
            publisher = Publisher.query.filter_by(publisher_id=book.publisher_id).first()
            user_data['publishers'] = publisher.publisher_name
            user_data['author_name'] = author.author_name
            user_data['year'] = book.year_published
            user_data['isbn'] = book.isbn
            user_data['types'] = book.types
            output.append(user_data)

        return jsonify({'books': output})


#TITLE SEARCH
#INPUT: JSON: {title}
#       headers: {x-access-token}
#OUTPUT:
#if wala: 'Book not found'
#else ireturn niya ang mga libro nakit-an sa db
#(sa backend sa web kay mapakita ang libro gikan sa db og mga libro makit-an sa API sa google og OPENLib
# pwede ra sad ilisdan para sa mobile
@app.route('/book/title', methods=['POST'])
@token_required
def title_check(self):
    data = request.get_json()
    books = Books.query.filter(Books.title.like(data['title'])).all()
    print(books)
    if not books:
        return make_response('Book not found')
    else:
        output = []
        for book in books:
            user_data = {}
            user_data['title'] = book.title
            user_data['book_id'] = book.book_id
            user_data['book_cover'] = book.book_cover
            user_data['description'] = book.description
            book_author = WrittenByAssociation.query.filter_by(book_id=book.book_id).first()
            author = Author.query.filter_by(author_id=book_author.author_id).first()
            publisher = Publisher.query.filter_by(publisher_id=book.publisher_id).first()
            user_data['publishers'] = publisher.publisher_name
            user_data['author_name'] = author.author_name
            user_data['year'] = book.year_published
            user_data['isbn'] = book.isbn
            user_data['types'] = book.types
            output.append(user_data)

        return jsonify({'books': output})

# {"title": "new book","edition": "20", "year": "2018", "isbn": "SEVENTEEN", "types": "HARD" , "publisher_name":"DK", "author_fname": "SEANNE", "author_lname": "CANOY"}


@app.route('/user/bookshelf/availability', methods=['GET', 'POST'])
@token_required
def viewbooks(self):
    data = request.get_json()
    books = ContainsAssociation.query.join(Bookshelf).filter_by(bookshef_owner=data['current_user']).all()

    if books == []:
        return jsonify({'message': 'No book found!'})

    else:

        output = []
        for book in books:
            user_data = {}
            user_data['shelf_id'] = book.shelf_id
            user_data['book_id'] = book.book_id
            user_data['quantity'] = book.quantity
            user_data['availability'] = book.availability
            output.append(user_data)

        return jsonify({'book': output})

@app.route('/category/<string:category>/', methods=['GET'])
@token_required
def category(category):

    books = Books.query.join(Category).filter(Category.categories == category).filter(Books.book_id == Category.book_id).all()
    # filter_by(firstname.like(search_var1),lastname.like(search_var2))
    #
    # q = (db.session.query(Category, Books)
    #      .join(Books)
    #      .join(Category)
    #      .filter(Category.categories == category)
    #      .filter(Books.book_id == Category.book_id)
    #      .all())

    output = []

    for book in books:
        user_data = {}
        user_data['title'] = book.title
        user_data['description'] = book.description
        user_data['edition'] = book.edition
        user_data['year'] = book.year_published
        user_data['isbn'] = book.isbn
        user_data['types'] = book.types
        user_data['publisher_id'] = book.publisher_id
        output.append(user_data)


    return jsonify({'book': output})

#Associate Genre to User(Genre Interests)
#INPUT: JSON:{current_user}
#       Sa url: {genre_name} Ex. http://localhost:5050/interests/view/Adventure'
#       headers: {x-access-token}
#OUTPUT:
# if genre doesnt exist in db: add genre to db
# {'message': "added successful'}
@app.route('/interests/<genre_name>', methods=['POST'])
@token_required
def add_interest(genre_name):
    data = request.get_json()
    user = User.query.filter_by(username=data['current_user']).first()

    genre = Genre.query.filter_by(genre_name=genre_name).first()
    if genre is None:
        genre = Genre(genre_name=genre_name)
        db.session.add(genre)
        db.session.commit()

    genre = Genre.query.filter_by(genre_name=genre_name).first()
    interests = InterestAssociation(user_Id=user.id, genreId=genre.id_genre)
    db.session.add(interests)
    db.session.commit()
    return jsonify({'message': "added successful"})

#Display books associated to the genre
#INPUT:
#       Sa url: {genre_name} Ex. http://localhost:5050/interests/view/Adventure'
#       headers: {x-access-token}
#OUTPUT:
# if genre doesnt exist in db: add genre to db
# if no books: 'No book found!'
# details sa mga libro
@app.route('/interests/view/<genre_name>', methods=['GET'])
@token_required
def view_genre(self, genre_name):
    data = request.get_json()
    genre = Genre.query.filter_by(genre_name=genre_name).first()
    if genre is None:
        genre = Genre(genre_name=genre_name)
        db.session.add(genre)
        db.session.commit()
        return jsonify({'message': 'No book found!'})

    genre = Genre.query.filter_by(genre_name=genre_name).first()
    countbooks = Books.query.join(HasGenreAssociation).filter(HasGenreAssociation.genreId == genre.id_genre).filter(
        Books.book_id == HasGenreAssociation.bookId).order_by(Books.year_published.desc()).count()
    freezebook = Books.query.join(HasGenreAssociation).filter(HasGenreAssociation.genreId == genre.id_genre).filter(
        Books.book_id == HasGenreAssociation.bookId).order_by(Books.year_published.desc()).paginate(per_page=39, page=int(data['page_num']), error_out=True).iter_pages(left_edge=1,
                                                                                                         right_edge=1,
                                                                                                         left_current=2,
                                                                                                         right_current=2)
    output2 = []
    user_data = {}
    user_data['totalBooks'] = countbooks
    frozen = jsonpickle.encode(freezebook)
    user_data['paginate'] = frozen
    output2.append(user_data)
    books = Books.query.join(HasGenreAssociation).filter(HasGenreAssociation.genreId == genre.id_genre).filter(
        Books.book_id == HasGenreAssociation.bookId).order_by(Books.year_published.desc()).paginate(per_page=39, page=int(data['page_num']), error_out=True).items
    if books is None:
        return jsonify({'message': 'No book found!'})
    output = []

    for book in books:
        print(book)
        book_ = Books.query.filter_by(book_id=book.book_id).first()
        owner_contains = ContainsAssociation.query.filter_by(book_id=book_.book_id).first()
        if owner_contains is None:
            continue
        else:
            owner_bookshelf = Bookshelf.query.filter_by(bookshelf_id=owner_contains.shelf_id).first()
            user_data = {}
            user_data['genre'] = genre_name
            user_data['title'] = book_.title
            bookrate = BookRateTotal.query.filter_by(bookRated=owner_contains.contains_id).first()
            if bookrate is not None:
                user_data['totalRate'] = ((bookrate.totalRate/bookrate.numofRates))
            else:
                user_data['totalRate'] = 0.0
            user_data['book_id'] = book_.book_id
            book_author = WrittenByAssociation.query.filter_by(book_id=book_.book_id).first()
            author = Author.query.filter_by(author_id=book_author.author_id).first()
            user_data['author_name'] = author.author_name
            owner = User.query.filter_by(username=owner_bookshelf.bookshef_owner).first()
            user_data['book_cover'] = book.book_cover
            user_data['owner_fname'] = owner.first_name
            user_data['owner_lname'] = owner.last_name
            user_data['owner_username'] = owner.username
            output.append(user_data)

    return jsonify({'book': output, 'totalBooks': output2})

#Display books associated to the category
#INPUT:
#       Sa url: {genre_name} Ex. http://localhost:5050/category/view/Fiction'
#       headers: {x-access-token}
#OUTPUT:
# if category doesnt exist in db: add category to db
# if no books: 'No book found!'
# details sa mga libro
@app.route('/category/view/<category_name>', methods=['GET'])
@token_required
def view_category(self, category_name):

    category = Category.query.filter_by(category_name=category_name).first()
    if category is None:
        category = Category(category_name=category_name)
        db.session.add(category)
        db.session.commit()
        return jsonify({'message': 'No book found!'})

    category = Category.query.filter_by(category_name=category_name).first()

    books = Books.query.join(CategoryAssociation).filter(CategoryAssociation.book_id == Books.book_id).filter(
        category.category_id == CategoryAssociation.category_id).order_by(Books.year_published.desc()).limit(12).all()
    if books is None:
        return jsonify({'message': 'No book found!'})
    output = []

    for book in books:
        print(book)
        book_ = Books.query.filter_by(book_id=book.book_id).first()
        owner_contains = ContainsAssociation.query.filter_by(book_id=book_.book_id).first()
        if owner_contains is None:
            continue
        else:
            owner_bookshelf = Bookshelf.query.filter_by(bookshelf_id=owner_contains.shelf_id).first()
            bookrate = BookRateTotal.query.filter_by(bookRated=owner_contains.contains_id).first()
            user_data = {}
            if bookrate is not None:
                user_data['totalRate'] = ((bookrate.totalRate/bookrate.numofRates))
            else:
                user_data['totalRate'] = 0.0
            genre = HasGenreAssociation.query.filter_by(bookId=book.book_id).first()
            get_genre = Genre.query.filter_by(id_genre=genre.genreId).first()
            user_data['genre'] = get_genre.genre_name
            user_data['title'] = book_.title
            user_data['book_id'] = book_.book_id
            book_author = WrittenByAssociation.query.filter_by(book_id=book_.book_id).first()
            author = Author.query.filter_by(author_id=book_author.author_id).first()
            user_data['author_name'] = author.author_name
            owner = User.query.filter_by(username=owner_bookshelf.bookshef_owner).first()
            user_data['book_cover'] = book.book_cover
            user_data['owner_fname'] = owner.first_name
            user_data['owner_lname'] = owner.last_name
            user_data['owner_username'] = owner.username
            output.append(user_data)

    return jsonify({'book': output})

#Parehas ra sa Display Genre pero gi limit og 12 kay para display sa dashboard
#INPUT:
#       Sa url: {genre_name} Ex. http://localhost:5050/interests/view2/Adventure'
#       headers: {x-access-token}
@app.route('/interests/view2/<genre_name>', methods=['GET'])
@token_required
def view_genre2(self, genre_name):

    genre = Genre.query.filter_by(genre_name=genre_name).first()
    if genre is None:
        genre = Genre(genre_name=genre_name)
        db.session.add(genre)
        db.session.commit()
        return jsonify({'message': 'No book found!'})

    genre = Genre.query.filter_by(genre_name=genre_name).first()

    books = Books.query.join(HasGenreAssociation).filter(HasGenreAssociation.genreId == genre.id_genre).filter(
        Books.book_id == HasGenreAssociation.bookId).order_by(Books.year_published.desc()).limit(12).all()
    if books is None:
        return jsonify({'message': 'No book found!'})
    output = []

    for book in books:
        print(book)
        book_ = Books.query.filter_by(book_id=book.book_id).first()
        owner_contains = ContainsAssociation.query.filter_by(book_id=book_.book_id).first()
        if owner_contains is None:
            continue
        else:
            owner_bookshelf = Bookshelf.query.filter_by(bookshelf_id=owner_contains.shelf_id).first()
            user_data = {}
            user_data['genre'] = genre_name
            user_data['title'] = book_.title
            user_data['book_id'] = book_.book_id
            bookrate = BookRateTotal.query.filter_by(bookRated=owner_contains.contains_id).first()
            if bookrate is not None:
                user_data['totalRate'] = ((bookrate.totalRate/bookrate.numofRates))
            else:
                user_data['totalRate'] = 0.0
            book_author = WrittenByAssociation.query.filter_by(book_id=book_.book_id).first()
            author = Author.query.filter_by(author_id=book_author.author_id).first()
            user_data['author_name'] = author.author_name
            owner = User.query.filter_by(username=owner_bookshelf.bookshef_owner).first()
            user_data['book_cover'] = book.book_cover
            user_data['owner_fname'] = owner.first_name
            user_data['owner_lname'] = owner.last_name
            user_data['owner_username'] = owner.username
            output.append(user_data)

    return jsonify({'book': output})


@app.route('/mobile/interests/view2/<genre_name>', methods=['GET'])
@token_required
def view_genre2mobile(self, genre_name):

    genre = Genre.query.filter_by(genre_name=genre_name).first()
    if genre is None:
        genre = Genre(genre_name=genre_name)
        db.session.add(genre)
        db.session.commit()
        return jsonify({'message': 'No book found!'})

    genre = Genre.query.filter_by(genre_name=genre_name).first()

    books = Books.query.join(HasGenreAssociation).filter(HasGenreAssociation.genreId == genre.id_genre).filter(
        Books.book_id == HasGenreAssociation.bookId).order_by(Books.year_published.desc()).all()
    if books is None:
        return jsonify({'message': 'No book found!'})
    output = []

    for book in books:
        print(book)
        book_ = Books.query.filter_by(book_id=book.book_id).first()
        owner_contains = ContainsAssociation.query.filter_by(
            book_id=book_.book_id).first()
        if owner_contains is None:
            continue
        else:
            owner_bookshelf = Bookshelf.query.filter_by(
                bookshelf_id=owner_contains.shelf_id).first()
            user_data = {}
            user_data['genre'] = genre_name
            user_data['title'] = book_.title
            user_data['book_id'] = book_.book_id
            bookrate = BookRateTotal.query.filter_by(
                bookRated=owner_contains.contains_id).first()
            if bookrate is not None:
                user_data['totalRate'] = (
                    (bookrate.totalRate/bookrate.numofRates))
            else:
                user_data['totalRate'] = 0.0
            book_author = WrittenByAssociation.query.filter_by(
                book_id=book_.book_id).first()
            author = Author.query.filter_by(
                author_id=book_author.author_id).first()
            user_data['author_name'] = author.author_name
            owner = User.query.filter_by(
                username=owner_bookshelf.bookshef_owner).first()
            user_data['book_cover'] = book.book_cover
            user_data['owner_fname'] = owner.first_name
            user_data['owner_lname'] = owner.last_name
            user_data['owner_username'] = owner.username
            output.append(user_data)

    return jsonify({'book': output})

#Display all books (sa web kay sa shop ni, dili dashboard)
#INPUT:
@app.route('/bookshelf/books', methods=['GET', 'POST'])
@token_required
def get_all_book(self):
    output = []
    data = request.get_json()
    countbooks = Books.query.count()
    freezebook = Books.query.paginate(per_page=24, page=int(data['pagenum']), error_out=True).iter_pages(left_edge=1, right_edge=1, left_current=2, right_current=2)
    output2 = []
    user_data = {}
    user_data['totalBooks'] = countbooks
    frozen = jsonpickle.encode(freezebook)
    user_data['paginate'] = frozen
    output2.append(user_data)
    books = Books.query.paginate(per_page=24, page=int(data['pagenum']), error_out=True).items
    for book in books:
        print(book)
        owner_contains = ContainsAssociation.query.filter_by(book_id=book.book_id).all()
        for owner_contain in owner_contains:
            user_data = {}
            owner_bookshelf = Bookshelf.query.filter_by(bookshelf_id=owner_contain.shelf_id).first()
            owner = User.query.filter_by(username=owner_bookshelf.bookshef_owner).first()
            bookrate = BookRateTotal.query.filter_by(bookRated=owner_contain.contains_id).first()
            if bookrate is not None:
                user_data['totalRate'] = ((bookrate.totalRate/bookrate.numofRates))
            else:
                user_data['totalRate'] = '0.0'
            user_data['owner_fname'] = owner.first_name
            user_data['owner_lname'] = owner.last_name
            user_data['owner_username'] = owner.username
            user_data['owner_bookshelfid'] = owner_bookshelf.bookshelf_id
            user_data['title'] = book.title
            user_data['book_id'] = book.book_id
            user_data['book_cover'] = book.book_cover
            genre = HasGenreAssociation.query.filter_by(bookId=book.book_id).first()
            genre_final = Genre.query.filter_by(id_genre=genre.genreId).first()
            user_data['genre'] = genre_final.genre_name
            book_author = WrittenByAssociation.query.filter_by(book_id=book.book_id).first()
            author = Author.query.filter_by(author_id=book_author.author_id).first()
            user_data['author_name'] = author.author_name
            output.append(user_data)


    return jsonify({'book': output, 'totalBooks': output2})

@app.route('/mobile/bookshelf/books', methods=['GET', 'POST'])
@token_required
def mobile_get_all_book(self):
    output = []
    books = Books.query.all()
    for book in books:
        # print(book)
        owner_contains = ContainsAssociation.query.filter_by(book_id=book.book_id).all()
        for owner_contain in owner_contains:
            user_data = {}
            owner_bookshelf = Bookshelf.query.filter_by(bookshelf_id=owner_contain.shelf_id).first()
            owner = User.query.filter_by(username=owner_bookshelf.bookshef_owner).first()
            bookrate = BookRateTotal.query.filter_by(bookRated=owner_contain.contains_id).first()
            if bookrate is not None:
                user_data['totalRate'] = ((bookrate.totalRate/bookrate.numofRates))
            else:
                user_data['totalRate'] = '0.0'
            user_data['owner_fname'] = owner.first_name
            user_data['owner_lname'] = owner.last_name
            user_data['owner_username'] = owner.username
            user_data['owner_bookshelfid'] = owner_bookshelf.bookshelf_id
            user_data['title'] = book.title
            user_data['book_id'] = book.book_id
            user_data['book_cover'] = book.book_cover
            genre = HasGenreAssociation.query.filter_by(bookId=book.book_id).first()
            genre_final = Genre.query.filter_by(id_genre=genre.genreId).first()
            user_data['genre'] = genre_final.genre_name
            book_author = WrittenByAssociation.query.filter_by(book_id=book.book_id).first()
            author = Author.query.filter_by(author_id=book_author.author_id).first()
            user_data['author_name'] = author.author_name
            output.append(user_data)


    return jsonify({'book': output})


# get all books for mobile
@app.route('/mobile/bookshelf/books', methods=['GET', 'POST'])
@token_required
def get_all_bookmobile(self):
    output = []
    data = request.get_json()
    owner_contains = ContainsAssociation.query.filter_by(book_id=data['book_id']).all()
    book = Books.query.filter_by(book_id=data['book_id']).first()
    for owner_contain in owner_contains:
        user_data = {}
        owner_bookshelf = Bookshelf.query.filter_by(bookshelf_id=owner_contain.shelf_id).first()
        owner = User.query.filter_by(username=owner_bookshelf.bookshef_owner).first()
        bookrate = BookRateTotal.query.filter_by(bookRated=owner_contain.contains_id).first()
        if bookrate is not None:
            user_data['totalRate'] = ((bookrate.totalRate/bookrate.numofRates))
        else:
            user_data['totalRate'] = '0.0'
        
        user_data['owner_fname'] = owner.first_name
        user_data['owner_lname'] = owner.last_name
        user_data['owner_username'] = owner.username
        user_data['owners'] = owner.first_name +' '+owner.last_name 
        user_data['owner_bookshelfid'] = owner_bookshelf.bookshelf_id
        user_data['title'] = book.title
        user_data['book_id'] = book.book_id
        user_data['book_cover'] = book.book_cover
        genre = HasGenreAssociation.query.filter_by(bookId=book.book_id).first()
        genre_final = Genre.query.filter_by(id_genre=genre.genreId).first()
        user_data['genre'] = genre_final.genre_name
        book_author = WrittenByAssociation.query.filter_by(book_id=book.book_id).first()
        author = Author.query.filter_by(author_id=book_author.author_id).first()
        user_data['author_name'] = author.author_name
        output.append(user_data)


    return jsonify({'book': output})


#INPUT:
#       headers: {x-access-token}
@app.route('/bookshelf/books/latest', methods=['GET'])
@token_required
#       headers: {x-access-token}
def get_latest_books(self):
    request.headers.get('x-access-token')
    output = []
    books = Books.query.order_by(Books.year_published.desc()).limit(12).all()
    for book in books:
        owner_contains = ContainsAssociation.query.filter_by(book_id=book.book_id).all()
        for owner_contain in owner_contains:
            user_data = {}
            user_data['title'] = book.title
            user_data['book_id'] = book.book_id
            bookrate = BookRateTotal.query.filter_by(bookRated=owner_contain.contains_id).first()
            if bookrate is not None:
                user_data['totalRate'] = ((bookrate.totalRate/bookrate.numofRates))
            else:
                user_data['totalRate'] = 0.0
            genre = HasGenreAssociation.query.filter_by(bookId=book.book_id).first()
            genre_final = Genre.query.filter_by(id_genre=genre.genreId).first()
            user_data['genre'] = genre_final.genre_name
            book_author = WrittenByAssociation.query.filter_by(book_id=book.book_id).first()
            author = Author.query.filter_by(author_id=book_author.author_id).first()
            user_data['author_name'] = author.author_name
            user_data['book_cover'] = book.book_cover
            owner_bookshelf = Bookshelf.query.filter_by(bookshelf_id=owner_contain.shelf_id).first()
            owner = User.query.filter_by(username=owner_bookshelf.bookshef_owner).first()
            user_data['owner_fname'] = owner.first_name
            user_data['owner_lname'] = owner.last_name
            user_data['owner_username'] = owner.username
            user_data['owner_bookshelfid'] = owner_bookshelf.bookshelf_id
            output.append(user_data)

    return jsonify({'book': output})

# Show all books sorted by year publication
@app.route('/bookshelf/books/alllatest', methods=['GET'])
@token_required
#       headers: {x-access-token}
def get_alllatest_books(self):
    request.headers.get('x-access-token')
    output = []
    books = Books.query.order_by(Books.year_published.desc()).all()
    for book in books:
        owner_contains = ContainsAssociation.query.filter_by(book_id=book.book_id).all()
        for owner_contain in owner_contains:
            user_data = {}
            user_data['title'] = book.title
            user_data['book_id'] = book.book_id
            bookrate = BookRateTotal.query.filter_by(bookRated=owner_contain.contains_id).first()
            if bookrate is not None:
                user_data['totalRate'] = ((bookrate.totalRate/bookrate.numofRates))
            else:
                user_data['totalRate'] = 0.0
            genre = HasGenreAssociation.query.filter_by(bookId=book.book_id).first()
            genre_final = Genre.query.filter_by(id_genre=genre.genreId).first()
            user_data['genre'] = genre_final.genre_name
            book_author = WrittenByAssociation.query.filter_by(book_id=book.book_id).first()
            author = Author.query.filter_by(author_id=book_author.author_id).first()
            user_data['author_name'] = author.author_name
            user_data['book_cover'] = book.book_cover
            owner_bookshelf = Bookshelf.query.filter_by(bookshelf_id=owner_contain.shelf_id).first()
            owner = User.query.filter_by(username=owner_bookshelf.bookshef_owner).first()
            user_data['owner_fname'] = owner.first_name
            user_data['owner_lname'] = owner.last_name
            user_data['owner_username'] = owner.username
            user_data['owner_bookshelfid'] = owner_bookshelf.bookshelf_id
            output.append(user_data)

    return jsonify({'book': output})


#INPUT:
#       headers: {x-access-token}
@app.route('/bookshelf/books/toprated', methods=['GET'])
@token_required
def get_toprated_books(self):
    output = []
    ratedbooks = BookRateTotal.query.order_by(BookRateTotal.totalRate.asc()).limit(12).all()
    if ratedbooks is None:
        return jsonify({'book': [{}]})
    for ratedbook in ratedbooks:
        owner_contains = ContainsAssociation.query.filter_by(book_id=ratedbook.bookRated).first()
        if owner_contains is not None:
            book = Books.query.filter_by(book_id=owner_contains.book_id).first()
            user_data = {}
            user_data['title'] = book.title
            user_data['book_id'] = book.book_id
            user_data['totalRate'] = ((ratedbook.totalRate/ratedbook.numofRates))
            genre = HasGenreAssociation.query.filter_by(bookId=book.book_id).first()
            genre_final = Genre.query.filter_by(id_genre=genre.genreId).first()
            user_data['genre'] = genre_final.genre_name
            book_author = WrittenByAssociation.query.filter_by(book_id=book.book_id).first()
            author = Author.query.filter_by(author_id=book_author.author_id).first()
            user_data['author_name'] = author.author_name
            user_data['book_cover'] = book.book_cover
            owner_bookshelf = Bookshelf.query.filter_by(bookshelf_id=owner_contains.shelf_id).first()
            owner = User.query.filter_by(username=owner_bookshelf.bookshef_owner).first()
            user_data['owner_fname'] = owner.first_name
            user_data['owner_lname'] = owner.last_name
            user_data['owner_username'] = owner.username
            user_data['owner_bookshelfid'] = owner_bookshelf.bookshelf_id
        else:
            continue
        output.append(user_data)

    return jsonify({'book': output})

# view all books sorted by Total rate of the book
@app.route('/bookshelf/books/alltoprated', methods=['GET'])
@token_required
def get_alltoprated_books(self):
    output = []
    ratedbooks = BookRateTotal.query.order_by(BookRateTotal.totalRate.asc()).all()
    if ratedbooks is None:
        return jsonify({'book': [{}]})
    for ratedbook in ratedbooks:
        owner_contains = ContainsAssociation.query.filter_by(book_id=ratedbook.bookRated).first()
        if owner_contains is not None:
            book = Books.query.filter_by(book_id=owner_contains.book_id).first()
            user_data = {}
            user_data['title'] = book.title
            user_data['book_id'] = book.book_id
            user_data['totalRate'] = ((ratedbook.totalRate/ratedbook.numofRates))
            genre = HasGenreAssociation.query.filter_by(bookId=book.book_id).first()
            genre_final = Genre.query.filter_by(id_genre=genre.genreId).first()
            user_data['genre'] = genre_final.genre_name
            book_author = WrittenByAssociation.query.filter_by(book_id=book.book_id).first()
            author = Author.query.filter_by(author_id=book_author.author_id).first()
            user_data['author_name'] = author.author_name
            user_data['book_cover'] = book.book_cover
            owner_bookshelf = Bookshelf.query.filter_by(bookshelf_id=owner_contains.shelf_id).first()
            owner = User.query.filter_by(username=owner_bookshelf.bookshef_owner).first()
            user_data['owner_fname'] = owner.first_name
            user_data['owner_lname'] = owner.last_name
            user_data['owner_username'] = owner.username
            user_data['owner_bookshelfid'] = owner_bookshelf.bookshelf_id
        else:
            continue
        output.append(user_data)

    return jsonify({'book': output})

#INPUT:
#       headers: {x-access-token}
@app.route('/bookshelf/books/recent', methods=['GET'])
@token_required
def get_recent_books(self):
    output = []
    contains = ContainsAssociation.query.order_by(ContainsAssociation.date.desc()).limit(20).all()
    for contain in contains:
        book = Books.query.filter_by(book_id=contain.book_id).first()
        user_data = {}
        user_data['title'] = book.title
        user_data['book_id'] = book.book_id
        bookrate = BookRateTotal.query.filter_by(bookRated=contain.contains_id).first()
        if bookrate is not None:
            user_data['totalRate'] = ((bookrate.totalRate/bookrate.numofRates))
        else:
            user_data['totalRate'] = 0.0
        genre = HasGenreAssociation.query.filter_by(bookId=book.book_id).first()
        genre_final = Genre.query.filter_by(id_genre=genre.genreId).first()
        user_data['genre'] = genre_final.genre_name
        book_author = WrittenByAssociation.query.filter_by(book_id=book.book_id).first()
        author = Author.query.filter_by(author_id=book_author.author_id).first()
        user_data['author_name'] = author.author_name
        user_data['book_cover'] = book.book_cover
        owner_bookshelf = Bookshelf.query.filter_by(bookshelf_id=contain.shelf_id).first()
        owner = User.query.filter_by(username=owner_bookshelf.bookshef_owner).first()
        user_data['owner_fname'] = owner.first_name
        user_data['owner_lname'] = owner.last_name
        user_data['owner_username'] = owner.username
        user_data['owner_bookshelfid'] = owner_bookshelf.bookshelf_id
        output.append(user_data)

    return jsonify({'book': output})

# all books sorted by date it was uploaded
@app.route('/bookshelf/books/allrecent', methods=['GET'])
@token_required
def get_allrecent_books(self):
    output = []
    contains = ContainsAssociation.query.order_by(ContainsAssociation.date.desc()).all()
    for contain in contains:
        book = Books.query.filter_by(book_id=contain.book_id).first()
        user_data = {}
        user_data['title'] = book.title
        user_data['book_id'] = book.book_id
        bookrate = BookRateTotal.query.filter_by(bookRated=contain.contains_id).first()
        if bookrate is not None:
            user_data['totalRate'] = ((bookrate.totalRate/bookrate.numofRates))
        else:
            user_data['totalRate'] = 0.0
        genre = HasGenreAssociation.query.filter_by(bookId=book.book_id).first()
        genre_final = Genre.query.filter_by(id_genre=genre.genreId).first()
        user_data['genre'] = genre_final.genre_name
        book_author = WrittenByAssociation.query.filter_by(book_id=book.book_id).first()
        author = Author.query.filter_by(author_id=book_author.author_id).first()
        user_data['author_name'] = author.author_name
        user_data['book_cover'] = book.book_cover
        owner_bookshelf = Bookshelf.query.filter_by(bookshelf_id=contain.shelf_id).first()
        owner = User.query.filter_by(username=owner_bookshelf.bookshef_owner).first()
        user_data['owner_fname'] = owner.first_name
        user_data['owner_lname'] = owner.last_name
        user_data['owner_username'] = owner.username
        user_data['owner_bookshelfid'] = owner_bookshelf.bookshelf_id
        output.append(user_data)

    return jsonify({'book': output})


#### WISHLIST ###
#INPUT: JSON: {username(user), bookshelf_id(bookshelf_id sa tag-iya sa libro), book_id}
#       headers: {x-access-token}
#OUTPUT:
#if ang user ni add to wishlist sa iyang libro: "You can't add..."
#if ang libro naa na sa iyang wishlist: "Book is already.."
#"Added successful"
@app.route('/bookshelf/wishlist', methods=['POST'])
@token_required
def add_wishlist(self):
    data = request.get_json()

    user = User.query.filter_by(username=data['username']).first()
    bookshelf = Bookshelf.query.filter_by(bookshef_owner=user.username).first()
    bookshelf_id = data['bookshelf_id']
    print(bookshelf.bookshelf_id)
    print(bookshelf_id)
    if int(bookshelf_id) == int(user.id):
        return jsonify({'message': "You can't add your own book to your wishlist"})
    else:
        wishlist = Wishlist.query.filter((Wishlist.user_id==user.id) & (Wishlist.shelf_id==data['bookshelf_id']) & (Wishlist.bookId==data['book_id'])).first()
        print(wishlist)
        if wishlist is not None:
            return jsonify({'message': "Book is already in wishlist"})

        wishlist1 = Wishlist(user_id=user.id, shelf_id=data['bookshelf_id'], bookId=data['book_id'])
        db.session.add(wishlist1)
        db.session.commit()
        return jsonify({'message': "Added successful"})

#INPUT JSON: {username(user na mo remove), bookshelf_owner(tag-iya sa libro), book_id}
#       headers: {x-access-token}
@app.route('/bookshelf/remove_wishlist', methods=['POST'])
@token_required
def remove_wishlist(self):
    data = request.get_json()

    user = User.query.filter_by(username=data['username']).first()
    bookshelf = Bookshelf.query.filter_by(bookshef_owner=data['bookshelf_owner']).first()
    book = Books.query.filter_by(book_id=data['book_id']).first()
    wishlist = Wishlist.query.filter((Wishlist.user_id == user.id) & (Wishlist.shelf_id == bookshelf.bookshelf_id) &
                                     (Wishlist.bookId == book.book_id)).first()
    db.session.delete(wishlist)
    db.session.commit()
    return jsonify({'message': "Removed successful"})

#INPUT JSON: {current_user}
#       headers: {x-access-token}
@app.route('/bookshelf/wishlist/user', methods=['GET', 'POST'])
@token_required
def show_wishlist(self):
    data = request.get_json()
    output = []
    user = User.query.filter_by(username=data['current_user']).first()
    wishlist_books = Wishlist.query.filter_by(user_id=user.id).all()
    for book in wishlist_books:
        user_data = {}
        get_book = Books.query.filter_by(book_id=book.bookId).first()
        owner_contains = ContainsAssociation.query.filter_by(book_id=get_book.book_id).first()
        if owner_contains is None:
            # if ang book kay di na associated sa isa ka user kay iskip
            continue
        else:
            owner_bookshelf = Bookshelf.query.filter_by(bookshelf_id=owner_contains.shelf_id).first()
            bookrate = BookRateTotal.query.filter_by(bookRated=owner_contains.contains_id).first()
            if bookrate is not None:
                user_data['totalRate'] = ((bookrate.totalRate/bookrate.numofRates))
            else:
                user_data['totalRate'] = 0.0
            user_data['title'] = get_book.title
            user_data['book_id'] = get_book.book_id
            genre = HasGenreAssociation.query.filter_by(bookId=get_book.book_id).first()
            genre_final = Genre.query.filter_by(id_genre=genre.genreId).first()
            user_data['genre'] = genre_final.genre_name
            book_author = WrittenByAssociation.query.filter_by(book_id=get_book.book_id).first()
            author = Author.query.filter_by(author_id=book_author.author_id).first()
            user_data['author_name'] = author.author_name
            owner = User.query.filter_by(username=owner_bookshelf.bookshef_owner).first()
            user_data['book_cover'] = get_book.book_cover
            user_data['owner_fname'] = owner.first_name
            user_data['owner_lname'] = owner.last_name
            user_data['owner_username'] = owner.username
            output.append(user_data)

    return jsonify({'book': output})
### END OF WISHLIST ###

# COMMENT (USER)
# @app.route('/profile/comment-user/', methods=['GET', 'POST'])
@app.route('/profile/comment-user/<int:user_id>', methods=['GET', 'POST'])
def comment(current_user, user_id):
    if user_id == current_user.id:
        comments = UserCommentAssociation.query.filter((UserCommentAssociation.user_idCommentee == current_user.id))
        x = []
        for c in comments:
            s = User.query.filter_by(id=c.user_idCommenter).first()
            x.append(s.first_name + ' ' + s.last_name)
        return jsonify({'message': 'ok', 'comments': comments, 'name': x, 'currrent_user': current_user})
    else:
        user = User.query.filter_by(id=user_id).first()
        otheruserId = user_id
        comments = UserCommentAssociation.query.filter((UserCommentAssociation.user_idCommentee == user_id))
        xs = []
        for c in comments:
            s = User.query.filter_by(id=c.user_idCommenter).first()
            xs.append(s.first_name + ' ' + s.last_name)
        if request.method == 'POST':
            comment = request.form['comment']
            commentOld = UserCommentAssociation.query.filter(
                (UserCommentAssociation.user_idCommentee == otheruserId) & (
                        UserCommentAssociation.user_idCommenterter == current_user.id)).first()

            if commentOld is not None:
                commentOld.comment = comment
                db.session.commit()

            else:
                newCommenter = UserCommentAssociation(current_user.id, otheruserId, comment)
                db.session.add(newCommenter)
                db.session.commit()
            return jsonify({'message': 'ok', 'user_id': user_id})
        return jsonify({'message': 'ok', 'user': user, 'comments': comments, 'name': xs, 'currrent_user': current_user})

#GET COORDINATES OF OTHER USER (PARA SA GOOGLE MAPS)(WEB)
#INPUT JSON: {current_user}
#       headers: {x-access-token}
@app.route('/users/coordinates', methods=['GET', 'POST'])
@token_required
def coordinates(self):
    data = request.get_json()
    user = User.query.filter_by(username=data['current_user']).first()
    users = User.query.filter(User.username != data['current_user']).filter(User.username != data['username']).all()
    output = []
    for user in users:
        user_data = {}
        user_data['other_username'] = user.username
        user_data['other_userfname'] = user.first_name
        user_data['other_userlname'] = user.last_name
        user_data['other_user_lat'] = user.latitude
        user_data['other_user_lng'] = user.longitude
        output.append(user_data)
    return jsonify({'users': output})

#GET COORDINATES OF CURRENT USER (PARA SA GOOGLE MAPS)(WEB)
#INPUT JSON: {current_user}
#       headers: {x-access-token}
@app.route('/user/coordinates', methods=['GET', 'POST'])
@token_required
def own_coordinates(self):
    data = request.get_json()
    user = User.query.filter_by(username=data['current_user']).first()
    output = []
    user_data = {}
    user_data['username'] = user.username
    user_data['firstname'] = user.first_name
    user_data['lastname'] = user.last_name
    user_data['latitude'] = user.latitude
    user_data['longitude'] = user.longitude
    output.append(user_data)
    return jsonify({'user': output})

@app.route('/search', methods=['GET', 'POST'])
@token_required
def search(self):

    data = request.get_json()
    item = '%' + data['item'] + '%'

    books = Books.query.filter(((Books.title.ilike(item)) | (Books.isbn.ilike(item)))).all()

    if books is None:
        return jsonify({'message': 'No book found!'})

    output = []

    for book in books:
        user_data = {}
        contains = ContainsAssociation.query.filter_by(book_id=book.book_id).first()
        owner = Bookshelf.query.filter_by(bookshelf_id=contains.shelf_id).first()
        user_owner = User.query.filter_by(username=owner.bookshef_owner).first()
        genre = HasGenreAssociation.query.filter_by(bookId=book.book_id).first()
        genre_final = Genre.query.filter_by(id_genre=genre.genreId).first()
        user_data['genre'] = genre_final.genre_name
        book_author = WrittenByAssociation.query.filter_by(book_id=book.book_id).first()
        author = Author.query.filter_by(author_id=book_author.author_id).first()
        user_data['author_name'] = author.author_name
        user_data['owner_username'] = user_owner.username
        user_data['owner_fname'] = user_owner.first_name
        user_data['owner_lname'] = user_owner.last_name
        user_data['book_id'] = book.book_id
        user_data['title'] = book.title
        user_data['description'] = book.description
        user_data['year_published'] = book.year_published
        user_data['isbn'] = book.isbn
        user_data['types'] = book.types
        user_data['publisher_id'] = book.publisher_id
        user_data['book_cover'] = book.book_cover
        output.append(user_data)
	print(output)
    return jsonify({'book': output})

@app.route('/search/user/books', methods=['GET', 'POST'])
@token_required
def search_in_profile(self):

    data = request.get_json()
    item = '%' + data['item'] + '%'
    print(data['username'])
    books = Bookshelf.query.filter_by(bookshef_owner=data['username']).first()
    shelf_id = books.bookshelf_id

    contains = ContainsAssociation.query.filter_by(shelf_id=shelf_id).first()
    if contains is None:
        return make_response('no books found')
    shelf_id = contains.shelf_id
    Book = Books.query.join(ContainsAssociation).filter_by(shelf_id=shelf_id).filter(((Books.title.like(item)) | (Books.year_published.like(item))  | (Books.isbn.like(item)))).all()

    # q = (db.session.query(Books, Bookshelf, ContainsAssociation, Author)
    #      .filter(Bookshelf.bookshef_owner == id)
    #      .filter(ContainsAssociation.shelf_id == Bookshelf.bookshelf_id)
    #      .filter(Books.book_id == ContainsAssociation.book_id)
    #      .filter(Author.author_id == Books.publisher_id)
    #      .all())

    output = []
    if (Book is None) or (contains is None) or (books is None):
        return make_response('no books found')

    for book in Book:
        user_data = {}
        user_data['title'] = book.title
        user_data['book_id'] = book.book_id
        genre = HasGenreAssociation.query.filter_by(bookId=book.book_id).first()
        genre_final = Genre.query.filter_by(id_genre=genre.genreId).first()
        user_data['genre'] = genre_final.genre_name
        user_data['book_cover'] = book.book_cover
        book_author = WrittenByAssociation.query.filter_by(book_id=book.book_id).first()
        author = Author.query.filter_by(author_id=book_author.author_id).first()
        user_data['owner_bookshelfid'] = books.bookshelf_id
        user_data['author_name'] = author.author_name
        user_data['description'] = book.description
        user_data['edition'] = book.edition
        user_data['year'] = book.year_published
        user_data['isbn'] = book.isbn
        user_data['types'] = book.types
        user_data['publisher_id'] = book.publisher_id
        output.append(user_data)

    return jsonify({'book': output})

@app.route('/store/search', methods=['GET', 'POST'])
@token_required
def store_search(self):
    data = request.get_json()
    print(data['search'])
    print(data['genre'])
    print(data['time'])
    today = datetime.datetime.today()
    genre = Genre.query.filter_by(genre_name=data['genre']).first()
    if not data['search'] and (genre is None and data['time'] is None):
        countbooks = Books.query.count()
        freezebook = Books.query.paginate(per_page=24, page=int(data['pagenum']),error_out=True).iter_pages(
            left_edge=1,
            right_edge=1,
            left_current=2,
            right_current=2)
        books = Books.query.paginate(per_page=24, page=int(data['pagenum']), error_out=True).items
    elif not data['search'] and genre is None:
        margin = datetime.timedelta(days=int(data['time']))
        countbooks = Books.query.join(ContainsAssociation).filter(ContainsAssociation.date.between(today-margin, today)).count()
        freezebook = Books.query.join(ContainsAssociation).filter(ContainsAssociation.date.between(today-margin, today)).paginate(per_page=24, page=int(data['pagenum']), error_out=True).iter_pages(
            left_edge=1,
            right_edge=1,
            left_current=2,
            right_current=2)
        books = Books.query.join(ContainsAssociation).filter(ContainsAssociation.date.between(today-margin, today))\
            .paginate(per_page=24, page=int(data['pagenum']), error_out=True).items
        print(today-margin)
        print(today)
        books2 = Books.query.join(ContainsAssociation).filter(ContainsAssociation.date.between(today - margin, today)).first()
        print(books2)
    elif not data['search']:
        countbooks = Books.query.join(HasGenreAssociation).filter(HasGenreAssociation.bookId == Books.book_id).filter(
        HasGenreAssociation.genreId == genre.id_genre).count()
        freezebook = Books.query.join(HasGenreAssociation).filter(HasGenreAssociation.bookId == Books.book_id).filter(
        HasGenreAssociation.genreId == genre.id_genre).paginate(per_page=24, page=int(data['pagenum']), error_out=True).iter_pages(
            left_edge=1,
            right_edge=1,
            left_current=2,
            right_current=2)
        books = Books.query.join(HasGenreAssociation).filter(HasGenreAssociation.bookId == Books.book_id).filter(
        HasGenreAssociation.genreId == genre.id_genre).paginate(per_page=24, page=int(data['pagenum']), error_out=True).items

    elif genre is None:
        item = '%' + data['search'] + '%'
        countbooks = Books.query.filter(Books.title.like(item)).count()
        freezebook = Books.query.filter(Books.title.like(item)).paginate(per_page=24, page=int(data['pagenum']), error_out=True).iter_pages(
            left_edge=1,
            right_edge=1,
            left_current=2,
            right_current=2)
        books = Books.query.filter(Books.title.like(item)).paginate(per_page=24, page=int(data['pagenum']), error_out=True).items
    else:
        item = '%' + data['search'] + '%'
        books = Books.query.join(HasGenreAssociation).filter(((Books.title.like(item)))).filter(HasGenreAssociation.bookId == Books.book_id).filter(
            HasGenreAssociation.genreId == genre.id_genre).paginate(per_page=24, page=int(data['pagenum']), error_out=True).items
        countbooks = Books.query.join(HasGenreAssociation).filter(((Books.title.like(item)))).filter(HasGenreAssociation.bookId == Books.book_id).filter(
            HasGenreAssociation.genreId == genre.id_genre).count()
        freezebook = Books.query.join(HasGenreAssociation).filter(((Books.title.like(item)))).filter(HasGenreAssociation.bookId == Books.book_id).filter(
            HasGenreAssociation.genreId == genre.id_genre).paginate(per_page=24, page=int(data['pagenum']), error_out=True).iter_pages(
            left_edge=1,
            right_edge=1,
            left_current=2,
            right_current=2)

    output2 = []
    user_data = {}
    user_data['totalBooks'] = countbooks
    frozen = jsonpickle.encode(freezebook)
    user_data['paginate'] = frozen
    output2.append(user_data)


    if countbooks == 0 or not books:
        return make_response("No book found!")

    output = []
    for book in books:
        user_data = {}
        contains = ContainsAssociation.query.filter_by(book_id=book.book_id).first()
        if contains is not None:
            owner = Bookshelf.query.filter_by(bookshelf_id=contains.shelf_id).first()
            user_owner = User.query.filter_by(username=owner.bookshef_owner).first()
            genre = HasGenreAssociation.query.filter_by(bookId=book.book_id).first()
            genre_final = Genre.query.filter_by(id_genre=genre.genreId).first()
            if data['time'] is None:
                user_data['genre'] = genre_final.genre_name
                book_author = WrittenByAssociation.query.filter_by(book_id=book.book_id).first()
                author = Author.query.filter_by(author_id=book_author.author_id).first()
                bookrate = BookRateTotal.query.filter_by(bookRated=contains.contains_id).first()
                if bookrate is not None:
                    user_data['totalRate'] = ((bookrate.totalRate/bookrate.numofRates))
                else:
                    user_data['totalRate'] = '0.0'
                user_data['author_name'] = author.author_name
                user_data['owner_username'] = user_owner.username
                user_data['owner_fname'] = user_owner.first_name
                user_data['owner_lname'] = user_owner.last_name
                user_data['book_id'] = book.book_id
                user_data['title'] = book.title
                user_data['description'] = book.description
                user_data['year_published'] = book.year_published
                user_data['isbn'] = book.isbn
                user_data['types'] = book.types
                user_data['publisher_id'] = book.publisher_id
                user_data['book_cover'] = book.book_cover
                output.append(user_data)
            else:
                margin = datetime.timedelta(days=int(data['time']))
                if (today - margin <= contains.date  <= today):
                    user_data['genre'] = genre_final.genre_name
                    book_author = WrittenByAssociation.query.filter_by(book_id=book.book_id).first()
                    author = Author.query.filter_by(author_id=book_author.author_id).first()
                    bookrate = BookRateTotal.query.filter_by(bookRated=contains.contains_id).first()
                    if bookrate is not None:
                        user_data['totalRate'] = ((bookrate.totalRate / bookrate.numofRates))
                    else:
                        user_data['totalRate'] = '0.0'
                    user_data['author_name'] = author.author_name
                    user_data['owner_username'] = user_owner.username
                    user_data['owner_fname'] = user_owner.first_name
                    user_data['owner_lname'] = user_owner.last_name
                    user_data['book_id'] = book.book_id
                    user_data['title'] = book.title
                    user_data['description'] = book.description
                    user_data['year_published'] = book.year_published
                    user_data['isbn'] = book.isbn
                    user_data['types'] = book.types
                    user_data['publisher_id'] = book.publisher_id
                    user_data['book_cover'] = book.book_cover
                    output.append(user_data)
                else:
                    continue
        else:
            continue

    print(output)
    return jsonify({'book': output, 'totalBooks': output2})
############################################################################################################################################################################################################
############################################################################################################################################################################################################
############################################################################################################################################################################################################
####################################################################### BORROW RENT AND PURCHASE ###########################################################################################################
############################################################################################################################################################################################################
############################################################################################################################################################################################################

#STEP 1
#User's View on The Owner's Book
#When the button(borrow, rent or purchase) is pressed the user requests to borrow, rent or purchase the book
#In Database: It creates a WaitingList Model containing the details of the book, return date and method.
#The book is still not considered borrowed, rent or purchased. It's a request to be approved.
@app.route('/bookshelf/borrow_book', methods=['POST'])
@token_required
def add_borrow(self):
    data = request.get_json()
    date_end = data['end']
    user = User.query.filter_by(username=data['book_owner']).first() #for owner id
    current_user = User.query.filter_by(username=data['book_borrower']).first() #for borrower id
    bookshelf = Bookshelf.query.filter_by(bookshef_owner=user.username).first()
    today = date.today()
    if date_end == 0:
        return jsonify({"message": "Date invalid!"})
    elif date_end == 1:
        return jsonify({"message": "Date invalid!"})
    print(bookshelf.bookshelf_id)
    print(user.id)
    borrow = WaitingList.query.filter((WaitingList.borrower==current_user.id) & (WaitingList.owner_shelf_id==data['bookshelf_id']) & (WaitingList.bookid==data['book_id'])).first()
    print(borrow)
    if borrow is not None:
        return jsonify({"message":"You've already requested for this book."})

    borrow1 = WaitingList(borrower=current_user.id, owner_shelf_id=data['bookshelf_id'], bookid=data['book_id'], request_Date=data['end'], approval=None, method='Borrow',
                          price_rate=None, price=None)
    db.session.add(borrow1)
    db.session.commit()
    actlogs = ActLogs(current_user_id=current_user.id, other_user_id=user.id,
                                  bookid=data['book_id'], status=0, type='request')
    notifications = Notifications(current_user=user.id, user_id=current_user.id, bookshelf_id=user.id,
                                  book_id=data['book_id'], last_open=None, type='borrow_request')
    db.session.add(notifications)
    db.session.add(actlogs)
    db.session.commit()
    return jsonify({"message":"Successful!"})


@app.route('/bookshelf/rent_book', methods=['POST'])
@token_required
def add_rent(self):
    data = request.get_json()
    date_end = data['end']
    if date_end == 0:
        return jsonify({"message": "Date invalid!"})
    elif date_end == 1:
        return jsonify({"message": "Date invalid!"})
    user = User.query.filter_by(username=data['book_owner']).first() #for owner id
    current_user = User.query.filter_by(username=data['book_borrower']).first()    #for borrower id
    bookshelf = Bookshelf.query.filter_by(bookshef_owner=user.username).first()
    print(bookshelf.bookshelf_id)
    print(user.id)
    borrow = WaitingList.query.filter((WaitingList.borrower==current_user.id) & (WaitingList.owner_shelf_id==data['bookshelf_id']) & (WaitingList.bookid==data['book_id'])).first()
    print(borrow)
    if borrow is not None:
        return jsonify({"message":"You've already requested for this book."})

    borrow1 = WaitingList(borrower=current_user.id, owner_shelf_id=data['bookshelf_id'], bookid=data['book_id'], request_Date=data['end'], approval=None, method='Rent', price=None, price_rate=data['price_rate'])
    db.session.add(borrow1)
    db.session.commit()
    notifications = Notifications(current_user=user.id, user_id=current_user.id, bookshelf_id=user.id,
                                  book_id=data['book_id'], last_open=None, type='rent_request')
    db.session.add(notifications)
    actlogs = ActLogs(current_user_id=current_user.id, other_user_id=user.id,
                      bookid=data['book_id'], status=0, type='request')
    db.session.add(actlogs)
    db.session.commit()
    return jsonify({"message":"Successful!"})

@app.route('/bookshelf/purchase_book', methods=['POST'])
@token_required
def add_purchase(self):
    data = request.get_json()

    user = User.query.filter_by(username=data['book_owner']).first() #for owner id
    current_user = User.query.filter_by(username=data['book_buyer']).first()    #for borrower id
    bookshelf = Bookshelf.query.filter_by(bookshef_owner=user.username).first()
    print(bookshelf.bookshelf_id)
    print(user.id)
    borrow = WaitingList.query.filter((WaitingList.borrower==current_user.id) & (WaitingList.owner_shelf_id==data['bookshelf_id']) & (WaitingList.bookid==data['book_id'])).first()
    print(borrow)
    if borrow is not None:
        return jsonify({"message":"You've already requested for this book."})

    borrow1 = WaitingList(borrower=current_user.id, owner_shelf_id=data['bookshelf_id'], bookid=data['book_id'], request_Date=None, approval=None, method='Purchase', price=data['price'], price_rate=None)
    db.session.add(borrow1)
    db.session.commit()
    notifications = Notifications(current_user=user.id, user_id=current_user.id, bookshelf_id=user.id,
                                   book_id=data['book_id'], last_open=None, type='purchase_request')
    db.session.add(notifications)
    actlogs = ActLogs(current_user_id=current_user.id, other_user_id=user.id,
                      bookid=data['book_id'], status=0, type='request')
    db.session.add(actlogs)
    db.session.commit()
    return jsonify({"message":"Successful!"})


#DISPLAYS THE BOOKS THAT THE USER HAS REQUESTED
@app.route('/bookshelf/borrow/user', methods=['GET', 'POST'])
@token_required
def show_borrow(self):
    data = request.get_json()
    user = User.query.filter_by(username=data['current_user']).first()
    output = []
    borrow_books = WaitingList.query.filter_by(borrower=user.id).all()
    if borrow_books is None:
        return make_response('No books found!')
    for book in borrow_books:
        user_data = {}
        get_book = Books.query.filter_by(book_id=book.bookid).first()
        user_data['title'] = get_book.title
        user_data['book_id'] = get_book.book_id
        user_data['method'] = book.method
        user_data['price_rate'] = book.price_rate
        user_data['price'] = book.price
        if book.request_Date is not None:
            user_data['returnDate'] = book.request_Date
        book_author = WrittenByAssociation.query.filter_by(book_id=get_book.book_id).first()
        author = Author.query.filter_by(author_id=book_author.author_id).first()
        user_data['author_name'] = author.author_name
        owner_contains = ContainsAssociation.query.filter_by(book_id=get_book.book_id).first()
        user_data['book_cover'] = get_book.book_cover
        owner_bookshelf = Bookshelf.query.filter_by(bookshelf_id=owner_contains.shelf_id).first()
        owner = User.query.filter_by(username=owner_bookshelf.bookshef_owner).first()
        user_data['owner_fname'] = owner.first_name
        user_data['owner_lname'] = owner.last_name
        user_data['owner_username'] = owner.username
        output.append(user_data)

    print(output)
    return jsonify({'books': output})


#DISPLAY FOR THE OWNER TO SEE THE USERS REQUESTING THE BOOKS
@app.route('/bookshelf/requests/user', methods=['GET', 'POST'])
@token_required
def show_requests(self):
    data = request.get_json()
    bookshelf = Bookshelf.query.filter_by(bookshef_owner=data['current_user']).first()
    output = []
    borrow_books = WaitingList.query.filter_by(owner_shelf_id=bookshelf.bookshelf_id).all()
    if borrow_books is None:
        return make_response('No books found!')
    for book in borrow_books:
        user_data = {}
        get_book = Books.query.filter_by(book_id=book.bookid).first()
        user_data['title'] = get_book.title
        user_data['book_id'] = get_book.book_id
        user_data['method'] = book.method
        user_data['price_rate'] = book.price_rate
        user_data['price'] = book.price
        if book.approval is not None:
            user_data['approval'] = book.approval
        borrower = User.query.filter_by(id=book.borrower).first()
        user_data['borrower'] = borrower.username
        user_data['borrower_fname'] = borrower.first_name
        user_data['borrower_lname'] = borrower.last_name
        if book.request_Date is not None:
            user_data['returnDate'] = book.request_Date
        book_author = WrittenByAssociation.query.filter_by(book_id=get_book.book_id).first()
        author = Author.query.filter_by(author_id=book_author.author_id).first()
        user_data['author_name'] = author.author_name
        owner_contains = ContainsAssociation.query.filter_by(book_id=get_book.book_id).first()
        user_data['book_cover'] = get_book.book_cover
        owner_bookshelf = Bookshelf.query.filter_by(bookshelf_id=owner_contains.shelf_id).first()
        owner = User.query.filter_by(username=owner_bookshelf.bookshef_owner).first()
        user_data['owner_fname'] = owner.first_name
        user_data['owner_lname'] = owner.last_name
        user_data['owner_username'] = owner.username
        output.append(user_data)

    print(output)
    return jsonify({'books': output})

#OWNER OF THE BOOK DECLINES THE REQUEST
@app.route('/bookshelf/remove_borrow', methods=['POST'])
@token_required
def remove_borrow(self):
    data = request.get_json()

    borrower = User.query.filter_by(username=data['username']).first()
    owner = User.query.filter_by(username=data['bookshelf_owner']).first()
    bookshelf = Bookshelf.query.filter_by(bookshef_owner=data['bookshelf_owner']).first()
    book = Books.query.filter_by(book_id=data['book_id']).first()
    print(owner.username)
    print(borrower.username)
    waiting = WaitingList.query.filter((WaitingList.borrower == borrower.id) &
                                       (WaitingList.owner_shelf_id == bookshelf.bookshelf_id) &
                                     (WaitingList.bookid == book.book_id)).first()
    code = CodeVerification.query.filter((CodeVerification.owner_id == owner.id)
                                         & (CodeVerification.borrower_id == borrower.id)
                                         & (CodeVerification.book_id == book.book_id)).first()
    db.session.delete(waiting)
    db.session.commit()
    notifications3 = Notifications.query.filter((Notifications.current_user == owner.id) &
                                                (Notifications.user_id == borrower.id) &
                                                (Notifications.bookshelf_id == owner.id)
                                                & (Notifications.book_id == book.book_id)
                                                & (Notifications.type == 'borrow_request')).\
        order_by(Notifications.logs.desc()).first()
    notifications4 = Notifications.query.filter((Notifications.current_user == owner.id) &
                                                (Notifications.user_id == borrower.id) &
                                                (Notifications.bookshelf_id == owner.id)
                                                & (Notifications.book_id == book.book_id)
                                                & (Notifications.type == 'rent_request')). \
            order_by(Notifications.logs.desc()).first()
    notifications5 = Notifications.query.filter((Notifications.current_user == owner.id) &
                                                (Notifications.user_id == borrower.id) &
                                                (Notifications.bookshelf_id == owner.id)
                                                & (Notifications.book_id == book.book_id)
                                                & (Notifications.type == 'purchase_request'))\
        .order_by(Notifications.logs.desc()).first()
    print('Notifications Delete')
    print(notifications3)
    if notifications3 is not None:
        db.session.delete(notifications3)
    if notifications4 is not None:
        db.session.delete(notifications4)
    if notifications5 is not None:
        db.session.delete(notifications5)
    db.session.commit()
    if code is not None:
        db.session.delete(code)
        db.session.commit()
        notifications = Notifications.query.filter((Notifications.current_user == borrower.id) &
                                                   (Notifications.user_id == owner.id) &
                                                   (Notifications.bookshelf_id == owner.id)
                                                   & (Notifications.book_id == book.book_id)
                                                   & (Notifications.type == 'borrower_request_accepted')).first()
        notifications2 = Notifications.query.filter((Notifications.current_user == owner.id) &
                                                   (Notifications.user_id == borrower.id) &
                                                   (Notifications.bookshelf_id == owner.id)
                                                   & (Notifications.book_id == book.book_id)
                                                   & (Notifications.type == 'owner_request_accepted')).first()

        db.session.delete(notifications)
        db.session.delete(notifications2)
        db.session.commit()
    return jsonify({'message': "Removed successful"})

#STEP 2
#WHEN OWNER APPROVES THE REQUEST OF THE USER
#GENERATES A CODE FOR TRANSACTION OF THE USER AND OWNER
#AFTER GIVING THE BOOK, OWNER MUST ALSO GIVE THE CODE SO THE START TIME WILL START
def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

@app.route('/verification-code', methods=['GET','POST'])
@token_required
def verification_code(self):
    data = request.get_json()
    borrower = User.query.filter_by(username=data['book_borrower']).first()
    bookshelf = Bookshelf.query.filter_by(bookshef_owner=data['book_owner']).first()
    owner = User.query.filter_by(username=data['book_owner']).first()
    book = Books.query.filter_by(book_id=data['book_id']).first()
    print(borrower)
    print(data['book_borrower'])
    print(owner)
    print(data['book_owner'])
    print(book)
    print(data['book_id'])
    waiting = WaitingList.query.filter(
        (WaitingList.borrower == borrower.id) & (WaitingList.owner_shelf_id == bookshelf.bookshelf_id) &
        (WaitingList.bookid == book.book_id)).first()
    code = id_generator()
    code2 = CodeVerification.query.filter((CodeVerification.owner_id == owner.id) &
                                          (CodeVerification.borrower_id == borrower.id) &
                                          (CodeVerification.book_id == book.book_id)).first()
    output = []
    code_dict = {}
    if code2 is None:
        # waiting.approval = True
        code = id_generator()
        code3 = CodeVerification(
            code=code, owner_id=owner.id, borrower_id=borrower.id, book_id=book.book_id)
        db.session.add(code3)
        db.session.commit()
        print("aftercommit")
        print(borrower)
        print(bookshelf)
        print( owner)
        #  waiting.approval = True
        # db.session.commit()
        borrower = User.query.filter_by(username=data['book_borrower']).first()
        book = Books.query.filter_by(book_id=data['book_id']).first()
        owner = User.query.filter_by(username=data['book_owner']).first()
        notifications = Notifications(current_user=borrower.id, user_id=owner.id, bookshelf_id=owner.id,
                                      book_id=book.book_id, last_open=None, type='borrower_request_accepted')
        notifications2 = Notifications(current_user=owner.id, user_id=borrower.id, bookshelf_id=owner.id,
                                       book_id=book.book_id, last_open=None, type='owner_request_accepted')
        db.session.add(notifications)
        db.session.add(notifications2)
        db.session.commit()

    code4 = CodeVerification.query.filter((CodeVerification.owner_id == owner.id) &
                                          (CodeVerification.borrower_id == borrower.id) &
                                          (CodeVerification.book_id == book.book_id)).first()
    code_dict['code'] = code4.code
    output.append(code_dict)
    return jsonify({'code': output})

@app.route('/verification-code-details', methods=['GET', 'POST'])
@token_required
def verification_code_details(self):
    data = request.get_json()
    user = User.query.filter_by(username=data['book_borrower']).first()
    bookshelf = Bookshelf.query.filter_by(bookshef_owner=data['book_owner']).first()
    get_book = Books.query.filter_by(book_id=data['book_id']).first()
    waiting = WaitingList.query.filter(
        (WaitingList.borrower == user.id) & (WaitingList.owner_shelf_id == bookshelf.bookshelf_id) &
        (WaitingList.bookid == get_book.book_id)).first()


    output = []
    user_data = {}
    user_data['title'] = get_book.title
    user_data['book_id'] = get_book.book_id
    user_data['method'] = waiting.method
    user_data['price_rate'] = waiting.price_rate
    user_data['price'] = waiting.price
    borrower = User.query.filter_by(id=waiting.borrower).first()
    user_data['borrower'] = borrower.username
    user_data['borrower_fname'] = borrower.first_name
    user_data['borrower_lname'] = borrower.last_name
    if waiting.request_Date is not None:
        user_data['returnDate'] = waiting.request_Date.strftime('%a, %d %b %Y')
    book_author = WrittenByAssociation.query.filter_by(book_id=get_book.book_id).first()
    author = Author.query.filter_by(author_id=book_author.author_id).first()
    user_data['author_name'] = author.author_name
    owner_contains = ContainsAssociation.query.filter_by(book_id=get_book.book_id).first()
    user_data['book_cover'] = get_book.book_cover
    owner_bookshelf = Bookshelf.query.filter_by(bookshelf_id=owner_contains.shelf_id).first()
    owner = User.query.filter_by(username=owner_bookshelf.bookshef_owner).first()
    user_data['owner_fname'] = owner.first_name
    user_data['owner_lname'] = owner.last_name
    user_data['owner_username'] = owner.username
    output.append(user_data)

    print(output)
    return jsonify({'books': output})


#STEP 3
#WHEN THE USER RECEIVED THE CODE
#ENTERS THE CODE AND MATCHES, THE TIME WILL START
@app.route('/bookshelf/confirm', methods=['POST'])
@token_required
def confirm(self):
    data = request.get_json()


    user = User.query.filter_by(username=data['book_borrower']).first()
    user2 = User.query.filter_by(username=data['book_owner']).first()
    book = Books.query.filter_by(book_id=data['book_id']).first()
    code = CodeVerification.query.filter((CodeVerification.owner_id == user2.id) &
                                         (CodeVerification.borrower_id == user.id)).first()
    print(code.code)
    print(data['code'])
    code_input = str(data['code'])
    code_database = str(code.code)
    if code_database == code_input:
        db.session.delete(code)
        db.session.commit()
        notifications = Notifications.query.filter((Notifications.current_user == user.id) &
                                                   (Notifications.user_id == user2.id) &
                                                   (Notifications.bookshelf_id == user2.id)
                                                   & (Notifications.book_id == book.book_id)
                                                   & (Notifications.type == 'borrower_request_accepted')).first()
        notifications2 = Notifications.query.filter((Notifications.current_user == user2.id) &
                                                   (Notifications.user_id == user.id) &
                                                   (Notifications.bookshelf_id == user2.id)
                                                   & (Notifications.book_id == book.book_id)
                                                   & (Notifications.type == 'owner_request_accepted')).first()
        db.session.delete(notifications)
        db.session.delete(notifications2)
        db.session.commit()
        bookshelf = Bookshelf.query.filter_by(bookshef_owner=data['book_owner']).first()

        waiting = WaitingList.query.filter((WaitingList.borrower == user.id) & (WaitingList.owner_shelf_id == bookshelf.bookshelf_id) &
                                         (WaitingList.bookid == book.book_id)).first()
        if waiting.method == 'Borrow':
            borrow_check = BorrowsAssociation.query.filter((BorrowsAssociation.borrower == user.id) &
                                                           (BorrowsAssociation.owner_shelf_id == bookshelf.bookshelf_id) &
                                                           (BorrowsAssociation.bookid == book.book_id)).first()
            if borrow_check is not None:
                return make_response('Book is already borrowed.')
            borrow = BorrowsAssociation(borrower=user.id, owner_shelf_id=bookshelf.bookshelf_id, bookid=book.book_id,
                                        status='Borrowed', startDate=date.today(), returnDate= datetime.datetime.utcnow() + datetime.timedelta(days=waiting.request_Date),
                                        verification=False)
            db.session.add(borrow)
            db.session.commit()
            contains = ContainsAssociation.query.filter((ContainsAssociation.book_id == book.book_id) & (ContainsAssociation.shelf_id == bookshelf.bookshelf_id)).first()
            contains.quantity = int(contains.quantity) - 1
            if contains.quantity == 0:
                contains.availability = 'NO'
            db.session.commit()
            db.session.delete(waiting)
            db.session.commit()
            notification = ActLogs(current_user_id=user.id, other_user_id=user2.id, bookid=book.book_id,
                                         type='borrower_borrow_book', status=0)
            db.session.add(notification)
            db.session.commit()
            notification1 = Notifications(current_user=user2.id, user_id=user.id,
                                          bookshelf_id=user2.id, book_id=book.book_id,
                                          type='owner_borrow_book', last_open=None)
            db.session.add(notification1)
            db.session.commit()
        elif waiting.method == 'Rent':
            rent_check = RentAssociation.query.filter((RentAssociation.borrower == user.id) &
                                                           (RentAssociation.owner_shelf_id == bookshelf.bookshelf_id) &
                                                           (RentAssociation.bookid == book.book_id)).first()
            if rent_check is not None:
                return make_response('Book is already rented.')
            today = date.today()
            returnDate = waiting.request_Date.date()
            delta = returnDate - today
            total = int(waiting.price_rate * delta.days)
            rent = RentAssociation(borrower=user.id, owner_shelf_id=bookshelf.bookshelf_id, bookid=book.book_id,
                                   status='Rented', startDate=date.today(), returnDate= datetime.datetime.utcnow() + datetime.timedelta(days=waiting.request_Date), price_rate=waiting.price_rate,
                                   verification=False, total=total)
            db.session.add(rent)
            db.session.commit()
            notification = ActLogs(current_user_id=user.id, other_user_id=user2.id, bookid=book.book_id,
                                         type='user_rent_book', status=0)
            db.session.add(notification)
            db.session.commit()
            notification1 = Notifications(current_user=user2.id, user_id=user.id,
                                          bookshelf_id=user2.id, book_id=book.book_id,
                                          type='owner_rent_book', last_open=None)
            db.session.add(notification1)
            db.session.commit()
            contains = ContainsAssociation.query.filter((ContainsAssociation.book_id == book.book_id) & (
            ContainsAssociation.shelf_id == bookshelf.bookshelf_id)).first()
            contains.quantity = int(contains.quantity) - 1
            if contains.quantity == 0:
                contains.availability = 'NO'
            db.session.commit()
            db.session.delete(waiting)
            db.session.commit()
        else:
            rent_check = PurchaseAssociation.query.filter((PurchaseAssociation.buyer == user.id) &
                                                      (PurchaseAssociation.owner_shelf_id == bookshelf.bookshelf_id) &
                                                      (PurchaseAssociation.bookid == book.book_id)).first()
            if rent_check is not None:
                return make_response('Book is already purchased.')
            purchase = PurchaseAssociation(buyer=user.id, owner_shelf_id=bookshelf.bookshelf_id, status='Purchased', price=waiting.price, bookid=book.book_id)
            db.session.add(purchase)
            db.session.commit()
            contains = ContainsAssociation.query.filter((ContainsAssociation.book_id == book.book_id) & (
            ContainsAssociation.shelf_id == bookshelf.bookshelf_id)).first()
            contains.quantity = int(contains.quantity) - 1
            if contains.quantity == 0:
                bookrate = BookRateAssociation.query.filter_by(book_id=contains.contains_id).first()
                bookratetotal = BookRateTotal.query.filter_by(bookRated=contains.contains_id).first()
                if bookrate is not None and bookratetotal is not None:
                    db.session.delete(bookratetotal)
                    db.session.commit()
                    db.session.delete(bookrate)
                    db.session.commit()
                db.session.delete(contains)
                db.session.commit()
            db.session.commit()
            db.session.delete(waiting)
            db.session.commit()
            notification = ActLogs(current_user_id=user.id, other_user_id=user2.id, bookid=book.book_id,
                                         type='user_purchased_book', status=0)
            db.session.add(notification)
            db.session.commit()
            notification1 = Notifications(current_user=user2.id, user_id=user.id,
                                          bookshelf_id=user2.id, book_id=book.book_id,
                                          type='owner_purchased_book', last_open=None)
            db.session.add(notification1)
            db.session.commit()
        return jsonify({'message': "Removed successful"})
    else:
        print('Code invalid')
        return make_response('Code invalid')



@app.route('/borrow_check', methods=['GET'])
@token_required
def borrow_check(self):
    data = request.get_json()
    bookshelf = Bookshelf.query.filter_by(bookshef_owner= data['username']).first()
    book = BorrowsAssociation.query.filter((BorrowsAssociation.owner_shelf_id == bookshelf.bookshelf_id)
                                           & (BorrowsAssociation.bookid == data['book_id'])).first()
    book2 = RentAssociation.query.filter((RentAssociation.owner_shelf_id == bookshelf.bookshelf_id)
                                           & (RentAssociation.bookid == data['book_id'])).first()
    output = []
    if book is None and book2 is None:
        return make_response('Book not borrowed')
    elif book is not None:
        user_data = {}
        borrower = User.query.filter_by(id=book.borrower).first()
        user_data['borrower'] = borrower.username
        user_data['borrower_fname'] = borrower.first_name
        user_data['borrower_lname'] = borrower.last_name
        user_data['owner_username'] = data['username']
        user_data['method'] = 'Borrow'
        output.append(user_data)
        print(output)
        return jsonify({'borrower': output})
    elif book2 is not None:
        user_data = {}
        borrower = User.query.filter_by(id=book2.borrower).first()
        user_data['borrower'] = borrower.username
        user_data['borrower_fname'] = borrower.first_name
        user_data['borrower_lname'] = borrower.last_name
        user_data['owner_username'] = data['username']
        user_data['total'] = book2.total
        user_data['method'] = 'Rent'
        output.append(user_data)
        print(output)
        return jsonify({'borrower': output})


#STEP 4
# THE BORROWER REQUESTS HE HAS RETURNED THE BOOK
@app.route('/borrow_return_request', methods=['POST'])
@token_required
def borrow_return_request(self):
    data = request.get_json()
    book = Books.query.filter_by(book_id= data['book_id']).first()
    user_borrower = User.query.filter_by(username=data['borrower']).first()
    user_owner = User.query.filter_by(username=data['owner']).first()
    forowner = Bookshelf.query.filter_by(bookshelf_id=user_owner.id).first()
    borrow = BorrowsAssociation.query.filter((BorrowsAssociation.owner_shelf_id == forowner.bookshelf_id)
                                            & (BorrowsAssociation.bookid == data['book_id'])
                                            & (BorrowsAssociation.borrower == user_borrower.id)).first()

    notifications = Notifications(current_user=user_owner.id, user_id=user_borrower.id, bookshelf_id=user_owner.id,
                                  book_id=book.book_id, last_open=None, type='borrower_returned_request')
    db.session.add(notifications)
    db.session.commit()
    return make_response('Successful!')

#STEP 5
#THE OWNER CONFIRMS THE REQUEST THAT HE HAVE THE BOOK AFTER BORROWING
@app.route('/borrow_return', methods=['POST'])
@token_required
def borrow_return(self):
    data = request.get_json()
    book = Books.query.filter_by(book_id= data['book_id']).first()
    user_borrower = User.query.filter_by(username=data['borrower']).first()
    user_owner = User.query.filter_by(username=data['owner']).first()
    forowner = Bookshelf.query.filter_by(bookshelf_id=user_owner.id).first()
    borrow = BorrowsAssociation.query.filter((BorrowsAssociation.owner_shelf_id == forowner.bookshelf_id)
                                            & (BorrowsAssociation.bookid == data['book_id'])
                                            & (BorrowsAssociation.borrower == user_borrower.id)).first()
    if borrow is not None:
        borrow.verification = True
        #Delete old notifications
        old_notifications = Notifications.query.filter_by(user_id=user_borrower.id, bookshelf_id=forowner.bookshelf_id,
                                                          book_id=book.book_id, current_user=user_owner.id).all()
        old_notifications2 = Notifications.query.filter_by(user_id=user_owner.id, bookshelf_id=forowner.bookshelf_id,
                                                          book_id=book.book_id, current_user=user_borrower.id).all()
        for old_notif in old_notifications:
            db.session.delete(old_notif)
            db.session.commit()
        for old_notif2 in old_notifications2:
            db.session.delete(old_notif2)
            db.session.commit()

        #Borrower
        notifications = Notifications(current_user=user_borrower.id, user_id=user_owner.id, bookshelf_id=user_owner.id,
                                      book_id=book.book_id, last_open=None, type='borrower_returned_successful')
        #Owner
        actlogs2 = ActLogs(current_user_id=user_owner.id, other_user_id=user_borrower.id, status=0,
                           bookid=book.book_id, type='borrower_returned_successful')
        notifications2 = Notifications(current_user=user_owner.id, user_id=user_borrower.id, bookshelf_id=user_owner.id,
                                      book_id=book.book_id, last_open=None, type='owner_returned_successful')

        db.session.add(notifications)
        db.session.add(actlogs2)
        db.session.add(notifications2)
        db.session.delete(borrow)
        db.session.commit()
        book.borrowcount = book.borrowcount + 1
        contains = ContainsAssociation.query.filter((ContainsAssociation.book_id == book.book_id) & (ContainsAssociation.shelf_id == forowner.bookshelf_id)).first()
        contains.quantity = contains.quantity + 1
        contains.availability = 'YES'
        db.session.commit()
    return make_response('Successful!')

#STEP 5
#THE OWNER CONFIRMS THE REQUEST THAT HE HAVE THE BOOK AFTER RENTING
@app.route('/rent_return', methods=['POST'])
@token_required
def rent_return(self):
    data = request.get_json()
    book = Books.query.filter_by(book_id= data['book_id']).first()
    user_borrower = User.query.filter_by(username=data['borrower']).first()
    user_owner = User.query.filter_by(username=data['owner']).first()
    forowner = Bookshelf.query.filter_by(bookshelf_id=user_owner.id).first()
    borrow = RentAssociation.query.filter((RentAssociation.owner_shelf_id == forowner.bookshelf_id)
                                            & (RentAssociation.bookid == data['book_id'])
                                            & (RentAssociation  .borrower == user_borrower.id)).first()
    if borrow is not None:
        borrow.verification = True
        #Delete old notifications
        old_notifications = Notifications.query.filter_by(user_id=user_borrower.id, bookshelf_id=forowner.bookshelf_id,
                                                          book_id=book.book_id, current_user=user_owner.id).all()
        old_notifications2 = Notifications.query.filter_by(user_id=user_owner.id, bookshelf_id=forowner.bookshelf_id,
                                                          book_id=book.book_id, current_user=user_borrower.id).all()
        for old_notif in old_notifications:
            db.session.delete(old_notif)
            db.session.commit()
        for old_notif2 in old_notifications2:
            db.session.delete(old_notif2)
            db.session.commit()

        #Borrower
        notifications = Notifications(current_user=user_borrower.id, user_id=user_owner.id, bookshelf_id=user_owner.id,
                                      book_id=book.book_id, last_open=None, type='borrower_returned_successful')
        #Owner
        actlogs2 = ActLogs(current_user_id=user_owner.id, other_user_id=user_borrower.id, status=0,
                           bookid=book.book_id, type='borrower_returned_successful')
        notifications2 = Notifications(current_user=user_owner.id, user_id=user_borrower.id, bookshelf_id=user_owner.id,
                                      book_id=book.book_id, last_open=None, type='owner_returned_successful')

        db.session.add(notifications)
        db.session.add(actlogs2)
        db.session.add(notifications2)
        db.session.delete(borrow)
        db.session.commit()
        book.borrowcount = book.borrowcount + 1
        contains = ContainsAssociation.query.filter((ContainsAssociation.book_id == book.book_id) & (ContainsAssociation.shelf_id == forowner.bookshelf_id)).first()
        contains.quantity = contains.quantity + 1
        contains.availability = 'YES'
        db.session.commit()
    return make_response('Successful!')

@app.before_request
def before_request():
	check_date2();

def check_date2():
    borrows = BorrowsAssociation.query.all()
    rents = RentAssociation.query.all()
    waitinglist = WaitingList.query.all()
    today = dt.datetime.now()

    for waiting in waitinglist:
        if waiting.request_Date is not None:
            if waiting.request_Date < today:
                db.session.delete(waiting)
                db.session.commit()
            elif waiting.request_Date == today:
                db.session.delete(waiting)
                db.session.commit()
    for borrow in borrows:
        one_day_left = borrow.returnDate.date() - timedelta(days=1)
        book_owner = Bookshelf.query.filter_by(bookshelf_id=borrow.owner_shelf_id).first()
        book_person = User.query.filter_by(username=book_owner.bookshef_owner).first()
        if datetime.datetime.today().date() == one_day_left:
            notification_check = Notifications.query.filter((Notifications.current_user ==borrow.borrower) &
                                                            (Notifications.user_id == book_person.id) &
                                                            (Notifications.bookshelf_id == borrow.owner_shelf_id) &
                                                            (Notifications.type == 'borrower_borrow_one_day')).first()
            if notification_check is None:
                notification = Notifications(current_user=borrow.borrower, user_id=book_person.id, bookshelf_id=borrow.owner_shelf_id, book_id=borrow.bookid, type='borrower_borrow_one_day', last_open=None)
                db.session.add(notification)
                db.session.commit()
                notification1 = Notifications(current_user=book_person.id, user_id=borrow.borrower,
                                             bookshelf_id=borrow.owner_shelf_id, book_id=borrow.bookid,
                                             type='owner_borrow_one_day', last_open=None)
                db.session.add(notification1)
                db.session.commit()
        elif borrow.returnDate.date() == datetime.datetime.today().date():
            notification_check = Notifications.query.filter((Notifications.current_user ==borrow.borrower) &
                                                            (Notifications.user_id == book_person.id) &
                                                            (Notifications.bookshelf_id == borrow.owner_shelf_id) &
                                                            (Notifications.type == 'borrower_borrow_today')).first()

            if notification_check is None:
                notification = Notifications(current_user=borrow.borrower, user_id=book_person.id,
                                             bookshelf_id=borrow.owner_shelf_id, book_id=borrow.bookid,
                                             type='borrower_borrow_today', last_open=None)
                db.session.add(notification)
                db.session.commit()
                notification1 = Notifications(current_user=book_person.id, user_id=borrow.borrower,
                                              bookshelf_id=borrow.owner_shelf_id, book_id=borrow.bookid,
                                              type='owner_borrow_today', last_open=None)
                db.session.add(notification1)
                db.session.commit()

        elif (borrow.returnDate.date() <  datetime.datetime.today().date()) and (borrow.status == 'Borrowed'):
            delta = datetime.datetime.today().date() - borrow.returnDate.date()
            notification_check = Notifications.query.filter((Notifications.current_user == borrow.borrower) &
                                                            (Notifications.user_id == book_person.id) &
                                                            (Notifications.bookshelf_id == borrow.owner_shelf_id) &
                                                            (Notifications.type == 'borrower_borrow_return_'+str(delta.days))).first()
            if notification_check is None:
                notification = Notifications(current_user=borrow.borrower, user_id=book_person.id,
                                                   bookshelf_id=borrow.owner_shelf_id, book_id=borrow.bookid, last_open=None,
                                                   type='borrower_borrow_return_'+str(delta.days))
                db.session.add(notification)
                db.session.commit()
                notification1 = Notifications(current_user=book_person.id, user_id=borrow.borrower,
                                              bookshelf_id=borrow.owner_shelf_id, book_id=borrow.bookid,
                                              type='owner_borrow_return_verification', last_open=None)
                db.session.add(notification1)
                db.session.commit()

    for borrow in rents:
        one_day_left = borrow.returnDate.date() - timedelta(days=1)
        book_owner = Bookshelf.query.filter_by(bookshelf_id=borrow.owner_shelf_id).first()
        book_person = User.query.filter_by(username=book_owner.bookshef_owner).first()
        if datetime.datetime.today().date() == one_day_left:
            notification_check = Notifications.query.filter((Notifications.current_user ==borrow.borrower) &
                                                            (Notifications.user_id == book_person.id) &
                                                            (Notifications.bookshelf_id == borrow.owner_shelf_id) &
                                                            (Notifications.type == 'renter_rent_one_day')).first()
            if notification_check is None:
                notification = Notifications(current_user=borrow.borrower, user_id=book_person.id,
                                             bookshelf_id=borrow.owner_shelf_id, book_id=borrow.bookid,
                                             type='renter_rent_one_day', last_open=None)
                db.session.add(notification)
                db.session.commit()
                notification1 = Notifications(current_user=book_person.id, user_id=borrow.borrower,
                                              bookshelf_id=borrow.owner_shelf_id, book_id=borrow.bookid,
                                              type='owner_rent_one_day', last_open=None)
                db.session.add(notification1)
                db.session.commit()
        elif borrow.returnDate.date() == datetime.datetime.today().date():
            notification_check = Notifications.query.filter((Notifications.current_user ==borrow.borrower) &
                                                            (Notifications.user_id == book_person.id) &
                                                            (Notifications.bookshelf_id == borrow.owner_shelf_id) &
                                                            (Notifications.type == 'renter_rent_return')).first()
            if notification_check is None:
                notification = Notifications(current_user=borrow.borrower, user_id=book_person.id,
                                             bookshelf_id=borrow.owner_shelf_id, book_id=borrow.bookid,
                                             type='renter_rent_return', last_open=None)
                db.session.add(notification)
                db.session.commit()
                notification1 = Notifications(current_user=book_person.id, user_id=borrow.borrower,
                                              bookshelf_id=borrow.owner_shelf_id, book_id=borrow.bookid,
                                              type='owner_rent_return', last_open=None)
                db.session.add(notification1)
                db.session.commit()

        elif (borrow.returnDate.date() <  datetime.datetime.today().date()) and (borrow.status == 'Rented'):
            delta = datetime.datetime.today().date - borrow.returnDate.date()
            notification_check = Notifications.query.filter((Notifications.current_user == borrow.borrower) &
                                                            (Notifications.user_id == book_person.id) &
                                                            (Notifications.bookshelf_id == borrow.owner_shelf_id) &
                                                            (Notifications.type == 'renter_rent_return_'+delta.days)).first()
            if notification_check is None:
                notification = Notifications(current_user=borrow.borrower, user_id=book_person.id,
                                                   bookshelf_id=borrow.owner_shelf_id, book_id=borrow.bookid,
                                                   type='renter_rent_return_'+delta.days)
                borrow.total = borrow.total + borrow.price_rate
                db.session.add(notification)
                db.session.commit()
                notification1 = Notifications(current_user=book_person.id, user_id=borrow.borrower,
                                              bookshelf_id=borrow.owner_shelf_id, book_id=borrow.bookid,
                                              type='owner_rent_return_verification', last_open=None)
                db.session.add(notification1)
                db.session.commit()

    return jsonify({'message':'date updated!'})

@app.route('/check_date', methods=['GET'])
def check_date():
    borrows = BorrowsAssociation.query.all()
    rents = RentAssociation.query.all()
    waitinglist = WaitingList.query.all()
    # today = date.today()
    today = dt.datetime.now()
    for waiting in waitinglist:
        if waiting.request_Date is not None:
            if waiting.request_Date < today:
                db.session.delete(waiting)
                db.session.commit()
            elif waiting.request_Date == today:
                db.session.delete(waiting)
                db.session.commit()
    for borrow in borrows:
        one_day_left = borrow.returnDate.date() - timedelta(days=1)
        book_owner = Bookshelf.query.filter_by(bookshelf_id=borrow.owner_shelf_id).first()
        book_person = User.query.filter_by(username=book_owner.bookshef_owner).first()
        if datetime.datetime.today().date() == one_day_left:
            notification_check = Notifications.query.filter((Notifications.current_user ==borrow.borrower) &
                                                            (Notifications.user_id == book_person.id) &
                                                            (Notifications.bookshelf_id == borrow.owner_shelf_id) &
                                                            (Notifications.type == 'borrower_borrow_one_day')).first()
            if notification_check is None:
                notification = Notifications(current_user=borrow.borrower, user_id=book_person.id, bookshelf_id=borrow.owner_shelf_id, book_id=borrow.bookid, type='borrower_borrow_one_day', last_open=None)
                db.session.add(notification)
                db.session.commit()
                notification1 = Notifications(current_user=book_person.id, user_id=borrow.borrower,
                                             bookshelf_id=borrow.owner_shelf_id, book_id=borrow.bookid,
                                             type='owner_borrow_one_day', last_open=None)
                db.session.add(notification1)
                db.session.commit()
        elif borrow.returnDate.date() == datetime.datetime.today().date():
            notification_check = Notifications.query.filter((Notifications.current_user ==borrow.borrower) &
                                                            (Notifications.user_id == book_person.id) &
                                                            (Notifications.bookshelf_id == borrow.owner_shelf_id) &
                                                            (Notifications.type == 'borrower_borrow_today')).first()

            if notification_check is None:
                notification = Notifications(current_user=borrow.borrower, user_id=book_person.id,
                                             bookshelf_id=borrow.owner_shelf_id, book_id=borrow.bookid,
                                             type='borrower_borrow_today', last_open=None)
                db.session.add(notification)
                db.session.commit()
                notification1 = Notifications(current_user=book_person.id, user_id=borrow.borrower,
                                              bookshelf_id=borrow.owner_shelf_id, book_id=borrow.bookid,
                                              type='owner_borrow_today', last_open=None)
                db.session.add(notification1)
                db.session.commit()

        elif (borrow.returnDate.date() <  datetime.datetime.today().date()) and (borrow.status == 'Borrowed'):
            delta = datetime.datetime.today().date() - borrow.returnDate.date()
            notification_check = Notifications.query.filter((Notifications.current_user == borrow.borrower) &
                                                            (Notifications.user_id == book_person.id) &
                                                            (Notifications.bookshelf_id == borrow.owner_shelf_id) &
                                                            (Notifications.type == 'borrower_borrow_return_'+str(delta.days))).first()
            if notification_check is None:
                notification = Notifications(current_user=borrow.borrower, user_id=book_person.id,
                                                   bookshelf_id=borrow.owner_shelf_id, book_id=borrow.bookid, last_open=None,
                                                   type='borrower_borrow_return_'+str(delta.days))
                db.session.add(notification)
                db.session.commit()
                notification1 = Notifications(current_user=book_person.id, user_id=borrow.borrower,
                                              bookshelf_id=borrow.owner_shelf_id, book_id=borrow.bookid,
                                              type='owner_borrow_return_verification', last_open=None)
                db.session.add(notification1)
                db.session.commit()

    for borrow in rents:
        one_day_left = borrow.returnDate.date() - timedelta(days=1)
        book_owner = Bookshelf.query.filter_by(bookshelf_id=borrow.owner_shelf_id).first()
        book_person = User.query.filter_by(username=book_owner.bookshef_owner).first()
        if datetime.datetime.today().date() == one_day_left:
            notification_check = Notifications.query.filter((Notifications.current_user ==borrow.borrower) &
                                                            (Notifications.user_id == book_person.id) &
                                                            (Notifications.bookshelf_id == borrow.owner_shelf_id) &
                                                            (Notifications.type == 'renter_rent_one_day')).first()
            if notification_check is None:
                notification = Notifications(current_user=borrow.borrower, user_id=book_person.id,
                                             bookshelf_id=borrow.owner_shelf_id, book_id=borrow.bookid,
                                             type='renter_rent_one_day', last_open=None)
                db.session.add(notification)
                db.session.commit()
                notification1 = Notifications(current_user=book_person.id, user_id=borrow.borrower,
                                              bookshelf_id=borrow.owner_shelf_id, book_id=borrow.bookid,
                                              type='owner_rent_one_day', last_open=None)
                db.session.add(notification1)
                db.session.commit()
        elif borrow.returnDate.date() == datetime.datetime.today().date():
            notification_check = Notifications.query.filter((Notifications.current_user ==borrow.borrower) &
                                                            (Notifications.user_id == book_person.id) &
                                                            (Notifications.bookshelf_id == borrow.owner_shelf_id) &
                                                            (Notifications.type == 'renter_rent_return')).first()
            if notification_check is None:
                notification = Notifications(current_user=borrow.borrower, user_id=book_person.id,
                                             bookshelf_id=borrow.owner_shelf_id, book_id=borrow.bookid,
                                             type='renter_rent_return', last_open=None)
                db.session.add(notification)
                db.session.commit()
                notification1 = Notifications(current_user=book_person.id, user_id=borrow.borrower,
                                              bookshelf_id=borrow.owner_shelf_id, book_id=borrow.bookid,
                                              type='owner_rent_return', last_open=None)
                db.session.add(notification1)
                db.session.commit()

        elif (borrow.returnDate.date() <  datetime.datetime.today().date()) and (borrow.status == 'Rented'):
            delta = datetime.datetime.today().date - borrow.returnDate.date()
            notification_check = Notifications.query.filter((Notifications.current_user == borrow.borrower) &
                                                            (Notifications.user_id == book_person.id) &
                                                            (Notifications.bookshelf_id == borrow.owner_shelf_id) &
                                                            (Notifications.type == 'renter_rent_return_'+delta.days)).first()
            if notification_check is None:
                notification = Notifications(current_user=borrow.borrower, user_id=book_person.id,
                                                   bookshelf_id=borrow.owner_shelf_id, book_id=borrow.bookid,
                                                   type='renter_rent_return_'+delta.days)
                borrow.total = borrow.total + borrow.price_rate
                db.session.add(notification)
                db.session.commit()
                notification1 = Notifications(current_user=book_person.id, user_id=borrow.borrower,
                                              bookshelf_id=borrow.owner_shelf_id, book_id=borrow.bookid,
                                              type='owner_rent_return_verification', last_open=None)
                db.session.add(notification1)
                db.session.commit()

    return make_response('date updated!')

@app.route('/notifications', methods=['GET', 'POST'])
@token_required
def get_notifications(self):
    data = request.get_json()

    user = User.query.filter_by(username=data['current_user']).first()
    notifications = Notifications.query.filter_by(current_user=user.id).order_by(desc(Notifications.date)).all()
    notifications_unread = Notifications.query.filter((Notifications.current_user == user.id) & (Notifications.last_open == None)).count()
    output = []
    for notification in notifications:
        user_data = {}
        get_book = Books.query.filter_by(book_id=notification.book_id).first()
        if get_book is not None:
            user_data['title'] = get_book.title
            user_data['book_id'] = get_book.book_id
        borrower = User.query.filter_by(id=notification.user_id).first()
        user_data['borrower'] = borrower.username
        user_data['borrower_fname'] = borrower.first_name
        user_data['borrower_lname'] = borrower.last_name
        bookshelf = Bookshelf.query.filter_by(bookshelf_id=notification.bookshelf_id).first()
        if bookshelf is not None:
            username1 = User.query.filter_by(username=bookshelf.bookshef_owner).first()
            user_data['owner_username'] = username1.username
        else:
            username1 = User.query.filter_by(id=notification.user_id).first()
            user_data['owner_username'] = username1.username
        user_data['type'] = notification.type
        user_data['unread'] = notification.last_open
        now = notification.date.strftime('%b %d, %Y at %I:%M %p')
        user_data['time'] = now
        output.append(user_data)

    return jsonify({'notifications': output, 'total': notifications_unread})

@app.route('/mark-read', methods=['POST'])
def mark_read():
    data = request.get_json()
    user = User.query.filter_by(username=data['current_user']).first()
    notifications = Notifications.query.filter_by(current_user=user.id).order_by(desc(Notifications.date)).all()
    notifications_unread = Notifications.query.filter(
        (Notifications.current_user == user.id) & (Notifications.last_open == None)).all()
    for notification in notifications_unread:
        notification.last_open = datetime.datetime.now()
        db.session.commit()
    return make_response('Success')

@app.route('/get-followers', methods=['GET', 'POST'])
@token_required
def get_followers(self):
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    followers = Followers.query.filter_by(followed_username=user.username).all()
    if followers is None:
        return make_response('No followers')
    output = []
    for follower in followers:
        user_data = {}
        user_follower = User.query.filter_by(username=follower.follower_username).first()
        user_data['username'] = user_follower.username
        user_data['first_name'] = user_follower.first_name
        user_data['last_name'] = user_follower.last_name
        output.append(user_data)
    print(output)
    return jsonify({'followers': output})

@app.route('/get-following', methods=['GET','POST'])
@token_required
def get_following(self):
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    following = Followers.query.filter_by(follower_username=user.username).all()
    if following is None:
        return make_response('No following')
    output = []
    for f in following:
        user_data = {}
        user_following = User.query.filter_by(username=f.followed_username).first()
        user_data['username'] = user_following.username
        user_data['first_name'] = user_following.first_name
        user_data['last_name'] = user_following.last_name
        output.append(user_data)

    return jsonify({'following': output})

@app.route('/follow-check', methods=['GET','POST'])
@token_required
def follow_check(self):
    data = request.get_json()
    followed = User.query.filter_by(username=data['username']).first()
    print(data['username'])
    follower = User.query.filter_by(username=data['current_user']).first()
    follow_test = Followers.query.filter(
        (Followers.follower_username == follower.username) & (Followers.followed_username == followed.username)).first()
    if follow_test is None:
        return jsonify({'data':'Not Following'})
    else:
        return jsonify({'data': 'Following'})

@app.route('/follow', methods=['POST'])
@token_required
def follow(self):
    data = request.get_json()
    followed = User.query.filter_by(username=data['username']).first()
    follower = User.query.filter_by(username=data['current_user']).first()
    follow_test = Followers.query.filter((Followers.follower_username == follower.username) & (Followers.followed_username == followed.username)).first()

    if follow_test is None:
        new_follow = Followers(followed_username=followed.username, follower_username=follower.username)
        db.session.add(new_follow)
        db.session.commit()
        notifications2 = Notifications(current_user=followed.id, user_id=follower.id, bookshelf_id=None, book_id=None, last_open=None, type='user_follow')
        db.session.add(notifications2)
        db.session.commit()
        actlogs = ActLogs(current_user_id=follower.id, other_user_id=followed.id,
                          bookid=None, status=0, type='follow')
        db.session.add(actlogs)
        db.session.commit()

    return jsonify({'data':'Success'})

@app.route('/unfollow', methods=['POST'])
@token_required
def unfollow(self):
    data = request.get_json()
    followed = User.query.filter_by(username=data['username']).first()
    follower = User.query.filter_by(username=data['current_user']).first()
    follow_test = Followers.query.filter((Followers.follower_username == follower.username) & (Followers.followed_username == followed.username)).first()
    if follow_test is not None:
        db.session.delete(follow_test)
        db.session.commit()
        notification_check = Notifications.query.filter((Notifications.current_user == followed.id) &
                                                        (Notifications.user_id == follower.id) &
                                                        (Notifications.type == 'user_follow')).first()
        if notification_check is not None:
            db.session.delete(notification_check)
            db.session.commit()
            actlogs = ActLogs.query.filter((ActLogs.current_user_id == follower.id) &
                                           (ActLogs.other_user_id == followed.id) &
                                           (ActLogs.type == 'follow')).first()
            actlogs.type = 'unfollow'
            db.session.commit()

    return jsonify({'data':'Success'})

@app.route('/activity_logs', methods=['GET','POST'])
@token_required
def activity_logs(self):
    data = request.get_json()
    user = User.query.filter_by(username=data['current_user']).first()
    print user
    activity = ActLogs.query.filter_by(current_user_id=user.id).order_by(desc(ActLogs.date)).all()
    output=[]
    for notification in activity:
        user_data = {}
        get_book = Books.query.filter_by(book_id=notification.bookid).first()
        if get_book is not None:
            user_data['title'] = get_book.title
            user_data['book_id'] = get_book.book_id
        borrower = User.query.filter_by(id=notification.other_user_id).first()
        if borrower is not None:
            user_data['borrower'] = borrower.username
            user_data['borrower_fname'] = borrower.first_name
            user_data['borrower_lname'] = borrower.last_name
        user_data['type'] = notification.type
        now = notification.date.strftime('%b %d, %Y at %I:%M %p')
        user_data['time'] = now
        output.append(user_data)

    return jsonify({'activities': output})

@app.route('/activity_logs_mobile', methods=['GET','POST'])
@token_required
def activity_logs_mobile(self):
    data = request.get_json()
    user=User.query.filter_by(username=data['current_user']).first()
    activity = ActLogs.query.filter_by(current_user_id=user.id).order_by(desc(ActLogs.date)).all()
    output = []
    for notification in activity:
        user_data = {}
        get_book = Books.query.filter_by(book_id=notification.bookid).first()
        if get_book is not None:
            user_data['title'] = get_book.title
            user_data['book_id'] = get_book.book_id
        borrower = User.query.filter_by(id=notification.other_user_id).first()
        if borrower is not None:
            user_data['borrower'] = borrower.username
            user_data['borrower_fname'] = borrower.first_name
            user_data['borrower_lname'] = borrower.first_name
        if notification.type == 'borrower_borrow_book':
            user_data['content'] = 'You have borrowed '+ borrower.first_name+ ' ' +borrower.first_name+ ' book.'
        elif notification.type == 'user_rent_book':

            user_data['content'] ='You have rented'+ borrower.first_name+ ' ' +borrower.first_name+"'s" + ' book.'

        elif notification.type == 'user_purchased_book':
            user_data['content'] ='You have purchased'+ borrower.first_name+ ' ' +borrower.first_name+"'s"+' book.'

        elif notification.type == 'addbook':
            user_data['content'] ='You have added a book.'
        elif notification.type == 'request':

            user_data['content'] ='You have sent a request for a book.'
        elif notification.type == 'follow':

            user_data['content'] ='You have followed'+ borrower.first_name+ ' ' +borrower.first_name
        elif notification.type == 'unfollow':

            user_data['content'] ='You have unfollowed'+ borrower.first_name+ ' ' +borrower.first_name
        elif notification.type == 'borrower_returned_successful':

            user_data['content'] ='You have returned'+ borrower.first_name+ ' ' +borrower.first_name+"'s" + 'book.'

        date = notification.date.strftime('%b %d, %Y')
        time = notification.date.strftime('%I:%M %p')
        user_data['date'] = date
        user_data['time'] = time
        output.append(user_data)

    return jsonify({'activities': output})

@app.route('/message', methods=['POST'])
@token_required
def message(self):
    data = request.get_json()
    current_user = User.query.filter_by(username=data['current_user']).first()
    other_user = User.query.filter_by(username=data['name']).first()
    check_inbox = Inbox.query.filter((Inbox.user1 == current_user.id) & (Inbox.user2 == other_user.id)).first()
    check_inbox2 = Inbox.query.filter((Inbox.user2 == current_user.id) & (Inbox.user1 == other_user.id)).first()
    if check_inbox is None and check_inbox2 is None:
        new_inbox = Inbox(user1=current_user.id, user2=other_user.id)
        db.session.add(new_inbox)
        db.session.commit()
        get_inbox = Inbox.query.filter((Inbox.user1 == current_user.id) & (Inbox.user2 == other_user.id)).first()
        new_message = Message(inbox_id=get_inbox.inbox_id, message_from=current_user.id, message_to=other_user.id, content=data['content'])
        db.session.add(new_message)
        db.session.commit()
    elif check_inbox is not None:
        new_message = Message(inbox_id=check_inbox.inbox_id, message_from=current_user.id, message_to=other_user.id,
                              content=data['content'])
        db.session.add(new_message)
        db.session.commit()
    elif check_inbox2 is not None:
        new_message = Message(inbox_id=check_inbox2.inbox_id, message_from=current_user.id, message_to=other_user.id,
                              content=data['content'])
        db.session.add(new_message)
        db.session.commit()
    return make_response('Success!')

@app.route('/get_inbox', methods=['GET', 'POST'])
@token_required
def get_inbox(self):
    data = request.get_json()
    current_user = User.query.filter_by(username=data['current_user']).first()
    check_inbox = Inbox.query.filter((Inbox.user1 == current_user.id) | (Inbox.user2 == current_user.id)).all()
    output = []
    for inbox in check_inbox:
        user_data1 = {}
        messages = Message.query.filter_by(inbox_id=inbox.inbox_id).all()
        user_data1['inbox_id'] = inbox.inbox_id
        user = User.query.filter((User.username != data['current_user']) &
                                 ((User.id == inbox.user1) | (User.id == inbox.user2))).first()
        user_data1['username'] = user.username
        latest = Message.query.filter_by(inbox_id=inbox.inbox_id).order_by(desc(Message.datetime)).first()
        user_data1['latest'] = latest.content
        user_data1['latest_time'] = latest.datetime.strftime('%b %d, %Y at %I:%M %p')
        user_data1['latest_date'] = latest.datetime.strftime('%b %d, %Y')
        user_data1['latest_time2'] = latest.datetime.strftime('%I:%M %p')
        output.append(user_data1)
    return jsonify({'inbox': output})

@app.route('/get_messages', methods=['GET', 'POST'])
@token_required
def get_messages(self):
    data = request.get_json()
    current_user = User.query.filter_by(username=data['current_user']).first()
    check_inbox = Inbox.query.filter((Inbox.user1 == current_user.id) | (Inbox.user2 == current_user.id)).all()
    output = []
    for inbox in check_inbox:
        user_data = {}
        messages = Message.query.filter_by(inbox_id=inbox.inbox_id).all()
        user_data['id'] = inbox.inbox_id
        for message in messages:
            user_data1 = {}
            user_data1['inbox_id'] = message.inbox_id
            user_data1['content'] = message.content
            user_data1['message_from'] = message.message_from
            user_data1['message_to'] = message.message_to
            user_data1['date'] = message.datetime.strftime('%b %d, %Y at %I:%M %p')
            if message.message_from == current_user.id:
                user_data1['from'] = 'Me'
            else:
                user_data1['from'] = 'Other_user'
            output.append(user_data1)
        output.append(user_data)
    return jsonify({'messages':output})


@app.route('/get_messages/user', methods=['GET', 'POST'])
@token_required
def get_messages_user(self):
    data = request.get_json()
    current_user = User.query.filter_by(username=data['current_user']).first()
    other_user = User.query.filter_by(username=data['username']).first()
    check_inbox = Inbox.query.filter(((Inbox.user1 == current_user.id) & (Inbox.user2 == other_user.id)) | (
        (Inbox.user1 == other_user.id) & (Inbox.user2 == current_user.id))).first()
    output = []
    user_data = {}
    messages = Message.query.filter_by(inbox_id=check_inbox.inbox_id).all()
    user_data['id'] = check_inbox.inbox_id
    for message in messages:
        user_data1 = {}
        user_data1['inbox_id'] = message.inbox_id
        user_data1['content'] = message.content
        user_data1['message_from'] = message.message_from
        user_data1['message_to'] = message.message_to
        user_data1['time'] = message.datetime.strftime(
            '%I:%M %p')
        user_data1['date'] = message.datetime.strftime(
            '%b %d, %Y')
        if message.message_from == current_user.id:
            user_data1['from'] = 'Me'
        else:
            user_data1['from'] = 'Other_user'
        output.append(user_data1)
    output.append(user_data)
    return jsonify({'messages': output})


@app.route('/review/book', methods=['GET', 'POST'])
def review_book():
    data = request.get_json()
    current_user = User.query.filter_by(username=data['current_user']).first()
    book = Books.query.filter_by(book_id=data['book_id']).first()
    if book is None:
        return make_response('Could not comment!')
    else:
        comment = BookReview(
            comment=data['comment'], rating=data['rating'], user_id=current_user.id, book_id=book.book_id)
        comment_get = BookReview.query.filter((BookReview.book_id == book.book_id) & (
            BookReview.user_id == current_user.id)).first()
        rating = BookReview_RateTotal.query.filter_by(
            book_id=book.book_id).first()
        if comment_get is None:
            db.session.add(comment)
            if rating is None:
                rating_new = BookReview_RateTotal(
                    book_id=book.book_id, totalRate=data['rating'], numOfRates=1)
                db.session.add(rating_new)
            else:
                ratingfloat = float(data['rating'])
                rating.totalRate = float(rating.totalRate) + ratingfloat
                rating.numOfRates = rating.numOfRates + 1
        else:
            comment_get.comment = data['comment']
            comment_get.rating = data['rating']
            rating.totalRate = float(rating.totalRate) + float(data['rating'])
            rating.numOfRates = rating.numOfRates + 1
            db.session.commit()
            return jsonify({'messages': 'Review changed'})
    db.session.commit()
    return make_response('Comment posted!')


@app.route('/bookshelf/review/book', methods=['GET', 'POST'])
def get_reviews():
    data = request.get_json()
    book = Books.query.filter_by(book_id=data['book_id']).first()
    comments = BookReview.query.filter_by(book_id=book.book_id).all()
    output = []
    for comment in comments:
        comments1 = {}
        comments1['comment'] = comment.comment
        comments1['rating'] = comment.rating
        totalRate = BookReview_RateTotal.query.filter_by(
            book_id=book.book_id).first()
        if totalRate is not None:
            comments1['totalRate'] = (
                (totalRate.totalRate / totalRate.numOfRates))
            comments1['numofRates'] = totalRate.numOfRates
        else:  # No rating on book
            comments1['totalRate'] = 0.0
            comments1['numofRates'] = 0
        fmt = "%a, %d %b %Y %H:%M:%S GMT"
        # Convert time to format(Ex. Sat, 26 Jan 2018 13:43)
        now = comment.date.strftime('%a, %d %b %Y %H:%M')
        comments1['date'] = now
        user_commenter = User.query.filter_by(id=comment.user_id).first()
        comments1['user_fname'] = user_commenter.first_name
        comments1['user_lname'] = user_commenter.last_name
        comments1['user_username'] = user_commenter.username
        output.append(comments1)

    return jsonify({'comments': output})

@app.route('/user/info/<user_id>/upload', methods=['POST'])
def upload_profpic(user_id):
    
    img_type = request.form['img_type']
    file = request.files['image']
    tempid = random.randint(1, 200)
    
    msg = cloudinary_upload(user_id, img_type, file, tempid, allowed_file, app_dump, Images)
    uploaded = Images.query.filter_by(acc_id = user_id).first()
    return jsonify({'msg':msg,'id':uploaded.acc_id,'img':uploaded.img})

@app.route('/user/info/<user_id>/photo', methods=['GET'])
def show_profpic(user_id):

    user = Images.query.filter_by(acc_id=user_id).first()
    if not user:
        return make_response('no user found!')
    if user.img is None:
        return jsonify({'img': 'https://res.cloudinary.com/dal7ygjnn/image/upload/v1558839529/ov1akhxntwxpy13rzggs.gif'})
    return jsonify({'img': user.img})

