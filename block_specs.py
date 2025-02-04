"""Space Engineers block specifications for mass calculations."""

# Block masses in kg
BLOCK_MASSES = {
    # Armor blocks
    'light_armor_block': {
        'small': 25,
        'large': 1220
    },
    'heavy_armor_block': {
        'small': 87,
        'large': 4170
    },
    
    # Structural blocks
    'steel_plate': {
        'small': 20,
        'large': 980
    },
    'interior_plate': {
        'small': 3,
        'large': 120
    },
    
    # Functional blocks
    'cargo_container': {
        'small': 128,
        'large': 2175
    },
    'refinery': {
        'small': 2000,
        'large': 15400
    },
    'assembler': {
        'small': 1000,
        'large': 3360
    },
    'reactor': {
        'small': 368,
        'large': 4860
    }
}

def calculate_total_mass(block_counts: dict) -> float:
    """
    Calculate total mass based on block counts.
    
    Args:
        block_counts: Dictionary with block types as keys and tuple of (small_count, large_count) as values
        
    Returns:
        float: Total mass in kg
    """
    total_mass = 0.0
    
    for block_type, (small_count, large_count) in block_counts.items():
        if block_type in BLOCK_MASSES:
            block_specs = BLOCK_MASSES[block_type]
            total_mass += (small_count * block_specs['small']) + (large_count * block_specs['large'])
    
    return total_mass
