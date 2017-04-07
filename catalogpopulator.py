from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from catalog_database import Base, ActivityCategory, ActivityItem, User

engine = create_engine('sqlite:///activitiescatalogwithuser.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Create dummy user
user1 = User(name="Robo Barista", email="tinnyTim@udacity.com",
             picture='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')
session.add(user1)
session.commit()

# Create categories
category1 = ActivityCategory(name='Family')
session.add(category1)
session.commit()

# Create items for category 1
item1 = ActivityItem(name='5Wits', description="""5 Wits adventures are cutting-edge, live-action entertainment venues that
                     immerse you in realistic, hands-on experiences. They are similar to escape rooms in that you must use
                     teamwork to solve puzzles and challenges, but 5 Wits adventures have higher quality environments,
                     special effects, and more compelling storytelling. 5 Wits puts you in the center of the action, making
                     you feel as if you are in a movie or video game.""", website='www.5-wits.com', category=category1, user=user1)
session.add(item1)
session.commit()

category2 = ActivityCategory(name='Date Night')
session.add(category2)
session.commit()

category3 = ActivityCategory(name='Weekend and Day Trips')
session.add(category3)
session.commit()

category4 = ActivityCategory(name='Spa and Wellness')
session.add(category4)
session.commit()

# Create items for category 2
item1 = ActivityItem(name='RaffaYoga - Urban Sweat', description="""We get it, you are busy.That's why our Old World offerings provide an
                     opportunity to unplug and disconnect from the stress-inducing pace of each day and provide a space to
                     calm and center oneself, detoxify, and truly relax. After a session at Urban Sweat, you'll be ready to meet the challenges
                     of each day ahead. We are also proud to be one ofthe greenest  facilities in Rhode Island, since we keep environmental
                     conservation, community and conscious living in mind.""", website='www.raffayoga.com/urbansweat/urban-sweat/', category=category4, user=user1)
session.add(item1)
session.commit()

category5 = ActivityCategory(name='Outdoors')
session.add(category5)
session.commit()

category6 = ActivityCategory(name='Everything Else')
session.add(category6)
session.commit()

print "done adding items!"
