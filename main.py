import discord
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
from pprint import pprint
import os

client = discord.Client()
vc = None

@client.event
async def on_ready():
    print("Welcome to Super Spoti-bot")

    channel = None
    for guild in client.guilds:
        print("GUILD: "+str(guild.id)+" "+str(guild.name))
        if guild.name == "Ilan's Discord Bot Test server":
            channel = guild.get_channel(1023706018078785556)
    global vc
    vc = await channel.connect()

    await channel.send("Welcome to superSpotify bot. If you don't know what you're doing, type '$help'.")
    print('Connected!')

poll_id = None
sp = None
curSongId = None
playlist = None
next_songs = None

async def update_display(cur_song):
    song_info = sp.current_playback()
    await cur_song.edit(content='Playing ' + str(song_info['album']))


@client.event
async def on_message(message):

    if message.author.bot:
        return

    msg = message.content
    if msg.startswith('$login'):
        scope = "user-read-playback-state,user-modify-playback-state"
        global sp

        try:
            sp = spotipy.Spotify(client_credentials_manager=SpotifyOAuth(scope=scope))

        except:
            await message.channel.send("Not spotify device linked to your account has been recently active.\n"
                                       "Please turn on any song.")
            return

        sp.volume(80)
        await message.channel.send('Login Successful!')

    elif msg.startswith('$vote'):
        global poll_id
        global next_songs
        next_songs = sp.recommendations(seed_tracks=[sp.current_playback()['item']['uri']], limit='4')['tracks']
        print(sp.current_playback()['item']['uri'])
        for song in next_songs:
            print(str(song) + ":")

        dis_msg = "Please vote on next song:"
        for i in range(0,4,1):
            dis_msg = dis_msg + "\n" + str(i+1) + ") " + next_songs[i]['name']\
                      + " by " + next_songs[i]['artists'][0]['name']

        poll = await message.channel.send(dis_msg)
        await poll.add_reaction('1️⃣')
        await poll.add_reaction('2️⃣')
        await poll.add_reaction('3️⃣')
        await poll.add_reaction('4️⃣')
        poll_id = poll.id

    elif msg.startswith('$test_result'):
        poll = discord.utils.get(client.cached_messages, id=poll_id)
        if poll is not None and poll.reactions is not None:
            # tally results and message highest tally
            winner = None
            max_cnt = 0
            for rxn in poll.reactions:
                if winner is None:
                    winner = rxn.emoji

                if rxn.count >= max_cnt:
                    winner = rxn.emoji
                    max_cnt = rxn.count

            await message.channel.send('Winner: '+str(winner)+' with '+str(max_cnt-1)+' votes.')

    elif msg.startswith('$play'):
        # TODO: Save the active song to your playlist (or make one as well if you don't have one for the bot)
        if not sp:
            await message.channel.send("Please login using $login before using the bot")
            return

        res = sp.devices()

        print("DEVICES:")
        pprint(res)

        if res == None:
            print("ERROR: Can't find device with recently active spotify. Go onto spotify and play then pause something and it will find it")

        #Handle album title
        if len(msg) <= 6:
            await message.channel.send("ERROR: Specify playlist name, e.g. $play My Songs")
            return

        playlists = sp.current_user_playlists()

        playlist_name = msg[6:len(msg)]

        global playlist
        for pl in playlists['items']:
            print(pl)
            if pl['name'] == playlist_name:
                playlist = pl

        if playlist is None:
            await message.channel.send("ERROR: Playlist "+playlist_name+" doesn't exist")
            return

        print("PLAYLIST PLAYING: "+playlist['name'])
        print("URI PLAYING: "+str(playlist['uri']))

        sp.start_playback(context_uri=playlist['uri'])
        #sp.start_playback(context_uri='spotify:playlist:4nQhwDDOkqPKZgO2y6J7Yn')
        #sp.start_playback(uris=['spotify:track:3ZE3wv8V3w2T2f7nOCjV0N'])

        # Change volume
        sp.volume(80)


        global curSongId
        # TODO: Only shows one artist- have it show multiple artists
        cur_song = await message.channel.send('Music Player:')
        curSongId = cur_song.id
        await cur_song.add_reaction('🔉')
        await cur_song.add_reaction('⏯')
        await cur_song.add_reaction('⏩')
        await cur_song.add_reaction('🔊')
        print("cur_song.id: "+str(cur_song.id))

    elif msg.startswith('$stop'):
        if not sp:
            await message.channel.send("Please login using $login before using the bot")
            return

        sp.pause_playback()
        sp = None;
        return

    elif msg.startswith('$help'):
        await message.channel.send("COMMANDS:")
        await message.channel.send("$login             - Authenticate. Must do this before using any other command.")
        await message.channel.send("$play [album name] - play one of your albums")
        await message.channel.send("$title             - get info on song")
        await message.channel.send("$vote              - get list of recommendations based on current song and pick one")
        await message.channel.send("$stop              - stop music player")
        return

    elif msg.startswith('$title'):
        # TODO: return title song - have it just show the playlist name
        song_info = sp.current_playback()
        await message.channel.send(content='Playing ' + str(song_info['item']['name']) + '\nby ' + str(
            song_info['item']['artists'][0]['name']))


        # TODO: Save the active song to your playlist (or make one as well if you don't have one for the bot)

