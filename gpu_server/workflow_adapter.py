"""
ComfyUI Workflow Adapters
Base class and mode-specific adapters for injecting parameters into ComfyUI workflows
"""
import json
import logging
import base64
from typing import Dict, Any, Optional
from pathlib import Path
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class WorkflowAdapter(ABC):
    """Base class for ComfyUI workflow adapters"""
    
    def __init__(self, workflow_dir: str = "/workspace/workflows"):
        """
        Initialize workflow adapter
        
        Args:
            workflow_dir: Directory containing workflow JSON files
        """
        self.workflow_dir = Path(workflow_dir)
        self.workflow = None
    
    @abstractmethod
    def get_workflow_filename(self) -> str:
        """Return the workflow JSON filename"""
        pass
    
    def load_workflow(self) -> Dict[str, Any]:
        """
        Load workflow JSON from file
        
        Returns:
            Workflow dictionary
        """
        workflow_path = self.workflow_dir / self.get_workflow_filename()
        
        if not workflow_path.exists():
            raise FileNotFoundError(f"Workflow file not found: {workflow_path}")
        
        with open(workflow_path, 'r', encoding='utf-8') as f:
            self.workflow = json.load(f)
        
        logger.info(f"Loaded workflow: {self.get_workflow_filename()}")
        return self.workflow
    
    def inject_node_value(self, node_id: str, field: str, value: Any):
        """
        Inject value into workflow node
        
        Args:
            node_id: Node identifier
            field: Field name in node inputs
            value: Value to inject
        """
        if self.workflow is None:
            raise ValueError("Workflow not loaded. Call load_workflow() first")
        
        if node_id not in self.workflow:
            raise ValueError(f"Node {node_id} not found in workflow")
        
        if "inputs" not in self.workflow[node_id]:
            self.workflow[node_id]["inputs"] = {}
        
        self.workflow[node_id]["inputs"][field] = value
        logger.debug(f"Injected {field}={value} into node {node_id}")
    
    @abstractmethod
    def inject_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inject generation parameters into workflow
        
        Args:
            params: Parameter dictionary
        
        Returns:
            Modified workflow
        """
        pass
    
    def get_workflow(self) -> Dict[str, Any]:
        """Get current workflow"""
        if self.workflow is None:
            raise ValueError("Workflow not loaded")
        return self.workflow


class FreeWorkflowAdapter(WorkflowAdapter):
    """Adapter for Free SDXL text-to-image generation"""
    
    def get_workflow_filename(self) -> str:
        return "free_generation.json"
    
    def inject_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inject parameters for free generation
        
        Expected params:
            - prompt: str
            - negative_prompt: str (optional)
            - seed: int (optional)
            - steps: int (optional)
            - cfg_scale: float (optional)
            - width: int (optional)
            - height: int (optional)
            - sampler_name: str (optional)
        """
        if self.workflow is None:
            self.load_workflow()
        
        # Inject prompt
        prompt = params.get("prompt", "")
        self.inject_node_value("6", "text", prompt)  # Positive prompt node
        
        # Inject negative prompt
        negative_prompt = params.get("negative_prompt", "")
        self.inject_node_value("7", "text", negative_prompt)  # Negative prompt node
        
        # Inject sampler parameters
        if "seed" in params:
            self.inject_node_value("3", "seed", params["seed"])
        if "steps" in params:
            self.inject_node_value("3", "steps", params["steps"])
        if "cfg_scale" in params:
            self.inject_node_value("3", "cfg", params["cfg_scale"])
        if "sampler_name" in params:
            self.inject_node_value("3", "sampler_name", params["sampler_name"])
        
        # Inject latent image dimensions
        if "width" in params:
            self.inject_node_value("5", "width", params["width"])
        if "height" in params:
            self.inject_node_value("5", "height", params["height"])
        
        return self.workflow


