from flask_sqlalchemy import SQLAlchemy
from flask import Flask
import sqlalchemy, datetime
from flask_login import UserMixin

from __init__ import app


db = SQLAlchemy(app)


class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    contact_number = db.Column(db.String(11))
    birth_date = db.Column(db.DATE, nullable=False)
    gender = db.Column(db.String(6), nullable=False)
    longitude = db.Column(db.FLOAT, nullable=False)
    latitude = db.Column(db.FLOAT, nullable=False)
    address = db.Column(db.String(100))
    bookshelf_user = db.relationship('Bookshelf', uselist=False, backref='user_bookshelf')
    borrow_bookshelfs = db.relationship('BorrowsAssociation', backref='user_borrow')
    rent_bookshelfs = db.relationship('RentAssociation', backref='user_rent')
    waitinglist = db.relationship('WaitingList', backref='user_watinglist')
    wishlists_bookshelf = db.relationship('Wishlist', backref='user_wishlist')
    user_interest = db.relationship('InterestAssociation', backref='user_interest')

    def __init__(self, username='', password='', first_name='', last_name='', contact_number='', birth_date='',
                 gender='', longitude='', latitude='', profpic='', address=''):
        self.username = username
        self.password = password
        self.first_name = first_name
        self.last_name = last_name
        self.contact_number = contact_number
        self.birth_date = birth_date
        self.gender = gender
        self.longitude = longitude
        self.latitude = latitude
        self.profpic = profpic
        self.address = address

class Token(db.Model):
    __tablename__ = 'token'
    id = db.Column(db.Integer, db.ForeignKey('user.id'))
    token = db.Column(db.String(125), primary_key=True)
    TTL = db.Column(db.DateTime)

    def __init__(self, id='', token='', TTL=''):
        self.id = id
        self.token = token
        self.TTL = TTL

class Bookshelf(db.Model):
    __tablename__ = 'bookshelf'
    bookshelf_id = db.Column(db.Integer, primary_key=True)
    bookshef_owner = db.Column(db.String, db.ForeignKey('user.username'))
    owner = db.relationship('User', backref='bookshelf_owner')
    booksContain = db.relationship('ContainsAssociation', backref=db.backref('bookshelf_contains'))
    borrow_users = db.relationship('BorrowsAssociation', backref='bookshelfBooks')
    rent_users = db.relationship('RentAssociation', backref='rentBooks')
    waitinglist = db.relationship('WaitingList', backref='waitingBooks')
    wishlist_users = db.relation('Wishlist', backref='bookshelfwish')
    purchase = db.relationship('PurchaseAssociation', backref='books_purchase')

    def __init__(self, bookshelf_id='', bookshef_owner=''):
        self.bookshelf_id = bookshelf_id
        self.bookshef_owner = bookshef_owner

#add rating and time

class Books(db.Model):
    __tablename__ = 'books'
    book_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.TEXT, nullable=False)
    description = db.Column(db.VARCHAR, nullable=True)
    edition = db.Column(db.Integer, nullable=True)
    year_published = db.Column(db.String(500), nullable=True)
    isbn = db.Column(db.String(20), nullable=True, unique=True)
    types = db.Column(db.String(20), nullable=True)
    book_cover = db.Column(db.TEXT, nullable=True)
    publisher_id = db.Column(db.Integer, db.ForeignKey('publisher.publisher_id'), nullable=True)
    bookshelfBooks = db.relationship('ContainsAssociation', backref='books_contains')
    categoryBooks = db.relationship('CategoryAssociation', backref='books_category')
    booksAuthor = db.relationship('WrittenByAssociation', backref='books_author')
    publisher = db.relationship('Publisher', backref='bookPublish')
    booksInGenre = db.relationship('HasGenreAssociation', backref='books_genre')

    borrowcount = db.Column(db.Integer, default=0)

    def __init__(self, title='', description='', edition='', year_published='', isbn='', types='', publisher_id='', book_cover=''):
        self.title = title
        self.description = description
        self.edition = edition
        self.year_published = year_published
        self.isbn = isbn
        self.types = types
        self.publisher_id = publisher_id
        self.book_cover = book_cover


