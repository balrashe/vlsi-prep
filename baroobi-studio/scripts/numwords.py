"""Digits -> spoken words, shared by the voice clone (what to say) and caption alignment (matching Whisper)."""
import re

ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen " \
       "seventeen eighteen nineteen".split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def words(n):
    if n < 20:
        return ONES[n]
    if n < 100:
        return TENS[n // 10] + ("-" + ONES[n % 10] if n % 10 else "")
    if n < 1000:
        return ONES[n // 100] + " hundred" + (" " + words(n % 100) if n % 100 else "")
    if n < 1_000_000:
        return words(n // 1000) + " thousand" + (" " + words(n % 1000) if n % 1000 else "")
    return words(n // 1_000_000) + " million" + (" " + words(n % 1_000_000) if n % 1_000_000 else "")


def spoken(tok):
    """'2025' -> 'twenty twenty-five', '311' -> 'three hundred eleven'; non-integers are returned unchanged."""
    if not re.fullmatch(r"\d+", tok):
        return tok
    n = int(tok)
    if 1900 <= n <= 2099 and len(tok) == 4:
        hi, lo = divmod(n, 100)
        return words(hi) + " " + (words(lo) if lo >= 10 else ("oh " + words(lo) if lo else "hundred"))
    return words(n)


def say_numbers(text):
    return re.sub(r"\b\d+\b", lambda m: spoken(m.group()), text)
