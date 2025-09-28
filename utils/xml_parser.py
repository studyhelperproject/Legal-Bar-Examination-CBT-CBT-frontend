# utils/xml_parser.py
import re
import xml.etree.ElementTree as ET

def kanji_to_number_string(kanji_str):
    if not kanji_str: return ""
    trans_map = str.maketrans('一二三四五六七八九〇', '1234567890')
    kanji_str = kanji_str.translate(trans_map)
    num = 0
    if '千' in kanji_str:
        parts = kanji_str.split('千'); num += (int(parts[0]) if parts[0] else 1) * 1000; kanji_str = parts[1]
    if '百' in kanji_str:
        parts = kanji_str.split('百'); num += (int(parts[0]) if parts[0] else 1) * 100; kanji_str = parts[1]
    if '十' in kanji_str:
        parts = kanji_str.split('十'); num += (int(parts[0]) if parts[0] else 1) * 10; kanji_str = parts[1]
    if kanji_str:
        num += int(kanji_str)
    return str(num)

def parse_law_xml_to_html(xml_text):
    try:
        root = ET.fromstring(xml_text)
        main_html = "<html><body style='line-height:1.6;'>"
        law_title = root.find(".//LawTitle")
        if law_title is not None:
            main_html += f"<h1>{law_title.text}</h1>"

        def get_text(e): return "".join(e.itertext()) if e is not None else ""

        for element in root.findall(".//*"):
            if element.tag in ["Part", "Chapter", "Section", "Subsection", "Division"]:
                num = element.attrib.get("Num")
                title_elem = element.find(f"./{element.tag}Title")
                if num and title_elem is not None:
                    main_html += f"<a name='{num}'></a>"
                    tag = {"Part": "h2", "Chapter": "h3", "Section": "h4"}.get(element.tag, "h4")
                    main_html += f"<{tag}>{get_text(title_elem)}</{tag}>"
            if element.tag == "Article":
                title_elem = element.find("ArticleTitle")
                article_anchor_num = ""
                sub_num = ""
                if title_elem is not None:
                    title_text = get_text(title_elem)
                    match = re.search(r'第([一二三四五六七八九〇十百千]+)条(?:の([一二三四五六七八九〇十百千]+))?', title_text)
                    if match:
                        main_num = kanji_to_number_string(match.group(1))
                        if match.group(2):
                            sub_num = kanji_to_number_string(match.group(2))
                        article_anchor_num = f"{main_num}-{sub_num}" if sub_num else main_num
                        main_html += f"<a name='article-{article_anchor_num}'></a>"
                    main_html += f"<h3 style='margin: 1em 0 0.5em 0;'>{title_text}</h3>"

                for p_idx, para in enumerate(element.findall("Paragraph"), 1):
                    para_anchor = f"article-{article_anchor_num}-{p_idx}" if article_anchor_num else ""
                    main_html += f"<a name='{para_anchor}'></a>"
                    if len(element.findall("Paragraph")) > 1:
                        main_html += f"<div style='margin-left: 1.5em; text-indent: -1.5em; padding-left: 0.5em;'><b>{p_idx}</b>&nbsp;"
                    else:
                        main_html += "<div style='margin-left: 1.5em;'>"
                    main_html += get_text(para.find("ParagraphSentence"))
                    
                    for i_idx, item in enumerate(para.findall("Item"), 1):
                        item_anchor = f"{para_anchor}-{i_idx}" if para_anchor else ""
                        main_html += f"<a name='{item_anchor}'></a>"
                        main_html += f"<div style='margin-left: 1.5em; text-indent: -1.5em; padding-left: 0.5em;'><b>({get_text(item.find('ItemTitle'))})</b>&nbsp;{get_text(item.find('ItemSentence'))}</div>"
                    main_html += "</div>"
        
        main_html += "</body></html>"
        return "", main_html # toc_html is not used, so return empty string
    except Exception as e:
        return "", f"法令解析失敗: {e}"