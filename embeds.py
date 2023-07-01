import discord

def message_embed(text):
  msgEmbed = discord.Embed(color=0xC40808, title='KiriBot', description=text)
  #msgEmbed.set_author(name="KiriBot", url=None, icon_url="https://cdn.discordapp.com/attachments/815405038506999820/1120507716343971920/pfp.png")
  return msgEmbed

def list_embed(title, description):
  msgEmbed = discord.Embed(color=0xC40808, title=title , description=description)
  return msgEmbed

def image_embed(name, text, image):
  msgEmbed = discord.Embed(color=0xC40808, title=name, description=text)
  msgEmbed.set_image(url=image)
  return msgEmbed