class ContainsAssociation(db.Model):
    __tablename__ = 'contains'
    contains_id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer)
    availability = db.Column(db.String(3))
    methods= db.Column(db.String(50))
    price = db.Column(db.Integer, nullable=True)
    price_rate = db.Column(db.Integer, nullable=True)
    date = db.Column(db.DateTime, default=datetime.datetime.today)
    shelf_id = db.Column(db.Integer, db.ForeignKey('bookshelf.bookshelf_id'))
    book_id = db.Column(db.Integer, db.ForeignKey('books.book_id'))
    rateBooks = db.relationship('BookRateAssociation', backref='books_rateBooks')
    commentBooks = db.relationship('BookCommentAssociation', backref='books_commentBooks')
    bookshelfcontain = db.relationship('Bookshelf', backref='containingbooks')
    containsbooks = db.relationship('Books', backref='booksBookshelf')

    def __init__(self, shelf_id='', book_id='', quantity='', availability='', methods='', price='', price_rate=''):
        self.shelf_id = shelf_id
        self.book_id = book_id
        self.quantity = quantity
        self.methods = methods
        self.price = price
        self.price_rate = price_rate
        self.availability = availability

class Category(db.Model):
    __tablename__ = 'category'
    category_id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String)
    books = db.relationship('CategoryAssociation', backref='books_cat')

    def __init__(self, category_name=''):
        self.category_name = category_name

class CategoryAssociation(db.Model):
    __tablename__ = 'category_association'
    category_book_id = db.Column(db.Integer)
    book_id = db.Column(db.Integer, db.ForeignKey('books.book_id'), primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.category_id'), primary_key=True)
    book = db.relationship('Books', backref='categorybook')
    category = db.relationship('Category', backref='category_ass')

    def __init__(self, book_id='', category_id=''):
        self.book_id = book_id
        self.category_id = category_id

class Author(db.Model):
    __tablename__ = 'author'
    author_id = db.Column(db.Integer, primary_key=True)
    author_name = db.Column(db.String(50))
    authorBooks = db.relationship('WrittenByAssociation', backref="author_books")

    def __init__(self, author_name=''):
        self.author_name = author_name


class WrittenByAssociation(db.Model):
    __tablename__ = 'writtenBy'
    book_id = db.Column(db.Integer, db.ForeignKey('books.book_id'), primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('author.author_id'))
    author = db.relationship('Author', backref='author_writtenby')
    books = db.relationship('Books', backref='booksAuthor_writtenby')

    def __init__(self, author_id='', book_id=''):
        self.author_id = author_id
        self.book_id = book_id


class Publisher(db.Model):
    __tablename__ = 'publisher'
    publisher_id = db.Column(db.Integer, primary_key=True)
    publisher_name = db.Column(db.String(50))
    publishBooks = db.relationship('Books', backref='publisher_books')

    def __init__(self, publisher_name=''):
        self.publisher_name = publisher_name


class Genre(db.Model):
    __tablename__ = 'genre'
    id_genre = db.Column(db.Integer, primary_key=True)
    genre_name = db.Column(db.String, nullable=False, unique=True)
    genreBooks = db.relationship('HasGenreAssociation', backref='genres_books')
    genreInterest = db.relationship('InterestAssociation', backref='genre_interest')

    def __init__(self, genre_name=''):
        self.genre_name = genre_name

class HasGenreAssociation(db.Model):
    __tablename__ = 'hasGenre'
    genre_book_id = db.Column(db.Integer, primary_key=True)
    genreId = db.Column(db.Integer, db.ForeignKey('genre.id_genre'))
    bookId = db.Column(db.Integer, db.ForeignKey('books.book_id'))
    books = db.relationship('Books', backref='booksGenre')
    genre = db.relationship('Genre', backref='bookHasGenre')

    def __init__(self, bookId='', genreId=''):
        self.bookId = bookId
        self.genreId = genreId

class InterestAssociation(db.Model):
    __tablename__ = 'hasInterest'
    interestId = db.Column(db.Integer, primary_key=True)
    user_Id = db.Column(db.Integer, db.ForeignKey('user.id'))
    genreId = db.Column(db.Integer, db.ForeignKey('genre.id_genre'))
    user = db.relationship('User', backref='Interestuser')
    genre = db.relationship('Genre', backref='Interestgenre')




class PurchaseAssociation(db.Model):
    __tablename__ = 'purchase'
    purchase_id = db.Column(db.Integer, primary_key=True)
    buyer = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String)
    owner_shelf_id = db.Column(db.Integer, db.ForeignKey('bookshelf.bookshelf_id'))
    bookid = db.Column(db.Integer, db.ForeignKey('books.book_id'))
    price = db.Column(db.Integer)
    date = db.Column(db.DateTime, default=datetime.datetime.today)
    user = db.relationship('User', backref='purchaseBook')
    bookshelf = db.relationship('Bookshelf', backref='purchasebook')

    def __init__(self, buyer='', owner_shelf_id='', status='', price='', bookid=''):
        self.buyer = buyer
        self.owner_shelf_id = owner_shelf_id
        self.status = status
        self.price = price
        self.bookid = bookid

