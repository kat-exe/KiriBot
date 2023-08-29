# This code is based on the following example:
# https://discordpy.readthedocs.io/en/stable/quickstart.html#a-minimal-bot

import discord
from discord import app_commands
from discord.ext.commands import MissingPermissions
import os

from keep_alive import keep_alive

import database
import embeds

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

guild_id = 813303722301849630

tree = app_commands.CommandTree(client)

# --- events ---


@client.event
async def on_ready():
  await tree.sync(guild=discord.Object(id=guild_id))
  print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
  if message.author == client.user:
    return

  #if message.content.startswith('$hello'):
  #  await message.channel.send('Hello!')


# --- commands ---

# -- test command --


# a test command, does nothing but repeat whatever was sent
@tree.command(name="test",
              description="testing out commands",
              guild=discord.Object(id=guild_id))
async def first_command(interaction, caption: str):
  await interaction.response.send_message(embed=embeds.message_embed(caption))


# -- adding and approving characters --


# add character for submission
@tree.command(name="submit_character",
              description="submit a new character",
              guild=discord.Object(id=guild_id))
async def submit_character(interaction, charactername: str):
  charactername = charactername.lower().capitalize()
  result = database.add_character(charactername)
  if result:
    await interaction.response.send_message(embed=embeds.message_embed(
      f"{charactername} has been submitted for approval!"))
  else:
    await interaction.response.send_message(embed=embeds.message_embed(
      f"Could not submit {charactername} for approval: please check this character doesn't already exist."
    ))

  #output = database.return_character(charactername)
  #await interaction.response.send_message(f"{output}")


# list characters waiting approval
@tree.command(
  name="approve_characters",
  description="Approve or deny submitted characters",
  guild=discord.Object(id=guild_id),
)
@app_commands.checks.has_permissions(administrator=True)
async def approve_characters(interaction):

  # --- helper functions ---

  # Our check for the reaction - author
  def check(reaction, user):
    return user == interaction.user  # We check that only the authors reaction counts

  # --- actual code ---

  # initial message to start approval process
  embed = embeds.message_embed(
    "Approve or deny submitted characters by reacting with the corresponding emotes. \n\n✅: Get Started\n❎: Cancel"
  )

  await interaction.response.send_message(embed=embed)  # Message to react to

  # add reactions and return user choice
  # Loop through channel history and pull the message that matches (should be first)
  message: discord.Message
  async for message in interaction.channel.history():
    if not message.embeds:
      continue
    if message.embeds[0].title == embed.title and message.embeds[
        0].color == embed.color:
      msg = message
      break
  else:
    # something broke
    return

  await msg.add_reaction('✅')
  await msg.add_reaction('❎')

  reaction = await client.wait_for("reaction_add",
                                   check=check)  # Wait for a reaction

  if (str(reaction[0]) == '✅'):
    #await interaction.edit_original_response(embed=message_embed("Insert cool shit here."))

    # get characters for approval
    characters = database.get_for_approval('characters')

    # for each character, approve or deny them
    smthBroke = False
    for character in characters:
      # remove previous reaction
      await msg.remove_reaction(emoji='✅', member=interaction.user)
      await msg.remove_reaction(emoji='❎', member=interaction.user)

      # display the character
      embed = embeds.message_embed(f"{character[0]} \n\n✅: Approve\n❎: Deny")
      await interaction.edit_original_response(embed=embed)

      # check for approval
      reaction = await client.wait_for("reaction_add",
                                       check=check)  # Wait for a reaction

      if (str(reaction[0]) == '✅'):
        # approved
        result = database.accept_character(character[0])
        if (result == False):
          smthBroke = True
          await interaction.edit_original_response(
            embed=embeds.message_embed("Oops! Something went wrong."))
          break

      elif (str(reaction[0]) == '❎'):
        # denied
        result = database.deny_character(character[0])
        if (result == False):
          smthBroke = True
          await interaction.edit_original_response(
            embed=embeds.message_embed("Oops! Something went wrong."))
          break

      else:
        smthBroke = True
        await interaction.edit_original_response(
          embed=embeds.message_embed("Oh look... you broke him. Rude :/"))
        break

    #await interaction.edit_original_response(embed=message_embed(f"You reacted with: {reaction[0]}"))
    if (smthBroke == False):
      await interaction.edit_original_response(embed=embeds.message_embed(
        "There are no more characters left to approve."))

  elif (str(reaction[0]) == '❎'):
    await interaction.edit_original_response(
      embed=embeds.message_embed("Action cancelled."))
    #await interaction.edit_original_response(embed=message_embed(f"You reacted with: {reaction[0]}"))

  else:
    await interaction.edit_original_response(
      embed=embeds.message_embed(f"You reacted with: {reaction[0]}... why?"))


