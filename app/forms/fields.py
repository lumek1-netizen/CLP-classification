"""
Vlastní pole formulářů (Custom Fields).
"""
from wtforms import FloatField

class FlexibleFloatField(FloatField):
    """
    FloatField, který akceptuje jak tečku, tak čárku jako oddělovač desetinných míst.
    Před zpracováním nahradí čárku tečkou.
    """
    def process_formdata(self, valuelist):
        if valuelist:
            try:
                # Nahrazení čárky tečkou v prvním prvků seznamu
                valuelist[0] = valuelist[0].replace(',', '.')
            except (AttributeError, IndexError):
                pass # Necháme původní zpracování, pokud to není string nebo je list prázdný
        
        return super().process_formdata(valuelist)
