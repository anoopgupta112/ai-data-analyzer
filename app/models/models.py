from typing import List, Dict, Any

class FormDefinition:
    def __init__(self, fields: List[Dict[str, Any]]):
        self.fields = fields
        self.submissions = []