@approve_characters.error
async def approve_characters_error(interaction, error):
  # doesn't really work: doesnt break the code and technically makes it admin only sooo
  if isinstance(error, MissingPermissions):
    await interaction.response.send_message(embed=embeds.message_embed(
      "You don't have permissions to access this command."))


# -- display characters --


# display a list of characters to use in a /pls
@tree.command(name="list_characters",
              description="Gives a list of characters to display",
              guild=discord.Object(id=guild_id))
async def list_characters(interaction):
  # get list of characters
  characters = database.return_all()
  # add character to string
  list = ""
  checkfirst = 0
  for character in characters:
    if checkfirst == 0:
      list += f"- {character[1]}"
      checkfirst = 1
    else:
      list += f"\n- {character[1]}"

  await interaction.response.send_message(
    embed=embeds.list_embed("Available Characters", list))


# generate random attributes to display a character
@tree.command(name="pls",
              description="Get a random image of your character",
              guild=discord.Object(id=guild_id))
async def generate_character(interaction, charactername: str):
  charactername = charactername.lower().capitalize()
  phrase, image = database.generate_post(charactername)
  if (phrase == None or image == None):
    await interaction.response.send_message(embed=embeds.message_embed(
      "Oops! Something went wrong. Please check you've given a valid character name."
    ))
  else:
    await interaction.response.send_message(
      embed=embeds.image_embed(charactername, phrase[0][0], image[0][0]))


# -- submit and approve images --


# instructions for image submission
@tree.command(name="submit_image_help",
              description="Instructions for uploading an image",
              guild=discord.Object(id=guild_id))
async def submit_image_help(interaction):
  await interaction.response.send_message(embed=embeds.list_embed(
    "How to Submit an Image:",
    "1. Post the image you want to submit into the channel like you would normally.\n2. On PC, right click on the image. On mobile, hold down on the image.\n3. On PC, click 'Copy Link'. On mobile, Tap 'Copy Media Link'\n4. Type the command '/submit_image', include the name of the character you want to submit to in the 'charactername' field and paste the link you just copied into the 'imagelink' field*.\n\n*Alternatively, you can paste an image link from anywhere. However, you risk that image being deleted by the original poster."
  ))


# add image for submission
@tree.command(name="submit_image",
              description="Submit a new image for a character",
              guild=discord.Object(id=guild_id))
async def submit_image(interaction, charactername: str, imagelink: str):
  #await interaction.response.send_message(embed=embeds.image_embed(charactername, "test", imagelink))
  charactername = charactername.lower().capitalize()
  result = database.add_image(charactername, imagelink)
  if result:
    await interaction.response.send_message(
      embed=embeds.message_embed("Your image has been submitted for approval!")
    )
  else:
    await interaction.response.send_message(embed=embeds.message_embed(
      "Could not submit image for approval: please check all values are correct."
    ))