@client.event
async def on_reaction_add(reaction, user):

    if user.id != client.user.id and poll_id == reaction.message.id:  # TODO: test the second condition of this line - wasn't here before
        poll = discord.utils.get(client.cached_messages, id=reaction.message.id)

        for rxn in poll.reactions:
            # got the below two lines from
            # https://stackoverflow.com/questions/70458812/discord-py-bot-limit-player-to-one-reaction-for-a-poll
            if user in await rxn.users().flatten() and not user.bot and str(rxn) != str(reaction.emoji):
                await poll.remove_reaction(rxn.emoji, user)
                print("not first react: " + str(rxn)+" "+str(reaction.emoji))
                return

            if rxn.count >= 2:
                print("Next song chosen")
                if reaction.emoji == '1️⃣':
                    print(next_songs[0]['uri'])
                    sp.start_playback(uris=[next_songs[0]['uri']])
                elif reaction.emoji == '2️⃣':
                    print(next_songs[1]['uri'])
                    sp.start_playback(uris=[next_songs[1]['uri']])
                elif reaction.emoji == '3️⃣':
                    print(next_songs[2]['uri'])
                    sp.start_playback(uris=[next_songs[2]['uri']])
                elif reaction.emoji == '4️⃣':
                    print(next_songs[3]['uri'])
                    sp.start_playback(uris=[next_songs[3]['uri']])

    elif user.id != client.user.id and curSongId == reaction.message.id:
        cur_song = discord.utils.get(client.cached_messages, id=reaction.message.id)

        for rxn in cur_song.reactions:
            # got the below line from
            # https://stackoverflow.com/questions/70458812/discord-py-bot-limit-player-to-one-reaction-for-a-poll
            if user in await rxn.users().flatten() and not user.bot:
                if rxn.emoji == '🔉':
                    res = sp.current_playback()
                    if res['is_playing']:
                        dev = res['device']
                        cur_vol = dev['volume_percent']
                        print(str(cur_vol) + "%")
                        if cur_vol <= 10:
                            sp.volume(0)
                        else:
                            sp.volume(cur_vol - 10)

                elif rxn.emoji == '⏯':
                    track = sp.current_user_playing_track()
                    if track['is_playing']:
                        sp.pause_playback()
                    else:
                        sp.start_playback()

                elif rxn.emoji == '⏩':
                    sp.next_track()

                elif rxn.emoji == '🔊':
                    res = sp.current_playback()
                    if res['is_playing']:
                        dev = res['device']
                        cur_vol = dev['volume_percent']
                        print(str(cur_vol)+"%")
                        if cur_vol >= 90:
                            sp.volume(100)
                        else:
                            sp.volume(cur_vol + 10)

                await cur_song.remove_reaction(rxn.emoji, user)


client.run(os.getenv('BOT_ID'))

# event planner: have people react to a message and notify / make a list of who repsonded and who didn't
#               send reminders, some time suggestion aspct to it
#               host it somewhere so others can use it


# - rather keep to spotipy bot - have it play songs to a voice channel is a server
#       the bot annouces possible next songs, users vote on which song to play next, and the one with
#       the most votes goes next
#
#       guess songs - keeps track of how long it takes each player to guess

# TODO:
#  Add songs to your own playlist (if you liked the song and want to write it down) (will have special playlist to add songs to from this bot)
# That's VOTE mode, also GUESS (guess the song, keeping track of points), ARTIST (plays only that artist)
# need play, pause, etc


# IS PLAYING? https://developer.spotify.com/documentation/web-api/reference/#/operations/get-the-users-currently-playing-track