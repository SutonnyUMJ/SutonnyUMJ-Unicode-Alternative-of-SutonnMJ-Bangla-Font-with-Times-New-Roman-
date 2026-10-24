#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SutonnyMJ (Bijoy / ANSI)  ->  SutonnyUMJ (Unicode)         version 2

* Glyph OUTLINES are never modified.  Unicode text is turned into exactly the same
  glyph runs Bijoy typing produces (ground truth: the Bijoy guide's glyph table,
  embedded below as TRUTH), by GSUB rules; no composite glyphs are used for text, so every
  glyph is laid out / hinted exactly like in the original SutonnyMJ.
* Two pipelines in one GSUB table, selected by script tag:
    bng2 / beng : apps with a Bengali shaping engine (browsers, Word, LibreOffice ...)
    DFLT / latn : apps WITHOUT one (Photoshop/Illustrator western engine, CorelDRAW, GDI ...):
                  reordering, reph, conjuncts, phala, vowel signs done by plain lookups.
* Word-initial vs mid-word forms of ে ো ৈ († ‡ ˆ ‰), per-letter phala variants, ু/ূ/ৃ variants
  follow the Bijoy table.  ZWNJ-hasant, ঁ before vowel signs, ে+া, য় / ড় / ঢ় nukta forms
  are handled so text from Avro (all layouts) and Bijoy Unicode layouts renders correctly.
