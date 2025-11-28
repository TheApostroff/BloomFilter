from bloomfilter import BloomFilter
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PASSWORDS = os.path.join(CURRENT_DIR, "passwords.txt")

passwords = []

with open(PASSWORDS, "r", encoding="utf-8") as f:
    passwords = f.readlines()

BF = BloomFilter(len(passwords) if passwords else 100, 0.01)

for password in passwords:
    BF.add(password.removesuffix("\n"))