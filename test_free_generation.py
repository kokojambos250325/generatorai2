"""
Test Free Generation - имитация пользователя
Тестирует оба варианта: с лицом и без
"""
import asyncio
import httpx
import base64
from io import BytesIO
from PIL import Image

BASE_URL = "http://localhost:8000"

def create_test_image_base64():
    """Create a simple test image (red square)"""
    img = Image.new('RGB', (512, 512), color='red')
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_bytes = buffer.getvalue()
    return base64.b64encode(img_bytes).decode('utf-8')

async def test_free_generation_without_face():
    """Test 1: Free generation БЕЗ лица"""
    print("\n" + "="*60)
    print("ТЕСТ 1: Свободная генерация БЕЗ лица")
    print("="*60)
    
    try:
        payload = {
            "mode": "free",
            "prompt": "a beautiful sunset over mountains, photorealistic, high quality",
            "style": "realism",
            "add_face": False,
            "seed": 42
        }
        
        print(f"📝 Промпт: {payload['prompt']}")
        print(f"🎨 Стиль: {payload['style']}")
        print(f"👤 Лицо: НЕТ")
        print("\n⏳ Отправка запроса...")
        
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(f"{BASE_URL}/generate", json=payload)
            
            print(f"📊 Статус: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"📦 Результат: {result.get('status')}")
                
                if result.get("status") == "done" and result.get("image"):
                    image_size = len(result["image"]) if result["image"] else 0
                    print(f"✅ УСПЕХ! Изображение получено ({image_size} байт base64)")
                    print(f"🆔 Task ID: {result.get('task_id', 'N/A')}")
                    return True
                else:
                    error = result.get("error", "Unknown error")
                    print(f"❌ ОШИБКА: {error}")
                    return False
            else:
                print(f"❌ HTTP Ошибка: {response.status_code}")
                print(f"📄 Ответ: {response.text[:200]}")
                return False
                
    except Exception as e:
        print(f"❌ ИСКЛЮЧЕНИЕ: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_free_generation_with_face():
    """Test 2: Free generation С лицом"""
    print("\n" + "="*60)
    print("ТЕСТ 2: Свободная генерация С лицом")
    print("="*60)
    
    try:
        test_face_image = create_test_image_base64()
        
        payload = {
            "mode": "free",
            "prompt": "a beautiful woman in elegant dress, professional photography, high quality",
            "style": "realism",
            "add_face": True,
            "face_images": [test_face_image],
            "face_strength": 0.75,
            "seed": 42
        }
        
        print(f"📝 Промпт: {payload['prompt']}")
        print(f"🎨 Стиль: {payload['style']}")
        print(f"👤 Лицо: ДА (1 фото, strength={payload['face_strength']})")
        print("\n⏳ Отправка запроса...")
        
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(f"{BASE_URL}/generate", json=payload)
            
            print(f"📊 Статус: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"📦 Результат: {result.get('status')}")
                
                if result.get("status") == "done" and result.get("image"):
                    image_size = len(result["image"]) if result["image"] else 0
                    print(f"✅ УСПЕХ! Изображение получено ({image_size} байт base64)")
                    print(f"🆔 Task ID: {result.get('task_id', 'N/A')}")
                    return True
                else:
                    error = result.get("error", "Unknown error")
                    print(f"❌ ОШИБКА: {error}")
                    return False
            else:
                print(f"❌ HTTP Ошибка: {response.status_code}")
                print(f"📄 Ответ: {response.text[:200]}")
                return False
                
    except Exception as e:
        print(f"❌ ИСКЛЮЧЕНИЕ: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_different_styles():
    """Test 3: Разные стили"""
    print("\n" + "="*60)
    print("ТЕСТ 3: Разные стили (noir, super_realism, anime)")
    print("="*60)
    
    styles = ["noir", "super_realism", "anime"]
    results = {}
    
    for style in styles:
        print(f"\n🎨 Тестирую стиль: {style}")
        try:
            payload = {
                "mode": "free",
                "prompt": "a beautiful landscape",
                "style": style,
                "add_face": False,
                "seed": 42
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(f"{BASE_URL}/generate", json=payload)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("status") == "done":
                        print(f"  ✅ {style}: OK")
                        results[style] = True
                    else:
                        print(f"  ❌ {style}: {result.get('error', 'Unknown')}")
                        results[style] = False
                else:
                    print(f"  ❌ {style}: HTTP {response.status_code}")
                    results[style] = False
        except Exception as e:
            print(f"  ❌ {style}: {e}")
            results[style] = False
    
    return results

async def main():
    """Run all tests"""
    print("🚀 ТЕСТИРОВАНИЕ СВОБОДНОЙ ГЕНЕРАЦИИ")
    print("="*60)
    
    results = {}
    
    # Test 1: Без лица
    results["without_face"] = await test_free_generation_without_face()
    
    # Test 2: С лицом
    results["with_face"] = await test_free_generation_with_face()
    
    # Test 3: Разные стили
    style_results = await test_different_styles()
    results.update(style_results)
    
    # Summary
    print("\n" + "="*60)
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print("="*60)
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:30} {status}")
    
    total = len(results)
    passed = sum(results.values())
    print(f"\nВсего тестов: {total}")
    print(f"Успешно: {passed}")
    print(f"Провалено: {total - passed}")
    print(f"Процент успеха: {passed/total*100:.1f}%")

if __name__ == "__main__":
    asyncio.run(main())

