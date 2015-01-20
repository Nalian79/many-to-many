from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, Text
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Table

import logging
log = logging.getLogger(__name__)

################################################################################
# set up logging - see: https://docs.python.org/2/howto/logging.html

# when we get to using Flask, this will all be done for us
import logging
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
log.addHandler(console_handler)


################################################################################
# Domain Model

Base = declarative_base()
log.info("base class generated: {}".format(Base) )

# define our domain model
class Species(Base):
    """
    domain model class for a Species
    """
    __tablename__ = 'species'

    # database fields
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    breeds = relationship('Breed', backref="species")

    # methods
    def __repr__(self):
        return self.name


class Breed(Base):
    """
    domain model class for a Breed
    has a with many-to-one relationship Species
    """
    __tablename__ = 'breed'

    # database fields
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    species_id = Column(Integer, ForeignKey('species.id'), nullable=False )
    pets = relationship('Pet', backref="breed")
    # methods
    def __repr__(self):
        return "{}: {}".format(self.name, self.species)


#########################################################
#   Add your code for BreedTraits object here			#
#########################################################

breed_trait_table = Table('breed_breedtrait', Base.metadata,
    Column('breed_id', Integer, ForeignKey('breed.id'), nullable=False),
    Column('trait_id', Integer, ForeignKey('trait.id'), nullable=False)
)

class Trait(Base):
    """
    domain model class for Breed traits.  Many-to-many relationship
    with breeds.
    """
    __tablename__ = 'trait'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    breeds = relationship('Breed', secondary=breed_trait_table, backref="traits")

    def __repr__(self):
        return "{}".format(self.name)


class Shelter(Base):
    __tablename__ = 'shelter'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    website = Column(Text)
    pets = relationship('Pet', backref="shelter")

    def __repr__(self):
        return "Shelter: {}".format(self.name)


# our many-to-many association table, in our domain model *before* Pet class 
pet_person_table = Table('pet_person', Base.metadata,
    Column('pet_id', Integer, ForeignKey('pet.id'), nullable=False),
    Column('person_id', Integer, ForeignKey('person.id'), nullable=False)
)


class Pet(Base):
    """
    domain model class for a Pet, which has a many-to-one relation with Shelter, 
    a many-to-one relation with breed, and a many-to-many relation with person
    """
    __tablename__ = 'pet'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    age = Column(Integer)
    adopted = Column(Boolean)
    breed_id = Column(Integer, ForeignKey('breed.id'), nullable=False )
    shelter_id = Column(Integer, ForeignKey('shelter.id') )

    # foreign key to self to set up parent/child relationship..
    parent_id = Column(Integer, ForeignKey(id), nullable=True)
    parent = relationship('Pet', remote_side=id, backref="children")

    # no foreign key here, it's in the many-to-many table
    # mapped relationship, pet_person_table must already be in scope!
    people = relationship('Person', secondary=pet_person_table,
                          backref='pets')

    def __repr__(self):
        return "Pet:{}".format(self.name)

