import pytest
from bloom_filter import BloomFilter


def test_add_and_query():
    bf = BloomFilter(size=100, num_hashes=3)
    quote = "Hello World"
    bf.add(quote, "Book1")
    assert bf.possibly_contains(quote) is True
    sources = bf.get_quote_source(quote)
    assert "Book1" in sources


def test_negative():
    bf = BloomFilter(size=100, num_hashes=3)
    assert bf.possibly_contains("something unknown") is False


def test_add_quotes_from_text():
    text = "one two three four five six seven eight"
    bf = BloomFilter(size=100, num_hashes=2)
    bf.add_quotes_from_text(text, "TestBook", chunk_size=2)
    # ensure at least one chunk present
    assert bf.possibly_contains("one two") is True
    assert "TestBook" in bf.get_quote_source("one two")


def test_add_quotes_from_text_small_ngrams():
    text = "this is a simple quote extraction test for indexing" 
    bf = BloomFilter(size=200, num_hashes=3)
    # create 2-3-4 grams
    bf.add_quotes_from_text(text, "TestBook2", chunk_size=10, min_chunk=2, max_chunk=4)
    assert bf.possibly_contains('simple quote') is True
    assert "TestBook2" in bf.get_quote_source('simple quote')


def test_to_dict_from_dict_roundtrip():
    bf = BloomFilter(size=200, num_hashes=4)
    bf.add('hello world', 'BookX')
    data = bf.to_dict()
    bf2 = BloomFilter.from_dict(data)
    assert bf2.size == bf.size
    assert bf2.num_hashes == bf.num_hashes
    assert bf2.get_quote_source('hello world') == bf.get_quote_source('hello world')
