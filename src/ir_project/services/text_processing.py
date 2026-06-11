import re
from dataclasses import dataclass

from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS


TOKEN_RE = re.compile(r"[a-zA-Z0-9]+")


@dataclass
class TextProcessor:
    lowercase: bool = True
    remove_stopwords: bool = True
    min_token_len: int = 2

    def tokenize(self, text: str) -> list[str]:
        if self.lowercase:
            text = text.lower()
        tokens = TOKEN_RE.findall(text)
        tokens = [token for token in tokens if len(token) >= self.min_token_len]
        if self.remove_stopwords:
            tokens = [token for token in tokens if token not in ENGLISH_STOP_WORDS]
        return tokens

    def normalize(self, text: str) -> str:
        return " ".join(self.tokenize(text or ""))
