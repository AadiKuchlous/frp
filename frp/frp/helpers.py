from . import app

def allowed_file(fname):
    """
    Returns true if 'fname' has an extension mentioned in
    ALLOWED_EXTENSIONS
    """

    extension = "." in fname and fname.rsplit('.', 1)[-1] or ""
    return extension in app.config['ALLOWED_EXTENSIONS']
        
    
    
    
    
