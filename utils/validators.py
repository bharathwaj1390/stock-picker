"""
Input validation utilities.

Functions:
  is_valid_nse_symbol(symbol: str) -> bool
      Checks symbol ends with .NS and contains only valid characters.

  is_valid_date_range(start, end) -> bool
      Validates start < end and both are within sensible bounds.

  validate_filter_config(config: FilterConfig) -> list[str]
      Returns list of validation errors (empty if valid).
      Catches issues like min > max in range filters.
"""
