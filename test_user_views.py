"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_views.py


import os
from unittest import TestCase

from models import Follows, db, connect_db, Message, User, Likes

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class UserViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        self.testuser.id = 1122

        self.user1=User.signup("user1","user1@test.com","password1",None)
        self.user2=User.signup("user2","user2@test.com","password2",None)
        self.user1.id = 1111
        self.user2.id = 2222

        db.session.commit()

    def tearDown(self):
        db.session.rollback()

    def test_list_users(self):
        with self.client as c:
            resp = c.get("/users")
            html = resp.get_data(as_text=True)

            self.assertIn("@testuser",html)
            self.assertIn("@user1",html)
            self.assertIn("@user2",html)

    def setup_followers(self):
        """testuser following user1"""
        f = Follows(user_being_followed_id=self.user1.id, user_following_id=self.testuser.id)
        db.session.add(f)
        db.session.commit()


    def test_user_add_follow(self):
        self.setup_followers()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            resp = c.post("/users/follow/2222", follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertIn("@user1",html)
            self.assertIn("@user2",html)

    def test_user_show_followers(self):
        self.setup_followers()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.user1.id    

            resp = c.get(f"/users/{self.user1.id}/followers")
            html = resp.get_data(as_text=True)
            self.assertIn("@testuser",html)
            self.assertNotIn("@user2",html)

    def test_user_stop_following(self):
        self.setup_followers()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/users/stop-following/1111", follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertNotIn("@user1",html)
            self.assertNotIn("@user2",html)

    def test_user_delete(self):
        self.user3=User.signup("user3","user3@test.com","password3",None)
        self.user3.id=3333
        self.assertTrue(User.query.get(3333))

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/users/delete", follow_redirects=True)
            self.assertIsNone(User.query.get(3333))

    def setup_likes(self):
        m = Message(text="testuser message", user_id=self.testuser.id)
        m1 = Message(id=999111, text="user1 message", user_id=self.user1.id)
        m2 = Message(id=999222, text="user1 message", user_id=self.user1.id)
        db.session.add_all([m,m1,m2])
        db.session.commit()

        like = Likes(user_id=self.testuser.id, message_id=999111)
        db.session.add(like)
        db.session.commit()

    def test_like_message(self):
        self.setup_likes()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            self.assertEqual(len(Likes.query.all()),1)

            #like message_id=999222
            resp = c.post("/users/add_like/999222", follow_redirects=True)
            self.assertEqual(len(Likes.query.all()),2)

            #unlike message_id=999222
            resp = c.post("/users/add_like/999222", follow_redirects=True)
            self.assertEqual(len(Likes.query.all()),1)

    def test_show_likes(self):
        self.setup_likes()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            resp = c.get(f"/users/{self.testuser.id}/likes")
            html = resp.get_data(as_text=True)
            self.assertIn("user1 message", html)
            self.assertNotIn("user2 message", html)




            