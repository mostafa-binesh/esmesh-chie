def fix_garbled_persian(garbled_text):
    try:
        # Correct mojibake by decoding as Windows-1252 first
        return garbled_text.encode('windows-1252').decode('utf-8')
    except Exception as e:
        return f"Error: {str(e)}"


# Test with multiple sample texts
test_cases = [
    "Ø±ÙˆØ­ Ø§Ù„Ù„Ù‡ Ù…Ø±Ø§Ø¯Ù„Ùˆ",
    "Ø¨Ù‡Ø´ØªÙ‡ ÙƒÙˆÙ‡Ø³ØªØ§Ù†ÙŠ",
    "Ø­Ø³ÙŠÙ† Ù†Ø§Ø±ÙˆØ¦ÙŠ",
    "ØºÙ„Ø§Ù…Ø­Ø³ÙŠÙ† Ù…Ø­Ù…Ø¯Ø²Ø§Ø¯Ù‡ Ø³ÙŠØ§Ù†ÙŠ"
]

for garbled_text in test_cases:
    fixed_text = fix_garbled_persian(garbled_text)
    print(f"Input: {garbled_text}")
    print(f"Output: {fixed_text}")
    print()
