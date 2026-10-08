import re

def video_id(url):
    m=re.search(r'(?:v=|youtu\.be/|shorts/)([A-Za-z0-9_-]{11})',url)
    return m.group(1) if m else None

def get_transcript(url):
    vid=video_id(url)
    if not vid: raise ValueError('Could not detect a valid YouTube video ID.')
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        raise RuntimeError('Install youtube-transcript-api from requirements.txt.')
    try:
        api=YouTubeTranscriptApi()
        result=api.fetch(vid)
        return ' '.join(x.text for x in result.snippets)
    except Exception:
        try:
            items=YouTubeTranscriptApi.get_transcript(vid)
            return ' '.join(x['text'] for x in items)
        except Exception as e:
            raise RuntimeError(f'Could not retrieve a transcript. Captions may be unavailable. {e}')