class FaceSwapWorkflowAdapter(WorkflowAdapter):
    """Adapter for face swap using InsightFace"""
    
    def get_workflow_filename(self) -> str:
        return "face_swap_workflow_template.json"
    
    def inject_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inject parameters for face swap
        
        Expected params:
            - source_image: str (filename in ComfyUI input folder)
            - target_image: str (filename in ComfyUI input folder)
            - face_restore_strength: float (optional)
            - face_index_source: int (optional)
            - face_index_target: int (optional)
        """
        if self.workflow is None:
            self.load_workflow()
        
        # Inject source image
        source_image = params.get("source_image")
        if source_image:
            self.inject_node_value("1", "image", source_image)  # Source image loader
        
        # Inject target image
        target_image = params.get("target_image")
        if target_image:
            self.inject_node_value("2", "image", target_image)  # Target image loader
        
        # Inject face restoration strength
        if "face_restore_strength" in params:
            self.inject_node_value("8", "strength", params["face_restore_strength"])
        
        # Inject face indices
        if "face_index_source" in params:
            self.inject_node_value("4", "face_index", params["face_index_source"])
        if "face_index_target" in params:
            self.inject_node_value("5", "face_index", params["face_index_target"])
        
        return self.workflow


class ClothesRemovalWorkflowAdapter(WorkflowAdapter):
    """Adapter for clothes removal/undressing"""
    
    def get_workflow_filename(self) -> str:
        return "clothes_removal_workflow_template.json"
    
    def inject_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inject parameters for clothes removal
        
        Expected params:
            - source_image: str (filename in ComfyUI input folder)
            - prompt: str (optional, default: nude-related prompts)
            - denoise_strength: float (optional)
            - preserve_face: bool (optional, default: True)
        """
        if self.workflow is None:
            self.load_workflow()
        
        # Inject source image
        source_image = params.get("source_image")
        if source_image:
            self.inject_node_value("1", "image", source_image)
        
        # Inject prompt
        prompt = params.get("prompt", "nude, naked body, natural skin, high quality, photorealistic")
        self.inject_node_value("6", "text", prompt)
        
        # Inject negative prompt
        negative_prompt = params.get("negative_prompt", "clothes, clothing, dressed, censored, low quality")
        self.inject_node_value("7", "text", negative_prompt)
        
        # Inject denoise strength
        if "denoise_strength" in params:
            self.inject_node_value("10", "denoise", params["denoise_strength"])
        
        return self.workflow


class FaceConsistentWorkflowAdapter(WorkflowAdapter):
    """Adapter for face-consistent generation using IP-Adapter"""
    
    def get_workflow_filename(self) -> str:
        return "face_consistent_workflow_template.json"
    
    def inject_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inject parameters for face-consistent generation
        
        Expected params:
            - face_image: str (filename in ComfyUI input folder)
            - prompt: str
            - style: str (realistic or anime)
            - negative_prompt: str (optional)
            - ip_adapter_strength: float (optional)
            - seed: int (optional)
            - steps: int (optional)
        """
        if self.workflow is None:
            self.load_workflow()
        
        # Inject reference face image
        face_image = params.get("face_image")
        if face_image:
            self.inject_node_value("1", "image", face_image)
        
        # Inject prompt
        prompt = params.get("prompt", "")
        self.inject_node_value("6", "text", prompt)
        
        # Inject negative prompt
        negative_prompt = params.get("negative_prompt", "low quality, blurry")
        self.inject_node_value("7", "text", negative_prompt)
        
        # Inject IP-Adapter strength (face preservation strength)
        if "ip_adapter_strength" in params:
            self.inject_node_value("11", "strength", params["ip_adapter_strength"])
        
        # Inject sampler parameters
        if "seed" in params:
            self.inject_node_value("3", "seed", params["seed"])
        if "steps" in params:
            self.inject_node_value("3", "steps", params["steps"])
        
        # Style-specific adjustments
        style = params.get("style", "realistic")
        if style == "anime":
            # Use anime-specific LoRA or checkpoint
            self.inject_node_value("4", "lora_name", "anime_lora.safetensors")
        
        return self.workflow


class AnimeWorkflowAdapter(WorkflowAdapter):
    """Adapter for anime-style generation"""
    
    def get_workflow_filename(self) -> str:
        return "anime.json"
    
    def inject_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inject parameters for anime generation
        
        Expected params:
            - prompt: str
            - model_name: str (optional)
            - lora_weights: Dict[str, float] (optional)
            - seed: int (optional)
        """
        if self.workflow is None:
            self.load_workflow()
        
        # Inject prompt
        prompt = params.get("prompt", "")
        self.inject_node_value("6", "text", prompt)
        
        # Inject anime-specific negative prompt
        negative_prompt = params.get("negative_prompt", "realistic, photorealistic, low quality")
        self.inject_node_value("7", "text", negative_prompt)
        
        # Inject model selection
        if "model_name" in params:
            self.inject_node_value("4", "ckpt_name", params["model_name"])
        
        # Inject LoRA weights
        lora_weights = params.get("lora_weights", {})
        for lora_name, weight in lora_weights.items():
            # Assuming LoRA nodes are numbered 12, 13, 14, etc.
            # This needs to match the actual workflow structure
            pass
        
        # Inject seed
        if "seed" in params:
            self.inject_node_value("3", "seed", params["seed"])
        
        return self.workflow


