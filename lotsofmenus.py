from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, Genre, Movie, User

engine = create_engine('sqlite:///moviebaseusers.db')

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

session = DBSession()

# Create dummy user
User1 = User(name="Aman Motwani", email="aman7878@gamil.com",
             picture='http://mdb.ibcdn.com/528e99487ff811e6bca5463f06fd5b40.jfif')
session.add(User1)
session.commit()


genre1 = Genre(user_id=1, name = "Action")
session.add(genre1)
session.commit()

movie1 = Movie(user_id=1, name = "Action Jackson", description = "Story of two twins with lots of actions!!!", region = "Bollywood", genre = genre1)
session.add(movie1)
session.commit()

movie2 = Movie(user_id=1, name = "Transformers", description = "Story about Robots", region = "Hollywood", genre = genre1)
session.add(movie2)
session.commit()

movie3 = Movie(user_id=1, name = "Knight and Day", description = "Action Comedy starring Tom Cruise and Cameron Diaz", region = "Hollywood", genre = genre1)
session.add(movie3)
session.commit()

genre2 = Genre(user_id=1, name = "Romance")
session.add(genre2)
session.commit()

movie4 = Movie(user_id=1, name = "The Notebook", description = "Two Lovers", region = "Hollywood", genre = genre2)
session.add(movie4)
session.commit()

movie5 = Movie(user_id=1, name = "Devdas", description = "Set in 1800 about two star crossed lovers!!", region = "Bollywood", genre = genre2)
session.add(movie5)
session.commit()

genre3 = Genre(user_id=1, name = "Comedy")
session.add(genre3)
session.commit()

movie6 = Movie(user_id=1, name = "Golmaal", description = "Four friend story", region = "Bollywood", genre = genre3)
session.add(movie6)
session.commit()

print "Added Successfully!!"

