from abc import abstractmethod
from typing import Any, Dict, List, Optional
from pipelines.base.base_pipeline import BasePipeline


class ControlNetPipelineBase(BasePipeline):
    """
    Base class for pipelines with ControlNet integration support
    
    Provides reusable methods for ControlNet-enabled generation pipelines:
    - Preparing ControlNet conditioning inputs
    - Attaching ControlNet models to SDXL pipeline
    - Managing multiple ControlNet models simultaneously
    
    Extends BasePipeline with ControlNet-specific functionality.
    """
    
    def __init__(self, device: str = "cuda", model_manager: Optional[Any] = None):
        """
        Initialize ControlNet-enabled pipeline
        
        Args:
            device: Device for computations ("cuda" or "cpu")
            model_manager: Model manager for loading and caching models
        """
        super().__init__(device, model_manager)
        # Dictionary storing loaded ControlNet instances
        self.controlnet_models: Dict[str, Any] = {}
        # Configuration for ControlNet behavior
        self.controlnet_config: Dict[str, Any] = {
            'controlnet_conditioning_scale': 0.8,
            'guess_mode': False,
            'control_guidance_start': 0.0,
            'control_guidance_end': 1.0
        }
    
    def prepare_controlnet_inputs(self, request: Any, control_type: str) -> Dict[str, Any]:
        """
        Prepare conditioning inputs for ControlNet from request data
        
        Extracts and preprocesses control images for ControlNet conditioning:
        1. Extract control image from request (path or base64)
        2. Load and decode image data
        3. Resize to match generation resolution
        4. Apply preprocessing based on control type:
           - Pose: Extract pose keypoints (placeholder)
           - Depth: Generate depth map (placeholder)
           - Struct: Apply edge detection (placeholder)
        5. Prepare strength and scale parameters
        6. Return structured conditioning dictionary
        
        Args:
            request: Generation request object with control image data
            control_type: Type of control ("pose", "depth", "struct")
            
        Returns:
            Dictionary with conditioning data:
            - control_image: Processed conditioning image
            - control_type: Type of ControlNet being used
            - control_strength: Conditioning strength (0.0-1.0)
            - controlnet_model: Reference to loaded model
        """
        from PIL import Image
        import base64
        import io
        
        # Extract control image
        control_img = None
        if hasattr(request, 'control_image') and request.control_image:
            if isinstance(request.control_image, str):
                if request.control_image.startswith('data:'):
                    # Decode base64
                    try:
                        img_data = base64.b64decode(request.control_image.split(',')[1])
                        control_img = Image.open(io.BytesIO(img_data))
                    except Exception as e:
                        print(f"Failed to decode base64 control image: {e}")
                        control_img = None
                else:
                    # Load from path
                    try:
                        control_img = Image.open(request.control_image)
                    except Exception as e:
                        print(f"Failed to load control image from path: {e}")
                        control_img = None
            else:
                control_img = request.control_image
            
            # Resize to target resolution and ensure RGB
            if control_img:
                try:
                    control_img = control_img.convert('RGB')
                    control_img = control_img.resize((1024, 1024))
                except Exception as e:
                    print(f"Failed to process control image: {e}")
                    control_img = None
            
            # Apply preprocessing based on type (future: add preprocessors)
            if control_img:
                if control_type == "pose":
                    # TODO: Extract pose keypoints with OpenPose
                    processed_img = control_img
                elif control_type == "depth":
                    # TODO: Generate depth map
                    processed_img = control_img
                elif control_type == "struct":
                    # TODO: Apply Canny edge detection
                    processed_img = control_img
                else:
                    processed_img = control_img
            else:
                processed_img = None
            
            return {
                'control_image': processed_img,
                'control_type': control_type,
                'control_strength': getattr(request, 'control_strength', 0.8),
                'controlnet_model': self.controlnet_models.get(control_type)
            }
        
        return {
            'control_image': None,
            'control_type': control_type,
            'control_strength': 0.8,
            'controlnet_model': None
        }
    
    def attach_controlnet_to_sdxl(
        self, 
        sdxl_pipeline: Any, 
        controlnet_models: List[Any]
    ) -> Any:
        """
        Integrate one or multiple ControlNet models with SDXL pipeline
        
        Creates a ControlNet-enhanced SDXL pipeline:
        1. Validate SDXL pipeline is loaded and ready
        2. Validate all ControlNet models in list
        3. Determine single vs multi-ControlNet configuration
        4. Create appropriate pipeline wrapper:
           - Single: StableDiffusionXLControlNetPipeline
           - Multiple: StableDiffusionXLControlNetPipeline with MultiControlNetModel
        5. Transfer SDXL components (VAE, scheduler, etc.)
        6. Configure ControlNet-specific parameters
        7. Apply memory optimizations
        8. Return integrated pipeline
        
        Args:
            sdxl_pipeline: Base SDXL pipeline instance
            controlnet_models: List of ControlNet models to attach
            
        Returns:
            Modified pipeline with ControlNet integration, or original pipeline if
            ControlNet integration fails
        """
        from diffusers import StableDiffusionXLControlNetPipeline, MultiControlNetModel
        
        # Validate inputs
        if not sdxl_pipeline:
            print("Error: SDXL pipeline is required")
            return sdxl_pipeline
        
        if not controlnet_models or all(m is None for m in controlnet_models):
            # No valid ControlNet models, return original pipeline
            return sdxl_pipeline
        
        # Filter out None models
        valid_controlnets = [m for m in controlnet_models if m is not None]
        
        if not valid_controlnets:
            return sdxl_pipeline
        
        try:
            # Determine single vs multi-ControlNet
            if len(valid_controlnets) == 1:
                controlnet = valid_controlnets[0]
            else:
                # Create MultiControlNetModel for multiple ControlNets
                controlnet = MultiControlNetModel(valid_controlnets)
            
            # Create ControlNet-enhanced pipeline
            controlnet_pipeline = StableDiffusionXLControlNetPipeline(
                vae=sdxl_pipeline.vae,
                text_encoder=sdxl_pipeline.text_encoder,
                text_encoder_2=sdxl_pipeline.text_encoder_2,
                tokenizer=sdxl_pipeline.tokenizer,
                tokenizer_2=sdxl_pipeline.tokenizer_2,
                unet=sdxl_pipeline.unet,
                controlnet=controlnet,
                scheduler=sdxl_pipeline.scheduler
            )
            
            # Transfer to device
            controlnet_pipeline = controlnet_pipeline.to(self.device)
            
            # Apply optimizations
            controlnet_pipeline.enable_attention_slicing()
            controlnet_pipeline.enable_vae_slicing()
            
            try:
                controlnet_pipeline.enable_xformers_memory_efficient_attention()
            except Exception:
                pass  # xformers not available
            
            return controlnet_pipeline
            
        except Exception as e:
            print(f"Failed to attach ControlNet to SDXL: {e}")
            return sdxl_pipeline
    
    def prepare_reference_image(self, image: Any) -> Dict[str, Any]:
        """
        Prepare reference images for ControlNet conditioning
        
        Processes reference images for undressing and body exposure workflow:
        1. Load image from path or use PIL Image directly
        2. Validate image format and dimensions
        3. Resize to target resolution
        4. Convert to RGB color space
        5. Normalize pixel values for model compatibility
        6. Return structured dictionary
        
        Args:
            image: Reference image for style or structure (PIL.Image or str path)
            
        Returns:
            Dictionary with processed reference data:
            - reference_image: PIL.Image
            - width: int
            - height: int
            - format: str
        """
        from PIL import Image
        
        # Load image if path provided
        if isinstance(image, str):
            try:
                img = Image.open(image)
            except Exception as e:
                print(f"Failed to load reference image from path: {e}")
                return {
                    'reference_image': None,
                    'width': 0,
                    'height': 0,
                    'format': 'unknown'
                }
        else:
            img = image
        
        # Validate and process
        if img is None:
            return {
                'reference_image': None,
                'width': 0,
                'height': 0,
                'format': 'unknown'
            }
        
        # Convert to RGB
        img = img.convert('RGB')
        
        # Resize to target resolution (1024x1024 for SDXL)
        target_size = (1024, 1024)
        img = img.resize(target_size, Image.Resampling.LANCZOS)
        
        return {
            'reference_image': img,
            'width': img.width,
            'height': img.height,
            'format': 'RGB'
        }
    
    def prepare_pose_map(self, image: Any) -> Any:
        """
        Generate pose keypoint map from human figure to preserve body structure
        
        Ensures generated undressed/nude body maintains original pose and proportions.
        
        Processing Steps (Placeholder):
        1. Detect human body keypoints
        2. Generate pose skeleton visualization
        3. Render as image compatible with OpenPose ControlNet
        4. Return pose map
        
        Future Integration: OpenPose or MediaPipe for keypoint detection
        
        Args:
            image: Image containing human figure (PIL.Image)
            
        Returns:
            PIL.Image: Pose map for ControlNet pose conditioning
            
        Placeholder Behavior:
            Returns resized copy of input
            
        Future implementation will use pose detection:
        
        ```python
        from controlnet_aux import OpenposeDetector
        
        # Initialize pose detector
        openpose = OpenposeDetector.from_pretrained("lllyasviel/ControlNet")
        
        # Detect pose
        pose_image = openpose(image)
        
        # Resize to match generation resolution
        pose_image = pose_image.resize((1024, 1024), Image.Resampling.LANCZOS)
        
        return pose_image
        ```
        """
        from PIL import Image
        
        # Load image if path
        if isinstance(image, str):
            try:
                img = Image.open(image)
            except Exception:
                return None
        else:
            img = image
        
        if img is None:
            return None
        
        # Placeholder: return resized copy
        img = img.convert('RGB')
        img = img.resize((1024, 1024), Image.Resampling.LANCZOS)
        
        return img
    
    def prepare_structure_map(self, image: Any) -> Any:
        """
        Extract structural edges for ControlNet structural conditioning
        
        Preserves body contours and overall composition during undressing regeneration.
        
        Processing Steps (Placeholder):
        1. Convert to grayscale
        2. Apply edge detection algorithm
        3. Post-process for ControlNet compatibility
        4. Return structure map
        
        Future Integration: Canny edge detection or HED boundary detection
        
        Args:
            image: Image to extract structure from (PIL.Image)
            
        Returns:
            PIL.Image: Edge map for ControlNet struct conditioning
            
        Placeholder Behavior:
            Returns resized copy of input
            
        Future implementation will use edge detection:
        
        ```python
        import cv2
        import numpy as np
        
        # Convert to numpy array
        img_array = np.array(image)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # Apply Canny edge detection
        edges = cv2.Canny(gray, threshold1=100, threshold2=200)
        
        # Convert to PIL Image
        edges_image = Image.fromarray(edges)
        
        # Convert to RGB for ControlNet
        edges_rgb = edges_image.convert('RGB')
        
        # Resize to match generation resolution
        edges_rgb = edges_rgb.resize((1024, 1024), Image.Resampling.LANCZOS)
        
        return edges_rgb
        ```
        """
        from PIL import Image
        
        # Load image if path
        if isinstance(image, str):
            try:
                img = Image.open(image)
            except Exception:
                return None
        else:
            img = image
        
        if img is None:
            return None
        
        # Placeholder: return resized copy
        img = img.convert('RGB')
        img = img.resize((1024, 1024), Image.Resampling.LANCZOS)
        
        return img
    
    @abstractmethod
    async def load_models(self) -> None:
        """
        Load models for generation through model_manager
        
        Concrete implementations should:
        1. Load SDXL via model_manager.get_sdxl()
        2. Load ControlNet models via model_manager.get_controlnet_*()
        3. Store models in self.models and self.controlnet_models
        4. Set self.loaded = True
        """
        pass
    
    @abstractmethod
    async def prepare_inputs(self, request: Any) -> Dict[str, Any]:
        """
        Prepare input data for generation
        
        Concrete implementations should handle both standard inputs
        and ControlNet-specific conditioning data.
        """
        pass
    
    @abstractmethod
    async def run(self, inputs: Dict[str, Any]) -> Any:
        """
        Execute generation with optional ControlNet conditioning
        
        Concrete implementations should check for ControlNet inputs
        and use attach_controlnet_to_sdxl if needed.
        """
        pass