class CodeVerification(db.Model):
    __tablename__ = 'CodeVerification'
    code_id = db.Column(db.Integer, primary_key = True)
    code = db.Column(db.String, nullable=False)
    owner_id = db.Column(db.Integer)
    borrower_id = db.Column(db.Integer)
    book_id = db.Column(db.Integer)

    def __init__(self, code='', owner_id='', borrower_id='', book_id=''):
        self.code = code
        self.owner_id = owner_id
        self.borrower_id = borrower_id
        self.book_id = book_id


class WaitingList(db.Model):
    waiting_id = db.Column(db.Integer, primary_key=True)
    approval = db.Column(db.Boolean, nullable=True)
    method = db.Column(db.String)
    request_Date = db.Column(db.Integer, nullable=True)
    borrower = db.Column(db.Integer, db.ForeignKey('user.id'))
    price = db.Column(db.Integer, nullable=True)
    price_rate = db.Column(db.Integer, nullable=True)
    owner_shelf_id = db.Column(db.Integer, db.ForeignKey('bookshelf.bookshelf_id'))
    bookid = db.Column(db.Integer, db.ForeignKey('books.book_id'))
    user = db.relationship('User', backref='waitingUsers')
    bookshelf = db.relationship('Bookshelf', backref='waitingBookshelf')

    def __init__(self, borrower='', owner_shelf_id='', price='', price_rate='', approval='', method='', bookid='', request_Date=''):
        self.borrower = borrower
        self.owner_shelf_id = owner_shelf_id
        self.approval = approval
        self.price_rate = price_rate
        self.price = price
        self.bookid = bookid
        self.method = method
        self.request_Date = request_Date
class RentAssociation(db.Model):
    __tablename__ = 'rents'
    borrowed = db.Column(db.Integer, primary_key=True)
    borrower = db.Column(db.Integer, db.ForeignKey('user.id'))
    owner_shelf_id = db.Column(db.Integer, db.ForeignKey('bookshelf.bookshelf_id'))
    bookid = db.Column(db.Integer, db.ForeignKey('books.book_id'))
    status = db.Column(db.String)
    total = db.Column(db.Integer)
    price_rate = db.Column(db.Integer)
    startDate = db.Column(db.DateTime)
    returnDate = db.Column(db.DateTime)
    verification = db.Column(db.Boolean)
    user = db.relationship('User', backref='userRent')
    bookshelf = db.relationship('Bookshelf', backref='bookRent')

    def __init__(self, borrower='', owner_shelf_id='', status='', verification='', price_rate='', bookid='', total='', startDate='', returnDate=''):
        self.borrower = borrower
        self.owner_shelf_id = owner_shelf_id
        self.status = status
        self.bookid = bookid
        self.total = total
        self.verification = verification
        self.price_rate = price_rate
        self.startDate = startDate
        self.returnDate = returnDate

class BorrowsAssociation(db.Model):
    __tablename__ = 'borrows'
    borrowed = db.Column(db.Integer, primary_key=True)
    borrower = db.Column(db.Integer, db.ForeignKey('user.id'))
    owner_shelf_id = db.Column(db.Integer, db.ForeignKey('bookshelf.bookshelf_id'))
    bookid = db.Column(db.Integer, db.ForeignKey('books.book_id'))
    status = db.Column(db.String)
    startDate = db.Column(db.DateTime)
    returnDate = db.Column(db.DateTime)
    verification = db.Column(db.Boolean)
    user = db.relationship('User', backref='borrowBookshelfs')
    bookshelf = db.relationship('Bookshelf', backref='borrowUsers')

    def __init__(self, borrower='', owner_shelf_id='', status='', bookid='', verification='', startDate='', returnDate=''):
        self.borrower = borrower
        self.owner_shelf_id = owner_shelf_id
        self.status = status
        self.bookid = bookid
        self.verification = verification
        self.startDate = startDate
        self.returnDate = returnDate


class Wishlist(db.Model):
    __tablename__ = "wishlist"
    wishlist_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    shelf_id = db.Column(db.Integer, db.ForeignKey('bookshelf.bookshelf_id'))
    bookId = db.Column(db.Integer)
    user = db.relationship('User', backref='wishlist_user')
    bookshelf = db.relationship('Bookshelf', backref='bookshelf_wishlist')

    def __init__(self, user_id='', shelf_id='', bookId=''):
        self.user_id = user_id
        self.shelf_id = shelf_id
        self.bookId = bookId