# list images waiting approval
@tree.command(
  name="approve_images",
  description="Approve or deny submitted images",
  guild=discord.Object(id=guild_id),
)
@app_commands.checks.has_permissions(administrator=True)
async def approve_images(interaction):

  # - helper functions -

  # Our check for the reaction - author
  def check(reaction, user):
    return user == interaction.user  # We check that only the authors reaction counts

  # - actual code -

  # initial message to start approval process
  embed = embeds.message_embed(
    "Approve or deny submitted images by reacting with the corresponding emotes.\n\n✅: Get Started\n❎: Cancel"
  )

  await interaction.response.send_message(embed=embed)  # Message to react to

  # add reactions and return user choice
  # Loop through channel history and pull the message that matches (should be first)
  message: discord.Message
  async for message in interaction.channel.history():
    if not message.embeds:
      continue
    if message.embeds[0].title == embed.title and message.embeds[
        0].color == embed.color:
      msg = message
      break
  else:
    # something broke
    return

  await msg.add_reaction('✅')
  await msg.add_reaction('❎')

  reaction = await client.wait_for("reaction_add",
                                   check=check)  # Wait for a reaction

  if (str(reaction[0]) == '✅'):
    #await interaction.edit_original_response(embed=embeds.message_embed("Insert cool shit here."))

    # get images for approval
    images = database.get_for_approval('images')
    #await interaction.edit_original_response(embed=embeds.message_embed(images))

    # for each character, approve or deny them
    smthBroke = False
    for image in images:
      # remove previous reaction
      await msg.remove_reaction(emoji='✅', member=interaction.user)
      await msg.remove_reaction(emoji='❎', member=interaction.user)

      # display the image
      name = database.id_return_character(image[1])
      try:
        embed = embeds.image_embed(f"{name[0][1]}", "✅: Approve\n❎: Deny",
                                   f"{image[0]}")
        await interaction.edit_original_response(embed=embed)
      except:
        embed = embeds.message_embed("Something went wrong here.")
        await interaction.edit_original_response(embed=embed)

      # check for approval
      reaction = await client.wait_for("reaction_add",
                                       check=check)  # Wait for a reaction

      if (str(reaction[0]) == '✅'):
        # approved
        result = database.accept_image(image[0])
        if (result == False):
          smthBroke = True
          await interaction.edit_original_response(
            embed=embeds.message_embed("Oops! Something went wrong."))
          break

      elif (str(reaction[0]) == '❎'):
        # denied
        result = database.deny_image(image[0])
        if (result == False):
          smthBroke = True
          await interaction.edit_original_response(
            embed=embeds.message_embed("Oops! Something went wrong."))
          break

      else:
        smthBroke = True
        await interaction.edit_original_response(
          embed=embeds.message_embed("Oh look... you broke him. Rude :/"))
        break

    #await interaction.edit_original_response(embed=message_embed(f"You reacted with: {reaction[0]}"))
    if (smthBroke == False):
      await interaction.edit_original_response(
        embed=embeds.message_embed("There are no more images left to approve.")
      )

  elif (str(reaction[0]) == '❎'):
    await interaction.edit_original_response(
      embed=embeds.message_embed("Action cancelled."))
    #await interaction.edit_original_response(embed=message_embed(f"You reacted with: {reaction[0]}"))

  else:
    await interaction.edit_original_response(
      embed=embeds.message_embed(f"You reacted with: {reaction[0]}... why?"))


@approve_images.error
async def approve_images_error(interaction, error):
  # doesn't really work: doesnt break the code and technically makes it admin only sooo
  if isinstance(error, MissingPermissions):
    await interaction.response.send_message(embed=embeds.message_embed(
      "You don't have permissions to access this command."))


# -- submit and approve phrases --


# add phrase for submission
@tree.command(name="submit_phrase",
              description="Submit a new image for a character",
              guild=discord.Object(id=guild_id))
async def submit_phrase(interaction, charactername: str, phrase: str):
  #await interaction.response.send_message(embed=embeds.image_embed(charactername, "test", imagelink))
  result = database.add_phrase(charactername, phrase)
  if result:
    await interaction.response.send_message(embed=embeds.message_embed(
      "Your phrase has been submitted for approval!"))
  else:
    await interaction.response.send_message(embed=embeds.message_embed(
      "Could not submit phrase for approval: please check all values are correct."
    ))


