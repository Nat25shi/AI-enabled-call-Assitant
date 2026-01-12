import re
import soundfile as sf
import pyttsx3
import socket
from faster_whisper import WhisperModel
from pydantic import BaseModel
from typing import List

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
#from langchain_community.chat_models import ChatOllama
from langchain_ollama import ChatOllama

AUDIO_FILE = "customer.wav"

# SYNTHETIC_CUSTOMER_TEXT = (
   # "Honestly, I like what you’re offering, "
   # "but the price feels too high for us right now."
#)
#def text_to_speech(text: str, output_file: str):
 #   engine = pyttsx3.init()
 #   engine.save_to_file(text, output_file)
 #   engine.runAndWait()

#print("Generating customer audio...")
#text_to_speech(SYNTHETIC_CUSTOMER_TEXT, AUDIO_FILE)


class ASR:
    def __init__(self):
        self.model = WhisperModel(
            "small",
            device="cpu",
            compute_type="int8"
        )

    def transcribe(self, audio_path: str, beam_size: int = 5, word_timestamps: bool = False) -> str:
        segments, _ = self.model.transcribe(audio_path, beam_size=beam_size, word_timestamps=word_timestamps)
        return " ".join(seg.text for seg in segments)


# Create a single ASR instance to avoid reloading the model per request (very slow)
asr = ASR()
def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\b(uh|um|you know|like)\b", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


class IntentOutput(BaseModel):
    intent: str
    sentiment: str
    entities: List[str]


# Intent Extractor

llm = ChatOllama(
    model="neural-chat", temperature=0
)

parser = PydanticOutputParser(
    pydantic_object=IntentOutput
)

intent_prompt = ChatPromptTemplate.from_template("""
You are an intent and sentiment classifier for sales calls.

Text:
{text}

Classify:
- intent (pricing_objection, interest, complaint, purchase_intent, other)
- sentiment (positive, neutral, negative)
- entities (keywords)

{format_instructions}
""")

intent_chain = intent_prompt | llm | parser
 

def _ollama_reachable() -> bool:
    try:
        sock = socket.create_connection(("localhost", 11434), timeout=1)
        sock.close()
        return True
    except Exception:
        return False


def _clean_recommendation(text: str) -> str:
    """Extract the actual recommendation from LLM output, removing template echoes and preambles."""
    if not text:
        return ""
    
    text = text.strip()
    
    # Remove template echoes (Intent:, Sentiment:, Entities:, etc.)
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        # Skip lines that are template echoes
        if not any(stripped.startswith(kw) for kw in ["Intent:", "Sentiment:", "Entities:", "Based on:", "Give", "Classify:", "Text:"]):
            cleaned_lines.append(stripped)
    
    text = " ".join(cleaned_lines).strip()
    
    # Remove common LLM preambles
    preambles = [
        "One short recommendation for the sales agent could be to ",
        "One short recommendation for the sales agent is to ",
        "A short recommendation for the sales agent could be to ",
        "The recommendation for the sales agent is to ",
        "A good recommendation is to ",
        "I recommend that the sales agent ",
        "Recommendation: ",
    ]
    
    for preamble in preambles:
        if text.lower().startswith(preamble.lower()):
            text = text[len(preamble):].strip()
            break
    
    return text


def process_audio(audio_path: str, fast: bool = False) -> dict:
    """Transcribe and analyze audio. Returns a dict with keys:
    raw_text, cleaned_text, intent, sentiment, entities, action, recommendation, error
    """
    # Use the shared ASR instance (faster) and allow fast mode
    raw_text = ""
    error_msg = ""
    try:
        if fast:
            raw_text = asr.transcribe(audio_path, beam_size=1)
        else:
            raw_text = asr.transcribe(audio_path)
    except Exception as e:
        error_msg = f"ASR transcription failed: {str(e)}"
        print(error_msg)
        raw_text = ""

    cleaned_text = clean_text(raw_text)

    ollama_ok = _ollama_reachable()
    raw_intent_resp = ""
    raw_recommendation_resp = ""

    if not ollama_ok:
        intent_result = IntentOutput(intent="other", sentiment="neutral", entities=[])
    else:
        try:
            # Always fetch raw model response first, then parse with the Pydantic parser
            raw_resp = (intent_prompt | llm).invoke({
                "text": cleaned_text,
                "format_instructions": parser.get_format_instructions()
            })
            raw_intent_resp = getattr(raw_resp, "content", raw_resp if isinstance(raw_resp, str) else str(raw_resp))
            try:
                intent_result = parser.parse(raw_intent_resp)
            except Exception:
                # parsing failed; fall back to defaults
                intent_result = IntentOutput(intent="other", sentiment="neutral", entities=[])
        except Exception:
            intent_result = IntentOutput(intent="other", sentiment="neutral", entities=[])

    action = decide_action(intent_result)

    recommendation_prompt = ChatPromptTemplate.from_template("""
You are a sales coach.

Based on:
Intent: {intent}
Sentiment: {sentiment}
Entities: {entities}

Give ONE short recommendation for the sales agent.
""")

    recommendation_chain = recommendation_prompt | llm

    try:
        rec_resp = recommendation_chain.invoke({
            "intent": intent_result.intent,
            "sentiment": intent_result.sentiment,
            "entities": ", ".join(intent_result.entities)
        })
        raw_recommendation_resp = getattr(rec_resp, "content", str(rec_resp))
        recommendation = _clean_recommendation(raw_recommendation_resp)
    except Exception:
        recommendation = ""

    return {
        "raw_text": raw_text,
        "cleaned_text": cleaned_text,
        "intent": getattr(intent_result, "intent", "other"),
        "sentiment": getattr(intent_result, "sentiment", "neutral"),
        "entities": getattr(intent_result, "entities", []),
        "action": action,
        "recommendation": recommendation,
        "error": error_msg,
        "ollama_reachable": ollama_ok,
        "raw_intent_response": raw_intent_resp,
        "raw_recommendation_response": raw_recommendation_resp,
    }


# Decision Logic (Rules)

def decide_action(intent_data: IntentOutput) -> str:
    if intent_data.intent == "pricing_objection":
        if intent_data.sentiment == "negative":
            return "Empathize with concern, then explain ROI before discount"
        return "Explain pricing structure clearly"

    if intent_data.intent == "complaint":
        return "Acknowledge issue and ask clarifying question"

    if intent_data.intent == "purchase_intent":
        return "Move to close and discuss onboarding"

    return "Provide general clarification"


if __name__ == "__main__":
    print("Transcribing audio...", AUDIO_FILE)
    res = process_audio(AUDIO_FILE)
    print("RAW TRANSCRIPT:", res.get("raw_text"))
    print("CLEANED TEXT:", res.get("cleaned_text"))
    print("Detected intent:", res.get("intent"))
    print("Detected sentiment:", res.get("sentiment"))
    print("Sales action:", res.get("action"))
    print("Sales recommendation:", res.get("recommendation"))