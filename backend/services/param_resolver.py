"""
Parameter Resolution Service

Resolves generation parameters from style + quality profile + extra_params.
Implements the parameter resolution logic from the design document.
"""

import logging
import random
from typing import Dict, Any, Optional
from config import STYLE_CONFIG

logger = logging.getLogger(__name__)

# Import quality profiles from GPU server (shared configuration)
# Since we can't cross-import, we define the mapping here
QUALITY_PROFILES = {
    "fast": {
        "steps": 18,
        "cfg": 6.5,
        "width": 704,
        "height": 1024,
        "sampler": "euler",
        "scheduler": "normal"
    },
    "balanced": {
        "steps": 26,
        "cfg": 7.5,
        "width": 832,
        "height": 1216,
        "sampler": "euler",
        "scheduler": "normal"
    },
    "high_quality": {
        "steps": 32,
        "cfg": 8.0,
        "width": 896,
        "height": 1344,
        "sampler": "dpmpp_2m",
        "scheduler": "karras"
    },
    # Pony Diffusion optimized profiles
    "pony_balanced": {
        "steps": 30,
        "cfg": 5.0,  # Recommended CFG for Pony
        "width": 832,
        "height": 1216,
        "sampler": "dpmpp_sde",  # DPM++ SDE Karras
        "scheduler": "karras"
    },
    "pony_high_quality": {
        "steps": 40,
        "cfg": 5.0,
        "width": 896,
        "height": 1152,
        "sampler": "dpmpp_2m",  # DPM++ 2M Karras
        "scheduler": "karras"
    }
}


class ParameterResolver:
    """Resolves final generation parameters from style, quality profile, and overrides"""
    
    @staticmethod
    def resolve_params(
        style: str,
        prompt: str,
        extra_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Resolve final generation parameters.
        
        Resolution order:
        1. Start with style's default quality profile
        2. Apply quality_profile override if provided in extra_params
        3. Apply individual parameter overrides from extra_params
        4. Add style-specific prompt prefix and negative prompt
        5. Map cfg_scale → cfg for GPU server
        
        Args:
            style: Style name (noir, super_realism, anime)
            prompt: User prompt
            extra_params: Optional parameter overrides
        
        Returns:
            Dict with resolved parameters ready for GPU server
        """
        # Get style configuration
        if style not in STYLE_CONFIG:
            raise ValueError(f"Unknown style: {style}")
        
        style_config = STYLE_CONFIG[style]
        
        # Step 1: Get default quality profile from style
        quality_profile_name = style_config["default_quality_profile"]
        
        # Step 2: Check for quality_profile override in extra_params
        if extra_params and "quality_profile" in extra_params and extra_params["quality_profile"]:
            quality_profile_name = extra_params["quality_profile"]
            logger.info(f"Quality profile overridden to: {quality_profile_name}")
        
        # Get quality profile parameters
        if quality_profile_name not in QUALITY_PROFILES:
            raise ValueError(f"Unknown quality profile: {quality_profile_name}")
        
        quality_params = QUALITY_PROFILES[quality_profile_name].copy()
        
        # Step 3: Apply individual parameter overrides from extra_params
        final_params = quality_params.copy()
        
        if extra_params:
            # Override individual parameters if provided
            if extra_params.get("steps"):
                final_params["steps"] = extra_params["steps"]
            if extra_params.get("cfg_scale"):
                # CRITICAL: Map cfg_scale → cfg for GPU server
                final_params["cfg"] = extra_params["cfg_scale"]
            if extra_params.get("sampler"):
                final_params["sampler"] = extra_params["sampler"]
            if extra_params.get("width"):
                final_params["width"] = extra_params["width"]
            if extra_params.get("height"):
                final_params["height"] = extra_params["height"]
        
        # Step 4: Add prompt with style prefix
        enhanced_prompt = style_config["prompt_prefix"] + prompt
        final_params["prompt"] = enhanced_prompt
        final_params["negative_prompt"] = style_config["negative_prompt"]
        
        # Add seed (convert -1 to random positive integer for ComfyUI)
        seed_value = extra_params.get("seed", -1) if extra_params else -1
        if seed_value == -1:
            # Generate random seed in ComfyUI's valid range (0 to 18446744073709551615)
            seed_value = random.randint(0, 2**32 - 1)  # Use 32-bit for reasonable range
        final_params["seed"] = seed_value
        
        # Add model checkpoint
        final_params["checkpoint"] = style_config["model"]
        
        # Log resolved parameters
        logger.info(
            f"Resolved params: style={style}, profile={quality_profile_name}, "
            f"steps={final_params['steps']}, cfg={final_params['cfg']}, "
            f"size={final_params['width']}x{final_params['height']}"
        )
        
        return final_params
