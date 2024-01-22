import streamlit as st
import cv2
from deepface import DeepFace
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import threading
import time
import webbrowser
from dotenv import load_dotenv
import os

load_dotenv()
# Spotify API credentials
SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
SPOTIPY_REDIRECT_URI = os.getenv('SPOTIPY_REDIRECT_URI')

# Load the pre-trained model
faceCascade = cv2.CascadeClassifier('haarcascade_frontalface_alt2.xml')


def authenticate_spotify(scope='user-library-read user-read-playback-state user-modify-playback-state'):
    sp_oauth = SpotifyOAuth(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI, scope=scope)
    auth_url = sp_oauth.get_authorize_url()
    return auth_url, sp_oauth


def analyze_emotion(frame):
    faces = faceCascade.detectMultiScale(frame, 1.1, 4)

    for (x, y, w, h) in faces:
        face_roi = frame[y:y + h, x:x + w]

        if w > 50 and h > 50:
            face_rgb = cv2.cvtColor(face_roi, cv2.COLOR_BGR2RGB)
            results = DeepFace.analyze(face_rgb, actions=['emotion'], enforce_detection=False)
            emotion = results[0].get('dominant_emotion', 'Unknown')

            return emotion


def get_song_uri(emotion):
    if emotion == "happy":
        return "spotify:playlist:1dJuYPzBtzt9ITxrCOQz5w"
    elif emotion == "sad":
        return "spotify:playlist:05moXwvnhC8KpfHwg7QMGZ"
    elif emotion == "fear":
        return "spotify:playlist:1a9wA1BSGqNEXIQjyjSYIH"
    elif emotion == "angry":
        return "spotify:playlist:1a9wA1BSGqNEXIQjyjSYIH"
    else:
        return "spotify:playlist:4StaDREDlexWb3YmDlNhft"


def play_song(emotion, sp):
    try:
       
        uri = get_song_uri(emotion)

        # Print the URI for debugging
        print(f"Spotify URI for {emotion}: {uri}")

        # Check for active devices
        devices = sp.devices()
        if devices and devices.get('devices'):
            # Start playback on the user's active device
            if "playlist" in uri:
                # For playlists, use start_playback with context_uri
                sp.start_playback(context_uri=uri)
            else:
                # For individual songs, use start_playback with uris
                sp.start_playback(uris=[uri])

            st.success(f"Playing {emotion} { 'playlist' if 'playlist' in uri else 'song' } on Spotify.")
        else:
            st.warning("No active device found. Please open the Spotify app on your device.")
    except Exception as e:
        st.error(f"Error playing song: {str(e)}")


def is_song_playing(sp):
    try:
        # Get current playback information
        playback_info = sp.current_playback()

        # Check if a track is currently playing
        return playback_info is not None and playback_info['is_playing']
    except Exception as e:
        print(f"Error checking if song is playing: {str(e)}")
        return False


def emotion_and_music_thread(sp):
    try:
        # Initialize webcam
        video_capture = cv2.VideoCapture(0)

        if not video_capture.isOpened():
            st.error("Error: Unable to open camera.")
            return

        while True:
            ret, frame = video_capture.read()

            if not ret:
                st.error("Error: Failed to capture frame.")
                break

            
            emotion = analyze_emotion(frame)

            
            play_song(emotion, sp)
            wait_until_song_end(sp)

        video_capture.release()

    except Exception as e:
        st.error(f"An error occurred in the emotion_and_music_thread: {str(e)}")



def wait_until_song_end(sp):
    while True:
        # Your logic to check if the song is still playing
        if not is_song_playing(sp):
            break
        time.sleep(1)


def main():
    st.set_page_config(
        page_title="Luna - Dreamy Emotion Analysis & Spotify Music App",
        page_icon="🌙",
        layout="wide",
    )

    # Custom CSS for mesh gradient background
    mesh_gradient_css = """
        body {
            background: linear-gradient(45deg, #93a5cf, #e4efe9, #f0f5f5);
        }
    """

    st.markdown(
        f"""
        <style>
            {mesh_gradient_css}
            .stApp {{
                max-width: 1200px;
                margin: 0 auto;
            }}
            .stTitle {{
                font-size: 3em;
                color: #5e5e5e;
                text-shadow: 2px 2px 2px #c0c0c0;
            }}
            .stButton {{
                color: #a7ccd2;
                font-size: 1.2em;
                border-radius: 8px;
            }}
            .stButton:hover {{
                background-color: #c0e4ec;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("LUNA🌙")


    auth_url, sp_oauth = authenticate_spotify()
    

    

    if st.button("Connect to Spotify"):
        webbrowser.open(auth_url)
        

    query_params = st.experimental_get_query_params()
    if 'code' in query_params:
        code = query_params['code'][0]
        token_info = sp_oauth.get_access_token(code)
        access_token = token_info['access_token']
        refresh_token = token_info['refresh_token']

        # Create a new Spotify object with the obtained access token
        sp = spotipy.Spotify(auth=access_token)

        # Display connected user info
        user_info = sp.current_user()
        st.write(f"Connected to Spotify as: {user_info['display_name']}")


        update_interval = 1  # in seconds

        # Initialize webcam
        video_capture = cv2.VideoCapture(0)

        if not video_capture.isOpened():
            st.error("Error: Unable to open camera.")
            return

        # Flag to track whether a song is already playing
        song_playing = False

        while True:
            ret, frame = video_capture.read()

            if not ret:
                st.error("Error: Failed to capture frame.")
                break

            # If a song is not currently playing, detect emotion and start playback
            if not song_playing:
                emotion = analyze_emotion(frame)
                st.write(f"Detected Emotion: {emotion}")

                # Set up themed interface based on emotion
                if emotion == "happy":
                    st.success("😊 It looks like you're happy! Enjoy the positive vibes.")
                elif emotion == "sad":
                    st.error("😢 Feeling sad? Take a moment and reach out to someone.")
                elif emotion == "fear":
                    st.warning("😨 It seems like you're feeling fearful. Take a deep breath, you're safe.")
                elif emotion == "angry":
                    st.error("😡 Feeling angry? It's okay, let's find a way to channel that energy positively.")
                else:
                    st.info("😐 Emotion detection results: Neutral. Keep it balanced!")

                play_song(emotion, sp)
                song_playing = True  # Set the flag to indicate that a song is playing

            # Check if the current song has finished
            if not is_song_playing(sp):
                song_playing = False  # Reset the flag when the song is over

            time.sleep(update_interval)

        video_capture.release()

if __name__ == "__main__":
    main()

