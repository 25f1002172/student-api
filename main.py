
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Existing student API
df = pd.read_csv("TDS 2026 Sep GA0.csv")

@app.get("/api")
def get_students(class_: list[str] | None = Query(default=None, alias="class")):
    data = df
    if class_:
        data = data[data["class"].isin(class_)]
    return {"students": data.to_dict(orient="records")}


# Sentiment API
class SentimentRequest(BaseModel):
    sentences: list[str]


positive_words = {
    "love", "loved", "lovely", "great", "excellent", "amazing",
    "awesome", "good", "wonderful", "fantastic", "happy", "glad",
    "joy", "joyful", "delightful", "perfect", "best", "beautiful",
    "enjoy", "enjoyed", "like", "liked", "brilliant", "helpful",
    "success", "successful", "pleased", "excited", "incredible",
    "impressive", "recommend", "satisfied", "easy", "win", "winning"
}

negative_words = {
    "hate", "hated", "terrible", "awful", "horrible", "bad",
    "worst", "sad", "unhappy", "angry", "upset", "disappointed",
    "disappointing", "poor", "fail", "failed", "failure", "broken",
    "annoying", "annoyed", "boring", "painful", "ugly", "useless",
    "difficult", "problem", "problems", "wrong", "regret", "fear",
    "scared", "frustrated", "frustrating", "unfortunately",
    "dislike", "disliked", "never", "damaged", "loss", "lose",
    "losing", "sadly", "stressful", "stress", "worse", "threat"
}

positive_phrases = [
    "not bad", "not terrible", "not disappointed",
    "well done", "looking forward", "thank you",
    "works perfectly", "highly recommend"
]

negative_phrases = [
    "not good", "not great", "not happy", "not worth",
    "do not like", "don't like", "did not enjoy",
    "doesn't work", "does not work", "no longer works",
    "waste of time", "waste of money", "very disappointed"
]

negations = {
    "not", "no", "never", "neither", "hardly",
    "barely", "isn't", "wasn't", "don't", "doesn't",
    "didn't", "can't", "cannot", "won't"
}


def classify_sentiment(sentence: str) -> str:
    text = sentence.lower()
    words = re.findall(r"[a-z']+", text)

    if not words:
        return "neutral"

    # Handle common multi-word expressions first.
    pos_score = sum(2 for phrase in positive_phrases if phrase in text)
    neg_score = sum(2 for phrase in negative_phrases if phrase in text)

    for i, word in enumerate(words):
        if word in positive_words:
            # A nearby negation reverses positive sentiment.
            window = words[max(0, i - 3):i]
            if any(w in negations for w in window):
                neg_score += 1
            else:
                pos_score += 1

        elif word in negative_words:
            # A nearby negation reverses negative sentiment.
            window = words[max(0, i - 3):i]
            if any(w in negations for w in window):
                pos_score += 1
            else:
                neg_score += 1

    # Intensifiers strengthen the following sentiment word.
    intensifiers = {"very", "really", "extremely", "absolutely", "so"}
    for i, word in enumerate(words):
        if word in intensifiers and i + 1 < len(words):
            next_word = words[i + 1]
            if next_word in positive_words:
                pos_score += 1
            elif next_word in negative_words:
                neg_score += 1

    if pos_score > neg_score:
        return "happy"
    if neg_score > pos_score:
        return "sad"
    return "neutral"


@app.post("/sentiment")
def sentiment(request: SentimentRequest):
    return {
        "results": [
            {
                "sentence": sentence,
                "sentiment": classify_sentiment(sentence)
            }
            for sentence in request.sentences
        ]
    }
