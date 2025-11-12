import mmh3
import json
from typing import Set, List


class BloomFilter:
    """
    Implementare a unui Bloom Filter pentru detecția rapidă a prezenței citate în cărți.
    Utilizează hash functions multiple (mmh3) pentru a minimiza false positives.
    """
    
    def __init__(self, size: int = 10000, num_hashes: int = 3):
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
    
    def add(self, quote: str, book_title: str):
        """
        Adaugă o citație în Bloom Filter.
        
        Args:
            quote: Textul citației
            book_title: Titlul cărții din care provine citația
        """
        quote_lower = quote.lower().strip()
        
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
        quote_lower = quote.lower().strip()
        
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
        quote_lower = quote.lower().strip()
        return self.quotes.get(quote_lower, [])
    
    def add_quotes_from_text(self, text: str, book_title: str, chunk_size: int = 100):
        """
        Extrage și adaugă citate din text (segmente de cuvinte).
        
        Args:
            text: Textul cărții
            book_title: Titlul cărții
            chunk_size: Numărul de cuvinte pentru fiecare segment
        """
        # Curăță textul
        words = text.lower().split()
        
        # Adaugă segmente de cuvinte ca citate
        for i in range(len(words) - chunk_size + 1):
            chunk = ' '.join(words[i:i + chunk_size])
            self.add(chunk, book_title)
    
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
        """Reconstrconstructe un Bloom Filter din dicționar."""
        bf = cls(size=data["size"], num_hashes=data["num_hashes"])
        bf.bit_array = data["bit_array"]
        bf.quotes = data["quotes"]
        return bf