# list images waiting approval
@tree.command(
  name="approve_phrases",
  description="Approve or deny submitted phrases",
  guild=discord.Object(id=guild_id),
)
@app_commands.checks.has_permissions(administrator=True)
async def approve_phrases(interaction):

  # --- helper functions ---

  # Our check for the reaction - author
  def check(reaction, user):
    return user == interaction.user  # We check that only the authors reaction counts

  # --- actual code ---

  # initial message to start approval process
  embed = embeds.message_embed(
    "Approve or deny submitted phrases and quotes by reacting with the corresponding emotes.\n\n✅: Get Started\n❎: Cancel"
  )

  await interaction.response.send_message(embed=embed)  # Message to react to

  # add reactions and return user choice
  # Loop through channel history and pull the message that matches (should be first)
  message: discord.Message
  async for message in interaction.channel.history():
    if not message.embeds:
      continue
    if message.embeds[0].title == embed.title and message.embeds[
        0].color == embed.color:
      msg = message
      break
  else:
    # something broke
    return

  await msg.add_reaction('✅')
  await msg.add_reaction('❎')

  reaction = await client.wait_for("reaction_add",
                                   check=check)  # Wait for a reaction

  if (str(reaction[0]) == '✅'):
    #await interaction.edit_original_response(embed=embeds.message_embed("Insert cool shit here."))

    # get images for approval
    phrases = database.get_for_approval('phrases')
    #await interaction.edit_original_response(embed=embeds.message_embed(images))

    # for each character, approve or deny them
    smthBroke = False
    for phrase in phrases:
      # remove previous reaction
      await msg.remove_reaction(emoji='✅', member=interaction.user)
      await msg.remove_reaction(emoji='❎', member=interaction.user)

      # display the image
      name = database.id_return_character(phrase[1])
      embed = embeds.list_embed(f"{name[0][1]}",
                                f"{phrase[0]}\n\n✅: Approve\n❎: Deny")
      await interaction.edit_original_response(embed=embed)

      # check for approval
      reaction = await client.wait_for("reaction_add",
                                       check=check)  # Wait for a reaction

      if (str(reaction[0]) == '✅'):
        # approved
        result = database.accept_phrase(phrase[0])
        if (result == False):
          smthBroke = True
          await interaction.edit_original_response(
            embed=embeds.message_embed("Oops! Something went wrong."))
          break

      elif (str(reaction[0]) == '❎'):
        # denied
        result = database.deny_phrase(phrase[0])
        if (result == False):
          smthBroke = True
          await interaction.edit_original_response(
            embed=embeds.message_embed("Oops! Something went wrong."))
          break

      else:
        smthBroke = True
        await interaction.edit_original_response(
          embed=embeds.message_embed("Oh look... you broke him. Rude :/"))
        break

    #await interaction.edit_original_response(embed=message_embed(f"You reacted with: {reaction[0]}"))
    if (smthBroke == False):
      await interaction.edit_original_response(embed=embeds.message_embed(
        "There are no more phrases or quotes left to approve."))

  elif (str(reaction[0]) == '❎'):
    await interaction.edit_original_response(
      embed=embeds.message_embed("Action cancelled."))
    #await interaction.edit_original_response(embed=message_embed(f"You reacted with: {reaction[0]}"))

  else:
    await interaction.edit_original_response(
      embed=embeds.message_embed(f"You reacted with: {reaction[0]}... why?"))


@approve_phrases.error
async def approve_phrases_error(interaction, error):
  # doesn't really work: doesnt break the code and technically makes it admin only sooo
  if isinstance(error, MissingPermissions):
    await interaction.response.send_message(embed=embeds.message_embed(
      "You don't have permissions to access this command."))


# -- edit and delete --


