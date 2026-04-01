import os
import shlex
import sys

# Add parent directory and src/ to Python path for imports
parent_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, 'src'))

from wilma_digest.main import main

def lambda_handler(event, context):
    """
    AWS Lambda entry point
    Calls the existing CLI main() function
    """
    # Get command from environment variable
    # Example: "wilma-digest Irina.yaml Alexei.yaml --max-messages 10"
    cmd = os.environ.get('WILMA_DIGEST_CMD', 'wilma-digest')
    sys.argv = shlex.split(cmd)
    
    try:
        main()
        return {
            'statusCode': 200,
            'body': 'Digest sent successfully'
        }
    except Exception as e:
        print(f"Error: {e}")
        raise
