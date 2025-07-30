from django import template

register = template.Library()

@register.filter
def floatdiv(value, divisor):
    """Divide a value by a divisor and return as float"""
    try:
        return float(value) / float(divisor)
    except (ValueError, ZeroDivisionError, TypeError):
        return 0

@register.filter
def modulo(value, divisor):
    """Return the remainder of value divided by divisor"""
    try:
        return int(value) % int(divisor)
    except (ValueError, ZeroDivisionError, TypeError):
        return 0

@register.filter
def multiply(value, multiplier):
    """Multiply a value by a multiplier"""
    try:
        return float(value) * float(multiplier)
    except (ValueError, TypeError):
        return 0