class Person(Base):
    __tablename__ = 'person'
    id = Column(Integer, primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    age = Column(Integer)
    _phone = Column(String)

    # mapped relationship 'pets' from backref on Pet class, so we don't
    # need to add it here.

    @property
    def phone(self):
        """return phone number formatted with hyphens"""
        # get the phone number from the database, mapped to private self._phone
        num = self._phone
        # return a formatted version using hyphens
        return "%s-%s-%s" % (num[0:3], num[3:6], num[6:10])

    # phone number writing property, writing to public Person.phone calls this
    @phone.setter
    def phone(self, value):
        """store only numeric digits, raise exception on wrong number length"""
        # remove any hyphens
        number = value.replace('-', '')
        # remove any spaces
        number = number.replace(' ', '')
        # check length, raise exception if bad
        if len(number) != 10:
            raise Exception("Phone number not 10 digits long")
        else:
            # write the value to the property that automatically goes to DB
            self._phone = number

    @property
    def full_name(self):
        return self.first_name + ' ' +self.last_name

    @property
    def pets(self):
        return [ assoc.pet for assoc in self.pet_assocs ]

    def has_pet(self, pet):
        for assoc in self.pet_assocs:
            if assoc.pet == pet:
                return assoc.years
        return None

    def __repr__(self):
        return "Person: {} ".format(self.full_name) # self.first_name, self.last_name, self.id)

class PetPersonAssociation(Base):
    __tablename__ = 'pet_person_association'

    # Here we use __table_args__ along with UniqueConstraint
    # to ensure that the combo of pet_id and person_id is unique
    # You can search for these terms in the SQLAlchemy docs.
    __table_args__ = (
            UniqueConstraint('pet_id', 'person_id', name='person_pet_uniqueness_constraint'),
        )
    id = Column(Integer, primary_key=True)

    # the combination of the two columns below must be unique, because above
    # we have defined the UniqueConstraint above. We require both fields
    # below.
    pet_id = Column(Integer, ForeignKey('pet.id'), nullable=False)
    person_id = Column(Integer, ForeignKey('person.id'), nullable=False)

    # an integer for capturing years
    years = Column(Integer)

    person = relationship('Person', backref=backref('pet_associations') )
    pet = relationship('Pet', backref=backref('person_associations'))

    # note that we added a .full_name property to our person class
    # which concatenates first and last name.

    def __repr__(self):
        return "PetPersonAssociation( {} : {} )".format(self.pet.name,
            self.person.full_name)


class PetNicknames(Base):
    """
    Store the nicknames people have given their pets.
    """
    __tablename__ = 'nicknames'

    id = Column(Integer, primary_key=True)
    pet_id = Column(Integer, ForeignKey('pet.id'), nullable=False)
    person_id = Column(Integer, ForeignKey('person.id'), nullable=False)

    nickname = Column(Text)

    person = relationship('Person', backref=backref('pet_nickname'))
    pet = relationship('Pet', backref=backref('nickname'))

#    @property
    def __repr__(self):
        return "{}".format(self.nickname)


################################################################################
def init_db(engine):
    "initialize our database, drops and creates our tables"
    log.info("init_db() engine: {}".format(engine) )

    # drop all tables and recreate
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    log.info("  - tables dropped and created")


if __name__ == "__main__":
    log.info("main executing:")

    # create an engine
    engine = create_engine('sqlite:///:memory:')
    log.info("created engine: {}".format(engine) )

    # if we asked to init the db from the command line, do so
    if True:
        init_db(engine)

    # call the sessionmaker factory to make a Session class
    Session = sessionmaker(bind=engine)

    # get a local session for the this script
    db_session = Session()
    log.info("Session created: {}".format(db_session) )

    # create two people: Tom and Sue
    log.info("Creating person object for Tom")
    tom = Person(first_name="Tom",
                last_name="Smith",
                age=52,
                phone = '555-555-5555')

    log.info("Creating person object for Sue")
    sue = Person(first_name="Sue",
                last_name="Johson",
                age=54,
                phone = '555 243 9988')


    # create two animals, and in process, new species, with two breeds.
    # Note how we only explicitly commit spot and goldie below, but by doing so
    # we also save our new people, breeds, and species.

    log.info("Creating pet object for Spot, who is a Dalmatian dog")
    spot = Pet(name = "Spot",
                age = 2,
                adopted = True,
                breed = Breed(name="Dalmatian", species=Species(name="Dog")),
                people = [tom, sue]
                )

    # now we set Spot's breed to a variable because we don't want to create
    # a duplicate record for Dog in the species table, which is what would
    # happen if we created Dog on the fly again when instantiating Goldie
    dog = spot.breed.species

    log.info("Creating pet object for Goldie, who is a Golden Retriever dog")
    goldie = Pet(name="Goldie",
                age=9,
                adopted = False,
                shelter = Shelter(name="Happy Animal Place"),
                breed = Breed(name="Golden Retriever", species=dog)
                )

    log.info("Adding Goldie and Spot to session and committing changes to DB")
    db_session.add_all([spot, goldie])
    db_session.commit()

    assert tom in spot.people
    spot.people.remove(tom)
    assert spot not in tom.pets

    #################################################
    #  Now it's up to you to complete this script ! #
    #################################################

    # Add your code that adds breed traits and links breeds with traits
    # here.

    # Creating breed traits
    log.info("Adding breed traits to the DB.")
    fast = Trait(name="Fast")
    smart = Trait(name="Smart")
    drools = Trait(name="Drools")
    dog_friendly = Trait(name="Dog Friendly")

    # Committing traits..
    db_session.add_all([fast, smart, drools, dog_friendly])
    db_session.commit()

    num_traits = db_session.query(Trait).count()

    log.info("There are now {} dog breed traits available".format(num_traits))

    log.info("Traits available are {}, {}, {}, and {}.".format(
            fast.name, smart.name, drools.name, dog_friendly.name))

    # Attributing breed traits to breeds
    fast.breeds.append(goldie.breed)
    fast.breeds.append(spot.breed)
    smart.breeds.append(spot.breed)
    dog_friendly.breeds.append(spot.breed)

    log.info("The breeds that are {} are: {}.".format(fast.name, fast.breeds))
    log.info("The breeds that are {} are: {}".format(smart.name, smart.breeds))
    log.info("The breeds that are {} are: {}".format(dog_friendly.name,
                                                     dog_friendly.breeds))
    db_session.commit()

    #################################################
    # Adding more people
    gary = Person(first_name="Gary",
                  last_name="Jones",
                  age=52,
                  phone = '555-123-5555')

    karim = Person(first_name="Karim",
                   last_name="",
                   age=32,
                   phone = '555-123-4545')
    # Adding more pets
    duke = Pet(name="Duke",
               age=5,
               adopted = True,
               shelter = Shelter(name="Happy Animal Place"),
               breed = Breed(name="Labrador Retriever", species=dog),
               people = [gary]
               )

    sonya = Pet(name="Sonya",
                age=7,
                adopted = True,
                breed = Breed(name="Boxer", species=dog),
                people = [karim],
                )

    fast.breeds.append(duke.breed)
    dog_friendly.breeds.append(duke.breed)
    db_session.add_all([duke, sonya])
    db_session.commit()
    log.info("Created new breeds, all breeds are now: ")
    for name in db_session.query(Breed).all():
        print name

    print("Printing Duke's people: {}".format(duke.people))

    # Creating nicknames for the pets
    goofus = PetNicknames(nickname="Goofus",
                          pet_id=sonya.id,
                          person_id=karim.id)
    crazypants = PetNicknames(nickname="Crazypants",
                              pet_id=sonya.id,
                              person_id=karim.id)
    dukers = PetNicknames(nickname="Dukers",
                          pet_id=duke.id,
                          person_id=gary.id)

    db_session.add_all([goofus, crazypants, dukers])
    db_session.commit()
    log.info("{} has the nicknames: {}".format(sonya.name, sonya.nickname))
    log.info("{} has the nicknames: {}".format(duke.name, duke.nickname))

    # Creating children for pets we already have.
    baby_spot = Pet(name="Spot Jr.", parent=spot, adopted = False,
                    breed=spot.breed)

    db_session.add(baby_spot)
    db_session.commit()

#    import pdb
#    pdb.set_trace()

    #################################################

    db_session.close()
    log.info("all done!")