Usage:  python3 sutonny_to_unicode.py  "SutonnyMJ Regular.ttf"  "SutonnyUMJ Regular.ttf"
Requires: fonttools
"""
import sys, os, math
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables._c_m_a_p import cmap_format_4
from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphComponent, GlyphCoordinates
from fontTools.ttLib.tables import ttProgram
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.pens.ttGlyphPen import TTGlyphPen

SRC = sys.argv[1] if len(sys.argv) > 1 else "SutonnyMJ Regular.ttf"
OUT = sys.argv[2] if len(sys.argv) > 2 else "SutonnyUMJ Regular.ttf"

# Unicode sequence -> Bijoy glyph string (from the Bijoy guide table)
TRUTH = {
    'কু': 'Kz',
    'কূ': 'K‚',
    'কৃ': 'K…',
    'ক্ক': '°',
    'ক্কু': '°z',
    'ক্কূ': '°‚',
    'ক্কৃ': '°…',
    'ক্ট': '±',
    'ক্টু': '±z',
    'ক্টূ': '±‚',
    'ক্টৃ': '±…',
    'ক্ত': '³',
    'ক্তু': '³z',
    'ক্তূ': '³‚',
    'ক্তৃ': '³…',
    'ক্ত্র': '³«',
    'ক্ন': 'Kè',
    'ক্নু': 'Kèz',
    'ক্নূ': 'Kè‚',
    'ক্নৃ': 'Kè…',
    'ক্ব': 'K¡',
    'ক্ম': '´',
    'ক্র': 'µ',
    'ক্রু': 'µz',
    'ক্রূ': 'µ‚',
    'ক্রৃ': 'µ…',
    'ক্ল': 'K¬',
    'ক্লু': 'K¬z',
    'ক্লূ': 'K¬‚',
    'ক্লৃ': 'K¬„',
    'ক্ষ': '¶',
    'ক্ষু': '¶z',
    'ক্ষূ': '¶‚',
    'ক্ষৃ': 'ÿ„',
    'ক্ষ্ন': 'ÿè',
    'ক্ষ্নু': '¶èy',
    'ক্ষ্নূ': 'ÿè~',
    'ক্ষ্নৃ': '¶è„',
    'ক্ষ্ম': '²',
    'ক্স': '·',
    'খ্র': 'Lª',
    'খ্রূ': 'Lªƒ',
    'গু': '¸',
    'গ্দ': 'º',
    'গ্ধ': '»',
    'গ্ধু': '»y',
    'গ্ধূ': '»~',
    'গ্ধৃ': '»„',
    'গ্ন': 'Mœ',
    'গ্ব': 'M¦',
    'গ্ম': 'M¥',
    'গ্র': 'MÖ',
    'গ্রু': 'MÖæ',
    'গ্রূ': 'MÖƒ',
    'ঘ্ন': 'Nœ',
    'ঘ্র': 'Nª',
    'ঘ্রু': 'Nªæ',
    'ঘ্রূ': 'Nªƒ',
    'ঙু': 'Oz',
    'ঙূ': 'O‚',
    'ঙৃ': 'O…',
    'ঙ্ক': '¼',
    'ঙ্কু': '¼z',
    'ঙ্ক্র': '¼«',
    'ঙ্ক্রু': '¼«y',
    'ঙ্ক্রূ': '¼«~',
    'ঙ্ক্রৃ': '¼«„',
    'ঙ্ক্ষ': '•¶',
    'ঙ্ক্ষু': '•¶y',
    'ঙ্ক্ষূ': '•¶~',
    'ঙ্ক্ষৃ': '•¶„',
    'ঙ্খ': '•L',
    'ঙ্গ': '½',
    'ঙ্ঘ': '•N',
    'ঙ্ঘ্র': '•Nª',
    'ঙ্ম': '•g',
    'চু': 'Pz',
    'চূ': 'P‚',
    'চৃ': 'P…',
    'চ্চ': '”P',
    'চ্চু': '”Pz',
    'চ্চূ': '”P‚',
    'চ্চৃ': '”P…',
    'চ্ছ': '”Q',
    'চ্ছু': '”Qz',
    'চ্ছূ': '”Q‚',
    'চ্ছৃ': '”Q…',
    'চ্ছ্ব': '”Q¡',
    'চ্ছ্র': '”Qª',
    'চ্ঞ': '”T',
    'চ্ঞু': '”Tz',
    'চ্ঞূ': '”T‚',
    'চ্ঞৃ': '”T…',
    'ছু': 'Qz',
    'ছূ': 'Q‚',
    'ছৃ': 'Q…',
    'ছ্র': 'Q«',
    'জ্জ': '¾',
    'জ্জ্ব': '¾¡',
    'জ্ঝ': 'À',
    'জ্ঝু': 'Àz',
    'জ্ঝূ': 'À~',
    'জ্ঝৃ': 'À„',
    'জ্ঞ': 'Á',
    'জ্ঞু': 'Áy',
    'জ্ঞূ': 'Á~',
    'জ্ঞৃ': 'Á„',
    'জ্ব': 'R¡',
    'ঝু': 'Sz',
    'ঝূ': 'S‚',
    'ঞু': 'Tz',
    'ঞূ': 'T‚',
    'ঞৃ': 'T…',
    'ঞ্চূ': 'Â~',
    'ঞ্চৃ': 'Â„',
    'ঞ্ছ': 'Ã',
    'ঞ্ছু': 'Ãz',
    'ঞ্ছূ': 'Ã‚',
    'ঞ্ছৃ': 'Ã…',
    'ঞ্জ': 'Ä',
    'ঞ্ঝ': 'Å',
    'ঞ্ঝু': 'Åz',
    'ঞ্ঝূ': 'Å~',
    'ঞ্ঝৃ': 'Å„',
    'টু': 'Uz',
    'টূ': 'U~',
    'টৃ': 'U„',
    'ট্ট': 'Æ',
    'ট্টু': 'Æz',
    'ট্টূ': 'Æ~',
    'ট্টৃ': 'Æ„',
    'ট্ট্র': 'Æª',
    'ট্ব': 'U¡',
    'ট্ম': 'U¥',
    'ট্র': 'Uª',
    'ঠু': 'Vz',
    'ঠূ': 'V‚',
    'ঠৃ': 'V…',
    'ডু': 'Wz',
    'ডূ': 'W‚',
    'ডৃ': 'W…',
    'ড্ড': 'Ç',
    'ড্ডু': 'Çz',
    'ড্ডূ': 'Ç‚',
    'ড্ডৃ': 'Ç…',
    'ড্র': 'Wª',
    'ঢূ': 'X‚',
    'ঢৃ': 'X…',
    'ণ্ট': 'È',
    'ণ্টু': 'Èz',
    'ণ্টূ': 'È~',
    'ণ্টৃ': 'È„',
    'ণ্ঠ': 'É',
    'ণ্ঠু': 'Éz',
    'ণ্ঠূ': 'É‚',
    'ণ্ঠৃ': 'É…',
    'ণ্ড': 'Ð',
    'ণ্ডু': 'Ðz',
    'ণ্ডূ': 'Ð‚',
    'ণ্ডৃ': 'Ð…',
    'ণ্ড্র': 'Ðª',
    'ণ্ন': 'Yœ',
    'ণ্ব': 'Y¦',
    'তু': 'Zz',
    'তূ': 'Z‚',
    'তৃ': 'Z…',
    'ত্ত': 'Ë',
    'ত্তু': 'Ëz',
    'ত্তূ': 'Ë‚',
    'ত্তৃ': 'Ë…',
    'ত্ত্ব': 'Ë¡',
    'ত্থ': 'Ì',
    'ত্ন': 'Zœ',
    'ত্ব': 'Z¡',
    'ত্ম': 'Z¥',
    'ত্র': 'Î',
    'ত্রু': 'Îæ',
    'দ্গ': '˜M',
    'দ্ঘ': '˜N',
    'দ্দ': 'Ï',
    'দ্ধ': '×',
    'দ্ধু': '×z',
    'দ্ধূ': '×~',
    'দ্ধৃ': '×„',
    'দ্ব': 'Ø',
    'দ্ভ': '™¢',
    'দ্ভু': '™¢z',
    'দ্ভূ': '™¢‚',
    'দ্ভৃ': '™¢„',
    'দ্ভ্র': '™£',
    'দ্ম': 'Ù',
    'দ্রু': '`ªæ',
    'দ্রূ': '`ªƒ',
    'ধ্ব': 'aŸ',
    'ধ্ম': 'a¥',
    'ধ্র': 'aª',
    'ধ্রু': 'aªæ',
    'ধ্রূ': 'aªƒ',
    'ন্ট': '›U',
    'ন্টু': '›Uz',
    'ন্টূ': '›U~',
    'ন্টৃ': '›U„',
    'ন্ঠ': 'Ú',
    'ন্ঠু': 'Úz',
    'ন্ঠূ': 'Ú‚',
    'ন্ঠৃ': 'Ú…',
    'ন্ড': 'Û',
    'ন্ডু': 'Ûz',
    'ন্ডূ': 'Û‚',
    'ন্ডৃ': 'Û…',
    'ন্ড্র': 'Ûª',
    'ন্ত': 'šÍ',
    'ন্তু': 'š‘',
    'ন্তূ': 'šÍ~',
    'ন্তৃ': 'šÍ„',
    'ন্ত্র': 'š¿',
    'ন্থ': 'š’',
    'ন্দ': '›`',
    'ন্দ্ব': '›Ø',
    'ন্দ্র': '›`ª',
    'ন্ধ': 'Ü',
    'ন্ধু': 'Üz',
    'ন্ধূ': 'Ü~',
    'ন্ধৃ': 'Ü„',
    'ন্ধ্র': 'Ü«',
    'ন্ধ্রু': 'Ü«y',
    'ন্ধ্রূ': 'Ü«~',
    'ন্ধ্রৃ': 'Ü«„',
    'ন্ন': 'bœ',
    'ন্ব': 'š^',
    'ন্ম': 'b¥',
    'ন্স': 'Ý',
    'প্ট': 'Þ',
    'প্টু': 'Þz',
    'প্টূ': 'Þ~',
    'প্টৃ': 'Þ„',
    'প্ত': 'ß',
    'প্তু': 'ßz',
    'প্তূ': 'ß‚',
    'প্তৃ': 'ß„',
    'প্ন': 'cœ',
    'প্প': 'à',
    'প্র': 'cÖ',
    'প্রু': 'cÖæ',
    'প্রূ': 'cÖƒ',
    'প্ল': 'cø',
    'ফু': 'dz',
    'ফূ': 'd‚',
    'ফৃ': 'd…',
    'ফ্র': 'd«',
    'ফ্রু': 'd«z',
    'ফ্ল': 'd¬',
    'ফ্লু': 'd¬z',
    'ফ্লূ': 'd¬‚',
    'ফ্লৃ': 'd¬„',
    'ব্জ': 'â',
    'ব্দ': 'ã',
    'ব্ধ': 'ä',
    'ব্ধু': 'äz',
    'ব্ধূ': 'ä~',
    'ব্ধৃ': 'ä„',
    'ব্ব': 'eŸ',
    'ব্রু': 'eªæ',
    'ব্রূ': 'eªƒ',
    'ব্ল': 'eø',
    'ভ্র': 'å',
    'ভ্রু': 'åæ',
    'ভ্রূ': 'åƒ',
    'ভ্ল': 'fø',
    'ম্ন': 'gœ',
    'ম্প': '¤ú',
    'ম্প্ল': '¤úø',
    'ম্ফ': 'ç',
    'ম্ফু': 'çz',
    'ম্ফূ': 'ç‚',
    'ম্ফৃ': 'ç…',
    'ম্ব': '¤^',
    'ম্ভ': '¤¢',
    'ম্ভ্র': '¤£',
    'ম্ম': '¤§',
    'ম্র': 'gª',
    'ম্ল': '¤ø',
    'রু': 'iæ',
    'রূ': 'iƒ',
    'ল্ক': 'é',
    'ল্কু': 'éz',
    'ল্কূ': 'é‚',
    'ল্কৃ': 'é…',
    'ল্গ': 'ê',
    'ল্ড': 'ì',
    'ল্প': 'í',
    'ল্ফ্র': 'î«',
    'ল্ম': 'j¥',
    'ল্ল': 'jø',
    'শু': 'ï',
    'শ্চ': 'ð',
    'শ্ছ': 'ñ',
    'শ্ন': 'kœ',
    'শ্ব': 'k¦',
    'শ্ম': 'k¥',
    'শ্র': 'kª',
    'শ্রু': 'kÖæ',
    'শ্রূ': 'kªƒ',
    'শ্ল': 'kø',
    'ষ্ক': '®‹',
    'ষ্কু': '®‹z',
    'ষ্কূ': '®‹‚',
    'ষ্কৃ': '®‹…',
    'ষ্ক্র': '®Œ',
    'ষ্ক্রু': '®Œz',
    'ষ্ক্রূ': '®Œ‚',
    'ষ্ক্রৃ': '®Œ„',
    'ষ্ট': 'ó',
    'ষ্টু': 'óz',
    'ষ্টূ': 'ó‚',
    'ষ্টৃ': 'ó…',
    'ষ্ঠ': 'ô',
    'ষ্ঠু': 'ôz',
    'ষ্ঠূ': 'ô‚',
    'ষ্ঠৃ': 'ô…',
    'ষ্ফ': 'õ',
    'ষ্ফু': 'õz',
    'ষ্ফূ': 'õ‚',
    'ষ্ফৃ': 'õ…',
    'স্ক': '¯‹',
    'স্কু': '¯‹z',
    'স্কূ': '¯‹‚',
    'স্কৃ': '¯‹…',
    'স্ক্র': '¯Œ',
    'স্ক্রু': '¯Œz',
    'স্ক্রূ': '¯Œ‚',
    'স্ক্রৃ': '¯Œ…',
    'স্ক্ল': '¯‹¬',
    'স্খ': 'ö',
    'স্ট': '÷',
    'স্ত': '¯Í',
    'স্তু': '¯‘',
    'স্তূ': '¯Í‚',
    'স্তৃ': '¯Í…',
    'স্ত্ব': '¯Í¡',
    'স্থ': '¯’',
    'স্ন': 'mœ',
    'স্প': '¯ú',
    'স্প্ল': '¯úø',
    'স্ফ': 'ù',
    'স্ফু': 'ùz',
    'স্ফূ': 'ù‚',
    'স্ফৃ': 'ù…',
    'স্ব': '¯^',
    'স্ম': '¯§',
    'স্ল': '¯ø',
    'হু': 'û',
    'হৃ': 'ü',
    'হ্ণ': 'nè',
    'হ্ন': 'ý',
    'হ্ব': 'nŸ',
    'হ্ম': 'þ',
    'হ্মু': 'þz',
    'হ্মূ': 'þ~',
    'হ্মৃ': 'þ„',
    'হ্র': 'n«',
    'হ্ল': 'n¬',
}

# ----------------------------------------------------------------------------
# 1.  INVENTORY  (Bijoy character -> Unicode)
# ----------------------------------------------------------------------------
SINGLE = {  # unicode codepoint : bijoy char (Windows-1252 character whose cmap slot holds the glyph)
    0x0985: 'A', 0x0987: 'B', 0x0988: 'C', 0x0989: 'D', 0x098A: 'E', 0x098B: 'F',
    0x098F: 'G', 0x0990: 'H', 0x0993: 'I', 0x0994: 'J',
    0x0995: 'K', 0x0996: 'L', 0x0997: 'M', 0x0998: 'N', 0x0999: 'O', 0x099A: 'P',
    0x099B: 'Q', 0x099C: 'R', 0x099D: 'S', 0x099E: 'T', 0x099F: 'U', 0x09A0: 'V',
    0x09A1: 'W', 0x09A2: 'X', 0x09A3: 'Y', 0x09A4: 'Z', 0x09A5: '_', 0x09A6: '`',
    0x09A7: 'a', 0x09A8: 'b', 0x09AA: 'c', 0x09AB: 'd', 0x09AC: 'e', 0x09AD: 'f',
    0x09AE: 'g', 0x09AF: 'h', 0x09B0: 'i', 0x09B2: 'j', 0x09B6: 'k', 0x09B7: 'l',
    0x09B8: 'm', 0x09B9: 'n', 0x09DC: 'o', 0x09DD: 'p', 0x09DF: 'q', 0x09CE: 'r',
    0x0982: 's', 0x0983: 't', 0x0981: 'u',
    0x09BE: 'v',            # া
    0x09BF: 'w',            # ি  (pre-base, reordered by the shaper / by the font)
    0x09C0: 'x',            # ী
    0x09C1: 'z',            # ু  (Bijoy's usual form; 'y' is the alternate)
    0x09C2: '\u201a',       # ূ  (‚ 0x82; '~' is the alternate)
    0x09C3: '\u2026',       # ৃ  (… 0x85; „ 0x84 is the alternate)
    0x09C7: '\u2020',       # ে  († 0x86 = word-initial form; ‡ 0x87 = mid-word form)
    0x09C8: '\u02c6',       # ৈ  (ˆ = word-initial form; ‰ = mid-word form)
    0x09D7: '\u0160',       # ৗ
    0x09CD: '&',            # ্  hasant
    0x0964: '|',            # ।
    0x0965: '\\',           # ॥
    0x09F3: '$',            # ৳
    0x2018: '\u00d4', 0x2019: '\u00d5', 0x201C: '\u00d2', 0x201D: '\u00d3',
    0x2013: '\u00d1', 0x2014: '\u00d1',     # dash
}
for i in range(10):
    SINGLE[0x09E6 + i] = str(i)
PUNCT = " !\"#%'()*+,-./:;<=>?@[]{}"
for ch in PUNCT:
    SINGLE[ord(ch)] = ch
SINGLE[0x00A0] = ' '

HALF = {  # consonant : half-form glyph used before an ordinary full consonant
    0x09A8: '\u203a', 0x09A6: '\u02dc', 0x09AE: '\u00a4', 0x09B7: '\u00ae',
    0x09B8: '\u00af', 0x0999: '\u2022', 0x099A: '\u201d',
}
PHALA_YA = '\u00a8'
PHALA_RA = ['\u00aa', '\u00ab', '\u00d6']        # ª « Ö
PHALA_BA = ['\u00a1', '\u00a6', '^']             # ¡ ¦ ^
PHALA_BA_SP = '\u0178'                           # Ÿ
PHALA_MA = '\u00a5'
PHALA_LA = ['\u00ac', '\u00f8']                  # ¬ ø
PHALA_NA = '\u0153'                              # œ
PHALA_NNA = '\u00e8'                             # è
REPH = '\u00a9'
UKAR_ALT, UUKAR_ALT, RKAR_ALT = 'y', '~', '\u201e'
EKAR_MID, AIKAR_MID = '\u2021', '\u2030'
RA_U, RA_UU = '\u00e6', '\u0192'

# legacy conjunct tables (verified visually earlier) -- TRUTH below overrides them
CONJ_SINGLE = {
    '°': 'ক্ক', '±': 'ক্ট', '²': 'ক্ষ্ম', '³': 'ক্ত', 'µ': 'ক্র', '¶': 'ক্ষ', '·': 'ক্স',
    'º': 'গ্দ', '»': 'গ্ধ', '¼': 'ঙ্ক', '½': 'ঙ্গ',
    '¾': 'জ্জ', 'À': 'জ্ঝ', 'Á': 'জ্ঞ', 'Â': 'ঞ্চ', 'Ã': 'ঞ্ছ', 'Ä': 'ঞ্জ', 'Å': 'ঞ্ঝ',
    'Æ': 'ট্ট', 'Ç': 'ড্ড', 'È': 'ণ্ট', 'É': 'ণ্ঠ', 'Ð': 'ণ্ড',
    'Ë': 'ত্ত', 'Ì': 'ত্থ', 'Î': 'ত্র', 'Ï': 'দ্দ', '×': 'দ্ধ', 'Ø': 'দ্ব', 'Ù': 'দ্ম',
    'Ú': 'ন্ঠ', 'Û': 'ন্ড', 'Ü': 'ন্ধ', 'Ý': 'ন্স',
    'Þ': 'প্ট', 'ß': 'প্ত', 'à': 'প্প', 'á': 'প্স',
    'â': 'ব্জ', 'ã': 'ব্দ', 'ä': 'ব্ধ', 'å': 'ভ্র', 'ç': 'ম্ফ',
    'é': 'ল্ক', 'ê': 'ল্গ', 'ë': 'ল্ট', 'ì': 'ল্ড', 'í': 'ল্প', 'î': 'ল্ফ',
    'ð': 'শ্চ', 'ñ': 'শ্ছ', 'ò': 'ষ্ণ', 'ó': 'ষ্ট', 'ô': 'ষ্ঠ', 'õ': 'ষ্ফ',
    '÷': 'স্ট', 'ö': 'স্খ', 'ù': 'স্ফ', 'ý': 'হ্ন', 'þ': 'হ্ম',
    '¸': 'গু', 'ï': 'শু', 'û': 'হু', 'ü': 'হৃ', '´': 'ক্ম',
}
CONJ_RUN = {
    '¯Œ': 'স্ক্র', '®‹': 'ষ্ক', '®Œ': 'ষ্ক্র', '¯‹': 'স্ক',
    '•¶': 'ঙ্ক্ষ', '•L': 'ঙ্খ', '•N': 'ঙ্ঘ',
    '”P': 'চ্চ', '”Q': 'চ্ছ', '”Q¡': 'চ্ছ্ব', '”T': 'চ্ঞ',
    '¾¡': 'জ্জ্ব', 'R¡': 'জ্ব', 'U¡': 'ট্ব', 'U¥': 'ট্ম', 'K¡': 'ক্ব', 'K¬': 'ক্ল',
    'Mœ': 'গ্ন', 'M¥': 'গ্ম',
    'Y^': 'ণ্ব', 'Ë¡': 'ত্ত্ব', 'Z¥': 'ত্ম', 'Z¡': 'ত্ব', '_¡': 'থ্ব',
    '˜M': 'দ্গ', '˜N': 'দ্ঘ', '˜¡': 'দ্ব', '™¢': 'দ্ভ',
    'aŸ': 'ধ্ব', 'a¥': 'ধ্ম',
    '›U': 'ন্ট', 'šÍ': 'ন্ত', 'š¿': 'ন্ত্র', '›`': 'ন্দ', '›Ø': 'ন্দ্ব',
    'bœ': 'ন্ন', 'š^': 'ন্ব', 'b¥': 'ন্ম',
    'cœ': 'প্ন', 'cø': 'প্ল', 'd¬': 'ফ্ল', 'eŸ': 'ব্ব', 'gœ': 'ম্ন',
    '¤ú': 'ম্প', '¤^': 'ম্ব', '¤¢': 'ম্ভ', '¤£': 'ম্ভ্র', '¤§': 'ম্ম',
    'j¦': 'ল্ব', 'j¥': 'ল্ম', 'jø': 'ল্ল',
    'kœ': 'শ্ন', 'kø': 'শ্ল', 'k¦': 'শ্ব', 'k¥': 'শ্ম',
    '®ú': 'ষ্প', '®§': 'ষ্ম',
    '¯Í': 'স্ত', '¯¿': 'স্ত্র', '¯’': 'স্থ', 'mœ': 'স্ন', '¯ú': 'স্প', '¯^': 'স্ব', '¯§': 'স্ম',
    'nè': 'হ্ণ', 'n¬': 'হ্ল', '¶è': 'ক্ষ্ণ', '•³': 'ঙ্ক্ত',
    'l¦': 'ষ্ব', 'Ï¡': 'দ্দ্ব', 'ò¡': 'ষ্ণ্ব',
}
COMPOSITE_LETTERS = {0x0986: 'Av'}      # আ = A + া
HASANT, ZWNJ, ZWJ, NUKTA, DOTTED_CIRCLE = 0x09CD, 0x200C, 0x200D, 0x09BC, 0x25CC
CHANDRA = 0x0981
POST_MATRAS = [0x09BE, 0x09C0, 0x09C1, 0x09C2, 0x09C3, 0x09CB, 0x09CC, 0x09D7]

# ----------------------------------------------------------------------------
font = TTFont(SRC)
cm = font.getBestCmap()
glyf, hmtx = font['glyf'], font['hmtx']
src_order = list(font.getGlyphOrder())
SC = font['head'].unitsPerEm / 1000.0   # 1.178 for the current SutonnyMJ

def sg(ch):
    return cm[ord(ch)]
def uname(cp):
    return "uni%04X" % cp
def useq_name(s):
    return "_".join(uname(ord(c)) for c in s)

# corrections taken from the user's "SutonnyMJ corrected form" PDF (they win over the guide table)
#TRUTH['হ্র'] = 'nª'
#TRUTH['ন্থ'] = 'b’'
# unit table  unicode-string -> run of Bijoy chars
UNITS = {}
for ch, u in CONJ_SINGLE.items():
    UNITS[u] = ch
for run, u in CONJ_RUN.items():
    UNITS.setdefault(u, run)
UNITS.update(TRUTH)                       # ground truth from the Bijoy guide wins
UNITS = {u: g for u, g in UNITS.items() if len(u) > 1}

# ---- v16: conjunct + ু ূ ৃ  (MJ typists attach the matra to the LAST full consonant of the conjunct) ----
_BJ = dict(zip("কখগঘঙচছজঝঞটঠডঢণতথদধনপফবভমযরলশষসহড়ঢ়য়ৎ".replace("ড়","ড়").replace("ঢ়","ঢ়"), ""))
_BJ = {'ক':'K','খ':'L','গ':'M','ঘ':'N','ঙ':'O','চ':'P','ছ':'Q','জ':'R','ঝ':'S','ঞ':'T','ট':'U','ঠ':'V','ড':'W','ঢ':'X',
       'ণ':'Y','ত':'Z','থ':'_','দ':'`','ধ':'a','ন':'b','প':'c','ফ':'d','ব':'e','ভ':'f','ম':'g','য':'h','র':'i','ল':'j',
       'শ':'k','ষ':'l','স':'m','হ':'n'}
_ZS = {chr(c) for c in (0x0995,0x0999,0x099A,0x099B,0x099D,0x099E,0x099F,0x09A0,0x09A1,0x09A2,0x09A4,0x09AB)}
_MZ = {'\u09C1': ('z','y'), '\u09C2': ('\u201a','~'), '\u09C3': ('\u2026','\u201e')}
_NEWU = {}
# v16: the guide table is not reliable for ূ/ৃ(/ু) after conjuncts ending in z-type consonants
#      (user's real SutonnyMJ: ঞ্চূ = Â‚, not Â~).  Follow the consonant rule for those entries.
_Y2Z = {'y': 'z', '~': '\u201a', '\u201e': '\u2026'}
_FLIP = 0
for _u, _g in list(UNITS.items()):
    if len(_u) >= 4 and _u[-1] in _MZ and _u[-2] in _ZS and _u[-3] == '\u09CD' and _g[-1:] in _Y2Z:
        UNITS[_u] = _g[:-1] + _Y2Z[_g[-1]]; _FLIP += 1
print("v16: flipped %d guide entries to the z-family" % _FLIP)
for _u, _g in list(UNITS.items()):
    _c = _u[-1]
    if _c not in _BJ or _u[-2:-1] != '\u09CD' and False: continue
    if len(_u) < 3 or _u[-2] != '\u09CD' : continue
    if _g[-1:] == '\u00fa': _g = _g[:-1] + 'c'      # MJ uses the full প (not the ligature-final ú) when a vowel sign follows
    _endc = _g[-1:] == _BJ[_c]
    for _m, (_zv, _yv) in _MZ.items():
        if _u + _m in UNITS or _u + _m in TRUTH: continue
        _sp = TRUTH.get(_c + _m)
        if _sp is not None and len(_sp) == 1 and _endc:
            _NEWU[_u + _m] = _g[:-1] + _sp
        elif _c == '\u09B0' and _m != '\u09C3':
            _NEWU[_u + _m] = _g + ('\u00e6' if _m == '\u09C1' else '\u0192')
        else:
            _NEWU[_u + _m] = _g + (_zv if (_c in _ZS or _g[-1:] in '\u2019\u00a2') else _yv)
# দ্ + consonant + ু ূ ৃ : MJ uses the narrow half-দ (™) -- except দ্গৃ which keeps the normal half (˜)
_DNOPHALA = [c for c in _BJ if c not in 'রবমলনযণ']
for _c in _DNOPHALA:
    if ('\u09A6\u09CD' + _c) in UNITS and UNITS['\u09A6\u09CD' + _c][:1] != '\u02dc': continue
    for _m, (_zv, _yv) in _MZ.items():
        _k = '\u09A6\u09CD' + _c + _m
        if _k in UNITS or _k in TRUTH: continue
        _sp = TRUTH.get(_c + _m)
        _tail = _sp if (_sp is not None and len(_sp) == 1) else _BJ[_c] + (_zv if (_c in _ZS or _g[-1:] in '\u2019\u00a2') else _yv)
        _NEWU[_k] = ('\u02dc' if (_c == '\u0997' and _m == '\u09C3') else '\u2122') + _tail
UNITS.update(_NEWU)
print("v16: added %d conjunct+matra units" % len(_NEWU))

# ----------------------------------------------------------------------------
# 2.  rename glyphs
# ----------------------------------------------------------------------------
rename = {}
def claim(old, new):
    if old not in rename and new not in rename.values():
        rename[old] = new

for cp, ch in SINGLE.items():
    if cp < 0x80 and ch in PUNCT:
        continue
    if cp == 0xA0 or cp == 0x2014:
        continue
    claim(sg(ch), uname(cp))
claim(sg(UKAR_ALT), "uni09C1.alt"); claim(sg(UUKAR_ALT), "uni09C2.alt"); claim(sg(RKAR_ALT), "uni09C3.alt")
claim(sg(EKAR_MID), "uni09C7.mid"); claim(sg(AIKAR_MID), "uni09C8.mid")
claim(sg(RA_U), "ra_u.special"); claim(sg(RA_UU), "ra_uu.special")
for cons, ch in HALF.items():
    claim(sg(ch), "half.%s" % uname(cons)[3:])
claim(sg(PHALA_YA), "phala.ya")
for i, ch in enumerate(PHALA_RA): claim(sg(ch), "phala.ra.%d" % (i + 1))
for i, ch in enumerate(PHALA_BA): claim(sg(ch), "phala.ba.%d" % (i + 1))
claim(sg(PHALA_BA_SP), "phala.ba.sp"); claim(sg(PHALA_MA), "phala.ma")
for i, ch in enumerate(PHALA_LA): claim(sg(ch), "phala.la.%d" % (i + 1))
claim(sg(PHALA_NA), "phala.na"); claim(sg(PHALA_NNA), "phala.nna"); claim(sg(REPH), "reph")
OTHER_HELPERS = {'\u00a2': 'phala.bha', '\u00a3': 'phala.bhra', '\u00fa': 'phala.pa', '\u00bf': 'phala.tra',
                 '\u00cd': 'phala.ta', '\u0152': 'half.kra', '\u2039': 'phala.ka', '\u2019': 'phala.tha',
                 '\u2018': 'phala.tu', '\u0161': 'half.na.alt', '\u2122': 'half.da.alt', '\u00a7': 'phala.ma.2',
                 '\u00ff': 'ksa.alt'}
for ch, nm in OTHER_HELPERS.items():
    claim(sg(ch), nm)
# single-glyph conjuncts take their Unicode name
for u in sorted(UNITS, key=len):
    g = UNITS[u]
    if len(g) == 1 and ord(g) in cm:
        claim(sg(g), useq_name(u))
for byte_ch in sorted(cm):
    gname = cm[byte_ch]
    if gname in rename or gname in ('.notdef', 'space'):
        continue
    if byte_ch < 0x80 and chr(byte_ch) in PUNCT:
        continue
    if gname in ('NULL', 'nonmarkingreturn'):
        continue
    rename[gname] = "bijoy_%04X" % byte_ch

def apply_rename(font, rename):
    glyf = font['glyf']; hmtx = font['hmtx']
    order = font.getGlyphOrder()
    new_order = [rename.get(g, g) for g in order]
    assert len(set(new_order)) == len(new_order), "duplicate glyph names"
    glyf.glyphs = {rename.get(k, k): v for k, v in glyf.glyphs.items()}
    hmtx.metrics = {rename.get(k, k): v for k, v in hmtx.metrics.items()}
    if 'hdmx' in font:
        font['hdmx'].hdmx = {p: {rename.get(k, k): w for k, w in d.items()} for p, d in font['hdmx'].hdmx.items()}
    if 'LTSH' in font:
        font['LTSH'].yPels = {rename.get(k, k): w for k, w in font['LTSH'].yPels.items()}
    font.setGlyphOrder(new_order)
    glyf.glyphOrder = new_order
orig_flags = font['head'].flags
apply_rename(font, rename)
def N(ch):
    g = cm[ord(ch)]
    return rename.get(g, g)

# ----------------------------------------------------------------------------
# 3.  new glyphs
# ----------------------------------------------------------------------------
glyf = font['glyf']; hmtx = font['hmtx']
NEW = []                    # new glyph names, creation order
EXP = {}                    # placeholder -> flattened list of simple glyph names
PARTS = {}                  # composite -> list of top-level parts (for hdmx)
def adv(name):
    return hmtx[name][0]
def add_glyph(name, glyph, advance, lsb=0):
    glyf.glyphs[name] = glyph
    hmtx.metrics[name] = (advance, lsb)
    NEW.append(name)
def flush_order():
    order = list(font.getGlyphOrder()) + [n for n in NEW if n not in set(font.getGlyphOrder())]
    font.setGlyphOrder(order); glyf.glyphOrder = order
def RUN(g):
    return EXP.get(g, [g])
def placeholder(name, run):
    gl_ = Glyph(); gl_.numberOfContours = 0
    add_glyph(name, gl_, 0, 0)
    EXP[name] = [x for p in run for x in RUN(p)]
    return name

runs_xy = {}
def make_composite(name, parts):
    """small number of real composites (half+reph, standalone ো ৌ আ, visible hasant ...)"""
    comps, x = [], 0
    for p in parts:
        extra = 0
        if isinstance(p, tuple): p, extra = p
        comps.append((p, x + extra)); x += adv(p)
    g = Glyph(); g.numberOfContours = -1; g.components = []
    for p, dx in comps:
        c = GlyphComponent(); c.glyphName = p; c.x, c.y = dx, 0
        c.flags = 0x0002 | 0x0004
        g.components.append(c)
    glyf.glyphs[name] = g
    hmtx.metrics[name] = (x, 0)
    NEW.append(name)
    PARTS[name] = [p if not isinstance(p, tuple) else p[0] for p in parts]
    return name

# ---- ligature units (explicit rows + legacy) ----
UNIT_GLYPH = {}              # unicode string -> glyph name (simple or placeholder)
for u, g in UNITS.items():
    names = [N(c) for c in g if ord(c) in cm]
    if len(names) != len(g):
        continue
    if len(names) == 1:
        UNIT_GLYPH[u] = names[0]
    else:
        UNIT_GLYPH[u] = placeholder(useq_name(u), names)

# ---- misc glyphs ----
gl_ = Glyph(); gl_.numberOfContours = 0
add_glyph("blank", gl_, 0, 0)
for cp in (ZWNJ, ZWJ):
    g0 = Glyph(); g0.numberOfContours = 0
    add_glyph(uname(cp), g0, 0, 0)
for nm in ("ph.rya", "ph.rzya", "ph.u_ya", "ph.uu_ya", "ph.r_ya", "ph.hu_ya", "ph.huu_ya", "ph.hr_ya"):
    gl_ = Glyph(); gl_.numberOfContours = 0
    add_glyph(nm, gl_, 0, 0)
make_composite("reph.pre", [N(REPH)])
make_composite("uni09CD.v", ['uni09CD'])               # visible hasant (after ZWNJ)
make_composite(uname(0x0986), [N('A'), N('v')])         # আ  (fallback outline; GSUB also expands it)
make_composite("uni09CB", [N('\u2020'), N('v')])        # standalone ো / ৌ  (cmap fallback)
make_composite("uni09CC", [N('\u2020'), N('\u0160')])

def contour_glyph(src_name, contour_index, dx=0):
    sgl = glyf[src_name]
    coords, ends, flags = sgl.getCoordinates(glyf)
    start = 0 if contour_index == 0 else ends[contour_index - 1] + 1
    end = ends[contour_index]
    pts = [(coords[i][0] + dx, coords[i][1]) for i in range(start, end + 1)]
    ng = Glyph(); ng.numberOfContours = 1
    ng.coordinates = GlyphCoordinates(pts)
    ng.flags = bytearray(flags[i] & 1 for i in range(start, end + 1))
    ng.endPtsOfContours = [len(pts) - 1]
    ng.program = ttProgram.Program(); ng.program.fromBytecode(b"")
    return ng
dot = contour_glyph(N('o'), 1, dx=round(-440 * SC))
dot.recalcBounds(glyf)
add_glyph(uname(NUKTA), dot, 0, dot.xMin)
pen = TTGlyphPen(None)
R, r, n_ = round(190 * SC), round(34 * SC), 12
for k in range(n_):
    a = 2 * math.pi * k / n_
    x0, y0 = 250 * SC + R * math.cos(a), 250 * SC + R * math.sin(a)
    pen.moveTo((round(x0 - r), round(y0 - r))); pen.lineTo((round(x0 - r), round(y0 + r)))
    pen.lineTo((round(x0 + r), round(y0 + r))); pen.lineTo((round(x0 + r), round(y0 - r))); pen.closePath()
dc = pen.glyph(); dc.recalcBounds(glyf)
add_glyph(uname(DOTTED_CIRCLE), dc, round(500 * SC), dc.xMin)

# ---- classes for the logical-order pipeline ----
cons_cps = [0x0995,0x0996,0x0997,0x0998,0x0999,0x099A,0x099B,0x099C,0x099D,0x099E,
            0x099F,0x09A0,0x09A1,0x09A2,0x09A3,0x09A4,0x09A5,0x09A6,0x09A7,0x09A8,
            0x09AA,0x09AB,0x09AC,0x09AD,0x09AE,0x09AF,0x09B0,0x09B2,0x09B6,0x09B7,
            0x09B8,0x09B9,0x09DC,0x09DD,0x09DF,0x09CE]
VOWEL_CPS = [0x0985,0x0986,0x0987,0x0988,0x0989,0x098A,0x098B,0x098F,0x0990,0x0993,0x0994]
FULL = [uname(c) for c in cons_cps] + list(UNIT_GLYPH.values()) + [uname(c) for c in VOWEL_CPS]
FULL = [x for x in dict.fromkeys(FULL) if x in glyf.glyphs]
HALFN = ["half.%s" % uname(c)[3:] for c in HALF]
REPH_SHIFT = round(380 * SC)
FULLR, HALFR = [], []
for f_ in FULL:
    FULLR.append(placeholder(f_ + ".r", RUN(f_) + [N(REPH)]))
for h_ in HALFN:
    make_composite(h_ + ".r", [h_, (N(REPH), REPH_SHIFT)]); HALFR.append(h_ + ".r")
FIRSTS = FULL + FULLR + HALFN + HALFR
PRE = {   # tag : pre-base vowel sign glyph
    "i":  N('w'),
    "es": N('\u2020'),          # ে/ো at the start of a word (†)
    "em": N('\u2021'),          # ে/ো inside a word (‡)
    "as": N('\u02c6'),          # ৈ at the start of a word (ˆ)
    "am": N('\u2030'),          # ৈ inside a word (‰)
}
for tag, mg in PRE.items():
    for f_ in FIRSTS:
        if f_ in HALFR:
            make_composite("%s.%s" % (f_, tag), [mg, f_])
        else:
            placeholder("%s.%s" % (f_, tag), [mg] + RUN(f_))
# chandrabindu-reorder placeholders
CB_PH = {}
for cp in POST_MATRAS:
    CB_PH[cp] = "ph.cb_%04X" % cp
    gl_ = Glyph(); gl_.numberOfContours = 0
    add_glyph(CB_PH[cp], gl_, 0, 0)

# ----------------------------------------------------------------------------
# 4.  cmap
# ----------------------------------------------------------------------------
newmap = {}
for cp, ch in SINGLE.items():
    newmap[cp] = 'space' if cp in (0x20, 0xA0) else N(ch)
newmap[0x20] = 'space'; newmap[0xA0] = 'space'
for cp in COMPOSITE_LETTERS: newmap[cp] = uname(cp)
newmap[0x09CB] = 'uni09CB'; newmap[0x09CC] = 'uni09CC'
newmap[ZWNJ] = uname(ZWNJ); newmap[ZWJ] = uname(ZWJ)
newmap[NUKTA] = uname(NUKTA); newmap[DOTTED_CIRCLE] = uname(DOTTED_CIRCLE)

# ----------------------------------------------------------------------------
# 3b. v16: Latin / English glyphs = Times New Roman outlines (path = 3rd argument)
# ----------------------------------------------------------------------------
TNR_PATH = sys.argv[3] if len(sys.argv) > 3 else None
TNR_NAME, TNR_HDMX = {}, {}
TNR_KERN = []
if TNR_PATH:
    from fontTools.pens.transformPen import TransformPen
    tnr = TTFont(TNR_PATH); tcm = tnr.getBestCmap(); tgs = tnr.getGlyphSet(); tH = tnr['hmtx']
    TS = font['head'].unitsPerEm / float(tnr['head'].unitsPerEm)
    KEEP_BN = set(range(0x0980, 0x0A00)) | {0x0964, 0x0965, 0x200C, 0x200D, 0x25CC}
    RANGES = [(0x20, 0x7E), (0xA0, 0x24F), (0x2B0, 0x2FF), (0x1E00, 0x1EFF), (0x2000, 0x206F), (0x2070, 0x209F),
              (0x20A0, 0x20BF), (0x2100, 0x214F), (0x2190, 0x21FF), (0x2200, 0x22FF), (0x25A0, 0x25FF), (0xFB00, 0xFB06)]
    for lo, hi in RANGES:
        for cp in range(lo, hi + 1):
            if cp in KEEP_BN or cp not in tcm: continue
            if 0x200B <= cp <= 0x200F or 0x2028 <= cp <= 0x202E or 0x2060 <= cp <= 0x206F: continue
            og = tcm[cp]; nm = "tnr." + og
            if og not in TNR_NAME:
                from fontTools.pens.recordingPen import DecomposingRecordingPen
                rp = DecomposingRecordingPen(tgs); tgs[og].draw(rp)
                pen = TTGlyphPen(None)
                rp.replay(TransformPen(pen, (TS, 0, 0, TS, 0, 0)))
                g_ = pen.glyph()
                if g_.numberOfContours > 0: g_.coordinates.toInt()
                g_.recalcBounds(glyf)
                lsb_ = g_.xMin if g_.numberOfContours > 0 else 0
                add_glyph(nm, g_, int(round(tH[og][0] * TS)), int(lsb_))
                TNR_NAME[og] = nm
            newmap_tnr = globals().setdefault('newmap_tnr', {})
            newmap_tnr[cp] = TNR_NAME[og]
    if 'hdmx' in tnr:
        TNR_HDMX = tnr['hdmx'].hdmx
    # kerning (GPOS 'kern' pair adjustments, restricted to Basic Latin + Latin-1)
    kset = {tcm[c] for c in range(0x20, 0x100) if c in tcm and c not in (0x7F,) and not 0x80 <= c <= 0x9F}
    gp = tnr['GPOS'].table
    kl = []
    for fr in gp.FeatureList.FeatureRecord:
        if fr.FeatureTag == 'kern':
            for li in fr.Feature.LookupListIndex:
                if li not in kl: kl.append(li)
    pairs = {}
    for li in kl:
        lk = gp.LookupList.Lookup[li]
        subs = [st.ExtSubTable if lk.LookupType == 9 else st for st in lk.SubTable]
        done = set()
        for st in subs:
            if st.LookupType != 2 if hasattr(st, 'LookupType') else False: continue
            cov = [x for x in st.Coverage.glyphs if x in kset]
            if st.Format == 1:
                for a in cov:
                    ps = st.PairSet[st.Coverage.glyphs.index(a)]
                    for r in ps.PairValueRecord:
                        if r.SecondGlyph in kset and (a, r.SecondGlyph) not in done:
                            done.add((a, r.SecondGlyph))
                            v = getattr(r.Value1, 'XAdvance', 0) if r.Value1 else 0
                            if v: pairs[(a, r.SecondGlyph)] = pairs.get((a, r.SecondGlyph), 0) + v
            elif st.Format == 2:
                cd1 = st.ClassDef1.classDefs; cd2 = st.ClassDef2.classDefs
                for a in cov:
                    c1 = cd1.get(a, 0)
                    for b in kset:
                        if (a, b) in done: continue
                        done.add((a, b))
                        rec = st.Class1Record[c1].Class2Record[cd2.get(b, 0)]
                        v = getattr(rec.Value1, 'XAdvance', 0) if rec.Value1 else 0
                        if v: pairs[(a, b)] = pairs.get((a, b), 0) + v
    TNR_KERN = [("tnr." + a, "tnr." + b, int(round(v * TS))) for (a, b), v in sorted(pairs.items()) if round(v * TS) != 0 and a in TNR_NAME and b in TNR_NAME]
    print("v16: %d Times New Roman glyphs, %d kerning pairs" % (len(TNR_NAME), len(TNR_KERN)))
_old_by_cp = {cp: newmap[cp] for cp in globals().get('newmap_tnr', {}) if cp in newmap}
newmap.update(globals().get('newmap_tnr', {}))
flush_order()
cmap_tab = newTable("cmap"); cmap_tab.tableVersion = 0; cmap_tab.tables = []
for plat, enc in ((3, 1), (0, 3)):
    t = cmap_format_4(4); t.platformID, t.platEncID, t.language = plat, enc, 0
    t.cmap = dict(newmap); cmap_tab.tables.append(t)
font['cmap'] = cmap_tab

# ----------------------------------------------------------------------------
# 5.  GSUB -- two pipelines separated by script tag
#     bng2/beng : Bengali shaping engines.   DFLT/latn : plain OpenType engines.
# ----------------------------------------------------------------------------
def gl(cp): return uname(cp)
U = lambda s_: [gl(ord(c)) for c in s_]
H_ = gl(HASANT)
fea = ["languagesystem DFLT dflt;\nlanguagesystem latn dflt;\nlanguagesystem bng2 dflt;\nlanguagesystem beng dflt;\n"]

# ---- classes ----
def cls(name, glyphs):
    glyphs = [g for g in dict.fromkeys(glyphs) if g in glyf.glyphs]
    return "@%s = [%s];\n" % (name, " ".join(glyphs)) if glyphs else "@%s = [.notdef];\n" % name

# variant classes derived from the guide's own rows
import collections
def observe(variants):
    obs = collections.defaultdict(set)
    for u, g in TRUTH.items():
        for i, c in enumerate(g):
            if c in variants and i > 0:
                obs[g[i - 1]].add(c)
    return obs
def classify(variants, default):
    obs = observe(variants)
    out = collections.defaultdict(list)
    for base, vs in obs.items():
        if len(vs) == 1 and ord(base) in cm and not (base in HALF.values()):
            v = next(iter(vs))
            if v != default:
                out[v].append(N(base))
    return out
RAc = classify(PHALA_RA, PHALA_RA[0]); BAc = classify(PHALA_BA + [PHALA_BA_SP], PHALA_BA[0])
LAc = classify(PHALA_LA, PHALA_LA[0]); NAc = classify([PHALA_NA, PHALA_NNA], PHALA_NA)
cls_txt = ""
var_rules = []
def add_var(cname, bases, default_glyph, new_glyph):
    global cls_txt
    if not bases: return
    cls_txt += cls(cname, bases)
    var_rules.append("    sub @%s %s' by %s;" % (cname, default_glyph, new_glyph))
    var_rules.append("    sub @%s reph %s' by %s;" % (cname, default_glyph, new_glyph))
add_var("RA2B", RAc.get('\u00ab', []), "phala.ra.1", "phala.ra.2")
add_var("RA3B", RAc.get('\u00d6', []), "phala.ra.1", "phala.ra.3")
add_var("BA2B", BAc.get('\u00a6', []), "phala.ba.1", "phala.ba.2")
add_var("BASB", BAc.get('\u0178', []), "phala.ba.1", "phala.ba.sp")
_la_obs = observe(PHALA_LA)
_la_keep = {N(b) for b, vs in _la_obs.items() if vs == {PHALA_LA[0]} and ord(b) in cm} | {N('K'), N('d'), N('n')}   # ক ফ হ keep ¬
_la_all = set(LAc.get('\u00f8', [])) | {uname(c) for c in cons_cps if c != 0x09CE}
add_var("LA2B", sorted(_la_all - _la_keep), "phala.la.1", "phala.la.2")      # v16: every other base uses ø (e.g. গ্ল)
add_var("NAEB", NAc.get('\u00e8', []), "phala.na", "phala.nna")
_obsNA = observe([PHALA_NA, PHALA_NNA])
NNA_OE = [N(b) for b, vs in _obsNA.items() if vs == {PHALA_NA} and ord(b) in cm and b not in HALF.values()]
add_var("NNAB", NNA_OE, "phala.nna", "phala.na")
RAEND = ["phala.ra.1", "phala.ra.3", N('\u00ce'), N('\u00e5')]   # ু ূ take  æ ƒ  after these
cls_txt += cls("RAEND", RAEND)
MARKG = ["phala.ya", "phala.ra.1", "phala.ra.2", "phala.ra.3", "phala.ba.1", "phala.ba.2", "phala.ba.3",
         "phala.ba.sp", "phala.nna", "phala.ma", "phala.la.1", "phala.la.2", "phala.na", "phala.ma.2"]
cls_txt += cls("MARKG", MARKG) + cls("MARKR", ["reph"] + MARKG)
cls_txt += cls("HALFG", HALFN) + cls("FULLG", FULL)
cls_txt += cls("HALFALL", HALFN + HALFR) + cls("FULLALL", FULL + FULLR)
NONWORD = ['space'] + [cm[ord(c)] for c in PUNCT if c != ' '] + [uname(c) for c in (0x0964, 0x0965, 0x09F3, 0x2018, 0x2019,
           0x201C, 0x201D, 0x2013)]
NONWORD = [x for x in NONWORD if x in glyf.glyphs]
allnames = [g for g in font.getGlyphOrder() if g not in NONWORD and g not in ('.notdef', 'NULL', 'nonmarkingreturn', uname(ZWNJ), uname(ZWJ))]
allnames += [n for n in NEW if n not in allnames and n not in NONWORD]
cls_txt += cls("WORD", list(dict.fromkeys(allnames)))
fea.append(cls_txt)

# ---- lookups (definition order = index order) ----
# chandrabindu typed before a vowel sign (some layouts): put it after the sign
fea.append("lookup d_cb1 {\n" + "\n".join("    sub %s %s by %s;" % (gl(CHANDRA), gl(cp), CB_PH[cp]) for cp in POST_MATRAS) + "\n} d_cb1;\n")
fea.append("lookup d_cb2 {\n" + "\n".join("    sub %s by %s %s;" % (CB_PH[cp], gl(cp), gl(CHANDRA)) for cp in POST_MATRAS) + "\n} d_cb2;\n")
# ো ৌ (precomposed or typed as ে + া/ৗ)  -> ে + া/ৗ
fea.append("""lookup d_cc1 {
    sub uni09C7 uni09BE by uni09CB;
    sub uni09C7 uni09D7 by uni09CC;
} d_cc1;
lookup d_cc2 {
    sub uni09CB by uni09C7 uni09BE;
    sub uni09CC by uni09C7 uni09D7;
} d_cc2;
""")
# আ
fea.append("lookup aa_1 {\n    sub uni0986 by uni0985 uni09BE;\n} aa_1;\n")
# explicit hasant (hasant + ZWNJ): visible hasant that blocks conjunct formation
fea.append("lookup d_zwnj {\n    sub uni09CD uni200C by uni09CD.v;\n} d_zwnj;\n")
fea.append("lookup nukt_1 {\n    sub %s %s by %s;\n    sub %s %s by %s;\n    sub %s %s by %s;\n} nukt_1;\n" % (
    gl(0x09A1), gl(NUKTA), gl(0x09DC), gl(0x09A2), gl(NUKTA), gl(0x09DD), gl(0x09AF), gl(NUKTA), gl(0x09DF)))
# conjunct / consonant+sign ligatures from the ground truth (longest first is handled by feaLib)
# smart path: the shaper puts ু ূ ৃ before ্য ; Bijoy keeps Unicode order (্য first)
fea.append("""lookup pre_uya1 {
    sub uni09C1 uni09CD uni09AF by ph.hu_ya;
    sub uni09C2 uni09CD uni09AF by ph.huu_ya;
    sub uni09C3 uni09CD uni09AF by ph.hr_ya;
} pre_uya1;
lookup pre_uya2 {
    sub ph.hu_ya by uni09CD uni09AF uni09C1;
    sub ph.huu_ya by uni09CD uni09AF uni09C2;
    sub ph.hr_ya by uni09CD uni09AF uni09C3;
} pre_uya2;
""")
PHALA_CONS = [0x09B0, 0x09AC, 0x09AE, 0x09B2, 0x09A8, 0x09A3, 0x09AF]
XM = {u: gname for u, gname in UNIT_GLYPH.items() if len(u) == 2 and ord(u[0]) in PHALA_CONS}
fea.append("lookup akhn_1 {\n" + "\n".join("    sub %s by %s;" % (" ".join(U(u)), gname) for u, gname in UNIT_GLYPH.items() if u not in XM) + "\n} akhn_1;\n")
# consonant+vowel-sign rows for letters that can also be phala (র ব ম ল ন ণ য): never right after a hasant
fea.append("lookup lig_xm {\n" + "\n".join("    sub %s by %s;" % (" ".join(U(u)), gname) for u, gname in XM.items()) + "\n} lig_xm;\n")
fea.append("lookup akhn_x {\n" + "\n".join("    ignore sub uni09CD %s' %s';" % tuple(U(u)) for u in XM) + "\n" +
           "\n".join("    sub %s' lookup lig_xm %s';" % tuple(U(u)) for u in XM) + "\n} akhn_x;\n")
fea.append("""lookup d_rya1 {
    sub uni09CD uni09B0 uni09CD uni09AF by ph.rya;
    sub uni09B0 uni200D uni09CD uni09AF by ph.rzya;
} d_rya1;
lookup d_rya2 {
    sub ph.rya by phala.ra.1 phala.ya;
    sub ph.rzya by uni09B0 phala.ya;
} d_rya2;
lookup d_rphf {
    sub uni09B0 uni09CD by reph.pre;
} d_rphf;
lookup rphf_1 {
    sub uni09B0 uni09CD by reph;
} rphf_1;
""")
fea.append("""lookup blwf_1 {
    sub %(h)s %(ra)s by phala.ra.1;
    sub %(h)s %(ba)s by phala.ba.1;
    sub %(h)s %(ma)s by phala.ma;
    sub %(h)s %(la)s by phala.la.1;
    sub %(h)s %(na)s by phala.na;
    sub %(h)s %(nna)s by phala.nna;
} blwf_1;
lookup pstf_1 {
    sub %(h)s %(ya)s by phala.ya;
} pstf_1;
""" % dict(h=H_, ra=gl(0x09B0), ba=gl(0x09AC), ma=gl(0x09AE), la=gl(0x09B2), na=gl(0x09A8), nna=gl(0x09A3), ya=gl(0x09AF)))
fea.append("lookup half_1 {\n" + "\n".join("    sub %s %s by half.%s;" % (gl(c), H_, uname(c)[3:]) for c in HALF) + "\n} half_1;\n")
fea.append("""lookup blws_rau {
    sub @RAEND uni09C1' by ra_u.special;
    sub @RAEND uni09C2' by ra_uu.special;
} blws_rau;
""")
ZSET = [0x0995, 0x0999, 0x099A, 0x099B, 0x099D, 0x099E, 0x099F, 0x09A0, 0x09A1, 0x09A2, 0x09A4, 0x09AB, 0x09DC, 0x09DD]
YSET = [uname(c) for c in cons_cps if c not in ZSET and c != 0x09CE]
YSET = YSET + ["phala.ra.1","phala.ra.2","phala.ra.3","phala.ba.1","phala.ba.2","phala.ba.3","phala.ba.sp","phala.nna","phala.ma","phala.ma.2","phala.la.1","phala.la.2","phala.na"]
cls_txt2 = cls("YBASE", YSET)
fea.append(cls_txt2)
fea.append("""lookup blws_uy {
    sub @YBASE uni09C1' by uni09C1.alt;
    sub @YBASE uni09C2' by uni09C2.alt;
    sub @YBASE uni09C3' by uni09C3.alt;
} blws_uy;
""")
fea.append("lookup blws_var {\n" + "\n".join(var_rules) + "\n} blws_var;\n")
# placeholder expansion: the actual Bijoy glyph runs
fea.append("lookup exp_units {\n" + "\n".join("    sub %s by %s;" % (p, " ".join(EXP[p])) for p in UNIT_GLYPH.values() if p in EXP and ".r" not in p) + "\n} exp_units;\n")
# smart path: ে/ো/ৈ at the start of a word use † / ˆ, inside a word ‡ / ‰
# Word's Bengali engine runs lookups one syllable at a time, so a lookup can never see the previous
# syllable.  Therefore the mid-word forms (‡ ‰) are the default for every ে / ৈ.  Engines that do pass
# the whole run (HarfBuzz, LibreOffice, browsers) then restore the word-initial forms († ˆ) when the sign
# directly follows a space / punctuation.
fea.append(cls("NONW", NONWORD))
fea.append("lookup pres_e1 {\n    sub uni09C7 by uni09C7.mid;\n    sub uni09C8 by uni09C8.mid;\n} pres_e1;\n")
fea.append("lookup pres_e2 {\n    sub @NONW uni09C7.mid' by uni09C7;\n    sub @NONW uni09C8.mid' by uni09C8;\n} pres_e2;\n")
# dumb path : reph and pre-base signs
fea.append("lookup d_reph_h {\n" + "\n".join("    sub reph.pre %s by %s;" % (h_, h_ + ".r") for h_ in HALFN) + "\n} d_reph_h;\n")
fea.append("lookup d_reph_f {\n" + "\n".join("    sub reph.pre %s by %s;" % (f_, f_ + ".r") for f_ in FULL) + "\n} d_reph_f;\n")
for tag in PRE:
    fea.append("lookup d_sub_%s {\n" % tag + "\n".join("    sub %s by %s.%s;" % (f_, f_, tag) for f_ in FIRSTS) + "\n} d_sub_%s;\n" % tag)
fea.append("lookup d_blank {\n    sub uni09BF by blank;\n    sub uni09C7 by blank;\n    sub uni09C8 by blank;\n} d_blank;\n")
def chain_rules(tag, mg, backtrack=""):
    out = []
    for nh in range(0, 3):
        for nm in range(0, 4):
            first = "@HALFALL" if nh else "@FULLALL"
            mid = (" @HALFALL'" * (nh - 1) + " @FULLALL'") if nh else ""
            out.append("    sub %s%s' lookup d_sub_%s%s %s%s' lookup d_blank;" % (backtrack, first, tag, mid, "@MARKG' " * nm, mg))
    return out
chain = chain_rules("em", "uni09C7", "@WORD ") + chain_rules("es", "uni09C7") + \
        chain_rules("am", "uni09C8", "@WORD ") + chain_rules("as", "uni09C8") + chain_rules("i", "uni09BF")
fea.append("lookup d_pre {\n" + "\n".join(chain) + "\n} d_pre;\n")
fea.append("lookup exp_units_d {\n" + "\n".join("    sub %s by %s;" % (p, " ".join(EXP[p])) for p in UNIT_GLYPH.values() if p in EXP and ".r" not in p) + "\n} exp_units_d;\n")
fea.append("lookup exp_dumb {\n" + "\n".join("    sub %s by %s;" % (p, " ".join(EXP[p])) for p in EXP
           if (".r" in p or p.rsplit(".", 1)[-1] in PRE) and p not in UNIT_GLYPH.values()) + "\n} exp_dumb;\n")

SMART, DUMB = ["bng2", "beng"], ["DFLT", "latn"]
def feat(tag, lookups, scripts):
    body = ""
    for sc in scripts:
        body += "    script %s;\n    language dflt;\n" % sc
        body += "".join("    lookup %s;\n" % l for l in lookups)
    return "feature %s {\n%s} %s;\n" % (tag, body, tag)
fea.append(feat("nukt", ["nukt_1"], SMART))
fea.append(feat("akhn", ["pre_uya1", "pre_uya2", "akhn_1", "akhn_x"], SMART))
fea.append(feat("rphf", ["rphf_1"], SMART))
fea.append(feat("blwf", ["blwf_1"], SMART))
fea.append(feat("half", ["half_1"], SMART))
fea.append(feat("pstf", ["pstf_1"], SMART))
fea.append(feat("pres", ["pres_e1", "pres_e2"], SMART))
fea.append(feat("blws", ["blws_rau", "blws_uy", "blws_var", "exp_units"], SMART))
DUMB_LOOKUPS = ["dm_p", "d_cb1", "d_cb2", "d_cc1", "d_cc2", "aa_1", "d_zwnj", "nukt_1", "akhn_1", "akhn_x", "d_rya1", "d_rya2", "d_rphf",
                "blwf_1", "pstf_1", "half_1", "blws_rau", "blws_uy", "blws_var", "d_reph_h", "d_reph_f", "d_pre", "exp_units_d", "exp_dumb"]
def feat2(tag, smart_l, dumb_l):
    body = ""
    for sc in SMART:
        if smart_l:
            body += "    script %s;\n    language dflt;\n" % sc + "".join("    lookup %s;\n" % l for l in smart_l)
    for sc in DUMB:
        body += "    script %s;\n    language dflt;\n" % sc + "".join("    lookup %s;\n" % l for l in dumb_l)
    return "feature %s {\n%s} %s;\n" % (tag, body, tag)
for t_ in ("ccmp", "liga", "clig", "calt"):
    fea.append(feat2(t_, ["sm_p1", "sm_p2", "aa_1"] if t_ == "ccmp" else (["pres_e1", "pres_e2"] if t_ in ("calt","clig") else []), DUMB_LOOKUPS))
fea.append("lookup m_none {\n    pos uni09BC <0 0 0 0>;\n} m_none;\n")
if TNR_KERN:
    fea.append("lookup kern_tnr {\n" + "\n".join("    pos %s %s %d;" % p for p in TNR_KERN) + "\n} kern_tnr;\n")
    fea.append(feat("kern", ["kern_tnr"], SMART + DUMB))
fea.append(feat("mark", ["m_none"], SMART + DUMB))
fea.append(feat("mkmk", ["m_none"], SMART + DUMB))
# v16: Bengali text keeps the Sutonny punctuation / quotes / space; English keeps Times New Roman.
#   Bengali engines (bng2/beng):  Sutonny form, restored to Times New Roman after a Latin letter/digit.
#   Plain engines (DFLT/latn):    Times New Roman form, switched to the Sutonny form after a Bengali glyph.
_fwd = {}                                    # tnr glyph -> sutonny glyph
for _cp, _og in _old_by_cp.items():
    _t = newmap[_cp]
    if _t not in _fwd: _fwd[_t] = _og
_rev = {}
for _t, _o in _fwd.items():
    _rev.setdefault(_o, _t)
_allg = list(font.getGlyphOrder()) + [n for n in NEW if n not in set(font.getGlyphOrder())]
_tl = [g for g in _allg if g.startswith("tnr.") and g not in _fwd]
_bn = [g for g in _allg if not g.startswith("tnr.") and g != ".notdef"]
_pb = "@P_T = [%s];\n@P_S = [%s];\n" % (" ".join(_fwd.keys()), " ".join(_fwd.values()))
_pb += "@P_RS = [%s];\n@P_RT = [%s];\n" % (" ".join(_rev.keys()), " ".join(_rev.values()))
_pb += "@P_LAT = [%s];\n@P_BN = [%s];\n" % (" ".join(_tl + list(_rev.values())), " ".join(_bn))
_pb += "lookup sm_p1 {\n" + "\n".join("    sub %s by %s;" % kv for kv in _fwd.items()) + "\n} sm_p1;\n"
_pb += "lookup sm_p2 {\n    sub @P_LAT @P_RS' by @P_RT;\n} sm_p2;\n"
_pb += "lookup dm_p {\n    sub @P_BN @P_T' by @P_S;\n} dm_p;\n"
FEA_TEXT = _pb + "\n".join(fea)

# ----------------------------------------------------------------------------
# 6.  GDEF, hinting tables, finish
# ----------------------------------------------------------------------------
flush_order()
order = font.getGlyphOrder()
hm = font['hmtx']
marks = [g for g in order if hm[g][0] == 0 and g not in EXP and g != '.notdef' and glyf[g].numberOfContours != 0]
bases = [g for g in order if g not in marks and g not in ('.notdef', 'NULL', 'nonmarkingreturn')]
gdef = "table GDEF {\n  GlyphClassDef [%s], , [%s], ;\n} GDEF;\n" % (" ".join(bases), " ".join(marks))
addOpenTypeFeaturesFromString(font, FEA_TEXT + "\n" + gdef)

# hdmx / LTSH: keep the original device metrics; new glyphs get consistent values
order = font.getGlyphOrder()
if 'hdmx' in font:
    hd = font['hdmx'].hdmx
    for ppem, d in hd.items():
        for g in order:
            if g in d: continue
            if g in PARTS:
                d[g] = sum(d.get(p, round(adv(p) * ppem / 1000)) for p in PARTS[g])
            elif g in EXP:
                d[g] = 0
            elif g.startswith("tnr."):
                og = g[4:]
                d[g] = TNR_HDMX[ppem][og] if (ppem in TNR_HDMX and og in TNR_HDMX[ppem]) else round(adv(g) * ppem / font['head'].unitsPerEm)
            else:
                d[g] = round(adv(g) * ppem / 1000)
        for g in list(d):
            if g not in glyf.glyphs: del d[g]
if 'LTSH' in font:
    for g in order:
        font['LTSH'].yPels.setdefault(g, 1)
    for g in list(font['LTSH'].yPels):
        if g not in glyf.glyphs: del font['LTSH'].yPels[g]

for t in ('PCLT', 'kern'):
    if t in font: del font[t]
name = font['name']
FAMILY, STYLE = "SutonnyUMJ", (name.getDebugName(2) or "Regular")   # style follows the source SutonnyMJ file
name.names = [n for n in name.names if n.nameID not in (1, 2, 3, 4, 5, 6, 16, 17, 21, 22, 25)]
_VER = "Version 2.0(misrender complain email:taskiaayatbd@proton.me)"
_DESC = ("SutonnyUMJ %s's Bangla and English is a all in all font for writing in unicode in offical docs. "
         "Unicode adaptation of SutonnyMJ (Ananda Computers, designed by Mustafa Jabbar) with Times New Roman (Monotype) Latin glyphs; "
         "adapted by H. Abdullah, Jackfruit Corporation." % STYLE)
for nid, val in [(1, FAMILY), (2, STYLE), (3, "SutonnyUMJ %s v2;Unicode;2.0" % STYLE), (4, "SutonnyUMJ %s + Times New Roman" % STYLE),
                 (5, _VER), (6, "SutonnyUMJ-" + STYLE.replace(" ", "")), (10, _DESC), (11, "jackfruitcorporationltd.vendetta084@slmail.me")]:
    name.names = [n for n in name.names if n.nameID != nid]
    name.setName(val, nid, 3, 1, 0x409)
    name.setName(val, nid, 1, 0, 0)
font['head'].fontRevision = 2.0
hh = font['hhea']; _o = font['OS/2']
# MJ stores descent / typo-descender with the wrong sign (+200).  Unicode text paths (DirectWrite/Uniscribe)
# read them and clip every glyph part below the baseline.  Use the same cell as winAscent/winDescent.
hh.ascent, hh.descent, hh.lineGap = _o.usWinAscent, -_o.usWinDescent, 0
_o.sTypoAscender, _o.sTypoDescender, _o.sTypoLineGap = _o.usWinAscent, -_o.usWinDescent, 0
_o.version = max(_o.version, 4); _o.fsSelection |= (1 << 7)   # style bits (bold/italic/regular), weight and macStyle stay as in the source MJ file
os2 = font['OS/2']
keys = sorted(k for k in newmap if k <= 0xFFFF)
os2.usFirstCharIndex, os2.usLastCharIndex = keys[0], keys[-1]
os2.ulUnicodeRange1 = (1 << 0) | (1 << 9)
os2.ulUnicodeRange2 = os2.ulUnicodeRange3 = os2.ulUnicodeRange4 = 0
os2.ulCodePageRange1, os2.ulCodePageRange2 = 1, 0
font['post'].formatType = 2.0
font['post'].extraNames = []
font['post'].mapping = {}
font.save(OUT)
font = TTFont(OUT)
font['head'].flags = orig_flags            # same head flags as the original font
font.save(OUT)
print("saved", OUT, "glyphs:", len(font.getGlyphOrder()))
