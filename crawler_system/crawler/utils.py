from difflib import SequenceMatcher
import re
from datetime import datetime

def is_similar(text1, text2, threshold = 0.75):
    #對比電影名稱，透過相似度判斷是不是同一部電影

    versions_to_remove = ["3d", "4dx", "2d", "imax", "數位版", "中文版", "英文版", "法語版", "劇場版", "電影版", "4K重映", "海報場", "特別場"]
    text1_clean = text1.lower()
    text2_clean = text2.lower()

    for v in versions_to_remove:
        text1_clean = text1_clean.replace(v, "")
        text2_clean = text2_clean.replace(v, "")

    #避免有集數不同問題
    nums1 = re.findall(r'\d+', text1_clean)
    nums2 = re.findall(r'\d+', text2_clean)
    if nums1 != nums2:
        return False
    
    sequel_keywords = ['ii', 'iii', 'iv', '第二', '第三', '最終', '續集', '前傳']
    has_seq1 = any(kw in text1_clean for kw in sequel_keywords)
    has_seq2 = any(kw in text2_clean for kw in sequel_keywords)
    if has_seq1 != has_seq2:
        return False
    
    ignore_chars = """：: -.,()[]「」『』【】《》<>，~～！!?？（）/&＆·・‧|｜—_'" """

    final_text1 = "".join([c for c in text1_clean if c not in ignore_chars])
    final_text2 = "".join([c for c in text2_clean if c not in ignore_chars])

    if final_text1 and final_text2:
        if final_text1 in final_text2 or final_text2 in final_text1:
            return True

    ratio = SequenceMatcher(None, final_text1, final_text2).ratio()

    if ratio >= threshold:
        return True
    else:
        return False
    
def get_now():
    """取得當下最新時間"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")