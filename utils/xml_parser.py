# utils/xml_parser.py
"""
法令XMLを解析し、表示用のHTMLに変換するためのユーティリティ関数を提供します。
e-Gov法令APIから取得したXML形式の法令データを、目次と本文のHTMLに変換する機能を含みます。
"""

import re
import xml.etree.ElementTree as ET
from typing import Tuple, Optional

def kanji_to_number_string(kanji_str: str) -> str:
    """漢数字の文字列をアラビア数字の文字列に変換する。

    「千」「百」「十」を含む漢数字（例：「二百三十四」）を正しく処理する。

    Args:
        kanji_str (str): 変換対象の漢数字文字列。

    Returns:
        str: アラビア数字に変換された文字列。入力が空の場合は空文字列を返す。
    """
    if not kanji_str:
        return ""

    trans_map = str.maketrans('一二三四五六七八九〇', '1234567890')
    kanji_str = kanji_str.translate(trans_map)

    num = 0
    if '千' in kanji_str:
        parts = kanji_str.split('千')
        num += (int(parts[0]) if parts[0] else 1) * 1000
        kanji_str = parts[1]
    if '百' in kanji_str:
        parts = kanji_str.split('百')
        num += (int(parts[0]) if parts[0] else 1) * 100
        kanji_str = parts[1]
    if '十' in kanji_str:
        parts = kanji_str.split('十')
        num += (int(parts[0]) if parts[0] else 1) * 10
        kanji_str = parts[1]
    if kanji_str:
        num += int(kanji_str)

    return str(num)

def parse_law_xml_to_html(xml_text: str) -> Tuple[str, str]:
    """法令のXMLテキストを解析し、目次と本文のHTML文字列を生成する。

    e-Govの法令XMLの構造を解析し、見出し、条、項、号などを
    HTMLタグ（h1-h4, div, aなど）に変換して、ブラウザで表示可能な形式にする。
    アンカーリンク（<a name="...">）を埋め込み、特定の条項へのジャンプを可能にする。

    Args:
        xml_text (str): 解析対象の法令XMLデータ文字列。

    Returns:
        Tuple[str, str]: (目次HTML, 本文HTML) のタプル。
                         現在は目次HTMLは空文字列。
                         解析エラーが発生した場合は、本文HTMLにエラーメッセージが格納される。
    """
    try:
        root = ET.fromstring(xml_text)
        main_html = "<html><body style='line-height:1.6;'>"
        law_title = root.find(".//LawTitle")
        if law_title is not None and law_title.text:
            main_html += f"<h1>{law_title.text}</h1>"

        def get_text(element: Optional[ET.Element]) -> str:
            """XML要素からすべてのテキストコンテンツを結合して取得する。

            Args:
                element (Optional[ET.Element]): テキストを取得するXML要素。Noneも許容。

            Returns:
                str: 結合されたテキスト。要素がNoneの場合は空文字列。
            """
            return "".join(element.itertext()) if element is not None else ""

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
                    # 条文番号からアンカーを生成
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

                    # 項が複数ある場合は項番号を表示
                    if len(element.findall("Paragraph")) > 1:
                        main_html += f"<div style='margin-left: 1.5em; text-indent: -1.5em; padding-left: 0.5em;'><b>{p_idx}</b>&nbsp;"
                    else:
                        main_html += "<div style='margin-left: 1.5em;'>"
                    
                    sentence_elem = para.find("ParagraphSentence")
                    if sentence_elem is not None:
                        main_html += get_text(sentence_elem)

                    # 号の処理
                    for i_idx, item in enumerate(para.findall("Item"), 1):
                        item_anchor = f"{para_anchor}-{i_idx}" if para_anchor else ""
                        item_title_elem = item.find('ItemTitle')
                        item_sentence_elem = item.find('ItemSentence')

                        if item_title_elem is not None and item_sentence_elem is not None:
                            main_html += f"<a name='{item_anchor}'></a>"
                            main_html += (f"<div style='margin-left: 1.5em; text-indent: -1.5em; padding-left: 0.5em;'>"
                                          f"<b>({get_text(item_title_elem)})</b>&nbsp;{get_text(item_sentence_elem)}</div>")
                    main_html += "</div>"
        
        main_html += "</body></html>"
        # toc_htmlは現在未使用のため空文字列を返す
        return "", main_html
    except Exception as e:
        return "", f"<html><body><h1>法令解析失敗</h1><p>{e}</p></body></html>"