#!/data/data/com.termux/files/usr/bin/python3
import os
import sys
import time
import subprocess
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
from PIL import Image

# ========== CONFIG ==========
ASCII_CHARS = " .:-=+*#%@"  # Dark to light
DEFAULT_WIDTH = 80
RENDER_DIR = "/data/data/com.termux/files/usr/tmp/ascii_render"
MAX_WORKERS = 2  # Parallel processing
# ============================

def setup():
    """Install required packages"""
    print("🔧 Setting up...")
    
    # Check ffmpeg
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except:
        print("Installing ffmpeg...")
        subprocess.run(['pkg', 'install', 'ffmpeg', '-y', '--quiet'], capture_output=True)
    
    # Check numpy
    try:
        import numpy
    except ImportError:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'numpy', '--quiet'], capture_output=True)
    
    # Check PIL
    try:
        from PIL import Image
    except ImportError:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pillow', '--quiet'], capture_output=True)
    
    # Create render directory
    os.makedirs(RENDER_DIR, exist_ok=True)
    print("✅ Setup complete\n")

def clear_screen():
    """Clear terminal"""
    print("\033[2J\033[H", end='')

def get_video_info(video_path):
    """Get accurate video info"""
    cmd = ['ffprobe', '-v', 'quiet',
           '-select_streams', 'v:0',
           '-show_entries', 'stream=r_frame_rate,duration,width,height',
           '-of', 'json',
           video_path]
    
    try:
        output = subprocess.check_output(cmd, text=True)
        data = json.loads(output)
        
        if 'streams' in data and len(data['streams']) > 0:
            stream = data['streams'][0]
            
            # Parse FPS
            fps_str = stream.get('r_frame_rate', '30/1')
            if '/' in fps_str:
                num, den = fps_str.split('/')
                fps = float(num) / float(den)
            else:
                fps = float(fps_str)
            
            duration = float(stream.get('duration', 0))
            width = int(stream.get('width', 640))
            height = int(stream.get('height', 480))
            
            return fps, duration, width, height
            
    except Exception as e:
        print(f"⚠️  Couldn't get video info: {e}")
    
    return 30.0, 0, 640, 480

def frame_to_ascii_fast(img_path, width):
    """Fast frame to ASCII conversion"""
    try:
        img = Image.open(img_path)
        
        # Calculate height
        aspect = img.height / img.width
        ascii_height = int(width * aspect / 2)
        if ascii_height < 1:
            ascii_height = 1
        
        # Resize
        img = img.resize((width, ascii_height * 2))
        img_gray = img.convert('L')
        img_array = np.array(img_gray)
        
        # Fast ASCII conversion
        normalized = img_array / 255.0
        indices = (normalized * (len(ASCII_CHARS) - 1)).astype(int)
        
        ascii_frame = ""
        for row in indices:
            for idx in row:
                ascii_frame += ASCII_CHARS[idx]
            ascii_frame += "\n"
        
        return ascii_frame, ascii_height
    except Exception as e:
        return None, 0

