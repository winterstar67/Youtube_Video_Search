import pickle

with open("data/results/Youtube_transcription.pkl", "rb") as f:
    youtube_transcription_dict = pickle.load(f)

print(youtube_transcription_dict['https://www.youtube.com/watch?v=EWvNQjAaOHw'])