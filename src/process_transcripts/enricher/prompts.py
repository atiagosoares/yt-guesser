BasePrompt = '''
Get an audio transcription as an input. Split and merge the words of the transcription into groups of sentences that convey complete thoughts.
- The resulting groups of sentences must be between ten and fifty works long
- I reiterate: The resulting groups of sentences must be between ten and fifty words long
- Each resulting group of sentences should be annotated in the beginning by "- " and terminated by a newline
- Ignore newlines in the input
- Correct punctuation and capitalization.
- Correct words that  likely transcription mistakes
- Don't correct grammar errors.
- Don't summarize the transcription
- Don't output anything besides  the requested output

user:
hello guys and gals me moodahar and
today we're looking at a brand new
YouTube scam boys it just dropped let's
get started this one uses AI now before
we begin this video is not necessarily
just for you it's for your favorite
content creators all right I'm not
naming names specifically but today's
video goes out to a few of the content
creators again not naming names that
decide to hit me up every time they
click a link hey Buddha what's what's
gonna happen I clicked on the Shady link
and of course guys if that's all you
tell me anything could happen okay all
right you could provide nuclear launch
codes to like another country for all I
know I don't I can't answer that usually
when I get to asking where what link you
clicked on usually it ends up being
something adult oriented but the best
best thing that I've ever heard is mood

assistant:
- Hello guys and gals. Me Mutahar, and today we're looking at a brand new YouTube scam. Boys it just dropped, let's get started, this one uses AI!
- Now, before we begin this video is not necessarily just for you it's for your favorite content creators, all right.
- I'm not naming names specifically, but today's video goes out to a few of the content creators, again, not naming names, that decide to hit me up every time they click a link.
- "Hey Muta,  what's gonna happen?  I clicked on the Shady link!"
- And of course, guys, if that's all you tell me, anything could happen, okay. All right? You could provide nuclear launch codes to like another country for all I know.
- I don't... I can't answer that. Usually, when I get to asking where, what link you clicked on, usually it ends up being something adult oriented.
- But the best best thing that I've ever heard is: "Muta..." [INCOMPLETE]

user:

'''