class RealismWorkflowAdapter(WorkflowAdapter):
    """Adapter for realistic photo generation with ControlNet"""
    
    def get_workflow_filename(self) -> str:
        return "realism.json"
    
    def inject_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inject parameters for realistic generation
        
        Expected params:
            - prompt: str
            - control_type: str (pose, depth, canny)
            - control_image: str (filename, optional)
            - controlnet_strength: float (optional)
            - seed: int (optional)
        """
        if self.workflow is None:
            self.load_workflow()
        
        # Inject prompt
        prompt = params.get("prompt", "")
        self.inject_node_value("6", "text", prompt)
        
        # Inject realism-focused negative prompt
        negative_prompt = params.get("negative_prompt", "cartoon, anime, drawing, low quality, blurry")
        self.inject_node_value("7", "text", negative_prompt)
        
        # Inject control image if provided
        control_image = params.get("control_image")
        if control_image:
            self.inject_node_value("2", "image", control_image)
        
        # Inject ControlNet strength
        if "controlnet_strength" in params:
            self.inject_node_value("10", "strength", params["controlnet_strength"])
        
        # Inject seed
        if "seed" in params:
            self.inject_node_value("3", "seed", params["seed"])
        
        return self.workflow


class FreeGenerationFaceAdapter(WorkflowAdapter):
    """Adapter for Free Generation with Face using IP-Adapter FaceID"""
    
    def get_workflow_filename(self) -> str:
        return "free_generation_face.json"
    
    def inject_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inject parameters for free generation with face embedding
        
        Expected params:
            - prompt: str
            - negative_prompt: str (optional)
            - face_image: str (filename in ComfyUI input folder)
            - face_strength: float (0.0-1.0, default: 0.75)
            - seed: int (optional)
            - steps: int (optional)
            - cfg: float (optional)
            - width: int (optional)
            - height: int (optional)
            - sampler_name: str (optional)
            - model: str (checkpoint name, optional)
        """
        if self.workflow is None:
            self.load_workflow()
        
        # Inject prompt
        prompt = params.get("prompt", "")
        self.inject_node_value("6", "text", prompt)
        
        # Inject negative prompt
        negative_prompt = params.get("negative_prompt", "low quality, blurry")
        self.inject_node_value("7", "text", negative_prompt)
        
        # Inject face reference image
        face_image = params.get("face_image")
        if face_image:
            self.inject_node_value("20", "image", face_image)
        
        # Inject face strength (IP-Adapter weight)
        face_strength = params.get("face_strength", 0.75)
        self.inject_node_value("22", "weight", face_strength)
        
        # Inject model if specified
        if "model" in params:
            self.inject_node_value("4", "ckpt_name", params["model"])
        
        # Inject sampler parameters
        if "seed" in params:
            self.inject_node_value("3", "seed", params["seed"])
        if "steps" in params:
            self.inject_node_value("3", "steps", params["steps"])
        if "cfg" in params:
            self.inject_node_value("3", "cfg", params["cfg"])
        if "sampler_name" in params:
            self.inject_node_value("3", "sampler_name", params["sampler_name"])
        
        # Inject latent dimensions
        if "width" in params:
            self.inject_node_value("5", "width", params["width"])
        if "height" in params:
            self.inject_node_value("5", "height", params["height"])
        
        return self.workflow


