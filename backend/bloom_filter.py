import mmh3
import json
import re
from typing import Set, List


class BloomFilter:
    """
    Implementare a unui Bloom Filter pentru detecția rapidă a prezenței citate în cărți.
    Utilizează hash functions multiple (mmh3) pentru a minimiza false positives.
    """
    
    def __init__(self, size: int = 200000, num_hashes: int = 3):
        """
        Inițializează Bloom Filter.
        
        Args:
            size: Dimensiunea bit array-ului
            num_hashes: Numărul de hash functions de utilizat
        """
        self.size = size
        self.num_hashes = num_hashes
        self.bit_array = [False] * size
        self.quotes = {}  # Stochează citații reale cu cartea de origine
        
    def _hash(self, item: str, seed: int) -> int:
        """Generează un hash pentru item utilizând seed-ul dat."""
        return mmh3.hash(item, seed=seed) % self.size
    
    def _get_hash_indices(self, item: str) -> List[int]:
        """Returnează indicii pentru o poziție în bit array."""
        indices = []
        for i in range(self.num_hashes):
            index = self._hash(item, seed=i)
            indices.append(index)
        return indices

    def _normalize_text(self, text: str) -> str:
        """
        Normalize text by lowercasing, removing punctuation, and collapsing whitespace.
        This ensures that stored quotes and search queries are compared in a consistent manner.
        """
        if not text:
            return ''
        # Lowercase
        t = text.lower()
        # Replace non-word characters with spaces; keep word characters and whitespace
        t = re.sub(r"[^\w\s]", ' ', t)
        # Collapse multiple whitespace to single space
        t = re.sub(r"\s+", ' ', t).strip()
        return t
    
    def add(self, quote: str, book_title: str):
        """
        Adaugă o citație în Bloom Filter.
        
        Args:
            quote: Textul citației
            book_title: Titlul cărții din care provine citația
        """
        quote_lower = self._normalize_text(quote)
        
        # Setează biții în array
        for index in self._get_hash_indices(quote_lower):
            self.bit_array[index] = True
        
        # Stochează citația și cartea de origine
        if quote_lower not in self.quotes:
            self.quotes[quote_lower] = []
        
        if book_title not in self.quotes[quote_lower]:
            self.quotes[quote_lower].append(book_title)
    
    def possibly_contains(self, quote: str) -> bool:
        """
        Verifică dacă o citație ar putea fi în set (poate da false positives).
        
        Args:
            quote: Textul citației de căutat
            
        Returns:
            True dacă citația ar putea fi prezentă, False dacă sigur nu este
        """
        quote_lower = self._normalize_text(quote)
        
        for index in self._get_hash_indices(quote_lower):
            if not self.bit_array[index]:
                return False
        return True
    
    def get_quote_source(self, quote: str) -> List[str]:
        """
        Dacă citația este verificată cu succes, returnează cărțile din care provine.
        
        Args:
            quote: Textul citației
            
        Returns:
            Lista cărților care conțin citația
        """
        quote_lower = self._normalize_text(quote)
        return self.quotes.get(quote_lower, [])
    
    def add_quotes_from_text(self, text: str, book_title: str, chunk_size: int = 100, min_chunk: int | None = None, max_chunk: int | None = None):
        """
        Extrage și adaugă citate din text (segmente de cuvinte).
        
        Args:
            text: Textul cărții
            book_title: Titlul cărții
            chunk_size: Numărul de cuvinte pentru fiecare segment
        """
        # Normalize and split text into words
        norm_text = self._normalize_text(text)
        words = norm_text.split()

        # Default cap for maximum n-gram length to avoid explosion
        DEFAULT_MAX_NGRAM = 25
        if min_chunk is None:
            # Preserve previous behavior of exact chunk size when min_chunk isn't provided
            min_chunk = chunk_size
        if max_chunk is None:
            # Cap large chunk_size by DEFAULT_MAX_NGRAM for performance
            max_chunk = min(chunk_size, DEFAULT_MAX_NGRAM)

        # Ensure bounds are sensible
        if min_chunk < 1:
            min_chunk = 1
        if min_chunk > max_chunk:
            # Reduce min_chunk to max_chunk if the requested min is larger than available cap
            min_chunk = max_chunk

        nwords = len(words)
        if nwords == 0:
            return

        # If the text is extremely short, still add the whole text as a quote
        if nwords <= min_chunk:
            self.add(' '.join(words), book_title)
            return

        # Add n-grams of sizes between min_chunk and max_chunk
        # Cap max_chunk to nwords to avoid long loops
        max_chunk = min(max_chunk, nwords)

        for size in range(min_chunk, max_chunk + 1):
            for i in range(0, nwords - size + 1):
                chunk = ' '.join(words[i:i + size])
                self.add(chunk, book_title)

        # Note: This will add small n-grams that make searching short quotes possible
    
    def get_stats(self) -> dict:
        """Returnează statistici despre Bloom Filter."""
        bits_set = sum(self.bit_array)
        return {
            "size": self.size,
            "bits_set": bits_set,
            "fill_percentage": (bits_set / self.size) * 100,
            "num_hashes": self.num_hashes,
            "total_quotes": len(self.quotes)
        }
    
    def to_dict(self) -> dict:
        """Convertește Bloom Filter-ul la dicționar pentru stocare."""
        return {
            "size": self.size,
            "num_hashes": self.num_hashes,
            "bit_array": self.bit_array,
            "quotes": self.quotes
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'BloomFilter':
        """Reconstruiește un Bloom Filter din dicționar."""
        bf = cls(size=data["size"], num_hashes=data["num_hashes"])
        bf.bit_array = data["bit_array"]
        bf.quotes = data["quotes"]
        return bf
