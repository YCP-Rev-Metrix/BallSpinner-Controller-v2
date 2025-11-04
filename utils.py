import io
def is_raspberry_pi():
    """Checks if the code is running on a Raspberry Pi."""
    try:
        with io.open('/sys/firmware/devicetree/base/model', 'r') as m:
            if 'raspberry pi' in m.read().lower():
                return True
    except FileNotFoundError:
        pass
    return False