class ClothesRemovalEnhancedAdapter(WorkflowAdapter):
    """Adapter for enhanced clothes removal with multi-ControlNet"""
    
    def get_workflow_filename(self) -> str:
        return "clothes_removal.json"
    
    def inject_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inject parameters for clothes removal with ControlNet
        
        Expected params:
            - target_image: str (filename in ComfyUI input folder)
            - model: str (checkpoint name based on style)
            - controlnet_strength: float (0.0-1.5, default: 0.8)
            - inpaint_denoise: float (0.5-1.0, default: 0.75)
            - segmentation_threshold: float (0.5-0.9, default: 0.7)
            - prompt: str (optional)
            - negative_prompt: str (optional)
            - seed: int (optional)
            - steps: int (optional)
            - cfg: float (optional)
        """
        if self.workflow is None:
            self.load_workflow()
        
        # Inject target image (can be "image" or "target_image" from params)
        target_image = params.get("target_image") or params.get("image")
        if target_image:
            self.inject_node_value("1", "image", target_image)
        
        # Inject model checkpoint
        if "model" in params:
            self.inject_node_value("4", "ckpt_name", params["model"])
        
        # Inject prompts
        prompt = params.get("prompt", "nude, naked body, natural skin, photorealistic, high quality")
        self.inject_node_value("6", "text", prompt)
        
        negative_prompt = params.get("negative_prompt", "clothes, clothing, dressed, censored, low quality")
        self.inject_node_value("7", "text", negative_prompt)
        
        # Inject ControlNet strength for all three controls
        controlnet_strength = params.get("controlnet_strength", 0.8)
        self.inject_node_value("16", "strength", controlnet_strength)  # OpenPose
        self.inject_node_value("18", "strength", controlnet_strength)  # Depth
        self.inject_node_value("20", "strength", controlnet_strength)  # Canny
        
        # Inject inpaint denoise strength
        inpaint_denoise = params.get("inpaint_denoise", 0.75)
        self.inject_node_value("3", "denoise", inpaint_denoise)
        
        # Inject segmentation threshold
        segmentation_threshold = params.get("segmentation_threshold", 0.7)
        self.inject_node_value("10", "threshold", segmentation_threshold)
        
        # Inject sampler parameters
        if "seed" in params:
            self.inject_node_value("3", "seed", params["seed"])
        if "steps" in params:
            self.inject_node_value("3", "steps", params["steps"])
        if "cfg" in params:
            self.inject_node_value("3", "cfg", params["cfg"])
        
        return self.workflow


class NSFWFaceAdapter(WorkflowAdapter):
    """Adapter for NSFW generation with multi-face consistency"""
    
    def get_workflow_filename(self) -> str:
        return "nsfw_face.json"
    
    def inject_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inject parameters for NSFW face-consistent generation
        
        Expected params:
            - face_images: List[str] (1-5 filenames in ComfyUI input folder)
            - scene_prompt: str
            - negative_prompt: str (optional)
            - face_strength: float (0.6-1.0, default: 0.8)
            - enable_upscale: bool (default: False)
            - model: str (checkpoint name based on style)
            - seed: int (optional)
            - steps: int (optional)
            - cfg: float (optional)
            - width: int (optional)
            - height: int (optional)
        """
        if self.workflow is None:
            self.load_workflow()
        
        # Inject face images (support 1-5 faces)
        face_images = params.get("face_images", [])
        face_node_ids = ["20", "21", "22", "23", "24"]
        
        for i, face_image in enumerate(face_images[:5]):
            if i < len(face_node_ids):
                self.inject_node_value(face_node_ids[i], "image", face_image)
        
        # Inject scene prompt
        scene_prompt = params.get("scene_prompt", "")
        self.inject_node_value("6", "text", scene_prompt)
        
        # Inject negative prompt
        negative_prompt = params.get("negative_prompt", "low quality, blurry, deformed, censored")
        self.inject_node_value("7", "text", negative_prompt)
        
        # Inject face strength
        face_strength = params.get("face_strength", 0.8)
        self.inject_node_value("26", "weight", face_strength)
        
        # Inject model
        if "model" in params:
            self.inject_node_value("4", "ckpt_name", params["model"])
        
        # Inject sampler parameters
        if "seed" in params:
            self.inject_node_value("3", "seed", params["seed"])
        if "steps" in params:
            self.inject_node_value("3", "steps", params["steps"])
        if "cfg" in params:
            self.inject_node_value("3", "cfg", params["cfg"])
        
        # Inject dimensions
        if "width" in params:
            self.inject_node_value("5", "width", params["width"])
        if "height" in params:
            self.inject_node_value("5", "height", params["height"])
        
        # Handle upscaling option
        enable_upscale = params.get("enable_upscale", False)
        if not enable_upscale:
            # If upscaling disabled, connect VAE decode directly to save
            # This requires modifying the save node input
            self.inject_node_value("9", "images", ["8", 0])
        
        return self.workflow


def get_adapter(mode: str, workflow_dir: str = "/workspace/workflows") -> WorkflowAdapter:
    """
    Factory function to get appropriate workflow adapter
    
    Args:
        mode: Generation mode
        workflow_dir: Workflow directory path
    
    Returns:
        Appropriate WorkflowAdapter instance
    """
    adapters = {
        "free": FreeWorkflowAdapter,
        "free_generation_face": FreeGenerationFaceAdapter,
        "face_swap": FaceSwapWorkflowAdapter,
        "clothes_removal": ClothesRemovalEnhancedAdapter,
        "face_consistent": FaceConsistentWorkflowAdapter,
        "nsfw_face": NSFWFaceAdapter,
        "anime": AnimeWorkflowAdapter,
        "realism": RealismWorkflowAdapter
    }
    
    adapter_class = adapters.get(mode)
    if not adapter_class:
        raise ValueError(f"Unknown generation mode: {mode}")
    
    return adapter_class(workflow_dir=workflow_dir)
