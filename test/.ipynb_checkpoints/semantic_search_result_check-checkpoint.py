import pickle

with open("data/results/semantic_search_results.pkl", "rb") as f:
    semantic_search_results = pickle.load(f)

print(semantic_search_results)