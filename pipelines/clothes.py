from typing import Any, Dict
import random
import base64
import io
import torch
from PIL import Image
from models.generation_request import GenerationRequest
from pipelines.controlnet_base import ControlNetPipelineBase
from models.clothes_segmenter import ClothesSegmenter
from models.clothes_fusion import ClothesFusion
from models.face_enhancer import FaceEnhancer


class ClothesPipeline(ControlNetPipelineBase):
    """
    Pipeline for undressing and body exposure by removing clothing
    
    Orchestrates complete undressing, clothing removal and body exposure workflow using:
    - SDXL for base generation of nude body
    - ControlNet for pose and structural preservation
    - ClothesSegmenter for identifying clothing regions to undress
    - ClothesFusion for blending exposed regions with preserved areas
    - FaceEnhancer for optional face quality preservation
    """

    async def load_models(self) -> None:
        """
        Load all required models for undressing and clothes removal pipeline
        
        Processing Sequence:
        1. SDXL Model - Critical component, raise ValueError if fails
        2. ControlNet Pose Model - Log warning if fails, continue without
        3. ControlNet Struct Model - Log warning if fails, continue without
        4. ClothesSegmenter - Log warning if fails, continue with manual mask
        5. FaceEnhancer - Non-critical, used only if preserve_face=true
        
        Raises:
            ValueError: If ModelManager is not provided or SDXL fails to load
        """
        if not self.model_manager:
            raise ValueError("ModelManager is required for ClothesPipeline")
        
        print("ClothesPipeline: Loading models for undressing workflow...")
        
        # 1. Load SDXL - Critical
        print("  Loading SDXL model...")
        self.models['sdxl'] = self.model_manager.get_sdxl()
        if not self.models['sdxl']:
            raise ValueError("Failed to load SDXL model - cannot proceed with undressing")
        print("  ✓ SDXL model loaded")
        
        # 2. Load ControlNet Pose - Optional
        print("  Loading ControlNet Pose model...")
        self.models['controlnet_pose'] = self.model_manager.get_controlnet_pose()
        if not self.models['controlnet_pose']:
            print("  ⚠ Warning: Failed to load pose ControlNet, will continue without pose control")
        else:
            print("  ✓ ControlNet Pose loaded")
        
        # 3. Load ControlNet Struct - Optional
        print("  Loading ControlNet Struct model...")
        self.models['controlnet_struct'] = self.model_manager.get_controlnet_struct()
        if not self.models['controlnet_struct']:
            print("  ⚠ Warning: Failed to load structural ControlNet, will continue without structural control")
        else:
            print("  ✓ ControlNet Struct loaded")
        
        # 4. Load ClothesSegmenter - Optional
        print("  Loading ClothesSegmenter...")
        segmenter = ClothesSegmenter(device=self.device)
        segmenter_loaded = segmenter.load_model()
        self.models['clothes_segmenter'] = segmenter
        if not segmenter_loaded:
            print("  ⚠ Warning: ClothesSegmenter using placeholder, will use default mask")
        else:
            print("  ✓ ClothesSegmenter loaded")
        
        # 5. Load FaceEnhancer - Optional
        print("  Loading FaceEnhancer...")
        face_enhancer = FaceEnhancer(model_type="gfpgan", device=self.device)
        enhancer_loaded = face_enhancer.load_model()
        self.models['face_enhancer'] = face_enhancer
        if not enhancer_loaded:
            print("  ⚠ Warning: FaceEnhancer using placeholder, face enhancement will be skipped")
        else:
            print("  ✓ FaceEnhancer loaded")
        
        self.loaded = True
        print("ClothesPipeline: All models loaded successfully")

    async def prepare_inputs(self, request: GenerationRequest) -> Dict[str, Any]:
        """
        Process request data into pipeline-ready inputs for undressing and body exposure generation
        
        Processing Steps:
        A. Extract Clothing Mask - Identify areas to undress
        B. Extract Clothing Region - Reference for what to remove
        C. Generate Pose Map - Maintain body proportions
        D. Generate Structure Map - Preserve body contours
        E. Build Prompt - Undressing generation prompt
        F. Prepare Generation Parameters
        
        Args:
            request: GenerationRequest with fields:
                - image: Required, clothed person to undress (base64 or path)
                - clothes_image: Deprecated for undressing
                - prompt: Optional undressing guidance
                - clothes_strength: Undressing strength (0.0-1.0)
                - preserve_face: Apply face enhancement
                - background_mode: "original" or "regenerate"
            
        Returns:
            Prepared inputs dictionary for run method
        """
        # Get base image path (from temp storage)
        base_image_path = getattr(request, 'image', None)
        
        # Load base image for processing
        base_image = None
        if base_image_path:
            try:
                if isinstance(base_image_path, str):
                    base_image = Image.open(base_image_path)
                else:
                    base_image = base_image_path
            except Exception as e:
                print(f"Failed to load base image: {e}")
        
        # Step A: Extract Clothing Mask
        clothes_mask = None
        if base_image and 'clothes_segmenter' in self.models:
            segmenter = self.models['clothes_segmenter']
            clothes_mask = segmenter.get_mask(base_image)
        
        # Step B: Extract Clothing Region
        clothes_region = None
        if base_image and 'clothes_segmenter' in self.models:
            segmenter = self.models['clothes_segmenter']
            clothes_region = segmenter.extract_clothes_region(base_image)
        
        # Step C: Generate Pose Map
        pose_conditioning = None
        if base_image:
            pose_conditioning = self.prepare_pose_map(base_image)
        
        # Step D: Generate Structure Map
        struct_conditioning = None
        if base_image:
            struct_conditioning = self.prepare_structure_map(base_image)
        
        # Step E: Build Prompt
        custom_prompt = request.prompt if hasattr(request, 'prompt') and request.prompt else None
        
        if custom_prompt:
            prompt = f"{custom_prompt}, undressed, nude body, exposed body, natural skin texture"
        else:
            prompt = "undressed person, nude body, exposed body, natural skin texture, realistic anatomy, detailed skin, naked, high quality"
        
        negative_prompt = "clothing, dressed, covered body, fabric, shirt, pants, dress, clothing artifacts, clothed, low quality, blurry, bad anatomy"
        
        # Step F: Prepare Generation Parameters
        clothes_strength = getattr(request, 'clothes_strength', 0.8)
        preserve_face = getattr(request, 'preserve_face', True)
        background_mode = getattr(request, 'background_mode', 'original')
        seed = request.seed if hasattr(request, 'seed') and request.seed is not None else random.randint(0, 2**32 - 1)
        
        return {
            'base_image_path': base_image_path,
            'base_image': base_image,
            'clothes_mask': clothes_mask,
            'clothes_region': clothes_region,
            'prompt': prompt,
            'negative_prompt': negative_prompt,
            'pose_conditioning': pose_conditioning,
            'struct_conditioning': struct_conditioning,
            'clothes_strength': clothes_strength,
            'preserve_face': preserve_face,
            'background_mode': background_mode,
            'seed': seed,
            'generation_params': {
                'num_inference_steps': 50,
                'guidance_scale': 7.5,
                'width': 1024,
                'height': 1024
            },
            # Post-processing parameters
            'quality_mode': getattr(request, 'quality_mode', 'balanced'),
            'enhance_face': getattr(request, 'enhance_face', preserve_face),
            'upscale': getattr(request, 'upscale', False)
        }

    async def run(self, inputs: Dict[str, Any]) -> Any:
        """
        Execute undressing and body exposure generation with ControlNet guidance and post-processing
        
        Processing Flow:
        Phase 1: Model Integration - Setup SDXL + ControlNet
        Phase 2: Pose and Structure Conditioning - Configure ControlNet parameters
        Phase 3: SDXL Generation - Generate undressed body
        Phase 4: Region Fusion - Blend with original
        Phase 5: Face Enhancement - Optional face improvement
        Phase 6: Encoding - Convert to base64
        
        Args:
            inputs: Prepared inputs from prepare_inputs
            
        Returns:
            Base64 encoded image of undressed result
        """
        print("\nClothesPipeline.run: Starting undressing generation...")
        
        # Phase 1: Model Integration
        print("Phase 1: Retrieving SDXL pipeline...")
        sdxl_pipeline = self.models.get('sdxl')
        if not sdxl_pipeline:
            raise ValueError("SDXL model not loaded")
        
        # Collect available ControlNet models
        controlnet_models = []
        if self.models.get('controlnet_pose'):
            controlnet_models.append(self.models['controlnet_pose'])
            print("  - Pose ControlNet available")
        if self.models.get('controlnet_struct'):
            controlnet_models.append(self.models['controlnet_struct'])
            print("  - Struct ControlNet available")
        
        # Integrate ControlNet if available
        active_pipeline = sdxl_pipeline
        if controlnet_models:
            active_pipeline = self.attach_controlnet_to_sdxl(sdxl_pipeline, controlnet_models)
            print(f"  ✓ Integrated {len(controlnet_models)} ControlNet model(s)")
        else:
            print("  ⚠ No ControlNet models available, using base SDXL")
        
        # Phase 2: Pose and Structure Conditioning
        print("\nPhase 2: Preparing ControlNet conditioning...")
        control_images = []
        control_scales = []
        
        if inputs.get('pose_conditioning') is not None and self.models.get('controlnet_pose'):
            control_images.append(inputs['pose_conditioning'])
            control_scales.append(0.8)  # Pose scale
            print("  - Pose conditioning prepared (scale=0.8)")
        
        if inputs.get('struct_conditioning') is not None and self.models.get('controlnet_struct'):
            control_images.append(inputs['struct_conditioning'])
            control_scales.append(0.6)  # Structure scale
            print("  - Structure conditioning prepared (scale=0.6)")
        
        # Phase 3: SDXL Generation
        print("\nPhase 3: Running SDXL undressing generation...")
        print(f"  Prompt: {inputs['prompt'][:80]}...")
        print(f"  Seed: {inputs['seed']}")
        print(f"  Steps: {inputs['generation_params']['num_inference_steps']}")
        
        # Setup generator
        generator = torch.Generator(device=self.device).manual_seed(inputs['seed'])
        
        # Configure generation parameters
        generation_kwargs = {
            'prompt': inputs['prompt'],
            'negative_prompt': inputs['negative_prompt'],
            'generator': generator,
            **inputs['generation_params']
        }
        
        # Add ControlNet conditioning if available
        if control_images and controlnet_models:
            if len(control_images) == 1:
                generation_kwargs['image'] = control_images[0]
                generation_kwargs['controlnet_conditioning_scale'] = control_scales[0]
            else:
                generation_kwargs['image'] = control_images
                generation_kwargs['controlnet_conditioning_scale'] = control_scales
            print(f"  ✓ Using {len(control_images)} ControlNet conditioning inputs")
        
        # Execute generation
        try:
            result = active_pipeline(**generation_kwargs).images[0]
            print("  ✓ Undressed body generation complete")
        except Exception as e:
            print(f"  ✗ Generation failed: {e}")
            raise
        
        # Phase 4: Region Fusion
        print("\nPhase 4: Blending undressed regions...")
        fusion = ClothesFusion()
        
        # Get original image for blending
        original_image = inputs.get('base_image')
        clothes_mask = inputs.get('clothes_mask')
        
        if original_image and clothes_mask and inputs.get('background_mode') == 'original':
            # Align generated with original
            result = fusion.align_clothes(result, original_image)
            # Blend using mask
            result = fusion.blend_clothes(result, original_image, clothes_mask)
            print("  ✓ Blended undressed and original regions")
        else:
            print("  - Skipping fusion (using generated image only)")
        
        # Phase 5: Post-processing with PostProcessPipeline
        print("\nPhase 5: Applying post-processing...")
        from pipelines.postprocess import PostProcessPipeline
        
        post_processor = PostProcessPipeline(device=self.device, model_manager=self.model_manager)
        await post_processor.load_models()
        
        # Extract quality settings from inputs
        quality_mode = inputs.get('quality_mode', 'balanced')
        enable_face_enhance = inputs.get('enhance_face', True)
        enable_upscale = inputs.get('upscale', False)
        
        # Apply post-processing and get base64 result
        result_base64 = post_processor.finalize(
            result,
            quality_mode=quality_mode,
            enable_face_enhance=enable_face_enhance,
            enable_upscale=enable_upscale
        )
        
        print("\n✓ ClothesPipeline.run: Undressing generation complete!")
        print(f"  Result size: {len(result_base64)} characters (base64)\n")
        
        return result_base64


async def generate_clothes():
    """Генерация одежды (deprecated, используйте ClothesPipeline)"""
    pass


async def run(request: GenerationRequest):
    """
    Пайплайн генерации одежды
    
    Будущая логика:
    1. Получение изображения одежды из request.clothes_image
    2. Применение одежды к базовому изображению или модели
    3. Использование промпта для дополнительной настройки
    4. Отправка на GPU-сервер для обработки
    5. Возврат сгенерированного изображения
    
    Args:
        request: Параметры генерации с полями clothes_image, image, prompt
        
    Returns:
        Результат генерации (изображение в base64)
    """
    pipeline = ClothesPipeline()
    return await pipeline.run(request)
