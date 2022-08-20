"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy import exc
from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.user1=User.signup("user1","user1@test.com","password1",None)
        self.user2=User.signup("user2","user2@test.com","password2",None)
        self.user1.id = 1111
        self.user2.id = 2222
        db.session.commit()


        self.client = app.test_client()

    def tearDown(self):
        db.session.rollback()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)
    

    def test_user_follows(self):
        self.user1.following.append(self.user2)
        db.session.commit()

        self.assertEqual(len(self.user1.following),1)
        self.assertEqual(len(self.user2.following),0)
        self.assertEqual(len(self.user1.followers),0)
        self.assertEqual(len(self.user2.followers),1)

        self.assertEqual(self.user2.followers[0].id, self.user1.id)
        self.assertEqual(self.user1.following[0].id, self.user2.id)

    def test_is_following(self):
        self.user1.following.append(self.user2)
        db.session.commit()

        self.assertTrue(self.user1.is_following(self.user2))
        self.assertFalse(self.user2.is_following(self.user1))

    def test_is_followed_by(self):
        self.user1.following.append(self.user2)
        db.session.commit()

        self.assertFalse(self.user1.is_followed_by(self.user2))
        self.assertTrue(self.user2.is_followed_by(self.user1))


    def test_signup(self):
        user1 = User.query.get(1111)
        self.assertIsNotNone(user1)
        self.assertEqual(user1.username, "user1")
        self.assertEqual(user1.email, "user1@test.com")
        self.assertNotEqual(user1.password, "password1")

    def test_invalid_username_signup(self):
        invalid_user = User.signup("user1","invalid_username@test.com","password",None)
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_email_signup(self):
        invalid_user = User.signup("user3","user1@test.com","password",None)
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_password_signup(self):
        with self.assertRaises(ValueError) as context:
            User.signup("user4", "user4@test.com", None, None)

    def test_valid_authentication(self):
        user = User.authenticate(self.user1.username, "password1")
        self.assertIsNotNone(user)
        self.assertEqual(user.email, self.user1.email)

    def test_invalid_username(self):
        user = User.authenticate("invaliduser", "password1")
        self.assertFalse(user)

    def test_invalid_password(self):
        user = User.authenticate(self.user1.username, "invalidpassword")
        self.assertFalse(user)

    

