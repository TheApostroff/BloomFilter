import math
import mmh3
import re
from typing import Set, List
from bitarray import bitarray


class BloomFilter(object):

    '''
    Class for Bloom filter, using murmur3 hash function
    '''

    def __init__(self, items_count, fp_prob):
        '''
        items_count : int
            Number of items expected to be stored in bloom filter
        fp_prob : float
            False Positive probability in decimal
        '''
        # False possible probability in decimal
        self.fp_prob = fp_prob

        # Size of bit array to use
        self.size = self.get_size(items_count, fp_prob)

        # number of hash functions to use
        self.hash_count = self.get_hash_count(self.size, items_count)

        # Bit array of given size
        self.bit_array = bitarray(self.size)

        # initialize all bits as 0
        self.bit_array.setall(0)

        self.quotes = {}

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

    def add(self, item):
        '''
        Add an item in the filter
        '''
        digests = []
        for i in range(self.hash_count):

            # create digest for given item.
            # i work as seed to mmh3.hash() function
            # With different seed, digest created is different
            digest = mmh3.hash(item, i) % self.size
            digests.append(digest)

            # set the bit True in bit_array
            self.bit_array[digest] = True

    def check(self, item):
        '''
        Check for existence of an item in filter
        '''
        for i in range(self.hash_count):
            digest = mmh3.hash(item, i) % self.size
            if not self.bit_array[digest]:

                # if any of bit is False then,its not present
                # in filter
                # else there is probability that it exist
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
            self.add(' '.join(words))
            return

        # Add n-grams of sizes between min_chunk and max_chunk
        # Cap max_chunk to nwords to avoid long loops
        max_chunk = min(max_chunk, nwords)

        for size in range(min_chunk, max_chunk + 1):
            for i in range(0, nwords - size + 1):
                chunk = ' '.join(words[i:i + size])
                self.add(chunk)

    @classmethod
    def get_size(cls, n, p):
        '''
        Return the size of bit array(m) to used using   
        following formula
        m = -(n * lg(p)) / (lg(2)^2)
        n : int
            number of items expected to be stored in filter
        p : float
            False Positive probability in decimal
        '''
        m = -(n * math.log(p))/(math.log(2)**2)
        return int(m)

    @classmethod
    def get_hash_count(cls, m, n):
        '''
        Return the hash function(k) to be used using
        following formula
        k = (m/n) * lg(2)

        m : int
            size of bit array
        n : int
            number of items expected to be stored in filter
        '''
        k = (m/n) * math.log(2)
        return int(k)
