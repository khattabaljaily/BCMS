from django import template

register = template.Library()


@register.filter
def format_number(value, decimal_places=2):
    """
    Format a number with comma as thousands separator and period as decimal separator.
    Format: 1,000.00
    
    Usage: {{ value|format_number:2 }}
    """
    try:
        if value is None or value == '':
            return '—'
        
        # Convert to float
        num = float(value)
        
        # Round to specified decimal places
        num = round(num, int(decimal_places))
        
        # Format with comma separator
        if decimal_places == 0:
            return f'{int(num):,}'
        else:
            # Use format specification
            formatted = f'{num:,.{int(decimal_places)}f}'
            return formatted
    except (ValueError, TypeError):
        return value
