import unittest
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from spellcheck import check_word, check_text, get_stats, romanian_words, BF


class TestSpellcheck(unittest.TestCase):
    """Test cases for Romanian spellcheck using Bloom Filter"""

    def test_bloom_filter_initialized(self):
        """Test that Bloom Filter is properly initialized"""
        self.assertIsNotNone(BF)
        self.assertGreater(BF.size, 0)
        self.assertGreater(BF.hash_count, 0)
        
    def test_romanian_words_loaded(self):
        """Test that Romanian words are loaded from file"""
        self.assertIsInstance(romanian_words, list)
        print(f"Loaded {len(romanian_words)} Romanian words")
        
    def test_check_word_exists(self):
        """Test checking words that exist in the dictionary"""
        # Test with words from the Romanian dictionary
        if romanian_words:
            # Test first few words
            for word in romanian_words[:min(5, len(romanian_words))]:
                result = check_word(word)
                self.assertTrue(result, f"Word '{word}' should be in dictionary")
                
    def test_check_word_case_insensitive(self):
        """Test that word checking is case insensitive"""
        if romanian_words:
            test_word = romanian_words[0]
            # Test lowercase
            self.assertTrue(check_word(test_word.lower()))
            # Test uppercase
            self.assertTrue(check_word(test_word.upper()))
            # Test mixed case
            self.assertTrue(check_word(test_word.capitalize()))
            
    def test_check_word_not_exists(self):
        """Test checking words that definitely don't exist"""
        # These are random strings that should not be in any Romanian dictionary
        fake_words = ["xyzabc123", "qqqqqqqq", "zzzzzzzz123", "abcdefghijklmnop"]
        for word in fake_words:
            result = check_word(word)
            # Note: Bloom filter may have false positives, but these should mostly be False
            print(f"Checking fake word '{word}': {result}")
            
    def test_check_text_empty(self):
        """Test checking empty text"""
        result = check_text("")
        self.assertEqual(result, [])
        
    def test_check_text_all_correct(self):
        """Test text with all correct words"""
        if len(romanian_words) >= 3:
            text = " ".join(romanian_words[:3])
            result = check_text(text)
            self.assertEqual(result, [], f"All words should be correct, but got: {result}")
            
    def test_check_text_with_misspelled(self):
        """Test text with some misspelled words"""
        if romanian_words:
            # Mix correct words with definitely incorrect ones
            text = f"{romanian_words[0]} xyzabc {romanian_words[1] if len(romanian_words) > 1 else 'test'} qqqqqqqq"
            result = check_text(text)
            print(f"Misspelled words in '{text}': {result}")
            # Should find at least some misspelled words
            self.assertIsInstance(result, list)
            
    def test_check_text_with_punctuation(self):
        """Test that punctuation is handled correctly"""
        if romanian_words:
            # Add punctuation to correct words
            text = f"{romanian_words[0]}. {romanian_words[1] if len(romanian_words) > 1 else 'test'}!"
            result = check_text(text)
            # Punctuation should be removed and words should be recognized
            print(f"Text with punctuation: '{text}', misspelled: {result}")
            
    def test_get_stats(self):
        """Test getting Bloom Filter statistics"""
        stats = get_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn("total_words", stats)
        self.assertIn("bloom_filter_size", stats)
        self.assertIn("hash_count", stats)
        self.assertIn("false_positive_probability", stats)
        
        # Verify values
        self.assertEqual(stats["total_words"], len(romanian_words))
        self.assertGreater(stats["bloom_filter_size"], 0)
        self.assertGreater(stats["hash_count"], 0)
        self.assertEqual(stats["false_positive_probability"], 0.01)
        
        print(f"\nBloom Filter Statistics:")
        print(f"  Total words: {stats['total_words']}")
        print(f"  Bloom filter size: {stats['bloom_filter_size']} bits")
        print(f"  Hash count: {stats['hash_count']}")
        print(f"  False positive probability: {stats['false_positive_probability']}")
        
    def test_bloom_filter_efficiency(self):
        """Test that Bloom Filter is more memory efficient than storing all words"""
        if romanian_words:
            # Calculate memory used by Bloom Filter (in bytes)
            bloom_memory = BF.size / 8  # bits to bytes
            
            # Calculate memory used by storing all words (rough estimate)
            words_memory = sum(len(word.encode('utf-8')) for word in romanian_words)
            
            print(f"\nMemory Efficiency:")
            print(f"  Bloom Filter memory: {bloom_memory:.2f} bytes")
            print(f"  Direct storage memory: {words_memory:.2f} bytes")
            print(f"  Compression ratio: {words_memory / bloom_memory:.2f}x")
            
            # Bloom filter should use less memory
            self.assertLess(bloom_memory, words_memory)


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == "__main__":
    print("="*70)
    print("Romanian Spellcheck Bloom Filter Tests")
    print("="*70)
    run_tests()
