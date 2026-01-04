#!/usr/bin/env python
"""
Server wrapper to set environment variables before importing modules
"""
import os

# Set threading environment variables BEFORE any imports
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['VECLIB_MAXIMUM_THREADS'] = '1'

# Now import and run the server
if __name__ == '__main__':
    import server
    server.app.run(host='0.0.0.0', port=5000, debug=False)
