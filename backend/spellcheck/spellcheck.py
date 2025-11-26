from bloomfilter import BloomFilter
import os

# Get the absolute path to the Romanian words file
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROMANIAN_WORDS_FILE = os.path.join(CURRENT_DIR, "words", "Romanian", "Romanian.txt")

romanian_words = []

# Read Romanian words from file
with open(ROMANIAN_WORDS_FILE, "r", encoding="utf-8") as f:
    content = f.read()
    romanian_words = [word.strip() for word in content.split(",") if word.strip()]

# Initialize Bloom Filter with the number of words and false positive probability
BF = BloomFilter(len(romanian_words) if romanian_words else 100, 0.01)

# Add all Romanian words to the Bloom Filter
for word in romanian_words:
    BF.add(word.lower())


def check_word(word):
    """
    Check if a word exists in the Romanian dictionary using Bloom Filter.
    
    Args:
        word (str): The word to check
        
    Returns:
        bool: True if the word might exist (or false positive), False if definitely not exists
    """
    return BF.check(word.lower())


def check_text(text):
    """
    Check multiple words in a text and return which ones are not in the dictionary.
    
    Args:
        text (str): Text containing words to check
        
    Returns:
        list: List of words that are not in the dictionary
    """
    words = text.split()
    misspelled = []
    
    for word in words:
        # Remove punctuation
        clean_word = ''.join(char for char in word if char.isalnum())
        if clean_word and not check_word(clean_word) and len(clean_word) > 1:
            misspelled.append(word)
    
    return misspelled


def get_stats():
    """
    Get statistics about the Bloom Filter.
    
    Returns:
        dict: Dictionary containing stats about the bloom filter
    """
    return {
        "total_words": len(romanian_words),
        "bloom_filter_size": BF.size,
        "hash_count": BF.hash_count,
        "false_positive_probability": BF.fp_prob
    }



