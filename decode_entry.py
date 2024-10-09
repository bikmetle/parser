import base64
import brotli


def decode_response_content(text):
    compressed_bytes = base64.b64decode(text)
    decompressed_bytes = brotli.decompress(compressed_bytes)
    original_data = decompressed_bytes.decode('utf-8')
    return original_data


# if entry['response']['content']['encoding'] == 'base64':
#     text_encoded = entry['response']['content']['text']
#     decoded_text = base64.b64decode(text_encoded).decode('utf-8')
#     entry['response']['content']['text'] = decoded_text