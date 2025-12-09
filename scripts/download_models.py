#!/usr/bin/env python3
"""
Model Download Script for RunPod Deployment

Automated downloading of all required ML models from HuggingFace Hub and GitHub releases.
Supports selective downloads via CLI flags with progress reporting and error handling.

Usage:
    python scripts/download_models.py [OPTIONS]

Options:
    --all              Download all models (default)
    --sdxl             Download only SDXL models (base + refiner)
    --controlnet       Download only ControlNet models
    --insightface      Download only InsightFace models
    --enhancement      Download only face enhancement models (GFPGAN, ESRGAN)
    --skip-existing    Skip models that are already cached
    --cache-dir PATH   Override cache directory (default: /workspace/models)
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from datetime import datetime
import requests
from tqdm import tqdm

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class ModelDownloader:
    """Orchestrates model downloads with progress tracking and error handling"""
    
    def __init__(self, cache_dir: str = None, skip_existing: bool = False):
        """
        Initialize model downloader
        
        Args:
            cache_dir: Base directory for model storage
            skip_existing: Skip models that already exist
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path("/workspace/models")
        self.skip_existing = skip_existing
        self.download_stats = {
            'success': [],
            'failed': [],
            'skipped': []
        }
        
        logger.info(f"ModelDownloader initialized with cache_dir: {self.cache_dir}")
        logger.info(f"Skip existing: {self.skip_existing}")
    
    def _model_exists(self, model_path: Path) -> bool:
        """Check if model files already exist"""
        if not model_path.exists():
            return False
        
        # Check if directory has files
        if model_path.is_dir():
            files = list(model_path.iterdir())
            return len(files) > 0
        
        return model_path.is_file()
    
    def download_diffusers_model(self, model_id: str, model_name: str, subfolder: str = None):
        """
        Download model using diffusers library
        
        Args:
            model_id: HuggingFace model ID (e.g., 'stabilityai/stable-diffusion-xl-base-1.0')
            model_name: Human-readable name for logging
            subfolder: Optional subfolder within cache
        """
        logger.info(f"Starting download: {model_name} ({model_id})")
        
        # Determine cache path
        if subfolder:
            cache_path = self.cache_dir / subfolder
        else:
            cache_path = self.cache_dir / "diffusers"
        
        # Skip if exists
        if self.skip_existing and self._model_exists(cache_path):
            logger.info(f"Skipping {model_name}: Already exists at {cache_path}")
            self.download_stats['skipped'].append(model_name)
            return
        
        try:
            # Import here to avoid dependency issues
            from diffusers import DiffusionPipeline, ControlNetModel, AutoencoderKL
            import torch
            
            # Determine model type and download
            if 'controlnet' in model_id.lower():
                logger.info(f"Downloading ControlNet model: {model_id}")
                model = ControlNetModel.from_pretrained(
                    model_id,
                    cache_dir=str(cache_path),
                    torch_dtype=torch.float16
                )
            elif 'vae' in model_id.lower() or 'vae' in model_name.lower():
                logger.info(f"Downloading VAE model: {model_id}")
                model = AutoencoderKL.from_pretrained(
                    model_id,
                    cache_dir=str(cache_path),
                    torch_dtype=torch.float16
                )
            else:
                logger.info(f"Downloading diffusion pipeline: {model_id}")
                model = DiffusionPipeline.from_pretrained(
                    model_id,
                    cache_dir=str(cache_path),
                    torch_dtype=torch.float16,
                    variant="fp16",
                    use_safetensors=True
                )
            
            logger.info(f"✓ Successfully downloaded: {model_name}")
            self.download_stats['success'].append(model_name)
            
            # Clean up to save memory
            del model
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                
        except Exception as e:
            logger.error(f"✗ Failed to download {model_name}: {str(e)}")
            self.download_stats['failed'].append((model_name, str(e)))
    
    def download_file_with_progress(self, url: str, destination: Path, description: str):
        """
        Download file from URL with progress bar
        
        Args:
            url: Download URL
            destination: Local file path
            description: Description for progress bar
        """
        logger.info(f"Downloading {description} from {url}")
        
        # Skip if exists
        if self.skip_existing and destination.exists():
            logger.info(f"Skipping {description}: File already exists")
            self.download_stats['skipped'].append(description)
            return
        
        try:
            # Create parent directory
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            # Download with progress bar
            response = requests.get(url, stream=True, timeout=300)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(destination, 'wb') as f:
                with tqdm(
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    desc=description,
                    ncols=100
                ) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
            
            logger.info(f"✓ Successfully downloaded: {description} ({destination})")
            self.download_stats['success'].append(description)
            
        except Exception as e:
            logger.error(f"✗ Failed to download {description}: {str(e)}")
            self.download_stats['failed'].append((description, str(e)))
            
            # Clean up partial download
            if destination.exists():
                destination.unlink()
    
    def download_insightface(self):
        """Download InsightFace models"""
        logger.info("=" * 80)
        logger.info("Downloading InsightFace models")
        logger.info("=" * 80)
        
        try:
            import insightface
            from insightface.app import FaceAnalysis
            
            # InsightFace downloads automatically on first use
            cache_path = self.cache_dir / "insightface"
            cache_path.mkdir(parents=True, exist_ok=True)
            
            logger.info("Initializing InsightFace (will auto-download buffalo_l model)")
            
            app = FaceAnalysis(
                name='buffalo_l',
                root=str(cache_path),
                providers=['CPUExecutionProvider']  # Use CPU for download
            )
            app.prepare(ctx_id=0, det_size=(640, 640))
            
            logger.info("✓ InsightFace models downloaded successfully")
            self.download_stats['success'].append("InsightFace buffalo_l")
            
        except Exception as e:
            logger.error(f"✗ Failed to download InsightFace: {str(e)}")
            self.download_stats['failed'].append(("InsightFace buffalo_l", str(e)))
    
    def download_enhancement_models(self):
        """Download face enhancement models (GFPGAN, Real-ESRGAN)"""
        logger.info("=" * 80)
        logger.info("Downloading face enhancement models")
        logger.info("=" * 80)
        
        # GFPGAN v1.4
        gfpgan_url = "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth"
        gfpgan_dest = self.cache_dir / "enhancement" / "gfpgan" / "GFPGANv1.4.pth"
        self.download_file_with_progress(gfpgan_url, gfpgan_dest, "GFPGAN v1.4")
        
        # Real-ESRGAN x4plus
        esrgan_url = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth"
        esrgan_dest = self.cache_dir / "enhancement" / "esrgan" / "RealESRGAN_x4plus.pth"
        self.download_file_with_progress(esrgan_url, esrgan_dest, "Real-ESRGAN x4plus")
        
        # Real-ESRGAN x2plus (optional, smaller model)
        esrgan_2x_url = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth"
        esrgan_2x_dest = self.cache_dir / "enhancement" / "esrgan" / "RealESRGAN_x2plus.pth"
        self.download_file_with_progress(esrgan_2x_url, esrgan_2x_dest, "Real-ESRGAN x2plus")
    
    def download_sdxl_models(self):
        """Download SDXL base and refiner models"""
        logger.info("=" * 80)
        logger.info("Downloading SDXL models")
        logger.info("=" * 80)
        
        # SDXL Base
        self.download_diffusers_model(
            "stabilityai/stable-diffusion-xl-base-1.0",
            "SDXL Base",
            "sdxl/base"
        )
        
        # SDXL Refiner
        self.download_diffusers_model(
            "stabilityai/stable-diffusion-xl-refiner-1.0",
            "SDXL Refiner",
            "sdxl/refiner"
        )
        
        # SDXL VAE FP16 Fix
        self.download_diffusers_model(
            "madebyollin/sdxl-vae-fp16-fix",
            "SDXL VAE FP16",
            "sdxl/vae"
        )
    
    def download_controlnet_models(self):
        """Download ControlNet models for SDXL"""
        logger.info("=" * 80)
        logger.info("Downloading ControlNet models")
        logger.info("=" * 80)
        
        controlnets = [
            ("thibaud/controlnet-openpose-sdxl-1.0", "ControlNet Pose", "controlnet/pose"),
            ("diffusers/controlnet-depth-sdxl-1.0", "ControlNet Depth", "controlnet/depth"),
            ("diffusers/controlnet-canny-sdxl-1.0", "ControlNet Canny", "controlnet/canny"),
        ]
        
        for model_id, name, subfolder in controlnets:
            self.download_diffusers_model(model_id, name, subfolder)
    
    def print_summary(self):
        """Print download summary report"""
        logger.info("=" * 80)
        logger.info("DOWNLOAD SUMMARY")
        logger.info("=" * 80)
        
        logger.info(f"✓ Successful downloads: {len(self.download_stats['success'])}")
        for model in self.download_stats['success']:
            logger.info(f"  - {model}")
        
        if self.download_stats['skipped']:
            logger.info(f"⊘ Skipped (already exist): {len(self.download_stats['skipped'])}")
            for model in self.download_stats['skipped']:
                logger.info(f"  - {model}")
        
        if self.download_stats['failed']:
            logger.warning(f"✗ Failed downloads: {len(self.download_stats['failed'])}")
            for model, error in self.download_stats['failed']:
                logger.warning(f"  - {model}: {error}")
        
        logger.info("=" * 80)
        
        # Exit code based on failures
        if self.download_stats['failed'] and not self.download_stats['success']:
            logger.error("All downloads failed!")
            return 1
        elif self.download_stats['failed']:
            logger.warning("Some downloads failed, but partial success achieved")
            return 0  # Don't fail startup if some models downloaded
        else:
            logger.info("All requested downloads completed successfully!")
            return 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Download ML models for GPU server deployment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Download all models:
    python scripts/download_models.py --all
  
  Download only SDXL:
    python scripts/download_models.py --sdxl
  
  Download ControlNet and skip existing:
    python scripts/download_models.py --controlnet --skip-existing
  
  Custom cache directory:
    python scripts/download_models.py --all --cache-dir /custom/path
        """
    )
    
    parser.add_argument('--all', action='store_true', help='Download all models (default)')
    parser.add_argument('--sdxl', action='store_true', help='Download only SDXL models')
    parser.add_argument('--controlnet', action='store_true', help='Download only ControlNet models')
    parser.add_argument('--insightface', action='store_true', help='Download only InsightFace models')
    parser.add_argument('--enhancement', action='store_true', help='Download only enhancement models')
    parser.add_argument('--skip-existing', action='store_true', help='Skip already cached models')
    parser.add_argument('--cache-dir', type=str, default=None, help='Override cache directory')
    
    args = parser.parse_args()
    
    # Default to --all if no specific flags
    if not any([args.sdxl, args.controlnet, args.insightface, args.enhancement]):
        args.all = True
    
    # Determine cache directory
    cache_dir = args.cache_dir or os.getenv('MODEL_CACHE_DIR', '/workspace/models')
    
    logger.info("=" * 80)
    logger.info("MODEL DOWNLOAD SCRIPT")
    logger.info("=" * 80)
    logger.info(f"Cache directory: {cache_dir}")
    logger.info(f"Skip existing: {args.skip_existing}")
    logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)
    
    # Initialize downloader
    downloader = ModelDownloader(cache_dir=cache_dir, skip_existing=args.skip_existing)
    
    try:
        # Download based on flags
        if args.all or args.sdxl:
            downloader.download_sdxl_models()
        
        if args.all or args.controlnet:
            downloader.download_controlnet_models()
        
        if args.all or args.insightface:
            downloader.download_insightface()
        
        if args.all or args.enhancement:
            downloader.download_enhancement_models()
        
        # Print summary
        exit_code = downloader.print_summary()
        
        logger.info(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        logger.warning("\nDownload interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
