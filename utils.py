from datetime import datetime

def generate_filename(title, extension='md'):
    # Create a safe filename from title and timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = "".join([c for c in title if c.isalnum() or c in (' ', '-', '_')]).strip()
    safe_title = safe_title.replace(' ', '_')
    return f"{timestamp}_{safe_title}.{extension}"

if __name__ == '__main__':
    # This script is a placeholder to show intended functionality if I were to automate file management
    pass
