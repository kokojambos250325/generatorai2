from typing import Optional, Any
import base64
import io
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance
from models.face_enhancer import FaceEnhancer
from models.upscale import UpscaleModel


class PostProcessPipeline:
    """
    Unified post-processing pipeline for image enhancement
    
    Orchestrates all post-processing operations including:
    - Face enhancement (GFPGAN/CodeFormer)
    - Image upscaling (RealESRGAN)
    - Denoising (OpenCV)
    - Sharpening (PIL)
    - Color correction (PIL)
    
    Supports three quality modes:
    - fast: No processing, direct encoding
    - balanced: Selective enhancement (face + sharpen + color)
    - high: Full pipeline (upscale + face + denoise + sharpen + color)
    """
    
    def __init__(self, device: str = "cuda", model_manager: Optional[Any] = None):
        """
        Initialize post-processing pipeline
        
        Args:
            device: Computation device (cuda/cpu)
            model_manager: Optional ModelManager for centralized model loading
        """
        self.device = device
        self.model_manager = model_manager
        self.loaded = False
        
        # Enhancement model instances
        self.face_enhancer: Optional[FaceEnhancer] = None
        self.upscale_model: Optional[UpscaleModel] = None
    
    async def load_models(self) -> None:
        """
        Load all post-processing models
        
        Initializes:
        1. FaceEnhancer for face restoration
        2. UpscaleModel for image upscaling
        
        Both models use placeholder logic initially and can be upgraded
        to full implementations later.
        """
        print("PostProcessPipeline: Loading enhancement models...")
        
        # Load FaceEnhancer
        print("  Loading FaceEnhancer...")
        self.face_enhancer = FaceEnhancer(model_type="gfpgan", device=self.device)
        enhancer_loaded = self.face_enhancer.load_model()
        if not enhancer_loaded:
            print("  ⚠ FaceEnhancer using placeholder (real model not loaded)")
        else:
            print("  ✓ FaceEnhancer loaded")
        
        # Load UpscaleModel
        print("  Loading UpscaleModel...")
        self.upscale_model = UpscaleModel(model_name="realesrgan", scale=2, device=self.device)
        upscale_loaded = self.upscale_model.load_model()
        if not upscale_loaded:
            print("  ⚠ UpscaleModel using placeholder (real model not loaded)")
        else:
            print("  ✓ UpscaleModel loaded")
        
        self.loaded = True
        print("PostProcessPipeline: Enhancement models ready")
    
    def enhance_face(self, image: Image.Image, strength: float = 0.7) -> Image.Image:
        """
        Apply face restoration to image
        
        Args:
            image: PIL Image to enhance
            strength: Enhancement strength (0.0-1.0)
                0.0 = original image
                1.0 = full restoration
                
        Returns:
            Enhanced PIL Image (or original if enhancement fails)
        """
        if not self.face_enhancer:
            print("  ⚠ FaceEnhancer not initialized, skipping face enhancement")
            return image
        
        try:
            # Convert PIL Image to numpy array (RGB to BGR for OpenCV)
            img_array = np.array(image)
            img_bgr = img_array[:, :, ::-1].copy()  # RGB to BGR
            
            # Apply face enhancement
            enhanced_bgr = self.face_enhancer.enhance(img_bgr, strength=strength)
            
            if enhanced_bgr is not None:
                # Convert back to RGB and PIL Image
                enhanced_rgb = enhanced_bgr[:, :, ::-1]  # BGR to RGB
                return Image.fromarray(enhanced_rgb)
            else:
                print("  ⚠ Face enhancement returned None, using original")
                return image
                
        except Exception as e:
            print(f"  ⚠ Face enhancement failed: {e}, using original")
            return image
    
    def upscale(self, image: Image.Image, scale: int = 2) -> Image.Image:
        """
        Increase image resolution
        
        Args:
            image: PIL Image to upscale
            scale: Scaling factor (2 or 4)
            
        Returns:
            Upscaled PIL Image
        """
        if not self.upscale_model:
            print("  ⚠ UpscaleModel not initialized, using PIL resize fallback")
            new_width = image.width * scale
            new_height = image.height * scale
            return image.resize((new_width, new_height), Image.LANCZOS)
        
        try:
            # Convert PIL Image to numpy array (RGB to BGR)
            img_array = np.array(image)
            img_bgr = img_array[:, :, ::-1].copy()
            
            # Apply upscaling
            upscaled_bgr = self.upscale_model.upscale(img_bgr, tile_size=512)
            
            if upscaled_bgr is not None:
                # Convert back to RGB and PIL Image
                upscaled_rgb = upscaled_bgr[:, :, ::-1]
                return Image.fromarray(upscaled_rgb)
            else:
                print("  ⚠ Upscaling returned None, using PIL resize fallback")
                new_width = image.width * scale
                new_height = image.height * scale
                return image.resize((new_width, new_height), Image.LANCZOS)
                
        except Exception as e:
            print(f"  ⚠ Upscaling failed: {e}, using PIL resize fallback")
            new_width = image.width * scale
            new_height = image.height * scale
            return image.resize((new_width, new_height), Image.LANCZOS)
    
    def denoise(self, image: Image.Image) -> Image.Image:
        """
        Remove noise and artifacts from image
        
        Args:
            image: PIL Image to denoise
            
        Returns:
            Denoised PIL Image
        """
        try:
            # Try using OpenCV for better denoising
            import cv2
            
            # Convert to numpy array
            img_array = np.array(image)
            img_bgr = img_array[:, :, ::-1].copy()
            
            # Apply non-local means denoising
            denoised = cv2.fastNlMeansDenoisingColored(
                img_bgr,
                None,
                h=10,
                hColor=10,
                templateWindowSize=7,
                searchWindowSize=21
            )
            
            # Convert back to RGB and PIL Image
            denoised_rgb = denoised[:, :, ::-1]
            return Image.fromarray(denoised_rgb)
            
        except ImportError:
            # Fallback to PIL if OpenCV not available
            print("  ⚠ OpenCV not available, using PIL blur for denoising")
            return image.filter(ImageFilter.SMOOTH)
        except Exception as e:
            print(f"  ⚠ Denoising failed: {e}, using original")
            return image
    
    def sharpen(self, image: Image.Image, amount: float = 1.0) -> Image.Image:
        """
        Enhance image sharpness
        
        Args:
            image: PIL Image to sharpen
            amount: Sharpening intensity multiplier (default 1.0)
            
        Returns:
            Sharpened PIL Image
        """
        try:
            # Use UnsharpMask filter for controllable sharpening
            radius = 2
            percent = int(150 * amount)
            threshold = 3
            
            return image.filter(
                ImageFilter.UnsharpMask(
                    radius=radius,
                    percent=percent,
                    threshold=threshold
                )
            )
        except Exception as e:
            print(f"  ⚠ Sharpening failed: {e}, using original")
            return image
    
    def color_correct(self, image: Image.Image) -> Image.Image:
        """
        Adjust color balance and saturation
        
        Args:
            image: PIL Image to correct
            
        Returns:
            Color-corrected PIL Image
        """
        try:
            # Apply subtle color corrections
            # Brightness
            enhancer = ImageEnhance.Brightness(image)
            result = enhancer.enhance(1.05)
            
            # Contrast
            enhancer = ImageEnhance.Contrast(result)
            result = enhancer.enhance(1.1)
            
            # Color saturation
            enhancer = ImageEnhance.Color(result)
            result = enhancer.enhance(1.05)
            
            return result
            
        except Exception as e:
            print(f"  ⚠ Color correction failed: {e}, using original")
            return image
    
    def finalize(
        self,
        image: Image.Image,
        quality_mode: str = "balanced",
        enable_face_enhance: bool = True,
        enable_upscale: bool = False
    ) -> str:
        """
        Complete post-processing pipeline and encode result
        
        Args:
            image: Generated PIL Image to process
            quality_mode: Processing mode ("fast", "balanced", or "high")
            enable_face_enhance: Whether to apply face enhancement
            enable_upscale: Whether to apply upscaling
            
        Returns:
            Base64 encoded PNG string
        """
        result = image
        
        # Validate quality mode
        valid_modes = ["fast", "balanced", "high"]
        if quality_mode not in valid_modes:
            print(f"  ⚠ Invalid quality mode '{quality_mode}', using 'balanced'")
            quality_mode = "balanced"
        
        print(f"\nPostProcessPipeline.finalize: Processing with mode='{quality_mode}'")
        
        # Fast mode: skip all processing
        if quality_mode == "fast":
            print("  Fast mode: Skipping all enhancements")
        
        # Balanced mode: selective enhancement
        elif quality_mode == "balanced":
            print("  Balanced mode: Applying selective enhancements...")
            
            if enable_face_enhance:
                print("    - Face enhancement (strength=0.7)")
                result = self.enhance_face(result, strength=0.7)
            
            print("    - Sharpening")
            result = self.sharpen(result, amount=1.0)
            
            print("    - Color correction")
            result = self.color_correct(result)
        
        # High mode: full pipeline
        elif quality_mode == "high":
            print("  High mode: Applying full enhancement pipeline...")
            
            if enable_upscale:
                print("    - Upscaling 2x")
                result = self.upscale(result, scale=2)
            
            print("    - Face enhancement (strength=0.8)")
            result = self.enhance_face(result, strength=0.8)
            
            print("    - Denoising")
            result = self.denoise(result)
            
            print("    - Sharpening (amount=1.2)")
            result = self.sharpen(result, amount=1.2)
            
            print("    - Color correction")
            result = self.color_correct(result)
        
        # Encode to base64
        print("  Encoding to PNG/base64...")
        buffered = io.BytesIO()
        result.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        print(f"✓ PostProcessPipeline.finalize: Complete ({len(img_base64)} chars)\n")
        
        return img_base64