# Rates (book)
class BookRateAssociation(db.Model):
    __tablename__ = 'bookRate'
    rate_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('contains.contains_id'))
    rating = db.Column(db.Integer)
    comment = db.Column(db.TEXT, nullable=True)
    user = db.relationship('User', backref='user_booksRate')
    books = db.relationship('ContainsAssociation', backref='bookRate')

    def __init__(self, user_id='', book_id='', rating='', comment=''):
        self.user_id = user_id
        self.book_id = book_id
        self.rating = rating
        self.comment = comment


class BookRateTotal(db.Model):
    __tablename__ = 'bookrateTotal'
    totalrate_id = db.Column(db.Integer, primary_key=True)
    bookRated = db.Column(db.Integer, db.ForeignKey('contains.contains_id'))
    numofRates = db.Column(db.Integer)
    totalRate = db.Column(db.Float, default=0)

    def __init__(self, bookRated='', numofRates='', totalRate=''):
        self.bookRated = bookRated
        self.numofRates = numofRates
        self.totalRate = totalRate


# Rates (user)
class UserRateAssociation(db.Model):
    __tablename__ = 'userRate'
    rate_id = db.Column(db.Integer, primary_key=True)
    user_idRater = db.Column(db.Integer, db.ForeignKey('user.id'))
    user_idRatee = db.Column(db.Integer, db.ForeignKey('user.id'))
    rating = db.Column(db.Integer)
    comment = db.Column(db.TEXT)

    def __init__(self, user_idRater='', user_idRatee='', rating='', comment=''):
        self.user_idRater = user_idRater
        self.user_idRatee = user_idRatee
        self.rating = rating
        self.comment = comment


class UserRateTotal(db.Model):
    __tablename__ = 'userRateTotal'
    user_totalrate_id = db.Column(db.Integer, primary_key=True)
    userRatee = db.Column(db.Integer, db.ForeignKey('user.id'))
    numOfRates = db.Column(db.Integer)
    totalRate = db.Column(db.Float)

    def __init__(self, userRatee='', totalRate='', numOfRates=''):
        self.userRatee = userRatee
        self.totalRate = totalRate
        self.numOfRates = numOfRates


# Comment (Book)--------------------------------
class BookCommentAssociation(db.Model):
    __tablename__ = 'bookComment'
    comment_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    bookshelf_id = db.Column(db.Integer, db.ForeignKey('contains.contains_id'))
    comment = db.Column(db.TEXT)
    date = db.Column(db.DateTime, default=datetime.datetime.today)
    user = db.relationship('User', backref='user_booksComment')
    books = db.relationship('ContainsAssociation', backref='bookComment')

    def __init__(self, user_id='', bookshelf_id='', comment=''):
        self.user_id = user_id
        self.bookshelf_id = bookshelf_id
        self.comment = comment


# Comment (User)
class UserCommentAssociation(db.Model):
    __tablename__ = 'userComment'
    comment_id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.datetime.today)
    user_idCommenter = db.Column(db.Integer, db.ForeignKey('user.id'))
    user_idCommentee = db.Column(db.Integer, db.ForeignKey('user.id'))
    comment = db.Column(db.TEXT)

    def __init__(self, user_idCommenter='', user_idCommentee='', comment=''):
        self.user_idCommenter = user_idCommenter
        self.user_idCommentee = user_idCommentee
        self.comment = comment

class Message(db.Model):
    __tablename__ = 'Message'
    message_id = db.Column(db.Integer, primary_key=True)
    inbox_id = db.Column(db.Integer, nullable=False)
    datetime = db.Column(db.DateTime, default=datetime.datetime.now)
    message_from = db.Column(db.Integer, nullable=False)
    message_to = db.Column(db.Integer, nullable=False)
    content = db.Column(db.String(280))

    def __init__(self, message_from='', message_to='', content='', inbox_id=''):
        self.inbox_id = inbox_id
        self.message_from = message_from
        self.message_to = message_to
        self.content = content

class Inbox(db.Model):
    __tablename__ = 'Inbox'
    inbox_id = db.Column(db.Integer, primary_key=True)
    user1 = db.Column(db.Integer, nullable=False)
    user2 = db.Column(db.Integer, nullable=False)

    def __init__(self, user1='', user2=''):
        self.user1 = user1
        self.user2 = user2