def render_video_fast(video_path, width):
    """Fast parallel rendering"""
    print("🎬 FAST RENDERING MODE")
    
    # Get video info
    fps, duration, vid_width, vid_height = get_video_info(video_path)
    total_frames = int(fps * duration) if duration > 0 else 0
    
    print(f"   Video: {vid_width}x{vid_height} @ {fps:.2f}FPS")
    print(f"   Duration: {duration:.1f}s (~{total_frames} frames)")
    
    # Clean render directory
    for f in os.listdir(RENDER_DIR):
        os.remove(os.path.join(RENDER_DIR, f))
    
    # Step 1: Extract ALL frames FAST
    print("\n   📥 Extracting frames...")
    
    frame_dir = os.path.join(RENDER_DIR, "raw_frames")
    os.makedirs(frame_dir, exist_ok=True)
    
    # Extract frames with ffmpeg (fastest method)
    extract_cmd = [
        'ffmpeg', '-i', video_path,
        '-vf', f'fps={fps},scale={width}:-2',  # -2 keeps aspect, even height
        '-q:v', '1',  # Low quality for speed
        os.path.join(frame_dir, 'frame_%06d.jpg'),  # JPEG is faster than PNG
        '-loglevel', 'quiet'
    ]
    
    start_extract = time.time()
    result = subprocess.run(extract_cmd, capture_output=True)
    extract_time = time.time() - start_extract
    
    if result.returncode != 0:
        print(f"   ❌ Extraction failed")
        return 0, fps, 0
    
    # Get extracted frames
    frame_files = sorted([f for f in os.listdir(frame_dir) if f.endswith('.jpg')])
    total_frames = len(frame_files)
    
    if total_frames == 0:
        print("   ❌ No frames extracted!")
        return 0, fps, 0
    
    print(f"   ✅ Extracted {total_frames} frames in {extract_time:.1f}s")
    
    # Step 2: Parallel ASCII conversion
    print("   🔄 Converting to ASCII (parallel)...")
    
    ascii_height = 0
    processed = 0
    errors = 0
    
    # Process in parallel
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all tasks
        future_to_file = {}
        for i, frame_file in enumerate(frame_files, 1):
            frame_path = os.path.join(frame_dir, frame_file)
            future = executor.submit(frame_to_ascii_fast, frame_path, width)
            future_to_file[future] = (i, frame_path)
        
        # Process results as they complete
        start_convert = time.time()
        
        for future in as_completed(future_to_file):
            i, frame_path = future_to_file[future]
            
            try:
                ascii_frame, frame_height = future.result()
                
                if ascii_frame:
                    if ascii_height == 0:
                        ascii_height = frame_height
                    
                    # Save ASCII frame
                    ascii_path = os.path.join(RENDER_DIR, f"frame_{i:06d}.txt")
                    with open(ascii_path, 'w') as f:
                        f.write(ascii_frame)
                    
                    processed += 1
                    
                    # Progress
                    if processed % 50 == 0 or processed == total_frames:
                        percent = (processed / total_frames) * 100
                        print(f"\r   Progress: {processed}/{total_frames} ({percent:.1f}%)", end='')
                else:
                    errors += 1
                    
            except Exception as e:
                errors += 1
    
    convert_time = time.time() - start_convert
    
    # Cleanup raw frames
    for f in os.listdir(frame_dir):
        os.remove(os.path.join(frame_dir, f))
    os.rmdir(frame_dir)
    
    total_time = extract_time + convert_time
    fps_rate = total_frames / total_time if total_time > 0 else 0
    
    print(f"\n\n   ✅ Rendered {processed} frames in {total_time:.1f}s")
    print(f"   🚀 Speed: {fps_rate:.1f} FPS processing rate")
    if errors > 0:
        print(f"   ⚠️  {errors} frames failed")
    
    # Save metadata for playback
    metadata = {
        'total_frames': total_frames,
        'fps': fps,
        'width': width,
        'height': ascii_height,
        'video_path': video_path,
        'render_time': time.time()
    }
    
    with open(os.path.join(RENDER_DIR, 'metadata.json'), 'w') as f:
        json.dump(metadata, f)
    
    return total_frames, fps, ascii_height

def play_with_accurate_fps(total_frames, fps, width, ascii_height):
    """Play with EXACT video timing"""
    frame_delay = 1.0 / fps
    
    print(f"\n▶️  PLAYBACK: {total_frames} frames @ {fps:.2f}FPS")
    print(f"   Frame delay: {frame_delay:.3f}s")
    print(f"   Total time: {total_frames * frame_delay:.1f}s")
    print("\n   Press Ctrl+C to stop\n")
    
    time.sleep(2)
    clear_screen()
    
    frame_count = 0
    start_time = time.time()
    next_frame_time = start_time
    
    try:
        while frame_count < total_frames:
            frame_num = frame_count + 1
            ascii_file = os.path.join(RENDER_DIR, f"frame_{frame_num:06d}.txt")
            
            if not os.path.exists(ascii_file):
                # Try to skip missing frame
                frame_count += 1
                next_frame_time += frame_delay
                continue
            
            # Load and display frame
            with open(ascii_file, 'r') as f:
                ascii_frame = f.read()
            
            # Clear and display
            print("\033[H", end='')
            print(ascii_frame)
            
            frame_count += 1
            
            # Show accurate timing info
            current_time = time.time()
            elapsed = current_time - start_time
            target_elapsed = frame_count * frame_delay
            drift = current_time - (start_time + target_elapsed)
            
            # Stats
            actual_fps = frame_count / elapsed if elapsed > 0 else 0
            progress = (frame_count / total_frames) * 100
            
            print(f"\n🎯 Frame: {frame_count}/{total_frames} ({progress:.1f}%)")
            print(f"📊 Target FPS: {fps:.2f} | Actual: {actual_fps:.2f}")
            print(f"⏱️  Drift: {drift*1000:.1f}ms {'(AHEAD)' if drift < 0 else '(BEHIND)'}")
            
            # ACCURATE TIMING
            next_frame_time += frame_delay
            sleep_time = next_frame_time - time.time()
            
            if sleep_time > 0:
                # High precision sleep
                time.sleep(sleep_time)
            else:
                # We're behind, don't sleep
                pass
            
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Stopped at frame {frame_count}")
    
    end_time = time.time()
    total_play_time = end_time - start_time
    avg_fps = frame_count / total_play_time if total_play_time > 0 else 0
    
    print(f"\n✅ Playback finished")
    print(f"   Frames: {frame_count}/{total_frames}")
    print(f"   Time: {total_play_time:.1f}s")
    print(f"   Average FPS: {avg_fps:.2f}")
    print(f"   Target FPS: {fps:.2f}")
    print(f"   Accuracy: {(avg_fps/fps*100 if fps>0 else 0):.1f}%")

