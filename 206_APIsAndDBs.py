## SI 206 2017
## Project 3

## OBJECTIVE:
## In this assignment you will be creating database and loading data
## into database.  You will also be performing SQL queries on the data.
## You will be creating a database file: 206_APIsAndDBs.sqlite

## Your name: Daniella Raz

import unittest
import itertools
import collections
import tweepy
import twitter_info_copy
import json
import sqlite3


## Define a function called get_user_tweets that gets at least 20 Tweets
## from a specific Twitter user's timeline, and uses caching. The function
## should return a Python object representing the data that was retrieved
## from Twitter.

# Tweepy Authentication
consumer_key = twitter_info_copy.consumer_key
consumer_secret = twitter_info_copy.consumer_secret
access_token = twitter_info_copy.access_token
access_token_secret = twitter_info_copy.access_token_secret
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

# returning in JSON format
api = tweepy.API(auth, parser=tweepy.parsers.JSONParser())

# Caching
CACHE_FNAME = "206_APIsAndDBs_cache.json"

try:
    cache_file = open(CACHE_FNAME, 'r')
    cache_contents = cache_file.read()
    CACHE_DICTION = json.loads(cache_contents)
    cache_file.close()
except:
    CACHE_DICTION = {}

# Input: Takes in the search term from the invocation below
# Output: returns python object of all data retrieved
def get_user_tweets(search_term):
    if search_term in CACHE_DICTION:
        print('using cached data')
        twitter_results = CACHE_DICTION[search_term]
    else:
        print('retrieving data from internet')
        twitter_results = api.user_timeline(search_term)

        CACHE_DICTION[search_term] = twitter_results
        f = open(CACHE_FNAME, 'w')
        f.write(json.dumps(CACHE_DICTION))
        f.close()
    return twitter_results

umich_tweets = get_user_tweets("umich")


## Task 2 - Create database, load data into database
## umich username, and all of the data about users that are mentioned in the umich timeline.
## NOTE: For example, if the user with the "TedXUM" screen name is
## mentioned in the umich timeline, that Twitter user's info should be
## in the Users table, etc.

# creating database and cursor, creating Users table
# checking if user is already in table
# if not, adding along with rest of relevant info about user
conn = sqlite3.connect('206_APIsAndDBs.sqlite')
cur = conn.cursor()

cur.execute('DROP TABLE IF EXISTS Users')
cur.execute('CREATE TABLE Users (user_id TEXT PRIMARY KEY NOT NULL, screen_name TEXT NOT NULL, num_favs NUMBER NOT NULL, description TEXT NOT NULL)')

for x in umich_tweets:
    tup1 = x["user"]["id_str"],x["user"]["screen_name"],x["user"]["favourites_count"],x["user"]["description"]

    try:
        cur.execute('INSERT INTO Users (user_id, screen_name, num_favs, description) VALUES (?, ?, ?, ?)', tup1)
    except:
        continue

    for full_dict in umich_tweets:
        for d1 in full_dict['entities']['user_mentions']:

            user_info = api.get_user(d1["screen_name"])
            user_screen_name = user_info["screen_name"]
            user_fav_counts = user_info["favourites_count"]
            user_description = user_info["description"]
            user_id = d1["id_str"]
            mentioned_user = d1["screen_name"]

            tup2 = user_id, mentioned_user, user_fav_counts, user_description

            try:
                cur.execute('INSERT INTO Users (user_id, screen_name, num_favs, description) VALUES (?, ?, ?, ?)', tup2)
            except:
                continue

#creating Tweets table and inserting relevant information from umich_tweets object
cur.execute('DROP TABLE IF EXISTS Tweets')
cur.execute('CREATE TABLE Tweets (tweet_id TEXT PRIMARY KEY, text TEXT, user_posted TEXT, time_posted DATETIME, retweets INTEGER)')

for tw in umich_tweets:
    tup3 = tw["id_str"], tw["text"], tw["user"]["id_str"], tw["created_at"], tw["retweet_count"]
    cur.execute('INSERT INTO Tweets (tweet_id, text, user_posted, time_posted, retweets) VALUES (?, ?, ?, ?, ?)', tup3)

conn.commit()


## Task 3 - Making queries, saving data, fetching data

# Query to select all of records in the Users database.
users_info = cur.execute('SELECT * FROM Users')
users_info = users_info.fetchall()

# Query to select all of user screen names from database
# Saving resulting list of strings in the variable screen_names.
screen_names = cur.execute('SELECT screen_name FROM Users')
screen_names = [' '.join(item) for item in screen_names]

# Query to select all of the tweets (full rows of tweet information)
# that have been retweeted more than 10 times.
retweets = cur.execute('SELECT * From Tweets WHERE retweets > 10')
retweets = retweets.fetchall()

# Query to select all the descriptions of users who have favorited more than 500 tweets.
favorites = cur.execute('SELECT description From Users WHERE num_favs > 500')
favorites = [' '.join(item) for item in favorites]

# Query to get list of tuples with 2 elements in each tuple:
# the user screenname and the text of the tweet
joined_data = cur.execute('SELECT Tweets.text, Users.screen_name from Users join Tweets')
joined_data = joined_data.fetchall()