# class Message(db.Model):
#     __tablename__ = 'message'
#     message_id = db.Column(db.Integer, primary_key=True)
#     messageFrom = db.Column(db.Integer, db.ForeignKey('user.id'))
#     messageTo = db.Column(db.Integer, db.ForeignKey('user.id'))
#     content = db.Column(db.String(100))
#     messaging_message = db.relationship('MessageAssociation', backref='messaging')
#
#     def __init__(self, messageFrom='', messageTo='', content='' ):
#         self.messageFrom = messageFrom
#         self.messageTo = messageTo
#         self.content = content
#
# class MessageAssociation(db.Model):
#     __tablename__ = 'messaging'
#     message_id = db.Column(db.Integer, db.ForeignKey('message.message_id'), primary_key=True)
#     messageFrom = db.Column(db.Integer, db.ForeignKey('user.id'))
#     messageTo = db.Column(db.Integer, db.ForeignKey('user.id'))
#     content = db.Column(db.String(100), db.ForeignKey('message.content'))
#     date = db.Column(db.DATE, nullable=False)
#     user = db.relationship('User', backref='userMessage')
#     messaging = db.relationship('Message', backref='hasMessage')
#
#     def __init__(self, messageFrom='', messageTo='', content='', date='' ):
#         self.messageFrom = messageFrom
#         self.messageTo = messageTo
#         self.content = content
#         self.date = date


class ActLogs(db.Model):
    __tablename__ = 'actlogs'
    logs = db.Column(db.Integer, primary_key=True)
    current_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    other_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    type = db.Column(db.String)
    date = db.Column(db.DateTime, default=datetime.datetime.today)
    status = db.Column(db.Integer)
    bookid = db.Column(db.Integer, nullable=True)

    def __init__(self, current_user_id='', other_user_id='', status='', bookid='', type=''):
        self.current_user_id = current_user_id
        self.other_user_id = other_user_id
        self.status = status
        self.bookid = bookid
        self.type = type

class Notifications(db.Model):
    __tablename__ = 'notifications'
    logs = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    bookshelf_id = db.Column(db.Integer, db.ForeignKey('bookshelf.bookshelf_id'), nullable=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.book_id'), nullable=True)
    current_user = db.Column(db.Integer, db.ForeignKey('user.id'))
    date = db.Column(db.DateTime, default=datetime.datetime.today)
    last_open = db.Column(db.DateTime, nullable=True)
    type = db.Column(db.String)


    def __init__(self, user_id='', last_open='', current_user='', type='', bookshelf_id='', book_id=''):
        self.user_id = user_id
        self.current_user = current_user
        self.last_open = last_open
        self.type = type
        self.bookshelf_id = bookshelf_id
        self.book_id = book_id


class Followers(db.Model):
    __tablename__ = 'followers'
    follow_id = db.Column(db.Integer, primary_key=True)
    followed_username = db.Column(db.String, nullable=False)
    follower_username = db.Column(db.String, nullable=False)

    def __init__(self, follow_id='', followed_username='', follower_username=''):
        self.followed_username = followed_username
        self.follower_username = follower_username

class BookReview(db.Model):
    __tablename__ = 'bookReview'
    review_id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.TEXT)
    rating = db.Column(db.Integer)
    date = db.Column(db.DateTime, default=datetime.datetime.today)

    def __init__(self, book_id='', user_id='', comment='', rating=''):
        self.book_id = book_id
        self.user_id = user_id
        self.comment = comment
        self.rating = rating


class BookReview_RateTotal(db.Model):
    __tablename__ = 'bookReviewRateTotal'
    book_total_rate_id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, nullable=False)
    numOfRates = db.Column(db.Integer)
    totalRate = db.Column(db.Float)

    def __init__(self, book_id='', totalRate='', numOfRates=''):
        self.book_id = book_id
        self.totalRate = totalRate
        self.numOfRates = numOfRates

class Transactions(db.Model):
    __tablename__ = 'transactions'
    transaction_id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, nullable=False)
    owner_id = db.Column(db.Integer, nullable=False)
    borrower_id = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String)
    total = db.Column(db.Integer)
    date = db.Column(db.DateTime, default=datetime.datetime.today)

    def __init__(self, book_id, owner_id, borrower_id, total, type):
        self.book_id = book_id
        self.owner_id = owner_id
        self.borrower_id = borrower_id
        self.total = total
        self.type = type

class Images(db.Model):
    img_id = db.Column(db.Integer, primary_key=True)
    acc_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    img_type = db.Column(db.String(50))
    img = db.Column(db.String(500))

    def __init__(self,acc_id, img_type, img):
        self.acc_id = acc_id
        self.img_type = img_type
        self.img = img


db.create_all()
