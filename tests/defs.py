# This file is part of https://github.com/KurtBoehm/polyqr.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# The test strings where partially generated using GPT-5
test_messages = [
    # basics and edge cases
    "",
    " ",
    "  ",
    "\t",
    "\n",
    "\r\n",
    " \n\t",
    "A",
    "0",
    "€",
    "Café",
    "e\u0301 vs é",  # combining acute vs precomposed
    "A\u030a vs Å",  # combining ring above vs precomposed
    # numeric-only (triggers numeric mode)
    "1",
    "42",
    "007",
    "1234567890",
    "1" * 25,
    "9" * 100,
    # alphanumeric set (triggers alphanumeric mode)
    "HELLO WORLD",
    "QR-CODE/TEST:12345",
    "THE QUICK BROWN FOX 0123456789 $%*+-./:",
    "ABC123XYZ$%*+-./:",
    "CODE-128-TEST-123456",
    # ASCII punctuation and symbols (forces byte mode)
    "!@#$%^&*()_+[]{}|;':,./<>?`~",
    'He said, "Hello" — then left.',
    "It's fine — isn’t it?",
    "“Smart quotes” and ‘single’",
    "\\ backslash and / slash",
    "C:\\Program Files\\App\\bin",
    "/usr/local/bin:/usr/bin",
    # URLs and URIs
    "https://example.org",
    "http://例え.テスト/パス?クエリ=値",
    "mailto:info@example.org",
    "tel:+1-555-0100",
    "geo:37.786971,-122.399677",
    "WIFI:T:WPA;S:MySSID;P:S3cr3t!;H:false;;",
    "SMSTO:+15550100:Hello",
    # JSON, XML-like, and structured payloads
    '{"name":"Alice","age":30,"active":true}',
    '{"list":[1,2,3,4,5],"nested":{"k":"v"}}',
    '{\n  "pretty": true,\n  "items": [1, 2, 3]\n}',
    "<note><to>Bob</to><msg>Hello</msg></note>",
    # vCard / MECARD (newlines included)
    "BEGIN:VCARD\nVERSION:3.0\nN:Doe;John;;;\nFN:John Doe\nEMAIL:john@example.com\nEND:VCARD",
    "MECARD:N:Doe,John;TEL:15550100;EMAIL:john@example.com;;",
    # whitespace variants
    "leading space",
    "trailing space ",
    "multiple   spaces",
    "tab\tseparated\tvalues",
    "line1\nline2\nline3",
    "non-breaking space:\u00a0here",
    "zero-width space:\u200bbetween",
    "zero-width joiner:\u200djoin",
    "em/en dashes — – and ellipsis …",
    # control characters (as escapes)
    "\x00",
    "\x00\x01\x02\t\n\r",
    "NUL-in-text:\x00end",
    # non-Latin scripts
    "汉字かな交じり文",
    "こんにちは世界",
    "中文測試",
    "繁體中文測試",
    "안녕하세요 세계",
    "สวัสดีโลก",
    "नमस्ते दुनिया",
    "مرحبا بالعالم",
    "שלום עולם",
    "γειά σου κόσμε",
    "Привет, мир",
    # emoji and complex sequences
    "😀",
    "👍🏽",
    "🏳️‍🌈",
    "🇺🇳",
    "👩‍👩‍👧‍👦 family",
    "🧑‍🔬🧪 science",
    "keycap: 1️⃣ 2️⃣ 3️⃣",
    "Zalgo: Z͑͗ͮȁ͌l̐ͭgͪͨo̓̅",
    # outside BMP (4-byte UTF-8)
    "𐍈 Gothic letter",
    "Rare CJK: 𠜎 𠜱 𠝹 𠱓",
    "Mathematical bold: 𝐀𝐁𝐂 𝟘𝟙𝟚",
    "Fraktur: 𝔘𝔫𝔦𝔠𝔬𝔡𝔢",
    # bidi and directionality marks
    "RTL Arabic with LRM\u200e and RLM\u200f: مرحبا",
    "Mixed bidi: ABC\u202eDEF\u202cXYZ",
    # currency and symbols
    "€ £ ¥ ₹ ₩ ₿",
    "∑ ∞ √ π ± ≤ ≥ ≠",
    # paths, IDs, codes
    "urn:isbn:0451450523",
    "doi:10.1000/182",
    "EAN-13: 4006381333931",
    "0xDEADBEEF",
    "deadbeef",
    "SGVsbG8sIFdvcmxkIQ==",
    # longer repeats (moderate size)
    "A" * 100,
    "語" * 80,
    "emoji-seq: " + "🙂" * 50,
    # mixed content
    "User: alice@example.com; Tel: +44 20 7946 0958; Addr: 221B Baker St, London",
    "Pangram: The quick brown fox jumps over the lazy dog 0123456789.",
    "German: Falsches Üben von Xylophonmusik quält jeden größeren Zwerg.",
    "Polish: Pchnąć w tę łódź jeża lub osiem skrzyń fig.",
    "Spanish: El veloz murciélago hindú comía feliz cardillo y kiwi.",
]
