import datetime
from collections import defaultdict

from telethon import TelegramClient, sync

from plotly import tools
import plotly.offline as py
import plotly.graph_objs as go

#authentication / authorization constants
api_id   = #TODO
api_hash = #TODO

phone    = #TODO
username = #TODO

#other constants
chatTitleSubstring = #TODO

maxPosts = 1000 #keep this low while testing to not upset Telegram's servers

#create client and connect
client = TelegramClient(username, api_id, api_hash)
client.start()

#find the chat ID from a substring in the chat title
chatTitle    = None
targetChatId = None
for dialog in client.iter_dialogs():
    if chatTitleSubstring in dialog.title:
        chatTitle    = dialog.title
        targetChatId = dialog.id

if not targetChatId:
    raise ValueError('Could not find a chat with a name matching your substring')

#collect message counts by sender from the target channel
targetChatEntity = client.get_entity(targetChatId)
actualStartDate  = None
countByPoster    = defaultdict(int)
for message in client.iter_messages(targetChatEntity, limit=maxPosts):
    if not actualStartDate:
        actualStartDate = message.date
    if (message.sender.username):
        countByPoster[message.sender.username]   += 1
    elif (message.sender.first_name):
        countByPoster[message.sender.first_name] += 1
    elif (message.sender.last_name):
        countByPoster[message.sender.last_name]  += 1

#create a list of the message counts, ordered from largest to smallest
counts  = sorted(countByPoster.values(),reverse=True)
posters = sorted(countByPoster, key=countByPoster.__getitem__,reverse=True)

#find the cumulative total post numbers of the top n posters to the chat, then from that the associated frequencies
cumulativeCounts = []
for i in range(len(counts)):
    if i==0:
        cumulativeCounts.append(counts[i])
    else:
        cumulativeCounts.append(cumulativeCounts[i-1] + counts[i])

cumulativeFrequencies = []
for i in range(len(counts)):
    cumulativeFrequencies.append(cumulativeCounts[i] / cumulativeCounts[len(counts)-1] * 100)

#generate the bar graph for the top posters and a scatter plot for the cumulative post frequencies
cumulativeTitles = []
for i in range(len(cumulativeFrequencies)):
    cumulativeTitles.append(i+1)

cumulativeTrace = go.Scatter(
    x=[0,*cumulativeTitles],
    y=[0,*cumulativeFrequencies],
    mode='lines+markers'
);

topPostersTrace = go.Bar(
    x=posters,
    y=counts
);

#print plots to the page
title = 'Percent of Total Posts by Top N Posters in <b>' + chatTitle + '</b> (Last ' + str(cumulativeCounts[len(counts)-1]) + ' Posts)'
cumulativeTraceTitle = 'Cumulative Frequency of Posts by Top N Posters'
topPostersTraceTitle = 'Top Posters by Post Volume'

fig = tools.make_subplots(rows=2, cols=1, subplot_titles=[cumulativeTraceTitle,topPostersTraceTitle])
fig.append_trace(cumulativeTrace, 1, 1)
fig.append_trace(topPostersTrace, 2, 1)
fig['layout'].update(title=title,xaxis=dict(title='Number of Posters',zeroline=False),xaxis2=dict(type='category',dtick=1),yaxis=dict(title='Cumulative Frequency'),yaxis2=dict(title='Post Volume'),showlegend=False,titlefont={"size": 24})

py.plot(fig, auto_open=True)
