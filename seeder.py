from database_setup import Category, User, Item, Base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

engine = create_engine('sqlite:///itemcatalogwithusers.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
session = DBSession()

# Your database, seed it. :)
user1 = User(name = 'Anas', email = 'anas1419hashim@gmail.com')

soccer = Category(name = 'Soccer', user = user1)
session.add(soccer)
soccer_ball = Item(name = 'ball', description = 'No way to play soccer without it!',
                 category = soccer, user = user1)
session.add(soccer_ball)
soccer_boot = Item(description = '''\
                                Well, It's a safety thing
                                and gives some control.''',
                   name = 'boot', category = soccer, user = user1)
session.add(soccer_boot)
session.commit()

squash = Category(name = 'Squash')
session.add(squash)
squash_racket = Item(name = 'racket', description = 'must have a racket to play the good game!',
                 category = squash, user = user1)
session.add(squash_racket)
squash_court = Item(name = 'court', description = "It's where we play!",
                 category = squash, user = user1)
session.add(squash_court)
session.commit()

print "Items add successfully!"
