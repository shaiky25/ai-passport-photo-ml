#!/usr/bin/env python3
"""
Test script to verify small rembg models work locally
"""

try:
    from rembg import remove, new_session
    from PIL import Image
    import io
    
    print("🧪 Testing small rembg models")
    print("=" * 40)
    
    # Create a simple test image
    img = Image.new('RGB', (200, 200), 'red')
    
    # Add a simple "person" shape
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    draw.ellipse([50, 50, 150, 150], fill='blue')  # Simple circle as "person"
    
    # Convert to bytes
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    input_data = img_buffer.getvalue()
    
    # Test models in order of size
    models_to_test = [
        ('silueta', 'Smallest model (~1.7MB)'),
        ('u2netp', 'Small model (~4.7MB)'),
        ('u2net_human_seg', 'Human-focused model (~176MB)'),
    ]
    
    successful_models = []
    
    for model_name, description in models_to_test:
        try:
            print(f"\n🔄 Testing {model_name}: {description}")
            session = new_session(model_name)
            print(f"✅ Session created for {model_name}")
            
            # Test background removal
            output_data = remove(input_data, session=session)
            print(f"✅ Background removal successful with {model_name}")
            print(f"   Input: {len(input_data)} bytes → Output: {len(output_data)} bytes")
            
            # Convert back to PIL
            result_img = Image.open(io.BytesIO(output_data))
            print(f"   Result: {result_img.size}, mode: {result_img.mode}")
            
            # Save result
            result_filename = f"test_result_{model_name}.png"
            result_img.save(result_filename)
            print(f"   Saved: {result_filename}")
            
            successful_models.append(model_name)
            
        except Exception as e:
            print(f"❌ Failed {model_name}: {e}")
    
    print(f"\n🎉 Summary:")
    print(f"   Successful models: {successful_models}")
    print(f"   Recommended: {successful_models[0] if successful_models else 'None'}")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Runtime error: {e}")