# Query to get a list of tuples with 2 elements in each tuple:
# the user screenname and the text of the tweet in descending order based on retweets
joined_data = cur.execute('SELECT Tweets.text, Users.screen_name from Users join Tweets ORDER BY Tweets.retweets')
joined_data = joined_data.fetchall()


conn.close()


## Tests ##
print("\n\nBELOW THIS LINE IS OUTPUT FROM TESTS:\n")

class Task1(unittest.TestCase):
	def test_umich_caching(self):
		fstr = open("206_APIsAndDBs_cache.json","r")
		data = fstr.read()
		fstr.close()
		self.assertTrue("umich" in data)
	def test_get_user_tweets(self):
		res = get_user_tweets("umsi")
		self.assertEqual(type(res),type(["hi",3]))
	def test_umich_tweets(self):
		self.assertEqual(type(umich_tweets),type([]))
	def test_umich_tweets2(self):
		self.assertEqual(type(umich_tweets[18]),type({"hi":3}))
	def test_umich_tweets_function(self):
		self.assertTrue(len(umich_tweets)>=20)

class Task2(unittest.TestCase):
	def test_tweets_1(self):
		conn = sqlite3.connect('206_APIsAndDBs.sqlite')
		cur = conn.cursor()
		cur.execute('SELECT * FROM Tweets');
		result = cur.fetchall()
		self.assertTrue(len(result)>=20, "Testing there are at least 20 records in the Tweets database")
		conn.close()
	def test_tweets_2(self):
		conn = sqlite3.connect('206_APIsAndDBs.sqlite')
		cur = conn.cursor()
		cur.execute('SELECT * FROM Tweets');
		result = cur.fetchall()
		self.assertTrue(len(result[1])==5,"Testing that there are 5 columns in the Tweets table")
		conn.close()
	def test_tweets_3(self):
		conn = sqlite3.connect('206_APIsAndDBs.sqlite')
		cur = conn.cursor()
		cur.execute('SELECT tweet_id FROM Tweets');
		result = cur.fetchall()
		self.assertTrue(result[0][0] != result[19][0], "Testing part of what's expected such that tweets are not being added over and over (tweet id is a primary key properly)...")
		if len(result) > 20:
			self.assertTrue(result[0][0] != result[20][0])
		conn.close()


	def test_users_1(self):
		conn = sqlite3.connect('206_APIsAndDBs.sqlite')
		cur = conn.cursor()
		cur.execute('SELECT * FROM Users');
		result = cur.fetchall()
		self.assertTrue(len(result)>=2,"Testing that there are at least 2 distinct users in the Users table")
		conn.close()
	def test_users_2(self):
		conn = sqlite3.connect('206_APIsAndDBs.sqlite')
		cur = conn.cursor()
		cur.execute('SELECT * FROM Users');
		result = cur.fetchall()
		self.assertTrue(len(result)<20,"Testing that there are fewer than 20 users in the users table -- effectively, that you haven't added duplicate users. If you got hundreds of tweets and are failing this, let's talk. Otherwise, careful that you are ensuring that your user id is a primary key!")
		conn.close()
	def test_users_3(self):
		conn = sqlite3.connect('206_APIsAndDBs.sqlite')
		cur = conn.cursor()
		cur.execute('SELECT * FROM Users');
		result = cur.fetchall()
		self.assertTrue(len(result[0])==4,"Testing that there are 4 columns in the Users database")
		conn.close()

class Task3(unittest.TestCase):
	def test_users_info(self):
		self.assertEqual(type(users_info),type([]),"testing that users_info contains a list")
	def test_users_info2(self):
		self.assertEqual(type(users_info[0]),type(("hi","bye")),"Testing that an element in the users_info list is a tuple")

	def test_track_names(self):
		self.assertEqual(type(screen_names),type([]),"Testing that screen_names is a list")
	def test_track_names2(self):
		self.assertEqual(type(screen_names[0]),type(""),"Testing that an element in screen_names list is a string")

	def test_more_rts(self):
		if len(retweets) >= 1:
			self.assertTrue(len(retweets[0])==5,"Testing that a tuple in retweets has 5 fields of info (one for each of the columns in the Tweet table)")
	def test_more_rts2(self):
		self.assertEqual(type(retweets),type([]),"Testing that retweets is a list")
	def test_more_rts3(self):
		if len(retweets) >= 1:
			self.assertTrue(retweets[1][-1]>10, "Testing that one of the retweet # values in the tweets is greater than 10")

	def test_descriptions_fxn(self):
		self.assertEqual(type(favorites),type([]),"Testing that favorites is a list")
	def test_descriptions_fxn2(self):
		self.assertEqual(type(favorites[0]),type(""),"Testing that at least one of the elements in the favorites list is a string, not a tuple or anything else")
	def test_joined_result(self):
		self.assertEqual(type(joined_data[0]),type(("hi","bye")),"Testing that an element in joined_result is a tuple")

if __name__ == "__main__":
	unittest.main(verbosity=2)