# list images waiting approval
@tree.command(
  name="delete_images",
  description="Delete images",
  guild=discord.Object(id=guild_id),
)
@app_commands.checks.has_permissions(administrator=True)
async def approve_images(interaction, charactername: str):
  # ensure charactername is accepted no matter capitalisation
  charactername = charactername.lower().capitalize()

  # - helper functions -

  # Our check for the reaction - author
  def check(reaction, user):
    return user == interaction.user  # We check that only the authors reaction counts

  # - actual code -

  # initial message to start approval process
  embed = embeds.message_embed(
    "Delete images by reacting with the corresponding emotes.\n\n✅: Get Started\n❎: Cancel"
  )

  await interaction.response.send_message(embed=embed)  # Message to react to

  # add reactions and return user choice
  # Loop through channel history and pull the message that matches (should be first)
  message: discord.Message
  async for message in interaction.channel.history():
    if not message.embeds:
      continue
    if message.embeds[0].title == embed.title and message.embeds[
        0].color == embed.color:
      msg = message
      break
  else:
    # something broke
    return

  await msg.add_reaction('✅')
  await msg.add_reaction('❎')

  reaction = await client.wait_for("reaction_add",
                                   check=check)  # Wait for a reaction

  await msg.add_reaction('❌')
  if (str(reaction[0]) == '✅'):
    #await interaction.edit_original_response(embed=embeds.message_embed("Insert cool shit here."))

    # get images for approval
    images = database.get_character_images(charactername)
    #await interaction.edit_original_response(embed=embeds.message_embed(images))

    # for each character, approve or deny them
    smthBroke = False
    for image in images:
      # remove previous reaction
      await msg.remove_reaction(emoji='✅', member=interaction.user)
      await msg.remove_reaction(emoji='❎', member=interaction.user)
      await msg.remove_reaction(emoji='❌', member=interaction.user)

      # display the image
      #name = database.id_return_character(image[1])
      try:
        embed = embeds.image_embed(f"{charactername}",
                                   "✅: Delete\n❎: Keep\n❌: Exit",
                                   f"{image[0]}")
        await interaction.edit_original_response(embed=embed)
      except:
        embed = embeds.message_embed("Something went wrong here.")
        await interaction.edit_original_response(embed=embed)

      # check for approval
      reaction = await client.wait_for("reaction_add",
                                       check=check)  # Wait for a reaction

      if (str(reaction[0]) == '✅'):
        # delete
        result = database.deny_image(image[0])
        if (result == False):
          smthBroke = True
          await interaction.edit_original_response(
            embed=embeds.message_embed("Oops! Something went wrong."))
          break

      elif (str(reaction[0]) == '❎'):
        # keep
        pass

      elif (str(reaction[0]) == '❌'):
        # exit
        await interaction.edit_original_response(
          embed=embeds.message_embed("Action cancelled."))
        break

      else:
        smthBroke = True
        await interaction.edit_original_response(
          embed=embeds.message_embed("Oh look... you broke him. Rude :/"))
        break

    #await interaction.edit_original_response(embed=message_embed(f"You reacted with: {reaction[0]}"))
    if (smthBroke == False):
      await interaction.edit_original_response(
        embed=embeds.message_embed("That's all.")
      )

  elif (str(reaction[0]) == '❎'):
    await interaction.edit_original_response(
      embed=embeds.message_embed("Action cancelled."))
    #await interaction.edit_original_response(embed=message_embed(f"You reacted with: {reaction[0]}"))

  else:
    await interaction.edit_original_response(
      embed=embeds.message_embed(f"You reacted with: {reaction[0]}... why?"))



# --- run bot ---

try:
  keep_alive()
  client.run(os.getenv("TOKEN"))
except discord.HTTPException as e:
  if e.status == 429:
    print(
      "The Discord servers denied the connection for making too many requests")
    print(
      "Get help from https://stackoverflow.com/questions/66724687/in-discord-py-how-to-solve-the-error-for-toomanyrequests"
    )
  else:
    raise e
