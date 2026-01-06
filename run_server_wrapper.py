#!/usr/bin/env python
"""
Server wrapper to set environment variables before importing modules
"""
import os
import sys

# Set threading environment variables BEFORE any imports
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['VECLIB_MAXIMUM_THREADS'] = '1'
os.environ['GOTO_NUM_THREADS'] = '1'
os.environ['LAPACK_NUM_THREADS'] = '1'

# Disable nested parallelism
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

if __name__ == '__main__':
    # Suppress scientific computing warnings
    import warnings
    warnings.filterwarnings('ignore')
    
    # Now import and run the server
    import server
    # Run with single-process, no threading
    server.app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        threaded=False,
        processes=1,
        use_reloader=False
    )
