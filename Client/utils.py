import base64
import xmltodict
import json
import re
import xml.etree.ElementTree as ET
from typing import List

# Archivo con funciones de utilidad para el proyecto
# Funciones para convertir entre XML y JSON
def xml_to_json(xml_string: str) -> str:
    """
    Convierte una cadena XML en un objeto JSON.

    Args:
        xml_string (str): Cadena XML a convertir.

    Returns:
        str: Cadena JSON resultante.
    """
    try:
        wrapped_xml = f"<root>{xml_string}</root>"
        dict_data = xmltodict.parse(wrapped_xml, force_list=True)
        json_data = json.dumps(dict_data)

        print(f"Converted XML to JSON: {json_data}")
        return json_data
    except Exception as e:
        print(f"Error converting XML to JSON: {e}")
        return {}


# Funciones para limpiar XML
def clean_xml(xml_str):
    # Elimina etiquetas incompletas o mal formadas
    xml_str = re.sub(r'<item[^>]*<item[^>]*>', '<item', xml_str)  # Corrige etiquetas <item> mal cerradas
    xml_str = re.sub(r'<item\s+[^>]+?[^>]*<item[^>]*>', '<item', xml_str)  # Corrige etiquetas <item> mal anidadas
    xml_str = re.sub(r'(<item[^>]+?)(?!jid=|name=).*?>', r'\1>', xml_str)  # Elimina atributos innecesarios
    xml_str = re.sub(r'<item\s+[^>]+?/>', '<item/>', xml_str)  # Corrige etiquetas <item> auto-cerradas
    return xml_str

# Funciones para codificar base64
def encode_base64(data: str) -> str:
    """Encode a string to base64."""
    return base64.b64encode(data.encode('utf-8')).decode('utf-8')


# Funciones decodificar base64
def decode_base64(data: str) -> str:
    """Decode a base64 encoded string."""
    return base64.b64decode(data).decode('utf-8')


# Funciones para imprimir mensajes
def log_message(direction: str, message: str) -> None:
    """Log a sent or received XMPP message."""
    print(f"{direction}: {message}")


# Funciones para dividir mensajes XML
def split_xml_messages(xml_data: str):
    # Expresión regular para encontrar los mensajes
    message_pattern = re.compile(r'<message[^>]*>.*?</message>', re.DOTALL)
    messages = message_pattern.findall(xml_data)
    return messages


# Funciones para dividir mensajes de presencia
def split_presence_messages(xml_data: str) -> List[str]:
    presence_messages = []
    try:
        root = ET.fromstring(f'<root>{xml_data}</root>') 
        for presence in root.findall(".//presence"):
            presence_xml = ET.tostring(presence, encoding='unicode')
            presence_messages.append(presence_xml)
    except ET.ParseError as e:
        print(f"Error parsing XML data: {e}")
    return presence_messages


# Funciones para dividir mensajes IQ
def split_all_messages(xml_data: str) -> list:
    message_patterns = [
        r'<message[^>]*>.*?</message>',  # Mensajes de chat
        r'<iq[^>]*>.*?</iq>',            # Mensajes IQ
        r'<presence[^>]*>.*?</presence>' # Mensajes de presencia
    ]
    
    combined_pattern = '|'.join(message_patterns)
    all_messages = re.findall(combined_pattern, xml_data, re.DOTALL)
    return all_messages


# Funcion para parsear la respuesta de la lista de bookmarks (grupos de chat)
def parse_bookmarks_response(xml_string):
    root = ET.fromstring(xml_string)
    bookmarks = []
    
    for conference in root.findall(".//storage:conference", namespaces={"storage": "storage:bookmarks"}):
        group_jid = conference.attrib.get('jid')
        autojoin = conference.attrib.get('autojoin', 'false') == 'true'
        name = conference.attrib.get('name')
        
        nick_element = conference.find("storage:nick", namespaces={"storage": "storage:bookmarks"})
        nick = nick_element.text if nick_element is not None else None
        
        bookmarks.append({
            "name": name,
            "jid": group_jid,
            "autojoin": autojoin,
            "nick": nick
        })
    
    return bookmarks


# Funcion para dividir mensajes IQ
def split_iq_messages(xml_data: str) -> list:
    root = ET.fromstring(f"<root>{xml_data}</root>")
    iq_messages = []
    for iq in root.findall('.//iq'):
        iq_messages.append(ET.tostring(iq, encoding='unicode'))
    return iq_messages