def check_existing_render(video_path, width):
    """Check if video already rendered"""
    metadata_file = os.path.join(RENDER_DIR, 'metadata.json')
    
    if not os.path.exists(metadata_file):
        return None
    
    try:
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Check if same video and width
        if (metadata.get('video_path') == video_path and 
            metadata.get('width') == width):
            
            # Check if all frames exist
            total_frames = metadata.get('total_frames', 0)
            missing_frames = False
            
            for i in range(1, total_frames + 1):
                frame_file = os.path.join(RENDER_DIR, f"frame_{i:06d}.txt")
                if not os.path.exists(frame_file):
                    missing_frames = True
                    break
            
            if not missing_frames:
                return metadata
    
    except:
        pass
    
    return None

def main():
    """Main function"""
    setup()
    
    clear_screen()
    print("╔══════════════════════════════════════════╗")
    print("║     ULTRA-FAST ASCII VIDEO PLAYER       ║")
    print("║   FAST RENDER • ACCURATE FPS • SAVE     ║")
    print("╚══════════════════════════════════════════╝")
    print()
    
    # Get video path
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    else:
        video_path = input("📂 Video path: ").strip()
    
    if not video_path or not os.path.exists(video_path):
        print("\n❌ File not found!")
        print("💡 Example: /sdcard/Download/video.mp4")
        return
    
    # Get width
    try:
        width_input = input(f"📏 ASCII width [{DEFAULT_WIDTH}]: ").strip()
        width = int(width_input) if width_input else DEFAULT_WIDTH
    except:
        width = DEFAULT_WIDTH
    
    print(f"\n📁 Video: {os.path.basename(video_path)}")
    print(f"📐 Width: {width} characters")
    
    # Check for existing render
    existing = check_existing_render(video_path, width)
    if existing:
        print("\n✅ Found existing render!")
        print(f"   Frames: {existing['total_frames']}")
        print(f"   FPS: {existing['fps']:.2f}")
        
        use_existing = input("\nUse existing render? (Y/n): ").strip().lower()
        if use_existing != 'n':
            total_frames = existing['total_frames']
            fps = existing['fps']
            ascii_height = existing['height']
            
            play_with_accurate_fps(total_frames, fps, width, ascii_height)
            return
    
    # Get video info for estimation
    fps, duration, vid_width, vid_height = get_video_info(video_path)
    estimated_frames = int(fps * duration) if duration > 0 else 0
    estimated_time = estimated_frames * 0.005  # 0.005s per frame (200 FPS processing)
    
    print(f"\n📊 Video info:")
    print(f"   Resolution: {vid_width}x{vid_height}")
    print(f"   FPS: {fps:.2f}")
    print(f"   Duration: {duration:.1f}s")
    print(f"   Est. frames: {estimated_frames}")
    print(f"   Est. render time: {estimated_time:.1f}s")
    
    # Start rendering
    input("\nPress Enter to start fast rendering...")
    
    render_start = time.time()
    total_frames, actual_fps, ascii_height = render_video_fast(video_path, width)
    render_time = time.time() - render_start
    
    if total_frames == 0:
        print("❌ Failed to render video")
        return
    
    print(f"\n✅ Total render time: {render_time:.1f}s")
    print(f"   Processing speed: {total_frames/render_time:.1f} FPS")
    
    # Ask to save permanently
    save = input("\n💾 Save render for future use? (Y/n): ").strip().lower()
    if save == 'n':
        # Move to permanent location
        import shutil
        import hashlib
        
        # Create hash based on video path and width
        video_hash = hashlib.md5(f"{video_path}_{width}".encode()).hexdigest()[:8]
        save_dir = f"/data/data/com.termux/files/usr/share/ascii_videos/{video_hash}"
        os.makedirs(save_dir, exist_ok=True)
        
        # Copy files
        for f in os.listdir(RENDER_DIR):
            src = os.path.join(RENDER_DIR, f)
            dst = os.path.join(save_dir, f)
            shutil.copy2(src, dst)
        
        print(f"💾 Saved to: {save_dir}")
    
    # Play the video
    play_with_accurate_fps(total_frames, actual_fps, width, ascii_height)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n💥 Error: {e}")
        import traceback
        traceback.print_exc()
