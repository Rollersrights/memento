import os

def _has_avx2() -> bool:
    """Detect AVX2 support at runtime."""
    try:
        # Method 1: Check CPU flags via /proc/cpuinfo (Linux)
        if os.path.exists('/proc/cpuinfo'):
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                if 'avx2' in cpuinfo.lower():
                    print("Found 'avx2' in /proc/cpuinfo")
                    return True
                else:
                    print("Did NOT find 'avx2' in /proc/cpuinfo")
        
        # Method 2: Try cpuinfo library if available
        try:
            import cpuinfo
            info = cpuinfo.get_cpu_info()
            flags = info.get('flags', []) if info else []
            print(f"cpuinfo flags: {flags}")
            if isinstance(flags, list):
                return 'avx2' in [f.lower() for f in flags]
            elif isinstance(flags, str):
                return 'avx2' in flags.lower()
        except ImportError:
            print("cpuinfo module not found")
            pass
        except Exception as e:
            print(f"cpuinfo error: {e}")
            pass
        
        return False
    except Exception as e:
        print(f"Error checking AVX2: {e}")
        return False

print(f"Has AVX2: {_has_avx2()}")
