import sqlite3
import random

# create database and connection
connection = sqlite3.connect("KiriBot")

# create tables
connection.execute(
  "CREATE TABLE IF NOT EXISTS characters (id INTEGER PRIMARY KEY, name STRING UNIQUE, approved INTEGER DEFAULT 0);"
)
connection.execute(
  "CREATE TABLE IF NOT EXISTS phrases (id INTEGER PRIMARY KEY, characterID INTEGER, phrase STRING, approved INTEGER DEFAULT 0, FOREIGN KEY(characterID) REFERENCES characters(id));"
)
#connection.execute(
#  "CREATE TABLE IF NOT EXISTS character_phrases (characterID INTEGER, phraseID INTEGER, FOREIGN KEY(characterID) REFERENCES characters(id), #FOREIGN KEY(phraseID) REFERENCES phrases(id));"
#)
connection.execute(
  "CREATE TABLE IF NOT EXISTS images (id INTEGER PRIMARY KEY, characterID INTEGER, link STRING, approved INTEGER DEFAULT 0, FOREIGN KEY(characterID) REFERENCES characters(id))"
)

connection.commit()

# get data


def add_character(character):
  try:
    connection.execute(
      f"INSERT INTO characters (name) VALUES ('{character}');")
    connection.commit()
  except:
    return False
  else:
    return True


def return_character(name):
  result = connection.execute(
    f"SELECT * FROM characters WHERE name = '{name}';")
  return result.fetchall()


def id_return_character(id):
  result = connection.execute(f"SELECT * FROM characters WHERE id = '{id}';")
  return result.fetchall()


def id_return_phrase(id):
  result = connection.execute(f"SELECT phrase FROM phrases WHERE id = '{id}';")
  return result.fetchall()


def id_return_image(id):
  result = connection.execute(f"SELECT link FROM images WHERE id = '{id}';")
  return result.fetchall()


def return_all():
  result = connection.execute("SELECT * FROM characters WHERE approved = 1;")
  return result.fetchall()


def get_for_approval(type):
  if type == "characters":
    result = connection.execute(
      "SELECT name FROM characters WHERE approved = 0;")
  elif type == "phrases":
    result = connection.execute(
      "SELECT phrase, characterID FROM phrases WHERE approved = 0;")
  elif type == "images":
    result = connection.execute(
      "SELECT link, characterID FROM images WHERE approved = 0;")
  else:
    return None
  return result.fetchall()


def get_character_images(charactername):
  charId = connection.execute(
    f"SELECT id FROM characters WHERE name = '{charactername}';")
  charId = charId.fetchone()
  result = connection.execute(
    f"SELECT link FROM images WHERE approved = 1 AND characterID = {charId[0]};")
  return result.fetchall()


def accept_character(name):
  try:
    connection.execute(
      f"UPDATE characters SET approved = 1 WHERE name = '{name}';")
    connection.commit()
  except:
    return False
  else:
    return True


def deny_character(name):
  try:
    connection.execute(f"DELETE FROM characters WHERE name = '{name}';")
    connection.commit()
  except:
    return False
  else:
    return True


def add_image(charactername, link):
  try:
    characterID = return_character(charactername)
    connection.execute(
      f"INSERT INTO images (characterID, link) VALUES ('{characterID[0][0]}', '{link}');"
    )
    connection.commit()
  except:
    return False
  else:
    return True


def accept_image(link):
  try:
    connection.execute(
      f"UPDATE images SET approved = 1 WHERE link = '{link}';")
    connection.commit()
  except:
    return False
  else:
    return True


def deny_image(link):
  try:
    connection.execute(f"DELETE FROM images WHERE link = '{link}';")
    connection.commit()
  except:
    return False
  else:
    return True


def add_phrase(charactername, phrase):
  try:
    characterID = return_character(charactername)
    connection.execute(
      f'INSERT INTO phrases (characterID, phrase) VALUES ("{characterID[0][0]}", "{phrase}");'
    )
    connection.commit()
  except:
    return False
  else:
    return True


def accept_phrase(phrase):
  try:
    connection.execute(
      f'UPDATE phrases SET approved = 1 WHERE phrase = "{phrase}";')
    connection.commit()
  except:
    return False
  else:
    return True


def deny_phrase(phrase):
  try:
    connection.execute(f'DELETE FROM phrases WHERE phrase = "{phrase}";')
    connection.commit()
  except:
    return False
  else:
    return True


def generate_post(character):
  try:
    # get id of character
    characterInfo = return_character(character)
    characterID = characterInfo[0][0]

    # counts for randint
    imageIDs = connection.execute(
      f"SELECT id FROM images WHERE (approved = 1 AND characterID = {characterID});"
    )
    imageIDs = imageIDs.fetchall()
    phraseIDs = connection.execute(
      f"SELECT id FROM phrases WHERE (approved = 1 AND characterID = {characterID});"
    )
    phraseIDs = phraseIDs.fetchall()

    # get random images and phrases
    randomImage = random.randint(0, len(imageIDs) - 1)
    randomPhrase = random.randint(0, len(phraseIDs) - 1)

    imageID = imageIDs[randomImage][0]
    phraseID = phraseIDs[randomPhrase][0]

    image = id_return_image(imageID)
    phrase = id_return_phrase(phraseID)

    #return f"imageIDs: {imageIDs}, randImage: {randomImage}, image: {imageID}"
    return phrase, image
  except:
    return None, None
