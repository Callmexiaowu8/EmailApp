import re

INLINE_IMAGE_RE = re.compile(r'^[0-9a-f]{32}\.(png|jpg|jpeg|gif)$', re.IGNORECASE)
